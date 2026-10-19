#!/bin/bash
# GPU side, both families in sequence: llama.cpp GPU reference (greedy answers, full logits), then the engine arms
# base, draft, and pb512 on the long and real-text sequences.  The reference run gets both GPUs (llama.cpp splits layers;
# neither model fits one 96 GB card with its KV at 31K); the engine runs on GPU 0 with its default placement.
# Usage: chain-gpu.sh [fam ...]   (default: deepseek glm).  Ends with CHAIN_GPU_DONE.
source /opt/us2-correctness/bin/env.sh
cd $C; mkdir -p logs
for fam in ${@:-deepseek glm}; do
  fam_vars $fam || exit 1
  export US2_CORR_ROOT=$ROOT US2_DUMP=$DUMP US2_VOCAB=$VOCAB
  echo "$(date -u +%FT%TZ) $fam: reference gpu"
  python3 $ROOT/ref-run.py $fam $GGUF gpu > logs/ref-$fam-gpu.out 2>&1
  for arm in base draft; do
    echo "$(date -u +%FT%TZ) $fam: poly $arm"
    CUDA_VISIBLE_DEVICES=0 python3 $ROOT/poly-run.py $fam $GGUF $arm > logs/poly-$fam-$arm.out 2>&1
  done
  echo "$(date -u +%FT%TZ) $fam: poly pb512 (long, realtext)"
  CUDA_VISIBLE_DEVICES=0 python3 $ROOT/poly-run.py $fam $GGUF pb512 d4k d16k d31k r16k > logs/poly-$fam-pb512.out 2>&1
done
echo "$(date -u +%FT%TZ) CHAIN_GPU_DONE"
