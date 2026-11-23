#!/usr/bin/env python3
"""B-gate log diff (Agent 8, session 3): checks a B game log against an A (baseline) game log. Stdlib only.

  python bench/agent8/run/gate_logdiff.py --a <A game.log | A run dir> --b <B game.log | B run dir>
                                          [--json OUT] [--top N] [--unimpl-regex RE] [--quiet]

Input: a game.log path or a run dir. The game rotates its log at 5 MB (game.1.log, then a new game.log), so every
game*.log next to the given file is read, oldest first (game.N.log ... game.1.log, game.log). If the oldest file has
no early boot line ('GPU route:' on native builds, 'DXGI adapter' / 'Direct3D 12 device' on OFF builds), boot lines
were rotated away: that is reported as 'boot lines missing' (the presence checks below may then be wrong).

Checks (Agent 10's B-gate proposal, perf-notes/agent10-codegen-review.md, 'B native game gate'):
  FAIL if B has ANY line with: REX_FATAL, __builtin_trap, 'Switch case out of range', 'not in any registered module',
       'Native GPU: pool copy unsupported', 'pool copy POINTLIST contract mismatch',
       'Native slot heap: external detach verification failed', 0xC0000409, 'stack overflow', or a [critical] level line.
       A's count is shown for context; a pattern that A also has is still a B FAIL.
  FAIL if B has more unimplemented-instruction lines than A (REX_UNIMPLEMENTED / 'unimplemented instruction|opcode';
       the vupkd3d128 gap is pre-existing, so equal counts pass).
  MATCH (FAIL on mismatch; native builds only, both 0 on OFF builds):
       'Native GPU: placement buffer relocation ... lr=83F9B660': present in B if present in A (counts are route-
       dependent, so they are shown, not compared);
       the set of callers in 'Native GPU: CPU pool copy ... caller=XXXXXXXX' must be equal;
       'Native slot heap: registered' and 'Native slot heap: extended': present in B if present in A.
  DIFF (review, not a FAIL by itself): the [warning]/[error]/[critical] messages of both logs, normalised (timestamp
       and [tNNN] dropped; 0x.. hex, 8+ digit hex words, decimal numbers and run-dir names replaced): messages new in
       B, messages gone in B, and count changes of at least 2x and 5 lines (route length changes counts).
Exit: 0 pass, 1 a FAIL finding, 2 usage error / log missing.
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

LINE_RE = re.compile(r'^\[(?P<ts>\d{4}-\d\d-\d\d [0-9:.]+)\] \[(?P<lvl>[a-z]+)\] \[(?P<cat>[^\]]*)\] (?:\[t\d+\] )?(?P<msg>.*)$')
ROT_RE = re.compile(r'^game(?:\.(\d+))?\.log$', re.I)
BOOT_RE = re.compile(r'GPU route:|DXGI adapter|Direct3D 12 device')
WARN_LEVELS = ('warning', 'error', 'critical')

FAIL_PATTERNS = [
    ('REX_FATAL', re.compile(r'REX_FATAL')),
    ('__builtin_trap', re.compile(r'__builtin_trap')),
    ('Switch case out of range', re.compile(r'Switch case out of range', re.I)),
    ('not in any registered module', re.compile(r'not in any registered module')),
    ('Native GPU: pool copy unsupported', re.compile(r'Native GPU: pool copy unsupported')),
    ('pool copy POINTLIST contract mismatch', re.compile(r'pool copy POINTLIST contract mismatch')),
    ('Native slot heap: external detach verification failed', re.compile(r'Native slot heap: external detach verification failed')),
    ('0xC0000409', re.compile(r'0xC0000409', re.I)),
    ('stack overflow', re.compile(r'stack overflow', re.I)),
]
UNIMPL_DEFAULT = r'(?i)REX_UNIMPLEMENTED|unimplemented (?:ppc )?instruction|unimplemented opcode'
RELOC_RE = re.compile(r'Native GPU: placement buffer relocation.*lr=83F9B660', re.I)
POOLCOPY_RE = re.compile(r'Native GPU: CPU pool copy .*?caller=([0-9A-Fa-f]{8})')
SLOT_REG_RE = re.compile(r'Native slot heap: registered')
SLOT_EXT_RE = re.compile(r'Native slot heap: extended')

NORM = [
    (re.compile(r'runs[\\/][0-9]{4}-[^\\/\s\'"]+'), 'runs/<run>'),
    (re.compile(r'0x[0-9A-Fa-f]+'), '0x#'),
    (re.compile(r'\b[0-9A-Fa-f]{8,16}\b'), '#h'),
    (re.compile(r'\d+(?:\.\d+)?'), '#'),
]


def log_files(path):
    """The rotated game*.log set for a file or run dir, oldest first."""
    if os.path.isdir(path):
        d = path
    else:
        d = os.path.dirname(os.path.abspath(path))
    found = []
    for p in glob.glob(os.path.join(d, 'game*.log')):
        m = ROT_RE.match(os.path.basename(p))
        if m:
            found.append((int(m.group(1)) if m.group(1) else 0, p))
    found.sort(key=lambda t: -t[0])  # highest rotation index = oldest
    return [p for _, p in found]


def norm(msg):
    for rx, rep in NORM:
        msg = rx.sub(rep, msg)
    return msg


def scan(path, unimpl_re):
    files = log_files(path)
    r = dict(input=os.path.abspath(path), files=[], lines=0, levels=Counter(), boot_lines_found=False,
             fail=Counter(), fail_examples={}, unimpl=0, unimpl_examples=[], reloc=0, poolcopy_callers=Counter(),
             slot_registered=0, slot_extended=0, warn=Counter(), warn_example={}, critical=0, critical_examples=[])
    for i, fp in enumerate(files):
        r['files'].append(dict(path=fp, bytes=os.path.getsize(fp)))
        with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
            for raw in fh:
                line = raw.rstrip('\r\n')
                if not line:
                    continue
                r['lines'] += 1
                if i == 0 and not r['boot_lines_found'] and BOOT_RE.search(line):
                    r['boot_lines_found'] = True
                m = LINE_RE.match(line)
                lvl = m.group('lvl') if m else ''
                msg = m.group('msg') if m else line
                if m:
                    r['levels'][lvl] += 1
                for name, rx in FAIL_PATTERNS:
                    if rx.search(line):
                        r['fail'][name] += 1
                        r['fail_examples'].setdefault(name, line[:300])
                if unimpl_re.search(line):
                    r['unimpl'] += 1
                    if len(r['unimpl_examples']) < 3:
                        r['unimpl_examples'].append(line[:300])
                if RELOC_RE.search(line):
                    r['reloc'] += 1
                pc = POOLCOPY_RE.search(line)
                if pc:
                    r['poolcopy_callers'][pc.group(1).upper()] += 1
                if SLOT_REG_RE.search(line):
                    r['slot_registered'] += 1
                if SLOT_EXT_RE.search(line):
                    r['slot_extended'] += 1
                if lvl == 'critical':
                    r['critical'] += 1
                    if len(r['critical_examples']) < 3:
                        r['critical_examples'].append(line[:300])
                if lvl in WARN_LEVELS:
                    key = '[%s] [%s] %s' % (lvl, m.group('cat'), norm(msg))
                    r['warn'][key] += 1
                    r['warn_example'].setdefault(key, line[:300])
    return r


def compare(a, b, top):
    findings, notes = [], []
    if not b['files']:
        findings.append('B: no game*.log found at %s' % b['input'])
    for name, _ in FAIL_PATTERNS:
        nb, na = b['fail'][name], a['fail'][name]
        if nb:
            findings.append('B has %d line(s) with "%s" (A: %d). First: %s' % (nb, name, na, b['fail_examples'][name]))
    if b['critical']:
        findings.append('B has %d [critical] line(s) (A: %d). First: %s' % (b['critical'], a['critical'], b['critical_examples'][0]))
    if b['unimpl'] > a['unimpl']:
        findings.append('B has more unimplemented-instruction lines than A: %d vs %d. First B: %s'
                        % (b['unimpl'], a['unimpl'], (b['unimpl_examples'] or [''])[0]))
    match = []
    if a['reloc'] and not b['reloc']:
        findings.append('placement buffer relocation lr=83F9B660: A has %d line(s), B has none' % a['reloc'])
    match.append('placement buffer relocation lr=83F9B660: A %d, B %d (route-dependent count; presence must match)'
                 % (a['reloc'], b['reloc']))
    ca, cb = set(a['poolcopy_callers']), set(b['poolcopy_callers'])
    if ca != cb:
        findings.append('CPU pool copy caller sets differ: only A %s, only B %s'
                        % (sorted(ca - cb) or '-', sorted(cb - ca) or '-'))
    match.append('CPU pool copy callers: A %s, B %s' % (dict(sorted(a['poolcopy_callers'].items())) or '-',
                                                       dict(sorted(b['poolcopy_callers'].items())) or '-'))
    for key, label in (('slot_registered', 'Native slot heap: registered'), ('slot_extended', 'Native slot heap: extended')):
        if a[key] and not b[key]:
            findings.append('%s: A has %d line(s), B has none' % (label, a[key]))
        match.append('%s: A %d, B %d' % (label, a[key], b[key]))
    for side, s in (('A', a), ('B', b)):
        if s['files'] and not s['boot_lines_found']:
            notes.append('%s: boot lines missing from the oldest log (rotated away?): presence checks may be wrong' % side)
        if len(s['files']) > 1:
            notes.append('%s: %d log files (rotated at 5 MB)' % (side, len(s['files'])))
    wa, wb = a['warn'], b['warn']
    new = sorted(((k, wb[k]) for k in wb if k not in wa), key=lambda kv: -kv[1])
    gone = sorted(((k, wa[k]) for k in wa if k not in wb), key=lambda kv: -kv[1])
    changed = []
    for k in wa:
        if k in wb:
            x, y = wa[k], wb[k]
            if abs(y - x) >= 5 and (y >= 2 * x or x >= 2 * y):
                changed.append((k, x, y))
    changed.sort(key=lambda t: -abs(t[2] - t[1]))
    diff = dict(
        new_in_b=[dict(msg=k, count=c, example=b['warn_example'][k]) for k, c in new[:top]],
        new_in_b_total=len(new),
        gone_in_b=[dict(msg=k, count=c, example=a['warn_example'][k]) for k, c in gone[:top]],
        gone_in_b_total=len(gone),
        count_changes=[dict(msg=k, a=x, b=y) for k, x, y in changed[:top]],
        count_changes_total=len(changed),
    )
    return findings, notes, match, diff


def side_summary(s):
    return dict(input=s['input'], files=s['files'], lines=s['lines'], levels=dict(s['levels']),
                boot_lines_found=s['boot_lines_found'], fail_counts=dict(s['fail']), critical=s['critical'],
                unimplemented=s['unimpl'], unimplemented_examples=s['unimpl_examples'], reloc_lr_83F9B660=s['reloc'],
                poolcopy_callers=dict(s['poolcopy_callers']), slot_registered=s['slot_registered'],
                slot_extended=s['slot_extended'], warn_messages=len(s['warn']), warn_lines=sum(s['warn'].values()))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--a', required=True, help='A (baseline) game.log or run dir')
    ap.add_argument('--b', required=True, help='B game.log or run dir')
    ap.add_argument('--json', help='write the full result as JSON')
    ap.add_argument('--top', type=int, default=25, help='rows per diff table (default 25)')
    ap.add_argument('--unimpl-regex', default=UNIMPL_DEFAULT, help='unimplemented-instruction line regex')
    ap.add_argument('--quiet', action='store_true')
    try:
        args = ap.parse_args()
    except SystemExit as e:
        return 2 if e.code else 0
    for p in (args.a, args.b):
        if not os.path.exists(p):
            print('no such file or dir: %s' % p, file=sys.stderr)
            return 2
    try:
        unimpl_re = re.compile(args.unimpl_regex)
    except re.error as e:
        print('bad --unimpl-regex: %s' % e, file=sys.stderr)
        return 2
    a, b = scan(args.a, unimpl_re), scan(args.b, unimpl_re)
    if not a['files'] or not b['files']:
        print('no game*.log found for %s' % ('A' if not a['files'] else 'B'), file=sys.stderr)
        return 2
    findings, notes, match, diff = compare(a, b, args.top)
    verdict = 'FAIL' if findings else 'PASS'
    res = dict(verdict=verdict, findings=findings, notes=notes, match=match, diff=diff,
               a=side_summary(a), b=side_summary(b), fail_patterns=[n for n, _ in FAIL_PATTERNS],
               unimpl_regex=args.unimpl_regex)
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as fh:
            json.dump(res, fh, indent=2)
    if not args.quiet:
        out = []
        w = out.append
        w('=== gate_logdiff: %s ===' % verdict)
        for side, s in (('A', a), ('B', b)):
            w('%s  %s: %d lines in %d file(s) (%s); levels %s' % (
                side, s['input'], s['lines'], len(s['files']),
                ', '.join('%s %d B' % (os.path.basename(f['path']), f['bytes']) for f in s['files']),
                ' '.join('%s=%d' % kv for kv in sorted(s['levels'].items()))))
        for n in notes:
            w('note  %s' % n)
        w('')
        w('FAIL findings: %s' % ('none' if not findings else len(findings)))
        for f in findings:
            w('  !!! %s' % f)
        w('unimplemented-instruction lines: A %d, B %d' % (a['unimpl'], b['unimpl']))
        w('match checks:')
        for m in match:
            w('  %s' % m)
        w('')
        w('warning/error messages (normalised): A %d kinds / %d lines, B %d kinds / %d lines' % (
            len(a['warn']), sum(a['warn'].values()), len(b['warn']), sum(b['warn'].values())))
        w('new in B (%d):' % diff['new_in_b_total'])
        for x in diff['new_in_b']:
            w('  %5d  %s' % (x['count'], x['msg'][:220]))
        w('gone in B (%d):' % diff['gone_in_b_total'])
        for x in diff['gone_in_b']:
            w('  %5d  %s' % (x['count'], x['msg'][:220]))
        w('count changes >= 2x and >= 5 lines (%d):' % diff['count_changes_total'])
        for x in diff['count_changes']:
            w('  A %5d  B %5d  %s' % (x['a'], x['b'], x['msg'][:200]))
        print('\n'.join(out))
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
