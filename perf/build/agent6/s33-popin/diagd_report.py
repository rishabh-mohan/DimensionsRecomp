#!/usr/bin/env python3
"""#33 diagnostic (d) report: resolves that follow dropped draws (Agent 6). Read-only.

With cvar d3d12_resolve_after_drop_log on (s33-diagd-on-nohunk5.patch), game.log
gets INFO lines (counters cumulative per run, dest = RB_COPY_DEST_BASE):
  resolve after drop: dest XXXXXXXX after N skipped draws (new|again) | resolves R, after drops A, healed H, tainted T
  resolve after drop: dest XXXXXXXX resolved clean again | resolves R, after drops A, healed H, tainted T
  resolve after drop: 4096 lines logged, no more from here on
A dest is tainted when a resolve to it follows >= 1 skipped draw, healed when it
is next resolved with no skipped draw in between. A dest still tainted at the end
of the log is a render-to-texture result that may have stayed wrong.

Per run: diag lines, cap hit, final counters, per-dest taints / heals / heal
latency / tainted at end, and consistency checks (replay of the events against
the counters in each line; WARN, never a crash). Per arm: totals and the union of
dests tainted at end. Heal latency is measured from the start of the taint
episode (the "new" line) to the heal: resolves = ordinal difference, seconds =
log timestamp difference. After a cap hit nothing more is logged, so state at
the end is "as of the cap".

Usage: python -B diagd_report.py [--out FILE] [--json FILE] [--arm NAME=PATH]...
                                 <game.log | run dir | matrix dir>...
  run dir = a dir with game*.log (and run.json); matrix dir = a dir with runs/*/.
  A run's log is all its rotations read as one stream, oldest first (game.N.log
  with the highest N first, game.log last); a game*.log given as a file is read
  alone. --arm NAME=PATH (repeatable) adds PATH as an input and labels all its
  runs NAME. Otherwise the arm is run.json "arm" or "id", else the run dir name
  (HHMM-<arm>[-...] or HHMM-cold-<arm>[-...], arm [A-Za-z0-9]+; a cold arm stays
  its own arm), else a harness dir name YYYYMMDD-HHMMSS-<tag>, else run.json
  "tag", else the dir name. A tag loses a leading "s33-", then gives
  [cold-]<arm> the same way (tag "s33-ond" -> arm "ond").
Exit:  0 parsed fine (tainted dests are a measurement, not an error),
       1 a consistency WARN occurred, 2 usage error / no input.
"""
import glob
import json
import math
import os
import re
import statistics
import sys
from datetime import datetime

PREFIX_RE = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d(?:\.\d+)?)\] \[\w+\] \[\w+\] '
                       r'(?:\[t\d+\] )?(.*?)\s*$')
MARK = 'resolve after drop:'
TAINT_RE = re.compile(r'^resolve after drop: dest ([0-9A-F]{8}) after (\d+) skipped draws '
                      r'\((new|again)\) \| resolves (\d+), after drops (\d+), healed (\d+), '
                      r'tainted (\d+)$')
HEAL_RE = re.compile(r'^resolve after drop: dest ([0-9A-F]{8}) resolved clean again \| '
                     r'resolves (\d+), after drops (\d+), healed (\d+), tainted (\d+)$')
CAP_RE = re.compile(r'^resolve after drop: (\d+) lines logged, no more from here on$')
ROT_RE = re.compile(r'^game(?:\.(\d+))?\.log$', re.I)      # as w6_kit.py
RUN_RE = re.compile(r'^\d{4}-(cold-[A-Za-z0-9]+|[A-Za-z0-9]+)(?:-|$)')   # w6_kit ARM_RE
HARNESS_RE = re.compile(r'^\d{8}-\d{6}-(.+)$')
TAG_RE = re.compile(r'^(cold-[A-Za-z0-9]+|[A-Za-z0-9]+)(?:-|$)')
MAX_WARN_LINES = 12


def parse_ts(s):
    fmt = '%Y-%m-%d %H:%M:%S.%f' if '.' in s else '%Y-%m-%d %H:%M:%S'
    return datetime.strptime(s, fmt).timestamp()


def hms(t):
    if t is None:
        return '-'
    return datetime.fromtimestamp(t).strftime('%H:%M:%S.%f')[:-3]


def lat_stats(vals):
    """n, median, p95 (nearest rank), max; None fields when empty."""
    if not vals:
        return {'n': 0, 'median': None, 'p95': None, 'max': None}
    s = sorted(vals)
    return {'n': len(s), 'median': statistics.median(s),
            'p95': s[max(0, math.ceil(0.95 * len(s)) - 1)], 'max': s[-1]}


def fmt_stats(st, nd):
    if not st['n']:
        return '-'
    f = '%.' + str(nd) + 'f'
    return '/'.join(f % st[k] for k in ('median', 'p95', 'max'))


def load_json(path):
    try:
        with open(path, encoding='utf-8-sig') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def tag_arm(tag):
    tag = str(tag)
    if tag.lower().startswith('s33-'):
        tag = tag[4:]
    m = TAG_RE.match(tag)
    return (m.group(1) if m else tag).lower()


def arm_of(run_dir):
    rj = load_json(os.path.join(run_dir, 'run.json'))
    for k in ('arm', 'id'):
        if rj.get(k):
            return str(rj[k]).lower()
    name = os.path.basename(os.path.normpath(run_dir))
    m = RUN_RE.match(name)
    if m:
        return m.group(1).lower()
    m = HARNESS_RE.match(name)
    if m:
        return tag_arm(m.group(1))
    if rj.get('tag'):
        return tag_arm(rj['tag'])
    return name.lower()


def find_logs(run_dir):
    """All game[.N].log rotations, oldest first (highest N first, game.log last)."""
    found = []
    for p in glob.glob(os.path.join(run_dir, 'game*.log')):
        m = ROT_RE.match(os.path.basename(p))
        if m:
            found.append((int(m.group(1)) if m.group(1) else 0, p))
    found.sort(key=lambda t: -t[0])
    return [p for _, p in found]


def collect_runs(inputs):
    """inputs: [(path, forced arm or None)] -> [(name, arm, logs)]; ValueError on a bad path."""
    runs = []
    for p, forced in inputs:
        if os.path.isfile(p):
            d = os.path.dirname(os.path.abspath(p))
            runs.append((os.path.basename(d), forced or arm_of(d), [p]))
        elif os.path.isdir(os.path.join(p, 'runs')):
            root = os.path.join(p, 'runs')
            for n in sorted(os.listdir(root)):
                d = os.path.join(root, n)
                if os.path.isdir(d):
                    runs.append((n, forced or arm_of(d), find_logs(d)))
        elif os.path.isdir(p):
            d = os.path.abspath(p)
            runs.append((os.path.basename(d), forced or arm_of(d), find_logs(d)))
        else:
            raise ValueError('no such file or dir: %s' % p)
    return runs


def stream(logs):
    """(where, raw line) over all files, as one stream."""
    for log in logs:
        with open(log, encoding='utf-8', errors='replace') as f:
            for ln, raw in enumerate(f, 1):
                yield '%s:%d' % (os.path.basename(log), ln), raw


def analyse(name, arm, logs):
    r = {'name': name, 'arm': arm, 'logs': logs, 'lines': 0, 'cap_hit': False,
         'final': None, 'dests': {}, 'still_tainted': [], 'warns': [], 'end_time': None}
    warn = r['warns'].append
    if not logs:
        warn('no game*.log in run dir')
        r['latency'] = {'resolves': lat_stats([]), 'seconds': lat_stats([])}
        return r
    tainted = {}          # dest -> (episode start ordinal, time)
    after = healed = 0    # replayed counters
    last_ord = 0
    events = 0
    cap_n = None
    lat_res, lat_s = [], []
    for where, raw in stream(logs):
        pm = PREFIX_RE.match(raw)
        t = None
        if pm:
            try:
                t = parse_ts(pm.group(1))
                r['end_time'] = t
            except ValueError:
                t = None
        if MARK not in raw:
            continue
        if not pm or t is None:
            warn('%s: malformed (no log prefix/timestamp): %r' % (where, raw.strip()[:120]))
            continue
        msg = pm.group(2)
        r['lines'] += 1
        if cap_n is not None:
            warn('%s: diag line after the cap line' % where)
        cm = CAP_RE.match(msg)
        if cm:
            cap_n = int(cm.group(1))
            r['cap_hit'] = True
            if events != cap_n:
                warn('%s: cap says %d lines, %d event lines seen' % (where, cap_n, events))
            continue
        tm, hm = TAINT_RE.match(msg), HEAL_RE.match(msg)
        if not tm and not hm:
            warn('%s: malformed diag line: %r' % (where, msg[:120]))
            continue
        events += 1
        if tm:
            dest, drops, kind = tm.group(1), int(tm.group(2)), tm.group(3)
            ords, a, h, tsz = (int(x) for x in tm.group(4, 5, 6, 7))
        else:
            dest, drops, kind = hm.group(1), 0, 'heal'
            ords, a, h, tsz = (int(x) for x in hm.group(2, 3, 4, 5))
        if ords <= last_ord:
            warn('%s: resolves ordinal %d not after previous %d' % (where, ords, last_ord))
        last_ord = max(last_ord, ords)
        d = r['dests'].setdefault(dest, {
            'taints': 0, 'episodes': 0, 'heals': 0, 'lat_resolves': [], 'lat_seconds': [],
            'tainted_at_end': False, 'first': t, 'last': t, 'last_taint': None})
        d['last'] = t
        if tm:
            after += 1
            d['taints'] += 1
            d['last_taint'] = t
            if drops < 1:
                warn('%s: taint with %d skipped draws' % (where, drops))
            if (kind == 'new') != (dest not in tainted):
                warn('%s: dest %s logged %s but replay has it %s' % (
                    where, dest, kind, 'tainted' if dest in tainted else 'clean'))
            if dest not in tainted:
                tainted[dest] = (ords, t)
                d['episodes'] += 1
        else:
            healed += 1
            if dest in tainted:
                o0, t0 = tainted.pop(dest)
                d['heals'] += 1
                d['lat_resolves'].append(ords - o0)
                d['lat_seconds'].append(t - t0)
                lat_res.append(ords - o0)
                lat_s.append(t - t0)
            else:
                warn('%s: heal of dest %s that replay has clean' % (where, dest))
        for label, got, want in (('after drops', a, after), ('healed', h, healed),
                                 ('tainted', tsz, len(tainted))):
            if got != want:
                warn('%s: %s %d in line, replay %d' % (where, label, got, want))
        r['final'] = {'resolves': ords, 'after_drops': a, 'healed': h, 'tainted': tsz}
    for dest, (o0, t0) in sorted(tainted.items()):
        d = r['dests'][dest]
        d['tainted_at_end'] = True
        r['still_tainted'].append({
            'dest': dest, 'episode_start': t0, 'since_last_taint_s': r['end_time'] - d['last_taint'],
            'healed_before': d['heals'] > 0})
    r['latency'] = {'resolves': lat_stats(lat_res), 'seconds': lat_stats(lat_s)}
    r['_lat'] = (lat_res, lat_s)
    return r


def report_run(r, w):
    logs = r['logs']
    where = '-' if not logs else logs[0].replace('\\', '/') + (
        '' if len(logs) == 1 else ' (+ %s)' % ', '.join(os.path.basename(p) for p in logs[1:]))
    w('== run %s  (arm %s)  %s' % (r['name'], r['arm'], where))
    fin = r['final']
    fin_s = ('resolves %(resolves)d, after drops %(after_drops)d, healed %(healed)d, '
             'tainted %(tainted)d' % fin) if fin else '(no event lines)'
    w('   diag lines %d, cap hit %s, final: %s' % (r['lines'], 'yes' if r['cap_hit'] else 'no', fin_s))
    if r['dests']:
        w('   %-8s %6s %4s %5s %-17s %-23s %-6s %-12s %-12s' % (
            'dest', 'taints', 'eps', 'heals', 'lat res med/max', 'lat s med/max', 'end', 'first', 'last'))
        for dest, d in sorted(r['dests'].items()):
            sr, ss = lat_stats(d['lat_resolves']), lat_stats(d['lat_seconds'])
            lr = '%g/%g' % (sr['median'], sr['max']) if sr['n'] else '-'
            ls = '%.3f/%.3f' % (ss['median'], ss['max']) if ss['n'] else '-'
            w('   %-8s %6d %4d %5d %-17s %-23s %-6s %-12s %-12s' % (
                dest, d['taints'], d['episodes'], d['heals'], lr, ls,
                'TAINT' if d['tainted_at_end'] else 'ok', hms(d['first']), hms(d['last'])))
    st = r['still_tainted']
    w('   distinct dests tainted %d; still tainted at end %d%s%s' % (
        len(r['dests']), len(st), ': ' if st else '',
        '; '.join('%s (last taint %.3f s before end, %s)' % (
            s['dest'], s['since_last_taint_s'], 'healed before' if s['healed_before'] else 'never healed')
            for s in st)))
    if r['cap_hit'] and st:
        w('   note: cap hit, so the state at end is as of the cap line')
    lat = r['latency']
    w('   heal latency: n %d, resolves med/p95/max %s, seconds med/p95/max %s' % (
        lat['resolves']['n'], fmt_stats(lat['resolves'], 1), fmt_stats(lat['seconds'], 3)))
    for msg in r['warns'][:MAX_WARN_LINES]:
        w('   WARN %s' % msg)
    if len(r['warns']) > MAX_WARN_LINES:
        w('   WARN ... %d more' % (len(r['warns']) - MAX_WARN_LINES))


def summarise_arms(runs):
    arms = {}
    for r in runs:
        a = arms.setdefault(r['arm'], {
            'runs': 0, 'with_diag': 0, 'cap_hits': 0, 'warn_runs': 0, 'resolves': 0,
            'after_drops': 0, 'healed': 0, 'tainted_at_end': 0, 'end_dests': {},
            '_res': [], '_s': []})
        a['runs'] += 1
        a['with_diag'] += r['lines'] > 0
        a['cap_hits'] += r['cap_hit']
        a['warn_runs'] += bool(r['warns'])
        if r['final']:
            for k in ('resolves', 'after_drops', 'healed'):
                a[k] += r['final'][k]
        a['tainted_at_end'] += len(r['still_tainted'])
        for s in r['still_tainted']:
            e = a['end_dests'].setdefault(s['dest'], {'runs': 0, 'never_healed_runs': 0})
            e['runs'] += 1
            e['never_healed_runs'] += not s['healed_before']
        res, sec = r.get('_lat', ([], []))
        a['_res'] += res
        a['_s'] += sec
    for a in arms.values():
        a['latency'] = {'resolves': lat_stats(a.pop('_res')), 'seconds': lat_stats(a.pop('_s'))}
    return arms


def report_arms(arms, w):
    for name, a in sorted(arms.items()):
        w('-- arm %s: runs %d (with diag lines %d, cap hit %d, with WARN %d); totals: resolves %d, '
          'after drops %d, healed %d, tainted at end %d' % (
              name, a['runs'], a['with_diag'], a['cap_hits'], a['warn_runs'], a['resolves'],
              a['after_drops'], a['healed'], a['tainted_at_end']))
        lat = a['latency']
        w('   heal latency: n %d, resolves med/p95/max %s, seconds med/p95/max %s' % (
            lat['resolves']['n'], fmt_stats(lat['resolves'], 1), fmt_stats(lat['seconds'], 3)))
        ed = a['end_dests']
        w('   dests tainted at end (union): %s' % (', '.join(
            '%s in %d/%d runs (never healed in %d)' % (d, e['runs'], a['runs'], e['never_healed_runs'])
            for d, e in sorted(ed.items(), key=lambda kv: (-kv[1]['runs'], kv[0]))) or 'none'))


def main(argv):
    out_path = json_path = None
    inputs = {}   # normalised path -> (path, forced arm or None); --arm wins
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ('--out', '--json', '--arm'):
            if i + 1 >= len(argv):
                print(__doc__)
                return 2
            v = argv[i + 1]
            if a == '--out':
                out_path = v
            elif a == '--json':
                json_path = v
            else:
                name, sep, path = v.partition('=')
                if not sep or not name.strip() or not path.strip():
                    print('error: --arm wants NAME=PATH, got %r' % v)
                    return 2
                inputs[os.path.normcase(os.path.abspath(path))] = (path, name.strip().lower())
            i += 2
            continue
        if a.startswith('-'):
            print(__doc__)
            return 2
        inputs.setdefault(os.path.normcase(os.path.abspath(a)), (a, None))
        i += 1
    if not inputs:
        print(__doc__)
        return 2
    try:
        found = collect_runs(list(inputs.values()))
    except ValueError as e:
        print('error: %s' % e)
        return 2
    if not found:
        print('error: no runs found in %s' % ', '.join(p for p, _ in inputs.values()))
        return 2
    lines = []

    def w(s):
        print(s)
        lines.append(s)

    w('#33 diag (d) resolve-after-drop report (build/agent6/s33-popin/diagd_report.py)')
    w('eps = taint episodes ("new"); lat = heal latency from episode start, in resolves and '
      'seconds; end = TAINT if still tainted at end of log.')
    w('')
    runs = [analyse(*x) for x in found]
    for r in runs:
        report_run(r, w)
    w('')
    arms = summarise_arms(runs)
    report_arms(arms, w)
    nwarn = sum(len(r['warns']) for r in runs)
    w('TOTAL: %d run(s), %d arm(s), %d WARN(s)' % (len(runs), len(arms), nwarn))
    if out_path:
        with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(lines) + '\n')
    if json_path:
        for r in runs:
            r.pop('_lat', None)
        with open(json_path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump({'runs': runs, 'arms': arms}, f, indent=1, sort_keys=True)
            f.write('\n')
    return 1 if nwarn else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
