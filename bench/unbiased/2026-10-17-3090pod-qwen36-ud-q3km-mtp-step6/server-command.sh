#!/bin/bash
# UnbiasedStrata 2 step 6, row 2 on the RTX 3090 pod: Qwen3.6-35B-A3B-UD-Q3_K_M.gguf (unsloth/Qwen3.6-35B-A3B-MTP-GGUF, draft block in
# the file) on strata-poly through the fork front end. Engine flags as upstream setup.py writes them for the qwen36
# family (--max-context, --expert-profile, --tail-skip 6); the profile file starts empty and the engine writes it.
exec /opt/us2-build/build/bin/unbiased-strata --engine /opt/us2-build/build/bin/strata-poly \
  -m /opt/us2-models/qwen36-mtp/Qwen3.6-35B-A3B-UD-Q3_K_M.gguf --host 127.0.0.1 --port 18091 --alias qwen3.6-35b-a3b-ud-q3_k_m \
  -- --model /opt/us2-models/qwen36-mtp/Qwen3.6-35B-A3B-UD-Q3_K_M.gguf --max-context 32768 --expert-profile /opt/us2-models/qwen36-mtp/expert-profile-qwen36-ud-q3km-mtp.txt --tail-skip 6
