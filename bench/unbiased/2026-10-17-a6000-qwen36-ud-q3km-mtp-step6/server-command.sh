#!/bin/bash
# UnbiasedStrata 2 step 6, row 2 on the A6000 VM: Qwen3.6-35B-A3B UD-Q3_K_M (unsloth .../Qwen3.6-35B-A3B-MTP-GGUF, draft
# block in the file; PLAN.md section 6 measured configuration) on strata-poly through the fork front end. Engine flags as
# upstream setup.py writes them for the qwen36 family.
export CUDA_MODULE_LOADING=EAGER
exec /home/rk/us2-build/build/bin/unbiased-strata --engine /home/rk/us2-build/build/bin/strata-poly \
  -m /mnt/ds4/unbiased-strata/qwen36/Qwen3.6-35B-A3B-UD-Q3_K_M.gguf --host 127.0.0.1 --port 18091 --alias qwen3.6-35b-a3b-ud-q3_k_m \
  -- --model /mnt/ds4/unbiased-strata/qwen36/Qwen3.6-35B-A3B-UD-Q3_K_M.gguf --max-context 32768 --expert-profile /mnt/ds4/unbiased-strata/qwen36/expert-profile-q3km.txt --tail-skip 6
