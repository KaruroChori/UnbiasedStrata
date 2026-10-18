# Community benchmark on NVIDIA GeForce RTX 3090

Measured on 2026-10-18 with `tools/strata_bench.py` (suite 1, 3 runs per test, medians with ranges). Speeds are the engine's own timings; first-token times are measured by the client over HTTP. Speed only: no correctness check was run.

## Hardware and software

- GPU and VRAM: NVIDIA GeForce RTX 3090, 24 GiB VRAM
- CPU: AMD EPYC 7H12 64-Core Processor (? cores, 256 threads); installed RAM: 1007.6 GiB; storage: not measured
- OS: Linux 6.8.0-107-generic; GPU driver: 580.126.20; CUDA: 13.0
- PolyStrata: project 0.1.45, commit d0cd84dc; engine b11062-3cf03257f
- Background workloads and power limits: not recorded

## Model and configuration

- Model and quantization: qwen3.6-35b-a3b-ud-q3_k_m
- Context: 32768 tokens; parallel slots: 1
- Settings: the install's own configuration, unchanged; thinking off for the suite; temperature 0

```text
unbiased-strata --model Qwen3.6-35B-A3B-UD-Q3_K_M.gguf --max-context 32768 --expert-profile expert-profile.txt --tail-skip 6
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
| short chat | not measured | 0 | 100 (100-100) | 9 | not measured | 213.5 (196.5-259.2) | 0.11 (0.11-0.12) |
| 4K prompt, fresh | not measured | 0 (0-0) | 24 cap | 3 | 3821.6 (3792.1-3831.6) | not measured | 1.06 (1.06-1.07) |
| 16K prompt, fresh | not measured | 0 (0-0) | 24 cap | 3 | 3486.3 (3482.9-3497.4) | not measured | 4.61 (4.57-4.61) |
| agent session, follow-up turns | not measured at the last turn | see below | up to 64 | 3 | see below | 186.9 (169.4-202.8) | 1.07 (0.52-1.20) |

Ranges are the lowest and highest of the runs; `Runs` counts requests that returned a token.

### Agent session (conversation cache)

Cache hit over the follow-up turns: 3254100.0 % (3253300.0-3258000.0); earlier-turn tokens read again per session: 0 (0-0) (earlier turns that the cache did not hold; the 14339 (14339-14339) new tokens of the files are read once); first turn (nothing cached) first token: 0.28 s (0.28-0.29).

| Turn (run 1) | Prompt tokens | Reused | Read | Prompt tok/s | First token (s) | Decode tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | None | 0 | 645 | 2343.2987106407563 | 0.285 | 200.12007204322592 |
| 1 | None | 663 | 3559 | 3214.3276464691166 | 1.127 | 177.32750717674534 |
| 2 | None | 4275 | 1597 | 3283.393676229011 | 0.523 | 193.90111735518875 |
| 3 | None | 5928 | 3372 | 2946.8904275875084 | 1.182 | 181.11055450657008 |
| 4 | None | 9347 | 2922 | 3027.449078865981 | 1.028 | 194.72337825970752 |
| 5 | None | 12320 | 2889 | 2871.538176349618 | 1.052 | 171.04320062552944 |

### Skipped and failed

- skipped 32K: the context is 32768 tokens

Per-request data: `results.json`. Engine log lines from the start: `engine-log-excerpt.txt` (when this run started the server).

## Correctness and limitations

Not measured: this is a speed suite. The conversation uses the model's own replies, so token counts differ a little between runs. Machine details come from the server, `nvidia-smi`/`rocm-smi` and the OS; background load and power limits are not recorded. Total time of the suite: 45 s.
