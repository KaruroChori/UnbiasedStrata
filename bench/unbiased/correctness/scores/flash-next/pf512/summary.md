# Scores: flash-next / pf512 against reference flash-next

| Set | Seq | Steps | Top-1 agree | Floor top-1 | KL top20 (mean / p99) | Floor KL top20 | Ratio | Floor KL full (mean / p99) | T1 (positions >= 0.5 nat / failures) | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long | d16k | 255 | 0.953 | 0.929 | 0.01332 / 0.1582 | 0.01646 | 0.81 | 0.01087 / 0.1588 | pass (187 / 0) | pass |
| long | d31k | 255 | 0.980 | 0.965 | 0.00114 / 0.0189 | 0.00245 | 0.46 | 0.00243 / 0.0522 | pass (214 / 0) | pass |
| long | d4k | 255 | 0.941 | 0.953 | 0.02991 / 0.2337 | 0.03473 | 0.86 | 0.01010 / 0.0769 | pass (199 / 0) | pass |
| realtext | r16k | 509 | 0.931 | 0.943 | 0.01475 / 0.1633 | 0.01674 | 0.88 | 0.00927 / 0.0658 | pass (406 / 0) | pass |

## Per set (steps-weighted)

| Set | Steps | Top-1 agree | Floor top-1 | KL top20 | Floor KL top20 | Ratio | T1 failures | T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long | 765 | 0.958 | 0.949 | 0.01479 | 0.01788 | 0.83 | 0 | pass |
| realtext | 509 | 0.931 | 0.943 | 0.01475 | 0.01674 | 0.88 | 0 | pass |

T1 failures (seq, step, llama argmax, engine argmax, gap): none
