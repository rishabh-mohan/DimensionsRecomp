"""Agent 2 - S3d inputs, at Agent 1's explicit GO (after Agent 4's live draw.cpp write). S3d = snap1 at S3 + exactly
Agent 4's live rexlego/src/gpu_native/draw.cpp -> native3d-bin (native only, run-s3d.ps1).
  python build\\agent2\\prep-s3d.py <sha256 of the written draw.cpp, 16-64 hex digits> --go HH:MM [--owner A4]
                                   [--dry-run] [--force]
Checks (each is printed PASS/FAIL; any FAIL and nothing is written):
  - S3 is snap1's current state: the newest STATE-*.tsv in snap1 (the base snap-patch.py plans against) is a
    STATE-S3-*.tsv, no PATCHES-S3d.tsv / STATE-S3d-*.tsv exists yet, and snap1's draw.cpp == the snap1 sha256 of its
    row there;
  - the live draw.cpp sha256 starts with the given hash, and live != snap1 (there is something to patch);
  - snap1-off/compile_commands.json compiles no gpu_native file (draw.cpp is not in OFF builds, so devoff3-bin stays
    the OFF build of S3d);
  - snap1-sdk/install/bin rexruntime.dll and rexgpu-xenos.dll == native3-bin's (the SDK is unchanged since S3).
Writes build/agent2/S3d-rules.txt (comments + one rule '<owner> | rexlego/src/gpu_native/draw.cpp | <full sha256>')
and build/agent2/S3d-notes.txt (3 lines, for snap-patch.py --note-file= and the native3d MANIFEST); refuses to
overwrite them without --force. --dry-run runs the checks and prints both files without writing them.
Next: snap-patch.py plan S3d / apply S3d build\\agent2\\S3d-rules.txt --note-file=build\\agent2\\S3d-notes.txt, then
snap-patch.py verify S3d, then run-s3d.ps1.
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
RULES = os.path.join(A, 'S3d-rules.txt')
NOTES = os.path.join(A, 'S3d-notes.txt')
CC_OFF = os.path.join(A, 'snap1-off', 'compile_commands.json')
SDK_BIN = os.path.join(A, 'snap1-sdk', 'install', 'bin')
REF = os.path.join(A, 'native3-bin')


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

    # S3 must be snap1's current state
    states = sorted([p for p in glob.glob(os.path.join(SNAP_ROOT, 'STATE-*.tsv'))
                     if 'reverted' not in os.path.basename(p)], key=os.path.getmtime)
    newest = os.path.basename(states[-1]) if states else 'none'
    check(re.fullmatch(r'STATE-S3-\d{4}\.tsv', newest), 'the newest STATE record in snap1 is a STATE-S3-*.tsv (%s)'
          % newest)
    done = sorted(os.path.basename(p) for p in glob.glob(os.path.join(SNAP_ROOT, 'PATCHES-S3d.tsv'))
                  + glob.glob(os.path.join(SNAP_ROOT, 'STATE-S3d-*.tsv')))
    check(not done, 'no S3d record in snap1 yet%s' % (' (found %s: ask Agent 1 before a second S3d)'
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
    # the SDK is unchanged since S3
    for dll in ('rexruntime.dll', 'rexgpu-xenos.dll'):
        hi, hr = sha(os.path.join(SDK_BIN, dll)), sha(os.path.join(REF, dll))
        check(hi == hr, 'snap1-sdk/install/bin/%s %s == native3-bin (%s)' % (dll, hi[:16].upper(), hr[:16].upper()))
    for ok, text in res:
        print('%s %s' % ('PASS' if ok else 'FAIL', text))
    nfail = sum(1 for ok, _ in res if not ok)
    if nfail:
        refuse('%d of %d check(s) failed' % (nfail, len(res)))
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    rules = [
        "# snap-patch.py rules for S3d, written %s by build/agent2/prep-s3d.py (Agent 1's GO %s)" % (now, a.go),
        '# base: %s (S3). S3d = S3 + exactly this one file; the live file must still have the full sha256 below.'
        % newest,
        "# %s: Agent 4's live draw.cpp write; S3 %s; live %s, %d B, mtime %s" % (owner, s3[:16], live[:16], st.st_size, mt),
        '%s | %s | %s' % (owner, REL, live),
    ]
    notes = [
        "S3d build inputs: S3 (%s: game commit 001336f + SDK commit c5fe668 + the uncommitted pre-sprint plume and simde "
        "edits) + exactly Agent 4's live write of %s, %s -> %s (%d B, live mtime %s); Agent 1's GO %s."
        % (newest, REL, s3[:16].upper(), live[:16].upper(), st.st_size, mt, a.go),
        'S3d is native only: draw.cpp is not compiled into OFF builds (snap1-off compile_commands.json: %d entries, no '
        'gpu_native file), so devoff3-bin stays the OFF build of S3d; snap1-sdk is not rebuilt (its install/bin '
        'rexruntime.dll and rexgpu-xenos.dll == native3-bin).' % len(cc),
        'Generated code: the pinned S1 output (gen-check against baseline/), as in S1-S3; only build B uses '
        'install/batch-nolr.',
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
    print('next: python build\\agent2\\snap-patch.py plan S3d build\\agent2\\S3d-rules.txt '
          '--note-file=build\\agent2\\S3d-notes.txt')


if __name__ == '__main__':
    main()
