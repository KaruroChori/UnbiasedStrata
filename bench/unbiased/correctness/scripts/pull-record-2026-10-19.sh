#!/bin/bash
# Pull the DeepSeek V4 Flash / GLM 5.3 Flash correctness record from the 2x B200 pod (2026-10-19) into this directory:
# inputs per tokenizer, the references' top-20 extracts and checksums (the f32 logits stay on the pod), the engine
# arms' outputs, the scores, the chain scripts and logs.
set -u
SSH="ssh -p 30381 -i $HOME/.ssh/id_ed25519"; H=root@38.80.152.146; P=/opt/us2-correctness
cd "$(dirname "$0")/.." || exit 1
for fam in deepseek glm; do
  mkdir -p inputs-$fam reference/$fam poly/$fam scores/$fam
  rsync -az -e "$SSH" $H:$P/$fam/inputs/ inputs-$fam/
  rsync -az -e "$SSH" --include='*/' --include='*.top20.tsv' --include='*.sha256' --include='*.gen.txt' --include='command.sh' --include='*.force.ids' --exclude='*' $H:$P/$fam/reference/$fam/ reference/$fam/
  rsync -az -e "$SSH" $H:$P/$fam/poly/$fam/ poly/$fam/
  rsync -az -e "$SSH" $H:$P/$fam/scores/$fam/ scores/$fam/
done
mkdir -p probes/deepseek-master-cpu logs/2026-10-19
rsync -az -e "$SSH" --include='*.log' --include='*.out' --include='*.sh' --exclude='*' $H:$P/deepseek/probes/ probes/deepseek-master-cpu/
rsync -az -e "$SSH" $H:$P/bin/ logs/2026-10-19/bin/
rsync -az -e "$SSH" --exclude='build-*.log' $H:$P/logs/ logs/2026-10-19/
echo pulled
