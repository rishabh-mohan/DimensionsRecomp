#!/usr/bin/env python3
"""Summarise a functional-boot run dir written by bench/agent8/run/first-boot.ps1 (task #16).

Usage:
  python bench/agent8/run/boot_report.py <run dir> [--md <out.md>] [--top 15]
         [--anchor HH:MM:SS.fff=BYTES ...] [--upper HH:MM:SS.fff=BYTES ...]

Reads run.json, proc.csv, game.log and perf.csv from the run dir and prints a markdown report:
milestones with their log time and offset from process start, log level counts and the most
frequent warning/error messages, process CPU/memory/thread peaks, the perf.csv frame data, and an
estimate of when the first guest frame (perf.csv row 1) was presented.

First-frame method. perf.csv has no timestamp column, the game flushes it only every 60 rows (and at
exit), and the game keeps it open without read sharing, so the runner records only its SIZE. The
size at a known time is mapped to the number of complete rows k through the row byte offsets of the
final file. frame_time_us is the wall-clock swap-to-swap interval (checked on run 1928-first: four
independent flush anchors agree to 4 ms over 5.5 min), so the first swap happened at
  t(flush of row k) - sum(frame_time_us of rows 2..k).
Anchor kinds:
  exact  the flush time is known: --anchor (a LastWriteTime reading), or the final perf.csv mtime when
         its row count is a multiple of 60 (a periodic flush; the game was killed, so no exit flush);
  bound  a proc.csv sample saw the size grow between t_prev and t, so that flush happened in (t_prev, t];
  upper  --upper: the size was seen at that time, so the flush happened at or before it.
Frame times from a run on a hidden or locked desktop are not valid timing; they are reported only as
a liveness check. Stdlib only.
"""
import argparse
import bisect
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta

LOG_RE = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\] \[(\w+)\] \[(\w+)\] \[t(\d+)\] ?(.*)$')
NOTE_BYTES_RE = re.compile(r'perf\.csv bytes (\d+)')

# (label, regex). The first match of each is reported, in log order.
MILESTONES = [
    ('DXGI adapter', r'DXGI adapter: (.*)'),
    ('D3D12 device created', r'Direct3D 12 device and OS features'),
    ('D3D12 feature level', r'(?i)feature level\s*[:=]?\s*(.*)'),
    ('Presenter attached to the window', r'Startup: presenter attached'),
    ('Runtime construction started', r'Startup: constructing the runtime'),
    ('Guest memory arena mapped', r'Guest memory arena mapped'),
    ('Function table initialized', r'Function table initialized'),
    ('XEX + TU23 patch applied', r'XEX patch applied successfully: (.*)'),
    ('Module launched', r'Startup: launching the module'),
    ('Shader storage init started', r'Initializing shader storage(.*)'),
    ('Guest GPU interrupt callback set', r'SetInterruptCallback'),
    ('Cutscene skip flag', r'Skip cutscenes: (.*)'),
    ('Audio endpoint opened', r'audio endpoint (.*)'),
    ('First ToyPad traffic', r'Toypad\[Write\]'),
    ('First disc file failure', r'NtCreateFile\] FAILED'),
]

NORM_RE = [
    (re.compile(r'0x[0-9a-fA-F]+'), '0x#'),
    (re.compile(r'\b[0-9A-F]{8}\b'), '#'),
    (re.compile(r'\d+'), '#'),
]


def norm(msg):
    for rx, rep in NORM_RE:
        msg = rx.sub(rep, msg)
    return msg[:160]


def parse_time(s):
    s = s.strip()
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError('bad time: %r' % s)


def hms(t):
    return t.strftime('%H:%M:%S.%f')[:-3]


def read_log(path):
    entries = []  # [time, level, cat, tid, msg]
    if not os.path.exists(path):
        return entries
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.rstrip('\r\n')
            m = LOG_RE.match(line)
            if m:
                entries.append([parse_time(m.group(1)), m.group(2), m.group(3), m.group(4), m.group(5)])
            elif entries:
                entries[-1][4] += '\n' + line
    return entries


def read_perf(path):
    """(header, rows, ends). rows: int lists; ends[i]: byte offset just past row i's newline.
    A truncated last line (no newline yet) or a malformed row is skipped."""
    if not os.path.exists(path):
        return None, [], []
    with open(path, 'rb') as f:
        data = f.read()
    nl = data.find(b'\n')
    if nl < 0:
        return [], [], []
    header = data[:nl].rstrip(b'\r').decode('ascii', 'replace').split(',')
    rows, ends = [], []
    off = nl + 1
    while off < len(data):
        nl = data.find(b'\n', off)
        if nl < 0:
            break
        parts = data[off:nl].rstrip(b'\r').split(b',')
        off = nl + 1
        if len(parts) != len(header):
            continue
        try:
            rows.append([int(x) for x in parts])
        except ValueError:
            continue
        ends.append(off)
    return header, rows, ends


def read_proc(path):
    import csv
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8-sig', errors='replace', newline='') as f:
        return list(csv.DictReader(f))


def fnum(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def pct(sorted_vals, p):
    """Nearest-rank percentile."""
    if not sorted_vals:
        return None
    k = max(1, int(-(-p * len(sorted_vals) // 100)))
    return sorted_vals[min(k, len(sorted_vals)) - 1]


def proc_bytes(p):
    """perf.csv size recorded by a proc.csv sample: the perf_csv_bytes column, or a recovery note."""
    v = fnum(p.get('perf_csv_bytes'))
    if v is not None:
        return int(v)
    m = NOTE_BYTES_RE.search(p.get('note') or '')
    return int(m.group(1)) if m else None


def parse_anchor(s, day):
    tm, _, b = s.partition('=')
    t = parse_time(day.strftime('%Y-%m-%d ') + tm.strip())
    return t, int(b)


def first_frame(ft, ends, start, proc, anchors, uppers, mtime):
    """Returns (table rows, summary text). Times are datetimes; start is the base for proc.csv t_s."""
    cum = [0]
    for x in ft:
        cum.append(cum[-1] + x)

    def back_to_first(b):
        k = bisect.bisect_right(ends, b)
        if k == 0:
            return 0, None, False
        return k, (cum[k] - cum[1]) / 1e6, ends[k - 1] == b

    table = []  # (kind, source, time text, bytes, rows, first-swap low dt, first-swap high dt)
    exact, lows, highs = [], [], []
    for t, b in anchors:
        k, back, ok = back_to_first(b)
        if k:
            est = t - timedelta(seconds=back)
            exact.append(est)
            table.append(('exact', '--anchor' + ('' if ok else ' (size not on a row boundary)'), hms(t), b, k, est, est))
    if mtime is not None and ends:
        k = len(ends)
        b = ends[-1]
        back = (cum[k] - cum[1]) / 1e6
        est = mtime - timedelta(seconds=back)
        if k % 60 == 0:
            exact.append(est)
            table.append(('exact', 'final perf.csv mtime (periodic flush)', hms(mtime), b, k, est, est))
        else:
            highs.append(est)
            table.append(('upper', 'final perf.csv mtime (exit flush)', hms(mtime), b, k, None, est))
    for t, b in uppers:
        k, back, ok = back_to_first(b)
        if k:
            est = t - timedelta(seconds=back)
            highs.append(est)
            table.append(('upper', '--upper', hms(t), b, k, None, est))
    if start is not None:
        prev_t, prev_b = None, None
        nb = 0
        for p in proc:
            t_s = fnum(p.get('t_s'))
            b = proc_bytes(p)
            if t_s is None or b is None:
                continue
            if prev_b is not None and b > prev_b and b > 0:
                k, back, ok = back_to_first(b)
                if k:
                    lo = start + timedelta(seconds=prev_t - back)
                    hi = start + timedelta(seconds=t_s - back)
                    lows.append(lo)
                    highs.append(hi)
                    nb += 1
                    if nb <= 3:
                        table.append(('bound', 'proc.csv t=%.2f..%.2f s' % (prev_t, t_s),
                                      hms(start + timedelta(seconds=t_s)), b, k, lo, hi))
            prev_t, prev_b = t_s, b
        if nb > 3:
            table.append(('bound', '(%d more proc.csv bounds folded into the summary)' % (nb - 3), '', '', '', None, None))
    lo = max(lows) if lows else None
    hi = min(highs) if highs else None
    return table, exact, lo, hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--md')
    ap.add_argument('--top', type=int, default=15)
    ap.add_argument('--anchor', action='append', default=[], help='HH:MM:SS.fff=BYTES, a known flush time (exact)')
    ap.add_argument('--upper', action='append', default=[], help='HH:MM:SS.fff=BYTES, size seen at that time')
    a = ap.parse_args()
    run = a.run
    out = []
    w = out.append

    meta = {}
    rj = os.path.join(run, 'run.json')
    if os.path.exists(rj):
        with open(rj, 'r', encoding='utf-8-sig') as f:
            meta = json.load(f)
    start = parse_time(meta.get('proc_t0') or meta['start']) if meta.get('start') else None  # base of proc.csv t_s
    pstart = parse_time(meta['process_start']) if meta.get('process_start') else start  # base of offsets

    log = read_log(os.path.join(run, 'game.log'))
    perf_path = os.path.join(run, 'perf.csv')
    header, rows, ends = read_perf(perf_path)
    proc = read_proc(os.path.join(run, 'proc.csv'))
    day = pstart or (log[0][0] if log else datetime.now())

    def off(t):
        return '%.1f' % (t - pstart).total_seconds() if pstart else ''

    w('### Run')
    w('')
    w('| item | value |')
    w('|---|---|')
    for k in ('run', 'bin_dir', 'pid', 'start', 'process_start', 'end', 'note', 'watch_s', 'exited_early',
              'exited_at_s', 'exit_code_hex', 'peak_ws_mb', 'peak_commit_mb', 'max_threads',
              'max_threads_recovery_window', 'not_responding_samples', 'sample_errors', 'first_log_line_s',
              'first_window_s', 'first_perf_csv_flush_s', 'log_lines', 'perf_csv_lines', 'perf_csv_bytes',
              'perf_csv_mtime', 'werfault_seen', 'free_ram_gb_at_start', 'runner_session', 'runner_desktop',
              'logonui_running', 'stop_when_unlocked', 'unlocked_at_s', 'build_procs_max', 'sys_busy_pct_mean',
              'sys_busy_pct_max', 'other_cores_mean', 'other_cores_max'):
        if k in meta and meta[k] is not None:
            w('| %s | %s |' % (k, meta[k]))
    if isinstance(meta.get('env'), dict) and meta['env']:
        w('| env | %s |' % ' '.join('%s=%s' % kv for kv in meta['env'].items()))
    if isinstance(meta.get('build_procs_at_start'), list):
        w('| build_procs_at_start | %s |' % ('; '.join(meta['build_procs_at_start']) or 'none'))
    if meta.get('close'):
        c = meta['close']
        w('| close | WM_CLOSE posted to %s window(s); exited after %s s; killed=%s; exit %s |'
          % (c.get('wm_close_posted'), c.get('exit_wait_s'), c.get('killed'), c.get('exit_code_hex')))
    for k in ('windows_at_end', 'dialogs', 'artifacts'):
        v = meta.get(k)
        if v:
            w('| %s | %s |' % (k, '; '.join(v) if isinstance(v, list) else v))
    w('')

    # First frame (needed for the milestone table)
    ff_table, ff_exact, ff_lo, ff_hi, ff_best = [], [], None, None, None
    if rows:
        idx = {h: i for i, h in enumerate(header)}
        ft = [r[idx['frame_time_us']] for r in rows] if 'frame_time_us' in idx else []
        mtime = None
        if meta.get('perf_csv_mtime'):
            mtime = parse_time(meta['perf_csv_mtime'])
        elif os.path.exists(perf_path):
            mtime = datetime.fromtimestamp(os.path.getmtime(perf_path))
        anchors = [parse_anchor(s, day) for s in a.anchor]
        uppers = [parse_anchor(s, day) for s in a.upper]
        if ft:
            ff_table, ff_exact, ff_lo, ff_hi = first_frame(ft, ends, start, proc, anchors, uppers, mtime)
            if ff_exact:
                ff_exact.sort()
                ff_best = ff_exact[len(ff_exact) // 2]
            elif ff_lo is not None and ff_hi is not None and abs((ff_lo - ff_hi).total_seconds()) < 1.0:
                ff_best = ff_lo + (ff_hi - ff_lo) / 2

    # Milestones
    w('### Milestones (game.log)')
    w('')
    w('| milestone | log time | s after process start | detail |')
    w('|---|---|---|---|')
    ms_rows = []
    for label, rx in MILESTONES:
        r = re.compile(rx)
        for e in log:
            m = r.search(e[4])
            if m:
                detail = (m.group(1) if m.groups() else '').split('\n')[0][:120]
                ms_rows.append((e[0], label, detail))
                break
        else:
            ms_rows.append((None, label, ''))
    if ff_best is not None:
        ms_rows.append((ff_best, '**First guest frame (perf.csv row 1)**', 'estimated from perf.csv flushes, see below'))
    seen = sorted([x for x in ms_rows if x[0] is not None], key=lambda x: x[0])
    for t, label, detail in seen:
        w('| %s | %s | %s | %s |' % (label, hms(t), off(t), detail.replace('|', '/')))
    for t, label, detail in ms_rows:
        if t is None:
            w('| %s | not seen | | |' % label)
    if log:
        last = log[-1]
        w('| (last log line on disk) | %s | %s | %s |' % (hms(last[0]), off(last[0]),
          last[4].split('\n')[0][:120].replace('|', '/')))
    w('')
    if log and meta.get('end') and meta.get('close', {}) and meta['close'].get('killed'):
        end = parse_time(meta['end'])
        w('The game was killed, so log lines after the last spdlog flush (%s) are lost; the process ended about %.0f s later.'
          % (hms(log[-1][0]), (end - log[-1][0]).total_seconds()))
        w('')

    # Levels
    lv = Counter(e[1] for e in log)
    w('### Log levels')
    w('')
    w('Entries: %d. ' % len(log) + ', '.join('%s %d' % (k, v) for k, v in lv.most_common()))
    w('')
    for level in ('critical', 'error', 'warning'):
        msgs = Counter(norm(e[4].split('\n')[0]) for e in log if e[1] == level)
        if not msgs:
            continue
        w('Top %s messages (%d distinct):' % (level, len(msgs)))
        w('')
        w('| count | message (digits normalised) |')
        w('|---|---|')
        for m, n in msgs.most_common(a.top):
            w('| %d | `%s` |' % (n, m.replace('|', '/').replace('`', "'")))
        w('')
    cats = Counter((e[1], e[2]) for e in log if e[1] in ('warning', 'error', 'critical'))
    if cats:
        w('By level and category: ' + ', '.join('%s/%s %d' % (k[0], k[1], v) for k, v in cats.most_common()))
        w('')

    # Process
    w('### Process (proc.csv, 1 s samples)')
    w('')
    alive = [p for p in proc if p.get('alive') == '1']
    if alive:
        ncpu = int(meta.get('logical_cpus') or os.cpu_count() or 0)
        cores_all = [fnum(p['cpu_cores']) for p in alive if fnum(p.get('cpu_cores')) is not None]
        cores = [c for c in cores_all if not ncpu or c <= ncpu + 0.5]
        bad_cores = len(cores_all) - len(cores)
        ws = [fnum(p['ws_mb']) for p in alive if fnum(p.get('ws_mb')) is not None]
        cm = [fnum(p['commit_mb']) for p in alive if fnum(p.get('commit_mb')) is not None]
        th = [int(p['threads']) for p in alive if p.get('threads')]
        fr = [fnum(p['free_ram_gb']) for p in proc if fnum(p.get('free_ram_gb')) is not None]
        nr = sum(1 for p in alive if p.get('responding') == 'False')
        gaps = []
        prev = None
        for p in alive:
            t = fnum(p['t_s'])
            if prev is not None and t is not None and t - prev > 5:
                gaps.append((prev, t))
            prev = t
        w('| metric | value |')
        w('|---|---|')
        w('| samples alive | %d (t %.0f-%.0f s) |' % (len(alive), fnum(alive[0]['t_s']), fnum(alive[-1]['t_s'])))
        if gaps:
            w('| sampling gaps | %s |' % ', '.join('%.0f-%.0f s' % g for g in gaps))
        w('| CPU, cores (mean / max) | %.2f / %.2f%s |' % (sum(cores) / len(cores), max(cores),
          (' (%d sample(s) above %d logical CPUs dropped: time-stamped before a blocking Responding check)'
           % (bad_cores, ncpu)) if bad_cores else ''))
        w('| working set MB (end / max sample / peak) | %.0f / %.0f / %s |' % (ws[-1], max(ws), alive[-1]['peak_ws_mb']))
        w('| commit MB (end / max sample / peak) | %.0f / %.0f / %s |' % (cm[-1], max(cm), alive[-1]['peak_commit_mb']))
        w('| threads (end / max) | %d / %d |' % (th[-1], max(th)))
        w('| not-responding samples | %d |' % nr)
        if fr:
            w('| system free RAM GB (min / max) | %.2f / %.2f |' % (min(fr), max(fr)))
        # Machine-wide columns (first-boot.ps1 from 22:35 on). cpu_pct_machine is the game's own share, not these.
        sysb = [fnum(p.get('sys_busy_pct')) for p in alive if fnum(p.get('sys_busy_pct')) is not None]
        oth = [fnum(p.get('other_cores')) for p in alive if fnum(p.get('other_cores')) is not None]
        bld = [int(p['build_procs']) for p in alive if (p.get('build_procs') or '').strip().isdigit()]
        if sysb:
            w('| machine CPU busy %%, all processes (mean / max) | %.1f / %.1f |' % (sum(sysb) / len(sysb), max(sysb)))
        if oth:
            w('| other processes, cores (machine minus game; mean / max) | %.2f / %.2f |' % (sum(oth) / len(oth), max(oth)))
        if bld:
            w('| build processes running (max of the 5 s samples) | %d |' % max(bld))
        w('')
        has_bytes = any(proc_bytes(p) is not None for p in alive)
        has_sys = bool(sysb)
        w('| t s | cores | WS MB | commit MB | threads | log lines | %s |%s' % ('perf.csv bytes' if has_bytes else 'perf.csv lines',
          ' machine % | other cores |' if has_sys else ''))
        w('|---|---|---|---|---|---|---|' + ('---|---|' if has_sys else ''))
        last_t = None
        for p in alive:
            t = fnum(p['t_s'])
            if t is None:
                continue
            if last_t is None or t - last_t >= 29.5 or p is alive[-1] or (gaps and any(abs(t - g[1]) < 0.01 for g in gaps)):
                v = proc_bytes(p) if has_bytes else p.get('csv_lines')
                w('| %s | %s | %s | %s | %s | %s | %s |' % (p['t_s'], p['cpu_cores'], p['ws_mb'], p['commit_mb'],
                  p['threads'], p['log_lines'], '' if v is None else v)
                  + ((' %s | %s |' % (p.get('sys_busy_pct') or '', p.get('other_cores') or '')) if has_sys else ''))
                last_t = t
        w('')

    # Frames
    w('### Frames (perf.csv)')
    w('')
    if header is None:
        w('perf.csv missing.')
    elif not rows:
        w('perf.csv has no complete data rows.')
    else:
        idx = {h: i for i, h in enumerate(header)}
        ft = [r[idx['frame_time_us']] for r in rows]
        fps = [r[idx['fps']] for r in rows]
        dc = [r[idx['draw_calls']] for r in rows] if 'draw_calls' in idx else []
        s = sorted(ft)
        w('Rows: %d (%d bytes). Sum of frame_time_us: %.1f s. Frame times from a hidden or locked desktop are '
          'NOT valid timing; they show only that the game kept presenting.' % (len(rows), ends[-1], sum(ft) / 1e6))
        w('')
        cum, i0 = 0, len(ft)
        for i, x in enumerate(ft):
            cum += x
            if cum > 60e6:
                i0 = i + 1
                break
        s60 = sorted(ft[i0:])
        w('| frame_time_us | all rows | after the first 60 s of frames |')
        w('|---|---|---|')
        w('| rows | %d | %d |' % (len(s), len(s60)))
        w('| median / p99 / p99.9 / max | %s / %s / %s / %s | %s |' % (
            pct(s, 50), pct(s, 99), pct(s, 99.9), s[-1],
            ('%s / %s / %s / %s' % (pct(s60, 50), pct(s60, 99), pct(s60, 99.9), s60[-1])) if s60 else ''))
        w('| rows over 33.3 ms / 100 ms | %d / %d | %d / %d |' % (
            sum(1 for x in s if x > 33333), sum(1 for x in s if x > 100000),
            sum(1 for x in s60 if x > 33333), sum(1 for x in s60 if x > 100000)))
        w('')
        w('First 5 frame_time_us: %s. fps column (first / median / last): %s / %s / %s.' % (
            ', '.join(str(x) for x in ft[:5]), fps[0], pct(sorted(fps), 50), fps[-1]))
        if dc:
            nz = [i for i, x in enumerate(dc) if x > 0]
            w('draw_calls (median / max / rows > 0): %s / %s / %d%s.' % (
                pct(sorted(dc), 50), max(dc), len(nz), ('; first row with draw calls: %d' % (nz[0] + 1)) if nz else ''))
        w('')
        win, c, n, fl = [], 0, 0, []
        for x in ft:
            c += x
            n += 1
            if c >= 30e6:
                win.append('%.1f' % (n / (c / 1e6)))
                c, n = 0, 0
        if win:
            w('Frames per second in consecutive 30 s windows of frame time: ' + ', '.join(win) + '.')
            w('')

        w('### First guest frame estimate')
        w('')
        if ff_table:
            w('| kind | source | time | perf.csv bytes | rows on disk | first swap (s after process start) |')
            w('|---|---|---|---|---|---|')
            for kind, src, tt, b, k, lo, hi in ff_table:
                if lo is None and hi is None:
                    rng = ''
                elif lo is None:
                    rng = '<= %s' % off(hi)
                elif lo == hi:
                    rng = off(lo)
                else:
                    rng = '%s .. %s' % (off(lo), off(hi))
                w('| %s | %s | %s | %s | %s | %s |' % (kind, src, tt, b, k, rng))
            w('')
        if ff_best is not None:
            parts = []
            if ff_exact:
                spread = (ff_exact[-1] - ff_exact[0]).total_seconds() * 1000
                parts.append('%d exact anchor(s) agree within %.0f ms' % (len(ff_exact), spread))
            if ff_lo is not None or ff_hi is not None:
                parts.append('proc.csv/upper bounds: %s .. %s s' % (off(ff_lo) if ff_lo else '-', off(ff_hi) if ff_hi else '-'))
                if ff_lo is not None and ff_hi is not None and ff_lo > ff_hi:
                    gap = (ff_lo - ff_hi).total_seconds()
                    if gap < 1.0:
                        parts.append('the bounds miss each other by %.2f s: sampler time-stamp skew, the exact anchors decide' % gap)
                    else:
                        parts.append('BOUNDS INCONSISTENT by %.2f s (frame_time_us may not be wall time)' % gap)
            w('**First guest frame at %s, %s s after process start** (%s).' % (hms(ff_best), off(ff_best), '; '.join(parts)))
        else:
            w('No usable perf.csv size anchors: pass --anchor HH:MM:SS.fff=BYTES (a LastWriteTime reading).')
        w('')
    text = '\n'.join(out) + '\n'
    sys.stdout.write(text)
    if a.md:
        with open(a.md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)


if __name__ == '__main__':
    main()
