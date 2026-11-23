"""Agent 2 - RESUME block update after the S3e prep (04:5x): standby status, an S3e section, Agent 9's nativeB static
check, the scripts and keep lists. Backs up the notes first; every replacement has an expected count (any mismatch and
nothing is written). Keeps LF.
  python build\\agent2\\notes-s3e-prep.py
"""
import hashlib
import os
import shutil
import sys
import time

R = r'<workspace>'
F = os.path.join(R, 'perf-notes', 'agent2-baseline.md')
BK = os.path.join(R, 'build', 'agent2', 'notes-backup')
now = time.strftime('%H:%M')
free = shutil.disk_usage('C:\\').free / 1e9

with open(F, 'rb') as f:
    raw = f.read()
if b'\r\n' in raw:
    sys.exit('REFUSED: the notes file has CRLF line ends')
t = raw.decode('utf-8')
errs = []


def rep(old, new, n=1, what=''):
    global t
    c = t.count(old)
    if c != n:
        errs.append('%s: expected %d match(es), found %d' % (what or old[:60], n, c))
        return
    t = t.replace(old, new)


rep('# Agent 2: build pipeline - RESUME NOTE (session 3, task #14 from Agent 1; updated 04:37)',
    '# Agent 2: build pipeline - RESUME NOTE (session 3, task #14 done, standby; updated %s)' % now, what='header')

rep('Agent 2 builds (<= -j10). Nothing of mine is running.**',
    'Agent 2 builds (<= -j10). Nothing of mine is running.\n'
    'Standby (Agent 1, 04:39): at most one more native build before 08:30, S3e -> `native3e-bin` (Agent 4\'s `|| !vs`\n'
    'draw.cpp variant), only if Agent 8\'s native3d rows (~05:03) still show hash=0 lines and only at Agent 1\'s explicit GO\n'
    'with the new draw.cpp sha256. It is prepared, not built (S3e section below; Agent 9 reviews the diffs). By ~06:30: a\n'
    '"Build inventory" table in this file, for the user report and the next restart prompt (delete nothing).**',
    what='status')

S3E = r'''**S3e (PREPARED 04:46, NOT BUILT; only at Agent 1's explicit GO with Agent 4's new draw.cpp sha256, before 08:30)**
- native3e-bin = S3d + exactly Agent 4's next live write of `rexlego/src/gpu_native/draw.cpp` (the `|| !vs` variant),
  native only, compared with native3d-bin. Only if Agent 8's native3d profile rows (~05:03) still show hash=0 lines.
  Tell Agent 8 before it starts and when it ends.
- Tools: `make-s3e-clones.py` (run 04:46; refuses to rerun without --force) generated `prep-s3e.py` 23536F1FB33DACC8
  and `run-s3e.ps1` FD188929D9831E64 from prep-s3d.py BD4D94DA / run-s3d.ps1 FE159F8A (both unchanged): token swaps
  (S3d -> S3e, the base S3 -> S3d, native3d -> native3e, native3-bin -> native3d-bin, s3d -> s3e) plus exact
  replacements, each with an expected count. It also patched stop-snap.ps1 C6B75748 -> 705233E59C9ED056 (adds
  run-s3e.ps1; backup `stop-snap.ps1.pre-S3e`). Diffs in `S3e-diffs/`: prep-s3e.py.vs-s3d 8A3BFEE3 (+36/-32),
  run-s3e.ps1.vs-s3d 794839B6 (+25/-25), stop-snap.ps1.S3e 88A5B710 (+2/-1).
- run-s3e's driver guard also lists run-s3d, rb-chain, run-rbN, prep-rbN, run-nb and prep-nb. stage-snap-bin.ps1 is
  unchanged: for S3e it lists the PATCHES rows of S1, S2, S3 and S3e; S3d's one row (draw.cpp) is superseded by S3e's
  (the last row per file wins), as the 4th line of S3e-notes.txt says.
- Tests (04:47): prep-s3e.py parses; run-s3e.ps1 and stop-snap.ps1 have 0 parse errors; all three ASCII, LF.
  `prep-s3e.py 5ea1f3576dcc2f90 --go 04:55 --dry-run`: 8/9 PASS, the only FAIL "live draw.cpp != snap1 draw.cpp"
  (no new write yet), exit 1, nothing written (SDK DLLs == native3d-bin: PASS). `run-s3e.ps1 -Jobs 10` without
  S3e-notes.txt: exit 4 before any build (log moved to `rbt-logs/test-snap3e-run.txt`). stop-snap.ps1 was not run.
- At the GO, in order:
  1. `python build\agent2\prep-s3e.py <sha> --go HH:MM --owner A4`: must be 9/9 PASS; writes S3e-rules.txt and
     S3e-notes.txt.
  2. `python build\agent2\snap-patch.py plan S3e build\agent2\S3e-rules.txt --note-file=build\agent2\S3e-notes.txt`
     (COPY 1, errors 0), then `apply S3e` with the same arguments (backup `snap1-backup-S3e/`), then
     `snap-patch.py verify S3e` PASS. snap1 is then S3e.
  3. `powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-s3e.ps1 -Jobs 10` as a run_command
     background task: snap1-on, tag snap3e, then stage-snap-bin -> `native3e-bin` with -CompareBin native3d-bin. ETA
     about 6-8 min from the GO (S3d: build 102.7 s + stage 74.5 s). Log `snap3e-run.txt` (+ snap3e-steps.txt,
     snap3e-stage-native.log).
  4. Check: 0 FAIL; exe differs from native3d-bin and the other 6 files are identical; MANIFEST patch rows S1+p1/p2,
     S2 18, S3 28, S3e 1; log the fingerprint. Post exe, rexruntime, MANIFEST and fingerprint to Agents 1, 4 and 8
     (and 9, 10); tell Agent 8 that the build has ended; update this block and the inventory.

'''
rep("**Task #14 (session 3 part 2; files: build/agent2/** and this file)**",
    S3E + "**Task #14 (session 3 part 2; files: build/agent2/** and this file)**", what='S3e section')

rep('    estimate was ~3.5). Free C 247.5 GB at 04:35.\n',
    '    estimate was ~3.5). Free C 247.5 GB at 04:35.\n'
    '  - Agent 9, static check of nativeB vs native3d-bin (04:47): all PASS. mapcmp: the same 164,786 sub_ functions,\n'
    '    __imp__ aliases and 109 hooked; .text -10.38%, exactly the devoff2 -> devoffB delta\n'
    '    (`build/agent9/logs/mapcmp-native.txt`). The fingerprint differs by design (`build/agent9/fpcheck.py`: the same\n'
    '    271 inputs, the 13 that differ are all codegen). Warnings: none in generated code, the rest pre-existing.\n'
    '    MANIFEST pins (SHA256SUMS 24ce1493), gate PASS (525 DB entries, 432 TUs), host regs 378 (0 new / 0 gone).\n',
    what='Agent 9 nativeB check')

rep("  `rb-chain.ps1`, `rb-tools-test.ps1`, `rb-chain-guardonly-diff.py`, `notes-resume-t14.py`.\n",
    "  `rb-chain.ps1`, `rb-tools-test.ps1`, `rb-chain-guardonly-diff.py`, `notes-resume-t14.py`; standby: `make-s3e-clones.py`\n"
    "  (-> `prep-s3e.py`, `run-s3e.ps1`), `notes-s3e-prep.py`.\n", what='scripts')

rep("`*.pre-RB`, `*.pre-GuardOnly`, `snap1-backup-S3d`;\n",
    "`*.pre-RB`, `*.pre-GuardOnly`, `*.pre-S3e`, `snap1-backup-S3d`;\n", what='keep list')
rep('snapB3, snapB3-on and nativeB-bin) until Agent 1 says otherwise. Free C: 247.5 GB at 04:35.',
    'snapB3, snapB3-on and nativeB-bin) until Agent 1 says otherwise. Free C: %.1f GB at %s.' % (free, now),
    what='free C')

if errs:
    print('REFUSED (nothing written):')
    for e in errs:
        print('  ' + e)
    sys.exit(1)
os.makedirs(BK, exist_ok=True)
bk = os.path.join(BK, 'agent2-baseline.md.' + time.strftime('%H%M%S'))
shutil.copy2(F, bk)
b = t.encode('utf-8')
with open(F, 'wb') as f:
    f.write(b)
print('backup %s (sha256 %s)' % (bk, hashlib.sha256(raw).hexdigest()[:16].upper()))
print('wrote %s: %d B, %d lines, sha256 %s, CRLF %d' % (F, len(b), t.count('\n'), hashlib.sha256(b).hexdigest()[:16].upper(),
                                                        b.count(b'\r\n')))
