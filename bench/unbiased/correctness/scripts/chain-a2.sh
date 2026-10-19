#!/bin/bash
# Replaces the arm part of chain-a.sh after the --short-read finding: the long sequences as two requests.
cd ~/us2-results/correctness || exit 1
python3 strata-run.py fp16 d4k d16k d31k r16k >> strata-fp16.out 2>&1
for arm in t4 int8; do python3 strata-run.py $arm > strata-$arm.out 2>&1; done
python3 strata-run.py int8str > strata-int8str.out 2>&1
python3 strata-run.py pf512 > strata-pf512.out 2>&1
echo CHAIN_A_DONE >> chain-a.out
echo CHAIN_A2_DONE
