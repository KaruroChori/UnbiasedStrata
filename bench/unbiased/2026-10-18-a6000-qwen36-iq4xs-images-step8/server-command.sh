#!/bin/bash
# UnbiasedStrata 2 step 6, row 2 on the A6000 VM: Qwen3.6-35B-A3B UD-IQ4_XS (unsloth .../Qwen3.6-35B-A3B-MTP-GGUF, draft
# block in the file) on strata-poly through the fork front end. Engine flags as upstream setup.py writes them for the
# qwen36 family (--max-context, --expert-profile, --tail-skip 6); the profile file starts empty and the engine writes it.
export CUDA_MODULE_LOADING=EAGER
exec /home/rk/us2-build/build/bin/unbiased-strata --engine /home/rk/us2-build/build/bin/strata-poly \
  -m /mnt/ds4/unbiased-strata/qwen36/Qwen3.6-35B-A3B-UD-IQ4_XS.gguf --host 127.0.0.1 --port 18091 --alias qwen3.6-35b-a3b-ud-iq4_xs --mmproj /mnt/ds4/unbiased-strata/qwen36/mmproj-F16.gguf --threads 8 \
  -- --model /mnt/ds4/unbiased-strata/qwen36/Qwen3.6-35B-A3B-UD-IQ4_XS.gguf --max-context 32768 --expert-profile /mnt/ds4/unbiased-strata/qwen36/expert-profile-iq4xs.txt --tail-skip 6
