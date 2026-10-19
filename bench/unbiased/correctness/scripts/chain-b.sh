#!/bin/bash
# Configuration B, the rest: waits for the running base arm, moves the Q3_K_M answers to per-model names, runs the
# other Q3_K_M arms, then the IQ4_XS reference (GPU now, CPU after the Q3_K_M CPU reference is done) and its arms,
# then scores everything.
cd ~/us2-results/correctness || exit 1
Q3=/mnt/ds4/unbiased-strata/qwen36/Qwen3.6-35B-A3B-UD-Q3_K_M.gguf; IQ4=/mnt/ds4/unbiased-strata/qwen36/Qwen3.6-35B-A3B-UD-IQ4_XS.gguf
while pgrep -f "^python3 poly-run.py" > /dev/null; do sleep 10; done
for f in inputs/*/*.answer.ids; do case $f in *r16k*) ;; *) mv "$f" "${f%.answer.ids}.answer.qwen36-q3km.ids";; esac; done
ls inputs/*/*.answer*.ids | wc -l
for arm in draft kvq8; do python3 poly-run.py qwen36-q3km $Q3 $arm > poly-q3km-$arm.out 2>&1; done
python3 poly-run.py qwen36-q3km $Q3 pb512 d4k d16k d31k r16k > poly-q3km-pb512.out 2>&1
python3 ref-run.py qwen36-iq4xs $IQ4 gpu > ref-qwen36-iq4xs-gpu.out 2>&1
for arm in base draft; do python3 poly-run.py qwen36-iq4xs $IQ4 $arm > poly-iq4xs-$arm.out 2>&1; done
while pgrep -f "^python3 ref-run.py qwen36-q3km" > /dev/null; do sleep 30; done
python3 ref-run.py qwen36-iq4xs $IQ4 cpu > ref-qwen36-iq4xs-cpu.out 2>&1
for arm in base draft kvq8 pb512; do python3 score-all.py poly qwen36-q3km qwen36-q3km $arm > scores-q3km-$arm.out 2>&1; done
for arm in base draft; do python3 score-all.py poly qwen36-iq4xs qwen36-iq4xs $arm > scores-iq4xs-$arm.out 2>&1; done
echo CHAIN_B_DONE
