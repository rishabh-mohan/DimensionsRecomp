#!/usr/bin/env python3
"""gameplay_post.py (M3 gameplay task): read-only report of one or more gameplay/exploration arms.

usage:
  gameplay_post.py --arm NAME=RUN_DIR[,TRACE_DIR[,SHOTS_DIR]] [--arm ...] --out REPORT.txt
  gameplay_post.py --selftest RUN_DIR [--selftest RUN_DIR2] --out REPORT.txt   (parsers on old level runs; no game)

Per arm:
  * clean exit (run.json: exit 0, wm_close, no crash events / dumps / WER), route steps done, the long waits
    (wait_log with a timeout >= 20 s: front-end states, pads-white, tags) ok or TIMEOUT;
  * the per-mark table: route time, mark, the native front-end state at that point (FE: last settled
    'Native frontend transition ... current=N pending=4294967295' before input.csv log_bytes; '-' = none yet),
    perf.csv scene before the mark (median draws / vertices / fps of the last 60 frames before input.csv perf_bytes;
    n/a when perf.csv has no draw counts, as on native), worst frame since the previous mark, the Toypad LED state
    (last 'Toypad: pad N mode M lit RR GG BB' line before log_bytes), game.log lines since the previous mark, and the
    screenshot (gameplay-watch index.csv) - the "what happened at each mark" view;
  * the front-end state path (distinct settled states with times) and the furthest state, INFO;
  * level / player control: no reliable marker yet (the orange 'FF 6E 00' LED cycle is the TITLE screen, not a level
    vortex), INFO only - the screenshots decide; with a mark named 'in-level' the later sections are split there;
  * Toypad: listener LOAD / REMOVE confirms and figure added/removed events (game.log);
  * stalls: perf.csv frames > 100 ms (count, after the 'in-level' mark, top 10 with the mark they follow);
  * missing draws: native trace events.tsv draw_missing_* (total, frames with misses, top guests); xenos: n/a;
  * fps: median and p1 (from frame_time_us) after the 'in-level' mark or the whole run (INFO, never timing);
  * warning/error line types in game.log (top 12, INFO).
Exit 0 = report written (RESULT line: PASS / PASS-WITH-CHECKS / FAIL); 1 = selftest failed; 2 = usage.
"""
import argparse
import collections
import csv
import json
import os
import re
import statistics
import sys

RE_LIT = re.compile(r'Toypad: pad (\d) mode (\d) lit ([0-9A-F]{2} [0-9A-F]{2} [0-9A-F]{2})')
RE_TS = re.compile(r'^\[\d{4}-\d\d-\d\d (\d\d:\d\d:\d\d\.\d+)\]')
RE_FE = re.compile(r'Native frontend transition: manager=\d+ current=(\d+) pending=4294967295\b')
FE_NONE = '4294967295'
STALL_US = 100000


def q(v, p):
    s = sorted(v)
    return s[min(len(s) - 1, int(p * len(s)))] if s else 0


def read_input(path):
    """input.csv rows as dicts; args/result may contain commas, the 10 counters at the end never do."""
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding='utf-8', errors='replace') as f:
        head = f.readline().rstrip('\r\n').split(',')
        tail_names = head[5:]
        for line in f:
            p = line.rstrip('\r\n').split(',')
            if len(p) < 5 + len(tail_names):
                continue
            mid = p[3:len(p) - len(tail_names)]
            r = {'t_s': p[0], 'line': p[1], 'cmd': p[2], 'args': mid[0] if mid else '',
                 'result': ','.join(mid[1:])}
            for k, v in zip(tail_names, p[len(p) - len(tail_names):]):
                try:
                    r[k] = int(v)
                except ValueError:
                    r[k] = -1
            try:
                r['t'] = float(p[0])
            except ValueError:
                r['t'] = 0.0
            rows.append(r)
    return rows


def read_perf(path):
    """perf.csv frame rows (frame_time_us, fps, draws, verts) with the byte offset where each row ends."""
    out = []
    if not os.path.exists(path):
        return out
    with open(path, 'rb') as f:
        head = f.readline()
        cols = head.decode('ascii', 'replace').strip().split(',')
        ix = {c: i for i, c in enumerate(cols)}
        pos = len(head)
        for raw in f:
            pos += len(raw)
            p = raw.decode('ascii', 'replace').strip().split(',')
            try:
                out.append((pos, int(p[ix['frame_time_us']]), int(p[ix['fps']]), int(p[ix['draw_calls']]),
                            int(p[ix['vertices_processed']])))
            except (ValueError, IndexError, KeyError):
                continue
    return out


def read_log(path):
    """game.log as (byte_end, line) plus a note when it rotated (offsets then approximate)."""
    out = []
    note = ''
    if os.path.exists(path):
        with open(path, 'rb') as f:
            pos = 0
            for raw in f:
                pos += len(raw)
                out.append((pos, raw.decode('utf-8', 'replace').rstrip('\r\n')))
    root, ext = os.path.splitext(path)
    if os.path.exists(root + '.1' + ext):
        note = 'game.log rotated (game.1.log exists): LED/log offsets are approximate'
    return out, note


def perf_index(perf, nbytes):
    """number of perf rows complete at file size nbytes."""
    lo, hi = 0, len(perf)
    while lo < hi:
        mid = (lo + hi) // 2
        if perf[mid][0] <= nbytes:
            lo = mid + 1
        else:
            hi = mid
    return lo


def led_at(log, nbytes):
    led = '-'
    for end, line in log:
        if end > nbytes:
            break
        m = RE_LIT.search(line)
        if m and m.group(1) in ('1', '0'):
            led = 'pad%s m%s %s' % (m.group(1), m.group(2), m.group(3))
    return led


def fe_at(log, nbytes):
    """last settled native front-end state (no pending transition) before byte offset nbytes; '-' = none yet."""
    fe = '-'
    for end, line in log:
        if end > nbytes:
            break
        m = RE_FE.search(line)
        if m:
            fe = 'none' if m.group(1) == FE_NONE else m.group(1)
    return fe


def fe_path(log):
    """distinct consecutive settled front-end states as (HH:MM:SS.s, state)."""
    path = []
    for _, line in log:
        m = RE_FE.search(line)
        if m:
            st = 'none' if m.group(1) == FE_NONE else m.group(1)
            if not path or path[-1][1] != st:
                t = RE_TS.match(line)
                path.append((t.group(1)[:10] if t else '?', st))
    return path


def norm_warn(line):
    m = re.match(r'^\[[^\]]*\] \[(warning|warn|error|critical)\] \[(\w+)\] \[t\d+\] (.*)$', line)
    if not m:
        return None
    s = re.sub(r'0x[0-9A-Fa-f]+', '0x#', m.group(3))
    s = re.sub(r'\b[0-9A-Fa-f]{8,}\b', '#', s)
    s = re.sub(r'\d+', '#', s)
    return '[%s] [%s] %s' % (m.group(1), m.group(2), s[:120])


def trace_missing(tdir):
    ev = os.path.join(tdir, 'events.tsv') if tdir else ''
    if not ev or not os.path.exists(ev):
        return None
    frames = 0
    miss = collections.Counter()
    guests = collections.Counter()
    with open(ev, encoding='utf-8', errors='replace') as f:
        next(f, None)
        for line in f:
            p = line.rstrip('\r\n').split('\t')
            if len(p) < 5:
                continue
            if p[2] == 'frame':
                frames += 1
            elif p[2].startswith('draw_missing_'):
                miss[p[1]] += 1
                d = p[4].split()
                guests[('VS' if 'vertex' in p[2] else 'PS' if 'pixel' in p[2] else p[2], d[1] if len(d) > 1 else '?')] += 1
    return {'frames': frames, 'missing_total': sum(miss.values()), 'frames_with_missing': len(miss),
            'top_guests': guests.most_common(8)}


def read_shots(sdir, arm):
    shots = {}
    idx = os.path.join(sdir, 'index.csv') if sdir else ''
    if idx and os.path.exists(idx):
        with open(idx, encoding='utf-8-sig', errors='replace') as f:
            for r in csv.DictReader(f):
                if r.get('file', '').startswith(arm + '-'):
                    m = re.match(r'^[^-]+-(\d{3})-', r['file'])
                    if m:
                        shots[int(m.group(1))] = r['file']
    return shots


def arm_report(name, run, tdir, sdir, say, check, expect_fp=''):
    say('== arm %s: run %s' % (name, run))
    j = {}
    try:
        j = json.load(open(os.path.join(run, 'run.json'), encoding='utf-8-sig'))
    except Exception as e:  # noqa
        check(False, '%s run.json' % name, 'unreadable: %s' % e)
    ins = j.get('input_script') or {}
    if j:
        check(j.get('exit_code') == 0 and not j.get('wer_seen') and not j.get('crash_events') and not j.get('dumps')
              and j.get('close_method') == 'wm_close', '%s clean exit' % name,
              'exit %s early %s close %s %s s wer %s crash %d dumps %d' % (
                  j.get('exit_code_hex'), j.get('exited_early'), j.get('close_method'), j.get('close_seconds'),
                  j.get('wer_seen'), len(j.get('crash_events') or []), len(j.get('dumps') or [])))
        say('INFO %s desktop %s elapsed %s s peak_ws %s MB exe %s steps %s/%s stopped_by_script %s error %s' % (
            name, j.get('desktop'), j.get('elapsed_s'), (j.get('process') or {}).get('peak_ws_mb'),
            str(j.get('exe_sha256'))[:16], ins.get('steps_done'), ins.get('steps_total'), ins.get('stopped_by_script'),
            ins.get('error')))
    rows = read_input(os.path.join(run, 'input.csv'))
    perf = read_perf(os.path.join(run, 'perf.csv'))
    log, lnote = read_log(os.path.join(run, 'game.log'))
    if lnote:
        say('NOTE %s %s' % (name, lnote))
    say('INFO %s input.csv %d rows, perf.csv %d frames, game.log %d lines' % (name, len(rows), len(perf), len(log)))
    fp = next((m.group(1) for m in (re.search(r'Native GPU \[([0-9a-f]{16})\]', l) for _, l in log) if m), None)
    if name.startswith('native') and expect_fp:
        check(fp == expect_fp.lower(), '%s fingerprint' % name, '%s (expected %s)' % (fp, expect_fp.lower()))
    elif fp:
        say('INFO %s native fingerprint %s' % (name, fp))
    check(bool(rows), '%s input.csv' % name, '%d rows' % len(rows))
    # long waits
    longw = []
    for r in rows:
        if r['cmd'] == 'wait_log':
            mt = re.search(r'\s(\d+(?:\.\d+)?)$', r['args'])
            if mt and float(mt.group(1)) >= 20:
                longw.append(r)
    for r in longw:
        say('  wait line %s %-48s %s' % (r['line'], r['args'][:48], r['result'][:40]))
    bad_waits = [r for r in longw if not r['result'].startswith('ok')]
    marks = [r for r in rows if r['cmd'] == 'mark']
    labels = [m['args'] for m in marks]
    vortex = next((i for i, m in enumerate(marks) if m['args'].split()[0] == 'in-level'), None)   # split point
    check(not bad_waits, '%s long waits' % name, '%d of %d ok' % (len(longw) - len(bad_waits), len(longw)))
    path = fe_path(log)
    say('INFO %s front-end state path: %s' % (name, ' > '.join('%s@%s' % (s, t) for t, s in path) if path else
                                              'no Native frontend transition lines (xenos arm or not logged)'))
    say('INFO %s level / player control: no reliable marker yet (the orange FF 6E 00 LED cycle is the title screen); '
        'furthest front-end state %s; last mark %s - check the screenshots' % (
            name, path[-1][1] if path else '-', labels[-1] if labels else '-'))
    noscene = not any(x[3] for x in perf)   # native: perf.csv draw counts are 0 / input.csv scene_draws -1
    # per-mark table
    shots = read_shots(sdir, name)
    say('  %3s %8s %-14s %4s %6s %8s %4s %8s %-20s %5s %s' % ('n', 't_s', 'mark', 'FE', 'draws', 'verts', 'fps', 'worst_ms',
                                                             'LED', 'loglns', 'shot'))
    prev_i, prev_ll = 0, 0
    scenes_after = []
    for n, m in enumerate(marks, 1):
        i = perf_index(perf, m.get('perf_bytes', 0)) if perf else 0
        win = perf[max(0, i - 60):i]
        dr = int(statistics.median(x[3] for x in win)) if win else -1
        vt = int(statistics.median(x[4] for x in win)) if win else -1
        fp = int(statistics.median(x[2] for x in win)) if win else -1
        seg = perf[prev_i:i]
        worst = max((x[1] for x in seg), default=0) / 1000.0
        ll = m.get('log_lines', 0)
        led = led_at(log, m.get('log_bytes', 0))
        fe = fe_at(log, m.get('log_bytes', 0))
        say('  %3d %8s %-14s %4s %6s %8s %4d %8.1f %-20s %5d %s' % (
            n, m['t_s'], m['args'].split()[0][:14], fe, 'n/a' if noscene else dr, 'n/a' if noscene else vt, fp, worst,
            led, ll - prev_ll, shots.get(n, '-')))
        if vortex is not None and n - 1 > vortex:
            scenes_after.append((dr, vt // 1000))
        prev_i, prev_ll = i, ll
    if vortex is not None and not noscene:
        distinct = len(set(scenes_after))
        say('INFO %s after the in-level mark: %d marks, %d distinct scenes (draws, kverts); >3 suggests the view moved '
            '(walking/camera/cutscene) - check the screenshots' % (name, len(scenes_after), distinct))
    # toypad
    loads = sum(1 for _, l in log if 'Toypad listener: LOAD ->' in l)
    removes = sum(1 for _, l in log if 'Toypad listener: REMOVE ->' in l)
    evp = os.path.join(run, 'toypad-events.csv')
    adds = rems = 0
    if os.path.exists(evp):
        for r in csv.DictReader(open(evp, encoding='utf-8', errors='replace')):
            d = r.get('detail', '')
            adds += d.startswith('figure added')
            rems += d.startswith('figure removed')
    check(loads >= 3, '%s toypad tags' % name, 'listener LOAD %d REMOVE %d; game saw figure added %d removed %d%s' % (
        loads, removes, adds, rems, '' if os.path.exists(evp) else ' (no toypad-events.csv)'))
    # stalls
    vb = marks[vortex].get('perf_bytes', 0) if vortex is not None else None
    vi = perf_index(perf, vb) if vb is not None else len(perf)
    st = [(k, x[1]) for k, x in enumerate(perf) if x[1] > STALL_US]
    st_after = [s for s in st if s[0] >= vi]
    mark_rows = [(perf_index(perf, m.get('perf_bytes', 0)), m['args'].split()[0]) for m in marks]

    def after_mark(k):
        lab = 'start'
        for i, lb in mark_rows:
            if i <= k:
                lab = lb
        return lab
    say('INFO %s stalls (frames > %d ms): %d total, %s' % (name, STALL_US // 1000, len(st), '%d after the in-level mark' % len(
        st_after) if vortex is not None else 'no in-level mark'))
    for k, us in sorted(st_after or st, key=lambda s: -s[1])[:10]:
        say('    frame %d: %.1f ms (after mark %s)' % (k, us / 1000.0, after_mark(k)))
    # fps after the in-level mark (whole run without one)
    ft = [x[1] for x in perf[vi if vortex is not None else 0:] if x[1] > 0]
    if ft:
        say('INFO %s fps %s: median %.1f, p1 %.1f (%d frames; functional run, not timing)' % (
            name, 'after the in-level mark' if vortex is not None else 'whole run', 1e6 / statistics.median(ft),
            1e6 / q(ft, 0.99), len(ft)))
    # missing draws
    tm = trace_missing(tdir)
    if tm is None:
        say('INFO %s missing draws: n/a (%s)' % (name, 'no native trace' if not tdir else 'no events.tsv in %s' % tdir))
    else:
        check(tm['missing_total'] == 0, '%s missing draws (native trace, whole run)' % name,
              '%d events in %d of %d frames%s' % (tm['missing_total'], tm['frames_with_missing'], tm['frames'],
                                                  ''.join('\n    %s guest %s: %d' % (k[0], k[1], v) for k, v in tm['top_guests'])),
              soft=True)
    # warnings
    wc = collections.Counter(k for k in (norm_warn(l) for _, l in log) if k)
    say('INFO %s warning/error line types: %d (%d lines)' % (name, len(wc), sum(wc.values())))
    for k, v in wc.most_common(12):
        say('    %s x%d' % (k, v))
    check(len(shots) >= 3 or not sdir, '%s screenshots' % name, '%d in %s' % (len(shots), sdir or '-'), soft=True)
    return {'marks': len(marks), 'perf': len(perf), 'fe_states': len(path)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arm', action='append', default=[])
    ap.add_argument('--selftest', action='append', default=[])
    ap.add_argument('--expect-fp', default='', help='native fingerprint (16 hex) required in arms named native*')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    out, fails, checks = [], [], []
    say = out.append

    def check(ok, nm, detail, soft=False):
        say('%s %s: %s' % ('PASS' if ok else ('CHECK' if soft else 'FAIL'), nm, detail))
        if not ok:
            (checks if soft else fails).append(nm)

    def write():
        with open(a.out, 'w', encoding='utf-8') as f:
            f.write('\n'.join(out) + '\n')
        print('\n'.join(out))

    if a.selftest:
        ok = True
        for k, run in enumerate(a.selftest):
            r = arm_report('st%d' % k, run, '', '', say, check)
            good = r['marks'] >= 10 and r['perf'] > 1000
            say('selftest %s: marks %d perf %d fe_states %d -> %s' % (run, r['marks'], r['perf'], r['fe_states'],
                                                                     'ok' if good else 'BAD'))
            ok = ok and good
        say('RESULT: selftest %s' % ('ok' if ok else 'FAILED'))
        write()
        return 0 if ok else 1
    if not a.arm:
        print('no --arm')
        return 2
    for s in a.arm:
        nm, _, rest = s.partition('=')
        run, tdir, sdir = (rest.split(',') + ['', ''])[:3]
        if not os.path.isdir(run):
            check(False, '%s run dir' % nm, 'missing: %s' % run)
            continue
        arm_report(nm, run, tdir, sdir, say, check, a.expect_fp)
    verdict = 'FAIL: ' + '; '.join(fails) if fails else ('PASS-WITH-CHECKS: ' + '; '.join(checks) if checks else 'PASS')
    say('RESULT: %s' % verdict)
    write()
    return 0


if __name__ == '__main__':
    sys.exit(main())
