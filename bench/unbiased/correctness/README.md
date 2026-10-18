# Step 12: correctness of the engines against llama.cpp at 3cf03257

PLAN.md step 12, the checks of `docs/CORRECTNESS-PLAN.md` (step 11, signed off 2026-10-18). Run 2026-10-18 on the
A6000 VM (NVIDIA RTX A6000 48 GB, driver 550.163.01, CUDA 12.4; AMD Ryzen 7 1700, 12 threads given to the VM, AVX2;
50 GB RAM), not on the RTX 3090 pod the plan was written for: the pod was unreachable that day and the VM holds every
file of both configurations (`docs/MODEL-FILES.md`). The A6000 is the same architecture as the 3090 (sm_86), so the
kernels under test are the pod's; what differs is that every expert of both models is resident on the 48 GB card, so no
CPU or PCIe expert tier ran (section "Not covered").

Fork: UnbiasedStrata 2 at 5a4f7136 (engines unmodified since the import, `UPSTREAM.md`), built with
`CUDA_ARCHS=86` and `-DSTRATA_BUILD_TESTS=ON`. Reference: llama.cpp `3cf03257` from `third_party/llama.cpp`, built
with `-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86 -DLLAMA_CURL=OFF`, driven by `tools/qwen35/q36_llama_dump.cpp`
(two additions for this run: `STRATA_DUMP_UBATCH`, default min(ctx, 4096), and `STRATA_DUMP_THREADS`, default every
hardware thread). Scripts and chains: `scripts/`. Raw outputs live on the VM under `~/us2-results/correctness/`; what
is committed here is listed at the end.

## 1. Inputs (plan 3.2)

16 sequences, `inputs/<set>/<seq>.prompt.ids` (`inputs-src/` has the texts; `scripts/make-inputs.py` the tokenizer
calls). The Qwen3.6 and Flash-Next files tokenize identically (checked on the first prompt), so one id set serves both.

| Set | Sequences | Prompt tokens | Scored steps each | Answer |
| --- | --- | --- | --- | --- |
| short | p00-p09, upstream's `tools/qwen35/parity_prompts.json` (ChatML, thinking off; ids equal upstream's `.ids` file) | 20-40 | 128 | the reference GPU run's greedy answer, per model (`<seq>.answer.<model>.ids`) |
| code | lru (LRU cache in Python, thinking off), puzzle (three mislabelled boxes, thinking on) | 52, 66 | 400, 324 | same |
| long | d4k, d16k, d31k: the first 4096 / 16384 / 31744 tokens of this repository's docs | 4096-31744 | 256 | same |
| realtext | r16k: tokens 15874-16383 of the same document, scored as given text | 15874 | 510 | fixed (`r16k.answer.ids`) |

The engine stops at `<|im_end|>` where llama.cpp's greedy answer ran past it (p04 16, p06 98, p07 69, p09 23 steps);
the scorer scores the steps both sides have.

## 2. Component parities (plan section 2.2, run order step 2)

`scripts/parity-run.sh`; per program `parity/<name>/{command.sh,ctest.txt|stdout.txt,stderr.txt,exit.txt}`.

| Result | Programs |
| --- | --- |
| PASS (exit 0, ctest "100% tests passed") | iq_parity (fixture by `tools/iq_fixture.py`, numpy installed for it), iq_avx2_parity (+ `_iq3s_mt1`), q8k_quant_parity (+ `_avx`), native_grouped_parity, iq_multi_parity, mmvq_multi_parity, prefill_fused_iq_test, prefill_mmq_scatter_test, kv_q8_parity, kv_stream_parity, kv_steps_parity, kv_window_parity, gdn_parity, gdn_rec_parity, qsa_parity, qsa_topk_parity, verify_parity, spec_verify_parity, sampler_parity, native_multi_parity, rope_parity, elementwise_parity, decode_cluster_parity (skips its sm_90 cases), quantize_act_parity, dequant_wide_parity, pdl_parity, dma_batch_parity, batch_rows_parity, verify_batch_parity, router_top10_parity, route_window_parity, native_expert_parity_{q4_K_q8_0,q6_K_q8_0,q8_0_q8_0}, poly_kv_q8_test, poly_workers_test |
| PASS (hand run, exit 0) | poly_route_test, poly_norm_q8_test, poly_gemm_small_test, poly_attend_test (dim 64, not Qwen3.6's shape), `poly_expert_parity` on UD-IQ4_XS |
| **FAIL (exit 1)** | `poly_expert_parity` on UD-Q3_K_M: finding 1 |
| SKIP (exit 3) | poly_draft_race_test (every expert cached, as the plan predicted) |
| not registered | poly_guesses_test (no such target in this tree) |

Settled from the files (plan 5.3): the pack's `native_experts.txt` equals `tests/data/native_experts/iq3_xxs.txt`
except the header line (format v3 against v2; `files/pack-native-experts.diff`). UD-Q3_K_M's routed experts are
IQ3_XXS 55 %, IQ4_XS 38 %, Q6_K 5 %, Q3_K 2 %, Q4_K 1 % of bytes (`files/q3km-tensors.txt`), so the formats the
parities had to cover for configuration B are IQ3_XXS, IQ4_XS, Q6_K, Q3_K, Q4_K, Q8_0: all in `iq_parity`,
`mmvq_multi_parity`, `native_expert_parity` or `poly_expert_parity` above.

## 3. Configuration B: `strata-poly`, Qwen3.6-35B-A3B (plan 3.3)

Reference runs: `scripts/ref-run.py`; GPU `--ngl 99`, CPU `--ngl 0`, full f32 logits per step on the VM
(`reference/<model>/<seq>.{gpu,cpu}.full`, sha256 and the derived `.top20.tsv` committed). Engine arms:
`scripts/poly-run.py`, a fresh process per sequence, `--follow` on the reference answer, `--top-probs 20`.

Scoring (`scripts/score.py`): per step, llama.cpp GPU's argmax and top-2 gap, the engine's argmax, top-20 overlap, and
KL(llama GPU || engine) over llama.cpp's top 20 plus one bucket for the rest. The floor on the same positions is the
same bucketed KL between llama.cpp's GPU and CPU runs (the full-vocabulary KL is reported beside it; the two differ
by up to 2x because the bucket treatment inflates both sides alike, so the gate compares like with like).

### 3.1 UD-Q3_K_M (17.1 GB, draft block in the file)

Per set, steps-weighted; per sequence in `scores/qwen36-q3km/<arm>/summary.md`. T1 = argmax equal at every position
where llama.cpp GPU's top-2 gap is 0.5 nats or more; T2 = mean KL within 1.5x the floor.

| Arm | Set | Steps | Top-1 agree | Floor top-1 | KL top20 | Floor | Ratio | T1 failures | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base (`--no-draft --lookup 0 --window 1`) | code | 724 | 0.990 | 0.993 | 0.00154 | 0.00131 | 1.18 | 1 | pass |
| | long | 768 | 0.982 | 0.983 | 0.00972 | 0.01046 | 0.93 | 1 | pass |
| | realtext | 510 | 0.971 | 0.971 | 0.01234 | 0.01356 | 0.91 | 0 | pass |
| | short | 974 | 0.988 | 0.991 | 0.00313 | 0.00387 | 0.81 | 1 | pass |
| draft (draft block, lookup 3, window 8) | code | 724 | 0.990 | 0.993 | 0.00154 | 0.00131 | 1.18 | 1 | pass |
| | long | 768 | 0.986 | 0.983 | 0.00959 | 0.01046 | 0.92 | 1 | pass |
| | realtext | 510 | 0.971 | 0.971 | 0.01234 | 0.01356 | 0.91 | 0 | pass |
| | short | 974 | 0.988 | 0.991 | 0.00309 | 0.00387 | 0.80 | 1 | pass |
| kvq8 (base + `--kv q8_0`) | code | 724 | 0.989 | 0.993 | 0.00138 | 0.00131 | 1.05 | 0 | pass |
| | long | 768 | 0.987 | 0.983 | 0.01123 | 0.01046 | 1.07 | 1 | pass |
| | realtext | 510 | 0.975 | 0.971 | 0.01282 | 0.01356 | 0.95 | 0 | pass |
| | short | 974 | 0.990 | 0.991 | 0.00328 | 0.00387 | 0.85 | 1 | pass |
| pb512 (base + `--prompt-batch 512`) | long | 768 | 0.986 | 0.983 | 0.01081 | 0.01046 | 1.03 | 2 | pass |
| | realtext | 510 | 0.982 | 0.971 | 0.01216 | 0.01356 | 0.90 | 0 | pass |

Per sequence, two of 16 base-arm sequences have a ratio above 1.5 (d31k 1.70 at KL 0.00097 against 0.00057; p07
1.51 at 0.00080 against 0.00053): small absolute values on a small denominator; every set passes.

**T1, read with the floor.** Of 2,700 positions with a gap of 0.5 nats or more, the base arm disagrees with llama.cpp
GPU at 3. At those same 3 positions (d4k step 96, p00 step 1, p00 step 39) llama.cpp's own CPU run disagrees with its
GPU run, and the engine sides with the CPU run at d4k 96 and p00 39 (kvq8 at p00 1). So the criterion "100 % at 0.5
nats" is not met by the reference against itself (3 of 2,700), and the engine-only disagreements, where both reference
runs agree, are: base and draft, puzzle step 144 (finding 3); kvq8, none; pb512, d16k step 12 (the engine at 0.499 /
0.497 between two tokens the references put at 0.68 / 0.31). In the band 0.2 to 0.5 nats the base arm agrees at 140
of 145.

**T0, draft on against off (finding 2).** `draft/<seq>.top.txt` must equal `base/<seq>.top.txt` byte for byte. It
does for 11 of 16 sequences and differs for d4k, d16k, d31k, p02 and p08 from the first window of five or more tokens
on (probe: `probes/draft-nographs/README.txt`). The draft arm's scores against llama.cpp are the base arm's to three
digits, so the option costs nothing measurable at T1/T2; the bitwise claim does not hold.

**Chunk effect (plan 3.3 last paragraph).** Step 0, the prompt path alone, bucketed KL against llama.cpp GPU:
d4k 0.0044 (base) / 0.0046 (pb512), floor 0.0045; d16k 0.0002 / 0.0005, floor 0.0011; d31k 0.0022 / 0.0070, floor
0.0043; r16k 0.0002 / 0.0001, floor 0.0002. KL(base || pb512) at step 0: 0.0007, 0.0008, 0.0022, 0.00004. Upstream's
figure for `strata-q36` was 0.0036 to 0.0042.

### 3.2 UD-IQ4_XS (18.2 GB, draft block in the file)

Same procedure, its own reference answers (`inputs/*/*.answer.qwen36-iq4xs.ids`), arms base and draft
(`scores/qwen36-iq4xs/<arm>/summary.md`).

| Arm | Set | Steps | Top-1 agree | Floor top-1 | KL top20 | Floor | Ratio | T1 failures | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | code | 724 | 0.992 | 0.985 | 0.00131 | 0.00213 | 0.61 | 0 | pass |
| | long | 768 | 0.979 | 0.974 | 0.01761 | 0.01985 | 0.89 | 1 | pass |
| | realtext | 510 | 0.976 | 0.973 | 0.01416 | 0.01402 | 1.01 | 1 | pass |
| | short | 970 | 0.993 | 0.991 | 0.00236 | 0.00289 | 0.82 | 0 | pass |
| draft | code | 724 | 0.992 | 0.985 | 0.00127 | 0.00213 | 0.59 | 0 | pass |
| | long | 768 | 0.978 | 0.974 | 0.02681 | 0.01985 | 1.35 | 2 | pass |
| | realtext | 510 | 0.976 | 0.973 | 0.01416 | 0.01402 | 1.01 | 1 | pass |
| | short | 970 | 0.993 | 0.991 | 0.00236 | 0.00289 | 0.82 | 0 | pass |

Top-1 agreement is at or above the floor in every set; T2 passes every set and every sequence (largest per-sequence
ratio 1.46, p09, 23 steps). The reference's own runs disagree at a 0.5-nat margin at 1 of 2,672 positions (puzzle step
271). T1 failures:

- **d4k step 249, gap 1.72 nats** (llama.cpp " M" at 0.51, the engine " requests" at 0.87; draft arm 0.9998). This
  reference answer degenerated into a repetition loop ("...project's own limit of 128 MTP layer is the same as..."),
  and in that region the two reference runs themselves differ by a KL of 0.77, 1.10 and 1.25 at steps 212, 233 and
  234 and 0.34 at step 249, against 0.001 to 0.01 elsewhere: the model is in a regime where every implementation's
  rounding is amplified. The gap criterion assumes near-ties are the only noise, which this sequence breaks. Reported,
  and read as a property of the sequence; the draft arm's long-set KL (ratio 1.35 against 0.89) is this sequence too,
  where the suffix lookup fires on every repeat and keeps the windows long (finding 2).
- **r16k step 440, gap 0.52**: llama.cpp GPU 0.255 / 0.151, CPU 0.189 / 0.137, the engine 0.139 / 0.150: a near-tie
  for the engine at the edge of the margin.
- **draft only, d16k step 242, gap 0.55**: GPU 0.58 / 0.33, CPU 0.89 / 0.10, the engine base 0.53 / 0.46, draft
  0.37 / 0.62: the long-window path (finding 2) moves a close pair across.

T0 (draft against base): 6 of 16 sequences differ (d4k, d16k, d31k, lru, p02, puzzle), finding 2 again.

## 4. Configuration A: `strata`, Qwen3.8-Flash-Next IQ3_XXS (plan 3.4)

_(filled when chain-a finishes: reference feasibility on this box, strata arms)_

## 5. Findings

1. **`poly_expert_parity` on UD-Q3_K_M fails its bound on one of twelve experts** (`parity/poly_expert_parity_q3km/`):
   blk.34 expert 128, IQ3_XXS gate/up with Q6_K down, CPU path relative error 0.0513 against the program's 0.05; the
   other eleven are 0.039 to 0.048 on the CPU path and 0.013 to 0.021 on the GPU path, and every "two in a launch"
   check is bitwise. The CPU path is `cpu_experts` through ggml-cpu's `vec_dot` with Q8_K activations, llama.cpp's own
   CPU arithmetic, against a double-precision product of the dequantized weights; the GPU path (q8_1 activations) is
   far inside. Reading: the program's bound is tight for a two-matrix chain with 8-bit activations and ggml-cpu's own
   rounding crosses it on this expert; no kernel the 24 GB or 48 GB configurations run is implicated (no CPU expert
   runs there). Per plan section 4: a ticket, and the test's bound is the thing to question.
2. **The draft block's T0 claim does not hold for windows of five or more tokens** (`probes/draft-nographs/`): with
   `--lookup 0` (draft block alone, window at most 4) and with `--window 2/3/4`, the per-step distributions equal the
   single-token path's bytes; with the default lookup 3 and window 8, or `--no-draft --lookup 3 --window 8`, they
   differ from the first long window on; `--no-graphs` changes nothing. The kernel that behaves differently above four
   rows is not located (plan 3.7 step 5). Per plan section 4: the README's bitwise claim comes out; speculation is
   reported as a T2-gated option (it passes, see 3.1).
3. **One T1 failure where both reference runs agree**: code/puzzle step 144 (thinking on), llama.cpp GPU 5435 at 0.53
   over 1781 at 0.25 (gap 0.76 nats), CPU 5435 over 1781 at 0.69 nats, the engine 1781 at 0.42 over 5435 at 0.38
   (`probes/puzzle-144/README.txt`). Step 0 is identical for every variant (the prompt path is not it);
   `--prompt-batch 16` and `--no-gpu-experts` variants agree with llama.cpp at that step but are different paths over
   144 steps; the mean KL of every engine variant over those steps is 1.4 to 1.5x the floor. Reading: decode-path
   rounding compounding through the recurrent GDN state along a long thinking answer, landing on a 0.7-nat margin.
   Localizing it to a kernel needs per-layer vectors from `strata-poly` (plan 5.3 b).

## 6. Not covered on this box

- The CPU and PCIe expert tiers of both engines (every expert resident on 48 GB): B arm 5 and the tier parts of A's
  arms are for a 24 GB or smaller card.
- `poly_attend_test` runs at head dim 64, not Qwen3.6's 256 (plan 2.3).
- Flash-Next: see section 4.

## 7. Files

`inputs/` (ids and lengths), `inputs-src/`, `reference/<model>/` (`.gen.txt` greedy ids, `.full.sha256`,
`.top20.tsv`, `command.sh`, `.log`), `parity/`, `poly/<model>/<arm>/` (`command.sh`, `.log`, `.ids.txt`; the
`.top.txt` distributions stay on the VM), `scores/<model>/<arm>/` (`summary.md`, per-sequence `.tsv` and `.json`),
`probes/`, `files/`, `scripts/`.
