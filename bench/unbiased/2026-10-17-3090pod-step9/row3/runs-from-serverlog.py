#!/usr/bin/env python3
"""Per-run request totals from a server log of PLAN section 11 row 3 (pi task, 3 runs against one server).
A run starts at the first request with no reused prefix and the task's initial prompt length; works for both
the fork's 'on_done' lines and upstream serve/server.py's per-request lines (pass the regex set with --upstream)."""
import re, sys, json
path = sys.argv[1]; up = '--upstream' in sys.argv
if up:
    pat = re.compile(r'prompt[=: ]+(?P<prompt>\d+).*?(?:reused|cached)[=: ]+(?P<reused>\d+).*?(?:produced|generated|decode_n|tokens)[=: ]+(?P<produced>\d+).*?prompt_ms[=: ]+(?P<prompt_ms>[\d.]+).*?decode_ms[=: ]+(?P<decode_ms>[\d.]+)')
else:
    pat = re.compile(r'on_done: task \d+: DONE produced=(?P<produced>\d+) prompt=(?P<prompt>\d+) prompt_ms=(?P<prompt_ms>[\d.]+) decode_ms=(?P<decode_ms>[\d.]+) finish=\w+ drafts=(?P<acc>\d+)/(?P<off>\d+) reused=(?P<reused>\d+)')
runs = []
for line in open(path, errors='replace'):
    m = pat.search(line)
    if not m: continue
    d = {k: float(v) for k, v in m.groupdict().items()}
    if d['reused'] == 0: runs.append([])
    if not runs: runs.append([])
    runs[-1].append(d)
out = []
for i, r in enumerate(runs, 1):
    read = sum(x['prompt'] - x['reused'] for x in r); prod = sum(x['produced'] for x in r)
    dms = sum(x['decode_ms'] for x in r); pms = sum(x['prompt_ms'] for x in r)
    row = {'run': i, 'requests': len(r), 'prompt_tokens_read': int(read), 'generated_tokens': int(prod), 'prompt_s': round(pms/1000, 1), 'decode_s': round(dms/1000, 1),
           'decode_tps': round(prod / (dms/1000), 1) if dms else None, 'final_context_tokens': int(r[-1]['prompt'] + r[-1]['produced'])}
    if 'acc' in r[0]: row['draft_acceptance_pct'] = round(100 * sum(x['acc'] for x in r) / max(1, sum(x['off'] for x in r)), 1)
    out.append(row)
print(json.dumps(out, indent=1))
