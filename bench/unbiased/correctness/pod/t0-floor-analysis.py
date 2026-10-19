import glob, os, sys, re
import numpy as np
C = '/opt/us2-correctness'
for fam, V in (('deepseek', 129280), ('glm', 154880)):
    root = f'{C}/{fam}'
    # floor T1: llama CPU argmax vs GPU argmax where the GPU top-2 gap >= 0.5
    pos = gap = flips = 0; fl = []
    for g in sorted(glob.glob(f'{root}/reference/{fam}/*.gpu.full')):
        s = os.path.basename(g).split('.')[0]; c = g.replace('.gpu.full', '.cpu.full')
        if not os.path.exists(c): continue
        G = np.fromfile(g, dtype=np.float32).reshape(-1, V); Cc = np.fromfile(c, dtype=np.float32).reshape(-1, V)
        n = min(len(G), len(Cc)); pos += n
        for t in range(n):
            r = G[t].astype(np.float64); i = np.argpartition(-r, 2)[:2]; i = i[np.argsort(-r[i])]
            if r[i[0]] - r[i[1]] >= 0.5:
                gap += 1
                if Cc[t].argmax() != i[0]: flips += 1; fl.append((s, t, round(float(r[i[0]] - r[i[1]]), 3)))
    print(f'{fam} floor: {pos} positions, {gap} gap>=0.5, llama CPU differs from GPU at {flips}: {fl[:12]}')
    # T0: base vs draft arm, per sequence
    def top(path):
        out = []
        for l in open(path):
            if not l.startswith('top '): continue
            toks = re.findall(r'(\d+):([-\d.eE]+)', l); out.append({int(a): float(b) for a, b in toks})
        return out
    print(f'{fam} base vs draft: seq steps same-argmax steps-identical max|dlogp on shared ids|')
    for b in sorted(glob.glob(f'{root}/poly/{fam}/base/*.top.txt')):
        s = os.path.basename(b)[:-8]; d = b.replace('/base/', '/draft/')
        if not os.path.exists(d): continue
        B, D = top(b), top(d); n = min(len(B), len(D)); same = ident = 0; mx = 0.0
        for t in range(n):
            bb, dd = B[t], D[t]
            if not bb or not dd: continue
            if max(bb, key=bb.get) == max(dd, key=dd.get): same += 1
            if bb == dd: ident += 1
            sh = set(bb) & set(dd)
            if sh: mx = max(mx, max(abs(bb[k] - dd[k]) for k in sh))
        print(f'  {s} {n} {same} {ident} {mx:.4f}')
