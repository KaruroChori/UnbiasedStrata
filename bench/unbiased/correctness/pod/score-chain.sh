#!/bin/bash
# Scores every arm against its family's reference, derives the committed top-20 tables, and runs the T0 byte
# comparison (draft arm top.txt == base arm top.txt).  Usage: score-chain.sh [fam ...]
source /opt/us2-correctness/bin/env.sh
cd $C
for fam in ${@:-deepseek glm}; do
  fam_vars $fam || exit 1
  export US2_CORR_ROOT=$ROOT US2_VOCAB=$VOCAB
  for arm in base draft pb512; do
    [ -d $ROOT/poly/$fam/$arm ] || continue
    python3 $ROOT/score-all.py poly $fam $fam $arm > logs/scores-$fam-$arm.out 2>&1
  done
  python3 $ROOT/derive-top20.py $ROOT/reference/$fam > logs/top20-$fam.out 2>&1
  for f in $ROOT/poly/$fam/base/*.top.txt; do s=$(basename $f .top.txt)
    if cmp -s $f $ROOT/poly/$fam/draft/$s.top.txt; then echo "$s T0 same"; else echo "$s T0 DIFFER"; fi
  done > logs/t0-$fam.out 2>&1
done
echo SCORE_DONE
