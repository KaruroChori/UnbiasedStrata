# Scores: glm / pb512 against reference glm

| Set | Seq | Steps | Top-1 agree | Floor top-1 | KL top20 (mean / p99) | Floor KL top20 | Ratio | Floor KL full (mean / p99) | T1 (positions >= 0.5 nat / failures) | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long | d16k | 256 | 1.000 | 0.992 | 0.00690 / 0.1036 | 0.01030 | 0.67 | 0.00220 / 0.0157 | pass (230 / 0) | pass |
| long | d31k | 256 | 0.969 | 0.961 | 0.00556 / 0.1501 | 0.00563 | 0.99 | 0.00318 / 0.0627 | pass (214 / 0) | pass |
| long | d4k | 256 | 0.973 | 0.988 | 0.03090 / 0.3804 | 0.03268 | 0.95 | 0.01053 / 0.1295 | FAIL (233 / 2) | pass |
| realtext | r16k | 510 | 0.963 | 0.976 | 0.03020 / 0.3426 | 0.02963 | 1.02 | 0.00446 / 0.0355 | pass (387 / 0) | pass |

## Per set (steps-weighted)

| Set | Steps | Top-1 agree | Floor top-1 | KL top20 | Floor KL top20 | Ratio | T1 failures | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long | 768 | 0.980 | 0.980 | 0.01445 | 0.01621 | 0.89 | 2 | pass |
| realtext | 510 | 0.963 | 0.976 | 0.03020 | 0.02963 | 1.02 | 0 | pass |

T1 failures (seq, step, llama argmax, engine argmax, gap): [('d4k', [95, 24, 23, 0.5531711578369141]), ('d4k', [252, 11, 303, 0.6713466644287109])]
