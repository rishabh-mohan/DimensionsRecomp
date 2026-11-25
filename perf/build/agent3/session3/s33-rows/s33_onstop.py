"""s33_onstop.py - #33 row 4 (M6 TESTPLAN.md section 2): does an onstop run count, and did it shut down cleanly?

M3 draft, 11-25. Read-only on the run dir.

  python -B s33_onstop.py <run dir> [--window 2.0] [--json out.json]

A run COUNTS when its log has pipeline misses (slow-frame lines with "new N", N > 0) within --window seconds before
"Window closing, shutting down". Shutdown is clean when run.json has exit 0, close_method wm_close, no dump, no WER,
and close_seconds below close_timeout (no hang in the Shutdown join). The W9 watchdog line
"Shutdown wedged past the close request" is reported (a NOTE, TESTPLAN section 3).

Exit: 0 = clean and counts, 1 = FAIL (unclean shutdown), 3 = clean but does not count (re-run with a shifted
-Seconds), 2 = usage / no log.
"""
import argparse
import datetime
import json
import os
import re
import sys

TS_RE = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\]')
NEW_RE = re.compile(r'slow frame #(\d+): ([\d.]+) ms \|.*\| pipeline create [\d.]+ \(\d+x\), new (\d+) \|')
ROT_RE = re.compile(r'^game(?:\.(\d+))?\.log$', re.I)
CLOSE = 'Window closing, shutting down'
WEDGE = 'Shutdown wedged past the close request'


def log_files(run):
    fs = [(int(m.group(1) or 0), fn) for fn in os.listdir(run) for m in [ROT_RE.match(fn)] if m]
    # rotated logs: the highest number is the oldest
    return [os.path.join(run, fn) for _, fn in sorted(fs, key=lambda x: -x[0])]


def ts(line):
    m = TS_RE.match(line)
    return datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f') if m else None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--window', type=float, default=2.0)
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    if not os.path.isdir(a.run) or not log_files(a.run):
        print('usage: no run dir or no game*.log in %s' % a.run)
        return 2
    rj = {}
    p = os.path.join(a.run, 'run.json')
    if os.path.isfile(p):
        with open(p, encoding='utf-8-sig') as f:
            rj = json.load(f)
    misses = []   # (time, frame, ms, new)
    close_t, wedge = None, 0
    for fn in log_files(a.run):
        with open(fn, encoding='utf-8', errors='replace') as f:
            for ln in f:
                if CLOSE in ln and close_t is None:
                    close_t = ts(ln)
                elif WEDGE in ln:
                    wedge += 1
                else:
                    m = NEW_RE.search(ln)
                    if m and int(m.group(3)) > 0:
                        misses.append((ts(ln), int(m.group(1)), float(m.group(2)), int(m.group(3))))
    near = [x for x in misses if close_t and x[0] and 0 <= (close_t - x[0]).total_seconds() <= a.window]
    last = [x for x in misses if close_t and x[0] and x[0] <= close_t]
    gap = round((close_t - last[-1][0]).total_seconds(), 3) if last else None
    ct = rj.get('close_timeout')
    cs = rj.get('close_seconds')
    clean = {'exit 0': rj.get('exit_code') == 0, 'wm_close': rj.get('close_method') == 'wm_close',
             'no dump': not rj.get('dumps'), 'no WER': not rj.get('wer_seen'),
             'close_seconds < close_timeout': cs is not None and ct is not None and float(cs) < float(ct)}
    counts = bool(near)
    res = {'run': os.path.basename(os.path.normpath(a.run)), 'seconds_requested': rj.get('seconds_requested'),
           'close_sent_s': rj.get('close_sent_s'), 'close_seconds': cs, 'close_line': str(close_t) if close_t else None,
           'misses_total': sum(x[3] for x in misses), 'miss_frames_in_window': len(near),
           'misses_in_window': sum(x[3] for x in near), 'last_miss_gap_s': gap, 'watchdog_wedge_lines': wedge,
           'clean': clean, 'counts': counts}
    print('# s33_onstop %s (-Seconds %s; close sent at %s s, took %s s)' % (
        res['run'], res['seconds_requested'], res['close_sent_s'], cs))
    print('close line: %s' % (res['close_line'] or 'MISSING'))
    print('misses: %d in the run; %d in %d frame(s) within %.1f s before the close line; last miss %s s before it' % (
        res['misses_total'], res['misses_in_window'], len(near), a.window, gap if gap is not None else '-'))
    for k, v in clean.items():
        print('%s %s' % ('ok  ' if v else 'MISS', k))
    if wedge:
        print('NOTE watchdog: "%s" x%d (W9; a NOTE, compare with OFF runs)' % (WEDGE, wedge))
    if not all(clean.values()) or close_t is None:
        rc, verdict = 1, 'FAIL (unclean shutdown)' if close_t is not None else 'FAIL (no close line)'
    elif not counts:
        rc, verdict = 3, 'DOES NOT COUNT (no miss within %.1f s of the close; re-run with a shifted -Seconds)' % a.window
    else:
        rc, verdict = 0, 'PASS (clean, counts)'
    res['result'] = verdict
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(res, f, indent=1)
    print('RESULT: %s' % verdict)
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
