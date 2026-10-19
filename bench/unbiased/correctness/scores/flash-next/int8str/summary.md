# Scores: flash-next / int8str against reference flash-next

| Set | Seq | Steps | Top-1 agree | Floor top-1 | KL top20 (mean / p99) | Floor KL top20 | Ratio | Floor KL full (mean / p99) | T1 (positions >= 0.5 nat / failures) | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long | d31k | 255 | 0.973 | 0.965 | 0.00259 / 0.0275 | 0.00245 | 1.06 | 0.00243 / 0.0522 | pass (214 / 0) | pass |

## Per set (steps-weighted)

| Set | Steps | Top-1 agree | Floor top-1 | KL top20 | Floor KL top20 | Ratio | T1 failures | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long | 255 | 0.973 | 0.965 | 0.00259 | 0.00245 | 1.06 | 0 | pass |

T1 failures (seq, step, llama argmax, engine argmax, gap): none
