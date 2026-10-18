Probe for finding 2 (CORRECTNESS-PLAN.md 3.7 step 1), strata-poly, Qwen3.6 UD-Q3_K_M, sequence short/p02 teacher-forced on
the reference answer, --top-probs 20 per step, compared byte for byte with the base arm (--no-draft --lookup 0 --window 1):
  base + --no-graphs                      SAME    (CUDA graphs are bitwise inert on the single-token path)
  draft block on, --lookup 0 (window <= 4) SAME    (the draft block alone: 1 known token + up to 3 guesses)
  draft on, --window 2 / 3 / 4             SAME
  draft on, --window 5 / 6 / 7 / 8 (default) differ from step 20-21 on
  --no-draft --lookup 3 --window 8         differ  (the suffix lookup alone fills windows beyond 4)
  --no-draft --lookup 3 --window 4         SAME
Reading: a verify window of 5 or more tokens is not bitwise the single-token path; windows of 4 or fewer are. With the
defaults (draft block + lookup 3, window 8) the lookup is what makes windows longer than 4. Which kernel changes
behaviour between 4 and 5 rows is not located (plan 3.7 step 5).
