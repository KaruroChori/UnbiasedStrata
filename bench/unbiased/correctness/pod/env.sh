#!/bin/bash
# Shared settings for the DeepSeek V4 Flash / GLM 5.3 Flash correctness chains on a RunPod box (2026-10-19).
# Layout on the pod: /opt/us2-correctness/<fam>/{inputs,reference,poly,scores,*.py}; logs in /opt/us2-correctness/logs.
# Reference builds: DeepSeek -> the pinned llama.cpp 3cf03257 (knows deepseek4); GLM -> llama.cpp master 99db719b
# (the pinned tree does not know glm5-next).  The master dump tool aborts in sched_reserve when CUDA sees no device,
# so every run, CPU included, keeps a GPU visible.
C=/opt/us2-correctness
export US2_POLY=${US2_POLY:-/opt/us2-build/build/bin/strata-poly}
export STRATA_DUMP_THREADS=${STRATA_DUMP_THREADS:-40}
fam_vars() {   # fam_vars <deepseek|glm>: sets GGUF, DUMP, VOCAB, ROOT
  case $1 in
    deepseek) GGUF=/opt/us2-models/deepseek/UD-IQ2_XXS/DeepSeek-V4-Flash-0731-UD-IQ2_XXS-00001-of-00003.gguf
              DUMP=/opt/llamacpp-ref/tools/q36_llama_dump; VOCAB=129280;;
    glm)      GGUF=/opt/us2-models/glm/GLM-5.3-Flash-GSQ-RCO-3.0bit-q4kattn.gguf
              DUMP=/opt/llamacpp-master/tools/q36_llama_dump; VOCAB=154880;;
    *) echo "unknown family $1" >&2; return 1;;
  esac
  ROOT=$C/$1
}
