#!/usr/bin/env python3
"""UnbiasedStrata 2, step 9 (PLAN.md section 11): upstream PolyStrata v0.1.45-poly.1 and the fork, back to back on the
same card, same model files, same context, greedy, the same client (upstream's tools/strata_bench.py, --runs 3 --long,
plus the three-document sustained supplement of the 2026-10-17 upstream run). One directory per arm under OUT.
Runs on the pod with upstream's venv: /opt/polystrata-v0.1.45-poly.1/.venv/bin/python us2-step9-run.py OUT [arm ...]"""
import sys, pathlib, subprocess, json, time, hashlib, statistics, os, shutil
ROOT = pathlib.Path('/opt/polystrata-v0.1.45-poly.1')
sys.path.insert(0, str(ROOT / 'tools'))
import strata_bench as bench  # noqa: E402
PY = str(ROOT / '.venv/bin/python')
FORK = pathlib.Path('/opt/us2-build')
M = pathlib.Path('/opt/us2-models')
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
FN1 = M / 'IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf'
FN2 = M / 'IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf'
PACK = M / 'pack-iq3-xxs'; MTP = M / 'mtp'
Q36 = M / 'qwen36-mtp/Qwen3.6-35B-A3B-UD-Q3_K_M.gguf'
FN_ENGINE_ARGS = ['--pack', str(PACK), '--native', str(FN1), '--ple-gguf', str(FN2), '--expert-profile', str(PACK / 'expert-profile.bin'),
                  '--expert-cache', 'auto', '--prefill', 'auto', '--spec', '4', '--spec-min-p', '0.5', '--mtp', str(MTP),
                  '--max-context', '65536', '--kv', 'int8', '--ple-io', 'ram', '--pool-workers', '15', '--kv-resident', '32768']
def q36_args(profile): return ['--model', str(Q36), '--max-context', '32768', '--expert-profile', profile, '--tail-skip', '6']
UP_POLY = ROOT / 'build/strata-poly'
if not UP_POLY.exists():
    UP_POLY = FORK / 'build/bin/strata-poly'  # recorded in the arm's provenance if it happens

def sha(p): h = hashlib.sha256(); f = open(p, 'rb'); [h.update(b) for b in iter(lambda: f.read(1 << 22), b'')]; return h.hexdigest()

ARMS = {
  'upstream-flash-next': dict(port=18080, model='qwen3.8-flash-next-iq3_xxs', engine=str(ROOT / 'build/strata'),
      cfg=lambda d: {'exe': str(ROOT / 'build/strata'), 'cwd': str(ROOT), 'tokenizer': str(PACK / 'tokenizer'), 'model_name': 'qwen3.8-flash-next-iq3_xxs',
                     'log': str(d / 'engine.log'), 'args': FN_ENGINE_ARGS, 'sampling': {'temperature': 0.6, 'top_p': 0.95, 'top_k': 20, 'min_p': 0.0}, 'fit_max_tokens': True},
      cmd=lambda d, cfg: [PY, str(ROOT / 'serve/server.py'), '--engine', 'strata', '--config', str(cfg), '--host', '127.0.0.1', '--port', '18080']),
  'fork-flash-next': dict(port=18090, model='qwen3.8-flash-next-iq3_xxs', engine=str(FORK / 'build/bin/strata'),
      cfg=lambda d: {'exe': str(FORK / 'build/bin/unbiased-strata'), 'engine': str(FORK / 'build/bin/strata'), 'model_name': 'qwen3.8-flash-next-iq3_xxs', 'args': FN_ENGINE_ARGS},
      cmd=lambda d, cfg: [str(FORK / 'build/bin/unbiased-strata'), '--engine', str(FORK / 'build/bin/strata'), '-m', str(FN1), '--host', '127.0.0.1', '--port', '18090',
                          '--alias', 'qwen3.8-flash-next-iq3_xxs', '--'] + FN_ENGINE_ARGS),
  'upstream-qwen36-q3km': dict(port=18080, model='qwen3.6-35b-a3b-ud-q3_k_m', engine=str(UP_POLY),
      cfg=lambda d: {'exe': str(UP_POLY), 'cwd': str(ROOT), 'tokenizer': str(M / 'qwen36-mtp/pack-q3km/tokenizer'), 'model_name': 'qwen3.6-35b-a3b-ud-q3_k_m',
                     'log': str(d / 'engine.log'), 'args': q36_args(str(d / 'expert-profile.txt')), 'sampling': {'temperature': 0.6, 'top_p': 0.95, 'top_k': 20, 'min_p': 0.0}, 'fit_max_tokens': True},
      cmd=lambda d, cfg: [PY, str(ROOT / 'serve/server.py'), '--engine', 'strata', '--config', str(cfg), '--host', '127.0.0.1', '--port', '18080']),
  'fork-qwen36-q3km': dict(port=18091, model='qwen3.6-35b-a3b-ud-q3_k_m', engine=str(FORK / 'build/bin/strata-poly'),
      cfg=lambda d: {'exe': str(FORK / 'build/bin/unbiased-strata'), 'engine': str(FORK / 'build/bin/strata-poly'), 'model_name': 'qwen3.6-35b-a3b-ud-q3_k_m', 'args': q36_args(str(d / 'expert-profile.txt'))},
      cmd=lambda d, cfg: [str(FORK / 'build/bin/unbiased-strata'), '--engine', str(FORK / 'build/bin/strata-poly'), '-m', str(Q36), '--host', '127.0.0.1', '--port', '18091',
                          '--alias', 'qwen3.6-35b-a3b-ud-q3_k_m', '--'] + q36_args(str(d / 'expert-profile.txt'))),
}
# Attribution arms (2026-10-18): fork front end + upstream engine binaries, same files and flags. Compare with
# upstream-* (upstream front end + upstream engine) and fork-* (fork front end + fork engine).
ARMS['forkfe-upengine-flash-next'] = dict(port=18090, model='qwen3.8-flash-next-iq3_xxs', engine=str(ROOT / 'build/strata'),
    cfg=lambda d: {'exe': str(FORK / 'build/bin/unbiased-strata'), 'engine': str(ROOT / 'build/strata'), 'model_name': 'qwen3.8-flash-next-iq3_xxs', 'args': FN_ENGINE_ARGS},
    cmd=lambda d, cfg: [str(FORK / 'build/bin/unbiased-strata'), '--engine', str(ROOT / 'build/strata'), '-m', str(FN1), '--host', '127.0.0.1', '--port', '18090',
                        '--alias', 'qwen3.8-flash-next-iq3_xxs', '--'] + FN_ENGINE_ARGS)
ARMS['forkfe-upengine-qwen36-q3km'] = dict(port=18091, model='qwen3.6-35b-a3b-ud-q3_k_m', engine=str(ROOT / 'build/strata-poly'),
    cfg=lambda d: {'exe': str(FORK / 'build/bin/unbiased-strata'), 'engine': str(ROOT / 'build/strata-poly'), 'model_name': 'qwen3.6-35b-a3b-ud-q3_k_m', 'args': q36_args(str(d / 'expert-profile.txt'))},
    cmd=lambda d, cfg: [str(FORK / 'build/bin/unbiased-strata'), '--engine', str(ROOT / 'build/strata-poly'), '-m', str(Q36), '--host', '127.0.0.1', '--port', '18091',
                        '--alias', 'qwen3.6-35b-a3b-ud-q3_k_m', '--'] + q36_args(str(d / 'expert-profile.txt')))
order = sys.argv[2:] or list(ARMS)

def stat(v):
    v = [x for x in v if isinstance(x, (int, float))]  # the fork streams no usage block, so prompt_tokens may be None
    return {'median': statistics.median(v), 'min': min(v), 'max': max(v), 'n': len(v)} if v else None

def summarize(d):
    c = json.loads(next((d / 'community').rglob('results.json')).read_text()); r = c['results']
    s = json.loads((d / 'sustained.json').read_text())
    rows = r['chat']['requests'] + [q for v in r['prompts'].values() for q in v['requests']] + [q for v in r['agent']['sessions'] for q in v] + [x['metrics'] for x in s]
    checks = {'requests': len(rows), 'all_successful': all(x['ok'] for x in rows), 'skipped': r['skipped'], 'failures': r['failures']}
    sust = {k: stat(x['metrics'][k] for x in s) for k in ['decode_tps', 'prompt_tps', 'ttft_s', 'total_s']}
    off = sum(x['metrics'].get('drafts_offered') or 0 for x in s)
    sust['draft_acceptance_pct'] = 100 * sum(x['metrics'].get('drafts_accepted') or 0 for x in s) / off if off else None
    per = {}
    for rel in sorted({x['source'] for x in s}):
        xs = [x['metrics'] for x in s if x['source'] == rel]
        per[rel] = {k: stat(x[k] for x in xs) for k in ['prompt_tokens', 'decode_tps', 'prompt_tps', 'ttft_s', 'total_s']}
    summary = {'checks': checks, 'sustained': sust, 'chat': r['chat'].get('decode_tps'), 'chat_ttft_s': r['chat'].get('ttft_s'),
               'prefill': {k: v['prompt_tps'] for k, v in r['prompts'].items()}, 'prefill_ttft_s': {k: v['ttft_s'] for k, v in r['prompts'].items()},
               'agent': {k: r['agent'].get(k) for k in ('turn_decode_tps', 'turn_ttft_s', 'turn_prompt_tps') if r['agent'].get(k) is not None}, 'per_document': per}
    (d / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n'); return summary

def run_arm(name):
    a = ARMS[name]; d = OUT / name; d.mkdir(parents=True, exist_ok=True)
    cfg = d / 'server.json'; cfg.write_text(json.dumps(a['cfg'](d), indent=1) + '\n')
    cmd = a['cmd'](d, cfg); (d / 'server-command.json').write_text(json.dumps(cmd, indent=1) + '\n')
    prov = {'arm': name, 'engine_binary': a['engine'], 'engine_sha256': sha(a['engine']), 'fork_commit': subprocess.run(['git', '-C', str(FORK), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip(),
            'nvidia_smi': subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version,memory.total', '--format=csv,noheader'], capture_output=True, text=True).stdout.strip(),
            'cpu_quota': (open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us').read().strip() + '/' + open('/sys/fs/cgroup/cpu/cpu.cfs_period_us').read().strip()) if os.path.exists('/sys/fs/cgroup/cpu/cpu.cfs_quota_us') else 'n/a',
            'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    (d / 'provenance.json').write_text(json.dumps(prov, indent=1) + '\n')
    base = f"http://127.0.0.1:{a['port']}"
    log = open(d / 'server.log', 'w')
    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    ok = False
    try:
        if not bench.wait_ready(base, '', proc, 1800, lambda s: print(f'[{name}] {s}', flush=True)):
            raise RuntimeError('server failed to start; see server.log')
        (d / 'health.json').write_text(json.dumps(bench.http_json(base, '/health'), indent=1))
        bcmd = [PY, str(ROOT / 'tools/strata_bench.py'), '--url', base, '--config', str(cfg), '--runs', '3', '--long', '--out', str(d / 'community')]
        (d / 'benchmark-command.json').write_text(json.dumps(bcmd, indent=1))
        t0 = time.time(); subprocess.run(bcmd, cwd=ROOT, check=True); bench_s = time.time() - t0
        rows = []
        for run in range(3):
            for i, rel in enumerate(['docs/HOW_IT_WORKS.md', 'docs/INSTALL.md', 'docs/DETAILS.md']):
                body = (ROOT / rel).read_text()[:14000]
                messages = [{'role': 'user', 'content': f'Run identifier {run}-{i}. Read the following project documentation and write a detailed technical explanation of its design, tradeoffs, and how someone would use it in practice.\n\n{body}'}]
                response = bench.chat(base, '', messages, 512, False)
                row = {'run': run, 'source': rel, 'messages': messages, 'response': response, 'metrics': bench.digest(response)}
                rows.append(row); (d / 'sustained.json').write_text(json.dumps(rows, indent=1))
                print(f'[{name}] SUSTAINED {rel} {run} {json.dumps(row["metrics"])}', flush=True)
                if not row['metrics']['ok']: raise RuntimeError('sustained request failed')
        ok = True
        (d / 'complete.json').write_text(json.dumps({'complete': True, 'bench_seconds': bench_s, 'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=1))
    finally:
        bench.stop_server(proc)
        for _ in range(30):
            if proc.poll() is not None: break
            time.sleep(1)
        log.close()
        subprocess.run(['pkill', '-x', 'unbiased-strata']); subprocess.run(['pkill', '-x', 'strata']); subprocess.run(['pkill', '-x', 'strata-poly']); time.sleep(5)
        (d / 'server-exit.json').write_text(json.dumps({'returncode': proc.poll()}))
    if ok:
        print(f'[{name}] SUMMARY ' + json.dumps({k: summarize(d)[k] for k in ('chat', 'prefill', 'sustained')}, default=str)[:1500], flush=True)

if os.environ.get('US2_SUMMARIZE_ONLY'):
    for name in order: print(f'[{name}] SUMMARY ' + json.dumps({k: summarize(OUT / name)[k] for k in ('chat', 'prefill', 'sustained')}, default=str)[:1500], flush=True)
    sys.exit(0)
for name in order:
    print(f'===== {name} {time.strftime("%H:%M:%S")} =====', flush=True)
    run_arm(name)
print('ALL ARMS DONE', flush=True)
