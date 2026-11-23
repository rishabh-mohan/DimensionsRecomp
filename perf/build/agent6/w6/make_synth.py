#!/usr/bin/env python3
"""Agent 6, task #16: build a synthetic W6-style matrix folder to test w6_kit.py's STUCK, dump and FAIL paths end to end.
Read-only on its sources. Writes only build/agent6/w6/test-synth/W6SYNTH/.
  python -B build/agent6/w6/make_synth.py
Runs: 3 untouched W5 s0 runs (the reference) plus 3 'p2fc' runs made from W5's s0-r1 game.log with s4b-24's real C1
keep-watch lines added:
  r1: gate A's 6 real STUCK-LOCK lines restamped to 20 s into the measured window, plus an empty hang dump -> FAIL
  r2: the same 6 lines restamped after the measured window, plus the hang dump -> NOTE only
  r3: C1 lines only -> PASS
matrix.json = W5's plus a 'p2fc' arm identical to s0, so the cvars/env/bin checks pass.
"""
import datetime
import json
import os
import re
import shutil
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w6_kit as k  # noqa: E402

W5 = os.path.join(k.ROOT, 'build', 'agent8', 'matrix', '20261122-1756')
GATEA = os.path.join(k.ROOT, 'build', 'agent3', 'runs', '20261122-210906-w6-gateA-p2fcv-level')
S4B24 = os.path.join(k.ROOT, 'build', 'agent3', 'runs', '20261122-220520-s4b-24-w6-c1')
OUT = os.path.join(HERE, 'test-synth', 'W6SYNTH')
TS_RE = re.compile(r'^\[(\d{4}-\d\d-\d\d [0-9:.]+)\] (.*)$')
FMT = '%Y-%m-%d %H:%M:%S.%f'


def read_lines(rd):
    out = []
    for fp in k.log_files(rd):
        with open(fp, encoding='utf-8', errors='replace') as fh:
            out += [x.rstrip('\r\n') for x in fh if x.strip()]
    return out


def ts_of(line):
    m = TS_RE.match(line)
    return datetime.datetime.strptime(m.group(1), FMT) if m else None


def restamp(line, dt):
    m = TS_RE.match(line)
    return '[%s] %s' % (dt.strftime(FMT)[:-3], m.group(2) if m else line)


def insert_at_time(lines, new, dt):
    """Insert new lines before the first line later than dt, but never inside the 3-line clean-exit tail."""
    pos = len(lines) - 3
    for i, x in enumerate(lines[:-3]):
        t = ts_of(x)
        if t and t > dt:
            pos = i
            break
    return lines[:pos] + new + lines[pos:]


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'runs'))
    stuck = [x for x in read_lines(GATEA) if any(t in x for t in k.EP_TEXTS)]
    c1_on = next(x for x in read_lines(S4B24) if 'C1 keep-watch: on' in x)
    c1_first = next(x for x in read_lines(S4B24) if 'C1 keep-watch: first kept protect at' in x)
    after = float(k.AFTER_RE.search(stuck[0]).group(1))
    dump = os.path.basename(k.DUMP_RE.search(next(x for x in stuck if 'Minidump written to' in x)).group(1).strip('"\''))
    print('gate A STUCK lines %d (after %.2f s, dump %s); C1 lines from s4b-24:\n  %s\n  %s'
          % (len(stuck), after, dump, c1_on[:160], c1_first[:160]))
    for name in ('1800-s0-r1', '1808-s0-r2', '1827-s0-r3'):
        src, dst = os.path.join(W5, 'runs', name), os.path.join(OUT, 'runs', name)
        os.makedirs(dst)
        for f in os.listdir(src):
            if k.ROT_RE.match(f) or f in ('run.json', 'sys.csv'):
                shutil.copy2(os.path.join(src, f), dst)
    src = os.path.join(W5, 'runs', '1800-s0-r1')
    rj = k.load_json(os.path.join(src, 'run.json'))
    ms = datetime.datetime.strptime(rj['measure_start']['wall'], FMT)
    me = datetime.datetime.strptime(rj['measure_end']['wall'], FMT)
    base = read_lines(src)
    t_c1 = next(t for t in map(ts_of, base[5:]) if t)  # the log starts with a few unstamped banner lines
    for name, t1 in (('1830-p2fc-r1', ms + datetime.timedelta(seconds=20)),
                     ('1832-p2fc-r2', me + datetime.timedelta(seconds=after + 3)),
                     ('1834-p2fc-r3', None)):
        dst = os.path.join(OUT, 'runs', name)
        os.makedirs(dst)
        lines = base[:6] + [restamp(c1_on, t_c1), restamp(c1_first, t_c1)] + base[6:]
        if t1 is not None:
            new = [restamp(x, t1 + datetime.timedelta(milliseconds=i)) for i, x in enumerate(stuck)]
            lines = insert_at_time(lines, new, t1)
            open(os.path.join(dst, dump), 'wb').close()
        with open(os.path.join(dst, 'game.log'), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(lines) + '\n')
        for f in ('run.json', 'sys.csv'):
            shutil.copy2(os.path.join(src, f), dst)
        print('%s: %d lines, stall %s' % (name, len(lines), t1))
    mj = k.load_json(os.path.join(W5, 'matrix.json'))
    s0 = next(a for a in mj['arms'] if str(a.get('id')).lower() == 's0')
    p2fc = dict(s0)
    p2fc['id'] = 'p2fc'
    mj['arms'].append(p2fc)
    with open(os.path.join(OUT, 'matrix.json'), 'w', encoding='utf-8') as fh:
        json.dump(mj, fh, indent=1)
    print('measured window %s .. %s; wrote %s' % (ms, me, os.path.relpath(OUT, k.ROOT)))


if __name__ == '__main__':
    main()
