# Scores: qwen36-q3km / pb512 against reference qwen36-q3km

| Set | Seq | Steps | Top-1 agree | Floor top-1 | KL top20 (mean / p99) | Floor KL top20 | Ratio | Floor KL full (mean / p99) | T1 (positions >= 0.5 nat / failures) | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long | d16k | 256 | 0.984 | 0.984 | 0.00342 / 0.0670 | 0.00332 | 1.03 | 0.00171 / 0.0236 | FAIL (235 / 1) | pass |
| long | d31k | 256 | 0.988 | 0.988 | 0.00069 / 0.0096 | 0.00057 | 1.21 | 0.00056 / 0.0101 | pass (235 / 0) | pass |
| long | d4k | 256 | 0.984 | 0.977 | 0.02831 / 0.2798 | 0.02748 | 1.03 | 0.00403 / 0.0332 | FAIL (203 / 1) | pass |
| realtext | r16k | 510 | 0.982 | 0.971 | 0.01216 / 0.1830 | 0.01356 | 0.90 | 0.00440 / 0.0353 | pass (422 / 0) | pass |

## Per set (steps-weighted)

| Set | Steps | Top-1 agree | Floor top-1 | KL top20 | Floor KL top20 | Ratio | T1 failures | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long | 768 | 0.986 | 0.983 | 0.01081 | 0.01046 | 1.03 | 2 | pass |
| realtext | 510 | 0.982 | 0.971 | 0.01216 | 0.01356 | 0.90 | 0 | pass |

T1 failures (seq, step, llama argmax, engine argmax, gap): [('d16k', [12, 15, 16, 0.7747058868408203]), ('d4k', [96, 4361, 4560, 0.6801185607910156])]
