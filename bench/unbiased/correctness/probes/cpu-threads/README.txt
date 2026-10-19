Does the CPU reference depend on the thread count? Qwen3.6 UD-Q3_K_M, short/p00, --ngl 0, 128 steps teacher-forced:
STRATA_DUMP_THREADS=4 (llama.cpp's own default) against the 12-thread run in reference/qwen36-q3km/.
Both .full files have sha256 16379e3d62be97d405ab21d71094765f4898f4f6792a9f159efc4d9feca0b1fc: byte-identical. ggml-cpu computes
each output element whole on one thread, so the count moves time only. The .full of this probe is deleted (127 MB).
