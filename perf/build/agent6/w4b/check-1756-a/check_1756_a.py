#!/usr/bin/env python3
"""check-1756-a: independent read-only check of Agent 6's W5 game.log logdiff (task #13).
python -B build/agent6/w4b/check-1756-a/check_1756_a.py  -> RESULT.txt next to this script. Stdlib only.
gate_logdiff.py is imported read-only (no bytecode). Agent 6's outputs are parsed as text, for check 4 only."""
import sys
sys.dont_write_bytecode = True
import ast, datetime, importlib.util, json, os, re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
MATRIX = os.path.join(ROOT, 'build', 'agent8', 'matrix', '20261122-1756')
RUNS_DIR = os.path.join(MATRIX, 'runs')
A6 = os.path.join(ROOT, 'build', 'agent6', 'w4b', 'out-20261122-1756-vs-s0')
GATE_PY = os.path.join(ROOT, 'bench', 'agent8', 'run', 'gate_logdiff.py')
OUT = os.path.join(HERE, 'RESULT.txt')

ARMS = ['base', 'cold-base', 's0', 'd11', 'd11t', 'd11p']
RUNS = {'base': ['1757-base-r1', '1817-base-r2', '1825-base-r3'], 'cold-base': ['1756-cold-base'],
        's0': ['1800-s0-r1', '1808-s0-r2', '1827-s0-r3'], 'd11': ['1802-d11-r1', '1810-d11-r2', '1819-d11-r3'],
        'd11t': ['1804-d11t-r1', '1813-d11t-r2', '1821-d11t-r3'], 'd11p': ['1806-d11p-r1', '1815-d11p-r2', '1823-d11p-r3']}
ALL = sorted(n for a in ARMS for n in RUNS[a])
ARM_OF = {n: a for a in ARMS for n in RUNS[a]}
NONS0 = ['base', 'cold-base', 'd11', 'd11t', 'd11p']
TEST = ['d11', 'd11t', 'd11p']
B_CV = ['framerate_limit=0']
D11_CV = B_CV + ['host_timer_resolution_ms=1', 'host_timer_throttling_optout=true', 'precise_guest_sleep=true',
                 'wait_timeout_round_up=true', 'cs_spin=true', 'spinlock_pause_spin=true', 'clock_lockfree=true',
                 'tls_bounds_fix=true']
EXP_CV = {'base': B_CV, 'cold-base': B_CV, 's0': B_CV, 'd11': D11_CV, 'd11t': D11_CV,
          'd11p': D11_CV + ['timer_queue_precise_wait=true']}
EXP_ENV = {a: ({'REX_TIMER_WAIT_BLOCKING': '1'} if a == 'd11t' else {}) for a in ARMS}
EXP_BIN = {a: ('devoff3-bin' if a in ('base', 'cold-base') else 'devoff4-bin') for a in ARMS}
EXIT_SEQ = ['Window closing, shutting down...', 'Execution complete', 'Title terminated; hard-exiting process.']
L_I = 'Host timer resolution set to 1 ms (background opt-out on)'
L_III = 'TimerQueue: precise wait (timer_queue_precise_wait)'
EXP_I = {a: (1 if a in TEST else 0) for a in ARMS}
EXP_III = {a: (1 if a == 'd11p' else 0) for a in ARMS}
LINE_RE = re.compile(r'^\[(?P<ts>\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\] \[(?P<lvl>[a-z]+)\] \[(?P<cat>[^\]]*)\] (?:\[t\d+\] )?(?P<msg>.*)$')
TOY_RE = re.compile(r'^Toypad\[(Write|Read)\s*\]\s*(.*)$')
HEX = re.compile(r'0x[0-9A-Fa-f]+')
DEC = re.compile(r'\d+')
IOD_RE = re.compile(r'IoDismountVolumeByFileHandle\((0x[0-9A-Fa-f]+)\)')
CSTR = {'c1': L_I, 'c2': L_III, 'c3': 'Host timer resolution', 'c4': 'TimerQueue',
        'c5': 'IoDismountVolumeByFileHandle(0xf8000160)', 'c6': 'IoDismountVolumeByFileHandle(0xf8000164)',
        'c7': '[warning]', 'c8': '[error]'}

out = []
w = out.append


def rtext(p):
    with open(p, 'rb') as fh:
        b = fh.read()
    if b[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return b.decode('utf-16', 'replace')
    if b[:3] == b'\xef\xbb\xbf':
        b = b[3:]
    return b.decode('utf-8', 'replace')


def rlines(p):
    L = re.split(r'\r\n|\n|\r', rtext(p))
    if L and L[-1] == '':
        L.pop()
    return L


def pts(ts):
    return datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S.%f')


# ---------------------------------------------------------------- load
found = sorted(x for x in os.listdir(RUNS_DIR) if os.path.isdir(os.path.join(RUNS_DIR, x)))
R = {}
for n in ALL:
    d = os.path.join(RUNS_DIR, n)
    recs = []
    for ln in rlines(os.path.join(d, 'game.log')):
        m = LINE_RE.match(ln)
        recs.append((m.group('lvl'), m.group('cat'), m.group('msg'), m.group('ts'), ln) if m else (None, None, ln, None, ln))
    R[n] = dict(n=n, arm=ARM_OF[n], d=d, rj=json.loads(rtext(os.path.join(d, 'run.json'))), recs=recs,
                bytes=os.path.getsize(os.path.join(d, 'game.log')),
                logs=sorted(f for f in os.listdir(d) if re.match(r'^game(\.\d+)?\.log$', f, re.I)))

ST = {}
for n in ALL:
    recs = R[n]['recs']
    ne = [x for x in recs if x[4] != '']
    lv = Counter((x[0] or 'raw') for x in ne)
    toy, seq, firstw, closing = Counter(), [], None, None
    for lvl, cat, msg, ts, raw in recs:
        m = TOY_RE.match(msg) if lvl else None
        if m:
            toy['%s %s' % (lvl, m.group(1))] += 1
            if m.group(1) == 'Write':
                t = m.group(2).split()
                seq.append(t[4] if len(t) > 4 else '?')
                firstw = firstw or ts
        if lvl and msg == EXIT_SEQ[0] and closing is None:
            closing = ts
    tss = [x[3] for x in recs if x[3]]
    iod = Counter()
    for x in recs:
        iod.update(IOD_RE.findall(x[4]))
    ST[n] = dict(lines=len(recs), empty=len(recs) - len(ne), lv=lv, toy=toy, seq=seq,
                 toyW=sum(v for k, v in toy.items() if k.endswith('Write')),
                 toyR=sum(v for k, v in toy.items() if k.endswith('Read')), B1=seq.count('B1'),
                 close=round((pts(closing) - pts(firstw)).total_seconds(), 1) if closing and firstw else None,
                 t0=tss[0], t1=tss[-1], dur=round((pts(tss[-1]) - pts(tss[0])).total_seconds()),
                 exit_line=sum(1 for x in recs if x[0] and x[2] == EXIT_SEQ[2]),
                 last3=[x[2] for x in ne[-3:]], iod=iod,
                 c={k: sum(1 for x in recs if s in x[4]) for k, s in CSTR.items()},
                 warn_sub=sum(1 for x in recs if '[warning]' in x[4]), err_sub=sum(1 for x in recs if '[error]' in x[4]))

w('=== check-1756-a: independent read-only check of matrix 20261122-1756 (W5) game.log logdiff ===')
w('generated %s; python %s; script %s' % (datetime.datetime.now().isoformat(timespec='seconds'), sys.version.split()[0], os.path.abspath(__file__)))
w('matrix %s' % MATRIX)
w('run dirs found %d; expected 16; missing %s; extra %s' % (len(found), sorted(set(ALL) - set(found)) or '-', sorted(set(found) - set(ALL)) or '-'))
w('')

# ---------------------------------------------------------------- CHECK 1
TEXT_EXT = ('.txt', '.json', '.log', '.md')


def scan_text(paths):
    stuck, ci, wmc = [], 0, 0
    for p in paths:
        for ln in rlines(p):
            if 'STUCK' in ln:
                stuck.append('%s: %s' % (os.path.basename(p), ln.strip()[:160]))
            if 'stuck' in ln.lower():
                ci += 1
            if 'WM_CLOSE' in ln:
                wmc += 1
    return stuck, ci, wmc


C1, c1_fail = {}, []
w('== CHECK 1: run health, all 16 runs (run.json, run dir, game.log tail) ==')
for n in ALL:
    r, rj = R[n], R[n]['rj']
    c = rj.get('close') or {}
    files = [os.path.join(dp, f) for dp, dn, fn in os.walk(r['d']) for f in fn]
    dmp = [os.path.relpath(p, r['d']) for p in files if p.lower().endswith('.dmp')]
    stuck, ci, wmc = scan_text([p for p in files if os.path.splitext(p)[1].lower() in TEXT_EXT])
    sumclose = [ln.strip() for ln in rlines(os.path.join(r['d'], 'summary.txt')) if ln.startswith('close')]
    v = dict(status=rj.get('status'), problems=rj.get('problems'), exit_code_hex=rj.get('exit_code_hex'),
             close_exit_code_hex=c.get('exit_code_hex'), wm_close_posted=c.get('wm_close_posted'),
             wm_close_repost_s=c.get('wm_close_repost_s'), killed=c.get('killed'), clean=c.get('clean'),
             exit_wait_s=c.get('exit_wait_s'), werfault_seen=rj.get('werfault_seen'),
             foreign_crash_dumps=rj.get('foreign_crash_dumps'), dialogs=rj.get('dialogs'),
             not_responding_samples=rj.get('not_responding_samples'), perf_csv_stalled=rj.get('perf_csv_stalled'))
    bad = []
    for k, ok in (('status', v['status'] == 'OK'), ('problems', v['problems'] == []),
                  ('exit_code_hex', v['exit_code_hex'] == '0x00000000'), ('close.exit_code_hex', v['close_exit_code_hex'] == '0x00000000'),
                  ('wm_close_posted', v['wm_close_posted'] == 1), ('wm_close_repost_s', v['wm_close_repost_s'] is None),
                  ('killed', v['killed'] is False), ('clean', v['clean'] is True),
                  ('exit_wait_s', isinstance(v['exit_wait_s'], (int, float)) and v['exit_wait_s'] < 60),
                  ('werfault_seen', v['werfault_seen'] is False), ('foreign_crash_dumps', v['foreign_crash_dumps'] == []),
                  ('dialogs', v['dialogs'] == []), ('not_responding_samples', v['not_responding_samples'] == 0),
                  ('perf_csv_stalled', v['perf_csv_stalled'] is False), ('dmp', not dmp), ('STUCK', not stuck),
                  ('exit_seq', ST[n]['last3'] == EXIT_SEQ), ('one game.log', r['logs'] == ['game.log'])):
        if not ok:
            bad.append(k)
    C1[n] = dict(v=v, dmp=dmp, stuck=stuck, ci=ci, wmc=wmc, bad=bad, sumclose=sumclose)
    if bad:
        c1_fail.append('%s: %s' % (n, bad))
    w('  %-15s %-9s %s | status=%s problems=%s exit=%s close.exit=%s wm_close_posted=%s repost=%s killed=%s clean=%s exit_wait_s=%s'
      % (n, r['arm'], 'ok ' if not bad else 'BAD', v['status'], len(v['problems'] or []), v['exit_code_hex'], v['close_exit_code_hex'],
         v['wm_close_posted'], v['wm_close_repost_s'], v['killed'], v['clean'], v['exit_wait_s']))
    w('  %-25s   wer=%s foreign_dumps=%s dialogs=%s not_resp=%s perf_stalled=%s dmp=%d STUCK=%d (case-insens. %d) WM_CLOSE=%d logs=%s tag=%s seconds=%s'
      % ('', v['werfault_seen'], len(v['foreign_crash_dumps'] or []), len(v['dialogs'] or []), v['not_responding_samples'],
         v['perf_csv_stalled'], len(dmp), len(stuck), ci, wmc, r['logs'], rj.get('tag'), (rj.get('params') or {}).get('seconds')))
    w('  %-25s   last3=%s%s' % ('', ST[n]['last3'], '' if not bad else '  FAILED: %s' % bad))
top = [os.path.join(MATRIX, f) for f in os.listdir(MATRIX) if os.path.isfile(os.path.join(MATRIX, f)) and os.path.splitext(f)[1].lower() in TEXT_EXT]
tstuck, tci, twm = scan_text(top)
lg = [os.path.join(MATRIX, 'logs', f) for f in os.listdir(os.path.join(MATRIX, 'logs'))]
lstuck, lci, lwm = scan_text(lg)
w('  matrix top-level (%s): STUCK=%d (case-insens. %d) WM_CLOSE=%d; info: logs/ (%d files) STUCK=%d (case-insens. %d)'
  % (', '.join(sorted(os.path.basename(p) for p in top)), len(tstuck), tci, twm, len(lg), len(lstuck), lci))
for s in tstuck + lstuck:
    w('    STUCK line: %s' % s)
CK1 = not c1_fail and not tstuck and found == ALL
w('CHECK 1: %s (%d/16 runs ok; failures: %s)' % ('PASS' if CK1 else 'FAIL', 16 - len(c1_fail), c1_fail or 'none'))
w('')

# ---------------------------------------------------------------- CHECK 2
w('== CHECK 2: required lines and arm config ==')
c2_fail = []
w('  run             arm       (i) (ii) (iii) (iv) | (v) env_set | (vi) cvar | (vii) bin | info: other "timer" lines')
for n in ALL:
    r, rj, a = R[n], R[n]['rj'], R[n]['arm']
    recs = r['recs']
    i_ = sum(1 for x in recs if x[0] and x[2] == L_I)
    ii = [x[4] for x in recs if x[2] != L_I and ('Host timer resolution' in x[4] or 'Could not set the host timer resolution' in x[4] or 'opt-out failed' in x[4])]
    iii = sum(1 for x in recs if x[0] and x[2] == L_III)
    iv = [x[4] for x in recs if x[2] != L_III and 'TimerQueue' in x[4]]
    tim = [x[4] for x in recs if x[2] not in (L_I, L_III) and re.search(r'(?i)timer', x[4])]
    env = rj.get('env_set') or {}
    penv = (rj.get('params') or {}).get('env') or []
    rexcount = rtext(os.path.join(r['d'], 'run.json')).count('REX_TIMER_WAIT_BLOCKING')
    cv = (rj.get('params') or {}).get('cvar') or []
    argcv = sorted(x[2:] for x in rj.get('args') or [] if x.startswith('--') and not re.match(
        r'--(log_file|perf_log_csv|native_settings_load|discord_rpc|audio_mute|pause_when_unfocused)=', x))
    binb = os.path.basename((rj.get('bin_dir') or '').rstrip('\\/'))
    ok = dict(i=i_ == EXP_I[a], ii=not ii, iii=iii == EXP_III[a], iv=not iv, v=env == EXP_ENV[a],
              vi=sorted(cv) == sorted(EXP_CV[a]) and len(cv) == len(set(cv)), vii=binb == EXP_BIN[a])
    bad = [k for k, x in ok.items() if not x]
    if bad:
        c2_fail.append('%s: %s' % (n, bad))
    w('  %-15s %-9s %d   %d    %d     %d    | %-28s | %s %s | %s | %d %s' % (
        n, a, i_, len(ii), iii, len(iv), json.dumps(env), 'set-ok' if ok['vi'] else 'SET-BAD',
        'order-ok' if cv == EXP_CV[a] else 'order-differs', binb, len(tim), ('BAD ' + str(bad)) if bad else ''))
    w('  %-25s   params.env=%s; REX_TIMER_WAIT_BLOCKING in run.json text %dx; args cvars == params.cvar: %s; cvar=%s'
      % ('', penv, rexcount, argcv == sorted(cv), cv))
    for s in ii + iv + tim:
        w('      line: %s' % s[:200])
CK2 = not c2_fail
w('CHECK 2: %s (failures: %s)' % ('PASS' if CK2 else 'FAIL', c2_fail or 'none'))
w('')


# ---------------------------------------------------------------- CHECK 3
def key(rec, run, sch):
    lvl, cat, msg = rec[0], rec[1], rec[2].replace(run, '<run>').rstrip()
    if sch != 'C':
        m = TOY_RE.match(msg) if lvl else None
        if m:
            nt = 5 if (m.group(1) == 'Write' or sch == 'B') else 4
            msg = 'Toypad[%s] %s' % (m.group(1), ' '.join(m.group(2).split()[:nt]))
        elif sch in ('B', 'N6'):
            msg = DEC.sub('#', HEX.sub('#', msg))
    return '[%s] [%s] %s' % (lvl, cat, msg) if lvl else '[raw] ' + msg


CNT = {s: {n: Counter(key(x, n, s) for x in R[n]['recs'] if x[4] != '') for n in ALL} for s in ('B', 'C', 'A6', 'N6')}


def cls(k):
    l = k.lower()
    if 'timer resolution' in l or 'timerqueue' in l or 'timer_queue' in l or 'opt-out failed' in l:
        return 'TIMER-MODE'
    if 'toypad' in l:
        return 'TOYPAD'
    if 'iodismountvolumebyfilehandle' in l:
        return 'IOD'
    return 'OTHER'


def dvs(refc, c):
    res = []
    for k in sorted(set(c).union(*[set(x) for x in refc])):
        rc = [x.get(k, 0) for x in refc]
        v, lo, hi = c.get(k, 0), min(rc), max(rc)
        t = 'NEW' if (v and not hi) else 'GONE' if (not v and lo) else 'COUNT' if (v < lo or v > hi) else None
        if t:
            res.append((t, k, rc, v))
    return res


def armdiff(sch, arm):
    refc = [CNT[sch][n] for n in RUNS['s0']]
    res = {}
    for n in RUNS[arm]:
        for t, k, rc, v in dvs(refc, CNT[sch][n]):
            res.setdefault(k, {'rc': rc, 'runs': {}})['runs'][n] = (t, v)
    return res


def show(res, skip_toy=False):
    cat = Counter()
    for k in sorted(res, key=lambda k: (cls(k), k)):
        cat[cls(k)] += 1
        if skip_toy and cls(k) == 'TOYPAD':
            continue
        w('      %-10s s0 %-9s %s   %s' % (cls(k), res[k]['rc'], ' '.join('%s=%s:%d' % (n, t, v) for n, (t, v) in sorted(res[k]['runs'].items())), k[:190]))
    return cat


def timer_ok(res, arm, exact):
    exp = {'[info] [core] ' + (L_I if exact else DEC.sub('#', L_I))}
    if arm == 'd11p':
        exp.add('[info] [core] ' + L_III)
    got = {k for k in res if cls(k) == 'TIMER-MODE'}
    return got == exp and all(len(res[k]['runs']) == len(RUNS[arm]) and all(t == 'NEW' and v == 1 for t, v in res[k]['runs'].values()) for k in got)


w('== CHECK 3: same-bin diff, d11 / d11t / d11p vs s0 (all devoff4-bin) ==')
spec = importlib.util.spec_from_file_location('gate_logdiff_ro', GATE_PY)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
ure = re.compile(gate.UNIMPL_DEFAULT)
SCAN = {n: gate.scan(R[n]['d'], ure) for n in ALL}
FAILN, GATE_ROWS = {}, {}
for arm in NONS0:
    FAILN[arm] = 0
    for n in RUNS[arm]:
        for s in RUNS['s0']:
            f, notes, match, diff = gate.compare(SCAN[s], SCAN[n], 50)
            FAILN[arm] += len(f)
            GATE_ROWS[(n, s)] = (f, notes, diff)
w('  (A) gate_logdiff.compare(A=s0 run, B=arm run) in-process (scan(run dir, UNIMPL_DEFAULT)); verdict FAIL iff findings non-empty')
for arm in TEST:
    for n in RUNS[arm]:
        for s in RUNS['s0']:
            f, notes, diff = GATE_ROWS[(n, s)]
            w('    B=%-14s A=%-11s %s findings=%d notes=%d warn-diff new=%d gone=%d count_changes=%d%s' % (
                n, s, 'FAIL' if f else 'PASS', len(f), len(notes), diff['new_in_b_total'], diff['gone_in_b_total'],
                diff['count_changes_total'], ''.join('\n        finding: %s' % x for x in f) +
                ''.join('\n        note: %s' % x for x in notes) +
                ''.join('\n        new: %s' % x['msg'] for x in diff['new_in_b']) + ''.join('\n        gone: %s' % x['msg'] for x in diff['gone_in_b'])))
A_ok = all(FAILN[a] == 0 for a in TEST)
w('  (A) total FAIL findings: d11 %d, d11t %d, d11p %d over 27 pairs  -> %s' % (FAILN['d11'], FAILN['d11t'], FAILN['d11p'], 'PASS' if A_ok else 'FAIL'))
w('')
w('  (B) normalized multiset vs the s0 set: ts and [tNNNN] stripped, run-dir name -> <run>, Toypad[Write|Read] payload -> first 5 tokens')
w('      (verbatim), elsewhere 0x.. -> # then decimal digit runs -> #. NEW = in the arm run, in no s0 run; GONE = in every s0 run, missing')
w('      from the arm run; COUNT = count outside s0 min..max. Rows: category, s0 counts [r1,r2,r3], arm run=type:count, key')
B_ok, BCAT = True, {}
for arm in TEST:
    res = armdiff('B', arm)
    w('    arm %s:' % arm)
    cat = show(res)
    BCAT[arm] = cat
    tok = timer_ok(res, arm, False)
    B_ok = B_ok and tok and cat['OTHER'] == 0
    w('    arm %s: keys TIMER-MODE %d TOYPAD %d IOD %d OTHER %d; TIMER-MODE exactly as expected ((i) 3/3%s): %s'
      % (arm, cat['TIMER-MODE'], cat['TOYPAD'], cat['IOD'], cat['OTHER'], ', (iii) 3/3' if arm == 'd11p' else '', tok))
w('    pairwise (B), keys whose count differs, T=TIMER-MODE Y=TOYPAD I=IOD O=OTHER:')
for arm in TEST:
    for n in RUNS[arm]:
        cells = []
        for s in RUNS['s0']:
            a, b = CNT['B'][s], CNT['B'][n]
            cc = Counter(cls(k) for k in set(a) | set(b) if a.get(k, 0) != b.get(k, 0))
            cells.append('%s T%d Y%d I%d O%d' % (s, cc['TIMER-MODE'], cc['TOYPAD'], cc['IOD'], cc['OTHER']))
        w('      %-14s %s' % (n, ' | '.join(cells)))
w('  (B) OTHER: d11 %d, d11t %d, d11p %d -> %s' % (BCAT['d11']['OTHER'], BCAT['d11t']['OTHER'], BCAT['d11p']['OTHER'], 'PASS' if B_ok else 'FAIL'))
w('')
w('  (C) exact text vs the s0 set: only ts, [tNNNN] and the run-dir name dropped (trailing blanks stripped); no Toypad reduction.')
w('      TOYPAD rows (random challenge payloads) are counted here and listed in the appendix.')
C_ok, CCAT, CRES = True, {}, {}
for arm in TEST:
    res = armdiff('C', arm)
    CRES[arm] = res
    w('    arm %s:' % arm)
    cat = show(res, skip_toy=True)
    CCAT[arm] = cat
    tok = timer_ok(res, arm, True)
    C_ok = C_ok and tok and cat['OTHER'] == 0
    per = {n: Counter(t for k, v in res.items() if cls(k) == 'TOYPAD' for rn, (t, x) in v['runs'].items() if rn == n) for n in RUNS[arm]}
    w('    arm %s: keys TIMER-MODE %d TOYPAD %d IOD %d OTHER %d; TIMER-MODE as expected: %s; TOYPAD per run %s'
      % (arm, cat['TIMER-MODE'], cat['TOYPAD'], cat['IOD'], cat['OTHER'], tok, {n: dict(c) for n, c in per.items()}))
w('    IoDismountVolumeByFileHandle handles per run (all 16):')
for n in ALL:
    w('      %-15s %-9s %s' % (n, R[n]['arm'], dict(sorted(ST[n]['iod'].items())) or '-'))
w('  (C) OTHER: d11 %d, d11t %d, d11p %d -> %s' % (CCAT['d11']['OTHER'], CCAT['d11t']['OTHER'], CCAT['d11p']['OTHER'], 'PASS' if C_ok else 'FAIL'))
w('  info, cross-bin (devoff3 vs devoff4), base / cold-base vs s0: gate FAIL findings base %d, cold-base %d (12 pairs);' % (FAILN['base'], FAILN['cold-base']))
for arm in ('base', 'cold-base'):
    w('    (B) arm %s:' % arm)
    show(armdiff('B', arm))
CK3 = A_ok and B_ok and C_ok
w('CHECK 3: %s ((A) %s, (B) %s, (C) %s)' % ('PASS' if CK3 else 'FAIL', A_ok, B_ok, C_ok))
w('')

# ---------------------------------------------------------------- CHECK 4
CMP = []


def agree(item, ok, detail=''):
    CMP.append((item, ok, detail))


def a6lines(name):
    p = os.path.join(A6, name)
    return rlines(p) if os.path.exists(p) else None


def num_eq(a, b, tol):
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return str(a) == str(b)


N6 = {}
for arm in NONS0:
    res = armdiff('N6', arm)
    refc = [CNT['N6'][n] for n in RUNS['s0']]
    anyt = lambda k, t: any(x == t for x, _ in res[k]['runs'].values())
    more = {k for n in RUNS[arm] for k, v in CNT['N6'][n].items() if v > max(c.get(k, 0) for c in refc) + max(5, max(c.get(k, 0) for c in refc))}
    N6[arm] = dict(res=res, new={k for k in res if anyt(k, 'NEW') and re.match(r'^\[(warning|error|critical)\]', k)},
                   more=more, gone={k for k in res if anyt(k, 'GONE')},
                   only={k for k in res if anyt(k, 'NEW') and cls(k) != 'TOYPAD'})
gone_b_nontoy = {arm: sorted(k for k, v in armdiff('B', arm).items() if cls(k) != 'TOYPAD' and any(t == 'GONE' for t, _ in v['runs'].values())) for arm in NONS0}
gone_b_toy = {arm: sum(1 for k, v in armdiff('B', arm).items() if cls(k) == 'TOYPAD' and any(t == 'GONE' for t, _ in v['runs'].values())) for arm in NONS0}

# claims
agree('claim 1: all 16 exit 0x00000000, clean, wm_close_posted=1, no repost, not killed, no WER, 0 dumps, 0 dialogs, 0 not-responding, not stalled, STUCK 0, exit seq ok',
      CK1, '; '.join(c1_fail))
bad2 = [n for n in ALL if ST[n]['lv'].get('warning', 0) != 40 or ST[n]['lv'].get('error', 0) != 0 or ST[n]['warn_sub'] != 40 or ST[n]['err_sub'] != 0]
agree('claim 2: every game.log has exactly 40 [warning] and 0 [error] lines', not bad2,
      '; '.join('%s warning=%d error=%d' % (n, ST[n]['lv'].get('warning', 0), ST[n]['lv'].get('error', 0)) for n in bad2))
z = {a: (FAILN[a], len(N6[a]['new']), len(N6[a]['more']), len(N6[a]['gone'])) for a in NONS0}
agree('claim 3: FAIL/NEW/MORE/GONE all 0 (gate findings; NEW w/e/c, MORE, GONE on A6-style keys = numbers normalized, Toypad W5/R4 tokens)',
      all(v == (0, 0, 0, 0) for v in z.values()) and not any(gone_b_nontoy.values()),
      'per arm (FAIL,NEW,MORE,GONE) %s; spec-(B) keys: non-Toypad GONE %s, Toypad GONE keys (5-token Read seq shift) %s' % (z, gone_b_nontoy, gone_b_toy))
agree('claim 4: only non-Toypad non-IoDismount difference vs s0 = (i) in d11/d11t/d11p 3/3 each + (iii) in d11p 3/3', B_ok and C_ok,
      '(B) %s (C) %s' % ({a: dict(BCAT[a]) for a in TEST}, {a: dict(CCAT[a]) for a in TEST}))
envruns = [n for n in ALL if 'REX_TIMER_WAIT_BLOCKING' in (R[n]['rj'].get('env_set') or {})]
agree('claim 5: REX_TIMER_WAIT_BLOCKING in d11t env_set 3/3 and nowhere else', envruns == sorted(RUNS['d11t']), 'env_set runs %s' % envruns)
t6 = {n: (ST[n]['toyW'], ST[n]['toyR'], ' '.join(ST[n]['seq']), ST[n]['B1']) for n in ALL}
ok6 = all(t6[n][:2] == (12, 12) and t6[n][2].startswith('C0 B0 B0 C0') and t6[n][3] == 4 for n in RUNS['d11t'][:2]) and \
    t6[RUNS['d11t'][2]][:2] == (8, 8) and t6[RUNS['d11t'][2]][3] == 3
agree('claim 6: d11t-r1/r2 12/12 Toypad (C0 B0 B0 C0), d11t-r3 8/8 (3 B1)', ok6, '; '.join('%s W/R %d/%d seq %s B1=%d' % ((n,) + t6[n]) for n in RUNS['d11t']))
h158 = sorted(n for n in ALL if '0xf8000158' in ST[n]['iod'])
h164 = sorted(n for n in ALL if '0xf8000164' in ST[n]['iod'])
agree('claim 7: IoD 0xf8000158 in 1813-d11t-r2 (and 1757-base-r1); 0xf8000164 in 1800-s0-r1',
      h158 == ['1757-base-r1', '1813-d11t-r2'] and h164 == ['1800-s0-r1'], '0158 in %s; 0164 in %s' % (h158, h164))

# summary.txt and report-*.txt
RUNLINE = re.compile(r'^\s+runs\\(?P<run>\S+): exit=(?P<exit>\S+) close=(?P<close>\S+) early=(?P<early>\S+) wer=(?P<wer>\S+) dumps=(?P<dumps>\d+) '
                     r'exit_line=(?P<el>\d+) stuck=(?P<stuck>\d+) \| (?P<lines>\d+) lines game\.log (?P<bytes>\d+), (?P<t0>[\d\- :.]+?)\.\.'
                     r'(?P<t1>[\d\- :.]+?) \((?P<dur>\d+) s\) \| levels (?P<lv>.+?) \| Toypad R/W (?P<tr>\d+)/(?P<tw>\d+)')


def cmp_runline(src, m):
    n = m.group('run')
    if n not in R:
        return agree('%s run line %s' % (src, n), False, 'unknown run')
    S, d = ST[n], []
    for name, th, mi in (('exit', m.group('exit'), R[n]['rj'].get('exit_code')), ('early', m.group('early'), R[n]['rj'].get('exited_early')),
                         ('dumps', m.group('dumps'), len(C1[n]['dmp'])), ('exit_line', m.group('el'), S['exit_line']),
                         ('stuck', m.group('stuck'), len(C1[n]['stuck'])), ('lines', m.group('lines'), S['lines']),
                         ('bytes', m.group('bytes'), R[n]['bytes']), ('t0', m.group('t0'), S['t0']), ('t1', m.group('t1'), S['t1']),
                         ('levels', sorted((a, int(b)) for a, b in re.findall(r'(\w+)=(\d+)', m.group('lv'))), sorted(S['lv'].items())),
                         ('toyR', m.group('tr'), S['toyR']), ('toyW', m.group('tw'), S['toyW'])):
        if str(th) != str(mi):
            d.append('%s theirs=%s mine=%s' % (name, th, mi))
    if abs(int(m.group('dur')) - S['dur']) > 1:
        d.append('dur theirs=%s mine=%s' % (m.group('dur'), S['dur']))
    agree('%s run line %s (exit, dumps, exit_line, stuck, lines, bytes, t0/t1, levels, Toypad R/W)' % (src, n), not d, '; '.join(d))


L = a6lines('summary.txt')
agree('summary.txt present', L is not None)
for ln in L or []:
    m = RUNLINE.match(ln)
    if m:
        cmp_runline('summary.txt', m)
    m = re.match(r'^(\S+): runs (\d+); FAIL findings (\d+); NEW (\d+); MORE (\d+); GONE (\d+); ONLY (\d+); dumps (\d+); exit lines \[([^\]]*)\]; exits \[([^\]]*)\]', ln)
    if m and m.group(1) in N6:
        a = m.group(1)
        th = (int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7)), int(m.group(8)), m.group(9), m.group(10))
        mi = (len(RUNS[a]), FAILN[a], len(N6[a]['new']), len(N6[a]['more']), len(N6[a]['gone']), len(N6[a]['only']),
              sum(len(C1[n]['dmp']) for n in RUNS[a]), ', '.join(str(ST[n]['exit_line']) for n in RUNS[a]),
              ', '.join(str(R[n]['rj'].get('exit_code')) for n in RUNS[a]))
        agree('summary.txt arm %s: runs/FAIL/NEW/MORE/GONE/ONLY/dumps/exit lines/exits' % a, th == mi, 'theirs %s mine %s' % (th, mi))
for arm in TEST:
    L = a6lines('report-%s.txt' % arm)
    agree('report-%s.txt present' % arm, L is not None)
    their_only = {}
    for ln in L or []:
        m = RUNLINE.match(ln)
        if m:
            cmp_runline('report-%s' % arm, m)
            continue
        m = re.match(r'^gate_logdiff FAIL findings .*: (\S+)$', ln)
        if m:
            th = 0 if m.group(1) == 'none' else int(m.group(1))
            agree('report-%s gate FAIL findings' % arm, th == FAILN[arm], 'theirs %s mine %d' % (m.group(1), FAILN[arm]))
        m = re.match(r'^(NEW|MORE|GONE) .*: (\d+)$', ln)
        if m:
            mi = len(N6[arm][m.group(1).lower()])
            agree('report-%s %s' % (arm, m.group(1)), int(m.group(2)) == mi, 'theirs %s mine %d' % (m.group(2), mi))
        m = re.match(r"^\s+runs\\(\S+): (\{.*?\}); non-info Toypad (.+?); prefixes not in base (.+?); other Toypad lines not in base (.+)$", ln)
        if m and m.group(1) in R:
            n = m.group(1)
            s0u = set().union(*[set(CNT['A6'][s]) for s in RUNS['s0']])
            pre = sorted(k for k in CNT['A6'][n] if 'Toypad[' in k and k not in s0u)
            oth = sorted(k for k in CNT['A6'][n] if 'toypad' in k.lower() and 'Toypad[' not in k and k not in s0u)
            noninfo = {k: v for k, v in ST[n]['toy'].items() if not k.startswith('info ')}
            th = (ast.literal_eval(m.group(2)), m.group(3), m.group(4), m.group(5))
            mi = (dict(ST[n]['toy']), str(noninfo) if noninfo else '-', str(pre) if pre else '-', str(oth) if oth else '-')
            agree('report-%s Toypad %s' % (arm, n), th == mi, 'theirs %s mine %s' % (th, mi))
        m = re.match(r'^ONLY in (\S+) .*: (\d+) keys', ln)
        if m:
            agree('report-%s ONLY key count' % arm, int(m.group(2)) == len(N6[arm]['only']), 'theirs %s mine %d' % (m.group(2), len(N6[arm]['only'])))
        m = re.match(r'^\s+(\d+)/(\d+) runs, counts \[([^\]]*)\], also in (.+?)  (\[.*)$', ln)
        if m:
            k = m.group(5).strip()
            their_only[k] = (int(m.group(1)), int(m.group(2)), m.group(3), [] if m.group(4) == '-' else ast.literal_eval(m.group(4)))
    for k in sorted(set(their_only) | N6[arm]['only']):
        mi = (sum(1 for n in RUNS[arm] if CNT['N6'][n].get(k)), len(RUNS[arm]), ', '.join(str(CNT['N6'][n].get(k, 0)) for n in RUNS[arm]),
              sorted(a for a in NONS0 if a != arm and any(CNT['N6'][n].get(k) for n in RUNS[a]))) if k in N6[arm]['only'] else None
        agree('report-%s ONLY key %s' % (arm, k), their_only.get(k) == mi, 'theirs %s mine %s' % (their_only.get(k), mi))

# extra-vs-s0.txt sections 1, 2, 5, 6
EX = a6lines('extra-vs-s0.txt') or []
agree('extra-vs-s0.txt present', bool(EX))
sec, cur = {}, None
for ln in EX:
    m = re.match(r'^(\d)\. ', ln)
    if m:
        cur = int(m.group(1))
    sec.setdefault(cur, []).append(ln)


def s1_mine(n):
    rj, c = R[n]['rj'], R[n]['rj'].get('close') or {}
    cv = (rj.get('params') or {}).get('cvar') or []
    env = rj.get('env_set') or {}
    return dict(exit_seq='ok' if ST[n]['last3'] == EXIT_SEQ else 'bad', status=rj.get('status'), problems=len(rj.get('problems') or []),
                exit=rj.get('exit_code_hex'), early=rj.get('exited_early'), wm_close=c.get('wm_close_posted'), repost=c.get('wm_close_repost_s'),
                exit_wait_s=c.get('exit_wait_s'), killed=c.get('killed'), clean=c.get('clean'), wer=rj.get('werfault_seen'),
                foreign_dumps=len(rj.get('foreign_crash_dumps') or []), dialogs=len(rj.get('dialogs') or []),
                not_resp=rj.get('not_responding_samples'), perf_stalled=rj.get('perf_csv_stalled'), artifacts=len(rj.get('artifacts') or []),
                log_lines=rj.get('log_lines'), runner_error=rj.get('runner_error'), excluded=rj.get('excluded'), dmp=len(C1[n]['dmp']),
                bin=os.path.basename((rj.get('bin_dir') or '').rstrip('\\/')), env=','.join('%s=%s' % kv for kv in env.items()) or '-',
                cvarp=[x for x in cv if x not in B_CV], cvarm=[x for x in B_CV if x not in cv], flags_info=rj.get('flags_info'),
                flags_excl=rj.get('flags_excluding'), sys_flags=(rj.get('sys') or {}).get('flags'), STUCK=len(C1[n]['stuck']), WM_CLOSE=C1[n]['wmc'])


last = None
for ln in sec.get(1, []):
    m = re.match(r'^\s+(\S+)\s+(\d{4}-\S+)\s+(exit_seq=.*)$', ln)
    if m and m.group(2) in R:
        last = m.group(2)
        mi, kv, d = s1_mine(last), dict(re.findall(r'(\w+)=(\S+)', m.group(3))), []
        if m.group(1) != R[last]['arm']:
            d.append('arm theirs=%s mine=%s' % (m.group(1), R[last]['arm']))
        for k, th in kv.items():
            if k not in mi:
                d.append('%s: no own value' % k)
            elif not num_eq(th, mi[k], 1e-9):
                d.append('%s theirs=%s mine=%s' % (k, th, mi[k]))
        agree('extra s1 %s' % last, not d, '; '.join(d))
        continue
    m = re.match(r'^\s+bin=(\S+) env=(\S+) cvar\+(\[.*?\]) cvar-(\[.*?\]) flags_info=(\[.*?\]) flags_excl=(\[.*?\]) sys_flags=(\[.*?\]) STUCK=(\d+) WM_CLOSE=(\d+)', ln)
    if m and last:
        mi = s1_mine(last)
        th = (m.group(1), m.group(2)) + tuple(ast.literal_eval(m.group(i)) for i in range(3, 8)) + (int(m.group(8)), int(m.group(9)))
        mv = (mi['bin'], mi['env'], mi['cvarp'], mi['cvarm'], mi['flags_info'], mi['flags_excl'], mi['sys_flags'], mi['STUCK'], mi['WM_CLOSE'])
        agree('extra s1 %s bin/env/cvar/flags/STUCK/WM_CLOSE' % last, th == mv, 'theirs %s mine %s' % (th, mv))
        last = None
        continue
    m = re.match(r'^\s+(\d{4}-\S+) summary\.txt: (close.*)$', ln)
    if m and m.group(1) in R:
        th, mi = ' '.join(m.group(2).split()), ' '.join(' '.join(C1[m.group(1)]['sumclose']).split())
        agree('extra s1 %s summary.txt close line' % m.group(1), th == mi, 'theirs %s mine %s' % (th, mi))
    m = re.match(r'^\s+matrix top-level text files: STUCK=(\d+) WM_CLOSE=(\d+)', ln)
    if m:
        agree('extra s1 matrix top-level STUCK/WM_CLOSE', (int(m.group(1)), int(m.group(2))) == (len(tstuck), twm),
              'theirs %s mine %s' % (m.groups(), (len(tstuck), twm)))

# section 2 (exact keys, Agent-6-style Toypad reduction: Write 5 tokens, Read 4 tokens)
s0c = [CNT['A6'][n] for n in RUNS['s0']]
uni, inall = set().union(*[set(c) for c in s0c]), set.intersection(*[set(c) for c in s0c])
s0var = {k: (min(c.get(k, 0) for c in s0c), max(c.get(k, 0) for c in s0c)) for k in uni if len({c.get(k, 0) for c in s0c}) > 1}
th_var, th_arm, th_items, carm = {}, {}, {}, None
for ln in sec.get(2, []):
    m = re.match(r'^\s+s0 keys: union (\d+), in all 3 runs (\d+)', ln)
    if m:
        agree('extra s2 s0 key union / in-all-3', (int(m.group(1)), int(m.group(2))) == (len(uni), len(inall)), 'theirs %s mine %s' % (m.groups(), (len(uni), len(inall))))
    m = re.match(r'^\s+s0 (\d+)\.\.(\d+)\s+(\[.*)$', ln)
    if m:
        th_var[m.group(3).strip()] = (int(m.group(1)), int(m.group(2)))
    m = re.match(r'^\s+arm (\S+) \((\d+) runs\): ONLY-exact (\d+), GONE-exact (\d+), count outside s0 min\.\.max (\d+)', ln)
    if m:
        carm = m.group(1)
        th_arm[carm] = tuple(int(m.group(i)) for i in (3, 4, 5))
        th_items[carm] = {}
    m = re.match(r'^\s+ONLY (\d+)/(\d+)\s+(.*)$', ln)
    if m and carm:
        k, rc = m.group(3).rsplit('   [', 1)
        th_items[carm][('NEW', k.strip())] = ('%s/%s' % (m.group(1), m.group(2)), rc.rstrip(']'))
    m = re.match(r'^\s+COUNT s0 (\d+)\.\.(\d+), (.*?)  (\[.*)$', ln)
    if m and carm:
        th_items[carm][('COUNT', m.group(4).strip())] = ('%s..%s' % (m.group(1), m.group(2)), m.group(3))
    m = re.match(r'^\s+GONE (.*)$', ln)
    if m and carm:
        th_items[carm][('GONE', m.group(1).strip())] = ('?', '?')
agree('extra s2 s0-internal variable keys', th_var == s0var, 'theirs %s mine %s' % (th_var, s0var))
for arm in NONS0:
    res = armdiff('A6', arm)
    mine = {}
    for k, v in res.items():
        types = {t for t, _ in v['runs'].values()}
        if 'NEW' in types:
            mine[('NEW', k)] = ('%d/%d' % (sum(1 for t, _ in v['runs'].values() if t == 'NEW'), len(RUNS[arm])),
                                ', '.join('%s=%d' % (n, x) for n, (t, x) in sorted(v['runs'].items()) if t == 'NEW'))
        if 'GONE' in types:
            mine[('GONE', k)] = ('?', '?')
        if 'COUNT' in types:
            mine[('COUNT', k)] = ('%d..%d' % (min(v['rc']), max(v['rc'])), ', '.join('%s=%d' % (n, x) for n, (t, x) in sorted(v['runs'].items()) if t == 'COUNT'))
    cnts = (sum(1 for t, _ in mine if t == 'NEW'), sum(1 for t, _ in mine if t == 'GONE'), sum(1 for t, _ in mine if t == 'COUNT'))
    agree('extra s2 arm %s ONLY/GONE/COUNT totals' % arm, th_arm.get(arm) == cnts, 'theirs %s mine %s' % (th_arm.get(arm), cnts))
    agree('extra s2 arm %s items (key, presence/range, run counts)' % arm, th_items.get(arm) == mine,
          'only theirs %s; only mine %s' % ({k: v for k, v in (th_items.get(arm) or {}).items() if mine.get(k) != v},
                                            {k: v for k, v in mine.items() if (th_items.get(arm) or {}).get(k) != v}))

# section 5
TOL = {'close': 0.051, 'cores': 0.0051}
seen5 = set()
for ln in sec.get(5, []):
    m = re.match(r'^\s+(\d{4}-\S+)\s+(\S+)\s+(devoff\d-bin)\s+(\d\d:\d\d:\d\d) (.*)$', ln)
    if m and m.group(1) in R:
        n = m.group(1)
        seen5.add(n)
        rj, S = R[n]['rj'], ST[n]
        fr, sw = rj.get('frames') or {}, ((rj.get('sys') or {}).get('window') or {})
        mi = dict(lines=S['lines'], B=R[n]['bytes'], info=S['lv'].get('info', 0), warn=S['lv'].get('warning', 0), err=S['lv'].get('error', 0),
                  other=sum(v for k, v in S['lv'].items() if k not in ('info', 'warning', 'error', 'raw')), toyW=S['toyW'], toyR=S['toyR'],
                  B1=S['B1'], close=S['close'], exit_wait=(rj.get('close') or {}).get('exit_wait_s'), med=fr.get('median_ms'),
                  p99=fr.get('p99_ms'), max=fr.get('max_ms'), mhz=sw.get('eff_mhz_mean'), P=sw.get('p_eff_mhz_mean'), E=sw.get('e_eff_mhz_mean'),
                  util=sw.get('cpu_util_mean'), Putil=sw.get('p_util_mean'), cores=rj.get('window_cpu_cores_mean'),
                  bprocs='%d/%d' % (len(rj.get('build_procs_window') or []), len(rj.get('build_procs_warmup') or [])),
                  boot=rj.get('first_frame_signal_s'), free=rj.get('free_ram_gb_at_start'), input=sw.get('input_events'),
                  fg=sw.get('fg_game_share'), nogrowth=rj.get('perf_csv_max_no_growth_window_s'), **S['c'])
        d = []
        for k, th in re.findall(r'(\w+)=(\S+)', m.group(5)):
            if k not in mi:
                d.append('%s: no own value' % k)
            elif not num_eq(th, mi[k], TOL.get(k, 1e-6)):
                d.append('%s theirs=%s mine=%s' % (k, th, mi[k]))
        for k, th, mv in (('arm', m.group(2), R[n]['arm']), ('bin', m.group(3), os.path.basename(rj.get('bin_dir', '').rstrip('\\/'))),
                          ('start', m.group(4), (rj.get('start') or '')[11:19])):
            if th != mv:
                d.append('%s theirs=%s mine=%s' % (k, th, mv))
        agree('extra s5 %s (lines, B, levels, Toypad, B1, close, c1..c8, run.json fields)' % n, not d, '; '.join(d))
    m = re.match(r'^\s+(c\d) per arm: (.*)$', ln)
    if m:
        th = {a: ast.literal_eval(v) for a, v in (x.split('=', 1) for x in m.group(2).split('; '))}
        mi = {a: [ST[n]['c'][m.group(1)] for n in RUNS[a]] for a in th}
        agree('extra s5 %s per arm' % m.group(1), th == mi and set(th) == set(ARMS), 'theirs %s mine %s' % (th, mi))
    m = re.match(r'^\s+env_set per arm: (.*)$', ln)
    if m:
        th = {a: ast.literal_eval(v) for a, v in (x.split('=', 1) for x in m.group(1).split('; '))}
        mi = {a: [','.join(R[n]['rj'].get('env_set') or {}) or '-' for n in RUNS[a]] for a in th}
        agree('extra s5 env_set per arm', th == mi and set(th) == set(ARMS), 'theirs %s mine %s' % (th, mi))
agree('extra s5 covers all 16 runs', seen5 == set(ALL), 'missing %s' % sorted(set(ALL) - seen5))

# section 6
allk = set().union(*[set(CNT['A6'][n]) for n in ALL])
notall = [k for k in allk if not all(CNT['A6'][n].get(k) for n in ALL)]
pres = {k: {a: '%d/%d' % (sum(1 for n in RUNS[a] if CNT['A6'][n].get(k)), len(RUNS[a])) for a in ARMS} for k in notall}
sig = {k for k in notall if all(sum(1 for n in RUNS[a] if CNT['A6'][n].get(k)) in (0, len(RUNS[a])) for a in ARMS)}
th6, thsig, thvar, grp = {}, None, None, None
for ln in sec.get(6, []):
    m = re.match(r'^\s+SIG .*: (\d+)', ln)
    if m:
        thsig, grp = int(m.group(1)), 'SIG'
    m = re.match(r'^\s+VAR .*: (\d+)', ln)
    if m:
        thvar, grp = int(m.group(1)), 'VAR'
    m = re.match(r'^\s+((?:[\w-]+=\d+/\d+ )+)\s*(\[.*)$', ln)
    if m:
        th6[m.group(2).strip()] = (grp, dict(x.split('=') for x in m.group(1).split()))
mine6 = {k: ('SIG' if k in sig else 'VAR', pres[k]) for k in notall}
agree('extra s6 SIG/VAR counts', (thsig, thvar) == (len(sig), len(notall) - len(sig)), 'theirs %s mine %s' % ((thsig, thvar), (len(sig), len(notall) - len(sig))))
agree('extra s6 per-key presence', th6 == mine6, 'only theirs %s; only mine %s' % ({k: v for k, v in th6.items() if mine6.get(k) != v},
                                                                                    {k: v for k, v in mine6.items() if th6.get(k) != v}))

w('== CHECK 4: comparison with Agent 6 (claims; summary.txt; report-d11/d11t/d11p.txt; extra-vs-s0.txt sections 1, 2, 5, 6) ==')
for item, ok, detail in CMP:
    w('  %s  %s%s' % ('AGREE   ' if ok else 'DISAGREE', item, ('  | ' + detail) if (detail and (not ok or item.startswith('claim'))) else ''))
ndis = sum(1 for _, ok, _ in CMP if not ok)
CK4 = ndis == 0
w('CHECK 4: %s (%d items, %d AGREE, %d DISAGREE)' % ('PASS' if CK4 else 'FAIL', len(CMP), len(CMP) - ndis, ndis))
w('')
w('== VERDICT ==')
w('CHECK 1 %s | CHECK 2 %s | CHECK 3 %s | CHECK 4 %s' % tuple('PASS' if x else 'FAIL' for x in (CK1, CK2, CK3, CK4)))
w('')
w('== APPENDIX: (C) exact-text TOYPAD rows (random challenge payloads; full keys) ==')
for arm in TEST:
    for k in sorted(k for k in CRES[arm] if cls(k) == 'TOYPAD'):
        v = CRES[arm][k]
        w('  %-5s s0 %-9s %s   %s' % (arm, v['rc'], ' '.join('%s=%s:%d' % (n, t, x) for n, (t, x) in sorted(v['runs'].items())), k))
w('== APPENDIX: Toypad write sequence per run ==')
for n in ALL:
    w('  %-15s %-9s W/R %d/%d B1=%d seq %s' % (n, R[n]['arm'], ST[n]['toyW'], ST[n]['toyR'], ST[n]['B1'], ' '.join(ST[n]['seq'])))

with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('\n'.join(out) + '\n')
print('\n'.join(x for x in out if x.startswith(('CHECK ', 'run dirs', '  DISAGREE'))))
print('wrote %s (%d lines)' % (OUT, len(out)))
