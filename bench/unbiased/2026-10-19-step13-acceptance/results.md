| Run | Model | Task | T | Pass | Wall s | Turns | Tool calls | In tok | Out tok | Errors | Judge | Harness notes |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `20261019T0213Z-qwen3.6-35b-a3b-ud-iq4_xs-md-toc-smoke` | qwen3.6-35b-a3b-ud-iq4_xs | md-toc | 0.6 | **pass** | 31 | 5 | 4 | 2563 | 5917 | 1 | {"hidden": "4 passed in 0.09s", "own_tests": "1 failed, 29 passed in 0.48s"} |  |
| `20261019T0215Z-deepseek-v4-flash-ud-iq2_xxs-b200-md-toc` | deepseek-v4-flash-ud-iq2_xxs-b200 | md-toc | 0.6 | **pass** | 252 | 9 | 7 | 2905 | 13021 | 2 | {"hidden": "4 passed in 0.09s", "own_tests": "17 passed in 0.01s"} |  |
| `20261019T0215Z-qwen3.6-35b-a3b-ud-iq4_xs-md-toc` | qwen3.6-35b-a3b-ud-iq4_xs | md-toc | 0.6 | **pass** | 38 | 10 | 9 | 1007 | 7011 | 0 | {"hidden": "4 passed in 0.09s", "own_tests": "25 passed in 0.38s"} |  |
| `20261019T0216Z-qwen3.6-35b-a3b-ud-iq4_xs-kvstore` | qwen3.6-35b-a3b-ud-iq4_xs | kvstore | 0.6 | **pass** | 64 | 14 | 13 | 4024 | 10433 | 0 | {"failures": []} |  |
| `20261019T0217Z-glm-5.3-flash-3.0bit-b200-md-toc` | glm-5.3-flash-3.0bit-b200 | md-toc | 0.6 | fail | 119 | 1 | 0 | 1673 | 8192 | 0 | {"why": "no mdtoc.py"} |  |
| `20261019T0217Z-qwen3.6-35b-a3b-ud-iq4_xs-bugfix` | qwen3.6-35b-a3b-ud-iq4_xs | bugfix | 0.6 | **pass** | 11 | 6 | 11 | 2939 | 1829 | 0 | {"tests_untouched": true, "pytest": "6 passed in 0.01s"} |  |
| `20261019T0217Z-qwen3.6-35b-a3b-ud-iq4_xs-minesweeper` | qwen3.6-35b-a3b-ud-iq4_xs | minesweeper | 0.6 | **pass** | 1499 | 14 | 13 | 5187 | 8620 | 0 | {"cells": 81, "revealed_after_click": 1, "console_errors": 0} | killed hung node test in qwen minesweeper run (10m41s); 2026-10-19T02:31:39Z killed the same hung node test again (second run, 1m20s); a third loop ends the run |
| `20261019T0219Z-deepseek-v4-flash-ud-iq2_xxs-b200-kvstore` | deepseek-v4-flash-ud-iq2_xxs-b200 | kvstore | 0.6 | **pass** | 53 | 2 | 1 | 1784 | 1473 | 1 | {"failures": []} |  |
| `20261019T0219Z-glm-5.3-flash-3.0bit-b200-kvstore` | glm-5.3-flash-3.0bit-b200 | kvstore | 0.6 | fail | 119 | 1 | 0 | 1634 | 8192 | 0 | {"why": "no kvstore.py"} |  |
| `20261019T0220Z-deepseek-v4-flash-ud-iq2_xxs-b200-bugfix` | deepseek-v4-flash-ud-iq2_xxs-b200 | bugfix | 0.6 | **pass** | 62 | 8 | 12 | 2751 | 3517 | 1 | {"tests_untouched": true, "pytest": "6 passed in 0.02s"} |  |
| `20261019T0221Z-deepseek-v4-flash-ud-iq2_xxs-b200-minesweeper` | deepseek-v4-flash-ud-iq2_xxs-b200 | minesweeper | 0.6 | fail | 47 | 2 | 1 | 1750 | 2043 | 1 | {"why": "no index.html"} |  |
| `20261019T0221Z-glm-5.3-flash-3.0bit-b200-bugfix` | glm-5.3-flash-3.0bit-b200 | bugfix | 0.6 | fail | 54 | 8 | 12 | 5002 | 2930 | 1 | {"tests_untouched": true, "pytest": "2 failed, 4 passed in 0.02s"} |  |
| `20261019T0222Z-deepseek-v4-flash-ud-iq2_xxs-b200-minesweeper-t1` | deepseek-v4-flash-ud-iq2_xxs-b200 | minesweeper | 1.0 | **pass** | 161 | 12 | 9 | 1390 | 7187 | 3 | {"cells": 81, "revealed_after_click": 1, "console_errors": 0} |  |
| `20261019T0225Z-glm-5.3-flash-3.0bit-b200-kvstore-low` | glm-5.3-flash-3.0bit-b200 | kvstore | 0.6 | **pass** | 55 | 4 | 4 | 1667 | 2739 | 1 | {"failures": []} |  |
| `20261019T0225Z-glm-5.3-flash-3.0bit-b200-md-toc-low` | glm-5.3-flash-3.0bit-b200 | md-toc | 0.6 | fail | 29 | 1 | 0 | 0 | 0 | 1 | {"why": "no mdtoc.py"} |  |
| `20261019T0226Z-glm-5.3-flash-3.0bit-b200-bugfix-low` | glm-5.3-flash-3.0bit-b200 | bugfix | 0.6 | **pass** | 18 | 5 | 6 | 3097 | 928 | 0 | {"tests_untouched": true, "pytest": "6 passed in 0.01s"} |  |
| `20261019T0226Z-glm-5.3-flash-3.0bit-b200-minesweeper-low` | glm-5.3-flash-3.0bit-b200 | minesweeper | 0.6 | fail | 30 | 1 | 0 | 0 | 0 | 1 | {"why": "no index.html"} |  |
| `20261019T0227Z-glm-5.3-flash-3.0bit-b200-minesweeper-low-t1` | glm-5.3-flash-3.0bit-b200 | minesweeper | 1.0 | fail | 43 | 2 | 2 | 1 | 2598 | 1 | {"why": "no index.html"} |  |
| `20261019T0230Z-deepseek-v4-flash-ud-iq2_xxs-b200-minesweeper-v` | deepseek-v4-flash-ud-iq2_xxs-b200 | minesweeper | 0.6 | fail | 67 | 2 | 1 | 1750 | 3211 | 1 | {"why": "no index.html"} |  |
| `20261019T0230Z-glm-5.3-flash-3.0bit-b200-md-toc-low-v` | glm-5.3-flash-3.0bit-b200 | md-toc | 0.6 | fail | 29 | 1 | 0 | 0 | 0 | 1 | {"why": "no mdtoc.py"} |  |
| `20261019T0232Z-qwen3.8-flash-next-iq3_xxs-3090-md-toc` | qwen3.8-flash-next-iq3_xxs-3090 | md-toc | 0.6 | **pass** | 119 | 16 | 13 | 3868 | 9358 | 3 | {"hidden": "4 passed in 0.10s", "own_tests": "17 passed in 0.08s"} |  |
| `20261019T0234Z-qwen3.8-flash-next-iq3_xxs-3090-kvstore` | qwen3.8-flash-next-iq3_xxs-3090 | kvstore | 0.6 | **pass** | 91 | 8 | 8 | 2094 | 7102 | 0 | {"failures": []} |  |
| `20261019T0236Z-qwen3.8-flash-next-iq3_xxs-3090-bugfix` | qwen3.8-flash-next-iq3_xxs-3090 | bugfix | 0.6 | **pass** | 34 | 6 | 11 | 2922 | 2350 | 0 | {"tests_untouched": true, "pytest": "6 passed in 0.01s"} |  |
| `20261019T0237Z-qwen3.8-flash-next-iq3_xxs-3090-minesweeper` | qwen3.8-flash-next-iq3_xxs-3090 | minesweeper | 0.6 | **pass** | 185 | 30 | 31 | 4838 | 14332 | 2 | {"cells": 81, "revealed_after_click": 56, "console_errors": 0} |  |
| `20261019T0241Z-deepseek-v4-flash-ud-iq2_xxs-b200-minesweeper-p` | deepseek-v4-flash-ud-iq2_xxs-b200 | minesweeper | 0.6 | fail | 67 | 2 | 1 | 1750 | 3211 | 1 | {"why": "no index.html"} |  |
| `20261019T0241Z-glm-5.3-flash-3.0bit-b200-md-toc-low-p` | glm-5.3-flash-3.0bit-b200 | md-toc | 0.6 | **pass** | 108 | 12 | 13 | 7009 | 7425 | 0 | {"hidden": "4 passed in 0.09s", "own_tests": "13 passed in 0.21s"} |  |
| `20261019T0242Z-qwen3.6-35b-a3b-ud-iq4_xs-minesweeper-t1` | qwen3.6-35b-a3b-ud-iq4_xs | minesweeper | 1.0 | fail | 83 | 31 | 30 | 3251 | 14439 | 0 | {"cells": 0, "revealed_after_click": 0, "console_errors": 0} |  |
| `20261019T0244Z-glm-5.3-flash-3.0bit-b200-minesweeper-low-p` | glm-5.3-flash-3.0bit-b200 | minesweeper | 0.6 | **pass** | 121 | 11 | 12 | 4341 | 8384 | 0 | {"cells": 81, "revealed_after_click": 55, "console_errors": 0} |  |
| `20261019T0245Z-deepseek-v4-flash-ud-iq2_xxs-b200-minesweeper-p2` | deepseek-v4-flash-ud-iq2_xxs-b200 | minesweeper | 0.6 | **pass** | 749 | 27 | 26 | 31462 | 24736 | 0 | {"cells": 81, "revealed_after_click": 60, "console_errors": 0} | 2026-10-19T02:56:30Z watchdog killed pid 183 (node) after 312s |
| `20261019T0246Z-glm-5.3-flash-3.0bit-b200-minesweeper-low-p-t1` | glm-5.3-flash-3.0bit-b200 | minesweeper | 1.0 | **pass** | 182 | 17 | 19 | 4171 | 12663 | 0 | {"cells": 81, "revealed_after_click": 38, "console_errors": 0} |  |
| `20261019T0247Z-qwen3.6-35b-a3b-ud-q3_k_m-3090-md-toc` | qwen3.6-35b-a3b-ud-q3_k_m-3090 | md-toc | 0.6 | **pass** | 48 | 13 | 11 | 2581 | 7323 | 1 | {"hidden": "4 passed in 0.08s", "own_tests": "39 passed in 0.58s"} |  |
| `20261019T0248Z-qwen3.6-35b-a3b-ud-q3_k_m-3090-kvstore` | qwen3.6-35b-a3b-ud-q3_k_m-3090 | kvstore | 0.6 | **pass** | 47 | 10 | 9 | 11471 | 6142 | 0 | {"failures": []} |  |
| `20261019T0249Z-qwen3.6-35b-a3b-ud-q3_k_m-3090-bugfix` | qwen3.6-35b-a3b-ud-q3_k_m-3090 | bugfix | 0.6 | **pass** | 18 | 7 | 12 | 2959 | 2284 | 0 | {"tests_untouched": true, "pytest": "6 passed in 0.01s"} |  |
| `20261019T0250Z-qwen3.6-35b-a3b-ud-q3_k_m-3090-minesweeper` | qwen3.6-35b-a3b-ud-q3_k_m-3090 | minesweeper | 0.6 | **pass** | 47 | 9 | 8 | 5663 | 8512 | 0 | {"cells": 81, "revealed_after_click": 1, "console_errors": 0} |  |
| `20261019T0251Z-qwen3.6-35b-a3b-ud-q3_k_m-3090-minesweeper-t1` | qwen3.6-35b-a3b-ud-q3_k_m-3090 | minesweeper | 1.0 | **pass** | 378 | 11 | 10 | 3486 | 8454 | 0 | {"cells": 81, "revealed_after_click": 49, "console_errors": 0} | 2026-10-19T02:57:04Z watchdog killed pid 43 (node) after 330s |
| `20261019T0259Z-deepseek-v4-flash-ud-iq2_xxs-b200-minesweeper-p2-t1` | deepseek-v4-flash-ud-iq2_xxs-b200 | minesweeper | 1.0 | **pass** | 139 | 12 | 11 | 2156 | 7332 | 0 | {"cells": 81, "revealed_after_click": 1, "console_errors": 0} |  |
| `20261019T0259Z-qwen3.8-flash-next-iq3_xxs-3090-minesweeper-t1` | qwen3.8-flash-next-iq3_xxs-3090 | minesweeper | 1.0 | **pass** | 148 | 23 | 23 | 4074 | 14493 | 1 | {"cells": 81, "revealed_after_click": 31, "console_errors": 0} |  |

| Model | Runs | Passed | Tasks passed |
| --- | ---: | ---: | --- |
| qwen3.6-35b-a3b-ud-iq4_xs | 6 | 5 | bugfix, kvstore, md-toc, minesweeper |
| deepseek-v4-flash-ud-iq2_xxs-b200 | 9 | 6 | bugfix, kvstore, md-toc, minesweeper, minesweeper@1.0 |
| glm-5.3-flash-3.0bit-b200 | 12 | 5 | bugfix, kvstore, md-toc, minesweeper, minesweeper@1.0 |
| qwen3.8-flash-next-iq3_xxs-3090 | 5 | 5 | bugfix, kvstore, md-toc, minesweeper, minesweeper@1.0 |
| qwen3.6-35b-a3b-ud-q3_k_m-3090 | 5 | 5 | bugfix, kvstore, md-toc, minesweeper, minesweeper@1.0 |
