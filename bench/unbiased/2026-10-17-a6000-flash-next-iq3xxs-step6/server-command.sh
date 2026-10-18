#!/bin/bash
# UnbiasedStrata 2 step 6, row 1 on the A6000 VM (gpu-vm, VM 220): Flash-Next IQ3_XXS through the fork front end.
# Engine flags: upstream PolyStrata's 2026-10-17 config for the model (pack, native shards, profile, spec 4, MTP) with
# the card-specific choices the UnbiasedStrata 1 service used on this VM (--resident-experts, --ple-io mmap, --kv int8,
# --kv-resident 32768). Same files the old service served.
export CUDA_MODULE_LOADING=EAGER
exec /home/rk/us2-build/build/bin/unbiased-strata --engine /home/rk/us2-build/build/bin/strata \
  -m /mnt/ds4/unbiased-strata/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf \
  --host 127.0.0.1 --port 18090 --alias qwen3.8-flash-next-iq3_xxs \
  -- --pack /mnt/ds4/unbiased-strata/pack-iq3-xxs --native /mnt/ds4/unbiased-strata/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf \
  --ple-gguf /mnt/ds4/unbiased-strata/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --expert-profile /mnt/ds4/unbiased-strata/pack-iq3-xxs/expert-profile.bin \
  --resident-experts --prefill auto --spec 4 --spec-min-p 0.5 --mtp /mnt/ds4/unbiased-strata/mtp \
  --max-context 65536 --kv int8 --ple-io mmap --kv-resident 32768
