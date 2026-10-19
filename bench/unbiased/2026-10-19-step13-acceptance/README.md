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

RESULTS_TABLE

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
6. **Pod bring-up facts** are in `tools/pod/README.md`: pod-to-pod copy of the tree (90 s) instead of laptop-to-pod
   (hours); HF downloads at 1 to 2 GB/s on both pods (the 2x B200 pod fetched 300 GB in 17 min).

## API-only acceptance (`frontend/tests/acceptance-real-engine.sh`)

API_TABLE
