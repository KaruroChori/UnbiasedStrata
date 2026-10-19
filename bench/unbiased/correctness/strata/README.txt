strata/<arm>/: command.sh (the serve line per sequence), <seq>.engine.log (stderr), <seq>.done.txt (DONE line),
<seq>.scored.tsv (the STRATA_LOGPOS rows aligned to the reference answer; <seq>.offset.txt = k when the rows start at
answer[k], a resumed read loses step 0) for the arms scored against llama.cpp. The pin2, pint4, pingpu, pincpu and
cpu2 arms are T0 repeats whose rows equal pin's (pincpu, pingpu, pint4, pin2) or cpu's (cpu2) byte for byte
(probes/placement/README.txt), so only their logs are kept. The full pos.tsv files (prompt positions too) stay on the
VM under ~/us2-results/correctness/strata/.
