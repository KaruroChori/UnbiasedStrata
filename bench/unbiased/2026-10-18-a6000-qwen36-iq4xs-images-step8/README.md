# Step 8: a screenshot through the fork to Qwen3.6, A6000 VM, 2026-10-18 UTC

PLAN.md step 8 gate: "a screenshot through pi to Qwen3.6; projector width checked against the model". Box: the A6000
VM (NVIDIA RTX A6000, driver 550.163.01; AMD Ryzen 7 1700, 8 threads given to the encoder). Front end
`unbiased-strata` at fork 17e27213 (VM build `~/us2-build` 52229a4, same content), engine `strata-poly` unchanged
since the import, model `Qwen3.6-35B-A3B-UD-IQ4_XS.gguf` with its draft block (`docs/MODEL-FILES.md`), projector
`mmproj-F16.gguf` from `unsloth/Qwen3.6-35B-A3B-MTP-GGUF` (sha256 `71f3cbc1…`, 899,283,584 bytes). Launch line:
`server-command.sh` here (the engine flags are upstream's qwen36 ones; the front end adds `--mmproj … --threads 8`).

## The picture

`facts.html` rendered at 1920x1080 by a headless Chromium into `facts.png`: a made-up warehouse dashboard with six
facts the model cannot guess (warehouse 7, Tuesday 14 October 2026, 4,812 pallets, 137 orders, 9 damaged, shift
manager Priya Raman, Forklift #3 out of service). Question (`ask-image.py`, temperature 0, `enable_thinking`
false): "Read this dashboard screenshot and answer with one line each: (1) the warehouse number and the date,
(2) pallets in stock, (3) orders shipped today, (4) damaged items, (5) the shift manager's name, (6) which forklift
is out of service."

## Runs

| Run | Front end | Encoder | Rows (grid) | Encode | Prompt tokens | Prefill | Decode | Facts right | File |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 71886db0 + d0bc0d86, no cap | CPU, 8 threads | 2040 (60x34) | 146.2 s | 2117 | 639 ms | 210 ms for 52 tokens, 38/38 drafts accepted | 6/6 | `api-run1.json` |
| 2 | 1026afb2, `--mmproj-gpu`, no cap | labelled GPU, ran on the CPU (see below) | 2040 (60x34) | 146.1 s | 2117 | 621 ms | 209 ms for 52 tokens, 38/38 | 6/6 | `api-run2-gpu.json` |
| 3 | 17e27213, default cap 300 rows | CPU, 8 threads | 276 (23x12) | 15.4 s | 353 | 165 ms | 234 ms for 58 tokens, 42/44 | 6/6 | `api-run3-cap300.json` |
| 4 (pi) | 17e27213, same server as run 3 | CPU, 8 threads | 276 (23x12) | 15.4 s | 861 (pi's system prompt) | | sampled at pi's defaults (temperature 0.6, top_p 0.95, top_k 20) | 6/6 | `pi-run1.txt` |

Prefill and decode are the engine's `timings`; encode is the front end's `encoded in … ms` log line
(`server-log-excerpt.txt` for runs 3 and 4; runs 1 and 2 were logged by the server instance that the relaunch for
run 3 replaced, numbers copied from that log before it was overwritten). The answers of all four runs name the same
six facts; run 3's and 4's text is in the JSON and in `pi-run1.txt`.

Run 4 is the gate's "through pi": `pi -p --no-session --no-tools --thinking off --provider "UnbiasedStrata 2"
--model qwen3.6-35b-a3b-ud-iq4_xs @facts.png "<question>"`, pi 0.85.1, with the model's `input` set to
`["text","image"]` in pi's `models.json` (pi sends the picture as an `image_url` data URL in the chat request, the
same shape upstream's server took). A first pi attempt with session, extensions and skills enabled printed nothing
and sent no request; the second, with `--no-session --no-extensions --no-skills`, is the run recorded. Not chased:
pi-side, the server saw no request.

## Projector width check

At start the front end reads `clip.vision.projection_dim` from the projector file (2048) and
`qwen35moe.embedding_length` from the model (2048) and refuses to start on a mismatch; the token `<|image_pad|>` must
tokenize to one id (248056). Log line: `vision: … rows of 2048, encoder on the CPU (8 CPU threads), at most 300 rows
a picture, image_pad=248056`.

## What was learned

- **Encode time is the cost, and it is quadratic in rows.** 2040 rows took 146 s on this CPU; 276 rows 15.4 s.
  Upstream's installer gave `strata-vision --max-tokens 300` on the CPU and 1024 on the GPU (`setup.py` `VISION`),
  so 17e27213 applies the same default (300 CPU, 1024 GPU; `--image-max-tokens` overrides). At 300 rows the model
  still read all six facts off a 1920x1080 dashboard.
- **`--mmproj-gpu` did nothing (run 2).** The front end's ggml is the submodule's, built without CUDA (the engines
  bring their own); `ldd build/bin/unbiased-strata` lists no CUDA library and the log says `CLIP using CPU backend`.
  Since 17e27213 the flag is refused at start when ggml has no GPU device (`gpu-refusal.log`). Giving the encoder
  the card means building llama.cpp's ggml with CUDA for the front end, a build change that touches the engines'
  ggml too; left open, see README "Known limits".
- The engine side needed nothing: `GENI` with the `SVE1` record file is upstream's own protocol, and the draft block
  kept accepting (38/38 on the long prompt, 42/44 on the short one).

## Files

`facts.html`, `facts.png` (the picture), `ask-image.py` (the client), `api-run{1,2-gpu,3-cap300}.json` (full
responses with `usage` and `timings`), `pi-run1.txt` (pi's answer), `server-command.sh`, `server-log-excerpt.txt`,
`gpu-refusal.log` (the start that `--mmproj-gpu` now fails), `box.txt`.
