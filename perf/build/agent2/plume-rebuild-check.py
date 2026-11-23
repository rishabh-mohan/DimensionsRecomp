#!/usr/bin/env python3
# plume-rebuild-check.py (Agent 2, board task #28): is the live plume checkout exactly its PIN plus the 7 tracked
# patches that DimensionsRecomp/tools/gpu-aot/prepare_plume.py applies (in its order), and nothing else?
#
#   python build/agent2/plume-rebuild-check.py --out build/agent2/pending/plume-rebuild-check.txt
#
# Read-only for every repo: git only with --no-optional-locks (rev-parse, diff --name-only, show). The PIN blobs and
# LF copies of the patches go to build/agent2/scratch/plume-rebuild (recreated each run), and GNU patch (Git for
# Windows' usr/bin/patch.exe, --fuzz=0) applies the patches there. Line endings are normalized to LF on both sides
# before comparing (core.autocrlf). Exit 0 = every patch applied cleanly and every rebuilt file equals the live one.
import argparse, hashlib, os, shutil, subprocess, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
PL = os.path.join(R, 'DimensionsRecomp', 'thirdparty', 'plume')
PD = os.path.join(R, 'DimensionsRecomp', 'tools', 'gpu-aot', 'patches')
PIN = 'e0c8871b930dc1a6544bf457f2348c456b9d7e13'
ORDER = ['plume-lego.patch', 'plume-state-cache.patch', 'plume-vulkan-readback.patch', 'plume-buffer-address.patch',
         'plume-adapter-query.patch', 'plume-graphics-read.patch', 'plume-winsdk-compat.patch']
SCRATCH = os.path.join(R, 'build', 'agent2', 'scratch', 'plume-rebuild')
HOLD = os.path.join(R, 'perf-notes', 'WINDOW-HOLD.txt')


def git(*a):
    p = subprocess.run(['git', '--no-optional-locks', '-C', PL] + list(a), capture_output=True)
    return p.returncode, p.stdout


def lf(b):
    return b.replace(b'\r\n', b'\n')


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    if os.path.exists(HOLD):
        print('HOLD exists - not starting')
        return 9
    t0 = time.time()
    out = ['# plume rebuild check (Agent 2, task #28), %s' % time.strftime('%Y-%m-%d %H:%M:%S'), '',
           '- Question: live `DimensionsRecomp/thirdparty/plume` == PIN %s + the 7 tracked patches of '
           '`DimensionsRecomp/tools/gpu-aot/patches` in prepare_plume.py order, exactly?' % PIN[:12],
           '- Method: PIN blobs via `git show` (read-only), GNU patch --fuzz=0 in `build/agent2/scratch/plume-rebuild`, '
           'compare with the live files after CRLF -> LF.', '']
    ok = True
    rc, head = git('rev-parse', 'HEAD')
    head = head.decode().strip()
    out.append('- plume HEAD: %s (%s)' % (head, 'PIN' if head == PIN else 'NOT the PIN'))
    ok &= head == PIN
    rc, names = git('diff', '--name-only', 'HEAD')
    live_mod = sorted(x for x in names.decode().splitlines() if x.strip())
    targets = set()
    for name in ORDER:
        with open(os.path.join(PD, name), 'rb') as f:
            for line in lf(f.read()).split(b'\n'):
                if line.startswith(b'+++ b/'):
                    targets.add(line[6:].decode())
    targets = sorted(targets)
    out.append('- files modified in the live checkout (diff --name-only HEAD): %s' % ', '.join(live_mod))
    out.append('- files the 7 patches touch: %s' % ', '.join(targets))
    if live_mod != targets:
        out.append('- MISMATCH: the two file sets differ')
        ok = False
    git_exe = shutil.which('git')
    patch_exe = os.path.join(os.path.dirname(os.path.dirname(git_exe)), 'usr', 'bin', 'patch.exe')
    if not os.path.isfile(patch_exe):
        out.append('- FAIL: GNU patch not found at Git\\usr\\bin\\patch.exe')
        ok = False
    else:
        if os.path.isdir(SCRATCH):
            shutil.rmtree(SCRATCH)
        tree = os.path.join(SCRATCH, 'tree')
        pdir = os.path.join(SCRATCH, 'patches')
        os.makedirs(tree)
        os.makedirs(pdir)
        for t in targets:
            rc, blob = git('show', '%s:%s' % (PIN, t))
            if rc:
                out.append('- FAIL: git show %s:%s exit %d' % (PIN[:12], t, rc))
                ok = False
                continue
            dst = os.path.join(tree, t)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, 'wb') as f:
                f.write(lf(blob))
        out += ['', '| # | patch | sha256 (16) | GNU patch exit | output |', '|---|---|---|---|---|']
        for i, name in enumerate(ORDER, 1):
            with open(os.path.join(PD, name), 'rb') as f:
                raw = f.read()
            cp = os.path.join(pdir, name)
            with open(cp, 'wb') as f:
                f.write(lf(raw))
            p = subprocess.run([patch_exe, '-p1', '--binary', '--fuzz=0', '--no-backup-if-mismatch', '-d', tree,
                                '-i', cp], capture_output=True)
            msg = ' / '.join(x.strip() for x in (p.stdout + p.stderr).decode(errors='replace').splitlines() if x.strip())
            out.append('| %d | `%s` | %s | %d | %s |' % (i, name, sha(raw)[:16], p.returncode, msg.replace('|', '/')))
            if p.returncode != 0 or 'offset' in msg.lower() or 'fuzz' in msg.lower():
                ok = ok and p.returncode == 0  # an offset is fine (line drift), a failure is not
        out += ['', '| file | live sha256 (16, as on disk) | live EOL | rebuilt == live (LF-normalized) |',
                '|---|---|---|---|']
        for t in targets:
            with open(os.path.join(PL, t), 'rb') as f:
                live = f.read()
            rp = os.path.join(tree, t)
            reb = open(rp, 'rb').read() if os.path.isfile(rp) else b''
            same = lf(live) == reb
            ok &= same
            eol = 'CRLF' if b'\r\n' in live else 'LF'
            out.append('| `%s` | %s | %s | %s |' % (t, sha(live)[:16], eol, 'yes' if same else 'NO'))
    out += ['', 'RESULT: %s  (%.1f s)' % ('PASS: the live plume checkout is exactly PIN + the 7 tracked patches'
                                         if ok else 'FAIL', time.time() - t0)]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print('\n'.join(out))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
