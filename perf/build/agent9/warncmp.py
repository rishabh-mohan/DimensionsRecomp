#!/usr/bin/env python3
"""Agent 9 (task #17 item 1a): compare the compiler warnings of a build log with reference build logs by signature:
(source path relative to its snapshot/game/SDK root, warning text with its [-W...] flag), line and column dropped, so a
full build can be checked against incremental ones. Prints the target's signatures that no reference has.
  python build/agent9/warncmp.py [--target build/agent2/snapB3n-native-build.log] [--refs GLOB,...]
                                 [--out build/agent9/logs/warncmp-native.txt]
Exit 0 when every target signature is in some reference and no warning is in generated code; 1 otherwise. Read-only.
"""
import argparse
import collections
import glob
import os
import re
import sys

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W = re.compile(r'^(?P<path>[A-Za-z]:[^:(]+?)(?::(?P<l1>\d+):(?P<c1>\d+)|\((?P<l2>\d+),(?P<c2>\d+)\)):? warning:? (?P<msg>.*)$')
SUBS = [(re.compile(r'(?i)^.*?/build/agent2/snap[^/]*-sdk/'), '<sdk>/'),
        (re.compile(r'(?i)^.*?/build/agent2/snap[^/]*/DimensionsRecomp/'), '<snap>/'),
        (re.compile(r'(?i)^.*?/build/agent2/snap[^/]*-o(?:n|ff)/'), '<game>/')]


def sigs(log):
    c, n = collections.Counter(), 0
    with open(log, encoding='utf-8', errors='replace') as f:
        for raw in f:
            m = W.match(raw.rstrip('\r\n'))
            if not m:
                continue
            n += 1
            p = m.group('path').replace('\\', '/')
            for rx, rep in SUBS:
                p = rx.sub(rep, p)
            c[(p.lower(), m.group('msg').strip())] += 1
    return c, n


def main():
    a2 = os.path.join(R, 'build', 'agent2')
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', default=os.path.join(a2, 'snapB3n-native-build.log'))
    ap.add_argument('--refs', default=os.path.join(a2, '*-native-build.log') + ',' + os.path.join(a2, '*-game-build.log'))
    ap.add_argument('--out', default=os.path.join(R, 'build', 'agent9', 'logs', 'warncmp-native.txt'))
    o = ap.parse_args()
    out = []

    def say(s=''):
        out.append(s)
        print(s)

    tgt = os.path.normcase(os.path.abspath(o.target))
    refs = sorted({os.path.normcase(os.path.abspath(p)) for g in o.refs.split(',') for p in glob.glob(g)} - {tgt})
    tc, tn = sigs(tgt)
    say(f'target {os.path.relpath(tgt, R)}: {tn} warning lines, {len(tc)} signatures')
    union = set()
    for r in refs:
        rc, rn = sigs(r)
        union |= set(rc)
        say(f'  ref {os.path.relpath(r, R)}: {rn} warning lines, {len(rc)} signatures, '
            f'{len(set(rc) & set(tc))} shared with the target')
    gen = [k for k in tc if '/generated/' in k[0]]
    new = [k for k in tc if k not in union]
    say(f'target signatures in generated code: {len(gen)}')
    for k in gen:
        say(f'  GEN {tc[k]}x {k[0]}: {k[1][:200]}')
    say(f'target signatures in no reference: {len(new)}')
    byfile = collections.defaultdict(list)
    for k in new:
        byfile[k[0]].append(k)
    for p in sorted(byfile):
        say(f'  {p}: {len(byfile[p])} signature(s), {sum(tc[k] for k in byfile[p])} line(s)')
        for k in byfile[p][:6]:
            say(f'    {tc[k]}x {k[1][:200]}')
    flags = collections.Counter()
    for k, v in tc.items():
        m = re.search(r'\[(-W[^\]]+)\]\s*$', k[1])
        flags[m.group(1) if m else '?'] += v
    say('target warning lines by flag: ' + ', '.join(f'{f} {n}' for f, n in flags.most_common()))
    ok = not new and not gen
    say(f'RESULT: {"PASS" if ok else "CHECK"}')
    os.makedirs(os.path.dirname(o.out), exist_ok=True)
    with open(o.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
