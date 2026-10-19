#!/bin/bash
# Replaces the tail of chain-b.sh: the CPU references with the dump tool at every hardware thread (the first attempt
# ran llama.cpp's default of 4 threads: 17 minutes into the 16K document), then the scoring.
cd ~/us2-results/correctness || exit 1
Q3=/mnt/ds4/unbiased-strata/qwen36/Qwen3.6-35B-A3B-UD-Q3_K_M.gguf; IQ4=/mnt/ds4/unbiased-strata/qwen36/Qwen3.6-35B-A3B-UD-IQ4_XS.gguf
rm -f reference/qwen36-q3km/*.cpu.* ; sed -i '/--ngl 0/d' reference/qwen36-q3km/command.sh
python3 ref-run.py qwen36-q3km $Q3 cpu > ref-qwen36-q3km-cpu.out 2>&1
python3 ref-run.py qwen36-iq4xs $IQ4 cpu > ref-qwen36-iq4xs-cpu.out 2>&1
for arm in base draft kvq8 pb512; do python3 score-all.py poly qwen36-q3km qwen36-q3km $arm > scores-q3km-$arm.out 2>&1; done
for arm in base draft; do python3 score-all.py poly qwen36-iq4xs qwen36-iq4xs $arm > scores-iq4xs-$arm.out 2>&1; done
echo CHAIN_B_DONE >> chain-b.out
echo CHAIN_B2_DONE
