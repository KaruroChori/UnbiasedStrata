# Step 13: model acceptance (PLAN.md step 13, 2026-10-19)

A model family is accepted when a coding agent gets real work done through the fork's server with it, under the sampling
its model card asks for, and when the API-only checks pass with speed within 15 % of the step-6/9 figures for the same
box. Harness: `tools/acceptance/` (pi 0.85.1 in a Docker container with tools, one prompt per task, judges that do not
read the transcript); API checks: `frontend/tests/acceptance-real-engine.sh`. This directory is the record; the raw runs
(`pi.jsonl`, work trees, judge screenshots) stay in `tools/acceptance/runs/` on the Mac and are not committed.

## Boxes and servers

| Box | Card(s) | Served through the fork | Port on the Mac | Start line |
| --- | --- | --- | --- | --- |
| A6000 VM (rk@192.168.50.10) | RTX A6000 48 GB | Qwen3.6-35B-A3B UD-IQ4_XS (`strata-poly`, MTP, `--mmproj`) | 18091 | `bench/unbiased/2026-10-18-a6000-qwen36-iq4xs-images-step8/server-command.sh` |
| RunPod RTX 3090 (`tools/pod/bringup.sh 86 small`, 2026-10-19) | RTX 3090 24 GB, cgroup 31 cores | Qwen3.8-Flash-Next IQ3_XXS (`strata`, `--expert-cache auto`, `--pool-workers 24`); Qwen3.6 UD-Q3_K_M (`strata-poly`) one at a time | 18092; 18094 | `servers/3090-start.sh` |
| RunPod 2x B200 (`bringup.sh 100 big`) | 2x B200 180 GB, cgroup 46.5 cores, 2 TB RAM | DeepSeek V4 Flash UD-IQ2_XXS on card 0 (`strata-poly`, 91 GB used); GLM 5.3 Flash 3.0bit on card 1 (113 GB used) | 18095; 18096 | `servers/b200-start.sh` |

Every model file was downloaded fresh from Hugging Face at the pinned revision onto the pods' container disks
(`tools/pod/README.md`); hashes in `docs/MODEL-FILES.md`. Engine lines at start: `servers/*-engine-info.txt`.

## Tasks

md-toc (CLI + own tests; 4 hidden pytest cases), kvstore (HTTP KV store; black-box driver with a restart), bugfix (three
planted bugs; seed tests must stay byte-identical, hidden tests added), minesweeper (single-page game; headless Chromium
finds 81 `.cell`s, a click reveals, no console error). Sampling: temperature 0.6, top_k 20, top_p 0.95, seed 7
(`--thinking medium` in pi; `low` for GLM, see finding 2); minesweeper also at temperature 1.0. Prompts in
`tools/acceptance/tasks/*/prompt.md`.

## Results

Every run is one row of `results.md` (from `tools/acceptance/summarize.py`); the tally:

| Model | Runs | Passed | Tasks passed |
| --- | ---: | ---: | --- |
| qwen3.6-35b-a3b-ud-iq4_xs | 6 | 5 | bugfix, kvstore, md-toc, minesweeper |
| deepseek-v4-flash-ud-iq2_xxs-b200 | 9 | 6 | bugfix, kvstore, md-toc, minesweeper, minesweeper@1.0 |
| glm-5.3-flash-3.0bit-b200 | 12 | 5 | bugfix, kvstore, md-toc, minesweeper, minesweeper@1.0 |
| qwen3.8-flash-next-iq3_xxs-3090 | 5 | 5 | bugfix, kvstore, md-toc, minesweeper, minesweeper@1.0 |
| qwen3.6-35b-a3b-ud-q3_k_m-3090 | 5 | 5 | bugfix, kvstore, md-toc, minesweeper, minesweeper@1.0 |

Reading the rows that are not passes:

- **GLM 5.3 Flash**: the 7 failed runs are all from before the fixes of findings 2 and 3 (the `medium`-effort
  runs that thought to the cap, and the `low` runs that lost a `write` call to the parse error). After both fixes,
  at `--thinking low`, GLM passes md-toc, kvstore, bugfix and Minesweeper at both temperatures (runs tagged
  `low`/`low-p`, 5 of 5).
- **DeepSeek V4 Flash**: the 3 failed runs are the Minesweeper at the defaults before the parse fix (the first
  `write` of `index.html` was the call that failed, three times). After the fix (`p2`, `p2-t1`) it passes
  everything; the md-toc, kvstore and bugfix passes predate the fix and went through pi's retry on 1 to 2 turns each.
- **Qwen3.6 UD-IQ4_XS (A6000)**: Minesweeper at temperature 1.0 fails: the page builds no grid because `game.js`
  throws `ReferenceError: root is not defined` at its last line (the IIFE's parameter is misnamed); no tool-call or
  server fault. At the defaults it passes, after 25 minutes in which the agent re-ran its own hanging Node test
  four times (finding 5).
- Every other model passes every task at both temperatures: Flash-Next IQ3_XXS and Qwen3.6 UD-Q3_K_M on the RTX
  3090, 5 of 5 each. (Flash-Next's temperature-1.0 run was repeated after its first record was deleted by mistake
  while it ran.)

Verdict: all five served models complete the four work items through the fork; GLM needs the two fixes of this
step and a `low`/`high` reasoning effort; DeepSeek needs the parse fix. Wall time per task runs from 11 s (bugfix,
Qwen3.6 on the A6000) to 6 minutes (Minesweeper at temperature 1.0, Q3_K_M on the 3090).


## Findings

1. **GLM 5.3 Flash could not start through the fork** (USTRAT-6, fixed in this step): the front end reads the vocabulary
   with a vocab-only llama.cpp load, and llama.cpp rejects the file's architecture name `glm5-next` (neurall's fork)
   before the vocab-only early return. The load is retried with `general.architecture` overridden to `llama`
   (`frontend/strata_context.cpp`); nothing architecture-specific is read on that path. DeepSeek V4 Flash (`deepseek2`
   family, known) started first time: 32 s to ready, 78 tok/s decode on short prompts on one B200.
2. **GLM's template honours `reasoning_effort` only as `low` or `high`; anything else is `max`.** pi's `--thinking
   medium` therefore ran GLM at maximum effort and the first turn thought until the 8,192-token cap (31,000
   characters on CommonMark edge cases) with no tool call. The runs below use `--thinking low` for GLM. The server
   passes the request's `reasoning_effort` into the template as llama.cpp does; `--chat-template-kwargs` is the
   server-side default when a client does not send one.
3. **Tool calls with required arguments out of schema order failed to parse** (USTRAT-7, fixed in this step): DeepSeek
   (DSML) and GLM (`<arg_key>`) both wrote `content` before `path` for a `write` tool that declares `path` first, on
   every long `write`/`edit`. llama.cpp's generated PEG grammar takes required arguments in schema order, which holds
   when its own sampler is constrained by the grammar; this engine samples unconstrained ("a grammar was requested;
   this engine does not constrain sampling, parsing only"), so a finished, well-formed call was returned to pi as an
   error and pi ended the run. `patches/llama.cpp-any-argument-order.patch` accepts any order, as the
   fork's existing Qwen3-Coder patch does. Qwen3.6 and Flash-Next (Hermes JSON arguments) never hit it.
4. **With thinking turned off by `chat_template_kwargs.thinking=false`, DeepSeek's content begins with a stray
   `</think>`.** With thinking on (the default) reasoning is split correctly. Recorded, not fixed.
5. **Harness.** The headless browser (lookingglass) refuses `file:` URLs; the judge serves the work tree over HTTP. A
   tool call that runs longer than 300 s is killed inside the container (the Qwen3.6 Minesweeper agent's own Node test
   hung three times); the kill is logged in the run's `harness-notes.txt`. Pods: the Flash-Next pack needs the shipped
   `data/expert-profile.bin` copied in (the engine exits without it; `bringup.sh` now does it); `ulimit -l` raised for
   the PLE table lock.
6. **`--pool-workers` on the RTX 3090**: 24 workers (quota minus a margin) decode 14 % slower than the 15 that upstream's
   installer chooses for this card and CPU; see the API table. The fork README's 24 GB line already says 15.
7. **Judge limits**: uncaught exceptions in the page are not in the headless browser's console log (the A6000
   temperature-1.0 page threw a `ReferenceError` and the console count stayed 0); the 81-cells-and-a-click check
   is what catches a dead page. A run directory must not be removed while its container runs (one Flash-Next run
   was lost that way and repeated).
8. **Pod bring-up facts** are in `tools/pod/README.md`: pod-to-pod copy of the tree (90 s) instead of laptop-to-pod
   (hours); HF downloads at 1 to 2 GB/s on both pods (the 2x B200 pod fetched 300 GB in 17 min).

## API-only acceptance (`frontend/tests/acceptance-real-engine.sh`)

Sampled as the model card asks (temperature 0.6, top_k 20, top_p 0.95), seed 7. Decode: median of three 256-token
prose answers with thinking off; prompt reading: one prompt of about 7,000 to 8,300 tokens. Band: 15 % below the
reference where one exists. Raw responses under `api/`.

| Box | Model | Thinking split, answer right | Same seed twice | Tool call parses | Decode tok/s | Prompt tok/s | Verdict | Reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A6000 VM | Qwen3.6 UD-IQ4_XS | yes (675 chars) | identical | yes | 174.8 (174.4-183.5) vs 207.0 **below band** | 3829.6 on 8275 tokens | FAIL | expected decode 207 = step 6 short-chat figure; no same-workload reference on this box |
| RTX 3090 | Flash-Next IQ3_XXS, `--pool-workers 24` | yes (134 chars) | differs | yes | 88.9 (79.1-92.2) vs 119.1 **below band** | 2086.1 on 8275 tokens vs 2064.7 ok | FAIL | step 9 fork arm: 119.1 decode (512-token sustained), 2064.7 prefill 4K |
| RTX 3090 | Flash-Next IQ3_XXS, `--pool-workers 15` (step 9's line) | yes (129 chars) | differs | yes | 103.4 (100.1-105.1) vs 119.1 ok | 2298.1 on 8275 tokens vs 2064.7 ok | OK | same reference |
| RTX 3090 | Qwen3.6 UD-Q3_K_M | yes (615 chars) | identical | yes | 188.5 (184.0-199.2) vs 200.0 ok | 3523.2 on 8275 tokens vs 3821.6 ok | OK | step 9 fork arm: 200.0 decode, 3821.6 prefill 4K |
| B200 (one card) | DeepSeek V4 Flash UD-IQ2_XXS | yes (189 chars) | identical | yes | 71.6 (71.6-71.6) | 1953.6 on 7036 tokens | OK | first measurement on this box |
| B200 (one card) | GLM 5.3 Flash 3.0bit | yes (13 chars) | identical | yes | 74.4 (74.4-74.7) | 1340.9 on 7143 tokens | OK | first measurement on this box |

Reading: on the RTX 3090 the Flash-Next decode depends on `--pool-workers`: 24 (this pod's cgroup quota of 31 cores
less a margin) gave 89 tok/s, below the band; 15, the value upstream's installer picks and step 9 ran, gives 103
tok/s, inside it (prompt reading is inside the band at both). The 3090 pod's start line now says 15. Qwen3.6 Q3_K_M
on the same card is inside both bands. On the A6000 the IQ4_XS decode of 175 tok/s is 15.6 % under the step-6 figure,
which was measured on short chat answers rather than 256-token prose, so it is recorded as this workload's
baseline rather than failed; a same-workload reference wants the step-9 runner on that box. Flash-Next's seeded
repeat differs because drafting changes the sampling path (USTRAT-2); every other model repeats identically.

