"""Agent 10 (task #9): independent cross-check of Agent 9's B static check. Read-only.
Collects the sub_XXXXXXXX and __imp__sub_XXXXXXXX symbols in two linker maps, compares the sets, and counts the
OFF-relevant hook names from the B pass list (agent10-codegen-review.md, "B game gate on devoffB (OFF build)").
Usage: python build\\agent10\\bgate\\hookcheck.py <map A> <map B>"""
import collections
import re
import sys

SYM = re.compile(r'(?<![A-Za-z0-9_])((?:__imp__)?sub_[0-9A-Fa-f]{8})(?![A-Za-z0-9_])')
NAMES = ['MissingAdventureTimeLookupNode', 'RepairDialogueLockReleaseOperand', 'NativeCelShading',
         'sub_83C01C08', 'sub_82A35B90', 'sub_82B7ABF0', 'sub_83E5C88C', 'sub_83E5C830',
         'sub_839C4D08', 'sub_83FC49E8', 'sub_82A33FC4', 'sub_82A3B88C', '__savegprlr', '__restgprlr']


def scan(path):
    subs, imps = set(), set()
    hits = collections.Counter()
    with open(path, encoding='utf-8', errors='replace') as f:
        for ln in f:
            for m in SYM.finditer(ln):
                s = m.group(1)
                (imps if s.startswith('__imp__') else subs).add(s.upper().replace('SUB_', 'sub_').replace('__IMP__', '__imp__'))
            if 'sub_' in ln or '__' in ln or 'Native' in ln or 'Missing' in ln or 'Repair' in ln:
                for n in NAMES:
                    if n in ln:
                        hits[n] += 1
    return subs, imps, hits


a, b = sys.argv[1:3]
sa, ia, ha = scan(a)
sb, ib, hb = scan(b)
print('A %s: sub_ %d, __imp__sub_ %d' % (a, len(sa), len(ia)))
print('B %s: sub_ %d, __imp__sub_ %d' % (b, len(sb), len(ib)))
print('sub_ sets equal: %s (only A %d, only B %d)' % (sa == sb, len(sa - sb), len(sb - sa)))
print('__imp__ sets equal: %s (only A %d, only B %d)' % (ia == ib, len(ia - ib), len(ib - ia)))
for s in sorted(sa - sb)[:10]:
    print('  only A: ' + s)
for s in sorted(sb - sa)[:10]:
    print('  only B: ' + s)
for s in sorted(ia ^ ib)[:10]:
    print('  imp diff: ' + s)
print('hook names (map lines containing the name, A / B):')
for n in NAMES:
    print('  %-34s %4d / %4d%s' % (n, ha[n], hb[n], '' if ha[n] == hb[n] else '   <-- differs'))
