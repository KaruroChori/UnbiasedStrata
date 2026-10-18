#!/bin/bash
# PLAN.md section 11, row 3: wall time and tokens for one fixed coding task under pi, three runs, against one server.
#   us2-pi-row3.sh <pi-model-id> <outdir> [runs]
set -u
MODEL=$1; OUT=$2; RUNS=${3:-3}; mkdir -p "$OUT"
S=$(cd "$(dirname "$0")" && pwd); A=$S/pi-agent; SRC=$S/pi-task
TASK="You are in a small Python project (wordstats.py counts words in text files). Do all of the following, using your tools, and verify each step by running commands: 1) Read wordstats.py and sample.txt. 2) Add a --json flag to wordstats.py: with it, print the full word counts as a JSON object (word -> count) instead of the top-10 table; without it, behaviour is unchanged. Use only the standard library. 3) Write test_wordstats.py with unittest tests covering count_words, the default table output and the --json output (run the script via subprocess with sys.executable). 4) Run python3 -m unittest -v and fix anything that fails. 5) Run python3 wordstats.py --json sample.txt and show the output. 6) git add -A and git commit with a one-line message. Finish with a short summary of what you changed."
echo "$TASK" > "$OUT/task.txt"
for run in $(seq 1 $RUNS); do
  W=$OUT/run$run; rm -rf "$W/project"; mkdir -p "$W"; cp -R "$SRC" "$W/project"; (cd "$W/project" && git reset -q --hard fc6976d && rm -rf __pycache__)
  t0=$(date +%s.%N)
  (cd "$W/project" && PI_CODING_AGENT_DIR=$A timeout 1800 pi -p --no-session --provider "UnbiasedStrata 2" --model "$MODEL" "$TASK" > "$W/pi.out" 2> "$W/pi.err"); rc=$?
  t1=$(date +%s.%N)
  tests=$(cd "$W/project" && python3 -m unittest 2>&1 | tail -1); commits=$(cd "$W/project" && git rev-list --count HEAD)
  json_ok=$(cd "$W/project" && python3 wordstats.py --json sample.txt 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print("ok" if d.get("the")==3 and d.get("sea")==2 else "wrong")' 2>/dev/null || echo fail)
  python3 - "$W/result.json" "$run" "$t0" "$t1" "$rc" "$tests" "$commits" "$json_ok" <<'PY'
import json,sys
out,run,t0,t1,rc,tests,commits,json_ok=sys.argv[1:]
r={"run":int(run),"wall_seconds":round(float(t1)-float(t0),1),"pi_exit":int(rc),"unittest_last_line":tests,"commits":int(commits),"json_flag":json_ok}
json.dump(r,open(out,"w"),indent=1); print(json.dumps(r))
PY
done
