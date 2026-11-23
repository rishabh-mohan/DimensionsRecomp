#!/usr/bin/env python3
"""mapdiff_sub2.py - full public-name diff of two lld-link /MAP files by NAME and OBJECT (Agent 2 / sub2).

Uses the parser of mapcheck_sub2.py (same directory; own code).  Lists the names only in NEW, the
names only in REF, and the names whose defining object(s) changed (a multiset per name, so repeated
names such as @vol.md are handled).  It also accounts for the change in the publics line count, and
lists per-object public counts, section-table names, import DLLs and the statics diff.  Symbol lines
are printed as lld writes them; addresses are never compared across maps.
Usage: mapdiff_sub2.py --new NEW.map --ref REF.map --out OUT.txt [--label L]
"""
import argparse
import os
import sys
import time
from collections import Counter, defaultdict

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapcheck_sub2 as mc  # noqa: E402


def decode_const(name):
    for p in ('__xmm@', '__ymm@', '__zmm@', '__real@'):
        if name.startswith(p):
            try:
                b = bytes.fromhex(name[len(p):])
            except ValueError:
                return ''
            mem = b[::-1]
            if mem and all(32 <= c < 127 for c in mem):
                return 'value bytes in memory order as ASCII: "%s"' % mem.decode('ascii')
            return ''
    return ''


def line_of(rec):
    return mc.lld_line(rec[1], rec[2], rec[0], rec[3], rec[4])


def index(mi):
    d = defaultdict(list)
    for rec in mi.publics:
        d[rec[0]].append(rec)
    return d


def main():
    ap = argparse.ArgumentParser(description='full public-name diff of two lld-link maps')
    ap.add_argument('--new', required=True)
    ap.add_argument('--ref', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--label', default='')
    args = ap.parse_args()
    t0 = time.time()
    rmi = mc.parse_map(args.ref, set())
    nmi = mc.parse_map(args.new, set())
    R = index(rmi)
    N = index(nmi)
    out = []
    w = out.append
    w('# mapdiff_sub2: full public-name diff by NAME and OBJECT (Agent 2 / sub2)  %s  %s'
      % (time.strftime('%Y-%m-%d %H:%M:%S'), args.label))
    w('# parser: mapcheck_sub2.parse_map (own parser); symbol lines are re-printed in lld format '
      '(identical to the raw lines when "re-format mismatches" is 0); addresses are not compared across maps')
    bad = False
    for tag, mi in (('NEW', nmi), ('REF', rmi)):
        w('%s: %s  %d B  sha256 %s  lines %d  publics %d  statics %d  unparsed %d  other %d  re-format mismatches %d'
          % (tag, mi.path, mi.size, mi.sha256[:16], mi.nlines, len(mi.publics), len(mi.statics),
             len(mi.unparsed), len(mi.other), len(mi.recon_bad)))
        if mi.unparsed or mi.other or mi.recon_bad or not mi.publics:
            bad = True
    names_r, names_n = set(R), set(N)
    only_new = sorted(names_n - names_r)
    only_ref = sorted(names_r - names_n)
    both = names_n & names_r
    changed = sorted(n for n in both if Counter(r[4] for r in R[n]) != Counter(r[4] for r in N[n]))
    mult = sorted(n for n in both if len(R[n]) != len(N[n]))
    delta = len(nmi.publics) - len(rmi.publics)
    w('')
    w('summary: publics REF %d -> NEW %d (%+d lines); distinct names REF %d -> NEW %d; only in NEW %d; only in REF %d; '
      'in both with changed object(s) %d (of them with a changed repeat count %d)'
      % (len(rmi.publics), len(nmi.publics), delta, len(names_r), len(names_n), len(only_new), len(only_ref),
         len(changed), len(mult)))
    contrib = []
    for n in sorted(names_r | names_n):
        d = len(N.get(n, [])) - len(R.get(n, []))
        if d:
            contrib.append((n, d))
    w('publics line-count accounting (every name whose number of lines changed; sum = %+d):' % sum(d for _, d in contrib))
    for n, d in contrib:
        objs = mc.fmt_objs(tuple(r[4] for r in (N.get(n) or R.get(n))))
        w('  %+d  %s   [%s]' % (d, n, objs))
    if sum(d for _, d in contrib) != delta:
        bad = True
        w('  ERROR: accounting does not add up to %+d' % delta)
    w('')

    def group_by_obj(names, idx):
        g = defaultdict(list)
        for n in names:
            g[mc.fmt_objs(tuple(r[4] for r in idx[n]))].append(n)
        return g

    for title, names, idx in (('names only in NEW', only_new, N), ('names only in REF', only_ref, R)):
        w('%s: %d' % (title, len(names)))
        g = group_by_obj(names, idx)
        for o in sorted(g, key=lambda z: (mc.obj_kind(z.split(' x')[0]), z)):
            w('  %s  [%s]: %d' % (o, mc.obj_kind(o.split(' x')[0]), len(g[o])))
            for n in g[o]:
                kind = mc.name_kind(n) or ''
                dec = decode_const(n)
                note = '; '.join(x for x in (kind, dec) if x)
                w('    %s%s' % (n, ('   (' + note + ')') if note else ''))
                for rec in idx[n][:3]:
                    w('        %s' % line_of(rec))
        w('')
    w('names in both maps whose defining object(s) changed: %d' % len(changed))
    for n in changed:
        w('  %s: %s -> %s%s' % (n, mc.fmt_objs(tuple(r[4] for r in R[n])), mc.fmt_objs(tuple(r[4] for r in N[n])),
                                ('   (' + mc.name_kind(n) + ')') if mc.name_kind(n) else ''))
    w('')
    oc_r = Counter(r[4] for r in rmi.publics)
    oc_n = Counter(r[4] for r in nmi.publics)
    w('objects (publics): REF %d, NEW %d; only in NEW: %s; only in REF: %s' % (
        len(oc_r), len(oc_n), ', '.join(sorted(set(oc_n) - set(oc_r))) or 'none', ', '.join(sorted(set(oc_r) - set(oc_n))) or 'none'))
    chg = ['%s %d->%d' % (o, oc_r.get(o, 0), oc_n.get(o, 0)) for o in sorted(set(oc_r) | set(oc_n)) if oc_r.get(o, 0) != oc_n.get(o, 0)]
    w('per-object public counts that changed: %s' % ('; '.join(chg) if chg else 'none'))
    w('section-table names only in NEW: %s; only in REF: %s' % (
        ' '.join(sorted(set(nmi.secnames) - set(rmi.secnames))) or 'none', ' '.join(sorted(set(rmi.secnames) - set(nmi.secnames))) or 'none'))
    w('')
    rs = Counter((r[0], r[4]) for r in rmi.statics)
    ns = Counter((r[0], r[4]) for r in nmi.statics)
    plus = ns - rs
    minus = rs - ns
    w('statics (name, object) multisets: REF %d -> NEW %d; added %d, removed %d' % (
        len(rmi.statics), len(nmi.statics), sum(plus.values()), sum(minus.values())))
    per = defaultdict(lambda: [[], []])
    for (n, o), c in plus.items():
        per[o][0].extend([n] * c)
    for (n, o), c in minus.items():
        per[o][1].extend([n] * c)
    for o in sorted(per, key=lambda z: (mc.obj_kind(z), z)):
        a, b = per[o]
        w('  %s  [%s]: +%d -%d' % (o, mc.obj_kind(o), len(a), len(b)))
        for n in sorted(a):
            w('    + %s' % n)
        for n in sorted(b):
            w('    - %s' % n)
    w('')
    parts = ['%+d %s [%s]' % (d, n, mc.fmt_objs(tuple(r[4] for r in (N.get(n) or R.get(n))))) for n, d in contrib]
    final = 'RESULT: %s  publics %d -> %d (%+d): %s  (%.1fs)' % (
        'DONE' if not bad else 'PARSE-PROBLEM', len(rmi.publics), len(nmi.publics), delta,
        ', '.join(parts[:12]) + (' ...' if len(parts) > 12 else ''), time.time() - t0)
    w(final)
    with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print('report: %s' % args.out)
    print(final)
    return 2 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
