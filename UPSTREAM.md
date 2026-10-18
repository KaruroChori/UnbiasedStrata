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

Nothing yet. The import is the current head of the engine tree.
