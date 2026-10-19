#!/bin/bash
# Pull the DeepSeek V4 Flash / GLM 5.3 Flash correctness record from the 2x B200 pod (2026-10-19) into this directory:
# inputs per tokenizer, the references' top-20 extracts and checksums (the f32 logits stay on the pod), the engine
# arms' outputs, the scores, the chain scripts and logs.
set -u
# pod address: override with US2_POD_PORT / US2_POD_HOST (2026-10-19: the B200 pod was replaced by 205.196.144.34:11149)
SSH="ssh -p ${US2_POD_PORT:-11149} -i $HOME/.ssh/id_ed25519"; H=root@${US2_POD_HOST:-205.196.144.34}; P=/opt/us2-correctness
cd "$(dirname "$0")/.." || exit 1
for fam in deepseek glm; do
  mkdir -p inputs-$fam reference/$fam poly/$fam scores/$fam
  rsync -az -e "$SSH" $H:$P/$fam/inputs/ inputs-$fam/
  rsync -az -e "$SSH" --include='*/' --include='*.top20.tsv' --include='*.sha256' --include='*.gen.txt' --include='command.sh' --include='*.force.ids' --exclude='*' $H:$P/$fam/reference/$fam/ reference/$fam/
  rsync -az -e "$SSH" $H:$P/$fam/poly/$fam/ poly/$fam/
  rsync -az -e "$SSH" $H:$P/$fam/scores/$fam/ scores/$fam/
done
mkdir -p reference/deepseek-master logs/2026-10-19
# the reference-drift probe (pod/probe-master-cpu.sh): llama.cpp master's CPU run on DeepSeek, as reference/deepseek-master/
rsync -az -e "$SSH" --include='*/' --include='*.top20.tsv' --include='*.sha256' --include='*.gen.txt' --include='command.sh' --include='*.force.ids' --exclude='*' $H:$P/deepseek/reference/deepseek-master/ reference/deepseek-master/
rsync -az -e "$SSH" $H:$P/logs/probe-master-tab.out $H:$P/logs/probe-master-cpu.out logs/2026-10-19/
rsync -az -e "$SSH" $H:$P/bin/ logs/2026-10-19/bin/
rsync -az -e "$SSH" --exclude='build-*.log' $H:$P/logs/ logs/2026-10-19/
echo pulled
