# Scores: flash-next / pint4 against reference flash-next

| Set | Seq | Steps | Top-1 agree | Floor top-1 | KL top20 (mean / p99) | Floor KL top20 | Ratio | Floor KL full (mean / p99) | T1 (positions >= 0.5 nat / failures) | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| code | lru | 400 | 0.998 | 0.998 | 0.00050 / 0.0041 | 0.00065 | 0.77 | 0.00056 / 0.0062 | pass (384 / 0) | pass |
| code | puzzle | 324 | 0.994 | 0.997 | 0.00078 / 0.0075 | 0.00100 | 0.79 | 0.00097 / 0.0101 | pass (303 / 0) | pass |
| long | d4k | 255 | 0.945 | 0.953 | 0.03109 / 0.2839 | 0.03473 | 0.90 | 0.01010 / 0.0769 | FAIL (199 / 1) | pass |
| short | p00 | 128 | 0.992 | 0.977 | 0.00567 / 0.0844 | 0.00853 | 0.66 | 0.00293 / 0.0261 | pass (103 / 0) | pass |
| short | p01 | 128 | 1.000 | 1.000 | 0.00040 / 0.0019 | 0.00046 | 0.85 | 0.00033 / 0.0045 | pass (122 / 0) | pass |

## Per set (steps-weighted)

| Set | Steps | Top-1 agree | Floor top-1 | KL top20 | Floor KL top20 | Ratio | T1 failures | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| code | 724 | 0.996 | 0.997 | 0.00063 | 0.00080 | 0.78 | 0 | pass |
| long | 255 | 0.945 | 0.953 | 0.03109 | 0.03473 | 0.90 | 1 | pass |
| short | 256 | 0.996 | 0.988 | 0.00303 | 0.00450 | 0.67 | 0 | pass |

T1 failures (seq, step, llama argmax, engine argmax, gap): [('d4k', [55, 1510, 11626, 0.5536060333251953])]
