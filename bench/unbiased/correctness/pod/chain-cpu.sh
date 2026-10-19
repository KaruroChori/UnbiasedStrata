#!/bin/bash
# CPU side: llama.cpp --ngl 0 reference, teacher-forced on the GPU run's answers, so it waits until the family's GPU
# reference has produced all 16 answer files.  Reruns only sequences without a cpu.full.sha256 (restart-safe).
# Usage: chain-cpu.sh [fam ...]   (default: deepseek glm).  Ends with CHAIN_CPU_DONE.
source /opt/us2-correctness/bin/env.sh
cd $C; mkdir -p logs
for fam in ${@:-deepseek glm}; do
  fam_vars $fam || exit 1
  export US2_CORR_ROOT=$ROOT US2_DUMP=$DUMP US2_VOCAB=$VOCAB
  while [ "$(ls $ROOT/inputs/*/*.answer*.ids 2>/dev/null | wc -l)" -lt 16 ]; do sleep 60; done
  missing=$(for p in $ROOT/inputs/*/*.prompt.ids; do s=$(basename $p .prompt.ids); [ -f $ROOT/reference/$fam/$s.cpu.full.sha256 ] || echo $s; done)
  echo "$(date -u +%FT%TZ) $fam: reference cpu ($(echo $missing | wc -w) sequences)"
  [ -n "$missing" ] && python3 $ROOT/ref-run.py $fam $GGUF cpu $missing >> logs/ref-$fam-cpu.out 2>&1
done
echo "$(date -u +%FT%TZ) CHAIN_CPU_DONE"
