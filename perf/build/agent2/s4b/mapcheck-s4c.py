#!/usr/bin/env python3
# mapcheck-s4c.py (Agent 2, board run 2 task #1): the S4b/S4c link-map check by NAME and OBJECT (never by address).
#
#   python build/agent2/s4b/mapcheck-s4c.py --map NEW.map --ref REF.map --out REPORT [--mode s4c|same]
#          [--expected build/agent9/s4/fence-wait/s4c/expected-map.txt]
#
# Parser and the 'hooked' test are Agent 9's (build/agent9/mapcmp.py, as in maplines.py): a name is hooked when its
# __imp__sub_X public is not at the address of sub_X *in the same map* (no address is compared across maps).
# mode s4c (devoff bins, REF = devoff4-bin's map): the hooked set must be REF's hooked set + the 4 #24 targets
#   (sub_83FBF7D0 sub_83FAF180 sub_83FB09E8 sub_83FC0C10), i.e. the 31 names Agent 9 lists in expected-map.txt;
#   each target's sub_X is defined by gpu_wait_backoff.cpp.obj and its __imp__ alias by the same recompiled TU object
#   as in REF; every other hooked name keeps its sub_ and __imp__ objects; the sub_ and __imp__sub_ name sets are
#   equal; per object, the sub_ names are REF's with only the 4 targets moved into gpu_wait_backoff.cpp.obj, and the
#   __imp__ names per object are unchanged; gpu_wait_backoff.cpp.obj defines no other sub_ public.
# mode same (native4b vs native4-bin, CG26 vs devoff4b): the same checks with nothing moved.
# Read-only, one thread. Exit 0 = PASS.
import argparse, hashlib, os, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
sys.path.insert(0, os.path.join(R, 'build', 'agent9'))
import mapcmp  # noqa: E402

TARGETS = ['sub_83FBF7D0', 'sub_83FAF180', 'sub_83FB09E8', 'sub_83FC0C10']
NEW_OBJ = 'gpu_wait_backoff.cpp.obj'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def load(p):
    _, pubs = mapcmp.parse(p)
    subs, imps, _, _ = mapcmp.summarize(pubs)
    hooked = sorted(n for n, v in imps.items() if subs.get(n, (None, None))[:2] != v[:2])
    return pubs, subs, imps, hooked


def by_obj(table):
    d = {}
    for n, v in table.items():
        d.setdefault(v[2], set()).add(n)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--map', required=True)
    ap.add_argument('--ref', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--mode', choices=('s4c', 'same'), default='s4c')
    ap.add_argument('--expected')
    a = ap.parse_args()
    t0 = time.time()
    out, fails = [], []
    say = out.append

    def check(what, ok, detail=''):
        say('%s %s%s' % ('PASS' if ok else 'FAIL', what, (': ' + detail) if detail else ''))
        if not ok:
            fails.append(what)

    say('# mapcheck-s4c (Agent 2, run 2 task #1; by name and object, not address)  ' +
        time.strftime('%Y-%m-%d %H:%M:%S') + '  mode ' + a.mode)
    for tag, p in (('new', a.map), ('ref', a.ref)):
        st = os.stat(p)
        say('%s: %s  %d B  mtime %s  sha256 %s' % (tag, os.path.relpath(p, R), st.st_size,
                                                   time.strftime('%m-%d %H:%M:%S', time.localtime(st.st_mtime)),
                                                   sha(p)[:16]))
    pn, sn, imn, hn = load(a.map)
    pr, sr, imr, hr = load(a.ref)
    say('new: publics %d; sub_ %d; __imp__sub_ %d; hooked %d' % (len(pn), len(sn), len(imn), len(hn)))
    say('ref: publics %d; sub_ %d; __imp__sub_ %d; hooked %d' % (len(pr), len(sr), len(imr), len(hr)))
    moved = TARGETS if a.mode == 's4c' else []
    # 1. name sets
    d1, d2 = sorted(set(sn) ^ set(sr)), sorted(set(imn) ^ set(imr))
    check('sub_ name set equal to ref', not d1, '%d differ %s' % (len(d1), ' '.join(d1[:10])) if d1 else
          '%d names' % len(sn))
    check('__imp__sub_ name set equal to ref', not d2, '%d differ %s' % (len(d2), ' '.join(d2[:10])) if d2 else
          '%d names' % len(imn))
    # 2. hooked set
    exp = sorted(set(hr) | set(moved))
    extra, missing = sorted(set(hn) - set(exp)), sorted(set(exp) - set(hn))
    check('hooked set = ref hooked (%d) + %d moved = %d' % (len(hr), len(moved), len(exp)), not extra and not missing,
          'have %d%s%s' % (len(hn), (' extra ' + ' '.join(extra)) if extra else '',
                           (' missing ' + ' '.join(missing)) if missing else ''))
    if a.expected:
        lst = None
        with open(a.expected, encoding='utf-8', errors='replace') as f:
            lines = f.read().splitlines()
        for i, l in enumerate(lines):
            if l.startswith('expected hooked set after S4c') and i + 1 < len(lines):
                lst = lines[i + 1].split()
        if lst is None:
            check('expected list found in %s' % os.path.relpath(a.expected, R), False)
        else:
            want = sorted(set(lst)) if a.mode == 's4c' else sorted(set(lst) - set(TARGETS))
            check('hooked set == the %d names in %s%s' % (len(want), os.path.relpath(a.expected, R),
                                                           '' if a.mode == 's4c' else ' minus the 4 targets'),
                  hn == want, '' if hn == want else 'extra %s missing %s' % (sorted(set(hn) - set(want)),
                                                                             sorted(set(want) - set(hn))))
    # 3. moved targets
    for t in moved:
        s, i, ri = sn.get(t), imn.get(t), imr.get(t)
        ok = bool(s and i and ri) and s[2] == NEW_OBJ and i[2] == ri[2] and bool(mapcmp.TU.match(i[2]))
        check('%s: sub_ in %s, __imp__ stays in %s' % (t, NEW_OBJ, ri[2] if ri else '?'), ok,
              'sub_ in %s, __imp__ in %s' % (s[2] if s else 'MISSING', i[2] if i else 'MISSING'))
    # 4. the other hooked names keep their objects
    bad = [n for n in hr if not (n in sn and n in imn and sn[n][2] == sr[n][2] and imn[n][2] == imr[n][2])]
    check('the %d ref-hooked names keep their sub_ and __imp__ objects' % len(hr), not bad,
          ' '.join(bad[:10]) if bad else '')
    # 5. per object sets
    bon, bor = by_obj(sn), by_obj(sr)
    expo = {o: set(v) - set(moved) for o, v in bor.items()}
    if moved:
        expo.setdefault(NEW_OBJ, set()).update(moved)
    expo = {o: v for o, v in expo.items() if v}
    diffo = sorted(o for o in set(bon) | set(expo) if bon.get(o, set()) != expo.get(o, set()))
    check('per-object sub_ sets = ref%s (%d objects)' % (' with the 4 targets moved' if moved else '', len(bon)),
          not diffo, ' '.join(diffo[:8]) if diffo else '')
    ion, ior = by_obj(imn), by_obj(imr)
    diffi = sorted(o for o in set(ion) | set(ior) if ion.get(o, set()) != ior.get(o, set()))
    check('per-object __imp__sub_ sets = ref (%d objects)' % len(ion), not diffi, ' '.join(diffi[:8]) if diffi else '')
    # 6. unhooked names: sub_ and __imp__ in one object
    un = [n for n in sn if n in imn and n not in set(hn) and sn[n][2] != imn[n][2]]
    check('unhooked names: sub_ and __imp__ in the same object', not un, ' '.join(un[:10]) if un else
          '%d names' % (len(sn) - len(hn)))
    # 7. the new object
    newpubs = sorted({p[2] for p in pn if p[3] == NEW_OBJ})
    newsubs = sorted(n for n in newpubs if mapcmp.SUB.match(n))
    check('%s defines exactly the sub_ publics %s' % (NEW_OBJ, ' '.join(moved) if moved else '(none)'),
          newsubs == sorted(moved), 'has %s' % (' '.join(newsubs) or 'none'))
    say('%s publics (%d): %s' % (NEW_OBJ, len(newpubs), ' '.join(newpubs[:40]) or 'none (object not in the map)'))
    say('hooked by sub_ object (new map):')
    hb = {}
    for n in hn:
        hb.setdefault(sn[n][2] if n in sn else '(no sub_ public)', []).append(n)
    for o in sorted(hb):
        say('  %-36s %2d  %s' % (o, len(hb[o]), ' '.join(hb[o])))
    say('RESULT: %s  (%d hooked; %.1f s)' % ('PASS' if not fails else 'FAIL (%d)' % len(fails), len(hn),
                                            time.time() - t0))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, 'w', encoding='ascii', errors='replace', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print('\n'.join(out))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
