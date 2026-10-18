Probe for finding 3 (T1 failure): strata-poly Qwen3.6 UD-Q3_K_M, code/puzzle (thinking on), teacher-forced on the
reference answer, step 144: llama.cpp GPU argmax 5435 (p 0.53) over 1781 (0.25), gap 0.76 nats; llama.cpp CPU agrees
(gap 0.69); llama.cpp GPU with micro-batch 16 agrees (0.57 / 0.24). The engine (base arm) picks 1781 0.424 over 5435 0.379.
Variants of the engine on the same ids (files here, steps 0-145):
  rerun                        bitwise the base arm (deterministic)
  --no-graphs                  bitwise the base arm
  --prompt-batch 16            5435 0.54 / 1781 0.26 (agrees with llama.cpp)
  --no-gpu-experts             5435 0.48 / 1781 0.33 (agrees)
Step 0 (the prompt path alone): KL(llama GPU || x) ~1e-5 for every variant and for llama CPU: the prompt path is not it.
Mean bucketed KL over steps 0-145, KL(llama GPU || x): llama CPU 0.00219, llama GPU ub16 0.00249, engine base 0.00324,
engine pb16 0.00300, engine no-gpu-experts 0.00337 (1.4-1.5x the CPU floor). Reading: a decode-path rounding difference
that compounds through the recurrent GDN state over 144 steps and lands on a 0.7-nat margin; not located to a kernel
(needs per-layer vectors from strata-poly, plan 5.3 (b)). Recorded as finding 3; the gate (100 % at 0.5 nats) fails by
one position of 301.
