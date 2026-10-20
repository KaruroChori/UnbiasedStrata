# Community benchmark on NVIDIA GeForce RTX 4090

Measured on 2026-10-19 with `tools/strata_bench.py` (suite 1, 3 runs per test, medians with ranges). Speeds are the engine's own timings; first-token times are measured by the client over HTTP. Speed only: no correctness check was run.

## Hardware and software

- GPU and VRAM: NVIDIA GeForce RTX 4090, 24 GiB VRAM
- CPU: Intel(R) Core(TM) i9-9900K CPU @ 3.60GHz (? cores, 16 threads); installed RAM: 66.7 GiB; storage: not measured
- OS: Linux 6.12.111+deb13-amd64; GPU driver: 550.163.01; CUDA: 12.4
- Strata: project 0.1.45, commit not a git checkout; engine b11062-3cf03257f
- Background workloads and power limits: not recorded

## Model and configuration

- Model and quantization: qwen3.8-flash-next-iq3_xxs
- Context: 131072 tokens; parallel slots: 1
- Settings: the install's own configuration, unchanged; thinking off for the suite; temperature 0

```text
unbiased-strata --pack pack-iq3-xxs --native Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile expert-profile.bin --expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mtp mtp --max-context 131072 --kv q4_0 --ple-io ram --pool-workers 15 --kv-resident 131072
```

## Method

Run by `python tools/strata_bench.py --long` against the HTTP API of a Strata server (already running); model loading is not timed. One warm-up chat and a 1K prompt are discarded first. Every prompt starts with a unique tag, so the conversation cache cannot help the fresh-prompt tests.

- short chat: the three questions of `tools/ab_engine.py`, up to 100 new tokens, 3 runs
- 4K / 16K prompts: generated word lists sized by a calibration request, 24 new tokens, 3 fresh prompts each
- agent session: system prompt and four tools, then 5 turns that each add about 1500 words of a project file and continue from the model's own earlier answers (the way agent clients resend a conversation), 64 new tokens per turn, 3 sessions; the cache numbers come from the answer's usage (`cached_tokens`) and timings (`prompt_n`)
- concurrency (when run): N requests sent at the same moment, total tokens over the wall time of the burst, latency over all requests

## Results

| Configuration | Actual prompt tokens | Reused tokens | Generated tokens | Runs | Prompt tok/s median and range | Decode tok/s median and range | TTFT seconds median and range |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| short chat | 46 (43-51) | 0 | 100 (100-100) | 9 | not measured | 98.5 (72.0-108.8) | 0.31 (0.24-0.49) |
| 4K prompt, fresh | 4019 (4019-4019) | 0 (0-0) | 24 cap | 3 | 1547.1 (1444.9-1552.4) | not measured | 2.63 (2.62-2.82) |
| 16K prompt, fresh | 16058 (16058-16058) | 0 (0-0) | 24 cap | 3 | 2991.6 (2886.6-2991.6) | not measured | 5.41 (5.41-5.61) |
| 32K prompt, fresh | 32049 (32049-32049) | 0 (0-0) | 24 cap | 3 | 3075.0 (3070.7-3075.7) | not measured | 10.50 (10.49-10.50) |
| agent session, follow-up turns | 14646 (14630-14661) at the last turn | see below | up to 64 | 3 | see below | 120.0 (75.5-171.2) | 2.58 (2.44-3.11) |

Ranges are the lowest and highest of the runs; `Runs` counts requests that returned a token.

### Agent session (conversation cache)

Cache hit over the follow-up turns: 68.8 % (68.8-69.0); earlier-turn tokens read again per session: 72 (2-75) (earlier turns that the cache did not hold; the 13718 (13718-13720) new tokens of the files are read once); first turn (nothing cached) first token: 1.32 s (1.30-1.44).

| Turn (run 1) | Prompt tokens | Reused | Read | Prompt tok/s | First token (s) | Decode tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 645 | 0 | 645 | 453.8035065994991 | 1.439 | 87.11668657905217 |
| 1 | 3796 | 673 | 3123 | 1013.3993919603649 | 3.109 | 75.48906127554945 |
| 2 | 5329 | 3859 | 1470 | 564.7737908077879 | 2.635 | 77.59413831709398 |
| 3 | 8762 | 5322 | 3440 | 1180.5897320267227 | 2.949 | 115.25542798182258 |
| 4 | 11688 | 8825 | 2863 | 1013.354475855405 | 2.87 | 121.0748160278431 |
| 5 | 14646 | 11747 | 2899 | 1076.4134749589987 | 2.739 | 104.00802347609674 |

Per-request data: `results.json`. Engine log lines from the start: `engine-log-excerpt.txt` (when this run started the server).

## Correctness and limitations

Not measured: this is a speed suite. The conversation uses the model's own replies, so token counts differ a little between runs. Machine details come from the server, `nvidia-smi`/`rocm-smi` and the OS; background load and power limits are not recorded. Total time of the suite: 128 s.
