#!/bin/bash
# Configuration A on the A6000 VM, after configuration B is done (the card and the RAM are needed whole):
# 1. Flash-Next reference, GPU-partial (STRATA_DUMP_NGL layers on the card, the rest on the CPU backend; the 76 GB of
#    shards do not fit 48 GB), one probe sequence first to find the layer count that fits, then every sequence.
# 2. Flash-Next CPU reference: one probe sequence, timed; the 50 GB box has to page 76 GB of weights.
# 3. strata arms fp16, t4, int8, int8str (d31k), pf512 (long set).
cd ~/us2-results/correctness || exit 1
FN=/mnt/ds4/unbiased-strata/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf
while ! grep -q CHAIN_B_DONE chain-b.out 2>/dev/null; do sleep 60; done
for ngl in 28 24 20 16; do
  echo "probe ngl=$ngl $(date -u +%H:%M:%S)"
  STRATA_DUMP_NGL=$ngl python3 ref-run.py flash-next $FN gpu p00 > ref-flash-next-gpu-probe-$ngl.out 2>&1
  if grep -q "steps" ref-flash-next-gpu-probe-$ngl.out; then echo "ngl=$ngl fits: $(cat ref-flash-next-gpu-probe-$ngl.out)"; echo $ngl > reference/flash-next/NGL.txt; break; fi
  rm -f reference/flash-next/p00.gpu.full inputs/short/p00.answer.flash-next.ids
done
NGL=$(cat reference/flash-next/NGL.txt 2>/dev/null)
if [ -n "$NGL" ]; then
  STRATA_DUMP_NGL=$NGL python3 ref-run.py flash-next $FN gpu > ref-flash-next-gpu.out 2>&1
  echo "cpu probe $(date -u +%H:%M:%S)"; ( time timeout 7200 python3 ref-run.py flash-next $FN cpu p00 ) > ref-flash-next-cpu-probe.out 2>&1
  cat ref-flash-next-cpu-probe.out
fi
for arm in fp16 t4 int8; do python3 strata-run.py $arm > strata-$arm.out 2>&1; done
python3 strata-run.py int8str > strata-int8str.out 2>&1
python3 strata-run.py pf512 > strata-pf512.out 2>&1
echo CHAIN_A_DONE
