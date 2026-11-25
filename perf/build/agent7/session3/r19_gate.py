#!/usr/bin/env python3
"""r19_gate.py - per-row #19 line gate for queue-r19.jsonl (M7, session 3, S3T-7 A).

Judges the #18/#19 proof lines of ONE run's game log for one #19 row (ROWS-R19.md section 2). Read-only; stdlib
only; no game, no build. Rows c, g, j, d, f, e reuse soak_check.py (build/agent7/s4-r1s2/soak-check/, CAB5CB2C,
rated with #19 by M10) unchanged: this script imports it and only changes which of its checks gate which row.
Clean exit, fail markers, dumps and the logdiff vs the reference run stay with s4b_check.py / logdiff.py.

Run (Below Normal, from the workspace root):
  python -B build/agent7/session3/r19_gate.py <run dir | game.log> --row a|b|i|c|g|j|d|f|e [--n KB] [--json out]

Exit: 0 PASS, 1 FAIL, 2 INCOMPLETE (no log, or the proof lines needed to judge are absent),
      3 FLAG (no FAIL, but the 3 s shutdown watchdog fired in an ON row: r19-rating (b) 4 -> Overseer decides).
Only exit 0 lets M3 write build/agent3/session3/r19-ok-<row>.

Row rules (OFF rows a, b, i; ON rows c, g, j, d, f, e):
  a  no 'd3d12_async_submit' line and no 'd3d12_submit_split' line of any kind (OFF identity).
  b  exactly one [warning] 'd3d12_async_submit: needs d3d12_submit_split_kb above 0, staying off'; no other
     d3d12_async_submit line; no d3d12_submit_split line (split 0 means no #18 init either).
  i  no d3d12_async_submit line; #18 init exactly once (says 'at <N> KB' with --n); every split counter line has
     failed=0 and the 7 keys; splits > 0 in the last split line, else INCOMPLETE (no split was due).
  ON #18 init exactly once ('at <N> KB' with --n; j: 16); async init exactly once and says '(3 slots)';
     soak_check.check_events (row 'j' for j, else 'e'): A1-A4, S1, X1, X2 gate every ON row;
     S2 (held_query > 0) gates only row e (queries are a soak proof; menus may run none); row e with no split
     line at all is INCOMPLETE, not FAIL;
     J1 (full_waits > 0, row j) is INCOMPLETE when false, not FAIL (the FIFO never filled is not a defect);
     no async counter line at all -> INCOMPLETE 'no split was due at this N' (row d under fallback A).
  all  'Shutdown wedged past the close request; hard-exiting.' (legodimensions_app.h StartShutdownWatchdog):
     ON rows -> FLAG, OFF rows -> INFO (first sighting was an off run, RESUME L179).
Options added for the live chain (r19prep/LAUNCH-R19.md):
  --bin DIR   bin identity (M10 N1): run.json bin_dir is DIR, and the run dir's legodimensions.exe, rexgpu-xenos.dll and
              rexruntime.dll have the sha256 that DIR/MANIFEST.txt lists. The exe is DFBE1D43 on every bin, so the #19 bin
              is told apart by rexgpu-xenos.dll. Wrong hash or bin_dir -> FAIL; no run dir/run.json/MANIFEST -> INCOMPLETE.
  --j1-info   row g16 (M10 C2: 'the j rule set; J1 INCOMPLETE is acceptable'): J1 full_waits = 0 is INFO, not INCOMPLETE.
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOAK_DIR = os.path.normpath(os.path.join(HERE, '..', 's4-r1s2', 'soak-check'))
sys.path.insert(0, SOAK_DIR)
import soak_check as sc  # noqa: E402

ROWS = ['a', 'b', 'i', 'c', 'g', 'j', 'd', 'f', 'e']
ON_ROWS = ['c', 'g', 'j', 'd', 'f', 'e']
WARN_OFF = 'd3d12_async_submit: needs d3d12_submit_split_kb above 0, staying off'
WATCHDOG = 'Shutdown wedged past the close request; hard-exiting.'
S2_MSG = 'held_query > 0 in at least one split line'
J1_MSG = 'row j: full_waits > 0'
MINLINES_MSG = 'at least '
BIN_FILES = ('legodimensions.exe', 'rexgpu-xenos.dll', 'rexruntime.dll')


def manifest_sha(bin_dir):
    # MANIFEST.txt file table: name \t size \t mtime \t sha256 \t source
    out = {}
    with open(os.path.join(bin_dir, 'MANIFEST.txt'), 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            f = line.rstrip('\r\n').split('\t')
            if len(f) >= 4 and f[0] in BIN_FILES and len(f[3]) == 64:
                out[f[0]] = f[3].upper()
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def bin_check(res, run_dir, bin_dir):
    if not os.path.isdir(run_dir):
        res.check(False, 'bin identity: %s is not a run dir' % run_dir, incomplete=True)
        return
    try:
        want = manifest_sha(bin_dir)
    except OSError as e:
        res.check(False, 'bin identity: no MANIFEST.txt in %s (%s)' % (bin_dir, e), incomplete=True)
        return
    res.check(sorted(want) == sorted(BIN_FILES), 'bin identity: %s MANIFEST lists %s' % (bin_dir, sorted(want)),
              incomplete=True)
    try:
        with open(os.path.join(run_dir, 'run.json'), 'r', encoding='utf-8-sig') as fh:
            bd = json.load(fh).get('bin_dir') or ''
    except (OSError, ValueError) as e:
        res.check(False, 'bin identity: no readable run.json (%s)' % e, incomplete=True)
        return
    name = lambda p: os.path.basename(os.path.normpath(p)).lower()  # noqa: E731
    res.check(name(bd) == name(bin_dir), 'bin identity: run.json bin_dir %s (want %s)' % (bd or '-', bin_dir))
    for fn in BIN_FILES:
        p = os.path.join(run_dir, fn)
        got = sha256(p) if os.path.isfile(p) else None
        res.check(got is not None and got == want.get(fn), 'bin identity: run-dir %s %s == MANIFEST %s'
                  % (fn, (got or 'missing')[:16], (want.get(fn) or '-')[:16]))


def level_of(line):
    # '[YYYY-MM-DD HH:MM:SS.mmm] [level] [cat] ...'
    parts = line.split('] [', 2)
    return parts[1] if len(parts) > 2 else ''


def gate(lines, row, n=None, min_lines=2, max_queued=3, j1_info=False):
    res = sc.Result()
    ev = sc.parse(lines)
    raw = [l.rstrip('\r\n') for l in lines]
    async_lines = [(i, l) for i, l in enumerate(raw, 1) if 'd3d12_async_submit' in l]
    split_lines = [(i, l) for i, l in enumerate(raw, 1) if 'd3d12_submit_split' in l and 'd3d12_async_submit' not in l]
    init_split = [e for e in ev if e[0] == 'init_split']
    init_async = [e for e in ev if e[0] == 'init_async']
    split_ctr = [e for e in ev if e[0] == 'split']
    async_ctr = [e for e in ev if e[0] == 'async']
    wd = [i for i, l in enumerate(raw, 1) if WATCHDOG in l]
    res.info('row %s: lines with d3d12_async_submit %d, d3d12_submit_split %d (split init %d, split counter %d, '
             'async init %d, async counter %d), watchdog %d'
             % (row, len(async_lines), len(split_lines), len(init_split), len(split_ctr), len(init_async),
                len(async_ctr), len(wd)))
    flags = []

    def split_init_check():
        res.check(len(init_split) == 1, '#18 init line exactly once (%d)' % len(init_split))
        if n is not None and init_split:
            res.check(('at %s KB' % n) in init_split[0][3], "#18 init says 'at %s KB': %s"
                      % (n, init_split[0][3][-70:]))

    if row == 'a':
        res.check(not async_lines, 'no d3d12_async_submit line (%d)%s'
                  % (len(async_lines), ': L%d' % async_lines[0][0] if async_lines else ''))
        res.check(not split_lines, 'no d3d12_submit_split line (%d)%s'
                  % (len(split_lines), ': L%d' % split_lines[0][0] if split_lines else ''))
    elif row == 'b':
        warn = [(i, l) for i, l in async_lines if WARN_OFF in l]
        res.check(len(warn) == 1, "exactly one 'needs d3d12_submit_split_kb above 0, staying off' line (%d)" % len(warn))
        if warn:
            res.check(level_of(warn[0][1]) == 'warning', 'that line is [warning] (%s)' % (level_of(warn[0][1]) or '?'))
        other = [(i, l) for i, l in async_lines if WARN_OFF not in l]
        res.check(not other, 'no other d3d12_async_submit line (%d)%s'
                  % (len(other), ': L%d %s' % (other[0][0], other[0][1][-60:]) if other else ''))
        res.check(not split_lines, 'no d3d12_submit_split line, init included (%d)' % len(split_lines))
    elif row == 'i':
        res.check(not async_lines, 'no d3d12_async_submit line (%d)' % len(async_lines))
        split_init_check()
        miss = [e[1] for e in split_ctr if set(sc.SPLIT_KEYS) - set(e[3])]
        res.check(not miss, 'every split counter line has the 7 keys%s' % (': L%d' % miss[0] if miss else ''))
        failed = [e for e in split_ctr if e[3].get('failed', 0) != 0]
        res.check(not failed, 'failed = 0 in every split line (%d lines)%s'
                  % (len(split_ctr), ': L%d failed=%d' % (failed[0][1], failed[0][3]['failed']) if failed else ''))
        sc.monotonic(split_ctr, sc.SPLIT_KEYS, 'split', res, 1)
        last = split_ctr[-1][3].get('splits', 0) if split_ctr else 0
        res.check(last > 0, 'splits > 0 in the last split line (%s; no line = no split was due at this N)'
                  % (last if split_ctr else 'no split line'), incomplete=True)
    else:
        split_init_check()
        res.check(len(init_async) == 1, 'async init line exactly once (%d)' % len(init_async))
        if init_async:
            res.check('(%d slots)' % max_queued in init_async[0][3], "async init says '(%d slots)'" % max_queued)
        sub, _rep = sc.check_events(ev, row='j' if row == 'j' else 'e', max_queued=max_queued, min_lines=min_lines)
        for ln in sub.lines:
            tag, msg = ln[:10].strip(), ln[11:]
            if tag == 'FAIL' and msg.startswith(S2_MSG) and row != 'e':
                res.info('INFO(S2)   %s  [held_query gates only row e]' % msg)
            elif tag == 'FAIL' and msg.startswith(S2_MSG) and not split_ctr:
                res.check(False, msg + '  [row e without any split line: nothing to judge]', incomplete=True)
            elif tag == 'FAIL' and msg.startswith(J1_MSG) and j1_info:
                res.info('INFO(J1)   %s  [--j1-info: row g16, M10 C2]' % msg)
            elif tag == 'FAIL' and msg.startswith(J1_MSG):
                res.check(False, msg + '  [J1: FIFO never filled -> INCOMPLETE, not FAIL]', incomplete=True)
            elif tag == 'INCOMPLETE' and msg.startswith(MINLINES_MSG) and not async_ctr:
                res.check(False, msg + '  [no async counter line: no split was due at this N]', incomplete=True)
            elif tag in ('PASS', 'FAIL', 'INCOMPLETE'):
                res.check(tag == 'PASS', 'soak_check: ' + msg, incomplete=(tag == 'INCOMPLETE'))
            else:
                res.info('soak_check: ' + ln.strip())
        if _rep:
            res.info('rule 5 per frame: ' + ', '.join('%s %.4f' % (k, v) for k, v in _rep['per_frame'].items()
                                                       if v is not None))
    if wd:
        if row in ON_ROWS:
            flags.append('shutdown watchdog fired (L%d) in ON row %s' % (wd[0], row))
            res.info('FLAG       shutdown watchdog line at L%d (r19-rating (b) 4: flagged even if the row passes)' % wd[0])
        else:
            res.info('INFO       shutdown watchdog line at L%d (OFF row: note only)' % wd[0])
    return res, flags


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('path', help='run dir (game.log + rotated game.N.log) or one log file')
    ap.add_argument('--row', required=True, choices=ROWS)
    ap.add_argument('--n', help='expected #18 split KB in the init line (the ready-N value; row j: 16)')
    ap.add_argument('--min-lines', type=int, default=2)
    ap.add_argument('--json')
    ap.add_argument('--bin', help='planned bin dir: check run.json bin_dir and the run-dir exe/dll sha256 vs its MANIFEST')
    ap.add_argument('--j1-info', action='store_true', help='row g16: J1 full_waits = 0 is INFO, not INCOMPLETE')
    a = ap.parse_args(argv)
    files = sc.log_files(a.path)
    if not files:
        print('INCOMPLETE no game log at %s' % a.path)
        return 2
    lines = []
    for p in files:
        with open(p, 'r', encoding='utf-8', errors='replace') as fh:
            lines.extend(fh.readlines())
    res, flags = gate(lines, a.row, n=a.n, min_lines=a.min_lines, j1_info=a.j1_info)
    if a.bin:
        bin_check(res, a.path if os.path.isdir(a.path) else os.path.dirname(os.path.abspath(a.path)), a.bin)
    verdict = 'FAIL' if res.fails else ('INCOMPLETE' if res.incomplete else ('FLAG' if flags else 'PASS'))
    print('r19_gate %s row %s: %s' % (a.path, a.row, ', '.join(os.path.basename(p) for p in files)))
    for ln in res.lines:
        print(ln)
    print('RESULT: %s (%d failed, %d incomplete, %d flags)' % (verdict, len(res.fails), len(res.incomplete), len(flags)))
    if a.json:
        if os.path.dirname(a.json):
            os.makedirs(os.path.dirname(a.json), exist_ok=True)
        with open(a.json, 'w', encoding='ascii', newline='\n') as fh:
            json.dump({'path': a.path, 'row': a.row, 'n': a.n, 'files': files, 'verdict': verdict,
                       'checks': res.lines, 'fails': res.fails, 'incomplete': res.incomplete, 'flags': flags},
                      fh, indent=1)
    return {'FAIL': 1, 'INCOMPLETE': 2, 'FLAG': 3, 'PASS': 0}[verdict]


if __name__ == '__main__':
    sys.exit(main())
