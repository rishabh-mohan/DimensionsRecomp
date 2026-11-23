#!/usr/bin/env python3
"""Warning/error type table across game runs (read-only).

usage: warntypes.py --run LABEL=RUNDIR [--run ...] [--out FILE] [--top N]
Reads game.N.log (rotated, oldest first) then game.log in each run dir.
A line counts if it has [warning], [error] or [critical]. The type is the
message with the timestamp, thread id, hex and decimal numbers normalized.
Also prints exact counts for a few named signatures (the placement shaders).
"""
import argparse
import glob
import os
import re
import sys

LEVEL = re.compile(r'\[(warning|error|critical)\]')
TS = re.compile(r'^\[\d{4}-\d\d-\d\d [\d:.]+\]\s*')
TID = re.compile(r'\[t\d+\]')
HEX = re.compile(r'0x[0-9A-Fa-f]+')
NUM = re.compile(r'(?<![A-Za-z_])\d+(\.\d+)?')

NAMED = [
    ('hash0', 'hash=0x0000000000000000'),
    ('placement-missing VS 0xAC449538', None),
    ('placement-missing PS 0xAC448F28', None),
    ('unrecognized PS 0xAC448F28', None),
    ('unrecognized VS 0xAC449538', None),
]


def logs_of(run):
    rot = sorted(glob.glob(os.path.join(run, 'game.*.log')),
                 key=lambda p: -int(re.search(r'game\.(\d+)\.log$', p).group(1)) if re.search(r'game\.(\d+)\.log$', p) else 0)
    out = [p for p in rot if re.search(r'game\.\d+\.log$', p)]
    if os.path.exists(os.path.join(run, 'game.log')):
        out.append(os.path.join(run, 'game.log'))
    return out


def norm(line):
    s = TS.sub('', line.rstrip())
    s = TID.sub('[t]', s)
    s = HEX.sub('0x#', s)
    s = NUM.sub('#', s)
    return s[:200]


def scan(run):
    types = {}
    named = {k: 0 for k, _ in NAMED}
    for p in logs_of(run):
        with open(p, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                if not LEVEL.search(line):
                    continue
                t = norm(line)
                types[t] = types.get(t, 0) + 1
                if 'hash=0x0000000000000000' in line:
                    named['hash0'] += 1
                low = line.lower()
                if 'missing from aot index' in low:
                    if '0xac449538' in low:
                        named['placement-missing VS 0xAC449538'] += 1
                    if '0xac448f28' in low:
                        named['placement-missing PS 0xAC448F28'] += 1
                if 'unrecognized' in low:
                    if '0xac448f28' in low:
                        named['unrecognized PS 0xAC448F28'] += 1
                    if '0xac449538' in low:
                        named['unrecognized VS 0xAC449538'] += 1
    return types, named


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', action='append', required=True, help='LABEL=RUNDIR')
    ap.add_argument('--out')
    ap.add_argument('--top', type=int, default=60)
    a = ap.parse_args()
    runs = []
    for r in a.run:
        label, _, d = r.partition('=')
        runs.append((label, d))
    res = [(label, d) + scan(d) for label, d in runs]
    lines = []
    lines.append('runs: ' + '; '.join('%s=%s' % (l, d) for l, d in runs))
    lines.append('')
    lines.append('named signatures:')
    hdr = '  %-34s' % 'signature' + ''.join('%14s' % l[:13] for l, _ in runs)
    lines.append(hdr)
    for k, _ in NAMED:
        lines.append('  %-34s' % k + ''.join('%14d' % r[3][k] for r in res))
    lines.append('')
    alltypes = {}
    for r in res:
        for t, c in r[2].items():
            alltypes[t] = alltypes.get(t, 0) + c
    lines.append('warning/error types (%d distinct), counts per run:' % len(alltypes))
    lines.append('  ' + ''.join('%9s' % l[:8] for l, _ in runs) + '  type')
    for t, _ in sorted(alltypes.items(), key=lambda kv: -kv[1])[:a.top]:
        lines.append('  ' + ''.join('%9d' % r[2].get(t, 0) for r in res) + '  ' + t)
    lines.append('')
    lines.append('totals: ' + ', '.join('%s %d lines / %d types' % (r[0], sum(r[2].values()), len(r[2])) for r in res))
    text = '\n'.join(lines) + '\n'
    if a.out:
        with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
