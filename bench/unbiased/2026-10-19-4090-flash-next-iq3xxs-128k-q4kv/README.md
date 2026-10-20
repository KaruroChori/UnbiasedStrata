# UnbiasedStrata 2 on the homelab RTX 4090: Flash-Next GSQ-RCO IQ3_XXS, 128K context, q4_0 KV, 2026-10-19 UTC

Fork only (no upstream arm), one card, nothing else on it. The purpose of the run: show that the fork, built fresh on
this box, serves a full `strata_bench.py --runs 3 --long` pass plus the sustained supplement at a usable context
without an error, and record the first 4090 numbers. Same client, same record layout as the 24 GB pod record
`bench/unbiased/2026-10-17-3090pod-step9/` (driver `us2-4090-run.py`, a copy here, adapted from `us2-step9-run.py`).

| | |
| --- | --- |
| Box | VM 221 `gpu-llm` (192.168.50.151), Debian, kernel 6.12.111+deb13-amd64, 16 vCPUs of an Intel i9-9900K (8 physical cores on the host), 66.7 GiB RAM |
| Card | NVIDIA GeForce RTX 4090, 24 GiB, driver 550.163.01, CUDA 12.4 |
| Fork | `unbiasedstrata2` at a0443466, cloned from a bundle, `git submodule update --init`, `make build CUDA_ARCHS=89` (`build.log`): `build/bin/{strata,strata-poly,unbiased-strata,libstrata_kq.so}`; `strata` sha256 `720073d8…`, `unbiased-strata` sha256 `ba2cc11a…` (full hashes in `*/provenance.json`) |
| Client | upstream `tools/strata_bench.py --runs 3 --long` from the `strata-upstream` checkout at 477ac13c (tag v0.1.45; the pod used v0.1.45-poly.1), run with the system Python 3.13 (the client is standard library only); its docs and README feed the agent turns, as on the pod |
| Model | ISTA-DASLab `Qwen3.8-Flash-Next-GSQ-RCO-GGUF` IQ3_XXS, two shards, sha256 `219ea929…` and `316b46f3…` (equal to the Hugging Face LFS hashes), with the pack and MTP directories upstream's installer made on 2026-10-05 (`model-checksums.txt`; pack `dense.bin` `d2af3d83…` and mtp `dense.bin` `c724dc0b…` are the files of `docs/MODEL-FILES.md`) |
| Before the run | the Coder IQ1_M `unbiased-strata.service` left from the 2026-10-18 BBW run was stopped, with its memory watchdog and RAM sampler; card at 2 MiB used, 65 GiB RAM available |

## Server command

The README's 24 GB Flash-Next line with three changes: `--max-context 131072` (was 65536), `--kv q4_0` (was `int8`),
`--kv-resident 131072` (was 32768; the engine reports this as `kv_resident=0`, every cell in VRAM, no streaming).
`--sse-ping-interval 10` as in the pod's pi arm.

```
build/bin/unbiased-strata --engine build/bin/strata \
  -m /tank/nvme/strata/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf \
  --host 127.0.0.1 --port 18090 --alias qwen3.8-flash-next-iq3_xxs --sse-ping-interval 10 \
  -- --pack /tank/nvme/strata/pack-iq3-xxs \
     --native /tank/nvme/strata/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf \
     --ple-gguf /tank/nvme/strata/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf \
     --expert-profile /tank/nvme/strata/pack-iq3-xxs/expert-profile.bin \
     --expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mtp /tank/nvme/strata/mtp \
     --max-context 131072 --kv q4_0 --ple-io ram --pool-workers 15 --kv-resident 131072
```

## Choosing the resident KV: two start-only probes (`probe-kvres*/`)

Each probe starts the server, waits for `/health`, sends one 22-token greedy chat request, records the engine's start
lines and stops. `--expert-cache auto` takes what is left after the resident KV.

| `--kv-resident` | engine `kv_resident` | expert cache | ready after | VRAM after load | smoke decode tok/s |
| --- | --- | --- | --- | --- | --- |
| 131072 (chosen) | 0 (all in VRAM) | 10,162 slots, 16,870 MiB | 51 s | 23,782 of 24,564 MiB | 74.1 (21 of 25 drafts accepted) |
| 32768 | 32768 | 10,545 slots, 17,514 MiB | 51 s | 23,782 of 24,564 MiB | 71.7 (22 of 26 drafts accepted) |

Keeping all 128K cells of q4_0 KV on the card costs 383 expert slots (3.6 %) against streaming beyond 32K. For
reference, the pod's 64K int8 configuration with 32K resident had 10,531 slots (17,485 MiB) on the 3090.

## Results (`fork-flash-next-128k-q4kv-kvres131072/`)

Median of 3 runs (range), tok/s unless noted. 45 client requests plus 9 sustained requests, all successful, nothing
skipped, no failures (`summary.json` `checks`). The client's own write-up: `community/…/README.md`; every request:
`community/…/results.json`; the sustained rows: `sustained.json`.

The pod column is the fork arm of `…-3090pod-step9/` and is a different configuration (RTX 3090, 64K context, int8 KV,
32K resident, 31-CPU quota), shown for scale, not as an A/B.

| Workload | RTX 4090, 128K, q4_0 KV all resident | RTX 3090 pod, 64K, int8 KV, 32K resident |
| --- | --- | --- |
| chat decode (9 requests) | 98.5 (72.0 - 108.8) | 103.1 (94.3 - 139.3) |
| chat TTFT s | 0.306 (0.242 - 0.492) | 0.346 (0.297 - 0.373) |
| prefill 4K | 1547.1 (1444.9 - 1552.4) | 2064.7 (2058.3 - 2075.5) |
| prefill 16K | 2991.6 (2886.6 - 2991.6) | 2531.0 (2406.6 - 2531.9) |
| prefill 32K | 3075.0 (3070.7 - 3075.7) | 2616.0 (2600.4 - 2617.4) |
| prefill TTFT 4K / 16K / 32K s | 2.63 / 5.41 / 10.50 | |
| agent turn decode (15 turns) | 120.0 (75.5 - 171.2) | 116.8 (106.6 - 154.2) |
| agent turn TTFT s | 2.583 (2.443 - 3.109) | 1.914 (1.579 - 2.055) |
| agent cache hit over follow-up turns | 68.8 % | |
| sustained decode, 512 tokens (9 requests) | 123.0 (110.4 - 129.2) | 119.1 (113.3 - 130.2) |
| sustained prompt | 1639.1 (634.7 - 1858.8) | 1929.0 |
| draft acceptance % (sustained) | 65.2 | 66.8 |

Sustained per document, prompt tok/s and decode tok/s medians: HOW_IT_WORKS (1,561 tokens) 637 / 121.6, INSTALL
(4,330) 1639 / 123.0, DETAILS (5,050) 1853 / 123.4. Pod: 1200 / 128.8, 1929 / 118.8, 2044 / 120.3.

Engine at the end of the arm (`engine-info.json`, `server.log`): decode expert cache hit rate 97.3 % (304,160 of
312,514 lookups), 0.2 % of routed experts read over PCIe; `spec=6` reported for `--spec 4`, as on the pod.

## Checks and findings

- **Passes the purpose.** Fresh build on the box, 54 requests through the fork at 128K, every one successful, server
  stopped cleanly by the client (`server-exit.json` returncode 1 after "shutting down so the service manager can
  restart", the same exit as the pod record). The only server warnings are the 15 "a grammar was requested; this
  engine does not constrain sampling, parsing only" lines of the agent turns, as on the pod (the client sends a JSON
  schema for tool arguments).
- **Decode is at the pod's level** (chat 98.5 vs 103.1, sustained 123.0 vs 119.1, agent 120.0 vs 116.8, ranges
  overlapping) with the whole 128K context on the card as q4_0 and 3.6 % fewer expert slots.
- **Long prefill is faster, short prefill slower.** 16K and 32K prompt reading is 18 % above the pod (2992 / 3075 vs
  2531 / 2616); 4K is 25 % below (1547 vs 2065) and the 1.5K-token sustained document reads at 637 vs 1200. Not
  separated here between the host (16 vCPUs on 8 physical cores against the pod's 31-CPU quota, with
  `--pool-workers 15` kept from the 24 GB line), the q4_0 KV write, and the 128K `--prefill auto` choice; a
  `--pool-workers 8` arm would be the first test. Open.
- **Agent-turn TTFT is 2.58 s against the pod's 1.91 s**, consistent with the short-prompt reading above (each turn
  reads about 2,900 new tokens).

## Files

- `fork-flash-next-128k-q4kv-kvres131072/`: `server-command.json` and `.sh`, `server.json` (the client's config),
  `benchmark-command.json`, `server.log`, `health.json`, `provenance.json`, `community/` (the client's results
  folder), `sustained.json`, `summary.json`, `engine-info.json`, `complete.json`, `server-exit.json`.
- `probe-kvres131072/`, `probe-kvres32768/`: the two start-only probes (`probe.json`, `server.log`, `provenance.json`).
- `model-checksums.txt`: sha256 of the shards, the pack's `dense.bin`, `expert-profile.bin` and `index.txt`, the
  MTP directory's `dense.bin`, `experts.bin` and `draft_vocab.bin`.
- `build.log`, `probe-*.log`, `bench-131072.log`: the build and the driver's console output.
- `us2-4090-run.py`: the driver (paths are the box's: `/tank/nvme/strata/us2-bench-20261019/`).
