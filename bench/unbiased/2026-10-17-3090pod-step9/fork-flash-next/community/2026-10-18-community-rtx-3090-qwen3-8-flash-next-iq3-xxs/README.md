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
| short chat | not measured | 0 | 100 (100-100) | 9 | not measured | 103.1 (94.3-139.3) | 0.35 (0.30-0.37) |
| 4K prompt, fresh | not measured | 0 (0-0) | 24 cap | 3 | 2064.7 (2058.3-2075.5) | not measured | 1.93 (1.93-1.95) |
| 16K prompt, fresh | not measured | 0 (0-0) | 24 cap | 3 | 2531.0 (2406.6-2531.9) | not measured | 6.30 (6.30-6.62) |
| 32K prompt, fresh | not measured | 0 (0-0) | 24 cap | 3 | 2616.0 (2600.4-2617.4) | not measured | 12.13 (12.13-12.21) |
| agent session, follow-up turns | not measured at the last turn | see below | up to 64 | 3 | see below | 116.8 (106.6-154.2) | 1.91 (1.58-2.06) |

Ranges are the lowest and highest of the runs; `Runs` counts requests that returned a token.

### Agent session (conversation cache)

Cache hit over the follow-up turns: 3253000.0 % (3246900.0-3254000.0); earlier-turn tokens read again per session: 0 (0-0) (earlier turns that the cache did not hold; the 14408 (14407-14408) new tokens of the files are read once); first turn (nothing cached) first token: 0.89 s (0.83-0.90).

| Turn (run 1) | Prompt tokens | Reused | Read | Prompt tok/s | First token (s) | Decode tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | None | 0 | 645 | 790.7716337341952 | 0.828 | 78.90880396798558 |
| 1 | None | 662 | 3556 | 1783.488686432496 | 2.009 | 109.23390620448588 |
| 2 | None | 4281 | 1598 | 1025.1120374326267 | 1.591 | 113.27919906212014 |
| 3 | None | 5872 | 3443 | 1697.4011472124512 | 2.055 | 108.76291559622705 |
| 4 | None | 9373 | 2922 | 1582.8270309155043 | 1.903 | 138.7945329563966 |
| 5 | None | 12352 | 2889 | 1560.5815151307265 | 1.92 | 123.79204508388385 |

Per-request data: `results.json`. Engine log lines from the start: `engine-log-excerpt.txt` (when this run started the server).

## Correctness and limitations

Not measured: this is a speed suite. The conversation uses the model's own replies, so token counts differ a little between runs. Machine details come from the server, `nvidia-smi`/`rocm-smi` and the OS; background load and power limits are not recorded. Total time of the suite: 117 s.
