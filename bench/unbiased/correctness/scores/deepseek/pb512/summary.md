# Scores: deepseek / pb512 against reference deepseek

| Set | Seq | Steps | Top-1 agree | Floor top-1 | KL top20 (mean / p99) | Floor KL top20 | Ratio | Floor KL full (mean / p99) | T1 (positions >= 0.5 nat / failures) | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long | d16k | 256 | 0.992 | 0.988 | 0.03050 / 0.5075 | 0.03294 | 0.93 | 0.00418 / 0.0396 | pass (239 / 0) | pass |
| long | d31k | 256 | 0.980 | 0.984 | 0.00999 / 0.1278 | 0.01208 | 0.83 | 0.00438 / 0.0410 | pass (221 / 0) | pass |
| long | d4k | 256 | 1.000 | 0.992 | 0.02900 / 0.5162 | 0.03332 | 0.87 | 0.00433 / 0.0350 | pass (244 / 0) | pass |
| realtext | r16k | 510 | 0.967 | 0.959 | 0.07173 / 1.2578 | 0.06771 | 1.06 | 0.00662 / 0.0652 | FAIL (400 / 1) | pass |

## Per set (steps-weighted)

| Set | Steps | Top-1 agree | Floor top-1 | KL top20 | Floor KL top20 | Ratio | T1 failures | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long | 768 | 0.991 | 0.988 | 0.02316 | 0.02611 | 0.89 | 0 | pass |
| realtext | 510 | 0.967 | 0.959 | 0.07173 | 0.06771 | 1.06 | 1 | pass |

T1 failures (seq, step, llama argmax, engine argmax, gap): [('r16k', [445, 12919, 1956, 0.5114917755126953])]
