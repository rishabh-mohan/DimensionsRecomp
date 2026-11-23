#!/usr/bin/env python3
# stage-cg26.py (Agent 2, board run 2 task #1): stage devoff4b-cg26-bin = devoff4b-bin with legodimensions.exe and
# legodimensions.map from cg26/link-on (via stage-variant.py), with MANIFEST notes that name the codegen tool, the
# config toml and the 10 ON TU sha256s (Agent 9's #18 kit reports whether the MANIFEST names them).
# Run after cg26-check.py --stage, both recompiles and both relinks, at Below Normal (python children inherit it):
#   cmd /c "start /belownormal /b /wait python build\agent2\cg26\stage-cg26.py [--dry-run] [--notes-only]
#           [--note LINE ...] [--exe FILE --map FILE] [--out DIR]"
# Refuses while perf-notes/WINDOW-HOLD.txt exists (exit 9). Each staged ON TU copy (cg26/tu) must equal the regen's TU
# (exit 2 otherwise). --notes-only prints the notes and stages nothing (cg26/tu may be missing then).
import argparse, hashlib, os, subprocess, sys

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
CG = os.path.join(R, 'build', 'agent2', 'cg26')
GEN = os.path.join(CG, 'DimensionsRecomp', 'rexlego', 'generated', 'default')
TOOL = os.path.join(CG, 'tool', 'rexglue.exe')
TOML = os.path.join(CG, 'DimensionsRecomp', 'rexlego', 'legodimensions_config.toml')
HOLD = os.path.join(R, 'perf-notes', 'WINDOW-HOLD.txt')
TUS = (107, 116, 125, 153, 169, 205, 284, 304, 321, 432)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--notes-only', action='store_true')
    ap.add_argument('--note', action='append', default=[])
    ap.add_argument('--exe', default=os.path.join(CG, 'link-on', 'legodimensions.exe'))
    ap.add_argument('--map', default=os.path.join(CG, 'link-on', 'legodimensions.map'))
    ap.add_argument('--out', default=os.path.join(R, 'build', 'agent2', 'devoff4b-cg26-bin'))
    a = ap.parse_args()
    if os.path.exists(HOLD):
        print('HOLD file exists: not starting')
        return 9
    notes = ['CG26 = devoff4b + #26 db16cyc_pause ON (arm A): cg26 regen with the new-A toml and the new codegen tool '
             '(20 pauses in 10 TUs), the 10 ON TUs recompiled with the snap1-off flags (recompile.py), and '
             'legodimensions.exe/.map relinked from the snap1-off objects (relink.py --replace-file cg26/replace-on.txt).',
             'cg26 codegen tool rexglue.exe sha256 %s' % sha(TOOL),
             'cg26 config toml legodimensions_config.toml sha256 %s' % sha(TOML)]
    bad = 0
    for n in TUS:
        b = 'legodimensions_recomp.%d.cpp' % n
        hg = sha(os.path.join(GEN, b))
        st = os.path.join(CG, 'tu', b)
        if os.path.isfile(st):
            if sha(st) != hg:
                print("FAIL: cg26/tu/%s differs from the regen's TU" % b)
                bad += 1
        elif not a.notes_only:
            print('FAIL: cg26/tu/%s is missing (run cg26-check.py --stage first)' % b)
            bad += 1
        notes.append('cg26 ON TU %s sha256 %s' % (b, hg))
    notes += a.note
    if bad:
        return 2
    if a.notes_only:
        print('\n'.join(notes))
        return 0
    cmd = [sys.executable, os.path.join(R, 'build', 'agent2', 'stage-variant.py'),
           '--base', os.path.join(R, 'build', 'agent2', 'devoff4b-bin'), '--out', a.out,
           '--replace', 'legodimensions.exe=' + a.exe, '--replace', 'legodimensions.map=' + a.map,
           '--title', 'CG26: devoff4b with #26 db16cyc_pause ON (arm A, 20 pauses); exe and map relinked with the 10 '
                      'ON TUs']
    for x in notes:
        cmd += ['--note', x]
    if a.dry_run:
        cmd.append('--dry-run')
    print('stage-cg26: stage-variant.py with %d notes%s' % (len(notes), ' (dry run)' if a.dry_run else ''))
    sys.stdout.flush()
    return subprocess.call(cmd, cwd=R)


if __name__ == '__main__':
    sys.exit(main())
