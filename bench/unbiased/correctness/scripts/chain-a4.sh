#!/bin/bash
# After check-batch: the pinned-placement arms (pin, pin2, pint4, pincpu, pingpu), realign every arm, then the
# Flash-Next CPU reference alone on the box. Short set first, long set last.
cd ~/us2-results/correctness || exit 1
FN=/mnt/ds4/unbiased-strata/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf
while pgrep -f "^/bin/bash ./check-batch.sh" > /dev/null; do sleep 20; done
echo CHECK_BATCH_DONE >> check-batch.out
for arm in pin pin2 pint4 pincpu pingpu; do python3 strata-run.py $arm > strata-$arm.out 2>&1; done
for arm in fp16 t4 int8 int8str pf512 pin pin2 pint4 pincpu pingpu; do python3 realign.py $arm > realign-$arm.out 2>&1; done
echo ARMS_DONE
echo "cpu reference $(date -u +%H:%M:%S)" >> ref-flash-next-cpu.out
( time python3 ref-run.py flash-next $FN cpu p01 p02 p03 p04 p05 p06 p07 p08 p09 ) >> ref-flash-next-cpu.out 2>&1
( time python3 ref-run.py flash-next $FN cpu lru puzzle ) >> ref-flash-next-cpu.out 2>&1
( time python3 ref-run.py flash-next $FN cpu r16k d4k ) >> ref-flash-next-cpu.out 2>&1
( time python3 ref-run.py flash-next $FN cpu d16k d31k ) >> ref-flash-next-cpu.out 2>&1
echo FN_CPU_DONE >> ref-flash-next-cpu.out
