Expert placement and the bits (configuration A, A6000 VM, 2026-10-18)

Finding. Two strata processes with the same flags gave different per-position log-probabilities (fp16 vs t4: every
row of the short set from position 1, lru from position 380, puzzle none). The cause is the expert cache's auto
sizing: --expert-cache auto (also under --resident-experts) sizes the GPU cache from the VRAM free at start, which
varied with what else sat on the card (40.52 to 41.56 GiB free: the CPU reference's CUDA context beside the fp16
arm, nothing beside the int8 arm), giving 18276 to 18758 slots in max-blob units = 24380 to 24576 of the 24576
experts (48 layers x 512) on the card. The experts left over sit in page-locked RAM and each miss is split by
--pcie-frac (0.55 here: 55 % fetched over PCIe and computed on the GPU, 45 % computed by the CPU pool with the AVX-2
kernels). The CPU and the GPU round an expert differently (upstream says so, docs/DETAILS.md, #410), so the bits
depend on which experts missed, which depends on the slot count, which depends on the free VRAM at start.

Per arm (expert cache line of the engine log):
  fp16    24380 (short set, long set, r16k) / 24541 (lru, puzzle, p09)   -> 196 / 35 experts in RAM
  t4      24543                                                           -> 33 in RAM
  int8    24576, int8str 24576, pin* 24576                                -> every expert on the card
  pf512   24541 (prompt chunks of 512 borrow fewer cache slots)
Bitwise comparisons (pos.tsv rows: target log-probability, argmax, 20 log-probabilities):
  pin vs pin2 (same flags, second process)       0 differing rows of 5507 (p00 p01 lru puzzle d4k)
  pin vs pint4 (--suffix-draft 0: windows 4/3/1 instead of 6/5/1)   0 of 5507  -> the window size changes no bits
  pin vs pingpu (--pcie-frac 1), pin vs pincpu (--pcie-frac 0)      0 of 5507  -> with every expert on the card no
                                                                      decode miss happens; the share has nothing to act on
  int8str vs int8 on d31k (streamed KV, --kv-resident 20480)        0 of 255   -> streaming changes no bits
  fp16 vs t4   differ on 15 of 16 sequences (puzzle: 24541 vs 24543, 0 rows)   -> placement, not the window size
  pin vs fp16  differ on every sequence (24576 vs 24380/24541)
Consequences. (1) On a card that holds every expert, strata is deterministic across starts and across the window
size, the KV streaming and the PCIe share. (2) On a card that does not (the 24 GB target), the answer depends on the
free VRAM at start through the CPU-computed share of the misses; --pcie-frac 0 or 1 removes the split but not the
dependence on the slot count; a fixed --expert-cache N does. (3) The fp16, t4 and pf512 arms here carry a small
CPU-computed share (0.1-0.8 % of the experts in RAM, 45 % of their misses on the CPU) and are scored as such against
llama.cpp; the cpu/cpu2/pcie arms (--expert-cache 16000, about 13 % of the experts in RAM) are the deterministic
CPU-tier and PCIe-tier arms, see the README.

The cpu / cpu2 / pcie arms (--expert-cache 16000 in max-blob units -> 21311 of the 24576 experts on the card, 8.62 GiB
of experts in RAM, 13 % of the set; the last decode window of the short set routed 18 to 111 of its 480 expert reads
to misses):
  cpu vs cpu2 (--pcie-frac 0, every miss on the CPU; second process)   0 differing rows of 5507 -> the CPU tier is
                                                                        deterministic once the placement is fixed
  cpu vs pin   (CPU-computed misses against every expert on the card)   every row differs (5507 of 5507), from position 0
  pcie vs pin  (--pcie-frac 1, every miss fetched over PCIe to the GPU) 0 of 5489 rows on p00, lru, puzzle, d4k; p01: 18
                                                                        of 161 rows from position 143 differ in the 7th
                                                                        significant digit (-0.000022956 vs -0.000022872)
So a fetched expert is computed as a cached one on 4 of 5 sequences and not quite on the fifth: the PCIe path is not
bitwise the cache-hit path everywhere (the kernel that differs is not located). The cpu arm is scored against llama.cpp
as the CPU tier (README section 4).
