#!/bin/bash
# After chain-a2: the fp16 run of p09 (killed mid-run when chain-a was stopped), realign every arm, the check-batch
# runs (plan run order step 6), then the Flash-Next CPU reference alone on the box (it was RAM-starved beside
# strata --serve). Short set first, long set last.
cd ~/us2-results/correctness || exit 1
FN=/mnt/ds4/unbiased-strata/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf
while ! grep -q CHAIN_A2_DONE chain-a2.out; do sleep 30; done
python3 strata-run.py fp16 p09 >> strata-fp16.out 2>&1
for arm in fp16 t4 int8 int8str pf512; do python3 realign.py $arm > realign-$arm.out 2>&1; done
./check-batch.sh > check-batch.out 2>&1
echo "cpu reference $(date -u +%H:%M:%S)" >> ref-flash-next-cpu.out
( time python3 ref-run.py flash-next $FN cpu p01 p02 p03 p04 p05 p06 p07 p08 p09 ) >> ref-flash-next-cpu.out 2>&1
( time python3 ref-run.py flash-next $FN cpu lru puzzle ) >> ref-flash-next-cpu.out 2>&1
( time python3 ref-run.py flash-next $FN cpu r16k d4k ) >> ref-flash-next-cpu.out 2>&1
( time python3 ref-run.py flash-next $FN cpu d16k d31k ) >> ref-flash-next-cpu.out 2>&1
echo FN_CPU_DONE >> ref-flash-next-cpu.out
