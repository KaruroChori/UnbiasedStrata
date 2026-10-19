# Step 12: correctness of the engines against llama.cpp at 3cf03257

PLAN.md step 12, the checks of `docs/CORRECTNESS-PLAN.md` (step 11, signed off 2026-10-18). Run 2026-10-18 on the
A6000 VM (NVIDIA RTX A6000 48 GB, driver 550.163.01, CUDA 12.4; AMD Ryzen 7 1700, 12 threads given to the VM, AVX2;
50 GB RAM), not on the RTX 3090 pod the plan was written for: the pod was unreachable that day and the VM holds every
file of both configurations (`docs/MODEL-FILES.md`). The A6000 is the same architecture as the 3090 (sm_86), so the
kernels under test are the pod's; what differs is the memory: every Qwen3.6 expert is resident on the 48 GB card (no
CPU or PCIe tier for `strata-poly`), and Flash-Next's 24,576 experts fit it only just, so `strata`'s tiers ran as
explicit arms with a fixed, smaller cache (section 4) and not in the 24 GB pattern (section 6).

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

### 3.3 `--check-batch 4` (plan run order step 6)

`scripts/check-batch.sh`: for each short prompt, `strata-poly --tokens … --batch 4 --check-batch 4 --max-new 64`
answers the prompt and the prompt without its first 1, 2 and 3 tokens on their own and then the four together in
their own sequences; exit 1 on a differing token. Both files, 10 prompts each: every run exits 0, "the first 64 of 64
tokens as on its own" for all four sequences (`checkbatch/<model>/<seq>.log`, `logs/check-batch.out`).

## 4. Configuration A: `strata`, Qwen3.8-Flash-Next IQ3_XXS (plan 3.4)

**Reference.** The 76 GB GGUF (47.0 GB of layers, the 28.8 GB n-gram shard) does not fit the card, so the "GPU" run
is a partial offload: `STRATA_DUMP_NGL=28`, 28 of 48 layers on the card (28.6 GB; `scripts/chain-a.sh` probed 28
first and it fit), the other 20 on ggml-cpu, ubatch 4096. The CPU run is `--ngl 0` at 12 threads, alone on the box
(beside `strata --serve` it was RAM-starved, the 76 GB going through what was left of a 50 GB page cache): 46 to
69 s per short sequence, lru 135 s, puzzle 116 s, d4k 560 s, d16k 2,117 s, r16k 2,238 s, d31k 4,376 s
(`logs/ref-flash-next-cpu.out`). The thread count moves no bits (`probes/cpu-threads/`: 4 and 12 threads give the
same sha256). The reference's answers are its own greedy ones (`inputs/*/*.answer.flash-next.ids`; the real-text
answer is fixed).

**Floor.** 3,282 positions, 2,882 with a top-2 gap of 0.5 nats or more; llama.cpp's CPU run disagrees with its
partial-GPU run at 1 of them (d16k step 254, gap 1.18). Full-vocabulary KL(GPU || CPU), mean by set: short 0.00256,
code 0.00074, long 0.00778, realtext 0.00925 (the bucketed floors the gate uses are in the table).

**Engine arms** (`scripts/strata-run.py`): a fresh `strata --serve` per sequence with the VM's step-6 line
(`--resident-experts --ple-io mmap --prefill auto --spec 4 --spec-min-p 0.5 --mtp … --max-context 65536`) plus
`--prompt-cache 0 --adapt-every 0 --pcie-frac 0.55`, and `STRATA_LOGPOS` (every position read through the verify
windows, top 20 log-probabilities), `STRATA_LOGPOS_TOPK=20`, `STRATA_ROUTE_TAIL_SKIP=0`, `STRATA_PREFILL_CPU_SHARE=0`,
`STRATA_IQ_MT_MIN=1`. `--short-read 4096` sends a whole read of at most 4,096 tokens through the windows; a longer
sequence goes as two requests, the prompt alone (`--prompt-cache 1`, read through the batched prompt path) and then
prompt + answer, which resumes and reads only the answer through the windows (`generate.cpp` `windows_ok`). That is
also how a chat reaches the answer positions. A resumed read loses step 0, so those rows are answer[1:]
(`strata/<arm>/<seq>.offset.txt`; `scripts/realign.py`).

| Arm | Flags on top of the line | Sequences |
| --- | --- | --- |
| fp16 | `--kv fp16`, suffix drafter on (windows of 6) | all 16 |
| t4 | fp16 + `--suffix-draft 0` (windows of 4) | all 16 |
| int8 | `--kv int8` | all 16 |
| int8str | `--kv int8 --kv-resident 20480 --short-read 1024` (the tail streamed) | d31k |
| pf512 | fp16 + `--prefill 512 --short-read 512` (prompt chunks of 512) | long set, r16k |
| pin | fp16 + `--expert-cache 24380`: every one of the 24,576 experts on the card (finding 4) | all 16 |
| cpu | fp16 + `--expert-cache 16000 --pcie-frac 0`: 21,311 experts on the card, 3,265 (8.6 GiB) in RAM, every miss computed by the CPU pool (the CPU expert tier, AVX-2 kernels) | all 16 |
| pcie | as cpu with `--pcie-frac 1`: every miss fetched over PCIe and computed on the GPU | p00 p01 lru puzzle d4k |
| pin2, pint4, pingpu, pincpu, cpu2 | T0 repeats: pin again; pin + `--suffix-draft 0`; pin + `--pcie-frac 1`; pin + `--pcie-frac 0` (all 16); cpu again | 5 (pincpu: 16) |

### 4.1 Scores

Per set, steps-weighted (`scores/flash-next/<arm>/summary.md` has every sequence). The long set has 765 steps, not
768: the three resumed reads lose step 0.

| Arm | Set | Steps | Top-1 agree | Floor top-1 | KL top20 | Floor | Ratio | T1 failures | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fp16 | code | 724 | 0.997 | 0.997 | 0.00057 | 0.00080 | 0.71 | 0 | pass |
| | long | 765 | 0.953 | 0.949 | 0.01594 | 0.01788 | 0.89 | 1 | pass |
| | realtext | 509 | 0.921 | 0.943 | 0.01424 | 0.01674 | 0.85 | 0 | pass |
| | short | 1280 | 0.992 | 0.990 | 0.00336 | 0.00469 | 0.72 | 0 | pass |
| t4 | code | 724 | 0.997 | 0.997 | 0.00058 | 0.00080 | 0.72 | 0 | pass |
| | long | 765 | 0.962 | 0.949 | 0.01547 | 0.01788 | 0.87 | 1 | pass |
| | realtext | 509 | 0.945 | 0.943 | 0.01484 | 0.01674 | 0.89 | 0 | pass |
| | short | 1280 | 0.994 | 0.990 | 0.00369 | 0.00469 | 0.79 | 1 | pass |
| int8 | code | 724 | 0.999 | 0.997 | 0.00059 | 0.00080 | 0.73 | 0 | pass |
| | long | 765 | 0.959 | 0.949 | 0.01604 | 0.01788 | 0.90 | 0 | pass |
| | realtext | 509 | 0.923 | 0.943 | 0.01531 | 0.01674 | 0.91 | 0 | pass |
| | short | 1280 | 0.991 | 0.990 | 0.00416 | 0.00469 | 0.89 | 1 | pass |
| int8str | long (d31k) | 255 | 0.973 | 0.965 | 0.00259 | 0.00245 | 1.06 | 0 | pass |
| pf512 | long | 765 | 0.958 | 0.949 | 0.01479 | 0.01788 | 0.83 | 0 | pass |
| | realtext | 509 | 0.931 | 0.943 | 0.01475 | 0.01674 | 0.88 | 0 | pass |
| pin | code | 724 | 0.996 | 0.997 | 0.00063 | 0.00080 | 0.78 | 0 | pass |
| | long | 765 | 0.957 | 0.949 | 0.01676 | 0.01788 | 0.94 | 3 | pass |
| | realtext | 509 | 0.931 | 0.943 | 0.01444 | 0.01674 | 0.86 | 0 | pass |
| | short | 1280 | 0.996 | 0.990 | 0.00428 | 0.00469 | 0.91 | 1 | pass |
| cpu | code | 724 | 0.999 | 0.997 | 0.00056 | 0.00080 | 0.70 | 0 | pass |
| | long | 765 | 0.956 | 0.949 | 0.01527 | 0.01788 | 0.85 | 0 | pass |
| | realtext | 509 | 0.931 | 0.943 | 0.01438 | 0.01674 | 0.86 | 0 | pass |
| | short | 1280 | 0.991 | 0.990 | 0.00402 | 0.00469 | 0.86 | 0 | pass |
| pcie | code | 724 | 0.996 | 0.997 | 0.00063 | 0.00080 | 0.78 | 0 | pass |
| | long (d4k) | 255 | 0.945 | 0.953 | 0.03109 | 0.03473 | 0.90 | 1 | pass |
| | short (p00, p01) | 256 | 0.996 | 0.988 | 0.00303 | 0.00450 | 0.67 | 0 | pass |

**T2** passes every set in every arm, 0.67 to 0.94x the floor. Per sequence, d31k is above 1.5 in three arms (fp16
1.79, pin 1.89, cpu 1.59; t4 1.03, int8 1.06, pf512 0.46) at a KL of 0.0025 to 0.0046 against a floor of 0.0025: the
smallest numbers of the run, where which experts were on the card (finding 4) moves the ratio by a factor of two.
Top-1 agreement is at or above the floor in every set but realtext, where every arm except t4 is 1 to 2 points under
it (0.921 to 0.931 against 0.943) with no T1 failure: the disagreements are below the 0.5-nat margin.

**T1, read with the floor.** Of about 2,880 positions with a 0.5-nat margin, the arms disagree with llama.cpp GPU at
0 (int8str, pf512, cpu), 1 (fp16, int8), 2 (t4) or 4 (pin). One of pin's is the position where llama.cpp's CPU run
also disagrees (d16k step 254). The other six, all with both reference runs agreeing, are each a close pair that the
engine puts within a few hundredths of each other, and each flips in some arms and not in others
(`scores/flash-next/<arm>/<seq>.tsv`; the figures are from the committed `.top20.tsv` and `.scored.tsv`):

| Position | llama.cpp GPU | llama.cpp CPU | Engine, the arms that fail | The arms that agree |
| --- | --- | --- | --- | --- |
| d4k 55, gap 0.55 | 1510 0.31 / 11626 0.18 | agrees | pin family and pcie: 11626 0.36 / 1510 0.22 | fp16 0.32 / 0.11, t4, int8, cpu |
| d4k 148, gap 0.66 | 15 0.29 / 7154 0.14 | 15 0.23 / 7154 0.19 | t4: 7154 0.23 / 15 0.20 | fp16 0.23 / 0.20, pin 0.35 / 0.11, int8, cpu |
| d4k 248, gap 0.66 | 220 0.28 / 423 0.14 | 220 first, 20934 second | fp16: 20934 0.152 / 220 0.151 | pin 0.21 / 0.13, int8, t4 |
| d16k 206, gap 1.04 | 5893 0.32 / 1765 0.11 | 5893 0.21 / 1765 0.12 (gap 0.57) | pin, pincpu: 1765 0.19 / 5893 0.16 | fp16 0.22 / 0.17, t4, int8, cpu 0.27 / 0.14 |
| p06 104, gap 0.97 | 248046 0.73 / 198 0.27 | 0.60 / 0.40 (gap 0.39) | t4: 198 0.55 / 248046 0.45 | fp16 0.56 / 0.44, pin 0.51 / 0.49, int8, cpu |
| p07 92, gap 0.52 | 248045 0.62 / 248046 0.37 | 0.64 / 0.34 | pin, pincpu, int8: 248046 0.50 / 248045 0.49 | fp16 0.53 / 0.46, t4 0.57 / 0.41, cpu |

Reading: at these positions the engine's two candidates sit closer together than the reference's (0.5 / 0.5 against
0.6 / 0.4; 0.19 / 0.16 against 0.32 / 0.11), and the reference's own two runs move the margin by up to 0.6 nats at
two of them (d16k 206, p06 104). No position fails in every arm, the cpu arm fails none, and T2 holds in every set,
so these are not a systematic bias; they are more of them than configuration B had (one engine-only position), on a
model whose reference is itself a mixed CPU/GPU run. Finding 5, ticketed, with the plan's section 4 reading: a wrong
token at a margin is a bug to localize (plan 3.7) before the README claims more than "same output as upstream".

### 4.2 T0, bitwise

Rows compared: every `pos.tsv` field but the position (target id and its log-probability, the argmax and its
log-probability, the agreement flags, the 20 log-probabilities). `probes/placement/README.txt` has the full list.

| Claim | Arms | Rows | Differing |
| --- | --- | --- | --- |
| A second process gives the same bytes | pin vs pin2, 5 sequences | 5,507 | 0 |
| The window size changes no bits (6/5/1 against 4/3/1) | pin vs pint4 | 5,507 | 0 |
| The PCIe share has nothing to act on when every expert is on the card | pin vs pingpu, pin vs pincpu | 5,507 each | 0 |
| Streamed KV equals resident KV | int8str vs int8, d31k | 255 | 0 |
| The CPU tier repeats | cpu vs cpu2 | 5,507 | 0 |
| A fetched expert equals a cached one | pcie vs pin | 5,507 | 18 (p01, positions 143-160, 7th significant digit) |
| Two processes with `--expert-cache auto` | fp16 vs t4 | 16 sequences | 15 sequences differ, puzzle (24541 vs 24543 slots) none |

So: with the expert placement held, `strata` is deterministic across processes, window sizes and KV streaming, and
the CPU tier is deterministic too; the PCIe path is bitwise the cache-hit path on 4 of 5 sequences and not on the
fifth (finding 6); and without the placement held, two starts of the same line differ (finding 4).

**Chunk effect.** Step 0 is not visible for the long sequences (the resumed read loses it), so pf512's prompt-chunk
effect is read from the whole answer: its long-set KL is 0.01479 against fp16's 0.01594 and d31k's 0.00114 against
0.00440, inside the floor either way.

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
4. **`strata`'s bits depend on the free VRAM at start** (`probes/placement/README.txt`). `--expert-cache auto` (also
   under `--resident-experts`) sizes the GPU expert cache from the VRAM free when the engine starts; on this card that
   was 40.5 to 41.6 GiB depending on what else sat on it (the CPU reference's CUDA context beside the fp16 arm, nothing
   beside the int8 arm), giving 24,380 to 24,576 of Flash-Next's 24,576 experts on the card. The ones left over sit in
   RAM and each miss is split by `--pcie-frac` between the GPU (over PCIe) and the CPU pool, which rounds an expert
   differently (upstream says so: `docs/DETAILS.md`, #410). So two processes with the same flags gave different
   log-probabilities at nearly every position (fp16 vs t4), and the same two gave identical ones once the cache held
   every expert (pin vs pint4). On a 24 GB card, where about half the experts miss, the answer to a prompt depends
   on the VRAM headroom at start through this path; `--pcie-frac 0` or `1` removes the split but not the
   dependence on the slot count; a fixed `--expert-cache N` removes both. Ticket USTRAT-4.
5. **Flash-Next T1 flips** (section 4.1): six positions with a 0.5 to 1.0-nat margin where some arms put the
   reference's second token first, none in every arm, none in the cpu arm; T2 holds. Ticket USTRAT-5; the plan's
   3.7 (per-layer vectors against the dump tool's captures) is the way to name a kernel.
6. **The PCIe-fetched expert is not bitwise the cached one everywhere**: pcie vs pin, 18 of 161 rows on p01 from
   position 143 differ in the 7th significant digit, 0 of 5,346 rows on the other four sequences. Not located; folded
   into USTRAT-4.

## 6. Not covered on this box

- `strata-poly`'s CPU expert tier (plan B arm 5): every Qwen3.6 expert is resident on 48 GB.
- `strata`'s tiers in the 24 GB pattern: here the CPU tier ran with 13 % of the experts in RAM at a fixed cache and
  every miss on the CPU (cpu arm, 0 T1 failures, T2 pass), the PCIe tier on 5 sequences (pcie arm); on the pod about
  half the experts miss, the adaptive swaps are on and the PCIe share is refined at run time.
- The Flash-Next "GPU" reference is a partial offload (28 of 48 layers on the card): the attention and GDN of 20
  layers ran on ggml-cpu on both reference sides.
- `poly_attend_test` runs at head dim 64, not Qwen3.6's 256 (plan 2.3).
- Prompt-path rows for the long sequences (step 0 of a resumed read is lost); the chunk effect is read from the
  answers.

## 7. Files

`inputs/` (ids and lengths), `inputs-src/`, `reference/<model>/` (`.gen.txt` greedy ids, `.full.sha256`,
`.top20.tsv`, `command.sh`, `.log`; the f32 `.full` files stay on the VM), `parity/`, `poly/<model>/<arm>/`
(`command.sh`, `.log`, `.ids.txt`; the `.top.txt` distributions stay on the VM), `strata/<arm>/` (`command.sh`,
`.engine.log`, `.done.txt`, `.scored.tsv` + `.offset.txt`; see `strata/README.txt`), `scores/<model>/<arm>/`
(`summary.md`, per-sequence `.tsv` and `.json`), `checkbatch/` (section 3.3), `probes/`, `files/`, `scripts/`,
`logs/` (the chains' stdout).

## 8. `strata-poly`, DeepSeek V4 Flash UD-IQ2_XXS and GLM 5.3 Flash 3.0bit (2026-10-19)

The step-12 procedure (sections 1 and 3) on the two large families the fork serves, on a RunPod box with two RTX PRO
6000 Blackwell Server cards (96 GB each, CUDA arch 120), a Xeon 6952P under an 81.6-core cgroup quota and 1.5 TB of RAM.
Everything was downloaded fresh from Hugging Face (`tools/pod/bringup.sh`'s repositories and revisions; SHA-256 in
`docs/MODEL-FILES.md`); the fork is f499b8cf (`src/poly/main.cpp` and the dump tool take `@FILE` id lists, nothing on
the serve path changed). A first run on a 2x B200 pod the same day was lost with the pod (terminated mid-run, results
unpulled); this run restarted from scratch with the chain scripts versioned in `pod/` (`pod/README.md`).

**Inputs.** The same source texts as the Qwen sets (`inputs-src/`), tokenized per model through the front end's
`/apply-template` and `/tokenize` (`scripts/make-inputs-model.py`): DeepSeek `<｜begin▁of▁sentence｜><｜User｜>…<｜Assistant｜><think>`,
GLM `[gMASK]<sop><|user|>…<|assistant|><think>`. Sets: short p00-p09 (128 steps), code lru (400) and puzzle (324),
long d4k/d16k/d31k (256), realtext r16k (15,874 prompt tokens, the fixed 510-token answer). `inputs-deepseek/`,
`inputs-glm/`.

**References.** DeepSeek: the pinned llama.cpp 3cf03257 (it knows `deepseek4`), `/opt/llamacpp-ref`. GLM: the pinned
tree does not know `glm5-next`, so its reference is llama.cpp master 99db719bdf07f7d537431ca556a0512bf3d995b6
(2026-10-19) built the same way with the same dump tool (`/opt/llamacpp-master`; the fork's `third_party/llama.cpp`
patch does not touch inference). Master's dump tool aborts in `sched_reserve` when CUDA sees no device, so its CPU run
keeps a card visible. The GPU run is `--ngl 99` over both cards (llama.cpp's own layer split; neither model fits one
card with its KV at 31K), 16-49 s a sequence; the CPU run is `--ngl 0` at 40 threads, 30 s (short) to 413 s (r16k,
DeepSeek). Answers are each reference's own greedy ones (`inputs-<fam>/*/*.answer.<fam>.ids`), the real-text answer
fixed. Full f32 logits stayed on the pod; `reference/<fam>/` has the top-20 extracts, checksums, generated ids,
commands and forced-id files.

**Floors.** DeepSeek: 3,282 positions, 2,943 with a top-2 gap of 0.5 nats or more, llama.cpp's CPU run disagrees with
its GPU run at 9 of them (p04 18, p05 41, p06 126, p07 127, p09 17 and 60, puzzle 124 and 285, r16k 445). GLM: 2,878
margin positions, 14 disagreements (d4k 95, lru 204 and 307, p00 122, p02 116 and 117, p03 78, p04 76, p06 81, p08 24,
p09 40 and 56, two more). Full-vocabulary KL(GPU || CPU), mean by set: DeepSeek short 0.00726, code 0.00443, long
0.00430, realtext 0.00662; GLM short 0.00848, code 0.00884, long 0.00530, realtext 0.00446. Both floors are several
times the Qwen ones (section 3: short 0.0029 to 0.0039 bucketed) and GLM's 14 flips against Qwen's 1 say the same:
llama.cpp's own CPU and GPU kernels sit further apart on these architectures, so the gate is correspondingly looser.

**Arms** (`scripts/poly-run.py`, `STRATA_FREEZE_EXPERTS=1`, GPU 0 alone): base (`--tail-skip 0 --no-draft --lookup 0
--window 1`), draft (`--tail-skip 0`, the draft block where the file has one, lookup 3, window 8), pb512 (base +
`--prompt-batch 512`, long set and r16k). kvq8 is not run: `--kv q8_0` is implemented for the qwen35moe path only.
DeepSeek holds every expert on the card (11,008 of 11,008, 78.2 GiB); GLM holds 10,167 of 12,096 (83.9 GiB) and
computes about 16 % of expert reads on the CPU. A sequence stops at the answer's first end token (the engine stops
when the forced token is an end token, as the reference's answers run on past it), identical in every arm: short set
908 of 1,280 steps for DeepSeek, 942 for GLM, the other sets complete.

### 8.1 Scores

Per set, steps-weighted (`scores/<fam>/<arm>/summary.md` has every sequence).

| Model | Arm | Set | Steps | Top-1 agree | Floor top-1 | KL top20 | Floor | Ratio | T1 failures | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek | base | code | 724 | 0.981 | 0.983 | 0.00305 | 0.00445 | 0.69 | 1 | pass |
| | | long | 768 | 0.987 | 0.988 | 0.02501 | 0.02611 | 0.96 | 0 | pass |
| | | realtext | 510 | 0.961 | 0.959 | 0.06739 | 0.06771 | 1.00 | 0 | pass |
| | | short | 908 | 0.979 | 0.980 | 0.00627 | 0.00744 | 0.84 | 2 | pass |
| | draft | code | 724 | 0.981 | 0.983 | 0.00305 | 0.00445 | 0.69 | 1 | pass |
| | | long | 768 | 0.987 | 0.988 | 0.02444 | 0.02611 | 0.94 | 0 | pass |
| | | realtext | 510 | 0.961 | 0.959 | 0.06739 | 0.06771 | 1.00 | 0 | pass |
| | | short | 908 | 0.979 | 0.980 | 0.00627 | 0.00744 | 0.84 | 2 | pass |
| | pb512 | long | 768 | 0.991 | 0.988 | 0.02316 | 0.02611 | 0.89 | 0 | pass |
| | | realtext | 510 | 0.967 | 0.959 | 0.07173 | 0.06771 | 1.06 | 1 | pass |
| GLM | base | code | 724 | 0.975 | 0.977 | 0.00810 | 0.00890 | 0.91 | 5 | pass |
| | | long | 768 | 0.973 | 0.980 | 0.01832 | 0.01621 | 1.13 | 1 | pass |
| | | realtext | 510 | 0.967 | 0.976 | 0.02674 | 0.02963 | 0.90 | 1 | pass |
| | | short | 942 | 0.972 | 0.965 | 0.00969 | 0.00964 | 1.01 | 0 | pass |
| | draft | code | 724 | 0.979 | 0.977 | 0.00862 | 0.00890 | 0.97 | 4 | pass |
| | | long | 768 | 0.978 | 0.980 | 0.01773 | 0.01621 | 1.09 | 2 | pass |
| | | realtext | 510 | 0.965 | 0.976 | 0.02750 | 0.02963 | 0.93 | 2 | pass |
| | | short | 942 | 0.977 | 0.965 | 0.00921 | 0.00964 | 0.96 | 1 | pass |
| | pb512 | long | 768 | 0.980 | 0.980 | 0.01445 | 0.01621 | 0.89 | 2 | pass |
| | | realtext | 510 | 0.963 | 0.976 | 0.03020 | 0.02963 | 1.02 | 0 | pass |

**T2** passes every set in every arm: DeepSeek 0.69 to 1.06x the floor, GLM 0.89 to 1.13x. Top-1 agreement is within
a point of the floor's everywhere, above it on GLM's short set and DeepSeek's pb512 sets.

**T1, read with the floor.** DeepSeek base and draft (the same three positions): p03 75 (gap 0.59) and 103 (1.43),
puzzle 10 (0.59), at all three both reference runs agree and the engine puts the reference's second token first; the
engine's KL at those positions is 0.04 to 0.18 against a floor of 0.002 to 0.11. pb512's one, r16k 445 (0.51), is a
position where llama.cpp's CPU run also disagrees with its GPU run. GLM base: d4k 95 and lru 307 are reference-spread
positions (the floor's own KL there is 0.98 and 0.70); the other five (lru 360 gap 1.03, puzzle 238 0.79, 262 0.94, 267
0.68, r16k 22 0.53) have both references agreeing. GLM draft fails at nine, four of them the same as base (d4k 95, lru
360, puzzle 267, r16k 22) and five of its own (d4k 96, p06 95, puzzle 159 and 233, r16k 430), which is what the
draft arm's different expert placement does (8.2). pb512 on GLM: d4k 95 (reference spread) and d4k 252 (0.67).
Nothing fails in every arm but the three DeepSeek positions, which are the same computation in base and draft (the
arms are bitwise equal there, 8.2). As for Qwen (findings 3 and 5): near ties by the margin's standard, no systematic
bias (T2), and naming a kernel needs per-layer vectors. Ticket USTRAT-10.

### 8.2 T0, bitwise

`draft/<seq>.top.txt` against `base/<seq>.top.txt` (`logs/2026-10-19/t0-<fam>.out`, `pod/t0-floor-analysis.py`).

- **DeepSeek: 15 of 16 identical.** The file has no draft block, so the draft arm is the n-gram lookup alone; it
  guessed on 11 sequences (3 to 139 accepted guesses each) and the bytes still match on all of them but d4k, which
  diverges from step 112 of 256 (139 of 196 guesses accepted over the run; the largest differences 0.05 in
  log-probability, every argmax the same). That is finding 2 again: lookup windows of five or more tokens change the
  bits, shorter ones do not.
- **GLM: 0 of 16 identical, from step 0, including p04 and p09 where the draft arm made no guess at all.** The cause is
  placement, not drafting: the draft block takes 0.4 GiB of the card, the engine keeps 10,115 instead of 10,167 experts
  in VRAM, and the 52 that moved are computed by the CPU in one arm and the GPU in the other, which round differently
  (finding 4's mechanism, now on `strata-poly`). Per step the two arms differ by up to 0.05 to 0.50 in log-probability
  and the argmax moves on 0 to 11 steps a sequence (lru 5 of 400, puzzle 11 of 324, r16k 21 of 510), inside T2 in both.
  A clean T0 for the GLM draft block needs the same expert set in both arms (an explicit expert count, or a card that
  holds all 12,096). Ticket USTRAT-9.

### 8.3 Reference drift (llama.cpp master against the pinned commit, DeepSeek)

`pod/probe-master-cpu.sh`, `pod/probe-master-tab.py`: llama.cpp master 99db719b (the GLM reference build) run `--ngl 0` on DeepSeek's short and code sequences (p01-p09, lru, puzzle; 1,876 steps), teacher-forced on the pinned run's answers, against the pinned 3cf03257 GPU and CPU runs (`reference/deepseek-master/`, `logs/2026-10-19/probe-master-tab.out`). Mean full-vocabulary KL: pinned GPU || pinned CPU (the floor) 0.01044; pinned GPU || master CPU 0.00996; pinned CPU || master CPU 0.00992. Top-1 agreement 0.979 (floor), 0.973, 0.977. At the 1,732 margin positions master's argmax leaves the pinned GPU's at 8 (p03 1, p06 2, p07 1, p09 2, puzzle 2), where the pinned CPU run leaves it at 8 on the same eleven sequences and the engine (16 sequences, 2,943 positions) at 3. Reading: two builds of llama.cpp four months apart disagree with each other on this architecture by the same amount as llama.cpp's CPU and GPU kernels do, and a little more than the engine disagrees with either. The floor is a property of llama.cpp, not a constant; a correctness claim for DeepSeek has to name the llama.cpp commit as well as the device. Ticket USTRAT-11 (observation; nothing to fix in the fork).

### 8.4 Not covered here

- A 24 GB-class placement for either model (both ran with most or all experts resident; DeepSeek entirely).
- `--kv q8_0` (qwen35moe only in this engine), the two-card `--layer-split` the pod now serves DeepSeek Q4 with
  (PLAN.md step 18), the CPU expert tier beyond GLM's 16 %.
- The B200 (arch 100) build: its pilot (p00, T2 1.18x, two T1 flips at steps 2 and 18) is not reproduced on this
  arch-120 box, where p00 has no T1 failure in any arm; the pod was terminated before the rest ran.

Files: `inputs-deepseek/`, `inputs-glm/`, `reference/{deepseek,glm}/`, `poly/{deepseek,glm}/<arm>/`,
`scores/{deepseek,glm}/<arm>/`, `logs/2026-10-19/` (chain logs, per-arm outputs, T0 and top-20 derivations, the pod
scripts as run), `pod/`, `scripts/make-inputs-model.py`, `scripts/pull-record-2026-10-19.sh`.
