#!/bin/bash
# After the CPU-tier arms: derive the committed top-20 of the Flash-Next reference, score every strata arm.
cd ~/us2-results/correctness || exit 1
while ! grep -q CHAIN_A5_DONE chain-a5.out; do sleep 60; done
python3 derive-top20.py reference/flash-next > derive-top20-flash-next.out 2>&1
for arm in fp16 t4 int8 int8str pf512 pin pin2 pint4 pincpu pingpu cpu cpu2 pcie; do
  echo "=== $arm"; python3 score-all.py strata flash-next $arm 2>&1 | grep -vE "reference incomplete"
done > scores-flash-next.out 2>&1
echo SCORES_DONE
