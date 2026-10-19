#!/bin/bash
# After the CPU reference: the CPU-tier arms with a fixed, smaller expert cache (cpu, cpu2, pcie), realigned.
cd ~/us2-results/correctness || exit 1
while ! grep -q FN_CPU_DONE ref-flash-next-cpu.out; do sleep 60; done
for arm in cpu cpu2 pcie; do python3 strata-run.py $arm > strata-$arm.out 2>&1; done
for arm in cpu cpu2 pcie; do python3 realign.py $arm > realign-$arm.out 2>&1; done
echo CHAIN_A5_DONE
