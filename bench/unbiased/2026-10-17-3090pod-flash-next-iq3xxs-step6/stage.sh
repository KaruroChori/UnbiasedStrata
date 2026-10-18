#!/bin/bash
# UnbiasedStrata 2: the model files on the pod's local disk. /workspace is a geesefs (S3) FUSE mount: it reads at
# ~150 MB/s idle but collapses to a few MB/s when the engine fills its expert cache from it while a download writes to
# it; the engine then sits for ever. Everything the engine or the front end opens lives under /opt/us2-models.
set -e
cd /opt/us2-models
rsync -a --info=progress2 /workspace/unbiased/pack-iq3-xxs ./
rsync -a --info=progress2 /workspace/unbiased/mtp-bf16/rt/ ./mtp/
rsync -a --info=progress2 /workspace/unbiased/models/IQ3_XXS ./
echo STAGE-DONE
