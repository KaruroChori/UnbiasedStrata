#!/usr/bin/env python3
"""Configuration A arms (CORRECTNESS-PLAN.md 3.4) on the A6000 VM: a fresh `strata --serve` per sequence, the whole
sequence (prompt + reference answer) sent as one GEN 1 request, STRATA_LOGPOS scoring every position read through the
verify windows (--short-read covers the sequence). strata-run.py <arm> [seq ...]
arms: fp16    = --kv fp16, suffix drafter on (arm 1)
      t4      = fp16 + --suffix-draft 0 (arm 2; pos.tsv log-probabilities must equal arm 1's)
      int8    = --kv int8 (arm 3)
      int8str = --kv int8 --kv-resident 20480 --short-read 1024, the 31K sequence (arm 4; equals arm 3 on those rows)
      pf512   = fp16 + --prefill 512 --short-read 512 on the long set (arm 5, chunk effect)
On this VM every expert is resident on the card (--resident-experts, 48 GB): no CPU or PCIe expert tier, so
STRATA_ROUTE_TAIL_SKIP / STRATA_PREFILL_CPU_SHARE / STRATA_IQ_MT_MIN / --adapt-every / --pcie-frac are set as the
plan says but have nothing to act on. Writes strata/<arm>/<seq>.pos.tsv, .scored.tsv (rows aligned to the answer),
.engine.log, .done.txt, command.sh."""
import os, pathlib, subprocess, sys, time
sys.path.insert(0, str(pathlib.Path.home() / 'us2-build/tools/qwen35'))
from q36_harness import Eng
ROOT = pathlib.Path.home() / 'us2-results/correctness'
EXE = str(pathlib.Path.home() / 'us2-build/build/bin/strata')
M = '/mnt/ds4/unbiased-strata'
BASE = ['--pack', f'{M}/pack-iq3-xxs', '--native', f'{M}/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf',
        '--ple-gguf', f'{M}/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf',
        '--expert-profile', f'{M}/pack-iq3-xxs/expert-profile.bin', '--resident-experts', '--prefill', 'auto',
        '--spec', '4', '--spec-min-p', '0.5', '--mtp', f'{M}/mtp', '--max-context', '65536', '--ple-io', 'mmap',
        '--prompt-cache', '0', '--adapt-every', '0', '--pcie-frac', '0.55']
ARMS = {'fp16':    (['--kv', 'fp16', '--short-read', '4096'], None),
        't4':      (['--kv', 'fp16', '--short-read', '4096', '--suffix-draft', '0'], None),
        'int8':    (['--kv', 'int8', '--short-read', '4096'], None),
        'int8str': (['--kv', 'int8', '--kv-resident', '20480', '--short-read', '1024'], {'d31k'}),
        'pf512':   (['--kv', 'fp16', '--prefill', '512', '--short-read', '512'], {'d4k', 'd16k', 'd31k', 'r16k'})}
arm = sys.argv[1]; only = set(sys.argv[2:])
REF_TAG = 'flash-next'

def answer_path(p, seq, tag):
    """The scored answer: the fixed one (<seq>.answer.ids, the real-text set) when it exists, else the reference
    model's own greedy answer <seq>.answer.<tag>.ids (a different file is a different model, so a different answer)."""
    fixed = p.parent / f'{seq}.answer.ids'
    return fixed if fixed.exists() else p.parent / f'{seq}.answer.{tag}.ids'
flags, default_seqs = ARMS[arm]
OUT = ROOT / 'strata' / arm; OUT.mkdir(parents=True, exist_ok=True)
for p in sorted(ROOT.glob('inputs/*/*.prompt.ids')):
    seq = p.name[:-len('.prompt.ids')]
    if only and seq not in only: continue
    if not only and default_seqs and seq not in default_seqs: continue
    ans_path = answer_path(p, seq, REF_TAG)
    if not ans_path.exists(): print(f'{seq}: no answer ids', flush=True); continue
    prompt = list(map(int, p.read_text().strip().split(','))); ans = list(map(int, ans_path.read_text().strip().split(',')))
    pos = OUT / f'{seq}.pos.tsv'
    env = {'STRATA_LOGPOS': str(pos), 'STRATA_LOGPOS_TOPK': '20', 'STRATA_ROUTE_TAIL_SKIP': '0', 'STRATA_PREFILL_CPU_SHARE': '0',
           'STRATA_IQ_MT_MIN': '1', 'CUDA_MODULE_LOADING': 'EAGER'}
    args = BASE + flags
    with open(OUT / 'command.sh', 'a') as f:
        f.write(' '.join(f'{k}={v}' for k, v in env.items()) + f' {EXE} --serve ' + ' '.join(args) + f'  # GEN 1 $(cat {p}),$(cat {ans_path})\n')
    t0 = time.time()
    try:
        e = Eng(EXE, args, env=env, log=str(OUT / f'{seq}.engine.log'))
        toks, done, ttft, wall = e.solo(prompt + ans, 1)
        e.send('QUIT'); e.p.wait(timeout=120)
    except SystemExit as ex:
        print(f'{p.parent.name}/{seq} {arm}: FAILED {ex}', flush=True); continue
    (OUT / f'{seq}.done.txt').write_text(done + '\n')
    # align: the rows whose target ids are the answer, in order
    rows = [l.rstrip('\n').split('\t') for l in open(pos)] if pos.exists() else []
    tg = [int(r[1]) for r in rows]
    start = next((i for i in range(len(tg) - len(ans) + 1) if tg[i:i + len(ans)] == ans), None)
    if start is None:
        print(f'{p.parent.name}/{seq} {arm}: {len(rows)} LOGPOS rows, answer not found in the targets; load {e.load_s:.0f} s', flush=True); continue
    (OUT / f'{seq}.scored.tsv').write_text('\n'.join('\t'.join(r) for r in rows[start:start + len(ans)]) + '\n')
    print(f'{p.parent.name}/{seq} {arm}: {len(rows)} rows, answer at row {start} (pos {rows[start][0]}), load {e.load_s:.0f} s, request {wall:.0f} s, {done}', flush=True)
