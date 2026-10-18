# Step 9: upstream PolyStrata v0.1.45-poly.1 vs UnbiasedStrata 2, RTX 3090 pod, 2026-10-18 UTC

PLAN.md section 11, rows 1 and 2. Same pod (RunPod RTX 3090 24 GB, driver 580.126.20, 31 CPU quota), same model
files (`docs/MODEL-FILES.md`), same engine arguments, same context, greedy, the same client: upstream's
`tools/strata_bench.py --runs 3 --long` (chat, 4K/16K/32K prompts, agent session) plus the three-document sustained
supplement of the 2026-10-17 upstream run (3 runs x 3 documents, 512 tokens each). Driver: `us2-step9-run.py` (copy
here), run from upstream's venv. Arms ran back to back, one server at a time, nothing else on the card.

| Arm | Front end | Engine | Server port | Started (UTC) |
| --- | --- | --- | --- | --- |
| upstream-flash-next | upstream `serve/server.py` (Python) | upstream `build/strata`, sha256 `4e7254ef…` | 18080 | 05:48:30 |
| fork-flash-next | `unbiased-strata` (fork 143ada2 = 453d3015 locally) | fork `build/bin/strata`, sha256 `62b91d67…` | 18090 | 06:29:25 |
| upstream-qwen36-q3km | upstream `serve/server.py` | upstream `build/strata-poly`, sha256 `c893c169…` | 18080 | 06:34:20 |
| fork-qwen36-q3km | `unbiased-strata` (fork 143ada2) | fork `build/bin/strata-poly`, sha256 `7ba58112…` | 18091 | 06:35:57 |

Both engines are built from the same v0.1.45-poly.1 sources, once in upstream's tree and once in the fork's tree; the
binaries differ (different build directories and times), so an engine-build difference is not excluded by this run.

## Row 1: Qwen3.8 Flash-Next IQ3_XXS, MTP spec 4, 64K context, int8 KV

Median of 3 runs (range). tok/s unless noted. 45 requests per arm, all successful, nothing skipped.

| Workload | upstream | fork | fork / upstream |
| --- | --- | --- | --- |
| chat decode (9 requests) | 87.1 (72.5 - 107.0) | 103.1 (94.3 - 139.3) | 1.18 |
| chat TTFT s | 0.406 (0.361 - 0.478) | 0.346 (0.297 - 0.373) | 0.85 |
| prefill 4K | 1923.9 (1835.2 - 1933.9) | 2064.7 (2058.3 - 2075.5) | 1.07 |
| prefill 16K | 2342.1 (2326.5 - 2347.6) | 2531.0 (2406.6 - 2531.9) | 1.08 |
| prefill 32K | 2392.9 (2388.9 - 2395.0) | 2616.0 (2600.4 - 2617.4) | 1.09 |
| agent turn decode (15 turns) | 110.6 (70.0 - 135.6) | 116.8 (106.6 - 154.2) | 1.06 |
| agent turn TTFT s | 2.003 (1.641 - 2.261) | 1.914 (1.579 - 2.055) | 0.96 |
| sustained decode, 512 tokens (9 requests) | 105.1 (92.9 - 115.5) | 119.1 (113.3 - 130.2) | 1.13 |
| sustained prompt | 1776.7 | 1929.0 | 1.09 |
| draft acceptance % | 64.3 | 66.8 | |

## Row 2: Qwen3.6-35B-A3B UD-Q3_K_M (unsloth MTP file), draft on, 32K context

42 requests per arm, all successful; the 32K prompt is skipped by the client on both arms (context is 32768).

| Workload | upstream | fork | fork / upstream |
| --- | --- | --- | --- |
| chat decode (9 requests) | 220.8 (198.5 - 271.1) | 213.5 (196.5 - 259.2) | 0.97 |
| chat TTFT s | 0.178 (0.175 - 0.184) | 0.110 (0.107 - 0.117) | 0.62 |
| prefill 4K | 3651.6 (3598.4 - 3655.0) | 3821.6 (3792.1 - 3831.6) | 1.05 |
| prefill 16K | 3569.7 (3567.6 - 3589.4) | 3486.3 (3483.0 - 3497.4) | 0.98 |
| agent turn decode (15 turns) | 194.0 (174.1 - 223.7) | 186.9 (169.4 - 202.8) | 0.96 |
| agent turn TTFT s | 1.127 (0.565 - 1.278) | 1.069 (0.518 - 1.198) | 0.95 |
| sustained decode, 512 tokens (9 requests) | 207.6 (198.5 - 225.7) | 200.0 (188.4 - 218.4) | 0.96 |
| sustained prompt | 3381.8 | 3480.6 | 1.03 |
| draft acceptance % | 80.4 | 80.0 | |

## Row 3: pi on the fixed coding task, Flash-Next, wall time (`row3/`)

pi 0.85.1 (`-p`, no session, provider "UnbiasedStrata 2" in `row3/pi-models.json`) against each server through an SSH
tunnel from the laptop, one server at a time, the step-9 Flash-Next server command on both sides (fork with
`--sse-ping-interval 10`, upstream with the step-9 arm's `server.json`). Task: `row3/*/task.txt` (add `--json` to
`wordstats.py`, write unittest tests, run them, commit). Sampling is pi's (temperature 0.6, top_p 0.95, top_k 20), so
each run is a different trajectory; all six runs passed the task's checks (tests OK, `--json` output right, one commit).

| Run | upstream wall s | upstream generated tokens | fork wall s | fork generated tokens |
| --- | --- | --- | --- | --- |
| 1 | 31.2 | 2251 | 44.7 | 3028 |
| 2 | 36.3 | 2453 | 44.7 | 3426 |
| 3 | 42.4 | 3208 | 44.7 | 3619 |
| median | 36.3 | 2453 | 44.7 | 3426 |

Generated tokens per wall-clock second (the whole run, pi's tool execution and the tunnel included): upstream 72.1,
67.6, 75.7 (median 72.1); fork 67.7, 76.6, 81.0 (median 76.6). The wall time follows the trajectory length: the fork's
three trajectories were longer (3028 to 3619 tokens against 2251 to 3208), and per generated token the two are within
the run-to-run spread. Three runs a side do not separate them further. The fork's three wall times agreeing to 0.1 s
is coincidence: the server-side spans were 43.9, 38.5 and 44.0 s (`row3/fork-flash-next/runs-from-serverlog.json`).
The fork's server logged 'a grammar was requested; this engine does not constrain sampling, parsing only' on every
request: pi sends a JSON schema for tool arguments, which neither server enforces at the sampler.

## Reading

- Row 1: the fork is faster than upstream on every workload, by 6 to 18 % on decode and 7 to 9 % on prefill; the
  chat and sustained ranges do not overlap. The engine binaries differ, so this is not attributed to the front end
  yet (PLAN.md section 11 asks only that the fork is not slower).
- Row 2: decode is within the run-to-run range on chat, agent and sustained (ranges overlap). Prefill 16K is 2.3 %
  slower with non-overlapping ranges (3483 - 3497 vs 3568 - 3589); prefill 4K is 4.7 % faster. Per the plan's pass
  rule this one cell is a finding to explain, not a pass. Candidates: engine build differences (see above), the
  fork's own `expert-profile.txt` written during the run versus upstream's.
- Chat TTFT is lower on the fork on both models (0.85x and 0.62x).
- Row 3: pi finishes the task on both; wall time per generated token is within noise (fork 76.6 vs upstream 72.1 tok/s
  median); raw wall medians (44.7 vs 36.3 s) differ because the sampled trajectories differed in length.

## What went wrong on the way (kept for the record)

- `fork-flash-next.attempt1-health-mismatch/`: the first fork arm (fork 4c25aa6f) served fine at 18 s but upstream's
  client never considered it ready (`/health` lacked `service: "strata"` and `loaded: true`); killed after the 1800 s
  wait. Fixed by fork commit 453d3015 (`143ada2` on the pod). `step9-launch.log` is that first campaign.
- The fork streams no `usage` block unless asked (`stream_options.include_usage`, llama.cpp's behaviour), upstream
  always sends one; the client takes `prompt_tokens` from it, so `prompt_tokens` is null in the fork rows (the token
  counts in `timings` are present). The runner's summary step crashed on it once (`step9-launch-2.log`), was made
  tolerant, and the fork-flash-next summary was regenerated from the recorded data (`US2_SUMMARIZE_ONLY=1`). Fork
  commit 96f4ef1f always sends the usage chunk; it was built on the pod after the campaign, so it is not what was
  measured here.
- `server-exit.json` is 1 for both fork arms: on SIGTERM the front end logs `E srv operator(): ; shutting down so the
  service manager can restart` and exits non-zero (the engine child dies with the process group, the front end
  reports an engine death with an empty message). Harmless here; a clean SIGTERM exit is a fix to make before the
  systemd unit uses `Restart=on-failure`.

## Files

Per arm: `server.json` (the client's config), `server-command.json`, `provenance.json` (engine sha256, fork commit,
GPU, CPU quota), `health.json`, `server.log` (upstream arms also `engine.log`), `community/` (the client's own
report and `results.json`), `sustained.json`, `summary.json`, `complete.json`, `server-exit.json`. The Qwen3.6 arms
also have the `expert-profile.txt` the engine wrote. Launch logs: `step9-launch.log` (first campaign, upstream
Flash-Next and the failed fork attempt), `step9-launch-2.log` (fork Flash-Next), `step9-launch-3.log` (Qwen3.6 arms).
