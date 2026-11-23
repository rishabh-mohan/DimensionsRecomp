# verify.py - independent checker for bench/agent11/timerq_slowstate_3mode.ps1 (Agent 11 task #10 helper).
# Run from the workspace root after the PowerShell runs:  python build/agent11/s4a/slowstate3-check/verify.py
# Reads the PS outputs in build/agent11/s4a/slowstate3-check/ and the raw run dirs; writes verify-out.md there.
# The recompute below is written from the rules in the task brief, not translated from the .ps1.
import csv, json, math, os, re, sys

CHK = os.path.join('build', 'agent11', 's4a', 'slowstate3-check')
MROOT = os.path.join('build', 'agent8', 'matrix')
TROOT = os.path.join('build', 'agent11', 's4a', 'slowstate3-test')
PRECISE = 'TimerQueue: precise wait (timer_queue_precise_wait)'
MS1 = 'Host timer resolution set to 1 ms'
EMHZ, MINROWS = 800.0, 3
ENVNAME = 'REX_TIMER_WAIT_BLOCKING'
COPY_COLS = ['matrix', 'run', 'arm', 'mode', 'env', 'pcvar', 'precise', 'ms1', 'onset_s', 'slow_pct', 'span_s', 'fg', 'flags']
ORIG_COLS = ['matrix', 'run', 'blocking', 'onset_s', 'slow_pct', 'span_s', 'fg']
ARM_COLS = ['matrix', 'arm', 'runs', 'mode', 'slow_runs', 'mean_slow_pct', 'mean_onset_s', 'note']
FLAG_COLS = ['matrix', 'run', 'mode', 'flags']
OUT = []


def md(s=''):
    OUT.append(s)


# ---------------------------------------------------------------- independent recompute
def round0(x):
    return int(round(x))  # Python round(): exact binary value, ties to even (== [math]::Round(x, 0))


def net_round1(x):
    return round0(x * 10.0) / 10.0  # .NET Framework Math.Round(x, 1) scales by 10 then rounds half-even


def ps_num(v):
    return str(int(v)) if float(v).is_integer() else repr(v)


def tie_margin(v):
    return abs((v - math.floor(v)) - 0.5)


def text_lines(path):
    with open(path, 'rb') as f:
        b = f.read()
    if b.startswith(b'\xef\xbb\xbf'):
        t = b[3:].decode('utf-8', 'replace')
    elif b.startswith(b'\xff\xfe'):
        t = b[2:].decode('utf-16-le', 'replace')
    elif b.startswith(b'\xfe\xff'):
        t = b[2:].decode('utf-16-be', 'replace')
    else:
        t = b.decode('utf-8', 'replace')
    return re.split(r'\r\n|\r|\n', t)


def names_env(o):
    if o is None:
        return False
    if isinstance(o, dict):
        return any(ENVNAME.lower() in str(k).lower() or names_env(v) for k, v in o.items())
    if isinstance(o, list):
        return any(names_env(v) for v in o)
    return ENVNAME.lower() in str(o).lower()


def precise_cvar_on(j):
    toks = [str(a) for a in (j.get('args') or [])]
    p = j.get('params')
    if isinstance(p, dict):
        cv = p.get('cvar')
        if isinstance(cv, list):
            toks += [str(c) for c in cv]
        elif cv is not None:
            toks.append(str(cv))
    for t in toks:
        k = t.strip().lstrip('-').lower()
        if k in ('timer_queue_precise_wait', 'timer_queue_precise_wait=true', 'timer_queue_precise_wait=1'):
            return True
    return False


def locate_log(rundir, j):
    p = os.path.join(rundir, 'game.log')
    if os.path.isfile(p):
        return p
    hit = ''
    for a in (j.get('args') or []):
        a = str(a)
        if a.lower().startswith('--log_file='):
            q = a[len('--log_file='):].strip().strip('"')
            if q and os.path.isfile(q):
                hit = q
    return hit


def arm_of(j, dirname):
    tag = j.get('tag')
    tag = '' if tag is None else str(tag)
    if tag == '':
        tag = re.sub(r'^\d{4}-', '', dirname)
    return re.sub(r'-r\d+$', '', tag)


def recompute_run(rundir):
    name = os.path.basename(rundir)
    sysp, rjp = os.path.join(rundir, 'sys.csv'), os.path.join(rundir, 'run.json')
    if not (os.path.isfile(sysp) and os.path.isfile(rjp)):
        return None, 'no sys.csv or run.json'
    try:
        with open(rjp, encoding='utf-8-sig') as f:
            j = json.load(f)
    except Exception:
        return None, 'run.json unreadable'
    ff = j.get('ff_signal_epoch_s')
    try:
        ff = float(ff) if ff not in (None, '') else 0.0
    except (TypeError, ValueError):
        ff = 0.0
    if not ff > 0:
        return None, 'ff_signal_epoch_s missing or <= 0'
    samples = []  # (t, e_mhz, fg)
    with open(sysp, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            e, ep = row.get('e_eff_mhz'), row.get('epoch_s')
            if e in (None, '') or ep in (None, ''):
                continue
            t = float(ep) - ff
            if t >= 0:
                samples.append((t, float(e), row.get('fg_game')))
    if not samples:
        return None, 'no samples from the first frame on'
    n = len(samples)
    low = sum(1 for s in samples if s[1] < EMHZ)
    onset = None
    i = 0
    while i < n and onset is None:  # first streak of >= MINROWS consecutive low samples
        if samples[i][1] < EMHZ:
            k = i
            while k < n and samples[k][1] < EMHZ:
                k += 1
            if k - i >= MINROWS:
                onset = samples[i][0]
            i = k
        else:
            i += 1
    slow_raw = 100.0 * low / n
    span_raw = samples[-1][0]
    fg = []
    for s in samples:
        if s[2] is not None and s[2] not in fg:
            fg.append(s[2])
    env = names_env(j.get('env_set'))
    pcvar = precise_cvar_on(j)
    logp = locate_log(rundir, j)
    have_log, npre, nms1 = False, 0, 0
    if logp:
        try:
            lines = text_lines(logp)
            have_log = True
            npre = sum(1 for ln in lines if PRECISE in ln)
            nms1 = sum(1 for ln in lines if MS1 in ln)
        except OSError:
            have_log, npre, nms1 = False, 0, 0
    if npre >= 1:
        mode = 'precise'
    elif pcvar and not have_log:
        mode = 'unknown'
    elif env:
        mode = 'blocking'
    else:
        mode = 'spin'
    flags = []
    if not have_log:
        flags.append('no_log')
    if npre > 1:
        flags.append('precise_lines>1')
    if npre >= 1 and env:
        flags.append('env+precise')
    if have_log and pcvar and npre == 0:
        flags.append('precise_cvar_no_line')
    if npre >= 1 and not pcvar:
        flags.append('precise_line_no_cvar')
    return dict(run=name, arm=arm_of(j, name), mode=mode, env=str(env), pcvar=str(pcvar), precise=str(npre),
                ms1=str(nms1), onset_s='-' if onset is None else str(round0(onset)), slow_pct=str(round0(slow_raw)),
                span_s=str(round0(span_raw)), fg='/'.join(fg), flags=','.join(flags), slow_raw=slow_raw,
                onset_raw=onset, span_raw=span_raw, n=n, low=low, log=logp), None


def recompute_matrix(root, mat):
    rd = os.path.join(root, mat, 'runs')
    rows, skipped = [], []
    for name in sorted(os.listdir(rd), key=str.lower):
        p = os.path.join(rd, name)
        if not os.path.isdir(p):
            continue
        r, why = recompute_run(p)
        if r is None:
            skipped.append((name, why))
            continue
        r['matrix'] = mat
        rows.append(r)
    return rows, skipped


def arm_table(rows):
    groups, order = {}, []
    for r in rows:
        k = (r['matrix'], r['arm'])
        if k not in groups:
            groups[k] = []
            order.append(k)
        groups[k].append(r)
    res = {}
    for k in order:
        g = groups[k]
        modes = []
        for r in g:
            if r['mode'] not in modes:
                modes.append(r['mode'])
        sl = [r for r in g if r['onset_raw'] is not None]
        mean_slow = sum(r['slow_raw'] for r in g) / len(g)
        mo = '-' if not sl else str(round0(sum(r['onset_raw'] for r in sl) / len(sl)))
        res[k] = dict(matrix=k[0], arm=k[1], runs=str(len(g)), mode='/'.join(modes), slow_runs=str(len(sl)),
                      mean_slow_pct=ps_num(net_round1(mean_slow)), mean_onset_s=mo,
                      note='MIXED' if len(modes) > 1 else '', exact=mean_slow)
    return res


def summary_line(rows):
    parts = []
    for m in ('precise', 'blocking', 'spin', 'unknown'):
        g = [r for r in rows if r['mode'] == m]
        if m == 'unknown' and not g:
            continue
        parts.append('%s runs: %d, with slow state: %d' % (m, len(g), sum(1 for r in g if r['onset_s'] != '-')))
    return '; '.join(parts) + ' (E below 800 MHz for 3+ samples)'


# ---------------------------------------------------------------- PowerShell output parsing
def ps_output(path):
    lines = [l.rstrip() for l in text_lines(path)]
    tables, i = [], 0
    while i < len(lines) - 1:
        if lines[i].strip() and '-' in lines[i + 1] and re.fullmatch(r'[- ]+', lines[i + 1]):
            hdr, rows, k = lines[i].split(), [], i + 2
            while k < len(lines) and lines[k].strip():
                rows.append(lines[k].split())
                k += 1
            tables.append((hdr, rows))
            i = k
        else:
            i += 1
    return lines, tables


def table_dicts(table, cols, optional_last, key):
    hdr, rows = table
    assert hdr == cols, 'header %r != %r' % (hdr, cols)
    res = {}
    for t in rows:
        if optional_last and len(t) == len(cols) - 1:
            t = t + ['']
        assert len(t) == len(cols), 'row %r' % (t,)
        d = dict(zip(cols, t))
        res[tuple(d[c] for c in key)] = d
    return res


def csv_rows(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return {(r['matrix'], r['run']): r for r in csv.DictReader(f)}


def find_line(lines, prefix):
    hits = [l for l in lines if l.startswith(prefix)]
    return hits[0] if len(hits) == 1 else None


class Check:
    def __init__(self, name):
        self.name, self.fails, self.notes = name, [], []

    def need(self, cond, msg):
        if not cond:
            self.fails.append(msg)
        return cond

    @property
    def status(self):
        return 'PASS' if not self.fails else 'FAIL'


# ---------------------------------------------------------------- checks 1 and 2 (+ the real-data part of 3)
def check_real(label, mat, orig_txt, copy_txt, copy_csv, since_txt, expect_mode, c3):
    c = Check(label)
    _, ot = ps_output(os.path.join(CHK, orig_txt))
    orig = {k: v for k, v in table_dicts(ot[0], ORIG_COLS, True, ('matrix', 'run')).items() if k[0] == mat}
    clines, ct = ps_output(os.path.join(CHK, copy_txt))
    ctab = table_dicts(ct[0], COPY_COLS, True, ('matrix', 'run'))
    carms = table_dicts(ct[1], ARM_COLS, True, ('matrix', 'arm'))
    csvr = csv_rows(os.path.join(CHK, copy_csv))
    _, st = ps_output(os.path.join(CHK, since_txt))
    since = {k: v for k, v in table_dicts(st[0], COPY_COLS, True, ('matrix', 'run')).items() if k[0] == mat}
    py, skipped = recompute_matrix(MROOT, mat)
    pyd = {(r['matrix'], r['run']): r for r in py}
    rd = os.path.join(MROOT, mat, 'runs')
    dirs = {(mat, n) for n in os.listdir(rd) if os.path.isdir(os.path.join(rd, n))}
    c.need(set(orig) == set(csvr), 'run set original %d vs copy csv %d' % (len(orig), len(csvr)))
    c.need(set(ctab) == set(csvr), 'run set copy table vs copy csv')
    c.need(set(since) == set(csvr), 'run set copy -Since vs copy -Matrix')
    c.need(set(csvr) == dirs, 'not every run dir is in the copy output')
    c.notes.append('run dirs %d; original rows %d; copy CSV rows %d; copy table rows %d; copy -Since rows %d; python rows %d (skipped %d)'
                   % (len(dirs), len(orig), len(csvr), len(ctab), len(since), len(py), len(skipped)))
    tbl = ['| run | arm | orig blocking | copy env | copy mode | expected | onset_s o/c/p | slow_pct o/c/p | span_s o/c/p | fg o ; c ; p | pcvar | precise | ms1 | flags | ok |',
           '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for k in sorted(csvr, key=lambda x: x[1].lower()):
        o, cr, t, p, s = orig.get(k, {}), csvr[k], ctab.get(k, {}), pyd.get(k, {}), since.get(k, {})
        n0 = len(c.fails)
        for col in ('onset_s', 'slow_pct', 'span_s', 'fg'):
            c.need(o.get(col) == cr[col], '%s %s original %r vs copy %r' % (k[1], col, o.get(col), cr[col]))
        c.need(o.get('blocking') == cr['env'], '%s original blocking %r vs copy env %r' % (k[1], o.get('blocking'), cr['env']))
        for col in COPY_COLS:
            c.need(t.get(col) == cr[col], '%s copy table %s %r vs csv %r' % (k[1], col, t.get(col), cr[col]))
            c.need(s.get(col) == cr[col], '%s copy -Since %s %r vs -Matrix %r' % (k[1], col, s.get(col), cr[col]))
        exp = expect_mode.get(cr['arm'], '?arm?')
        c.need(cr['mode'] == exp, '%s mode %r expected %r' % (k[1], cr['mode'], exp))
        c.need(cr['flags'] == '', '%s has flags %r' % (k[1], cr['flags']))
        tbl.append('| %s | %s | %s | %s | %s | %s | %s/%s/%s | %s/%s/%s | %s/%s/%s | %s ; %s ; %s | %s | %s | %s | %s | %s |' % (
            k[1], cr['arm'], o.get('blocking'), cr['env'], cr['mode'], exp,
            o.get('onset_s'), cr['onset_s'], p.get('onset_s'), o.get('slow_pct'), cr['slow_pct'], p.get('slow_pct'),
            o.get('span_s'), cr['span_s'], p.get('span_s'), o.get('fg'), cr['fg'], p.get('fg'),
            cr['pcvar'], cr['precise'], cr['ms1'], cr['flags'] or '-', 'yes' if len(c.fails) == n0 else 'NO'))
    c.need(all(a['note'] == '' for a in carms.values()), 'a MIXED arm is present')
    c.need(len(ct) == 2, 'unexpected flags table (%d tables)' % len(ct))
    cl = find_line(clines, 'runs with flags:')
    c.need(cl == 'runs with flags: 0; mixed arms: 0', 'counts line %r' % cl)
    sl = find_line(clines, 'precise runs:')
    csv_like = [dict(mode=r['mode'], onset_s=r['onset_s']) for r in csvr.values()]
    c.need(sl == summary_line(csv_like), 'summary line %r vs %r' % (sl, summary_line(csv_like)))
    ob = [v for v in orig.values() if v['blocking'] == 'True']
    on = [v for v in orig.values() if v['blocking'] != 'True']
    c.notes.append('copy summary: `%s`; counts: `%s`' % (sl, cl))
    c.notes.append('original restricted to %s: blocking %d (slow %d), non-blocking %d (slow %d)' % (
        mat, len(ob), sum(1 for v in ob if v['onset_s'] != '-'), len(on), sum(1 for v in on if v['onset_s'] != '-')))
    md('### %s per-run comparison (o = original, c = copy CSV, p = python recompute)' % label)
    md()
    OUT.extend(tbl)
    md()
    md('Copy arm table (parsed from the copy\'s text output):')
    md()
    md('| ' + ' | '.join(ARM_COLS) + ' |')
    md('|' + '---|' * len(ARM_COLS))
    for a in sorted(carms.values(), key=lambda a: a['arm'].lower()):
        md('| ' + ' | '.join(a[x] or '-' for x in ARM_COLS) + ' |')
    md()
    # ---- check 3 part: python vs copy csv
    pyarms = arm_table(py)
    for k in sorted(csvr):
        cr, p = csvr[k], pyd.get(k)
        if not c3.need(p is not None, '%s missing from python recompute' % (k,)):
            continue
        for col in COPY_COLS:
            c3.need(p[col] == cr[col], '%s %s python %r vs copy %r' % (k[1], col, p[col], cr[col]))
        c3.need(abs(float(cr['slow_raw']) - p['slow_raw']) < 1e-9, '%s slow_raw %s vs %r' % (k[1], cr['slow_raw'], p['slow_raw']))
        if p['onset_raw'] is None:
            c3.need(cr['onset_raw'] == '', '%s onset_raw %r vs None' % (k[1], cr['onset_raw']))
        else:
            c3.need(cr['onset_raw'] != '' and abs(float(cr['onset_raw']) - p['onset_raw']) < 1e-9,
                    '%s onset_raw %r vs %r' % (k[1], cr['onset_raw'], p['onset_raw']))
    c3.need(set(pyd) == set(csvr), '%s python run set differs from copy' % mat)
    for k, a in carms.items():
        pa = pyarms.get(k)
        if not c3.need(pa is not None, '%s arm %s missing from python arm table' % (mat, k[1])):
            continue
        for col in ARM_COLS:
            c3.need(pa[col] == a[col], '%s arm %s %s python %r vs copy %r' % (mat, k[1], col, pa[col], a[col]))
    c3.need(set(pyarms) == set(carms), '%s arm sets differ' % mat)
    c3.need(sl == summary_line(py), '%s summary line python %r vs copy %r' % (mat, summary_line(py), sl))
    nflag = sum(1 for r in py if r['flags'])
    nmix = sum(1 for a in pyarms.values() if a['note'])
    c3.need(cl == 'runs with flags: %d; mixed arms: %d' % (nflag, nmix), '%s counts line' % mat)
    margins = []
    for r in py:
        for nm in ('onset_raw', 'slow_raw', 'span_raw'):
            if r[nm] is not None:
                margins.append((tie_margin(r[nm]), r['run'], nm, r[nm]))
    margins.sort()
    c3.notes.append('%s: %d runs, all 13 columns + slow_raw/onset_raw (|diff| < 1e-9) compared; arm table %d rows compared; '
                    'smallest distance of any rounded value from a .5 tie: %.4f (%s %s = %r)'
                    % (mat, len(py), len(carms), margins[0][0], margins[0][1], margins[0][2], margins[0][3]))
    for a in pyarms.values():
        x = a['exact'] * 10
        if abs((x - math.floor(x)) - 0.5) < 1e-6:
            c3.notes.append('%s arm %s mean_slow_pct %r sits on a 1-decimal tie' % (mat, a['arm'], a['exact']))
    return c


# ---------------------------------------------------------------- check 4 (synthetic)
def check_synth(c3):
    c = Check('4 synthetic')
    exp = json.load(open(os.path.join(CHK, 'synth-expected.json'), encoding='utf-8'))
    mat = '20990101-0000'
    clines, ct = ps_output(os.path.join(CHK, 'synth-3mode.txt'))
    ctab = table_dicts(ct[0], COPY_COLS, True, ('matrix', 'run'))
    carms = table_dicts(ct[1], ARM_COLS, True, ('matrix', 'arm'))
    cflags = table_dicts(ct[2], FLAG_COLS, False, ('matrix', 'run')) if len(ct) > 2 else {}
    csvr = csv_rows(os.path.join(CHK, 'synth-3mode.csv'))
    rows = [e for e in exp if e['matrix'] == mat]
    md('### Synthetic cases (matrix %s)' % mat)
    md()
    md('| case | run | expected mode / flags | copy mode / flags | env | pcvar | precise | ms1 | onset/slow/span | arm | ok |')
    md('|---|---|---|---|---|---|---|---|---|---|---|')
    for e in rows:
        k = (mat, e['run'])
        n0 = len(c.fails)
        cr = csvr.get(k)
        if not e['included']:
            c.need(cr is None and k not in ctab, '%s should be skipped' % e['run'])
            md('| %s | %s | skipped | %s | | | | | | | %s |' % (e['desc'], e['run'], 'absent' if cr is None else 'PRESENT',
                                                               'yes' if len(c.fails) == n0 else 'NO'))
            continue
        if not c.need(cr is not None, '%s missing' % e['run']):
            md('| %s | %s | %s / %s | MISSING | | | | | | | NO |' % (e['desc'], e['run'], e['mode'], e['flags']))
            continue
        for col in ('arm', 'mode', 'env', 'pcvar', 'precise', 'ms1', 'onset_s', 'slow_pct', 'span_s', 'fg', 'flags'):
            c.need(cr[col] == e[col], '%s %s copy %r expected %r' % (e['run'], col, cr[col], e[col]))
        for col in COPY_COLS:
            c.need(ctab.get(k, {}).get(col) == cr[col], '%s table vs csv %s' % (e['run'], col))
        md('| %s | %s | %s / %s | %s / %s | %s | %s | %s | %s | %s/%s/%s | %s | %s |' % (
            e['desc'], e['run'], e['mode'], e['flags'] or '-', cr['mode'], cr['flags'] or '-', cr['env'], cr['pcvar'],
            cr['precise'], cr['ms1'], cr['onset_s'], cr['slow_pct'], cr['span_s'], cr['arm'],
            'yes' if len(c.fails) == n0 else 'NO'))
    inc = [e for e in rows if e['included']]
    c.need(set(csvr) == {(mat, e['run']) for e in inc}, 'copy CSV run set != expected included set')
    want_sum = summary_line(inc)
    sl = find_line(clines, 'precise runs:')
    c.need(sl == want_sum, 'summary line %r expected %r' % (sl, want_sum))
    # expected arm grouping: PowerShell Group-Object is case-insensitive, so Y and y merge into one arm row
    arms_ci = {}
    for e in inc:
        arms_ci.setdefault(e['arm'].lower(), []).append(e)
    want_mixed = sorted(a for a, g in arms_ci.items() if len({x['mode'] for x in g}) > 1)
    got_mixed = sorted(a[1].lower() for a in carms if carms[a]['note'] == 'MIXED')
    c.need(got_mixed == want_mixed, 'MIXED arms %r expected %r' % (got_mixed, want_mixed))
    x = carms.get((mat, 'x'), {})
    c.need(x.get('mode') == 'spin/precise' and x.get('runs') == '2', 'arm x row %r' % x)
    yrow = [a for a in carms.values() if a['arm'].lower() == 'y']
    c.notes.append('arm rows: %d (expected %d with case-insensitive grouping); Y/y rows: %s'
                   % (len(carms), len(arms_ci), ['%s runs=%s' % (a['arm'], a['runs']) for a in yrow]))
    c.need(len(carms) == len(arms_ci), 'arm row count %d expected %d' % (len(carms), len(arms_ci)))
    nflag = sum(1 for e in inc if e['flags'])
    want_cl = 'runs with flags: %d; mixed arms: %d' % (nflag, len(want_mixed))
    cl = find_line(clines, 'runs with flags:')
    c.need(cl == want_cl, 'counts line %r expected %r' % (cl, want_cl))
    want_flagtab = {(mat, e['run']): e['flags'] for e in inc if e['flags']}
    c.need({k: v['flags'] for k, v in cflags.items()} == want_flagtab, 'flags table differs')
    c.notes.append('summary: `%s`' % sl)
    c.notes.append('counts: `%s`; flags table rows: %d' % (cl, len(cflags)))
    md()
    md('Copy arm table for the synthetic matrix:')
    md()
    md('| ' + ' | '.join(ARM_COLS) + ' |')
    md('|' + '---|' * len(ARM_COLS))
    for a in sorted(carms.values(), key=lambda a: a['arm'].lower()):
        md('| ' + ' | '.join(a[x] or '-' for x in ARM_COLS) + ' |')
    md()
    # python recompute on the synthetic tree (informational: shows where the rules-as-written differ from the .ps1)
    py, skipped = recompute_matrix(TROOT, mat)
    diffs = []
    for r in py:
        cr = csvr.get((mat, r['run']))
        if cr is None:
            diffs.append('%s: python includes, copy skips' % r['run'])
            continue
        for col in COPY_COLS[2:]:
            if r[col] != cr[col]:
                diffs.append('%s %s: python %r vs copy %r' % (r['run'], col, r[col], cr[col]))
    for name, why in skipped:
        if (mat, name) in csvr:
            diffs.append('%s: python skips (%s), copy includes' % (name, why))
    c.notes.append('python recompute on the synthetic tree: %d runs, skipped %s; differences vs copy: %s'
                   % (len(py), [s[0] for s in skipped], diffs or 'none'))
    return c


def main():
    c1 = Check('1 W4b')
    c2 = Check('2 W5')
    c3 = Check('3 python recompute')
    w4b_modes = {'d0': 'spin', 'B': 'spin', 'd3': 'spin', 'cold-d0': 'spin', 'd11t': 'blocking'}
    w5_modes = {'base': 'spin', 's0': 'spin', 'd11': 'spin', 'cold-base': 'spin', 'd11t': 'blocking', 'd11p': 'precise'}
    r1 = check_real('1 W4b', '20261122-1541', 'orig-since-1541.txt', 'w4b-3mode.txt', 'w4b-3mode.csv',
                    'copy-since-1541.txt', w4b_modes, c3)
    r2 = check_real('2 W5', '20261122-1756', 'orig-since-1756.txt', 'w5-3mode.txt', 'w5-3mode.csv',
                    'copy-since-1541.txt', w5_modes, c3)
    r4 = check_synth(c3)
    head = ['## Check results (generated by verify.py)', '']
    for c in (r1, r2, c3, r4):
        head.append('- **%s: %s**' % (c.name, c.status))
        for n in c.notes:
            head.append('  - ' + n)
        for f in c.fails[:40]:
            head.append('  - FAIL: ' + f)
    head.append('')
    with open(os.path.join(CHK, 'verify-out.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(head + OUT) + '\n')
    print('\n'.join(head))


if __name__ == '__main__':
    main()
