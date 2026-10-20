#!/usr/bin/env python3
"""UnbiasedStrata 2 on the homelab RTX 4090 (VM 221, 2026-10-19): the fork alone, Flash-Next GSQ-RCO IQ3_XXS through
`strata`, 128K context, q4_0 KV. Adapted from bench/unbiased/2026-10-17-3090pod-step9/us2-step9-run.py: the same client
(upstream's tools/strata_bench.py --runs 3 --long) plus the three-document sustained supplement, one directory per arm.

  python3 us2-4090-run.py OUT probe <kv-resident>     start the server, record /health and the engine's start lines, stop
  python3 us2-4090-run.py OUT bench <kv-resident>     the full arm
  US2_SUMMARIZE_ONLY=1 python3 us2-4090-run.py OUT bench <kv-resident>
"""
import sys, pathlib, subprocess, json, time, hashlib, statistics, os, re
B = pathlib.Path('/tank/nvme/strata/us2-bench-20261019')
ROOT = B / 'upstream-tools'                      # upstream v0.1.45 tree (tools/, docs/, README.md: the client's prompts come from it)
sys.path.insert(0, str(ROOT / 'tools'))
import strata_bench as bench  # noqa: E402
PY = sys.executable
FORK = B / 'UnbiasedStrata'
M = pathlib.Path('/tank/nvme/strata')
FN1 = M / 'IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf'
FN2 = M / 'IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf'
PACK = M / 'pack-iq3-xxs'; MTP = M / 'mtp'
OUT = pathlib.Path(sys.argv[1]); MODE = sys.argv[2]; KV_RESIDENT = sys.argv[3]
OUT.mkdir(parents=True, exist_ok=True)
MODEL = 'qwen3.8-flash-next-iq3_xxs'
PORT = 18090

def engine_args():
    return ['--pack', str(PACK), '--native', str(FN1), '--ple-gguf', str(FN2), '--expert-profile', str(PACK / 'expert-profile.bin'),
            '--expert-cache', 'auto', '--prefill', 'auto', '--spec', '4', '--spec-min-p', '0.5', '--mtp', str(MTP),
            '--max-context', '131072', '--kv', 'q4_0', '--ple-io', 'ram', '--pool-workers', '15', '--kv-resident', KV_RESIDENT]

def server_cmd():
    return [str(FORK / 'build/bin/unbiased-strata'), '--engine', str(FORK / 'build/bin/strata'), '-m', str(FN1),
            '--host', '127.0.0.1', '--port', str(PORT), '--alias', MODEL, '--sse-ping-interval', '10', '--'] + engine_args()

def sha(p):
    h = hashlib.sha256(); f = open(p, 'rb'); [h.update(b) for b in iter(lambda: f.read(1 << 22), b'')]; return h.hexdigest()

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

def engine_info(log_path):
    txt = log_path.read_text(errors='replace')
    info = dict(re.findall(r'engine info: (\w+)=(\S+)', txt))
    info['ready_line'] = next((l for l in txt.splitlines() if 'engine ready' in l), None)
    info['strata_lines'] = [l for l in txt.splitlines() if l.startswith('strata:')][:40]
    return info

def provenance(name):
    return {'arm': name, 'kv_resident': KV_RESIDENT, 'engine_binary': str(FORK / 'build/bin/strata'), 'engine_sha256': sha(FORK / 'build/bin/strata'),
            'frontend_sha256': sha(FORK / 'build/bin/unbiased-strata'),
            'fork_commit': subprocess.run(['git', '-C', str(FORK), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip(),
            'upstream_client': 'strata-upstream 477ac13c (v0.1.45) tools/strata_bench.py; docs and README of that tree feed the agent turns',
            'nvidia_smi': subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version,memory.total', '--format=csv,noheader'], capture_output=True, text=True).stdout.strip(),
            'host': {'nproc': os.cpu_count(), 'mem_total_kib': int(open('/proc/meminfo').readline().split()[1]), 'kernel': os.uname().release},
            'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}

def start(d):
    cmd = server_cmd(); (d / 'server-command.json').write_text(json.dumps(cmd, indent=1) + '\n')
    (d / 'server-command.sh').write_text('#!/bin/sh\nexec ' + ' '.join(f"'{c}'" if ' ' in c else c for c in cmd) + '\n')
    log = open(d / 'server.log', 'w')
    proc = subprocess.Popen(cmd, cwd=str(FORK), stdout=log, stderr=subprocess.STDOUT)
    return proc, log

def stop(proc, log, d):
    bench.stop_server(proc)
    for _ in range(60):
        if proc.poll() is not None: break
        time.sleep(1)
    log.close()
    subprocess.run(['pkill', '-x', 'unbiased-strata']); subprocess.run(['pkill', '-x', 'strata']); time.sleep(5)
    (d / 'server-exit.json').write_text(json.dumps({'returncode': proc.poll()}))

def run_probe():
    name = f'probe-kvres{KV_RESIDENT}'; d = OUT / name; d.mkdir(parents=True, exist_ok=True)
    (d / 'provenance.json').write_text(json.dumps(provenance(name), indent=1) + '\n')
    proc, log = start(d); base = f'http://127.0.0.1:{PORT}'
    try:
        t0 = time.time()
        if not bench.wait_ready(base, '', proc, 1800, lambda s: print(f'[{name}] {s}', flush=True)):
            raise RuntimeError('server failed to start; see server.log')
        ready_s = time.time() - t0
        (d / 'health.json').write_text(json.dumps(bench.http_json(base, '/health'), indent=1))
        smi = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader'], capture_output=True, text=True).stdout.strip()
        r = bench.chat(base, '', [{'role': 'user', 'content': 'In one sentence, what is a hash table?'}], 64, False)
        info = engine_info(d / 'server.log'); info['ready_s'] = ready_s; info['nvidia_smi_after_load'] = smi
        info['smoke'] = {'metrics': bench.digest(r), 'text': r.get('text')}
        (d / 'probe.json').write_text(json.dumps(info, indent=1) + '\n')
        print(f'[{name}] PROBE ' + json.dumps({k: info.get(k) for k in ('context', 'expert_cache_mib', 'vram_free_mib', 'ready_s', 'nvidia_smi_after_load', 'smoke')}), flush=True)
    finally:
        stop(proc, log, d)

def run_bench():
    name = f'fork-flash-next-128k-q4kv-kvres{KV_RESIDENT}'; d = OUT / name; d.mkdir(parents=True, exist_ok=True)
    cfg = d / 'server.json'
    cfg.write_text(json.dumps({'exe': str(FORK / 'build/bin/unbiased-strata'), 'engine': str(FORK / 'build/bin/strata'), 'model_name': MODEL, 'args': engine_args()}, indent=1) + '\n')
    (d / 'provenance.json').write_text(json.dumps(provenance(name), indent=1) + '\n')
    proc, log = start(d); base = f'http://127.0.0.1:{PORT}'; ok = False
    try:
        if not bench.wait_ready(base, '', proc, 1800, lambda s: print(f'[{name}] {s}', flush=True)):
            raise RuntimeError('server failed to start; see server.log')
        (d / 'health.json').write_text(json.dumps(bench.http_json(base, '/health'), indent=1))
        bcmd = [PY, str(ROOT / 'tools/strata_bench.py'), '--url', base, '--config', str(cfg), '--runs', '3', '--long', '--out', str(d / 'community')]
        (d / 'benchmark-command.json').write_text(json.dumps(bcmd, indent=1))
        t0 = time.time(); subprocess.run(bcmd, cwd=str(ROOT), check=True); bench_s = time.time() - t0
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
        stop(proc, log, d)
        (d / 'engine-info.json').write_text(json.dumps(engine_info(d / 'server.log'), indent=1) + '\n')
    if ok:
        print(f'[{name}] SUMMARY ' + json.dumps({k: summarize(d)[k] for k in ('chat', 'prefill', 'sustained')}, default=str)[:1500], flush=True)

if os.environ.get('US2_SUMMARIZE_ONLY'):
    d = OUT / f'fork-flash-next-128k-q4kv-kvres{KV_RESIDENT}'
    print(json.dumps(summarize(d), indent=1, default=str)); sys.exit(0)
if MODE == 'probe': run_probe()
elif MODE == 'bench': run_bench()
else: sys.exit('mode: probe | bench')
print('DONE', flush=True)
