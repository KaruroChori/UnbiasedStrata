# Pod-side chain scripts (DeepSeek V4 Flash, GLM 5.3 Flash correctness; 2026-10-19)

Copied to `/opt/us2-correctness/bin/` on the pod and run from there; the per-model Python drivers in `../scripts/` are
copied into each model root (`/opt/us2-correctness/<fam>/`) because `score-all.py` expects `score.py` beside it.

| Script | Role |
| --- | --- |
| `env.sh` | paths, per-family model file, reference dump tool and vocabulary size |
| `chain-gpu.sh` | llama.cpp GPU reference (both cards), then engine arms base, draft, pb512 on GPU 0 |
| `chain-cpu.sh` | llama.cpp `--ngl 0` reference once the family's 16 answers exist; restart-safe |
| `score-chain.sh` | scores per arm, top-20 extracts, T0 byte comparison |
| `launch-after-build.sh` | starts both chains once the fork, pinned-reference and master builds report OK |

Shipping the tokenized inputs from a Mac: `COPYFILE_DISABLE=1 tar czf ...`, or delete `._*` files after unpacking.
Without it bsdtar adds AppleDouble `._<name>` entries, the drivers' `inputs/*/*.prompt.ids` glob picks up
`._p00.prompt.ids`, and `json.load` dies on the binary `._p00.json` (cost one chain restart on 2026-10-19).
Results come back with `../scripts/pull-record-2026-10-19.sh` (host and port via `US2_POD_HOST` / `US2_POD_PORT`).
