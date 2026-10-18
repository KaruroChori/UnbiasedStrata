# Community benchmark on NVIDIA GeForce RTX 3090

Measured on 2026-10-18 with `tools/strata_bench.py` (suite 1, 3 runs per test, medians with ranges). Speeds are the engine's own timings; first-token times are measured by the client over HTTP. Speed only: no correctness check was run.

## Hardware and software

- GPU and VRAM: NVIDIA GeForce RTX 3090, 24 GiB VRAM
- CPU: AMD EPYC 7H12 64-Core Processor (? cores, 256 threads); installed RAM: 1007.6 GiB; storage: not measured
- OS: Linux 6.8.0-107-generic; GPU driver: 580.126.20; CUDA: 13.0
- PolyStrata: project 0.1.45, commit d0cd84dc; engine b11062-3cf03257f
- Background workloads and power limits: not recorded

## Model and configuration

- Model and quantization: qwen3.8-flash-next-iq3_xxs
- Context: 65536 tokens; parallel slots: 1
- Settings: the install's own configuration, unchanged; thinking off for the suite; temperature 0

```text
unbiased-strata --pack pack-iq3-xxs --native Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile expert-profile.bin --expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mtp mtp --max-context 65536 --kv int8 --ple-io ram --pool-workers 15 --kv-resident 32768
```

## Method

Run by `python tools/strata_bench.py --long` against the HTTP API of a PolyStrata server (already running); model loading is not timed. One warm-up chat and a 1K prompt are discarded first. Every prompt starts with a unique tag, so the conversation cache cannot help the fresh-prompt tests.

- short chat: the three questions of `tools/ab_engine.py`, up to 100 new tokens, 3 runs
- 4K / 16K prompts: generated word lists sized by a calibration request, 24 new tokens, 3 fresh prompts each
- agent session: system prompt and four tools, then 5 turns that each add about 1500 words of a project file and continue from the model's own earlier answers (the way agent clients resend a conversation), 64 new tokens per turn, 3 sessions; the cache numbers come from the answer's usage (`cached_tokens`) and timings (`prompt_n`)
- concurrency (when run): N requests sent at the same moment, total tokens over the wall time of the burst, latency over all requests

## Results

| Configuration | Actual prompt tokens | Reused tokens | Generated tokens | Runs | Prompt tok/s median and range | Decode tok/s median and range | TTFT seconds median and range |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| short chat | 46 (43-51) | 0 | 100 (100-100) | 9 | not measured | 93.3 (73.8-99.6) | 0.42 (0.36-0.45) |
| 4K prompt, fresh | 4019 (4019-4019) | 0 (0-0) | 24 cap | 3 | 1908.1 (1783.9-1916.7) | not measured | 2.13 (2.12-2.29) |
| 16K prompt, fresh | 16058 (16058-16058) | 0 (0-0) | 24 cap | 3 | 2328.6 (2322.9-2331.2) | not measured | 6.98 (6.98-6.98) |
| 32K prompt, fresh | 32049 (32049-32049) | 0 (0-0) | 24 cap | 3 | 2384.7 (2358.9-2395.2) | not measured | 13.59 (13.51-13.71) |
| agent session, follow-up turns | 15236 (15193-15248) at the last turn | see below | up to 64 | 3 | see below | 104.0 (77.5-125.1) | 2.05 (1.65-2.29) |

Ranges are the lowest and highest of the runs; `Runs` counts requests that returned a token.

### Agent session (conversation cache)

Cache hit over the follow-up turns: 69.3 % (69.3-69.4); earlier-turn tokens read again per session: 73 (4-73) (earlier turns that the cache did not hold; the 14334 (14334-14335) new tokens of the files are read once); first turn (nothing cached) first token: 1.02 s (0.95-1.03).

| Turn (run 1) | Prompt tokens | Reused | Read | Prompt tok/s | First token (s) | Decode tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 645 | 0 | 645 | 688.3921081447993 | 0.951 | 81.34206663077286 |
| 1 | 4225 | 669 | 3556 | 1658.2510580910155 | 2.166 | 85.59619789840953 |
| 2 | 5886 | 4289 | 1597 | 957.8325754240674 | 1.703 | 78.01944541796752 |
| 3 | 9322 | 5879 | 3443 | 1539.8107951336074 | 2.286 | 102.18790834396884 |
| 4 | 12291 | 9369 | 2922 | 1459.4690170011659 | 2.064 | 103.11518334247867 |
| 5 | 15236 | 12347 | 2889 | 1460.0849467213031 | 2.048 | 77.521287591672 |

Per-request data: `results.json`. Engine log lines from the start: `engine-log-excerpt.txt` (when this run started the server).

## Correctness and limitations

Not measured: this is a speed suite. The conversation uses the model's own replies, so token counts differ a little between runs. Machine details come from the server, `nvidia-smi`/`rocm-smi` and the OS; background load and power limits are not recorded. Total time of the suite: 131 s.
