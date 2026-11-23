#!/usr/bin/env python3
# cg26-check.py (Agent 2, board run 2 task #1): the #26 ON regen gates on build/agent2/cg26, and the TU staging.
#
#   python build/agent2/cg26/cg26-check.py --out REPORT [--stage]
#
# new    = build/agent2/cg26/DimensionsRecomp/rexlego/generated  (the S4b tool's regen with the ON toml, new-A)
# pinned = build/agent2/snap1/DimensionsRecomp/rexlego/generated  (the pinned output every OFF bin compiles)
# Gates (Agent 10 b2r row 37): the same file list; the differing files are exactly the 10 A TUs + codegen.stamp,
# codegen.build.stamp (= the new codegen.stamp fingerprint, which must change) and codegen.d (by the tree path only);
# exactly 20 '\tsimde_mm_pause();'
# lines, each right after a '\t// db16cyc ' line, with Agent 9's per-TU / per-function counts; removing them gives
# the pinned file byte-for-byte; codegen.partition.json, sources.cmake and every header unchanged.
# --stage (only when every gate passes): the 10 ON TUs -> cg26/tu, the 10 pinned TUs -> cg26/tu-ctl (only .cpp,
# mtime now), and cg26/list-on.tsv, list-ctl.tsv (recompile.py) and replace-on.txt, replace-ctl.txt (relink.py
# --replace-file). Read-only otherwise, one thread.
import argparse, hashlib, json, os, re, shutil, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
CG = os.path.join(R, 'build', 'agent2', 'cg26')
NEW = os.path.join(CG, 'DimensionsRecomp', 'rexlego', 'generated')
PIN = os.path.join(R, 'build', 'agent2', 'snap1', 'DimensionsRecomp', 'rexlego', 'generated')
EXPECTED = {107: ('sub_83FAF180', 8), 116: ('sub_83F99F80', 2), 205: ('sub_83FCB608', 2), 321: ('sub_83F9A5B0', 2),
            125: ('sub_83E64900', 1), 153: ('sub_83EA90D0', 1), 169: ('sub_83E66CD8', 1), 284: ('sub_83E70320', 1),
            304: ('sub_83E96348', 1), 432: ('sub_83E63F38', 1)}
PAUSE = b'\tsimde_mm_pause();'
SITE = b'\t// db16cyc '
FUNC = re.compile(rb'^DEFINE_REX_FUNC\((sub_[0-9A-F]{8})\)')
OBJ = 'CMakeFiles/legodimensions_recomp.dir/generated/default/%s.obj'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def files(d):
    return sorted(os.path.relpath(os.path.join(dp, fn), d) for dp, _, fns in os.walk(d) for fn in fns)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--stage', action='store_true')
    a = ap.parse_args()
    t0 = time.time()
    out, fails = [], []
    say = out.append

    def check(what, ok, detail=''):
        say('%s %s%s' % ('PASS' if ok else 'FAIL', what, (': ' + detail) if detail else ''))
        if not ok:
            fails.append(what)

    say('# cg26-check (Agent 2, run 2 task #1)  %s' % time.strftime('%Y-%m-%d %H:%M:%S'))
    say('new: %s\npinned: %s' % (os.path.relpath(NEW, R), os.path.relpath(PIN, R)))
    fn, fp = files(NEW), files(PIN)
    check('same file list', fn == fp, '%d files' % len(fn) if fn == fp else 'only new %s; only pinned %s' % (
        sorted(set(fn) - set(fp))[:5], sorted(set(fp) - set(fn))[:5]))
    diff = [r for r in sorted(set(fn) & set(fp)) if os.path.getsize(os.path.join(NEW, r)) !=
            os.path.getsize(os.path.join(PIN, r)) or sha(os.path.join(NEW, r)) != sha(os.path.join(PIN, r))]
    say('differing files (%d): %s' % (len(diff), ' '.join(diff)))
    tus = sorted(r for r in diff if r.endswith('.cpp'))
    want = sorted(os.path.join('default', 'legodimensions_recomp.%d.cpp' % n) for n in EXPECTED)
    check('differing TUs == the 10 A TUs', tus == want, 'extra %s missing %s' % (
        sorted(set(tus) - set(want)), sorted(set(want) - set(tus))) if tus != want else ' '.join(
        os.path.basename(t) for t in tus))
    other = [r for r in diff if not r.endswith('.cpp')]
    for r in other:
        b = os.path.basename(r)
        if b == 'codegen.stamp':
            say('NOTE codegen.stamp differs (expected: its fingerprint digests the toml): %s -> %s' % (
                sha(os.path.join(PIN, r))[:16], sha(os.path.join(NEW, r))[:16]))
            continue
        if b == 'codegen.build.stamp':
            continue  # it holds codegen.stamp's fingerprint, not a path: checked below (Agent 9's 22:15 note)
        if b == 'codegen.d':
            tn = open(os.path.join(NEW, r), 'rb').read()
            tp = open(os.path.join(PIN, r), 'rb').read()
            ok = False
            for pre_n, pre_p in ((os.path.join(R, 'build', 'agent2', 'cg26'), os.path.join(R, 'build', 'agent2',
                                                                                          'snap1')),):
                for f_ in (lambda s: s, lambda s: s.replace('\\', '/'), lambda s: s.lower(),
                           lambda s: s.replace('\\', '/').lower()):
                    if tn.replace(f_(pre_n).encode(), f_(pre_p).encode()) == tp:
                        ok = True
            check('%s differs by the tree path only' % r, ok, '' if ok else '%d vs %d B' % (len(tn), len(tp)))
            continue
        check('%s unchanged' % r, False, 'differs')
    # codegen.build.stamp = the 32-hex "fingerprint" of codegen.stamp (JSON: fingerprint, outputs, version), so it
    # changes with the fingerprint (Agent 9, 22:15): new build.stamp == new fingerprint, pinned == pinned, the
    # fingerprint changed (the regen digested the ON toml), and the stamp's outputs list is unchanged.
    try:
        st = {}
        for tag, d in (('new', NEW), ('pinned', PIN)):
            with open(os.path.join(d, 'default', 'codegen.stamp'), 'r', encoding='utf-8') as f:
                js = json.load(f)
            with open(os.path.join(d, 'default', 'codegen.build.stamp'), 'r', encoding='utf-8') as f:
                st[tag] = (js, f.read().strip())
        (jn, bn), (jp, bp) = st['new'], st['pinned']
        fpn, fpp = jn.get('fingerprint'), jp.get('fingerprint')
        check('codegen.build.stamp == its codegen.stamp fingerprint (new %s, pinned %s)' % (fpn, fpp),
              bn == fpn and bp == fpp, 'new build.stamp %s, pinned build.stamp %s' % (bn, bp))
        check('codegen.stamp fingerprint changed (the regen digested the ON toml)', fpn != fpp, '%s -> %s' % (fpp, fpn))
        check('codegen.stamp outputs list unchanged', jn.get('outputs') == jp.get('outputs'),
              '%d vs %d entries' % (len(jn.get('outputs') or []), len(jp.get('outputs') or [])))
    except (OSError, ValueError) as e:
        check('codegen.stamp / codegen.build.stamp readable', False, str(e))
    for r in ('default/codegen.partition.json', 'default/sources.cmake', 'default/legodimensions_funcs.h'):
        r = r.replace('/', os.sep)
        if r in fn:
            check('%s unchanged' % r, r not in diff, sha(os.path.join(PIN, r))[:16])
    hdrs = [r for r in diff if r.endswith('.h')]
    check('every header unchanged', not hdrs, ' '.join(hdrs))
    total = 0
    for n in sorted(EXPECTED):
        r = os.path.join('default', 'legodimensions_recomp.%d.cpp' % n)
        if r not in fn:
            check('TU %d present' % n, False)
            continue
        ln = open(os.path.join(NEW, r), 'rb').read().split(b'\n')
        cur, cnt, funcs, orphan, keep = None, 0, {}, 0, []
        for i, l in enumerate(ln):
            m = FUNC.match(l)
            if m:
                cur = m.group(1).decode()
            if l.rstrip(b'\r') == PAUSE:
                cnt += 1
                funcs[cur] = funcs.get(cur, 0) + 1
                if i == 0 or not ln[i - 1].startswith(SITE):
                    orphan += 1
                continue
            keep.append(l)
        total += cnt
        stripped = b'\n'.join(keep)
        same = stripped == open(os.path.join(PIN, r), 'rb').read()
        sites_pin = sum(1 for l in open(os.path.join(PIN, r), 'rb').read().split(b'\n') if l.startswith(SITE))
        ef, ec = EXPECTED[n]
        check('TU %d: %d pause(s) in %s, each after a db16cyc site (%d sites), stripped == pinned' % (n, ec, ef,
                                                                                                    sites_pin),
              cnt == ec and funcs == {ef: ec} and orphan == 0 and same and sites_pin == ec,
              'pauses %d %s, orphans %d, stripped==pinned %s, sites %d' % (cnt, funcs, orphan, same, sites_pin))
    check('exactly 20 simde_mm_pause lines', total == 20, '%d' % total)
    # every other TU: no pause line (they are byte-identical when not in diff; checked above)
    res = 'PASS' if not fails else 'FAIL (%d)' % len(fails)
    if a.stage and not fails:
        for sub in ('tu', 'tu-ctl'):
            d = os.path.join(CG, sub)
            if os.path.isdir(d):
                shutil.rmtree(d)
            os.makedirs(d)
        rows_on, rows_ctl, rep_on, rep_ctl = [], [], [], []
        for n in sorted(EXPECTED):
            b = 'legodimensions_recomp.%d.cpp' % n
            pin_src = os.path.join(PIN, 'default', b)
            for sub, src, rows, rep, od in (('tu', os.path.join(NEW, 'default', b), rows_on, rep_on, 'obj-on'),
                                            ('tu-ctl', pin_src, rows_ctl, rep_ctl, 'obj-ctl')):
                dst = os.path.join(CG, sub, b)
                shutil.copyfile(src, dst)
                now = time.time()
                os.utime(dst, (now, now))
                obj = os.path.join(CG, od, b + '.obj')
                rows.append('%s\t%s\t%s' % (pin_src, dst, obj))
                rep.append('%s=%s' % (OBJ % b, obj))
        for name, rows in (('list-on.tsv', rows_on), ('list-ctl.tsv', rows_ctl), ('replace-on.txt', rep_on),
                           ('replace-ctl.txt', rep_ctl)):
            with open(os.path.join(CG, name), 'w', encoding='utf-8', newline='\n') as f:
                f.write('\n'.join(rows) + '\n')
        say('staged: cg26/tu (10 ON TUs), cg26/tu-ctl (10 pinned TUs), list-on.tsv, list-ctl.tsv, replace-on.txt, '
            'replace-ctl.txt')
        for n in sorted(EXPECTED):
            b = 'legodimensions_recomp.%d.cpp' % n
            say('  %s  ON %s  pinned %s' % (b, sha(os.path.join(CG, 'tu', b))[:16], sha(os.path.join(CG, 'tu-ctl',
                                                                                                b))[:16]))
    say('RESULT: %s  (%.1f s)' % (res, time.time() - t0))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, 'w', encoding='ascii', errors='replace', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print('\n'.join(out))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
