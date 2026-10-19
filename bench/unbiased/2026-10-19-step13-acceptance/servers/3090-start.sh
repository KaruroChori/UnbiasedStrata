#!/bin/bash
# start.sh <flash-next|q3km|iq4xs> : fork front end + engine on the 3090 (24 GB), one model at a time. Flags are the
# fork README 24 GB lines; --pool-workers 24 keeps under the cgroup quota (31 cores). Ports as tools/acceptance/models.tsv
# (the tunnel to the Mac maps them 1:1).
set -u
F=/opt/us2-build; M=/opt/us2-models; S=/opt/us2-servers; cd $S
SH1=$M/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf; SH2=$M/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf
case $1 in
  flash-next) PORT=18092; ALIAS=qwen3.8-flash-next-iq3_xxs-3090; ENGINE=$F/build/bin/strata; MODEL=$SH1
    ARGS="--pack $M/pack-iq3-xxs --native $SH1 --ple-gguf $SH2 --expert-profile $M/pack-iq3-xxs/expert-profile.bin --expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mtp $M/mtp --max-context 65536 --kv int8 --ple-io ram --pool-workers 24 --kv-resident 32768";;
  q3km)  PORT=18094; ALIAS=qwen3.6-35b-a3b-ud-q3_k_m-3090; ENGINE=$F/build/bin/strata-poly; MODEL=$M/qwen36-mtp/Qwen3.6-35B-A3B-UD-Q3_K_M.gguf
    ARGS="--model $MODEL --max-context 32768 --expert-profile $S/expert-profile-q3km.txt --tail-skip 6";;
  iq4xs) PORT=18093; ALIAS=qwen3.6-35b-a3b-ud-iq4_xs-3090; ENGINE=$F/build/bin/strata-poly; MODEL=$M/qwen36-mtp/Qwen3.6-35B-A3B-UD-IQ4_XS.gguf
    ARGS="--model $MODEL --max-context 32768 --expert-profile $S/expert-profile-iq4xs.txt --tail-skip 6";;
  *) echo "flash-next|q3km|iq4xs"; exit 2;;
esac
echo "$(date -u +%FT%TZ) start $1 port $PORT" >> $S/starts.log
ulimit -l unlimited 2>/dev/null; exec $F/build/bin/unbiased-strata --engine $ENGINE -m $MODEL --host 0.0.0.0 --port $PORT --alias $ALIAS --sse-ping-interval 10 -- $ARGS
