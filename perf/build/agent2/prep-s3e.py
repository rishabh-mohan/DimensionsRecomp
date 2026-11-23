"""Agent 2 - S3e inputs, at Agent 1's explicit GO (after Agent 4's next live draw.cpp write, the '|| !vs'
variant; cloned from prep-s3d.py by make-s3e-clones.py). S3e = snap1 at S3d + exactly
Agent 4's live rexlego/src/gpu_native/draw.cpp -> native3e-bin (native only, run-s3e.ps1).
  python build\\agent2\\prep-s3e.py <sha256 of the written draw.cpp, 16-64 hex digits> --go HH:MM [--owner A4]
                                   [--dry-run] [--force]
Checks (each is printed PASS/FAIL; any FAIL and nothing is written):
  - S3d is snap1's current state: the newest STATE-*.tsv in snap1 (the base snap-patch.py plans against) is a
    STATE-S3d-*.tsv, no PATCHES-S3e.tsv / STATE-S3e-*.tsv exists yet, and snap1's draw.cpp == the snap1 sha256 of its
    row there;
  - the live draw.cpp sha256 starts with the given hash, and live != snap1 (there is something to patch);
  - snap1-off/compile_commands.json compiles no gpu_native file (draw.cpp is not in OFF builds, so devoff3-bin stays
    the OFF build of S3e);
  - snap1-sdk/install/bin rexruntime.dll and rexgpu-xenos.dll == native3d-bin's (the SDK is unchanged since S3d).
Writes build/agent2/S3e-rules.txt (comments + one rule '<owner> | rexlego/src/gpu_native/draw.cpp | <full sha256>')
and build/agent2/S3e-notes.txt (4 lines, for snap-patch.py --note-file= and the native3e MANIFEST); refuses to
overwrite them without --force. --dry-run runs the checks and prints both files without writing them.
Next: snap-patch.py plan S3e / apply S3e build\\agent2\\S3e-rules.txt --note-file=build\\agent2\\S3e-notes.txt, then
snap-patch.py verify S3e, then run-s3e.ps1.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys
import time

R = r'<workspace>'
A = os.path.join(R, 'build', 'agent2')
SNAP_ROOT = os.path.join(A, 'snap1')
REL = 'rexlego/src/gpu_native/draw.cpp'
LIVE = os.path.join(R, 'DimensionsRecomp', *REL.split('/'))
SNAPF = os.path.join(SNAP_ROOT, 'DimensionsRecomp', *REL.split('/'))
RULES = os.path.join(A, 'S3e-rules.txt')
NOTES = os.path.join(A, 'S3e-notes.txt')
CC_OFF = os.path.join(A, 'snap1-off', 'compile_commands.json')
SDK_BIN = os.path.join(A, 'snap1-sdk', 'install', 'bin')
REF = os.path.join(A, 'native3d-bin')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def ts(t):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))


def refuse(msg):
    print('REFUSED: %s (nothing written)' % msg)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('sha')
    ap.add_argument('--go', required=True, help="Agent 1's GO time, HH:MM")
    ap.add_argument('--owner', default='A4')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    want = a.sha.strip().lower()
    if not re.fullmatch(r'[0-9a-f]{16,64}', want):
        refuse('the hash must be 16-64 hex digits, got %r' % a.sha)
    if not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', a.go):
        refuse('--go must be HH:MM, got %r' % a.go)
    owner = a.owner.strip()
    if not owner or '|' in owner or '\t' in owner or '#' in owner:
        refuse('bad --owner %r' % a.owner)
    res = []

    def check(ok, text):
        res.append((bool(ok), text))
        return bool(ok)

    # S3d must be snap1's current state
    states = sorted([p for p in glob.glob(os.path.join(SNAP_ROOT, 'STATE-*.tsv'))
                     if 'reverted' not in os.path.basename(p)], key=os.path.getmtime)
    newest = os.path.basename(states[-1]) if states else 'none'
    check(re.fullmatch(r'STATE-S3d-\d{4}\.tsv', newest), 'the newest STATE record in snap1 is a STATE-S3d-*.tsv (%s)'
          % newest)
    done = sorted(os.path.basename(p) for p in glob.glob(os.path.join(SNAP_ROOT, 'PATCHES-S3e.tsv'))
                  + glob.glob(os.path.join(SNAP_ROOT, 'STATE-S3e-*.tsv')))
    check(not done, 'no S3e record in snap1 yet%s' % (' (found %s: ask Agent 1 before a second S3e)'
                                                      % ', '.join(done) if done else ''))
    s3 = None
    if states:
        row = None
        with open(states[-1], encoding='utf-8-sig') as f:
            for ln in f:
                if ln.startswith('#') or not ln.strip():
                    continue
                c = ln.rstrip('\r\n').split('\t')
                if c[0] == REL:
                    row = c
                    break
        if check(row is not None and len(row) >= 7, '%s has a %s row' % (newest, REL)):
            s3 = row[6].lower()
    snap = sha(SNAPF)
    check(s3 is not None and snap == s3, 'snap1 %s %s == the snap1 sha256 of that row (%s)'
          % (REL, snap[:16], (s3 or '?')[:16]))
    st = os.stat(LIVE)
    live = sha(LIVE)
    mt = ts(st.st_mtime)
    check(live.startswith(want), 'live %s %s (%d B, mtime %s) starts with the given %s'
          % (REL, live[:16], st.st_size, mt, want[:16]))
    check(live != snap, 'live draw.cpp != snap1 draw.cpp (something to patch)')
    # draw.cpp is not in OFF builds
    with open(CC_OFF, encoding='utf-8') as f:
        cc = json.load(f)
    gn = [e.get('file', '') for e in cc if 'gpu_native' in e.get('file', '').replace('\\', '/').lower()]
    check(not gn, 'snap1-off/compile_commands.json: %d entries, %d gpu_native file(s)%s'
          % (len(cc), len(gn), ' (first %s)' % gn[0] if gn else ''))
    # the SDK is unchanged since S3d
    for dll in ('rexruntime.dll', 'rexgpu-xenos.dll'):
        hi, hr = sha(os.path.join(SDK_BIN, dll)), sha(os.path.join(REF, dll))
        check(hi == hr, 'snap1-sdk/install/bin/%s %s == native3d-bin (%s)' % (dll, hi[:16].upper(), hr[:16].upper()))
    for ok, text in res:
        print('%s %s' % ('PASS' if ok else 'FAIL', text))
    nfail = sum(1 for ok, _ in res if not ok)
    if nfail:
        refuse('%d of %d check(s) failed' % (nfail, len(res)))
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    rules = [
        "# snap-patch.py rules for S3e, written %s by build/agent2/prep-s3e.py (Agent 1's GO %s)" % (now, a.go),
        '# base: %s (S3d). S3e = S3d + exactly this one file; the live file must still have the full sha256 below.'
        % newest,
        "# %s: Agent 4's live draw.cpp write; S3d %s; live %s, %d B, mtime %s" % (owner, s3[:16], live[:16], st.st_size, mt),
        '%s | %s | %s' % (owner, REL, live),
    ]
    notes = [
        "S3e build inputs: S3d (%s: S3 = game commit 001336f + SDK commit c5fe668 + the uncommitted pre-sprint plume and simde "
        "edits, plus Agent 4's S3d draw.cpp write in PATCHES-S3d.tsv) + exactly Agent 4's next live write of %s "
        "(the '|| !vs' variant), %s -> %s (%d B, live mtime %s); Agent 1's GO %s."
        % (newest, REL, s3[:16].upper(), live[:16].upper(), st.st_size, mt, a.go),
        'S3e is native only: draw.cpp is not compiled into OFF builds (snap1-off compile_commands.json: %d entries, no '
        'gpu_native file), so devoff3-bin stays the OFF build of S3e; snap1-sdk is not rebuilt (its install/bin '
        'rexruntime.dll and rexgpu-xenos.dll == native3d-bin).' % len(cc),
        'Generated code: the pinned S1 output (gen-check against baseline/), as in S1-S3d; only builds B and nativeB use '
        'install/batch-nolr.',
        "Patch rows: stage-snap-bin.ps1 lists those of S1, S2, S3 and S3e; S3d's one row (draw.cpp) is superseded "
        "by S3e's, whose before-hash is S3d's after-hash.",
    ]
    if a.dry_run:
        print('--dry-run: would write %s:' % RULES)
        print('\n'.join('  ' + x for x in rules))
        print('--dry-run: would write %s:' % NOTES)
        print('\n'.join('  ' + x for x in notes))
        return
    for p in (RULES, NOTES):
        if os.path.exists(p) and not a.force:
            refuse('%s exists (use --force to overwrite)' % p)
    for p, lines in ((RULES, rules), (NOTES, notes)):
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(lines) + '\n')
        print('wrote %s (%d lines, sha256 %s)' % (p, len(lines), sha(p)[:16].upper()))
    print('next: python build\\agent2\\snap-patch.py plan S3e build\\agent2\\S3e-rules.txt '
          '--note-file=build\\agent2\\S3e-notes.txt')


if __name__ == '__main__':
    main()
