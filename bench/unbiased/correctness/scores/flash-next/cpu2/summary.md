# Scores: flash-next / cpu2 against reference flash-next

| Set | Seq | Steps | Top-1 agree | Floor top-1 | KL top20 (mean / p99) | Floor KL top20 | Ratio | Floor KL full (mean / p99) | T1 (positions >= 0.5 nat / failures) | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| code | lru | 400 | 1.000 | 0.998 | 0.00047 / 0.0040 | 0.00065 | 0.73 | 0.00056 / 0.0062 | pass (384 / 0) | pass |
| code | puzzle | 324 | 0.997 | 0.997 | 0.00067 / 0.0078 | 0.00100 | 0.68 | 0.00097 / 0.0101 | pass (303 / 0) | pass |
| long | d4k | 255 | 0.937 | 0.953 | 0.02935 / 0.2637 | 0.03473 | 0.85 | 0.01010 / 0.0769 | pass (199 / 0) | pass |
| short | p00 | 128 | 0.969 | 0.977 | 0.00534 / 0.0735 | 0.00853 | 0.63 | 0.00293 / 0.0261 | pass (103 / 0) | pass |
| short | p01 | 128 | 0.992 | 1.000 | 0.00048 / 0.0102 | 0.00046 | 1.04 | 0.00033 / 0.0045 | pass (122 / 0) | pass |

## Per set (steps-weighted)

| Set | Steps | Top-1 agree | Floor top-1 | KL top20 | Floor KL top20 | Ratio | T1 failures | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| code | 724 | 0.999 | 0.997 | 0.00056 | 0.00080 | 0.70 | 0 | pass |
| long | 255 | 0.937 | 0.953 | 0.02935 | 0.03473 | 0.85 | 0 | pass |
| short | 256 | 0.980 | 0.988 | 0.00291 | 0.00450 | 0.65 | 0 | pass |

T1 failures (seq, step, llama argmax, engine argmax, gap): none
