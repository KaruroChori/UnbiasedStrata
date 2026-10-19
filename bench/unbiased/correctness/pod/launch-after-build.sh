#!/bin/bash
# Waits for the three builds (fork, pinned reference, master dump tool) and starts the GPU and CPU chains detached.
B=/opt/us2-bringup; C=/opt/us2-correctness
until grep -q FORK_BUILD_OK $B/build-fork.log 2>/dev/null && grep -q REF_BUILD_OK $B/build-ref.log 2>/dev/null && grep -q MASTER_DUMP_OK $B/build-master-dump.log 2>/dev/null; do
  for l in build-fork build-ref build-master build-master-dump; do grep -qE "FAILED|Error [0-9]|error:" $B/$l.log 2>/dev/null && { echo "$(date -u +%FT%TZ) $l failed"; exit 1; }; done
  sleep 15
done
echo "$(date -u +%FT%TZ) builds ok"
cd $C
setsid nohup bash bin/chain-gpu.sh > logs/chain-gpu.log 2>&1 < /dev/null &
setsid nohup bash bin/chain-cpu.sh > logs/chain-cpu.log 2>&1 < /dev/null &
echo "$(date -u +%FT%TZ) chains launched"
