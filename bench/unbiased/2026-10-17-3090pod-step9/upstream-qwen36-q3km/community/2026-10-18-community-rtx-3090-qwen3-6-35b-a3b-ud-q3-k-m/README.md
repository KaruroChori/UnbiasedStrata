# Community benchmark on NVIDIA GeForce RTX 3090

Measured on 2026-10-18 with `tools/strata_bench.py` (suite 1, 3 runs per test, medians with ranges). Speeds are the engine's own timings; first-token times are measured by the client over HTTP. Speed only: no correctness check was run.

## Hardware and software

- GPU and VRAM: NVIDIA GeForce RTX 3090, 24 GiB VRAM
- CPU: AMD EPYC 7H12 64-Core Processor (128 cores, 256 threads); installed RAM: 1007.6 GiB; storage: not measured
- OS: Linux 6.8.0-107-generic; GPU driver: 580.126.20; CUDA: 13.0
- PolyStrata: project 0.1.45, commit d0cd84dc; engine 0.1.45
- Background workloads and power limits: not recorded

## Model and configuration

- Model and quantization: qwen3.6-35b-a3b-ud-q3_k_m
- Context: 32768 tokens; parallel slots: 1
- Settings: the install's own configuration, unchanged; thinking off for the suite; temperature 0

```text
strata-poly --model Qwen3.6-35B-A3B-UD-Q3_K_M.gguf --max-context 32768 --expert-profile expert-profile.txt --tail-skip 6
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
| short chat | 46 (43-51) | 0 | 100 (100-100) | 9 | not measured | 220.8 (198.5-271.1) | 0.18 (0.17-0.18) |
| 4K prompt, fresh | 4019 (4019-4019) | 0 (0-0) | 24 cap | 3 | 3651.6 (3598.4-3655.0) | not measured | 1.11 (1.11-1.13) |
| 16K prompt, fresh | 16058 (16058-16058) | 0 (0-0) | 24 cap | 3 | 3569.7 (3567.6-3589.4) | not measured | 4.53 (4.50-4.53) |
| agent session, follow-up turns | 15129 (15125-15130) at the last turn | see below | up to 64 | 3 | see below | 194.0 (174.1-223.7) | 1.13 (0.56-1.28) |

Ranges are the lowest and highest of the runs; `Runs` counts requests that returned a token.

### Agent session (conversation cache)

Cache hit over the follow-up turns: 68.8 % (68.8-68.8); earlier-turn tokens read again per session: 241 (237-242) (earlier turns that the cache did not hold; the 14314 (14314-14314) new tokens of the files are read once); first turn (nothing cached) first token: 0.32 s (0.32-0.33).

| Turn (run 1) | Prompt tokens | Reused | Read | Prompt tok/s | First token (s) | Decode tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 609 | 0 | 609 | 1955.1 | 0.32 | 240.8 |
| 1 | 4197 | 602 | 3595 | 3033.0 | 1.205 | 174.1 |
| 2 | 5829 | 4190 | 1639 | 2851.4 | 0.591 | 217.9 |
| 3 | 9247 | 5822 | 3425 | 2726.9 | 1.278 | 183.9 |
| 4 | 12201 | 9240 | 2961 | 2831.6 | 1.064 | 211.3 |
| 5 | 15130 | 12194 | 2936 | 2640.3 | 1.135 | 175.2 |

### Skipped and failed

- skipped 32K: the context is 32768 tokens

Per-request data: `results.json`. Engine log lines from the start: `engine-log-excerpt.txt` (when this run started the server).

## Correctness and limitations

Not measured: this is a speed suite. The conversation uses the model's own replies, so token counts differ a little between runs. Machine details come from the server, `nvidia-smi`/`rocm-smi` and the OS; background load and power limits are not recorded. Total time of the suite: 45 s.
