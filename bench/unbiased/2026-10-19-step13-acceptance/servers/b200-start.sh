#!/bin/bash
# start.sh <deepseek|glm> : fork front end + strata-poly, one card each (DeepSeek on GPU 0, GLM on GPU 1), as docs/DEEPSEEK.md
# and docs/GLM.md give the engine args, --pool-workers below the cgroup quota (46 cores).
set -u; FE_EXTRA=${FE_EXTRA:-}
F=/opt/us2-build; M=/opt/us2-models; S=/opt/us2-servers; cd $S
case $1 in
  deepseek) GPU=0; PORT=18095; ALIAS=deepseek-v4-flash-ud-iq2_xxs-b200; MODEL=$M/deepseek/UD-IQ2_XXS/DeepSeek-V4-Flash-0731-UD-IQ2_XXS-00001-of-00003.gguf
            ARGS="--model $MODEL --max-context 32768 --expert-profile $S/deepseek.profile --conversation-cache-mib 8192";;
  glm)      GPU=1; PORT=18096; ALIAS=glm-5.3-flash-3.0bit-b200; MODEL=$M/glm/GLM-5.3-Flash-GSQ-RCO-3.0bit-q4kattn.gguf
            ARGS="--model $MODEL --max-context 32768 --expert-profile $S/glm.profile --conversation-cache-mib 8192";;
  *) echo "deepseek|glm"; exit 2;;
esac
echo "$(date -u +%FT%TZ) start $1 gpu $GPU port $PORT" >> $S/starts.log
ulimit -l unlimited 2>/dev/null; exec env CUDA_VISIBLE_DEVICES=$GPU $F/build/bin/unbiased-strata --engine $F/build/bin/strata-poly -m $MODEL --host 0.0.0.0 --port $PORT --alias $ALIAS --sse-ping-interval 10 $FE_EXTRA -- $ARGS
