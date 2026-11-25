#!/usr/bin/env python3
# apply-check-s3.py (M2, session 3, S3T-2): re-run PENDING-DIFFS' hash and apply checks against current HEAD,
# read-only. Writes only --out and build/agent2/session3/s33-popin-no5.patch (the S1 copy, hunk #5 dropped).
#
#   python build/agent2/session3/apply-check-s3.py --out build/agent2/session3/apply-check-<HHMM>.txt
#
# Every git call is `git --no-optional-locks ... apply --check` (never writes). Two targets per patch:
#   live  = git -C <live repo> apply --check --verbose [--directory=...] <abs patch>   (the PENDING-DIFFS form)
#   snap1 = the same in build/agent2/snap1 (no usable .git: git runs in no-repo mode; GIT_CEILING_DIRECTORIES
#           stops discovery of any enclosing repo). Each result counts "Checking patch" and "Skipped patch" lines,
#           so the RESUME section 7 step 3 trap (Skipped patch + exit 0) shows up as SKIPPED, not as yes.
import argparse, hashlib, os, subprocess, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
S3 = os.path.join(R, 'build', 'agent2', 'session3')
LIVE_G = os.path.join(R, 'DimensionsRecomp')
LIVE_S = os.path.join(LIVE_G, 'rexglue-sdk')
SNAP_G = os.path.join(R, 'build', 'agent2', 'snap1', 'DimensionsRecomp')
SNAP_S = os.path.join(SNAP_G, 'rexglue-sdk')

# (label, path, expected sha256 from PENDING-DIFFS 11-23)
HASHES = [
    ('CG26 A diff', 'build/agent9/s4/spin/db16cyc-pause/toml-db16cyc-pause-A.diff', '95D901B9784705FA656145487B5611BA95A606E4DBD28FA7BE60C9E93B8F2620'),
    ('CG26 A after', 'build/agent9/s4/spin/db16cyc-pause/toml/new-A/rexlego/legodimensions_config.toml', '11707872E82D8B524D59B2E62DEABBABB90F10E2707CB2825338A920BD4D5FCF'),
    ('CG26 A base', 'build/agent9/s4/spin/db16cyc-pause/toml/base-A/rexlego/legodimensions_config.toml', '7F775847DB9CC2DA89DC3EDE57A0AD5F30FDF58D98F5021A0E27A4E0E4DA95BF'),
    ('CG26 build toml', 'build/agent2/cg26/DimensionsRecomp/rexlego/legodimensions_config.toml', '11707872E82D8B524D59B2E62DEABBABB90F10E2707CB2825338A920BD4D5FCF'),
    ('CG26 tool', 'build/agent2/cg26/tool/rexglue.exe', '9145166CDBEF5500E6E2607ED80AA6FC94CA1772DE2D3E87FF9E13BEAD87D586'),
    ('live toml (HEAD)', 'DimensionsRecomp/rexlego/legodimensions_config.toml', '7F775847DB9CC2DA89DC3EDE57A0AD5F30FDF58D98F5021A0E27A4E0E4DA95BF'),
    ('snap1 toml', 'build/agent2/snap1/DimensionsRecomp/rexlego/legodimensions_config.toml', '7F775847DB9CC2DA89DC3EDE57A0AD5F30FDF58D98F5021A0E27A4E0E4DA95BF'),
    ('CG26 B diff', 'build/agent9/s4/spin/db16cyc-pause/toml-db16cyc-pause-B.diff', '5D5892D33D09AF9D6889AF5BC991C82CD4443A8F7493053584BF6889261585B3'),
    ('CG26 tool option diff', 'build/agent9/s4/spin/db16cyc-pause/db16cyc-pause.diff', 'AC554DBBD965BF941BADE6391D0E0F483BE075B8A72434EEE8CB9D189ED61452'),
    ('codegen B toml', 'build/agent9/configs/batch-nolr.toml', 'E60EAF1CEB575572BA0274AA5F52E97F25A35C01690B41E6A637739408E6A090'),
    ('#21 diff', 'build/agent7/s4-t1/s4-t1.diff', '46FFD2E9044094DCE17C364C382F7BF2563E071E0DF81750C1DE1BC38BE38050'),
    ('#19 diff', 'build/agent7/s4-r1s2/s4-r1s2.diff', '06B0D371686CD384193DF30E8509BC4DA586E8EDD0F45F4122D5911483E33AD7'),
    ('#19 SHA256SUMS', 'build/agent7/s4-r1s2/SHA256SUMS.txt', '8A38FD9D3CD8B3752A5319B09BA3B9F61203ADEA35A5B99F8F6427F725CA9C5B'),
    ('#19 RATE-REQUEST', 'build/agent7/s4-r1s2/RATE-REQUEST.md', '1C2B8688A43ED4DC308E26D52271C3FFD8BEBC50863991624737D20CFC8E40CA'),
    ('#33 patch', 'build/agent6/s33-popin/s33-popin.patch', '0D23024484CCDEE1B15AF3EB79DC28759F9D422E78536F4766C83C2071CC2EFD'),
    ('#33 DESIGN', 'build/agent6/s33-popin/DESIGN.md', 'B2E33FE8B99F4041DD880D8A41F735F93FF220B0767DE78937AE131B57BAB318'),
    ('#33 CHECK', 'build/agent6/s33-popin/CHECK.txt', '5101A7B136CCCBE48DF420F1435C6743CAEF6B74F7DB86593A219F21FE624696'),
    ('#21 rating', 'build/agent10/t27/r21-s4t1.md', 'C2DB5124DA84A7EAA3C318106CA4D549A049D4427B8D5959234E55F72717DA50'),
    ('#33 rating', 'build/agent10/t27/r33-popin.md', 'ACF0BDB5A526236232A41D2A87FF2AACC17C00BE9ED35D3A227CCA238A0862B0'),
    ('CTR list-ctl', 'build/agent2/ctr/list-ctl.tsv', '6A357FEFBB0CE06A4BE09229FB9B32F6F0ED6576BF73ABD5753C441EFC8AD494'),
    ('CTR list-on', 'build/agent2/ctr/list-on.tsv', 'A63A77CD86AB7DA09C75468EE1DBF6857DE3E5D4F12B97AED2E9412CE6256305'),
    ('plume patch', 'build/agent2/pending/plume-local-on-e0c8871.patch', 'BF38B18300164ECF3817D16082377BBB5BA456D725A86008DE08AF216ADDCBF8'),
    ('simde patch', 'build/agent2/pending/simde-local-on-71fd833d.patch', '2A6DE738794F5DA059934444CC327082DDEEB24D8C78F56DB487A9DF9EBF27DC'),
    ('simde tracked patch', 'DimensionsRecomp/rexglue-sdk/patches/simde-native-m64-stream.patch', '2A6DE738794F5DA059934444CC327082DDEEB24D8C78F56DB487A9DF9EBF27DC'),
]
# before-files (= HEAD) of #21 and #19, live and snap1
BEFORE = [
    ('#21', 'rexlego/src/gpu_native/native_worker.cpp', '7157E8F2EDC3D5C438E3F2F21B50051693A3046B36A4BD8EE096901DF8FE0E2F'),
    ('#21', 'rexlego/src/gpu_native/native_recording.cpp', '48F0C429DDB89E452794365788C8B34EA9510A4B10B86F93771F418F3E53AA9B'),
    ('#21', 'rexlego/src/gpu_native/native_preparation.h', '889F3FA6F207011B03D044E745C2952C68200A44C99BE6E13EB810357D3D41A5'),
    ('#19', 'rexglue-sdk/include/rex/graphics/d3d12/command_processor.h', '67F4E8380C879377F06B6E3DD879EE737A82BBBE9682F123247ED5D0671FF325'),
    ('#19', 'rexglue-sdk/include/rex/graphics/d3d12/deferred_command_list.h', '9F6CC70A6922232D4FF7A32303E8B785A01D1C7A3CF54373369EF6B23F8AF0F0'),
    ('#19', 'rexglue-sdk/src/graphics/d3d12/command_processor.cpp', '027204B53A271D69275FCC6FEC6B2222905155E1FD67808F88A79329F4022C0E'),
    ('#19', 'rexglue-sdk/src/graphics/d3d12/shared_memory.cpp', '2A5ADF13B5E433F1F10B5C6AF9C14F8812527C4E155A5146B166723457B6EBB4'),
    ('#19', 'rexglue-sdk/src/graphics/d3d12/texture_cache.cpp', '949CCF4F4D80975D4DF3E833604BDBEC8C1442D787E2492085F0FA966E7F8C99'),
]
NO5 = os.path.join(S3, 's33-popin-no5.patch')
# (label, patch, live repo, snap1 root, extra args, expect forward-applies)
APPLY = [
    ('CG26 arm A', 'build/agent9/s4/spin/db16cyc-pause/toml-db16cyc-pause-A.diff', LIVE_G, SNAP_G, [], True),
    ('CG26 arm B (B line only)', 'build/agent9/s4/spin/db16cyc-pause/toml-db16cyc-pause-B.diff', LIVE_G, SNAP_G, [], False),
    ('CG26 tool option (in HEAD)', 'build/agent9/s4/spin/db16cyc-pause/db16cyc-pause.diff', LIVE_S, SNAP_S, [], False),
    ('#21 S4-T1 rev 2', 'build/agent7/s4-t1/s4-t1.diff', LIVE_G, SNAP_G, ['--directory=rexlego'], True),
    ('#19 R1 stage 2', 'build/agent7/s4-r1s2/s4-r1s2.diff', LIVE_S, SNAP_S, [], True),
    ('#33+#34 rated', 'build/agent6/s33-popin/s33-popin.patch', LIVE_S, SNAP_S, [], True),
    ('#33+#34 no hunk #5 (S1)', NO5, LIVE_S, SNAP_S, [], True),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def git(args, cwd_repo, env=None):
    p = subprocess.run(['git', '--no-optional-locks', '-C', cwd_repo] + args, capture_output=True, text=True,
                       env=env)
    return p.returncode, (p.stdout + p.stderr)


def make_no5(out):
    src = os.path.join(R, 'build', 'agent6', 's33-popin', 's33-popin.patch')
    data = open(src, 'rb').read()
    if sha(src) != '0D23024484CCDEE1B15AF3EB79DC28759F9D422E78536F4766C83C2071CC2EFD':
        out.append('FAIL: rated #33 patch hash changed; no5 copy not made')
        return False
    lines = data.split(b'\n')  # LF patch; index i = line i+1
    a, b = 81, 93  # delete L82..L93 (CHECK.txt L96 / DESIGN.md S10)
    ok = lines[a].startswith(b'@@ -4368,7 +4388,10 @@') and lines[b].startswith(b'diff --git a/src/graphics/d3d12/pipeline_cache.cpp')
    if not ok:
        out.append('FAIL: hunk #5 boundaries not where CHECK.txt says (L82 %r, L94 %r)' % (lines[a][:40], lines[b][:60]))
        return False
    new = b'\n'.join(lines[:a] + lines[b:])
    with open(NO5, 'wb') as f:
        f.write(new)
    out.append('made %s: %d B, %d lines, sha256 %s (rated patch minus L82-93; no N1 comment, unlike the withdrawn 2442037B copy)'
               % (os.path.relpath(NO5, R), len(new), new.count(b'\n'), sha(NO5)))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    out = ['apply-check-s3 %s (read-only; M2 session 3)' % time.strftime('%Y-%m-%d %H:%M:%S'), '']
    fails = 0
    for repo in (LIVE_G, LIVE_S):
        rc, o = git(['rev-parse', 'HEAD'], repo)
        out.append('HEAD %s = %s' % (os.path.relpath(repo, R), o.strip()))
    rc, o = git(['rev-parse', 'HEAD:rexglue-sdk'], LIVE_G)
    out.append('game gitlink rexglue-sdk = %s' % o.strip())
    rc, o = git(['diff', '--stat', 'b0bd3b4', 'HEAD', '--', '.', ':!perf'], LIVE_G)
    out.append('game b0bd3b4..HEAD outside perf/: ' + (o.strip().replace('\n', ' | ') or '(none)'))
    out += ['', '## Hashes']
    for lab, p, exp in HASHES:
        fp = os.path.join(R, p)
        got = sha(fp) if os.path.exists(fp) else 'MISSING'
        st = 'OK' if got == exp else 'CHANGED'
        fails += st != 'OK'
        out.append('%-8s %-22s %s %s' % (st, lab, got[:16], p))
    out += ['', '## Before-files (= HEAD) in live and snap1']
    for lab, rel, exp in BEFORE:
        for root, nm in ((LIVE_G, 'live'), (SNAP_G, 'snap1')):
            fp = os.path.join(root, rel)
            got = sha(fp) if os.path.exists(fp) else 'MISSING'
            st = 'OK' if got == exp else 'CHANGED'
            fails += st != 'OK'
            out.append('%-8s %-4s %-5s %s %s' % (st, lab, nm, got[:16], rel))
    out += ['', '## #33 S1 copy']
    if not make_no5(out):
        fails += 1
    out += ['', '## Apply checks (fwd = apply --check; rev = apply --check -R)']
    env = dict(os.environ)
    env['GIT_CEILING_DIRECTORIES'] = os.path.join(R, 'build', 'agent2', 'snap1')
    for lab, p, live, snap, extra, expect in APPLY:
        fp = p if os.path.isabs(p) else os.path.join(R, p)
        if not os.path.exists(fp):
            out.append('MISSING %s' % lab)
            fails += 1
            continue
        for nm, root, e in (('live', live, None), ('snap1', snap, env)):
            res = []
            for rv in ([], ['-R']):
                rc, o = git(['apply', '--check', '--verbose'] + rv + extra + [fp], root, e)
                nchk = o.count('Checking patch')
                nskip = o.count('Skipped patch')
                res.append((rc, nchk, nskip, o))
            (rf, cf, sf, of), (rr, cr, sr, orr) = res
            if sf or sr or cf == 0:
                verdict = 'SKIPPED/INVALID'
            elif rf == 0 and rr != 0:
                verdict = 'applies, not in tree'
            elif rf != 0 and rr == 0:
                verdict = 'already in tree'
            else:
                verdict = 'does not apply'
            good = (verdict == 'applies, not in tree') == expect
            fails += not good
            out.append('%-5s %-5s %-28s fwd exit %d (%d checking, %d skipped) / -R exit %d -> %s' %
                       ('OK' if good else 'FAIL', nm, lab, rf, cf, sf, rr, verdict))
            if not good or 'offset' in of or 'fuzz' in of:
                out += ['      | ' + ln for ln in of.strip().splitlines()[:12]]
    out += ['', 'RESULT: %s (%d unexpected)' % ('PASS' if not fails else 'FAIL', fails)]
    with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print('\n'.join(out))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
