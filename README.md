# UnbiasedStrata 2

A fork of [PolyStrata](https://github.com/VecSzn/PolyStrata) v0.1.45-poly.1 that keeps its two inference engines
unchanged and replaces everything around them: no installer, no downloads at build or start, no Python between a
request and a token. One `make build` on a Linux box with an NVIDIA card produces the engines and a C++ front end,
`unbiased-strata`, that serves an OpenAI-style chat API from llama.cpp's own server code. The target is one NVIDIA GPU,
Pascal or newer, CUDA 12.x, Linux x86-64, on a machine that may have no network at all. What was changed and why is in
[UPSTREAM.md](UPSTREAM.md); the plan this follows is [PLAN.md](PLAN.md).

## The two engines

| Engine | Input | Models measured here | Models present, unmeasured |
| --- | --- | --- | --- |
| `strata` | a pack directory made from a GGUF (`tools/iq_pack.py`), the native shards, an MTP draft directory | Qwen3.8-Flash-Next GSQ-RCO IQ3_XXS | the other Flash-Next quants, Flash-Next Coder, Unsloth NVFP4 |
| `strata-poly` | a GGUF in place | Qwen3.6-35B-A3B Unsloth UD-Q3_K_M and UD-IQ4_XS (the `-MTP` files) | GLM 5.3 Flash, DeepSeek V4 Flash, LFM2.5, Ornith 1.5, Gemma 4, Tiel Coder, MiniCPM-V |

"Measured" means the file is in [docs/MODEL-FILES.md](docs/MODEL-FILES.md) with its SHA-256, has been served through
the front end on at least one box, and has a row in a results directory under `bench/unbiased/`. "Present" means
upstream's engine supports it and nothing here has been removed that it needs, but no file has been loaded through
this front end. Upstream's model notes are kept as they were: [docs/MODELS.md](docs/MODELS.md),
[docs/QWEN36.md](docs/QWEN36.md), [docs/GLM.md](docs/GLM.md), [docs/DEEPSEEK.md](docs/DEEPSEEK.md),
[docs/LFM.md](docs/LFM.md), [docs/BACKENDS.md](docs/BACKENDS.md).

Pictures: Qwen3.6 with its projector file (`--mmproj`, below); the encoder runs on the CPU in the front end and the
engine takes the rows. Measured once, `bench/unbiased/2026-10-18-a6000-qwen36-iq4xs-images-step8/`.

## Build

Requirements: CMake 3.24 or newer, a C++20 compiler (GCC 11 to 14), a CUDA 12.x toolkit and driver, git, python3
and curl for the tests. Nothing is downloaded after the clone: ggml, llama, common and mtmd come from the
`third_party/llama.cpp` submodule, pinned to the commit upstream pins.

```
git clone <this repo> && cd UnbiasedStrata
git submodule update --init          # shallow, third_party/llama.cpp @ 3cf03257
make build                           # build/bin/{strata,strata-poly,libstrata_kq.so,unbiased-strata}
make test                            # the front end against a fake engine; no GPU, no model
```

The two `git` lines are the only ones that reach the network. For a box without one, run them on a machine that has
it and copy the tree over (`rsync -a UnbiasedStrata/ box:UnbiasedStrata/`; about 700 MB with `.git`), then `make build`
there; that is how the A6000 VM below was done (2026-10-19, fresh clone: 5 s clone, 27 s submodule, 20.6 min `make build`
at the default four archs on 12 cores and CUDA 12.4, 9 s `make test`). Configuring applies `patches/` to the submodule
in place; `.gitmodules` sets `ignore = dirty` for it, so `git status` stays quiet about those files and reports the
submodule only when its pinned commit changes (`git -C third_party/llama.cpp diff` still shows the patches).

`make build` configures once and builds only the four targets above, not upstream's `all`. Options, as `make`
variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `CUDA_ARCHS` | `61;75;86;89` | GTX 10, RTX 20 / GTX 16, RTX 30, RTX 40. One arch (`CUDA_ARCHS=86`) builds several times faster. An arch below 75 turns on upstream's `STRATA_EXPERIMENTAL_SM60`. Arches the installed nvcc cannot compile are dropped with a note. |
| `PORTABLE=1` | off | AVX2 baseline for the CPU expert kernels instead of `-march=native`: build on one box, run on another. |
| `NVCC` | `nvcc` on PATH, else `/usr/local/cuda/bin/nvcc` | the CUDA compiler |
| `HOSTCXX` | newest `g++-NN` that this nvcc accepts | one compiler for the C, C++ and CUDA host sides (a mix fails to link on `__cxa_call_terminate`) |
| `JOBS` | `nproc`, capped at 16 | parallel compile jobs |
| `BUILD_DIR` | `build` | |

`make frontend` builds `unbiased-strata` alone, without CUDA, into `build-frontend/`: for a laptop or a CI box.
`make test` builds that and runs `frontend/tests/`: seven adapter cases against `fake-engine.py` (cancel, drain,
backpressure, child exit, `ERR`) and `e2e.sh`, the HTTP surface a coding agent touches. The `patches/` directory is
applied to the submodule at configure time (one patch, the Qwen3-Coder tool-call grammar; see UPSTREAM.md).

Boxes this has been built and served on: a RunPod RTX 3090 (24 GB, driver 580, CUDA 12.x) and an RTX A6000 (48 GB)
in a Proxmox VM with no route to the internet. The front end's tests also run on macOS.

## Run

```
unbiased-strata --engine <strata|strata-poly|path> -m <model.gguf> [llama-server options] -- <engine options>
```

`-m` names the GGUF the vocabulary and chat template are read from; no tensors are loaded from it by the front end.
`--engine` takes a path, or a bare name looked up beside the program. Everything before `--` is a `llama-server`
option (`--host`, `--port`, `--api-key`, `--alias`, `--temp`, `--top-k`, `--top-p`, `--min-p`,
`--reasoning-format`, `--chat-template-kwargs`, `--sse-ping-interval`, ...); everything after `--` goes to the
engine, which is started as a child process with `--serve` added and spoken to over its line protocol
([docs/BACKENDS.md](docs/BACKENDS.md)). The server answers `/v1/chat/completions` (streaming and not), `/v1/models`,
`/health`, `/props`, `/tokenize`, `/detokenize`, as llama.cpp's server does, one request at a time.

The exact lines that produced the measured rows. Upstream's installer would have chosen these flags for a 24 GB card;
here they are written out.

**Qwen3.6-35B-A3B UD-Q3_K_M or UD-IQ4_XS from the GGUF** (`strata-poly`; the `-MTP` files from
`unsloth/Qwen3.6-35B-A3B-MTP-GGUF`, which carry the draft block). The expert profile file is created by the engine when
it is missing and read on later starts; pass the same path each time.

```
build/bin/unbiased-strata --engine build/bin/strata-poly \
  -m /models/Qwen3.6-35B-A3B-UD-Q3_K_M.gguf --host 127.0.0.1 --port 18091 --alias qwen3.6-35b-a3b-ud-q3_k_m \
  -- --model /models/Qwen3.6-35B-A3B-UD-Q3_K_M.gguf --max-context 32768 \
     --expert-profile /models/expert-profile-q3km.txt --tail-skip 6
```

With pictures, add `--mmproj /models/mmproj-F16.gguf` (the projector from the same `-MTP` repository) and
`--threads N` for the encoder before the `--`. The front end checks the projector's width against the model's at
start, encodes each picture with llama.cpp's mtmd and hands the rows to the engine over upstream's `GENI`
protocol. A picture is at most 300 rows by default (upstream's installer's CPU setting; `--image-max-tokens`
changes it), which read a 1920x1080 dashboard correctly in 15 s of encoding on a Ryzen 7 1700.

**Qwen3.8-Flash-Next GSQ-RCO IQ3_XXS** (`strata`; the two GGUF shards, the pack directory made from shard 1, the MTP
draft directory). On the 24 GB card:

```
build/bin/unbiased-strata --engine build/bin/strata \
  -m /models/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf \
  --host 127.0.0.1 --port 18090 --alias qwen3.8-flash-next-iq3_xxs --sse-ping-interval 10 \
  -- --pack /models/pack-iq3-xxs \
     --native /models/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf \
     --ple-gguf /models/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf \
     --expert-profile /models/pack-iq3-xxs/expert-profile.bin \
     --expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mtp /models/mtp \
     --max-context 65536 --kv int8 --ple-io ram --pool-workers 15 --kv-resident 32768
```

On the 48 GB card the same line with `--resident-experts --ple-io mmap` in place of `--expert-cache auto --ple-io ram
--pool-workers 15` (the whole expert set stays in VRAM): `bench/unbiased/2026-10-17-a6000-flash-next-iq3xxs-step6/server-command.sh`.

What the flags do, per upstream's [docs/DETAILS.md](docs/DETAILS.md) and [docs/BACKENDS.md](docs/BACKENDS.md):
`--expert-cache auto` sizes the VRAM expert cache from the free memory after everything else is loaded; `--prefill auto`
picks the prompt chunking; `--spec 4` with `--spec-min-p 0.5` is the MTP speculative window and how sure the draft
must be to extend it; `--kv int8` with `--kv-resident 32768` keeps 32K tokens of attention reads in VRAM as int8 and
streams the rest from host memory; `--ple-io ram|mmap|direct` is how the second shard, the 28.8 GB n-gram table, is
read (RAM, mapped, or unbuffered from the SSD); `--pool-workers` is how many CPU threads compute experts; `--tail-skip 6`
is `strata-poly`'s route-tail skip, the value upstream's installer sets for Qwen3.6.

### Preparing a Flash-Next pack

`strata-poly` reads a GGUF as it is. `strata` needs a pack directory and an MTP draft directory made once, offline
except for the draft download, with upstream's tools (`tools/requirements.txt`: numpy, regex; `gguf-py` comes from the
submodule). This is what upstream's installer ran; it has not been re-run in this fork, which used the pack and MTP
directory upstream's installer made on 2026-10-05 (`docs/MODEL-FILES.md`).

```
python tools/iq_pack.py --gguf <shard1> --out <pack>             # --compat-bf16 for Unsloth files
STRATA_SOURCE=huggingface python tools/mtp_fetch.py fetch --out <mtp>
python tools/mtp_pack.py --src <mtp> --experts q2_0 --out <mtp>/mtp-q2_0.gguf
python tools/mtp_rt.py --gguf <mtp>/mtp-q2_0.gguf --out <mtp>/rt
cp data/draft_vocab.bin <mtp>/rt/draft_vocab.bin
```

Model files themselves are downloaded on a machine with network access and copied to the inference box; the fork does
not fetch them. The files that have been served, with sizes and SHA-256, are in
[docs/MODEL-FILES.md](docs/MODEL-FILES.md).

## Measured

All numbers are from `bench/unbiased/`, each directory with the command, the raw client output, the server log and the
model files' checksums. Tokens per second, median of 3 runs. Upstream is PolyStrata v0.1.45-poly.1 with its Python
server, on the same card, the same files, the same client, back to back.

**Upstream versus this fork, RTX 3090, 2026-10-18** (`bench/unbiased/2026-10-17-3090pod-step9/README.md`; the client is
upstream's `tools/strata_bench.py --runs 3 --long` plus a three-document sustained supplement):

| Model | Workload | upstream | fork |
| --- | --- | --- | --- |
| Flash-Next IQ3_XXS, 64K ctx | chat decode | 87.1 | 103.1 |
| | sustained decode, 512 tokens | 105.1 | 119.1 |
| | prefill 4K / 16K / 32K | 1924 / 2342 / 2393 | 2065 / 2531 / 2616 |
| | agent turn decode | 110.6 | 116.8 |
| Qwen3.6 UD-Q3_K_M, 32K ctx | chat decode | 220.8 | 213.5 |
| | sustained decode, 512 tokens | 207.6 | 200.0 |
| | prefill 4K / 16K | 3652 / 3570 | 3822 / 3486 |
| | agent turn decode | 194.0 | 186.9 |

Flash-Next: the fork is ahead on every workload. Qwen3.6: decode is within the run-to-run range; 16K prefill is 2.3 %
slower with non-overlapping ranges and is recorded as an open finding. The two engines were built separately in the
two trees, so an engine-build difference is not excluded.

**pi on a fixed coding task** (pi 0.85.1, Flash-Next on the 3090, three runs a side, `…-step9/row3/`): every run
completed the task. Generated tokens per wall-clock second, the whole run: upstream 72.1, fork 76.6 (medians); the raw
wall times (36.3 vs 44.7 s) follow the length of each sampled trajectory.

**Short-prompt decode through the fork, first end-to-end runs** (`…-step6/`, 2026-10-17; ranges over the smoke
requests, not medians of a benchmark):

| Model | RTX 3090 | RTX A6000 |
| --- | --- | --- |
| Qwen3.6 UD-Q3_K_M | 211 to 227 | 214 to 235 |
| Qwen3.6 UD-IQ4_XS | 205 to 245 | 207 to 215 |

Greedy answers to the same prompt were identical on the two boxes and identical to upstream on the pod for both
Flash-Next and Qwen3.6 (text and token count). Against llama.cpp at the pinned commit (PLAN.md step 12,
`bench/unbiased/correctness/`, 2026-10-18 on the A6000): teacher-forced on 16 sequences per model, both engines' per-step
distributions are as close to llama.cpp's GPU run as llama.cpp's own CPU run is (mean KL 0.6 to 1.2x that spread on every
set and arm), and the greedy token agrees at every position with a 0.5-nat margin except a handful of near ties per arm
(Qwen3.6: 4 of 2,700; Flash-Next: 0 to 4 of about 2,880 depending on the arm). The findings, each with a ticket, are in
that directory's README: upstream's own `poly_expert_parity` exceeds its bound on one expert; speculation is not bitwise
inert above 4-token windows (it passes the KL gate); `strata`'s bits depend on the free VRAM at start when not every
expert fits the card. Extended 2026-10-19 to DeepSeek V4 Flash UD-IQ2_XXS and GLM 5.3 Flash 3.0bit on a 2x RTX PRO 6000 pod (section 8 of that record): T2 holds on every set and arm, 0.69 to 1.13x llama.cpp's own CPU-vs-GPU spread; a handful of 0.5-nat-margin flips per model where both llama.cpp runs agree (USTRAT-10); on GLM the draft block's VRAM moves 52 experts to the CPU, so its answers are not bitwise the no-draft ones (USTRAT-9); and llama.cpp master's CPU run differs from the pinned commit's by as much as the engine does, so the DeepSeek numbers are against 3cf03257 specifically (USTRAT-11).

**Model acceptance (PLAN.md step 13, 2026-10-19).** A coding agent (pi 0.85.1, in a container with tools, sampled as
the model card asks) completed four work items through the fork's server with every served model: a Markdown
table-of-contents CLI with tests, an HTTP key-value store with persistence, three planted bugs, and a browser
Minesweeper that a headless browser can play; Minesweeper again at temperature 1.0. Flash-Next IQ3_XXS and Qwen3.6
UD-Q3_K_M on an RTX 3090 and Qwen3.6 UD-IQ4_XS on the A6000 pass as is (the IQ4_XS temperature-1.0 page threw a
`ReferenceError` of the agent's own making); DeepSeek V4 Flash UD-IQ2_XXS and GLM 5.3 Flash 3.0bit on a B200 pass
after the two fixes under "Known limits" (argument order; GLM's architecture name in the vocabulary load). The
API-only checks (`frontend/tests/acceptance-real-engine.sh`) hold decode and prompt reading within 15 % of step 9 on
the 3090 (Flash-Next with the installer's `--pool-workers 15`; 24 costs 14 %) and record the first B200 figures
(72 and 74 tok/s decode on one card). Record: `bench/unbiased/2026-10-19-step13-acceptance/`. pi's compaction defaults (reserve 16K, keep the last 20K tokens) assume a window well above 64K: against a server at `--max-context 32768` a long pi session compacts to no effect and then sends `max_tokens: 1` ("Response was truncated before completion"); serve 128K or more to pi, or lower pi's `compaction` settings (USTRAT-8).

## Known limits

- One request at a time: the front end has one slot and queues the rest.
- No constrained decoding: a request's `response_format` or tool schema is parsed, not enforced at the sampler; the
  server logs `a grammar was requested; this engine does not constrain sampling` once per such request. One
  consequence is handled: llama.cpp's tool-call grammars expect required arguments in the schema's order, which
  only a constrained sampler guarantees, so `patches/llama.cpp-any-argument-order.patch` accepts any order (DeepSeek
  V4 Flash and GLM 5.3 Flash write `content` before `path`; without the patch their finished calls came back as parse
  errors). A tool call that is malformed in other ways is still an error to the client, not a retry.
- GLM 5.3 Flash's template honours `reasoning_effort` only as `low` or `high` and treats anything else as `max`, at
  which it thinks to the token cap on a coding task; send one of the two, or set `--chat-template-kwargs
  '{"reasoning_effort":"low"}'` on the server as the default.
- Pictures are encoded on the CPU, 15 s each at the 300-row default on an 8-thread Ryzen 7 1700, quadratic in rows
  (2040 rows took 146 s). The front end's ggml is built without CUDA (the engines bring their own), so `--mmproj-gpu`
  is refused; giving the encoder the card is a build change to llama.cpp's ggml in this tree, not done.
- Streams always end with a usage chunk (empty `choices`), as upstream's server does, whether or not the client asked
  for `stream_options.include_usage`.
- On SIGTERM the front end exits with status 1 after stopping the engine. Harmless under a shell; a systemd unit should
  not use `Restart=on-failure` until this is fixed.
- The engines are upstream's at v0.1.45-poly.1, unmodified, including their correctness; the checks against llama.cpp at
  the pinned commit are above ("Measured") and in `bench/unbiased/correctness/`. Two things to know from them: `strata`'s
  answer can differ from one start to the next on a card that does not hold every expert, because `--expert-cache auto`
  sizes the cache from the free VRAM and the CPU-computed share of the misses rounds differently (a fixed `--expert-cache N`
  pins it); and `strata-poly`'s drafting changes low-order bits above 4-token windows (within llama.cpp's own CPU/GPU spread).

## What was removed, and the rule

A file was removed only if it (1) reaches the network during setup, build or start, (2) puts Python between a
request and a token, (3) breaks the one-command build, or (4) is marketing. The list, by rule:
[UPSTREAM.md, Removed](UPSTREAM.md#removed). Everything else from upstream stays in the tree, built or not, including
its engineering docs under `docs/`, its offline tools under `tools/`, its parity tests and its benchmark records.

## Credits and license

The engines are PolyStrata's, by VecSzn and contributors, built on [Strata](https://github.com/Niko1221/Strata) by
Niko1221. The front end is built from [llama.cpp / ggml](https://github.com/ggml-org/llama.cpp)'s server, common and
mtmd code. Qwen3.8-Flash-Next and Qwen3.6-35B-A3B are by the Qwen team; the IQ3_XXS GSQ-RCO file is
[ISTA-DASLab](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF)'s, the Qwen3.6 files are
[Unsloth](https://huggingface.co/unsloth)'s. Upstream's full credits: [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md#credits).
MIT License ([LICENSE](LICENSE)); some parts and every model have their own licenses
([which ones](docs/HOW_IT_WORKS.md#license)).
