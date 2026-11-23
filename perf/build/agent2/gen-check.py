"""Agent 2 - gen-check: the snapshot's pinned codegen output must equal its reference copy (task #1 follow-on, 20:50;
reference/snapshot arguments added 23:40 for Agent 9's codegen build B).

The snapshot game trees run the codegen edge with a stand-in that writes nothing (Agent 1, 20:25: codegen must not be
able to change the TUs): build/agent2/codegen-frozen/codegen-frozen.exe in snap1-off/snap1-on, codegen-frozen2.exe (any
TU count) in snapB-off. This gate runs before every game build and checks the snapshot's rexlego/generated against the
reference:
  - the same relative file set (default: 887 files: 440 TUs, headers, stamps, sources.cmake, partition json, codegen.d);
  - every file sha256-identical, except codegen.d;
  - codegen.d must be the reference's with the --base-rex path replaced by the snapshot rexlego path (so ninja's deps
    for the codegen edge name the snapshot's stamp, config and manifest). If it is still the reference's byte-for-byte,
    it is rewritten here (once) and re-checked. The reference's codegen.d must name --base-rex, and the snapshot must
    resolve under build/agent2 (the live rexlego/generated is a junction to baseline/: never rewrite through it).
Defaults (unchanged): reference baseline/DimensionsRecomp/rexlego/generated, snapshot
build/agent2/snap1/DimensionsRecomp/rexlego/generated, --base-rex baseline/DimensionsRecomp/rexlego.
Build B: --base build/agent9/install/batch-nolr/generated (Agent 9's batch-nolr output in baseline layout, with
baseline's rexglue.cmake and codegen.d, so --base-rex stays the default; never install/batch, which has skip_lr) --snap
build/agent2/snapB/DimensionsRecomp/rexlego/generated (--snap-rex defaults to the parent of --snap).
Exit 0 and 'RESULT: PASS', or exit 1 and 'RESULT: FAIL'.
Usage: python build\\agent2\\gen-check.py [--base DIR] [--snap DIR] [--snap-rex DIR] [--base-rex DIR]
"""
import argparse, hashlib, os, sys, time

R = r'<workspace>'
BASE = os.path.join(R, r'baseline\DimensionsRecomp\rexlego\generated')
SNAP = os.path.join(R, r'build\agent2\snap1\DimensionsRecomp\rexlego\generated')
BASE_REX = (R + r'\baseline\DimensionsRecomp\rexlego').replace('\\', '/')
SNAP_REX = (R + r'\build\agent2\snap1\DimensionsRecomp\rexlego').replace('\\', '/')
DEPFILE = 'default' + os.sep + 'codegen.d'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def files(root):
    out = set()
    for dp, dn, fn in os.walk(root):
        for n in fn:
            out.add(os.path.relpath(os.path.join(dp, n), root))
    return out


def main():
    global BASE, SNAP, BASE_REX, SNAP_REX
    ap = argparse.ArgumentParser(description='snapshot rexlego/generated == reference (codegen.d on snapshot paths)')
    ap.add_argument('--base', help='reference generated/ dir (default: baseline)')
    ap.add_argument('--snap', help='snapshot generated/ dir (default: snap1)')
    ap.add_argument('--snap-rex', help='snapshot rexlego dir for the codegen.d rewrite (default: parent of --snap)')
    ap.add_argument('--base-rex', help='rexlego dir the reference codegen.d names (default: baseline rexlego)')
    a = ap.parse_args()
    if a.base:
        BASE = os.path.abspath(a.base)
    if a.snap:
        SNAP = os.path.abspath(a.snap)
        SNAP_REX = os.path.dirname(SNAP).replace('\\', '/')
    if a.snap_rex:
        SNAP_REX = os.path.abspath(a.snap_rex).replace('\\', '/')
    if a.base_rex:
        BASE_REX = os.path.abspath(a.base_rex).replace('\\', '/')
    t0 = time.time()
    fails = []
    agent2 = os.path.normcase(os.path.join(R, 'build', 'agent2')) + os.sep
    for what, p in (('snapshot', SNAP), ('snapshot rexlego', SNAP_REX)):
        rp = os.path.normcase(os.path.realpath(p))
        if not rp.startswith(agent2):
            print('# gen-check: refusing: the %s %s resolves to %s, outside build/agent2' % (what, p, rp))
            print('RESULT: FAIL (1)')
            return 1
    for what, p in (('reference', BASE), ('snapshot', SNAP)):
        if not os.path.isdir(p):
            fails.append('%s dir missing: %s' % (what, p))
    print('# reference %s; snapshot %s; codegen.d paths %s -> %s' % (BASE, SNAP, BASE_REX, SNAP_REX))
    b, s = files(BASE), files(SNAP)
    for r in sorted(b - s):
        fails.append('missing in snapshot: ' + r)
    for r in sorted(s - b):
        fails.append('extra in snapshot: ' + r)
    total = same = 0
    for r in sorted(b & s):
        if r == DEPFILE:
            continue
        total += os.path.getsize(os.path.join(BASE, r))
        if sha(os.path.join(BASE, r)) == sha(os.path.join(SNAP, r)):
            same += 1
        else:
            fails.append('differs: ' + r)
    note = 'codegen.d: missing'
    if DEPFILE in b and DEPFILE in s:
        bd = open(os.path.join(BASE, DEPFILE), 'rb').read()
        if BASE_REX.encode() not in bd:
            fails.append('the reference codegen.d does not name ' + BASE_REX)
        want = bd.replace(BASE_REX.encode(), SNAP_REX.encode())
        sp = os.path.join(SNAP, DEPFILE)
        cur = open(sp, 'rb').read()
        if cur == bd and want != bd:
            with open(sp, 'wb') as f:
                f.write(want)
            cur = open(sp, 'rb').read()
            note = 'codegen.d: rewritten to snapshot paths (%d -> %d bytes)' % (len(bd), len(cur))
        else:
            note = 'codegen.d: already has snapshot paths'
        if cur != want or BASE_REX.encode() in cur:
            fails.append('codegen.d is neither the reference\'s nor its snapshot-path rewrite')
    print('# gen-check %s: reference %d files, snapshot %d files; %d/%d compared files identical (%.1f MB); %s; %.1fs'
          % (time.strftime('%H:%M:%S'), len(b), len(s), same, len(b & s) - 1, total / 1e6, note, time.time() - t0))
    for f in fails[:50]:
        print('FAIL ' + f)
    print('RESULT: ' + ('FAIL (%d)' % len(fails) if fails else 'PASS'))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
