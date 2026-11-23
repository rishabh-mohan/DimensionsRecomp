#!/usr/bin/env python3
"""pairall: run the 1b route-pair checks on a BASE (native3d) and a CAND (nativeB) run dir.

Usage: pairall.py --base RUNDIR --cand RUNDIR --tag TAG [--head N]
Runs one tool at a time (one thread): bgate/logdiff.py, nb/nativelines.py, nb/warntypes.py,
nb/placescan.py (on the two run dirs only), nb/framepso.py and nb/exitpress.py. Writes
build/agent10/nb/<tool>-<TAG>.txt and prints each report's exit code and head. Read-only on
the run dirs.
"""
import argparse
import os
import subprocess
import sys

NB = os.path.dirname(os.path.abspath(__file__))
A10 = os.path.dirname(NB)
ROOT = os.path.dirname(os.path.dirname(A10))


def run(cmd, out):
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        p = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        f.write(p.stdout.decode('utf-8', 'replace').replace('\r\n', '\n'))
    return p.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True)
    ap.add_argument('--cand', required=True)
    ap.add_argument('--tag', required=True)
    ap.add_argument('--head', type=int, default=14)
    a = ap.parse_args()
    py = sys.executable
    o = lambda name: os.path.join(NB, '%s-%s.txt' % (name, a.tag))
    jobs = [
        ('logdiff', [py, os.path.join(A10, 'bgate', 'logdiff.py'), '--base', a.base, '--cand', a.cand], o('logdiff')),
        ('nativelines', [py, os.path.join(NB, 'nativelines.py'), '--base', a.base, '--cand', a.cand,
                         '--out', o('nativelines')], o('nativelines-stdout')),
        ('warntypes', [py, os.path.join(NB, 'warntypes.py'), '--run', 'native3d=' + a.base, '--run',
                       'nativeB=' + a.cand, '--out', o('warntypes')], o('warntypes-stdout')),
        ('placescan', [py, os.path.join(NB, 'placescan.py'), a.base, a.cand], o('placescan')),
        ('framepso', [py, os.path.join(NB, 'framepso.py'), a.base, a.cand, '--top', '6'], o('framepso')),
        ('exitpress', [py, os.path.join(NB, 'exitpress.py'), a.base, a.cand], o('exitpress')),
    ]
    for name, cmd, out in jobs:
        rc = run(cmd, out)
        report = o(name) if name in ('nativelines', 'warntypes') else out
        print('######## %s exit %d -> %s' % (name, rc, os.path.relpath(report, ROOT)))
        try:
            with open(report, encoding='utf-8', errors='replace') as f:
                lines = f.read().splitlines()
        except OSError as e:
            lines = ['(no report: %s)' % e]
        for ln in lines[:a.head]:
            print('  ' + ln[:240])
        if len(lines) > a.head:
            print('  ... (%d lines)' % len(lines))
    return 0


if __name__ == '__main__':
    sys.exit(main())
