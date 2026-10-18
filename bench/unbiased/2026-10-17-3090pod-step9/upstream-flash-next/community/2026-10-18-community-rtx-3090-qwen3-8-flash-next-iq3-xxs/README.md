# Community benchmark on NVIDIA GeForce RTX 3090

Measured on 2026-10-18 with `tools/strata_bench.py` (suite 1, 3 runs per test, medians with ranges). Speeds are the engine's own timings; first-token times are measured by the client over HTTP. Speed only: no correctness check was run.

## Hardware and software

- GPU and VRAM: NVIDIA GeForce RTX 3090, 24 GiB VRAM
- CPU: AMD EPYC 7H12 64-Core Processor (128 cores, 256 threads); installed RAM: 1007.6 GiB; storage: not measured
- OS: Linux 6.8.0-107-generic; GPU driver: 580.126.20; CUDA: 13.0
- PolyStrata: project 0.1.45, commit d0cd84dc; engine 0.1.45
- Background workloads and power limits: not recorded

## Model and configuration

- Model and quantization: qwen3.8-flash-next-iq3_xxs
- Context: 65536 tokens; parallel slots: 1
- Settings: the install's own configuration, unchanged; thinking off for the suite; temperature 0

```text
strata --pack pack-iq3-xxs --native Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile expert-profile.bin --expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mtp mtp --max-context 65536 --kv int8 --ple-io ram --pool-workers 15 --kv-resident 32768
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
| short chat | 46 (43-51) | 0 | 100 (100-100) | 9 | not measured | 87.1 (72.5-107.0) | 0.41 (0.36-0.48) |
| 4K prompt, fresh | 4019 (4019-4019) | 0 (0-0) | 24 cap | 3 | 1923.9 (1835.2-1933.9) | not measured | 2.11 (2.10-2.21) |
| 16K prompt, fresh | 16058 (16058-16058) | 0 (0-0) | 24 cap | 3 | 2342.1 (2326.5-2347.6) | not measured | 6.89 (6.88-6.93) |
| 32K prompt, fresh | 32049 (32049-32049) | 0 (0-0) | 24 cap | 3 | 2392.9 (2388.9-2395.0) | not measured | 13.45 (13.43-13.47) |
| agent session, follow-up turns | 15157 (15149-15169) at the last turn | see below | up to 64 | 3 | see below | 110.6 (70.0-135.6) | 2.00 (1.64-2.26) |

Ranges are the lowest and highest of the runs; `Runs` counts requests that returned a token.

### Agent session (conversation cache)

Cache hit over the follow-up turns: 69.3 % (69.1-69.3); earlier-turn tokens read again per session: 4 (3-74) (earlier turns that the cache did not hold; the 14334 (14334-14334) new tokens of the files are read once); first turn (nothing cached) first token: 0.97 s (0.97-1.01).

| Turn (run 1) | Prompt tokens | Reused | Read | Prompt tok/s | First token (s) | Decode tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 609 | 0 | 609 | 640.6 | 0.972 | 56.2 |
| 1 | 4180 | 624 | 3556 | 1664.6 | 2.167 | 70.0 |
| 2 | 5841 | 4243 | 1598 | 973.0 | 1.671 | 77.6 |
| 3 | 9277 | 5904 | 3373 | 1510.5 | 2.261 | 85.3 |
| 4 | 12253 | 9331 | 2922 | 1484.5 | 2.003 | 95.9 |
| 5 | 15157 | 12268 | 2889 | 1461.8 | 2.004 | 88.9 |

Per-request data: `results.json`. Engine log lines from the start: `engine-log-excerpt.txt` (when this run started the server).

## Correctness and limitations

Not measured: this is a speed suite. The conversation uses the model's own replies, so token counts differ a little between runs. Machine details come from the server, `nvidia-smi`/`rocm-smi` and the OS; background load and power limits are not recorded. Total time of the suite: 128 s.
