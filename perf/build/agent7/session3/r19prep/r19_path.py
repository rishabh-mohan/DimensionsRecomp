#!/usr/bin/env python3
"""r19_path.py - the two by-machine decisions of the #19 chain (M10 r19-rows-mp-rating C1/C2) (M7, r19prep).

Read-only, stdlib only. Run from WS at Below Normal.
  python -B build/agent7/session3/r19prep/r19_path.py path <r19r10 r19_gate --json>
      prints r19-pathN  (r19_gate --row i --n 4 PASS on r19r10: the menus route splits at N)
             r19-path16 (C2: no FAIL, no FLAG, and the only INCOMPLETE is 'splits > 0 in the last split line')
             STOP       (anything else: write neither marker, report)
  python -B build/agent7/session3/r19prep/r19_path.py noop <r19d r19_gate --json> <r19r25 run dir>
      prints NO-OP OK (C1 points 1 and 3: fails [], flags [], incomplete == only the 'no split was due at this N' entry,
             and r19r25 has 0 'd3d12_submit_split:' counter lines) or STOP. C1 point 2 (s4b_check clean, run valid)
             stays with M3.
  python -B build/agent7/session3/r19prep/r19_path.py bin
      prints READY-R19 OK when devoff4b-r19-bin MANIFEST.txt is 1EBF1163, its rexgpu-xenos.dll is 5DCDD8CB and has the 3
             #19 needles (ROWS-R19 0.1), and devoff4b-bin's rexgpu-xenos.dll (E3CB99CF) has none; else STOP.
Exit 0 for r19-pathN / r19-path16 / NO-OP OK / READY-R19 OK, 1 for STOP.
"""
import hashlib
import json
import os
import sys

NOSPLIT_I = 'splits > 0 in the last split line'
NOSPLIT_D = 'no async counter line: no split was due at this N'
NEEDLES = [b'd3d12_async_submit: needs d3d12_submit_split_kb above 0, staying off',
           b'd3d12_async_submit: submitting splits on the submit thread ({} slots)',
           b'd3d12_async_submit: frame={} submission={} chunks={} queued_max={}']


def bins():
    def rd(p):
        with open(p, 'rb') as fh:
            return fh.read()
    sha = lambda b: hashlib.sha256(b).hexdigest().upper()[:8]  # noqa: E731
    man = sha(rd(os.path.join('build', 'agent2', 'devoff4b-r19-bin', 'MANIFEST.txt')))
    on = rd(os.path.join('build', 'agent2', 'devoff4b-r19-bin', 'rexgpu-xenos.dll'))
    off = rd(os.path.join('build', 'agent2', 'devoff4b-bin', 'rexgpu-xenos.dll'))
    got = (man, sha(on), [x in on for x in NEEDLES], sha(off), [x in off for x in NEEDLES])
    ok = got == ('1EBF1163', '5DCDD8CB', [True] * 3, 'E3CB99CF', [False] * 3)
    return ('READY-R19 OK ' if ok else 'STOP (bin identity) ') + repr(got)


def load(p):
    with open(p, 'r', encoding='ascii') as fh:
        return json.load(fh)


def path(j):
    if j.get('verdict') == 'PASS':
        return 'r19-pathN'
    inc = j.get('incomplete') or []
    if not j.get('fails') and not j.get('flags') and len(inc) == 1 and inc[0].startswith(NOSPLIT_I):
        return 'r19-path16'
    return 'STOP'


def split_counter_lines(run):
    n = 0
    for fn in os.listdir(run):
        if fn == 'game.log' or (fn.startswith('game.') and fn.endswith('.log')):
            with open(os.path.join(run, fn), 'r', encoding='utf-8', errors='replace') as fh:
                n += sum(1 for ln in fh if 'd3d12_submit_split:' in ln)
    return n


def noop(j, r25):
    inc = j.get('incomplete') or []
    ok = not j.get('fails') and not j.get('flags') and len(inc) == 1 and NOSPLIT_D in inc[0]
    if not ok:
        return 'STOP (row d is not the pure no-op shape: fails %s, flags %s, incomplete %s)' % (
            j.get('fails'), j.get('flags'), inc)
    n = split_counter_lines(r25)
    return 'NO-OP OK' if n == 0 else 'STOP (r19r25 has %d split counter lines: discrepancy, report)' % n


def main(argv):
    if len(argv) == 2 and argv[0] == 'path':
        out = path(load(argv[1]))
    elif len(argv) == 3 and argv[0] == 'noop':
        out = noop(load(argv[1]), argv[2])
    elif argv == ['bin']:
        out = bins()
    else:
        print(__doc__)
        return 2
    print(out)
    return 1 if out.startswith('STOP') else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
