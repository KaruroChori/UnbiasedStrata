#!/bin/bash
# Reference-drift probe: llama.cpp master (99db719b) --ngl 0 on the DeepSeek short and code sequences, teacher-forced
# on the pinned GPU run's answers, as reference/deepseek-master/<seq>.cpu.full.  Waits for the CPU chain to finish so
# the two CPU runs do not share the cores.  Then probe-master-tab.py tabulates it against the pinned GPU and CPU runs.
source /opt/us2-correctness/bin/env.sh
fam_vars deepseek; cd $C
while ! grep -q CHAIN_CPU_DONE logs/chain-cpu.log 2>/dev/null; do sleep 60; done
# ref-run.py names the answer file after the tag: point the probe tag at the pinned run's answers
for a in $ROOT/inputs/*/*.answer.deepseek.ids; do ln -sf $(basename $a) ${a%.deepseek.ids}.deepseek-master.ids; done
export US2_CORR_ROOT=$ROOT US2_DUMP=/opt/llamacpp-master/tools/q36_llama_dump US2_VOCAB=$VOCAB
python3 $ROOT/ref-run.py deepseek-master $GGUF cpu p01 p02 p03 p04 p05 p06 p07 p08 p09 lru puzzle > logs/probe-master-cpu.out 2>&1
python3 bin/probe-master-tab.py $ROOT deepseek deepseek-master $VOCAB > logs/probe-master-tab.out 2>&1
echo "$(date -u +%FT%TZ) PROBE_DONE" >> logs/probe-master-cpu.out
