"""f10_results.py - Agent 3, task #23 (11-23): the numbers for build/agent3/f10/RESULTS.md.

Question (Agent 1): the four L1-poll hangs (gate A, s4b-24, s4b-20, gate B) all ran under Agent 2's -j8 build. Do they
happen on a quiet host? Rows f10a (s4b20's set, C1 OFF) and f10b (gate B's set, p2fc), untimed vpad L route + tags,
slow_frame_log_ms=1.

Per run (read-only on the run folder):
  hang: STUCK-LOCK events (lines <= 3 s apart = one event), the owner lr ("parked at lr="; finding 10 = owner in
        sub_83FAF180, 83FAF180-83FAF25F), [FATAL] lines, *.dmp files;
  slow frames: every "slow frame #N: X ms | ..." line (with slow_frame_log_ms=1 that is nearly every frame), buckets
        >= 100 ms / >= 1 s / >= 4 s, the largest frames with host-gpu wait (ms, count, ms per wait), memexport syncs
        (count, KB), on-demand syncs, P2's full-buffer counter and gpu-thread idle;
  route: input.csv marks (vortex = the level was reached), Toy Pad LOAD lines, run.json exit/close;
  host: sys.csv cpu_util_pct (median over the run, max over [-10, +2] s around each hang and the largest frame) and
        build/agent3/s4b/logs/hostload*.csv rows during the run (compiler process counts).
Usage: python -B f10_results.py [--json OUT.json] [--md OUT.md] label=RUN_DIR [label=RUN_DIR ...]
"""
import argparse
import csv
import datetime
import glob
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOSTLOAD_GLOB = os.path.join(HERE, '..', 's4b', 'logs', 'hostload*.csv')
TS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d(?:\.\d+)?)\]')
SLOW = re.compile(r'slow frame #(\d+): ([\d.]+) ms \| (.*)$')
F_WAIT = re.compile(r'host-gpu wait ([\d.]+) \((\d+)x\)')
F_IDLE = re.compile(r'gpu-thread idle ([\d.]+)')
F_SYNC = re.compile(r'memexport syncs (\d+) \((\d+) KB\)')
F_OD = re.compile(r'on demand (\d+) \((\d+) KB\)')
F_FB = re.compile(r'memexport full-buffer (\d+)x \(total (\d+)\)')
OWNER_LR = re.compile(r'parked at lr[=: ]+(?:0x)?([0-9A-Fa-f]{8})\b')


def ts(s):
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def rows(path):
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8-sig', errors='replace') as f:
        return list(csv.DictReader(f))


def logs_in_order(run):
    rot = []
    for p in glob.glob(os.path.join(run, 'game.*.log')):
        m = re.search(r'game\.(\d+)\.log$', p)
        if m:
            rot.append((int(m.group(1)), p))
    out = [p for _n, p in sorted(rot, reverse=True)]   # game.8.log (oldest) ... game.1.log
    if os.path.exists(os.path.join(run, 'game.log')):
        out.append(os.path.join(run, 'game.log'))
    return out


def pct(vals, q):
    if not vals:
        return None
    s = sorted(vals)
    return s[min(len(s) - 1, int(round(q * (len(s) - 1))))]


def scan(label, run):
    frames, stuck, fatal, loads, first, last = [], [], 0, 0, None, None
    for p in logs_in_order(run):
        with open(p, encoding='utf-8', errors='replace') as f:
            for line in f:
                m = TS.match(line)
                t = ts(m.group(1)) if m else None
                if t:
                    first = first or t
                    last = t
                if 'slow frame #' in line:
                    s = SLOW.search(line)
                    if s:
                        rest = s.group(3)
                        fr = {'n': int(s.group(1)), 'ms': float(s.group(2)), 't': t}
                        for key, rx, conv in (('w', F_WAIT, None), ('idle', F_IDLE, None), ('sync', F_SYNC, None),
                                              ('od', F_OD, None), ('fb', F_FB, None)):
                            mm = rx.search(rest)
                            fr[key] = mm.groups() if mm else None
                        frames.append(fr)
                    continue
                if 'STUCK-LOCK' in line and t:
                    stuck.append((t, line.rstrip()))
                elif '[FATAL]' in line:
                    fatal += 1
                elif 'Toypad listener: LOAD ->' in line:
                    loads += 1
    # STUCK-LOCK events
    events = []
    for t, line in sorted(stuck, key=lambda x: x[0]):
        if events and (t - events[-1][-1][0]).total_seconds() <= 3:
            events[-1].append((t, line))
        else:
            events.append([(t, line)])
    rj = {}
    if os.path.exists(os.path.join(run, 'run.json')):
        with open(os.path.join(run, 'run.json'), encoding='utf-8-sig') as f:
            rj = json.load(f)
    marks = [(r.get('args'), fnum(r.get('t_s'))) for r in rows(os.path.join(run, 'input.csv')) if r.get('cmd') == 'mark']
    sysrows = [(fnum(r.get('epoch_s')), fnum(r.get('cpu_util_pct'))) for r in rows(os.path.join(run, 'sys.csv'))]
    sysrows = [(e, c) for e, c in sysrows if e is not None and c is not None]

    def cpu_around(dt, before=10, after=2):
        if dt is None:
            return None
        e0 = dt.timestamp()
        w = [c for e, c in sysrows if e0 - before <= e <= e0 + after]
        return round(max(w), 1) if w else None

    # hostload rows during the run (time of day only: combine with the run's start date)
    hl = []
    start_e = fnum(rj.get('started_epoch_s'))
    if start_e:
        day = datetime.datetime.fromtimestamp(start_e).date()
        end_e = start_e + (fnum(rj.get('elapsed_s')) or 0)
        for path in sorted(glob.glob(HOSTLOAD_GLOB)):
            for r in rows(path):
                try:
                    tt = datetime.datetime.combine(day, datetime.datetime.strptime(r.get('time') or '', '%H:%M:%S').time())
                except ValueError:
                    continue
                if start_e - 60 <= tt.timestamp() <= end_e + 60:
                    busy = sum(int(fnum(r.get(k)) or 0) for k in ('clang', 'cl', 'ninja', 'link'))
                    hl.append({'time': r.get('time'), 'e': tt.timestamp(), 'busy': busy, 'cpu': fnum(r.get('cpu_pct')),
                               'top': r.get('top') or '', 'file': os.path.basename(path),
                               'inrun': start_e <= tt.timestamp() <= end_e})
    hl_near = hl
    hl = [h for h in hl if h['inrun']]
    hl_cpu = [h['cpu'] for h in hl if h['cpu'] is not None]
    ev_out = []
    for ev in events:
        lrs = sorted(set(m.group(1).upper() for _t, line in ev for m in OWNER_LR.finditer(line)))
        e0 = ev[0][0].timestamp()
        ev_out.append({'at': ev[0][0].strftime('%H:%M:%S.%f')[:-3], 'lines': len(ev), 'owner_lr': lrs,
                       'finding10': (bool(lrs) and all(0x83FAF180 <= int(x, 16) <= 0x83FAF25F for x in lrs)) if lrs else None,
                       'cpu_util_max_m10_p2': cpu_around(ev[0][0]),
                       # task #23: hostload rows within +-60 s of the hang (LoadPercentage %, compiler counts, top 4)
                       'hostload_pm60': ['%s cpu %s%% busy %s%s' % (h['time'], h['cpu'], h['busy'],
                                                                   (' top ' + h['top']) if h['top'] else '')
                                         for h in hl_near if abs(h['e'] - e0) <= 60]})

    def row_of(fr):
        w_ms, w_n = (float(fr['w'][0]), int(fr['w'][1])) if fr['w'] else (None, None)
        sy, sykb = (int(fr['sync'][0]), int(fr['sync'][1])) if fr['sync'] else (None, None)
        return {'frame': fr['n'], 'at': fr['t'].strftime('%H:%M:%S.%f')[:-3] if fr['t'] else None, 'ms': fr['ms'],
                'wait_ms': w_ms, 'waits': w_n, 'ms_per_wait': round(w_ms / w_n, 2) if w_ms is not None and w_n else None,
                'syncs': sy, 'sync_kb': sykb, 'on_demand': int(fr['od'][0]) if fr['od'] else None,
                'full_buffer': int(fr['fb'][0]) if fr['fb'] else None,
                'gpu_idle_ms': float(fr['idle'][0]) if fr['idle'] else None, 'cpu_util_max_m10_p2': cpu_around(fr['t'])}

    ms = [fr['ms'] for fr in frames]
    waits = [float(fr['w'][0]) for fr in frames if fr['w']]
    mpw = [float(fr['w'][0]) / int(fr['w'][1]) for fr in frames if fr['w'] and int(fr['w'][1]) >= 100]
    syncs = [int(fr['sync'][0]) for fr in frames if fr['sync']]
    fbt = [int(fr['fb'][1]) for fr in frames if fr['fb']]
    top = sorted(frames, key=lambda fr: -fr['ms'])
    res = {
        'label': label, 'run': os.path.basename(os.path.normpath(run)), 'logs': [os.path.basename(p) for p in logs_in_order(run)],
        'exit_code': rj.get('exit_code'), 'close_s': rj.get('close_seconds'), 'elapsed_s': rj.get('elapsed_s'),
        'cvars': rj.get('cvars'), 'dumps': sorted(os.path.basename(p) for p in glob.glob(os.path.join(run, '*.dmp'))),
        'stuck_events': ev_out, 'stuck_lines': len(stuck), 'fatal_lines': fatal, 'hang': bool(events),
        'toypad_load_lines': loads, 'marks_last': marks[-1][0] if marks else None,
        'vortex': any(m == 'vortex' for m, _t in marks), 'marks_n': len(marks),
        'cpu_util_median_run': round(statistics.median([c for _e, c in sysrows]), 1) if sysrows else None,
        'hostload_rows': len(hl), 'hostload_busy_rows': sum(1 for h in hl if h['busy']),
        'hostload_files': sorted(set(h['file'] for h in hl)),
        'hostload_cpu': {'median': statistics.median(hl_cpu) if hl_cpu else None, 'max': max(hl_cpu) if hl_cpu else None},
        'slow_frames': len(frames), 'ge100ms': sum(1 for x in ms if x >= 100), 'ge1s': sum(1 for x in ms if x >= 1000),
        'ge4s': sum(1 for x in ms if x >= 4000), 'max_frame_ms': max(ms) if ms else None,
        'wait_per_frame_ms': {'median': pct(waits, 0.5), 'p90': pct(waits, 0.9), 'p99': pct(waits, 0.99),
                              'max': max(waits) if waits else None, 'sum_s': round(sum(waits) / 1000, 1) if waits else None},
        'ms_per_wait_frames_ge100_waits': {'n': len(mpw), 'median': round(pct(mpw, 0.5), 2) if mpw else None,
                                           'max': round(max(mpw), 2) if mpw else None},
        'memexport_syncs': {'total': sum(syncs) if syncs else None, 'max_per_frame': max(syncs) if syncs else None,
                            'frames_with_syncs': sum(1 for s in syncs if s)},
        'full_buffer_total_last': fbt[-1] if fbt else None, 'full_buffer_total_max': max(fbt) if fbt else None,
        'top_frames': [row_of(fr) for fr in top[:5]],
        'stall_frames_ge1s': [row_of(fr) for fr in frames if fr['ms'] >= 1000][:20],
        'log_first': first.strftime('%H:%M:%S') if first else None, 'log_last': last.strftime('%H:%M:%S') if last else None,
    }
    return res


def md(results):
    o = ['| run | folder | exit | hang (STUCK-LOCK events, owner lr) | dumps | slow-frame lines | >=100 ms / >=1 s / >=4 s | '
         'max frame ms | host-gpu wait per frame ms (median / p99 / max) | ms per wait (frames >= 100 waits: median / max) | '
         'memexport syncs (total / max per frame) | P2 full-buffer total | tags LOAD lines | last mark (vortex?) | '
         'cpu_util median | hostload busy rows | hostload cpu % (median / max) |', '|' + '---|' * 17]
    for r in results:
        hang = 'no' if not r['hang'] else 'YES: ' + '; '.join(
            '%s x%d lr %s%s' % (e['at'], e['lines'], ','.join(e['owner_lr']) or '?', ' (finding 10)' if e['finding10'] else '')
            for e in r['stuck_events'])
        w, mp, sy, hc = r['wait_per_frame_ms'], r['ms_per_wait_frames_ge100_waits'], r['memexport_syncs'], r['hostload_cpu']
        o.append('| %s | `%s` | %s | %s | %s | %s | %s / %s / %s | %s | %s / %s / %s | %s / %s | %s / %s | %s | %s | %s (%s) | %s | %s of %s | %s / %s |' % (
            r['label'], r['run'], r['exit_code'], hang, ', '.join(r['dumps']) or '0', r['slow_frames'], r['ge100ms'],
            r['ge1s'], r['ge4s'], r['max_frame_ms'], w['median'], w['p99'], w['max'], mp['median'], mp['max'],
            sy['total'], sy['max_per_frame'], r['full_buffer_total_max'], r['toypad_load_lines'], r['marks_last'],
            'yes' if r['vortex'] else 'no', r['cpu_util_median_run'], r['hostload_busy_rows'], r['hostload_rows'],
            hc['median'], hc['max']))
    for r in results:
        for e in r['stuck_events']:
            o += ['', '**%s: hang at %s** (owner lr %s, sys.csv cpu_util max [-10, +2] s: %s); hostload rows +-60 s: %s' % (
                r['label'], e['at'], ','.join(e['owner_lr']) or '?', e['cpu_util_max_m10_p2'],
                '; '.join(e['hostload_pm60']) or 'none')]
    for r in results:
        if not r['stall_frames_ge1s'] and not r['top_frames']:
            continue
        o += ['', '**%s: frames >= 1 s** (or the 5 largest if none)' % r['label'], '',
              '| frame | at | ms | host-gpu wait ms (waits) | ms per wait | memexport syncs (KB) | on demand | full-buffer | '
              'gpu-thread idle ms | cpu_util max [-10, +2] s |', '|' + '---|' * 10]
        for f in (r['stall_frames_ge1s'] or r['top_frames']):
            o.append('| #%s | %s | %s | %s (%s) | %s | %s (%s) | %s | %s | %s | %s |' % (
                f['frame'], f['at'], f['ms'], f['wait_ms'], f['waits'], f['ms_per_wait'], f['syncs'], f['sync_kb'],
                f['on_demand'], f['full_buffer'], f['gpu_idle_ms'], f['cpu_util_max_m10_p2']))
    return '\n'.join(o) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('runs', nargs='+', help='label=RUN_DIR')
    ap.add_argument('--json')
    ap.add_argument('--md')
    a = ap.parse_args()
    results = []
    for spec in a.runs:
        label, _, run = spec.partition('=')
        if not os.path.isdir(run):
            sys.exit('not a folder: %s' % run)
        results.append(scan(label, run))
    text = md(results)
    if a.md:
        with open(a.md, 'w', encoding='utf-8') as f:
            f.write(text)
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=1, default=str)
    sys.stdout.write(text)


if __name__ == '__main__':
    main()
