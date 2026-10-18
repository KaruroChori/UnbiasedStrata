# Model files tried with UnbiasedStrata 2

(Upstream's `docs/MODELS.md` describes the models in general; this file is the fork's record of files actually run.)

A fork of an inference engine has to say which model files it has actually run. One row per file (not per model):
the same quantization from two Hugging Face repos is two files. "Works" means the front end served `/v1/chat/completions`
with correct text, streaming, a tool call and reasoning, through `frontend/tests/`-style checks against the real engine;
"measured" means a row exists under `bench/unbiased/`. Hashes are SHA-256 of the file as served.

| File | Source | Size (bytes) | SHA-256 | Engine | Boxes | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf` + `-00002-of-00002.gguf`, with `pack-iq3-xxs/` and `mtp/` made by upstream's `tools/iq_pack.py` and `tools/mtp_rt.py` | Niko1221 Strata GSQ-RCO release; pack and MTP built 2026-10-05 (`artifacts.sha256` on the pod) | 47,039,860,096 + 28,800,138,432 | shards unhashed; pack `dense.bin` `d2af3d83…`, mtp `dense.bin` `c724dc0b…` (full hashes in `bench/unbiased/*/engine-info.txt`) | `strata` | RTX 3090 pod, A6000 VM | works (2026-10-17: A6000 `bench/unbiased/2026-10-17-a6000-flash-next-iq3xxs-step6/`, RTX 3090 pod `…-3090pod-flash-next-iq3xxs-step6/`; the greedy answers of the two boxes are identical, and identical to upstream PolyStrata v0.1.45-poly.1 on the same files on the pod: `…-3090pod-…/upstream-compare/`) |
| `Qwen3.6-35B-A3B-UD-Q3_K_M.gguf` (MTP draft block in the file) | `unsloth/Qwen3.6-35B-A3B-MTP-GGUF` @ `5bc3e238` | 17,104,402,720 | `8966dd0cd8c543c4228490a2a8b0e0814fc4f1e6a8e199ceed4de6754ae7b8e1` | `strata-poly` | pod, A6000 VM | the measured configuration of PLAN.md section 6; on the pod and on the A6000 VM, not yet run |
| `Qwen3.6-35B-A3B-UD-IQ4_XS.gguf` (MTP draft block in the file; `/Volumes/models/qwen3.6/MTP/…-IQ4_XS-MTP.gguf` locally) | `unsloth/Qwen3.6-35B-A3B-MTP-GGUF` @ `5bc3e238` | 18,209,036,576 | `df27a780435b7b45c2597536112ea3cb091f8544c3d0c3318d9f4258b31f7adf` | `strata-poly` | pod, A6000 VM | works (2026-10-17, A6000: `bench/unbiased/2026-10-17-a6000-qwen36-ud-iq4xs-mtp-step6/`; 207 to 215 tok/s decode on short prompts, 83% draft acceptance); chosen as the local-use quant |
| `Qwen3.6-35B-A3B-UD-IQ4_XS.gguf` (no draft block) | `unsloth/Qwen3.6-35B-A3B-GGUF` | 17,730,509,792 | `649d7508507b84638732c4f52c24c8b15843c6dca2f3ff793ae07c14a67ebbb3` | `strata-poly` | pod | on disk, untried: without the draft block the engine runs without speculation |
| `Qwen3.6-35B-A3B-UD-Q3_K_M.gguf` (no draft block) | `unsloth/Qwen3.6-35B-A3B-GGUF` | 16,600,710,112 | `1b715841683f960bd9a49f008181bd910ee169b78d4cf465b6fde7f4d929ff99` | `strata-poly` | pod | on disk, untried; downloaded by mistake for the row above, kept to compare |

Rules: a file is added here when it is first downloaded for this fork, with its hash from the Hugging Face LFS object id
or from `sha256sum` on the box; its status changes only with a result that is on disk under `bench/unbiased/`. Models
upstream lists but nobody here has run stay out of this table and are "present, unmeasured" in `README.md`.
