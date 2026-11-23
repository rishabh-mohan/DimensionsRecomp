#!/usr/bin/env python3
"""Compares the independent recompute (xcheck_data.json from xcheck.py) with the published numbers and writes the
final report xcheck.md + xcheck_compare.csv into the matrix's xcheck dir. Helper of Agent 8 (2026-11-23); own code,
stdlib only; reads only; writes only into build/agent8/readout/{w4b,w5}/xcheck.

  python -B xcheck_compare.py w4b|w5

Sources (parsed from the files, except Agent 1's SESSION2 tables and sentences, transcribed by hand):
  runner    matrix summary.md (arms table, noise band, runs table)
  Agent 8   add-on JSON (w4b.json / w5.json / w5-s0.json: arms, deltas, verdicts, paired fps), rules-nodrop.md
            (R5 table + pair table, R7 TimerQueue per run and per arm), rules.md (R7), recheck.txt (runs, arms, deltas)
  Agent 1   perf-notes/SESSION2.md 16:35 (W4b) and 18:34 (W5)
Result per number: ok = the published value is a correct rounding of my value (within half a unit of its last digit;
JSON floats: equal to 1e-9 relative, or within 0.1 % = ok with the diff noted); definition = not ok, but a correct
rounding of the named alternative definition; rounding tie = not ok against my exact value, but a correct rounding
of an intermediate value that sits exactly on the rounding boundary (the runner's 4-dp light share in frames.json, or
a difference/median of the 3-dp results.csv values), so both roundings are legitimate; MISMATCH = none of these.
"""
import csv
import math
import os
import re
import statistics
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xcheck as X  # noqa: E402  (my own module, same dir)

REPO = X.REPO


def P(*a):
    return os.path.join(REPO, *a)


NUM = r'[-+\u2212]?\d+(?:\.\d+)?'
RNG = re.compile(r'^\s*(%s)\s*\((%s)\.\.(%s)\)' % (NUM, NUM, NUM))


def num(s):
    return float(str(s).strip().replace('\u2212', '-').rstrip('%'))


def nd_of(s):
    s = str(s).strip().rstrip('%')
    return len(s.split('.')[1]) if '.' in s else 0


def on_tie(v, nd):
    """True when v lies on the rounding boundary for nd decimals (e.g. 0.8075 for 3 decimals, -0.525 for 2)."""
    x = abs(v) * 10 ** nd
    return abs((x - math.floor(x)) - 0.5) < 1e-6


def cells(ln):
    return [c.strip() for c in ln.strip().strip('|').split('|')]


def read_lines(path):
    try:
        with open(path, encoding='utf-8-sig') as fh:
            return fh.read().splitlines()
    except OSError:
        return None


def table(lines, prefix):
    for i, ln in enumerate(lines or []):
        if ln.startswith(prefix):
            hdr = cells(ln)
            rows = []
            for ln2 in lines[i + 2:]:
                if not ln2.startswith('|'):
                    break
                rows.append(dict(zip(hdr, cells(ln2))))
            return hdr, rows
    return [], []


def col(row, prefix):
    for k, v in row.items():
        if k.startswith(prefix):
            return v
    return None


class Ctx:
    def __init__(self, label):
        self.label = label
        self.cfg = X.CFG[label]
        import json
        with open(os.path.join(self.cfg['out'], 'xcheck_data.json'), encoding='utf-8') as fh:
            self.d = json.load(fh)
        self.runs = self.d['runs']
        res = X.read_csv(os.path.join(self.cfg['matrix'], 'results.csv'))
        rc = {os.path.basename(r['run_dir']): r for r in res}
        for r in self.runs:
            r['cores_rj'] = r['cores_runjson']
            r['rc'] = rc[r['name']]
            r['cores_rc'] = X.fnum(r['rc']['cpu_cores_mean'])
            fjp = os.path.join(r['rc']['run_dir'], 'frames.json')
            fj = (X.load_json(fjp) if os.path.exists(fjp) else None) or {}
            r['fj_light'] = fj.get('share_lt_light')
            r['o33min'] = r['over33'] / (r['window_s'] / 60.0)
            r['cpf'] = r['cores_rj'] * 1000.0 / r['fps'] if r['cores_rj'] is not None else None
        self.by = {r['name']: r for r in self.runs}
        self.byseq = {r['seq']: r for r in self.runs}
        self.rows = []
        self.parsed = []

    def sel(self, arm, s='all'):
        return [r for r in self.runs if r['scored'] and r['arm'] == arm and
                (s == 'all' or (s == 'valid' and r['valid']) or (isinstance(s, (set, frozenset)) and r['name'] in s))]

    def st(self, arm, key, s='all'):
        return X.mmm([r[key] for r in self.sel(arm, s)])

    def pair(self, arm, ref, key, s='all'):
        return X.paired(self.sel(arm, s), self.sel(ref, s), key)

    def add(self, src, item, shown, mine, res, note=''):
        self.rows.append(dict(src=src, item=item, shown=str(shown), mine=str(mine), res=res, note=note))

    def chk(self, src, item, shown, mine, nd=None, alts=()):
        if shown is None or str(shown).strip() in ('', '-'):
            return
        s = str(shown).strip()
        v = num(s)
        n = nd_of(s) if nd is None else nd
        if mine is None:
            self.add(src, item, s, '-', 'NOT CHECKED', 'no recomputed value')
            return
        txt = '%.*f' % (n + 2, mine)
        if X.shown_ok(mine, v, n):
            self.add(src, item, s, txt, 'ok')
            return
        for a in alts:
            lab, alt = a[0], a[1]
            if alt is not None and X.shown_ok(alt, v, n):
                cls = 'definition'
                if len(a) > 2 and a[2] == 'tie' and on_tie(alt, n):
                    cls = 'rounding tie'
                self.add(src, item, s, txt, cls, '%s = %.*f' % (lab, n + 2, alt))
                return
        self.add(src, item, s, txt, 'MISMATCH',
                 '; '.join('%s = %.*f' % (a[0], n + 2, a[1]) for a in alts if a[1] is not None))

    @staticmethod
    def light_alts(r):
        return [('frames.json share_lt_light (runner rounds to 4 dp; rounded again)', r['fj_light'], 'tie'),
                ('results.csv light_share', X.fnum(r['rc']['light_share']))]

    def eq(self, src, item, shown, mine, note=''):
        self.add(src, item, shown, mine, 'ok' if str(shown).strip() == str(mine).strip() else 'MISMATCH', note)

    def fl(self, src, item, shown, mine):
        if shown is None or mine is None:
            self.add(src, item, shown, mine, 'NOT CHECKED' if (shown is None and mine is None) else 'MISMATCH',
                     'one side missing')
            return
        d = abs(shown - mine)
        scale = max(abs(shown), abs(mine), 1e-12)
        if d <= 1e-9 * scale + 1e-12:
            self.add(src, item, '%.6f' % shown, '%.6f' % mine, 'ok')
        elif d <= 1e-3 * scale:
            self.add(src, item, '%.6f' % shown, '%.6f' % mine, 'ok', 'within 0.1 %%, diff %.3g' % (shown - mine))
        else:
            self.add(src, item, '%.6f' % shown, '%.6f' % mine, 'MISMATCH', 'diff %.3g' % (shown - mine))


# ---------------------------------------------------------------- runner summary.md

def check_summary(c):
    src = 'runner summary.md'
    lines = read_lines(os.path.join(c.cfg['matrix'], 'summary.md'))
    ref = c.cfg['ref']
    _, rows = table(lines, '| arm | OK/runs |')
    for row in rows:
        arm = row['arm']
        st, sr = c.st(arm, 'median_ms'), c.st(ref, 'median_ms')
        m = RNG.match(row['median ms (min..max)'])
        for i, part in ((1, 'med'), (2, 'lo'), (3, 'hi')):
            c.chk(src, '%s median ms %s' % (arm, part), m.group(i), st[part], nd=2)
        c.chk(src, arm + ' spread %', row['spread %'], 100 * (st['hi'] - st['lo']) / st['med'], nd=1)
        c.chk(src, arm + ' p99 ms', row['p99 ms'], c.st(arm, 'p99_ms')['med'], nd=2)
        c.chk(src, arm + ' p99.9 ms', row['p99.9 ms'], c.st(arm, 'p999_ms')['med'], nd=2)
        c.chk(src, arm + ' fps', row['fps'], c.st(arm, 'fps')['med'], nd=2)
        cp, cr = c.st(arm, 'cores'), c.st(arm, 'cores_rj')
        c.chk(src, arm + ' cpu cores', row['cpu cores'], cp['med'], nd=2,
              alts=[('mean of the runs (run.json)', cr['mean']), ('mean of the runs (my proc.csv)', cp['mean'])])
        if arm != ref:
            c.chk(src, arm + ' d median %', row['d median %'], 100 * (st['med'] / sr['med'] - 1), nd=1)
            c.chk(src, arm + ' d p99 %', row['d p99 %'],
                  100 * (c.st(arm, 'p99_ms')['med'] / c.st(ref, 'p99_ms')['med'] - 1), nd=1)
        c.eq(src, arm + ' runs used (OK/runs)', row['OK/runs'].split('/')[0], len(c.sel(arm)))
        c.eq(src, arm + ' valid', row['valid'], len(c.sel(arm, 'valid')))
    for ln in lines:
        m = re.search(r'noise band \+-(%s) %%' % NUM, ln)
        if m:
            st = c.st(ref, 'median_ms')
            c.chk(src, 'noise band % (ref (max-min)/median)', m.group(1), 100 * (st['hi'] - st['lo']) / st['med'], nd=1)
            break
    _, rrows = table(lines, '| # | round | arm |')
    for row in rrows:
        r = c.byseq[int(row['#'])]
        c.eq(src, r['name'] + ' frames', row['frames'], r['frames'])
        c.chk(src, r['name'] + ' median ms', row['median ms'], r['median_ms'], nd=3)
        c.chk(src, r['name'] + ' p99 ms', row['p99 ms'], r['p99_ms'], nd=3)
        c.eq(src, r['name'] + ' >33', row['>33'], r['over33'])
        c.eq(src, r['name'] + ' >100', row['>100'], r['over100'])
        c.chk(src, r['name'] + ' cpu', row['cpu'], r['cores'], nd=3, alts=[('run.json cpu_cores_mean', r['cores_rj'])])
        c.chk(src, r['name'] + ' light', row['light'], r['light_share'], nd=3, alts=c.light_alts(r))
    c.parsed.append('%s: %d arm rows, %d run rows' % (src, len(rows), len(rrows)))


# ---------------------------------------------------------------- Agent 8: add-on JSON

def check_addon(c, path, src):
    d = X.load_json(path)
    if not d:
        c.add(src, 'file', path, '-', 'NOT CHECKED', 'not found')
        return
    ref = d['ref']
    sets = {arm: set(a.get('runs') or []) for arm, a in d['arms'].items()}
    for arm, a in d['arms'].items():
        S = sets[arm]
        c.eq(src, arm + ' n (runs: %s)' % ', '.join(sorted(S)), a.get('n'), len(c.sel(arm, S)))
        for jk, key in (('fps', 'fps'), ('p50_ms', 'median_ms'), ('p99_ms', 'p99_ms'), ('low1_fps', 'low1_fps'),
                        ('over33_min', 'o33min')):
            st = c.st(arm, key, S)
            for part in ('med', 'lo', 'hi'):
                c.fl(src, '%s %s %s' % (arm, jk, part), a[jk][part], st[part])
        if 'spread_pct' in a['fps']:
            st = c.st(arm, 'fps', S)
            c.fl(src, arm + ' fps spread_pct', a['fps']['spread_pct'], 100 * (st['hi'] - st['lo']) / st['med'])
    for arm, dd in d['deltas'].items():
        Sa, Sr = sets[arm], sets[ref]
        for jk, key, hb in (('fps', 'fps', True), ('p50_ms', 'median_ms', False), ('p99_ms', 'p99_ms', False),
                            ('low1_fps', 'low1_fps', True)):
            a, b = c.st(arm, key, Sa), c.st(ref, key, Sr)
            c.fl(src, '%s vs %s d %s pct' % (arm, ref, jk), dd[jk]['pct'], 100 * (a['med'] / b['med'] - 1))
            c.fl(src, '%s vs %s d %s delta' % (arm, ref, jk), dd[jk]['delta'], a['med'] - b['med'])
            c.eq(src, '%s vs %s %s verdict' % (arm, ref, jk), dd[jk]['verdict'],
                 X.decide([r[key] for r in c.sel(arm, Sa)], [r[key] for r in c.sel(ref, Sr)], hb))
        p = dd['paired_fps_pct']
        pf = X.paired(c.sel(arm, Sa), c.sel(ref, Sr), 'fps')
        c.fl(src, '%s vs %s paired fps median pct' % (arm, ref), p['med'], 100 * pf['rel_med'])
        c.eq(src, '%s vs %s paired fps up / n' % (arm, ref), '%s / %s' % (p['up'], p['n']), '%d / %d' % (pf['up'], pf['n']))
    c.parsed.append('%s: %d arms, %d deltas (ref %s)' % (src, len(d['arms']), len(d['deltas']), ref))


# ---------------------------------------------------------------- Agent 8: rules-nodrop R5 / R7

def vs_cell(c, src, arm, ref, cell, pcell, s):
    parts = [p.strip() for p in (cell or '').split(' / ')]
    for p, key, hb in zip(parts, ('fps', 'median_ms', 'p99_ms', 'low1_fps'), (True, False, False, True)):
        m = re.match(r'(%s)%%\s+(\w+)' % NUM, p)
        if not m:
            c.add(src, '%s vs %s %s' % (arm, ref, key), p, '-', 'NOT CHECKED', 'unparsed')
            continue
        a, b = c.st(arm, key, s), c.st(ref, key, s)
        c.chk(src, '%s vs %s d %s %%' % (arm, ref, key), m.group(1), 100 * (a['med'] / b['med'] - 1))
        c.eq(src, '%s vs %s %s decision' % (arm, ref, key), m.group(2),
             X.decide([r[key] for r in c.sel(arm, s)], [r[key] for r in c.sel(ref, s)], hb))
    if len(parts) > 4:
        m = re.match(r'(%s)/min\s+(\w+)' % NUM, parts[4])
        if m:
            c.chk(src, '%s vs %s d >33/min' % (arm, ref), m.group(1),
                  c.st(arm, 'o33min', s)['med'] - c.st(ref, 'o33min', s)['med'])
    m = re.match(r'(%s)%%\s*\((\d+)\s*/\s*(\d+)\)' % NUM, pcell or '')
    if m:
        pf = c.pair(arm, ref, 'fps', s)
        c.chk(src, '%s vs %s paired fps median %%' % (arm, ref), m.group(1), 100 * pf['rel_med'])
        c.eq(src, '%s vs %s paired fps up / rounds' % (arm, ref), '%s / %s' % (m.group(2), m.group(3)),
             '%d / %d' % (pf['up'], pf['n']))


def check_r5(c, path, src, s):
    lines = read_lines(path)
    if lines is None:
        c.add(src, 'file', path, '-', 'NOT CHECKED', 'not found')
        return
    ref = c.cfg['ref']
    _, rows = table(lines, '| arm | n | fps |')
    for row in rows:
        arm = row['arm']
        c.eq(src, arm + ' n', row['n'], len(c.sel(arm, s)))
        for cname, key in (('fps', 'fps'), ('p50 ms', 'median_ms'), ('p99 ms', 'p99_ms'), ('1% low fps', 'low1_fps'),
                           ('>33 ms/min', 'o33min')):
            m = RNG.match(row.get(cname, ''))
            if not m:
                continue
            st = c.st(arm, key, s)
            for i, part in ((1, 'med'), (2, 'lo'), (3, 'hi')):
                c.chk(src, '%s %s %s' % (arm, cname, part), m.group(i), st[part])
        if arm != ref:
            vs_cell(c, src, arm, ref, col(row, 'vs '), col(row, 'paired fps'), s)
    _, rows2 = table(lines, '| pair (arm vs against)')
    for row in rows2:
        arm, _, ref2 = row['pair (arm vs against)'].partition(' vs ')
        c.eq(src, '%s vs %s n vs n' % (arm, ref2), row['n vs n'], '%d vs %d' % (len(c.sel(arm, s)), len(c.sel(ref2, s))))
        vs_cell(c, src, arm, ref2, col(row, 'fps / p50'), col(row, 'paired fps'), s)
    c.parsed.append('%s R5: %d arm rows, %d pair rows' % (src, len(rows), len(rows2)))


def check_r7(c, path, src):
    lines = read_lines(path)
    if lines is None:
        c.add(src, 'file', path, '-', 'NOT CHECKED', 'not found')
        return
    pat = re.compile(r'(\d{4}-[A-Za-z0-9]+-[A-Za-z0-9]+) \(.*?TimerQueue (%s)%% \(max 1 s (%s)%%\)' % (NUM, NUM))
    seen = set()
    for ln in lines:
        m = pat.search(ln)
        if m and m.group(1) in c.by and m.group(1) not in seen:
            seen.add(m.group(1))
            r = c.by[m.group(1)]
            c.chk(src, r['name'] + ' TimerQueue busy %', m.group(2), r['tq_busy'])
            c.chk(src, r['name'] + ' TimerQueue max 1 s %', m.group(3), r['tq_max'])
    _, rows = table(lines, '| arm | mode |')
    for row in rows:
        arm = row['arm']
        m = RNG.match(col(row, 'TimerQueue') or '')
        st = c.st(arm, 'tq_busy')
        if m:
            for i, part in ((1, 'med'), (2, 'lo'), (3, 'hi')):
                c.chk(src, '%s TimerQueue busy %% %s' % (arm, part), m.group(i), st[part])
        c.chk(src, arm + ' TimerQueue max 1 s %', row.get('max 1 s'),
              max(r['tq_max'] for r in c.sel(arm) if r['tq_max'] is not None))
        c.eq(src, arm + ' scored runs', row.get('scored runs'), len(c.sel(arm)))
    c.parsed.append('%s R7: %d per-run lines, %d arm rows' % (src, len(seen), len(rows)))


# ---------------------------------------------------------------- Agent 8: recheck.txt

def check_recheck(c, path, src):
    lines = read_lines(path)
    if lines is None:
        c.add(src, 'file', path, '-', 'NOT CHECKED', 'not found')
        return
    _, rows = table(lines, '| seq | round | arm |')
    kept = set()
    for row in rows:
        r = c.byseq[int(row['seq'])]
        if row.get('kept') == 'yes':
            kept.add(r['name'])
        c.chk(src, r['name'] + ' median ms', row['median ms'], r['median_ms'])
        c.chk(src, r['name'] + ' fps', row['fps'], r['fps'],
              alts=[('results.csv fps_mean (runner-rounded)', X.fnum(r['rc']['fps_mean']), 'tie')])
        c.chk(src, r['name'] + ' p99 ms', row['p99 ms'], r['p99_ms'])
        c.eq(src, r['name'] + ' >33', row['>33'], r['over33'])
        c.eq(src, r['name'] + ' >100', row['>100'], r['over100'])
        c.chk(src, r['name'] + ' window s', row['window s'], r['window_s'])
        c.chk(src, r['name'] + ' light', row['light'], r['light_share'], alts=c.light_alts(r))
        c.chk(src, r['name'] + ' cpu cores', row['cpu cores'], r['cores'],
              alts=[('run.json cpu_cores_mean', r['cores_rj']),
                    ('results.csv 3-dp cpu_cores_mean', r['cores_rc'], 'tie')])
    S = kept
    _, arows = table(lines, '| group | arm | ref |')
    for row in arows:
        arm = row['arm']
        c.eq(src, arm + ' n (kept)', row['n'], len(c.sel(arm, S)))
        m = RNG.match(col(row, 'median of medians') or '')
        st = c.st(arm, 'median_ms', S)
        for i, part in ((1, 'med'), (2, 'lo'), (3, 'hi')):
            c.chk(src, '%s median ms %s' % (arm, part), m.group(i), st[part])
        c.chk(src, arm + ' p99 ms', row['p99 ms'], c.st(arm, 'p99_ms', S)['med'])
        c.chk(src, arm + ' p99.9 ms', row['p99.9 ms'], c.st(arm, 'p999_ms', S)['med'])
        m = RNG.match(col(row, 'cpu cores') or '')
        sp, sr, s3 = c.st(arm, 'cores', S), c.st(arm, 'cores_rj', S), c.st(arm, 'cores_rc', S)
        for i, part in ((1, 'med'), (2, 'lo'), (3, 'hi')):
            c.chk(src, '%s cpu cores %s' % (arm, part), m.group(i), sp[part],
                  alts=[('run.json values', sr[part]), ('results.csv 3-dp values', s3[part], 'tie')])
        c.chk(src, arm + ' fps', row['fps'], c.st(arm, 'fps', S)['med'])
    _, drows = table(lines, '| group | arm | vs |')
    for row in drows:
        arm, ref = row['arm'], row['vs']
        a, b = c.st(arm, 'median_ms', S), c.st(ref, 'median_ms', S)
        m = re.match(r'(%s) \((%s)%%\)' % (NUM, NUM), col(row, 'delta median ms') or '')
        c.chk(src, '%s vs %s d median ms' % (arm, ref), m.group(1), a['med'] - b['med'])
        c.chk(src, '%s vs %s d median %%' % (arm, ref), m.group(2), 100 * (a['med'] / b['med'] - 1))
        m = re.match(r'(%s) \((%s)\.\.(%s)\), (\d+) of (\d+)' % (NUM, NUM, NUM), col(row, 'paired by round') or '')
        pm = c.pair(arm, ref, 'median_ms', S)
        c.chk(src, '%s vs %s paired median ms diff: median' % (arm, ref), m.group(1), pm['dif_med'])
        c.chk(src, '%s vs %s paired median ms diff: min' % (arm, ref), m.group(2), pm['dif_lo'])
        c.chk(src, '%s vs %s paired median ms diff: max' % (arm, ref), m.group(3), pm['dif_hi'])
        c.eq(src, '%s vs %s rounds faster' % (arm, ref), '%s of %s' % (m.group(4), m.group(5)),
             '%d of %d' % (pm['down'], pm['n']))
        c.chk(src, '%s vs %s d p99 ms' % (arm, ref), row['delta p99 ms'],
              c.st(arm, 'p99_ms', S)['med'] - c.st(ref, 'p99_ms', S)['med'])
        c.chk(src, '%s vs %s d cpu cores' % (arm, ref), row['delta cpu cores'],
              c.st(arm, 'cores', S)['med'] - c.st(ref, 'cores', S)['med'],
              alts=[('run.json medians', c.st(arm, 'cores_rj', S)['med'] - c.st(ref, 'cores_rj', S)['med']),
                    ('medians of the results.csv 3-dp values', c.st(arm, 'cores_rc', S)['med'] -
                     c.st(ref, 'cores_rc', S)['med'], 'tie')])
        c.chk(src, '%s vs %s d fps %%' % (arm, ref), row['delta fps %'],
              100 * (c.st(arm, 'fps', S)['med'] / c.st(ref, 'fps', S)['med'] - 1))
    c.parsed.append('%s: %d run rows (%d kept), %d arm rows, %d delta rows' % (src, len(rows), len(kept), len(arows),
                                                                            len(drows)))


# ---------------------------------------------------------------- Agent 1 (SESSION2, transcribed)

A1 = {
    'w4b': ('Agent 1 SESSION2 16:35', '19.6', [
        # arm, median, min, max, d median %, p99, fps, cpu
        ('d0', '3.40', '3.07', '3.73', None, '10.73', '239.7', '3.44'),
        ('B', '3.23', '2.88', '3.53', '-4.9', '10.50', '255.1', '3.35'),
        ('d3', '3.21', '2.89', '4.26', '-5.4', '10.49', '248.9', '3.38'),
        ('d11t', '3.36', '3.02', '3.86', '-1.1', '10.94', '237.7', '2.91')]),
    'w5': ('Agent 1 SESSION2 18:34', '20.4', [
        ('base', '2.55', '2.41', '2.93', None, '7.49', None, '3.17'),
        ('s0', '2.69', '2.52', '2.76', '5.5', '7.58', None, '3.22'),
        ('d11', '2.61', '2.56', '2.62', '2.6', '7.45', None, '3.17'),
        ('d11t', '2.65', '2.55', '3.03', '4.0', '7.84', None, '2.74'),
        ('d11p', '2.62', '2.58', '2.64', '3.1', '7.72', None, '2.75')]),
}


def check_agent1(c):
    src, noise, rows = A1[c.label]
    ref = c.cfg['ref']
    sr = c.st(ref, 'median_ms')
    for arm, med, lo, hi, dm, p99, fps, cpu in rows:
        st = c.st(arm, 'median_ms')
        c.chk(src, arm + ' median ms', med, st['med'], nd=2)
        c.chk(src, arm + ' median ms min', lo, st['lo'], nd=2)
        c.chk(src, arm + ' median ms max', hi, st['hi'], nd=2)
        if dm:
            c.chk(src, arm + ' d median %', dm, 100 * (st['med'] / sr['med'] - 1), nd=1)
        c.chk(src, arm + ' p99 ms', p99, c.st(arm, 'p99_ms')['med'], nd=2)
        if fps:
            c.chk(src, arm + ' fps', fps, c.st(arm, 'fps')['med'], nd=1)
        cp, cr = c.st(arm, 'cores'), c.st(arm, 'cores_rj')
        c.chk(src, arm + ' CPU cores', cpu, cp['med'], nd=2,
              alts=[('mean of the runs (run.json)', cr['mean']), ('mean of the runs (my proc.csv)', cp['mean'])])
    c.chk(src, 'noise band %', noise, 100 * (sr['hi'] - sr['lo']) / sr['med'], nd=1)
    scored = [r for r in c.runs if r['scored']]
    if c.label == 'w4b':
        b6 = c.st('B', 'median_ms', 'valid')
        c.chk(src, 'B median ms without run 6', '3.03', b6['med'], nd=2)
        c.chk(src, 'B d median % without run 6', '-10.8', 100 * (b6['med'] / sr['med'] - 1), nd=1)
        t, z = c.st('d11t', 'cores'), c.st('d0', 'cores')
        tr, zr = c.st('d11t', 'cores_rj'), c.st('d0', 'cores_rj')
        c.chk(src, 'd11t CPU vs d0 % ("2.91 (-15 %)")', '-15', 100 * (t['med'] / z['med'] - 1), nd=0,
              alts=[('means (run.json)', 100 * (tr['mean'] / zr['mean'] - 1))])
        c.chk(src, 'd11t vs d0 "~0.5 core less" (cores)', '0.5', z['med'] - t['med'], nd=1,
              alts=[('means (run.json)', zr['mean'] - tr['mean'])])
        bmin = min(c.sel('B'), key=lambda r: r['median_ms'])
        c.eq(src, "B's best run", '1545-B-r1', bmin['name'])
        c.chk(src, '1545-B-r1 median ms', '2.88', c.by['1545-B-r1']['median_ms'], nd=2)
        slow = max(scored, key=lambda r: r['median_ms'])
        c.eq(src, 'slowest run', '1600-d3-r3', slow['name'])
        c.chk(src, '1600-d3-r3 median ms', '4.26', c.by['1600-d3-r3']['median_ms'], nd=2)
        c.chk(src, '1600-d3-r3 light share', '0.51', c.by['1600-d3-r3']['light_share'], nd=2)
        c.eq(src, 'runs / scored', '17 / 16', '%d / %d' % (len(c.runs), len(scored)))
    else:
        tim = [r for r in scored if r['arm'] in ('d11t', 'd11p')]
        spin = [r for r in scored if r['arm'] in ('base', 's0', 'd11')]
        for lab, grp, lo, hi in (('d11t/d11p', tim, '2.67', '2.84'), ('base/s0/d11', spin, '2.90', '3.46')):
            c.chk(src, lab + ' per-run cores min', lo, min(r['cores'] for r in grp), nd=2,
                  alts=[('run.json', min(r['cores_rj'] for r in grp))])
            c.chk(src, lab + ' per-run cores max', hi, max(r['cores'] for r in grp), nd=2,
                  alts=[('run.json', max(r['cores_rj'] for r in grp))])
        mt = statistics.mean(r['cores_rj'] for r in tim)
        ms = statistics.mean(r['cores_rj'] for r in spin)
        bm = c.st('base', 'cores_rj')['mean']
        c.chk(src, '"~0.4 core less" (pooled run means, run.json)', '0.4', ms - mt, nd=1,
              alts=[('d11t mean vs base mean', bm - c.st('d11t', 'cores_rj')['mean']),
                    ('d11p mean vs base mean', bm - c.st('d11p', 'cores_rj')['mean'])])
        c.chk(src, '"about -13 %" (pooled run means, run.json)', '-13', 100 * (mt / ms - 1), nd=0,
              alts=[('d11t mean / base mean', 100 * (c.st('d11t', 'cores_rj')['mean'] / bm - 1)),
                    ('d11p mean / base mean', 100 * (c.st('d11p', 'cores_rj')['mean'] / bm - 1))])
        top3 = sorted(scored, key=lambda r: -r['median_ms'])[:3]
        c.eq(src, 'three slowest runs', '1817-base-r2, 1821-d11t-r3, 1808-s0-r2',
             ', '.join(r['name'] for r in sorted(top3, key=lambda r: ['1817-base-r2', '1821-d11t-r3',
                                                                      '1808-s0-r2'].index(r['name'])
                                                 if r['name'] in ('1817-base-r2', '1821-d11t-r3', '1808-s0-r2') else 9)))
        for nm, v in (('1817-base-r2', '2.931'), ('1821-d11t-r3', '3.028'), ('1808-s0-r2', '2.764'),
                      ('1757-base-r1', '2.411')):
            c.chk(src, nm + ' median ms', v, c.by[nm]['median_ms'], nd=3)
        c.eq(src, 'fastest run', '1757-base-r1', min(scored, key=lambda r: r['median_ms'])['name'])
        c.eq(src, 'runs / scored', '16 / 15', '%d / %d' % (len(c.runs), len(scored)))
        c.eq(src, 'frames over 33 ms (all 16 runs)', '0', sum(r['over33'] for r in c.runs))
    c.parsed.append('%s: transcribed table + sentences' % src)


# ---------------------------------------------------------------- CPU section

def cpu_compare_rows(c, comps, s='all'):
    out = []
    for arm, ref in comps:
        a, b = c.sel(arm, s), c.sel(ref, s)
        ra = {r['round']: r for r in a}
        rb = {r['round']: r for r in b}
        rounds = sorted(set(ra) & set(rb), key=int)
        sa, sb = c.st(arm, 'cores_rj', s), c.st(ref, 'cores_rj', s)
        dec = X.decide([r['cores_rj'] for r in a], [r['cores_rj'] for r in b], False)
        per = []
        for rd in rounds:
            x, y = ra[rd], rb[rd]
            per.append((rd, x['cores_rj'] - y['cores_rj'], x['cores_rj'] / y['cores_rj'] - 1,
                        x['median_ms'] / y['median_ms'] - 1, x['cpf'] / y['cpf'] - 1))
        out.append(dict(arm=arm, ref=ref, n=len(a), n_ref=len(b), med_d=sa['med'] - sb['med'],
                        med_rel=sa['med'] / sb['med'] - 1, mean_d=sa['mean'] - sb['mean'],
                        mean_rel=sa['mean'] / sb['mean'] - 1, dec=dec, per=per,
                        lower=sum(1 for p in per if p[1] < 0),
                        pmed=statistics.median([p[2] for p in per]) if per else None))
    return out


def cpu_section(c):
    L = []
    w = L.append
    arms = c.cfg['arms']
    w('## Game CPU check')
    w('')
    w('cores = game process CPU in the measure window: run.json window_cpu_cores_mean (= results.csv cpu_cores_mean = '
      'mean of the 1 s runner samples); my proc.csv mean (same samples, each rounded to 0.01) differs by at most '
      '%.4f cores (%.3f %%) over all runs. Tables below use the run.json value. Lower = less CPU. '
      'CPU ms per frame = cores x 1000 / fps (info only, my own derived number).' % (
          max(abs(r['cores'] - r['cores_rj']) for r in c.runs),
          100 * max(abs(r['cores'] / r['cores_rj'] - 1) for r in c.runs)))
    w('')
    w('| arm | n | cores median (min..max) | cores mean | TimerQueue busy % median | per run (round: cores / median ms / CPU ms per frame) |')
    w('|---|---|---|---|---|---|')
    sets = [('all', '')] + ([('valid', ' (without run 6)')] if c.label == 'w4b' else [])
    for s, suf in sets:
        for arm in arms:
            if s == 'valid' and arm != 'B':
                continue
            st = c.st(arm, 'cores_rj', s)
            tq = c.st(arm, 'tq_busy', s)
            w('| %s%s | %d | %.3f (%.3f..%.3f) | %.3f | %s | %s |' % (
                arm, suf, st['n'], st['med'], st['lo'], st['hi'], st['mean'], X.f(tq['med'] if tq else None, 1),
                '; '.join('r%s %.3f / %.3f / %.2f' % (r['round'], r['cores_rj'], r['median_ms'], r['cpf'])
                          for r in c.sel(arm, s))))
    w('')
    ref = c.cfg['ref']
    if c.label == 'w4b':
        comps = [(a, ref) for a in arms if a != ref]
    else:
        comps = [(a, ref) for a in arms if a != ref] + [(t, s) for t in ('d11t', 'd11p') for s in ('s0', 'd11')] + \
                [('d11p', 'd11t')]
    rows = cpu_compare_rows(c, comps)
    if c.label == 'w4b':
        rows += [dict(x, arm='B (without run 6)') for x in cpu_compare_rows(c, [('B', ref)], 'valid')]
    w('| arm vs ref | n vs n | d cores: medians (rel) | d cores: means (rel) | decision (cores, lower = better) | paired: rounds lower, median rel | per round: d cores (rel) | per round: d median ms rel | per round: d CPU ms per frame rel |')
    w('|---|---|---|---|---|---|---|---|---|')
    for x in rows:
        w('| %s vs %s | %d vs %d | %+.3f (%s) | %+.3f (%s) | %s | %d of %d, %s | %s | %s | %s |' % (
            x['arm'], x['ref'], x['n'], x['n_ref'], x['med_d'], X.pct(x['med_rel']), x['mean_d'], X.pct(x['mean_rel']),
            x['dec'], x['lower'], len(x['per']), X.pct(x['pmed']),
            ' '.join('r%s %+.3f (%s)' % (p[0], p[1], X.pct(p[2])) for p in x['per']),
            ' '.join('r%s %s' % (p[0], X.pct(p[3])) for p in x['per']),
            ' '.join('r%s %s' % (p[0], X.pct(p[4])) for p in x['per'])))
    w('')
    by = {(x['arm'], x['ref']): x for x in rows}
    if c.label == 'w4b':
        x = by[('d11t', 'd0')]
        t, z = c.st('d11t', 'cores_rj'), c.st('d0', 'cores_rj')
        w('Claim (Agent 1, 16:35): "d11t 2.91 (-15 %)" vs d0 3.44 cores, "~0.5 core less", frame time held.')
        w('')
        w('- means (the summary.md column): d11t %.3f vs d0 %.4f = %+.3f cores (%s); medians %.4f vs %.4f = %+.3f (%s).' % (
            t['mean'], z['mean'], t['mean'] - z['mean'], X.pct(t['mean'] / z['mean'] - 1), t['med'], z['med'],
            t['med'] - z['med'], X.pct(t['med'] / z['med'] - 1)))
        w('- every d11t run (%.3f..%.3f) is below d0\'s min (%.3f): decision "%s"; paired: lower in %d of %d rounds, %s (median %s).' % (
            t['lo'], t['hi'], z['lo'], x['dec'], x['lower'], len(x['per']),
            ', '.join('r%s %+.3f (%s)' % (p[0], p[1], X.pct(p[2])) for p in x['per']), X.pct(x['pmed'])))
        fm = c.st('d11t', 'median_ms')
        pf = c.pair('d11t', 'd0', 'fps')
        w('- frame time: d11t median %.4f vs %.4f ms (%s, overlap), paired fps %s (%d of %d rounds up).' % (
            fm['med'], c.st('d0', 'median_ms')['med'], X.pct(fm['med'] / c.st('d0', 'median_ms')['med'] - 1),
            X.pct(pf['rel_med']), pf['up'], pf['n']))
        w('- result: confirmed (-15.3 % on means and on medians; about 0.53 core; all 4 rounds lower; frame time within noise).')
    else:
        tim = [r for r in c.runs if r['scored'] and r['arm'] in ('d11t', 'd11p')]
        spin = [r for r in c.runs if r['scored'] and r['arm'] in ('base', 's0', 'd11')]
        mt = statistics.mean(r['cores_rj'] for r in tim)
        ms = statistics.mean(r['cores_rj'] for r in spin)
        w('Claim (Agent 1, 18:34): d11t and d11p use ~0.4 core less game CPU than base, s0 and d11 (2.67-2.84 vs 2.90-3.46 '
          'cores per run, about -13 %) at about the same frame time; it holds in all 3 rounds.')
        w('')
        w('- per-run ranges: d11t/d11p %.3f..%.3f, base/s0/d11 %.3f..%.3f (no overlap); pooled run means %.3f vs %.3f = '
          '%+.3f cores (%s).' % (min(r['cores_rj'] for r in tim), max(r['cores_rj'] for r in tim),
                                 min(r['cores_rj'] for r in spin), max(r['cores_rj'] for r in spin), mt, ms, mt - ms,
                                 X.pct(mt / ms - 1)))
        allp = []
        for t in ('d11t', 'd11p'):
            for s in ('base', 's0', 'd11'):
                x = by[(t, s)]
                allp += [(t, s) + p for p in x['per']]
                w('- %s vs %s: means %+.3f (%s), medians %+.3f (%s), decision %s; lower in %d of %d rounds: %s; '
                  'frame time (median ms) per round %s.' % (
                      t, s, x['mean_d'], X.pct(x['mean_rel']), x['med_d'], X.pct(x['med_rel']), x['dec'], x['lower'],
                      len(x['per']), ', '.join('r%s %+.3f (%s)' % (p[0], p[1], X.pct(p[2])) for p in x['per']),
                      ', '.join('r%s %s' % (p[0], X.pct(p[3])) for p in x['per'])))
        lo = min(allp, key=lambda p: -p[3])
        hi = min(allp, key=lambda p: p[3])
        w('- all %d round pairs (2 timer arms x 3 spin arms x 3 rounds): %d lower; smallest saving %s vs %s r%s %+.3f '
          '(%s), largest %s vs %s r%s %+.3f (%s); %d of %d round pairs save >= 0.3 core.' % (
              len(allp), sum(1 for p in allp if p[3] < 0), lo[0], lo[1], lo[2], lo[3], X.pct(lo[4]), hi[0], hi[1],
              hi[2], hi[3], X.pct(hi[4]), sum(1 for p in allp if p[3] <= -0.3), len(allp)))
        fr = [p for p in allp]
        w('- frame time in the same round pairs: median ms rel %s..%s; CPU ms per frame rel %s..%s (%d of %d lower).' % (
            X.pct(min(p[5] for p in fr)), X.pct(max(p[5] for p in fr)), X.pct(min(p[6] for p in fr)),
            X.pct(max(p[6] for p in fr)), sum(1 for p in fr if p[6] < 0), len(fr)))
    return L


# ---------------------------------------------------------------- main

def main():
    label = sys.argv[1] if len(sys.argv) > 1 else 'w4b'
    c = Ctx(label)
    check_summary(c)
    if label == 'w4b':
        check_addon(c, P('build', 'agent8', 'readout', 'w4b', 'w4b.json'), 'Agent 8 w4b.json (add-on)')
        check_r5(c, P('build', 'agent8', 'readout', 'w5-dry-1541', 'rules-nodrop.md'),
                 'Agent 8 w5-dry-1541/rules-nodrop.md', 'valid')
        check_r7(c, P('build', 'agent8', 'readout', 'w5-dry-1541', 'rules-nodrop.md'),
                 'Agent 8 w5-dry-1541/rules-nodrop.md')
        check_r7(c, P('build', 'agent8', 'readout', 'w4b', 'rules.md'), 'Agent 8 w4b/rules.md')
        check_recheck(c, P('build', 'agent8', 'readout', 'w4b', 'recheck.txt'), 'Agent 8 w4b/recheck.txt')
    else:
        check_addon(c, P('build', 'agent8', 'readout', 'w5', 'w5.json'), 'Agent 8 w5.json (add-on)')
        check_addon(c, P('build', 'agent8', 'readout', 'w5', 'w5-s0.json'), 'Agent 8 w5-s0.json (add-on, ref s0)')
        check_r5(c, P('build', 'agent8', 'readout', 'w5', 'rules-nodrop.md'), 'Agent 8 w5/rules-nodrop.md', 'valid')
        check_r7(c, P('build', 'agent8', 'readout', 'w5', 'rules-nodrop.md'), 'Agent 8 w5/rules-nodrop.md')
        check_r7(c, P('build', 'agent8', 'readout', 'w5', 'rules.md'), 'Agent 8 w5/rules.md')
        check_recheck(c, P('build', 'agent8', 'readout', 'w5', 'recheck.txt'), 'Agent 8 w5/recheck.txt')
    check_agent1(c)

    out = c.cfg['out']
    with open(os.path.join(out, 'xcheck_compare.csv'), 'w', newline='', encoding='utf-8') as fh:
        wr = csv.writer(fh)
        wr.writerow(['source', 'item', 'published', 'recomputed', 'result', 'note'])
        for r in c.rows:
            wr.writerow([r['src'], r['item'], r['shown'], r['mine'], r['res'], r['note']])
    with open(os.path.join(out, 'xcheck_core.md'), encoding='utf-8') as fh:
        core = fh.read().rstrip('\n').split('\n')
    L = list(core)
    w = L.append
    w('')
    w('## Comparison with the published numbers')
    w('')
    w('Rule: ok = the published value is a correct rounding of my value (within half a unit of its last printed digit; '
      'JSON floats equal to 1e-9 relative, or within 0.1 % with the diff noted); definition = not ok, but a correct '
      'rounding under the named alternative definition; rounding tie = not ok against my exact value, but a correct '
      'rounding of an intermediate value that sits exactly on the rounding boundary (the runner\'s 4-dp light share in '
      'frames.json, or a difference/median of the 3-dp results.csv values), so both roundings are legitimate; '
      'MISMATCH = none of these. Full list: xcheck_compare.csv.')
    w('')
    w('| source | numbers | ok | definition | rounding tie | MISMATCH | not checked |')
    w('|---|---|---|---|---|---|---|')
    srcs = []
    for r in c.rows:
        if r['src'] not in srcs:
            srcs.append(r['src'])
    for s in srcs:
        rr = [r for r in c.rows if r['src'] == s]
        w('| %s | %d | %d | %d | %d | %d | %d |' % (s, len(rr), sum(r['res'] == 'ok' for r in rr),
                                              sum(r['res'] == 'definition' for r in rr),
                                              sum(r['res'] == 'rounding tie' for r in rr),
                                              sum(r['res'] == 'MISMATCH' for r in rr),
                                              sum(r['res'] == 'NOT CHECKED' for r in rr)))
    w('')
    w('Parsed: ' + '; '.join(c.parsed))
    w('')
    w('### Every number that is not ok')
    w('')
    bad = [r for r in c.rows if r['res'] != 'ok']
    noted = [r for r in c.rows if r['res'] == 'ok' and r['note']]
    if not bad:
        w('- none')
    else:
        w('| source | item | published | recomputed (mine) | result | note |')
        w('|---|---|---|---|---|---|')
        for r in bad:
            w('| %s | %s | %s | %s | %s | %s |' % (r['src'], r['item'], r['shown'], r['mine'], r['res'], r['note']))
    if noted:
        w('')
        w('JSON floats within 0.1 %% but not identical: %d (%s)' % (
            len(noted), '; '.join('%s %s %s' % (r['src'], r['item'], r['note']) for r in noted[:12])))
    w('')
    L += cpu_section(c)
    with open(os.path.join(out, 'xcheck.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')
    print('\n'.join(L[len(core):]))


if __name__ == '__main__':
    main()
