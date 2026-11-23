#!/usr/bin/env python3
"""placescan: tabulate 'placement buffer relocation' lines across run dirs.

Usage: placescan.py ROOT [ROOT ...] [--grep REGEX] [--route-substr S]
For every game.log under the roots: bin dir and route (from run.json if
present), count of matching lines, and for each line: seconds from the first
log line, thread, the text after 'relocation', and the previous log line.
Read-only.
"""
import argparse, json, os, re, sys
from datetime import datetime

TS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\] \[(\w+)\] \[\w+\] \[t(\d+)\] (.*)$')


def ts(s):
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f')


def run_info(d):
    p = os.path.join(d, 'run.json')
    if not os.path.isfile(p):
        return '-', '-'
    try:
        with open(p, encoding='utf-8-sig') as f:
            j = json.load(f)
    except Exception:
        return '?', '?'
    b = os.path.basename(str(j.get('bin_dir') or '-').rstrip('\\/'))
    r = '-'
    isc = j.get('input_script') or {}
    if isinstance(isc, dict) and isc.get('script'):
        r = os.path.basename(str(isc['script']))
        r += ' %s/%s' % (isc.get('steps_done', '?'), isc.get('steps_total', '?'))
    return b, r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('roots', nargs='+')
    ap.add_argument('--grep', default=r'placement buffer relocation')
    ap.add_argument('--route-substr', default='')
    ap.add_argument('--native-only', action='store_true',
                    help='skip logs without any "Native GPU" line')
    a = ap.parse_args()
    pat = re.compile(a.grep)
    rows = []
    for root in a.roots:
        for dp, dn, fn in os.walk(root):
            dn[:] = [x for x in dn if x not in ('cache', 'user', '.git')]
            if 'game.log' not in fn:
                continue
            b, r = run_info(dp)
            if a.route_substr and a.route_substr not in r:
                continue
            t0 = None
            prev = ''
            hits = []
            native = False
            with open(os.path.join(dp, 'game.log'), encoding='utf-8', errors='replace') as f:
                for line in f:
                    m = TS.match(line.rstrip('\n'))
                    if not m:
                        continue
                    t = ts(m.group(1))
                    if t0 is None:
                        t0 = t
                    msg = m.group(4)
                    if not native and 'Native GPU' in msg:
                        native = True
                    if pat.search(msg):
                        hits.append(((t - t0).total_seconds(), m.group(3), msg, prev))
                    prev = msg
            if a.native_only and not native:
                continue
            rows.append((dp, b, r, hits))
    for dp, b, r, hits in sorted(rows):
        print('%s | bin=%s | route=%s | hits=%d' % (os.path.relpath(dp), b, r, len(hits)))
        for s, tid, msg, prev in hits:
            k = msg.find('relocation')
            print('    %8.2fs t%s %s' % (s, tid, msg[k:] if k >= 0 else msg[:160]))
            print('              prev: %s' % prev[:150])
    print('# runs %d, with hits %d' % (len(rows), sum(1 for x in rows if x[3])))


if __name__ == '__main__':
    sys.exit(main())
