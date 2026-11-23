"""Agent 6 task #5 checker (read-only): W4b d11t vs d0 game.log exact-text diff (own normaliser, not w4b_logdiff.py),
crash evidence from run.json, host-timer line presence, Toypad cadence. Steps 2-5 of the checker brief.
Stdlib only, single-threaded; run with python -B. Writes check_d11t.out.txt and check_d11t.json beside itself.

  python -B build/agent6/w4b/check-d11t/check_d11t.py
"""
import glob
import json
import os
import re
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
RUNS = os.path.join(ROOT, 'build', 'agent8', 'matrix', '20261122-1541', 'runs')
ARMS = OrderedDict([
    ('d0', ['1542-d0-r1', '1558-d0-r2', '1604-d0-r3', '1611-d0-r4']),
    ('d11t', ['1549-d11t-r1', '1556-d11t-r2', '1602-d11t-r3', '1608-d11t-r4']),
    ('B', ['1545-B-r1', '1551-B-r2', '1606-B-r3', '1613-B-r4']),
    ('d3', ['1547-d3-r1', '1553-d3-r2', '1600-d3-r3', '1615-d3-r4']),
    ('cold-d0', ['1541-cold-d0']),
])
ALL_RUNS = [r for runs in ARMS.values() for r in runs]
D0, D11 = ARMS['d0'], ARMS['d11t']

TS_RE = re.compile(r'^\[(\d{4}-\d\d-\d\d) (\d\d):(\d\d):(\d\d(?:\.\d+)?)\] (.*)$')
BODY_RE = re.compile(r'^\[(?P<lvl>[a-z]+)\] \[(?P<cat>[^\]]*)\] (?:\[t\d+\] )?(?P<msg>.*)$')
RUNDIR_RE = re.compile(r'(runs[\\/])\d{4}-[^\\/\s\'"]+')
TOYPAY_RE = re.compile(r'^Toypad\[(Write|Read )\] (.*)$')
HEX2 = re.compile(r'^[0-9A-Fa-f]{2}$')
TOY_ALLOWED = ('Toypad: detected frame offset', 'Toypad: pad 0 mode', 'Toypad listener active',
               'Toypad: emulated LEGO Dimensions ToyPad active', 'Portal: using the emulated ToyPad.')
HOST_TIMER = 'Host timer resolution set to 1 ms (background opt-out on)'
CLEAN_TAIL = ['Window closing, shutting down...', 'Execution complete', 'Title terminated; hard-exiting process.']
GREPS = [('STUCK', re.compile(r'STUCK', re.I)), ('REX_FATAL', re.compile(r'REX_FATAL', re.I)),
         ('unimplemented', re.compile(r'unimplemented', re.I)), ('[critical]', re.compile(r'\[critical\]', re.I)),
         ('[error]', re.compile(r'\[error\]', re.I))]
WARN = ('warning', 'error', 'critical')
WANT = ['status', 'problems', 'exit_code_hex', 'exit_code', 'exited_early', 'close.killed', 'close.exit_wait_s',
        'close.wm_close_repost_s', 'werfault_seen', 'foreign_crash_dumps', 'dialogs', 'not_responding_samples',
        'perf_csv_stalled']

OUT = []


def w(s=''):
    OUT.append(s)


def walk(o, path=''):
    if isinstance(o, dict):
        for k, v in o.items():
            p = '%s.%s' % (path, k) if path else k
            yield p, v
            for x in walk(v, p):
                yield x
    elif isinstance(o, list):
        for i, v in enumerate(o):
            p = '%s[%d]' % (path, i)
            yield p, v
            for x in walk(v, p):
                yield x


def parse_run(run):
    d = os.path.join(RUNS, run)
    r = dict(run=run, logs=sorted(f for f in os.listdir(d) if re.match(r'^game(\.\d+)?\.log$', f, re.I)),
             keys=Counter(), toy=[], odd_toy=[], bad_payload=[], greps=Counter(), grep_lines=[], host_timer=0,
             host_timer_any=[], t_first=None, t_last=None, t_close=None, tail=[], lines=0)
    with open(os.path.join(d, 'game.log'), 'r', encoding='utf-8-sig', errors='replace', newline=None) as fh:
        lines = [x.rstrip('\n') for x in fh]
    msgs = []
    for line in lines:
        if not line.strip():
            continue
        r['lines'] += 1
        m = TS_RE.match(line)
        t = None
        if m:
            t = int(m.group(2)) * 3600 + int(m.group(3)) * 60 + float(m.group(4))
            if r['t_first'] is None:
                r['t_first'] = t
            r['t_last'] = t
            b = BODY_RE.match(m.group(5))
            if b:
                lvl, cat, msg = b.group('lvl'), b.group('cat'), b.group('msg')
            else:
                lvl, cat, msg = '?', '?', m.group(5)
        else:
            lvl, cat, msg = 'untimestamped', '', line
        msgs.append(msg)
        msg_n = RUNDIR_RE.sub(r'\1<RUN>', msg)
        tp = TOYPAY_RE.match(msg_n)
        if tp:
            direc = tp.group(1)
            toks = tp.group(2).split()
            if not toks or not all(HEX2.match(x) for x in toks):
                r['bad_payload'].append(line)
            nh = 5 if direc == 'Write' else 4
            key = '[%s] [%s] Toypad[%s] %s ...' % (lvl, cat, direc, ' '.join(toks[:nh]))
            r['toy'].append(dict(t=t, dir=direc.strip(), toks=[x.upper() for x in toks]))
        elif lvl == 'untimestamped':
            key = '[untimestamped] %s' % msg_n
        else:
            key = '[%s] [%s] %s' % (lvl, cat, msg_n)
        r['keys'][key] += 1
        if (('toypad' in msg.lower()) or msg.startswith('Portal')) and not tp:
            if not any(msg.startswith(a) for a in TOY_ALLOWED):
                r['odd_toy'].append(line)
        if msg == 'Window closing, shutting down...' and r['t_close'] is None:
            r['t_close'] = t
        if HOST_TIMER in line:
            r['host_timer'] += 1
        if 'host timer' in line.lower():
            r['host_timer_any'].append(msg)
        for name, rx in GREPS:
            if rx.search(line):
                r['greps'][name] += 1
                r['grep_lines'].append(line[:200])
    r['tail'] = msgs[-3:]
    r['clean_tail'] = (msgs[-3:] == CLEAN_TAIL)
    # run.json
    rj_path = os.path.join(d, 'run.json')
    r['runjson'] = OrderedDict()
    r['runjson_top'] = []
    if os.path.exists(rj_path):
        with open(rj_path, 'r', encoding='utf-8-sig') as fh:
            rj = json.load(fh)
        r['runjson_top'] = list(rj.keys()) if isinstance(rj, dict) else []
        paths = list(walk(rj))
        for want in WANT:
            hits = [(p, v) for p, v in paths if (p == want or p.endswith('.' + want))]
            r['runjson'][want] = hits
        r['runjson_close'] = rj.get('close') if isinstance(rj, dict) else None
        r['_rj'] = rj
    dumps = []
    for dp, dn, fn in os.walk(d):
        for f in fn:
            if f.lower().endswith('.dmp') or f.lower().endswith('.mdmp'):
                dumps.append(os.path.join(dp, f))
    r['dumps'] = dumps
    # toypad cadence
    writes = [e for e in r['toy'] if e['dir'] == 'Write']
    reads = [e for e in r['toy'] if e['dir'] == 'Read']
    r['n_write'], r['n_read'] = len(writes), len(reads)
    r['write_cmds'] = [e['toks'][4] if len(e['toks']) > 4 else '?' for e in writes]
    r['write_seq'] = [e['toks'][5] if len(e['toks']) > 5 else '?' for e in writes]
    r['read_seq'] = [e['toks'][4] if len(e['toks']) > 4 else '?' for e in reads]
    r['write_hdrs'] = sorted(set(' '.join(e['toks'][:5]) for e in writes))
    r['read_hdrs'] = sorted(set(' '.join(e['toks'][:4]) for e in reads))
    t0 = writes[0]['t'] if writes else None
    r['t0_write'] = t0
    r['b1_rel'] = [round(e['t'] - t0, 3) for e in writes if len(e['toks']) > 4 and e['toks'][4] == 'B1']
    r['b3_rel'] = [round(e['t'] - t0, 3) for e in writes if len(e['toks']) > 4 and e['toks'][4] == 'B3']
    r['close_rel'] = round(r['t_close'] - t0, 3) if (t0 is not None and r['t_close'] is not None) else None
    r['boot_to_first_write'] = round(t0 - r['t_first'], 3) if t0 is not None else None
    r['first_to_close'] = round(r['t_close'] - r['t_first'], 3) if r['t_close'] is not None else None
    r['last_b1_to_close'] = round(r['close_rel'] - r['b1_rel'][-1], 3) if (r['b1_rel'] and r['close_rel'] is not None) else None
    r['b1_gaps'] = [round(b - a, 3) for a, b in zip(r['b1_rel'], r['b1_rel'][1:])]
    ws, rs = set(r['write_seq']), set(r['read_seq'])
    r['unpaired'] = dict(write_no_read=sorted(ws - rs), read_no_write=sorted(rs - ws))
    order_bad = []
    for e in writes:
        sq = e['toks'][5] if len(e['toks']) > 5 else None
        rep = [x for x in reads if len(x['toks']) > 4 and x['toks'][4] == sq]
        if rep and rep[0]['t'] < e['t']:
            order_bad.append(sq)
    r['reply_before_write'] = order_bad
    cmds = r['write_cmds']
    r['pattern_ok'] = (cmds[:2] == ['B0', 'C0'] and len(cmds) % 2 == 0 and
                       all(cmds[i] == 'B1' and cmds[i + 1] == 'B3' for i in range(2, len(cmds), 2)))
    return r


def arm_of(run):
    for a, rs in ARMS.items():
        if run in rs:
            return a
    return '?'


def main():
    P = OrderedDict((run, parse_run(run)) for run in ALL_RUNS)
    res = OrderedDict()

    # ---------------- step 1 recap (gate JSONs written by the guarded loop)
    gate = {}
    for p in sorted(glob.glob(os.path.join(HERE, '*__vs__*.json'))):
        b, a = os.path.basename(p)[:-5].split('__vs__')
        with open(p, 'r', encoding='utf-8') as fh:
            j = json.load(fh)
        gate[(b, a)] = j
    w('=== STEP 1: gate_logdiff JSONs: %d pairs' % len(gate))
    for b in D11:
        cells = []
        for a in D0:
            j = gate.get((b, a))
            if j is None:
                cells.append('%s:MISSING' % a)
                continue
            dd = j['diff']
            cells.append('%s:%s f%d n%d new%d gone%d chg%d' % (a.split('-')[0], j['verdict'], len(j['findings']),
                                                            len(j['notes']), dd['new_in_b_total'],
                                                            dd['gone_in_b_total'], dd['count_changes_total']))
        w('  %-13s %s' % (b, ' | '.join(cells)))
    res['gate'] = {'%s__vs__%s' % k: dict(verdict=v['verdict'], findings=v['findings'], notes=v['notes'],
                                          new=v['diff']['new_in_b_total'], gone=v['diff']['gone_in_b_total'],
                                          chg=v['diff']['count_changes_total']) for k, v in gate.items()}

    # ---------------- step 2: exact-text diff
    w('')
    w('=== STEP 2: exact-text key diff (timestamp + [tNNN] stripped, run dir -> <RUN>, Toypad payload -> header)')
    allkeys = set()
    for run in ALL_RUNS:
        allkeys |= set(P[run]['keys'])

    def pres(key, runs):
        return [r for r in runs if P[r]['keys'][key] > 0]

    a_list, b_list, c_list, gone_any = [], [], [], []
    for key in sorted(allkeys):
        in11 = pres(key, D11)
        in0 = pres(key, D0)
        if in11 and not in0:
            a_list.append(dict(key=key, d11t=len(in11), d11t_runs=in11, counts=[P[r]['keys'][key] for r in D11],
                               B=len(pres(key, ARMS['B'])), d3=len(pres(key, ARMS['d3'])),
                               cold=len(pres(key, ARMS['cold-d0']))))
        if len(in0) == 4 and len(in11) < 4:
            b_list.append(dict(key=key, missing_in=[r for r in D11 if r not in in11]))
        if in0 and not in11:
            gone_any.append(dict(key=key, d0=len(in0)))
        lvl = key[1:key.index(']')] if key.startswith('[') else ''
        if lvl in WARN:
            c0 = [P[r]['keys'][key] for r in D0]
            lo, hi = min(c0), max(c0)
            for r in D11:
                c = P[r]['keys'][key]
                if c < lo or c > hi:
                    c_list.append(dict(key=key, run=r, count=c, d0_min=lo, d0_max=hi))
    w('(a) keys in some d11t run and in no warm d0 run: %d' % len(a_list))
    for x in a_list:
        w('    d11t %d/4 counts %s | B %d/4 d3 %d/4 cold-d0 %d/1 | %s' % (x['d11t'], x['counts'], x['B'], x['d3'],
                                                                   x['cold'], x['key']))
    w('(b) keys in all 4 warm d0 runs but missing from some d11t run: %d' % len(b_list))
    for x in b_list:
        w('    missing in %s | %s' % (x['missing_in'], x['key']))
    w('(b+) keys in some d0 run but in no d11t run (context): %d' % len(gone_any))
    for x in gone_any:
        w('    d0 %d/4 | %s' % (x['d0'], x['key']))
    w('(c) warning/error/critical keys with a d11t per-run count outside d0 min..max: %d' % len(c_list))
    for x in c_list:
        w('    %s count %d vs d0 %d..%d | %s' % (x['run'], x['count'], x['d0_min'], x['d0_max'], x['key']))
    # all-level out-of-range (context: explains info deltas)
    w('(c+) ANY-level keys with a d11t per-run count outside d0 min..max (context):')
    for key in sorted(allkeys):
        c0 = [P[r]['keys'][key] for r in D0]
        lo, hi = min(c0), max(c0)
        outs = ['%s=%d' % (r.split('-')[0], P[r]['keys'][key]) for r in D11 if not lo <= P[r]['keys'][key] <= hi]
        if outs:
            w('    d0 %d..%d  d11t out: %s | %s' % (lo, hi, ', '.join(outs), key))
    # warn-level totals per run
    w('warn/error/critical totals per run (lines, kinds):')
    for run in D0 + D11:
        wk = {k: c for k, c in P[run]['keys'].items() if k.startswith(('[warning]', '[error]', '[critical]'))}
        w('    %-13s lines %d kinds %d | total log lines %d' % (run, sum(wk.values()), len(wk), P[run]['lines']))
    # key x run matrix for d0 + d11t
    w('key x run count matrix (d0 r1..r4 | d11t r1..r4 | B r1..r4 | d3 r1..r4 | cold):')
    for key in sorted(allkeys):
        row = lambda rs: ' '.join('%2d' % P[r]['keys'][key] for r in rs)
        w('    %s | %s | %s | %s | %s  %s' % (row(D0), row(D11), row(ARMS['B']), row(ARMS['d3']),
                                            row(ARMS['cold-d0']), key[:150]))
    res['step2'] = dict(a=a_list, b=b_list, b_plus=gone_any, c=c_list)

    # ---------------- step 3: crash evidence
    w('')
    w('=== STEP 3: crash evidence per d11t run (run.json fields, dumps, tail, greps)')
    s3 = OrderedDict()
    for run in D11:
        r = P[run]
        w('  --- %s' % run)
        for want, hits in r['runjson'].items():
            if not hits:
                w('    %-24s NOT FOUND' % want)
            for p, v in hits:
                w('    %-24s %s = %s' % (want, p, json.dumps(v)[:300]))
        w('    close dict: %s' % json.dumps(r.get('runjson_close'))[:600])
        w('    dumps (*.dmp/*.mdmp, recursive): %s' % (r['dumps'] or 'none'))
        w('    logs: %s' % r['logs'])
        w('    tail: %s clean=%s' % (r['tail'], r['clean_tail']))
        w('    greps: %s' % (dict(r['greps']) or 'none'))
        for gl in r['grep_lines']:
            w('      %s' % gl)
        s3[run] = dict(runjson={k: v for k, v in r['runjson'].items()}, dumps=r['dumps'], tail=r['tail'],
                       clean_tail=r['clean_tail'], greps=dict(r['greps']), grep_lines=r['grep_lines'])
    w('  tails/greps/dumps of the other runs (context):')
    for run in ALL_RUNS:
        if run in D11:
            continue
        r = P[run]
        w('    %-13s clean_tail=%s greps=%s dumps=%d' % (run, r['clean_tail'], dict(r['greps']) or 'none',
                                                       len(r['dumps'])))
    res['step3'] = s3
    rj0 = P[D11[0]].get('_rj')
    if isinstance(rj0, dict):
        w('  run.json structure of %s (depth<=2 scalars / container sizes):' % D11[0])
        for p, v in walk(rj0):
            if p.count('.') + p.count('[') > 1:
                continue
            if isinstance(v, (dict, list)):
                w('    %s : %s[%d]' % (p, type(v).__name__, len(v)))
            else:
                w('    %s = %s' % (p, json.dumps(v)[:120]))

    # ---------------- step 4: host timer line
    w('')
    w('=== STEP 4: "%s" per run' % HOST_TIMER)
    have = [run for run in ALL_RUNS if P[run]['host_timer'] > 0]
    for run in ALL_RUNS:
        w('    %-13s %-7s count %d  any-host-timer-lines %s' % (run, arm_of(run), P[run]['host_timer'],
                                                             P[run]['host_timer_any'] or '-'))
    w('  runs with it: %s ; exactly the 4 d11t runs: %s' % (have, sorted(have) == sorted(D11)))
    res['step4'] = dict(have=have, exactly_d11t=(sorted(have) == sorted(D11)))

    # ---------------- step 5: toypad
    w('')
    w('=== STEP 5: Toypad cadence (times in s after the first Toypad[Write])')
    s5 = OrderedDict()
    for run in ALL_RUNS:
        r = P[run]
        w('  %-13s %-7s W/R %d/%d cmds %s pattern_ok=%s' % (run, arm_of(run), r['n_write'], r['n_read'],
                                                          ' '.join(r['write_cmds']), r['pattern_ok']))
        w('      B1 at %s gaps %s | close at %s (last B1 -> close %s) | boot->first write %s, first line->close %s'
          % (r['b1_rel'], r['b1_gaps'], r['close_rel'], r['last_b1_to_close'], r['boot_to_first_write'],
             r['first_to_close']))
        w('      write hdrs %s | read hdrs %s | seq W %s R %s | unpaired %s | reply-before-write %s'
          % (r['write_hdrs'], r['read_hdrs'], ' '.join(r['write_seq']), ' '.join(r['read_seq']), r['unpaired'],
             r['reply_before_write'] or '-'))
        if r['odd_toy']:
            for x in r['odd_toy']:
                w('      ODD TOYPAD LINE: %s' % x)
        if r['bad_payload']:
            for x in r['bad_payload']:
                w('      BAD PAYLOAD: %s' % x)
        s5[run] = dict(arm=arm_of(run), n_write=r['n_write'], n_read=r['n_read'], cmds=r['write_cmds'],
                       pattern_ok=r['pattern_ok'], b1_rel=r['b1_rel'], b1_gaps=r['b1_gaps'], close_rel=r['close_rel'],
                       last_b1_to_close=r['last_b1_to_close'], boot_to_first_write=r['boot_to_first_write'],
                       first_to_close=r['first_to_close'], write_hdrs=r['write_hdrs'], read_hdrs=r['read_hdrs'],
                       unpaired=r['unpaired'], odd_toy=r['odd_toy'], bad_payload=r['bad_payload'])
    allgaps = [g for run in ALL_RUNS for g in P[run]['b1_gaps']]
    w('  all-run B1 gap range %.3f..%.3f s; max last-B1->close among 10/10 runs %s; min among 8/8 runs %s' % (
        min(allgaps), max(allgaps),
        max([P[x]['last_b1_to_close'] for x in ALL_RUNS if P[x]['n_write'] == 10] or [None]),
        min([P[x]['last_b1_to_close'] for x in ALL_RUNS if P[x]['n_write'] == 8] or [None])))
    res['step5'] = s5

    # ---------------- per-run table
    w('')
    w('=== TABLE (d11t + d0)')
    for run in D11 + D0:
        r = P[run]
        ex = r['runjson'].get('exit_code_hex') or []
        exs = ','.join(json.dumps(v) for _, v in ex) or '?'
        wer = r['runjson'].get('werfault_seen') or []
        fcd = r['runjson'].get('foreign_crash_dumps') or []
        st = r['runjson'].get('status') or []
        gv = ''
        if run in D11:
            gv = ' '.join(gate[(run, a)]['verdict'] if (run, a) in gate else '?' for a in D0)
            ng = '%d/%d/%d' % (sum(gate[(run, a)]['diff']['new_in_b_total'] for a in D0 if (run, a) in gate),
                               sum(gate[(run, a)]['diff']['gone_in_b_total'] for a in D0 if (run, a) in gate),
                               sum(gate[(run, a)]['diff']['count_changes_total'] for a in D0 if (run, a) in gate))
        else:
            ng = '-'
        w('  %-13s status=%s exit=%s clean_tail=%s dumps=%d wer=%s fcd=%s gate=[%s] new/gone/chg=%s toypad W/R %d/%d'
          % (run, ','.join(json.dumps(v) for _, v in st), exs, r['clean_tail'], len(r['dumps']),
             ','.join(json.dumps(v) for _, v in wer) or '?', ','.join(json.dumps(v)[:60] for _, v in fcd) or '?',
             gv, ng, r['n_write'], r['n_read']))

    with open(os.path.join(HERE, 'check_d11t.out.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(OUT) + '\n')
    with open(os.path.join(HERE, 'check_d11t.json'), 'w', encoding='utf-8') as fh:
        json.dump(res, fh, indent=1, default=str)
    print('wrote %d lines' % len(OUT))


if __name__ == '__main__':
    main()
