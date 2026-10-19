#!/usr/bin/env python3
"""probe-master-tab.py <root> <ref-tag> <probe-tag> <vocab>: per sequence, KL(gpu||cpu) (the floor), KL(gpu||probe),
KL(cpu||probe), top-1 agreement of each pair, and how often the probe's argmax leaves the GPU argmax where the GPU's
top-2 gap is >= 0.5 nat (the T1 criterion applied to a second llama.cpp build instead of the engine)."""
import glob, os, sys
import numpy as np
root, ref, probe, V = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
def ls(r): m = r.max(); return r - (m + np.log(np.exp(r - m).sum()))
tot = dict(n=0, gc=0.0, gm=0.0, cm=0.0, agc=0, agm=0, acm=0, t1pos=0, t1flip=0)
print('seq steps | KL gpu||cpu (floor) | KL gpu||probe | KL cpu||probe | top1 gpu~cpu gpu~probe cpu~probe | gap>=0.5: n, probe flips')
for f in sorted(glob.glob(f'{root}/reference/{probe}/*.cpu.full')):
    s = os.path.basename(f).split('.')[0]
    try:
        g = np.fromfile(f'{root}/reference/{ref}/{s}.gpu.full', dtype=np.float32).reshape(-1, V).astype(np.float64)
        c = np.fromfile(f'{root}/reference/{ref}/{s}.cpu.full', dtype=np.float32).reshape(-1, V).astype(np.float64)
    except Exception: print(s, 'reference incomplete'); continue
    m = np.fromfile(f, dtype=np.float32).reshape(-1, V).astype(np.float64)
    n = min(len(g), len(c), len(m)); r = dict(n=n, gc=0.0, gm=0.0, cm=0.0, agc=0, agm=0, acm=0, t1pos=0, t1flip=0)
    for t in range(n):
        lg, lc, lm = ls(g[t]), ls(c[t]), ls(m[t]); pg = np.exp(lg)
        r['gc'] += float((pg * (lg - lc)).sum()); r['gm'] += float((pg * (lg - lm)).sum()); r['cm'] += float((np.exp(lc) * (lc - lm)).sum())
        r['agc'] += int(lg.argmax() == lc.argmax()); r['agm'] += int(lg.argmax() == lm.argmax()); r['acm'] += int(lc.argmax() == lm.argmax())
        i = np.argsort(-lg)[:2]
        if lg[i[0]] - lg[i[1]] >= 0.5: r['t1pos'] += 1; r['t1flip'] += int(lm.argmax() != i[0])
    print(f"{s} {n} | {r['gc']/n:.5f} | {r['gm']/n:.5f} | {r['cm']/n:.5f} | {r['agc']/n:.3f} {r['agm']/n:.3f} {r['acm']/n:.3f} | {r['t1pos']}, {r['t1flip']}")
    for k in tot: tot[k] += r[k]
n = tot['n']
if n: print(f"ALL {n} | {tot['gc']/n:.5f} | {tot['gm']/n:.5f} | {tot['cm']/n:.5f} | {tot['agc']/n:.3f} {tot['agm']/n:.3f} {tot['acm']/n:.3f} | {tot['t1pos']}, {tot['t1flip']}")
