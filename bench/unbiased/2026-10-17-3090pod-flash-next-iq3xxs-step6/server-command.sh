#!/bin/bash
# UnbiasedStrata 2 step 6, row 1: Flash-Next IQ3_XXS through the fork front end. Engine flags are upstream PolyStrata
# v0.1.45-poly.1 run of 2026-10-17 on this pod (results/polystrata-v0.1.45-poly.1-20261017/server.json), verbatim;
# the files are the same bytes staged on the local disk (/opt/us2-models/stage.sh), because the FUSE volume stalls.
exec /opt/us2-build/build/bin/unbiased-strata --engine /opt/us2-build/build/bin/strata \
  -m /opt/us2-models/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf \
  --host 127.0.0.1 --port 18090 --alias qwen3.8-flash-next-iq3_xxs \
  -- --pack /opt/us2-models/pack-iq3-xxs --native /opt/us2-models/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf \
  --ple-gguf /opt/us2-models/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile /opt/us2-models/pack-iq3-xxs/expert-profile.bin \
  --expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mtp /opt/us2-models/mtp \
  --max-context 65536 --kv int8 --ple-io ram --pool-workers 15 --kv-resident 32768
