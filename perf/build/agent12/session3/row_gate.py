# row_gate.py <run dir> <row id> (M12, session 3): common gates C1-C4, C6, C7 of GATE-CHECKLIST.md, read-only.
# Also compares run.json cvars/env/bin with the queue row (build/agent3/session3/queue-s3.jsonl), re-hashes the exe
# against the bin's MANIFEST, and prints the tails of M3's postcheck outputs (s4b/logs/<id>.check|f10|p2c.txt).
# Exit 0 = no common-gate problem found (row-specific gates are read from the postcheck output), 1 = problems.
import glob, hashlib, json, os, re, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
run, rid = sys.argv[1], sys.argv[2]
if not os.path.isabs(run):
    run = os.path.join(REPO, run)
probs, notes = [], []


def P(ok, msg):
    (notes if ok else probs).append(('ok   ' if ok else 'BAD  ') + msg)


rj = json.load(open(os.path.join(run, 'run.json'), encoding='utf-8-sig'))
q = None
for qf in ('build/agent3/session3/queue-s3.jsonl', 'build/agent3/s4b/queue.jsonl'):  # last match wins
    for line in open(os.path.join(REPO, qf), encoding='utf-8-sig'):
        if line.strip().startswith('{') and json.loads(line).get('id') == rid:
            q = json.loads(line)
print('queue row: %s' % (json.dumps(q) if q else 'NOT FOUND'))
# C1 exit
P(rj.get('exit_code') == 0, 'exit_code %s (%s), close %s, elapsed %s s of %s' % (
    rj.get('exit_code'), rj.get('exit_code_hex'), rj.get('close_method'), rj.get('elapsed_s'), rj.get('seconds_requested')))
P(not rj.get('wer_seen'), 'wer_seen %s' % rj.get('wer_seen'))
P(not rj.get('crash_events'), 'crash_events %s' % rj.get('crash_events'))
P(not rj.get('exited_early'), 'exited_early %s' % rj.get('exited_early'))
# C2 bin + manifest
args = q['args'] if q else []
qa = {args[i]: args[i + 1] for i in range(0, len(args) - 1) if args[i].startswith('-')}
bd = os.path.normcase(os.path.abspath(os.path.join(REPO, qa.get('-BinDir', '?'))))
P(os.path.normcase(rj.get('bin_dir', '')) == bd, 'bin_dir %s (queued %s)' % (rj.get('bin_dir'), qa.get('-BinDir')))
man = os.path.join(rj.get('bin_dir', ''), 'MANIFEST.txt')
exe_h = hashlib.sha256(open(os.path.join(run, 'legodimensions.exe'), 'rb').read()).hexdigest().upper()
mtxt = open(man, encoding='utf-8-sig').read().upper() if os.path.exists(man) else ''
P(exe_h == (rj.get('exe_sha256') or '').upper() and exe_h in mtxt, 'run exe sha256 %s = run.json and in %s' % (exe_h[:16], man))
# C3 switches as queued
qc = dict(kv.split('=', 1) for kv in qa.get('-Cvar', '').split(';') if '=' in kv)
rc = rj.get('cvars') or {}
P(qc == {k: str(v) for k, v in rc.items()}, 'cvars %s (queued %s)' % (rc, qc))
qe = dict(kv.split('=', 1) for kv in qa.get('-Env', '').split(';') if '=' in kv)
re_ = {k: v for k, v in (rj.get('env') or {}).items() if k in qe}
P(qe == re_, 'env %s (queued %s)' % (re_, qe))
P(os.path.basename(str((rj.get('input_script') or {}).get('script') or '-')) == os.path.basename(qa.get('-InputScript', '-')),
  'input script %s (queued %s)' % ((rj.get('input_script') or {}).get('script'), qa.get('-InputScript')))
# log scan
logs = sorted(glob.glob(os.path.join(run, 'game*.log')))
pat = {k: 0 for k in ['Recovered stale physical page protection', 'Unhandled guest physical write fault',
                      'PhysicalHeap::Protect failed', 'STUCK-LOCK', 'REX_FATAL', 'C1 keep-watch: on (with',
                      'C1 keep-watch: on, but', 'blocked for this process', 'C1 verify: on.', 'C1 verify K:',
                      'C1 verify F:', 'GPU wait back-off: ON', 'd3d12_submit_split_kb: splitting', 'd3d12_submit_split: ',
                      'Host timer resolution set', 'TimerQueue: precise wait']}
nl = 0
for p in logs:
    for line in open(p, encoding='utf-8', errors='replace'):
        nl += 1
        for k in pat:
            if k in line:
                pat[k] += 1
notes.append('     logs %d (%d lines); counts: %s' % (len(logs), nl, '; '.join('%s=%d' % (k, v) for k, v in pat.items())))
for k in ['Recovered stale physical page protection', 'Unhandled guest physical write fault', 'PhysicalHeap::Protect failed',
          'REX_FATAL', 'C1 keep-watch: on, but', 'blocked for this process']:
    P(pat[k] == 0, 'C4 "%s" x%d' % (k, pat[k]))
kw = str(rc.get('physical_protect_keep_watch', '')).lower() == 'true'
vf = str(rc.get('physical_protect_keep_watch_verify', '')).lower() == 'true'
# FINAL bins (build/agent2/final/BIN-PINS.md) ship the win3 values as code defaults, so the C3 "line iff cvar/env set"
# rule doesn't hold there: final_gate.py <run> <F1..F7> checks those lines via check-defaults.py instead.
final_bin = os.path.basename(rj.get('bin_dir', '').rstrip('\\/')).lower() in (
    'devfinal-bin', 'devfinal-off-bin', 'nativefinal-bin', 'nativefinal-off-bin')
if final_bin:
    notes.append('     C3 init lines skipped: FINAL bin %s -> run final_gate.py <run> <F1..F7>' % os.path.basename(rj['bin_dir']))
else:
    P(pat['C1 keep-watch: on (with'] == (1 if kw else 0), 'C3 keep-watch init x%d (keep_watch=%s)' % (pat['C1 keep-watch: on (with'], kw))
P(pat['C1 verify: on.'] == (1 if vf else 0), 'C3 "C1 verify: on." x%d (verify=%s)' % (pat['C1 verify: on.'], vf))
gw = 'LEGO_GPU_WAIT_BACKOFF_US' in qe
sp = 'd3d12_submit_split_kb' in qc and qc['d3d12_submit_split_kb'] != '0'
P(pat['d3d12_submit_split_kb: splitting'] == (1 if sp else 0), 'C3 split init x%d (split cvar %s)' % (pat['d3d12_submit_split_kb: splitting'], sp))
ht = 'host_timer_resolution_ms' in qc
pw = str(qc.get('timer_queue_precise_wait', '')).lower() == 'true'
if not final_bin:
    P(pat['GPU wait back-off: ON'] == (1 if gw else 0), 'C3 back-off init x%d (env set %s)' % (pat['GPU wait back-off: ON'], gw))
    P(pat['Host timer resolution set'] == (1 if ht else 0), 'C3 host timer line x%d (cvar %s)' % (pat['Host timer resolution set'], ht))
    P(pat['TimerQueue: precise wait'] == (1 if pw else 0), 'C3 precise-wait line x%d (cvar %s)' % (pat['TimerQueue: precise wait'], pw))
notes.append('     STUCK-LOCK lines %d (C5: see f10 output / by hand)' % pat['STUCK-LOCK'])
# C6 dumps
dmps = [os.path.relpath(p, run) for p in glob.glob(os.path.join(run, '**', '*.dmp'), recursive=True)]
P(not dmps and not rj.get('dumps'), 'C6 dumps in dir %s, run.json dumps %s' % (dmps, rj.get('dumps')))
# C7 coverage
isr = rj.get('input_script') or {}
marks = []
ic = os.path.join(run, 'input.csv')
if os.path.exists(ic):
    for line in open(ic, encoding='utf-8', errors='replace'):
        m = re.search(r',mark,([^,\s]+)', line)
        if m:
            marks.append(m.group(1))
notes.append('     C7 steps %s/%s last %s timeouts %s; marks %s' % (isr.get('steps_done'), isr.get('steps_total'),
                                                                     isr.get('last_step'), isr.get('timeouts'), marks[-6:]))
if 'level' in os.path.basename(qa.get('-InputScript', '')):
    P('vortex' in marks, 'C7 vortex mark reached')
for line in probs + notes:
    print(line)
for ext in ('check', 'f10', 'p2c'):
    f = os.path.join(REPO, 'build/agent3/s4b/logs/%s.%s.txt' % (rid, ext))
    if os.path.exists(f):
        b = open(f, 'rb').read()  # postcheck's *> redirection writes UTF-16LE with a BOM
        t = b.decode('utf-16' if b[:2] in (b'\xff\xfe', b'\xfe\xff') else 'utf-8-sig', errors='replace').splitlines()
        sel = [l for l in t if re.match(r'(PROOF|VERDICT|RESULT|BASE items|EVENT|event|  missing)', l)] or t[-8:]
        print('--- %s.%s.txt (%d lines)' % (rid, ext, len(t)))
        for l in sel[:40]:
            print('  ' + l[:300])
    else:
        print('--- %s.%s.txt: not present' % (rid, ext))
print('COMMON: %s (%d problems)' % ('OK' if not probs else 'PROBLEMS', len(probs)))
sys.exit(1 if probs else 0)
