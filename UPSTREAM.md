# Relationship to upstream

## Sources

| What | Where | Version |
| --- | --- | --- |
| Engines (`strata`, `strata-poly`), tools, docs | https://github.com/VecSzn/PolyStrata | tag `v0.1.45-poly.1`, commit `d0cd84dc6bd009d1d9e2191e4e28cc76b80f1ee3` |
| ggml, llama, common, mtmd, cpp-httplib | https://github.com/ggml-org/llama.cpp, as the submodule `third_party/llama.cpp` | commit `3cf03257f219afbe7334045ff7c6a06ac68c627d`, the one upstream pins |

Commit `0197ae86` ("Import PolyStrata v0.1.45-poly.1 (d0cd84dc) unmodified") is the upstream tree, every tracked
file, with the same tree hash as upstream's commit. `git diff 0197ae86 HEAD` is the whole story of this fork;
`git diff 0197ae86 HEAD -- src include` is every change to the engines.

The history before that commit is UnbiasedStrata 1, a fork of Niko1221/Strata 0.1.39, ended at the tags
`unbiasedstrata-1` and `unbiasedstrata-1-muse-spark-native`.

## Rules

A thing is removed only when it (1) reaches the network during setup, build or start-up, (2) puts Python
between a request and a token, (3) breaks or complicates the one-command build, or (4) is marketing.
Everything else stays, built or not. Engine changes are bug fixes for the target (Linux x86-64, one NVIDIA
GPU, Pascal or newer, CUDA 12.x), each recorded below with the file, the reason and the measurement.

## Build (`CMakeLists.txt`, `Makefile`, `.gitmodules`, `.gitignore`, `patches/`)

- **ggml from the submodule, not a fetch.** `STRATA_GGML_DIR` defaults to `third_party/llama.cpp` and the
  configure stops with the `git submodule update --init` line if `ggml/CMakeLists.txt` is missing. Upstream's
  `FetchContent` of llama.cpp (the only network access of its build) is deleted. The three later
  `if(STRATA_GGML_DIR)` blocks are unchanged; their `else()` branches are now dead. `.gitignore` no longer
  ignores `/third_party/llama.cpp*`.
- **`patches/*.patch` applied at configure time.** Each patch is checked in reverse first, so configuring twice
  applies it once. The submodule's working tree is therefore modified after a configure; `git -C
  third_party/llama.cpp diff` shows exactly the patches. UnbiasedStrata 1 applied its patch in `make` and in
  CMake both; here it is CMake only, so a tree configured directly gets it too.
- **llama.cpp's libraries for the front end.** A second `add_subdirectory` of the submodule with
  `LLAMA_BUILD_COMMON` and `LLAMA_BUILD_MTMD` on and tests, tools, examples, server, app, UI, prebuilt UI,
  OpenSSL and llguidance off. It reuses the ggml targets configured above.
- **`Makefile`.** `make build` configures once and builds `strata`, `strata-poly`, `strata_kq`, `llama-common`
  and `mtmd` into `build/bin/`, not upstream's `all`, which also builds about 70 parity and bench programs.
  `CUDA_ARCHS` defaults to `61;75;86;89`; an arch below 75 adds upstream's `STRATA_EXPERIMENTAL_SM60`
  (upstream's default is `120`, which needs CUDA 13). `PORTABLE=1` gives the AVX2 baseline instead of
  `-march=native`. One GCC for the C, C++ and nvcc host sides: the Makefile probes `g++-15`, `g++-14`, ... with
  `nvcc -ccbin` and passes the newest accepted one as `CMAKE_C_COMPILER`, `CMAKE_CXX_COMPILER` and
  `CMAKE_CUDA_HOST_COMPILER`. Without that, on a box whose default `g++` is newer than nvcc accepts (Debian 13 with
  CUDA 12.4: GCC 14 against a GCC 13 limit), the C++ files were compiled by GCC 14 and the CUDA files by GCC 13, and
  `strata` failed to link on `__cxa_call_terminate` (upstream's installer handles the same case, its #1645).
  `HOSTCXX=/usr/bin/g++-13` overrides the probe.

## Patches to llama.cpp (`patches/`)

- `llama.cpp-qwen3-coder-any-argument-order.patch` (`common/parsers/qwen3-coder.cpp`): the Qwen3-Coder
  tool-call grammar accepts a call's arguments in any order. Upstream takes the required ones first and the
  optional ones after; Qwen3.8 Flash-Next often writes the optional ones first (`limit`, `offset`, `path`), and
  because the grammar's tool-call group is optional and has no end anchor, such a call was dropped silently:
  the client got `finish_reason=stop` and an empty answer (UnbiasedStrata 1, 2026-10-08, REGINA-104). Qwen3.6's
  template routes to the same parser. Carried over unchanged; it applies cleanly at this pin.

## Engine source (`src/`, `include/`)

No changes yet.

## Removed

Each entry names the rule above that it satisfies.

- **Rule 1, installers and downloaders:** `setup.py` (8,223 lines: hardware detection, pip, CUDA, llama.cpp zips,
  prebuilt engines from GitHub releases, model files from Hugging Face or ModelScope, pack and MTP orchestration,
  run-config JSON, start), `setup.sh`, `SETUP.bat`, `START-HERE.bat`, `UPDATE.bat`, `update.sh`, `Dockerfile`,
  `docker-entrypoint.sh`, `.dockerignore`, `flake.nix`, `flake.lock`, `requirements.txt` (replaced by
  `tools/requirements.txt`: numpy and regex, for the offline tools only), `conftest.py` (pytest root for
  `setup.py`'s tests), `tools/strata_mcp.py` (an installer driven over MCP), `tools/image/` (stable-diffusion.cpp,
  Vulkan SDK and model downloads), `tools/hip/package_windows.py` (AMD nightly wheels), and their tests
  (`tools/test_setup_*.py` with two golden JSONs, `test_strata_mcp.py`, `test_qimage.py`,
  `test_docker_entrypoint.py`, `test_poly_prebuilt.py`). The jobs of `setup.py` that were not downloads (choosing
  engine flags per card, RAM and context) become documented flags in `README.md`.
- **Rule 2, Python in the serving path:** `serve/` (92 files, 33.9k lines: the HTTP server with the OpenAI,
  Anthropic and Responses dialects, the jinja2 chat templating, the Python tokenizer path, the per-family
  reasoning and tool-call parsers, MCP, structured output, replicas, Prometheus, the hardware monitor, the web
  UI and 58 test files) and `polystrata.py` (the terminal front end, which imports `serve/`). Replaced by the C++
  front end in `frontend/`, built from the pinned llama.cpp's `common`, `mtmd`, `cpp-httplib` and the
  engine-agnostic files of `tools/server`. The engines' stdin/stdout protocol is unchanged.
- **Rule 4, marketing:** the six translated READMEs (383 KB), `docs/media/` (12 MB: a 9.6 MB demo video still,
  a 1.8 MB GIF, the figure SVGs and their generator), `.github/` (issue and PR templates), `SECURITY.md` (the
  upstream project's advisory process) and `AGENTS.md` (contributor notes for upstream's tests and installers).
  `README.md` is rewritten for this fork; until then its image links point at removed files.
- **Documents only removed components (decided 2026-10-17):** `docs/INSTALL.md`, `AI_SETUP.md`, `MCP_SERVER.md`,
  `IMAGES.md`, `LLAMA_SWAP.md`, `COMMUNITY_BENCHMARKS.md`, `FAQ.md`; `chat.py` (a terminal client) and
  `tools/calibrate.py` (imports `setup` and `serve.server`), with their tests.

## Kept but not runnable

These stay because no rule removes them, but they import `setup` or `serve` and so do not run here: the engine gate
scripts `tools/batch_groups_cache_test.py`, `cancel_park_test.py`, `conversation_cache_*.py`,
`conversation_restore_speed.py`, `logit_bias_english_example.py`, `logit_bias_http_probe.py`,
`session_pressure_test.py`, and `tools/strata_bench.py` (one helper from `setup`), `tools/make_poly_release.py`,
`tools/test_mtp_fetch.py`, `tools/test_shards.py`, `test_strata_tokenizer.py`, `test_effort_end_args.py`,
`test_research_run.py`, `test_benchmark_prompt.py`, `test_dll_closure.py`, `test_windows_amd_gpu.py`, and the
benchmark scripts under `bench/results/*/`. Upstream's own copies run against upstream.

