"""Agent 2 (task #14, ~03:58): refresh the RESUME block of perf-notes/agent2-baseline.md (S3d done, task #14 state).
Backup first: build/agent2/notes-backup/agent2-baseline.md.<HHMMSS>. Every anchor must match exactly once.
  python build\\agent2\\notes-resume-t14.py "<rb-tools-test result text>" """
import os, shutil, sys, time
R = r'<workspace>'
P = os.path.join(R, 'perf-notes', 'agent2-baseline.md')
test_txt = sys.argv[1] if len(sys.argv) > 1 else 'see rbt-logs/'
raw = open(P, 'rb').read()
crlf = b'\r\n' in raw
t = raw.decode('utf-8').replace('\r\n', '\n')
now = time.strftime('%H:%M')

HEADER = """# Agent 2: build pipeline - RESUME NOTE (session 3, task #14 from Agent 1; updated @NOW@)

**Task #1 is DONE (`@@done 1` about 03:05). Task #14 (session 3 part 2): step 1, S3d -> `native3d-bin`, is DONE and
staged (03:46; hashes posted to Agents 1, 4, 8 and 10; Agent 1 re-hashed: match). Step 2, the B rollback, is NOT
needed (Agent 10's tie-break cleared B; rb1/rb2 stay prepared and unbuilt). Step 3, nativeB: Agent 1's conditional
GO; tools made and tested, disk estimate accepted (~3.5 GB), Agent 9 OK'd the diffs (03:51); WAITING for Agent 8's
"last -Profile run done"; never start it after 07:00. No builds or game runs from 08:30 (window 4 waits for the user,
asleep until about 10:00; questions go to Agent 1). Only Agent 2 builds (<= -j10). Nothing of mine is running.**

"""

ROW3D = ("| `native3d-bin` | 03:46:18 | 8, 363.7 MB | 103/0/34, 368F9CE650EC56CE... | B90DF683D0A57A21... | S3d native "
         "(S3 + Agent 4's draw.cpp 5EA1F357...), fingerprint `335ff2d47268f3a1`; map 1C9AB7E3E471A6BA... |\n")

S3D_T14 = """**S3d (DONE; Agent 1's GO 03:35, with Agent 4's draw.cpp sha256)**
- Live `rexlego/src/gpu_native/draw.cpp` 5EA1F3576DCC2F90C7CBE410CFCDE093CB39D170A2BDD6259C3A85B41BE14410 (306,557 B,
  mtime 03:34:59, Agent 4) was the only change against HEAD `001336f`.
- `prep-s3d.py 5EA1F357... --go 03:35 --owner A4` (03:42): 9/9 PASS; `S3d-rules.txt` 714CBC5E..., `S3d-notes.txt`
  C9B1707C.... `snap-patch.py plan S3d` -> COPY 1, errors 0 (`snap1/PLAN-S3d-0342.txt`); `apply` at 03:42:56:
  PATCHES-S3d.tsv 0250A3D000CB11C5..., STATE-S3d-0342.tsv AC7B88D344A2C446..., backup under `snap1-backup-S3d/`;
  `verify S3d` PASS (23843 files, 0 problems). snap1 is now S3d.
- `run-s3d.ps1`, 03:43:18-03:46:18 (build 102.7 s, stage 74.5 s): stage 0 FAIL, 103 PASS / 34 NOTE. Against
  native3-bin: exe differs (PASS), map NOTE; rexruntime, rexgpu-xenos, TracyClient, the wav, the ttf and
  amd_fidelityfx are identical. MANIFEST patch rows S1 2 (S1+p1, S1+p2) / S2 18 / S3 28 / S3d 1. Fingerprint
  335ff2d47268f3a1 (native3: 8f849b69907d4006; it hashes draw.cpp). Hashes: exe
  B90DF683D0A57A21F4DC24F8EA69F75FC954ADD4712B830A08C28F82FF521944, map 1C9AB7E3E471A6BA..., rexruntime
  D1D66AC3716835AC..., rexgpu-xenos EE0A661FB0C30FCB..., MANIFEST 368F9CE650EC56CE....
- devoff3-bin stays the OFF build of S3d: OFF builds don't compile draw.cpp.

**Task #14 (session 3 part 2; files: build/agent2/** and this file)**
- Step 2, B rollback: NOT needed (Agent 1, after Agent 10's tie-break cleared B); rb1/rb2 stay prepared and unbuilt.
  Only at Agent 1's GO: `rb-chain.ps1 -Variant rb1|rb2 -Jobs 10`. prep-rbN copies snap1 (now S3d) to snapB3 with
  `install/rb1-nolocal` or `install/rb2-nomusttail`; game tree snapB3-off; A = devoff3-bin; out devoffRB1-bin or
  devoffRB2-bin. snapB3 holds one variant at a time, so switching variants needs `-Resync`.
- Step 3, nativeB (Agent 1's GO with 4 conditions):
  1. native3d staged: YES.
  2. disk estimate <= 40 GB: YES. About 3.5 GB: the snapB3 copy ~2.1 (snapB 1.5 + rexlego/out 0.6), snapB3-on ~1.0,
     nativeB-bin ~0.36. Agent 1 OK at 03:50.
  3. Agent 9 OK of the diffs: YES (03:51). Agent 9's independent dry run is byte-identical. Non-blocking nits:
     run-nb's guard doesn't list prep-*.py (rb-chain covers that); an explicit -Compare isn't checked against the tag;
     the fingerprint against A is only logged.
  4. Agent 8 says the last -Profile run is done: WAITING.
  Never start it after 07:00.
  - Command (run_command background task): `powershell -NoProfile -ExecutionPolicy Bypass -File
    build\\agent2\\rb-chain.ps1 -Variant nb -Jobs 10`. It runs verify S3d, then prep-nb.py, then run-nb.ps1.
    - prep-nb.py: robocopy snap1 -> snapB3 including rexlego/out, the batch-nolr step 4, gen-check. Its notes must
      say S3d.
    - run-nb.ps1: native configure of the fresh snapB3-on, gen-check against batch-nolr, gate, build, rexruntime ==
      install/bin, then stage nativeB-bin with -CompareBin native3d-bin.
    ETA ~25 min. Logs: rb-chain-nb.txt, rb-chain-nb-verify.txt, rb-chain-nb-prep.log, rb-chain-nb-run.log,
    snapB3-prep.txt, snapB3n-run.txt, snapB3n-steps.txt, snapB3n-stage.log.
  - Then check 0 FAIL, exe differs and the other files == native3d-bin. Post the exe, rexruntime, MANIFEST and
    fingerprint to Agents 1, 8, 9 and 10, then `@@done 14`.
- Tools (03:24-03:53):
  - `make-rb-clones.py` (run 03:46; refuses to rerun without --force) wrote prep-rb1.py 94C6C91698D88447, run-rb1.ps1
    0665AA37C8EF434F, prep-rb2.py E0A003731BD95532, run-rb2.ps1 118C2D6E0A498A0F and prep-nb.py 0FAF4A924AEEE498, and
    patched stop-snap.ps1 B9AECC6A -> C6B757480AFEA48F (backup `stop-snap.ps1.pre-RB`). Diffs in `RB-diffs/`:
    prep-rb1 DA5EDDBC, run-rb1 FEECE89A, prep-rb2 A6FA98BB, run-rb2 C07F412B, prep-nb F5B9A4B7, stop-snap.RB
    87D09AB2, run-nb.ps1.vs-run-b 48168743.
  - `run-nb.ps1` 979F4309EE10E9EF, written by hand from run-b.ps1 and the native parts of run-s3d.ps1.
  - `rb-chain.ps1` 65A2CFE4BE73E146. Agent 9 reviewed 3660069E; the only change since is the `-GuardOnly` switch
    (diff `RB-diffs/rb-chain.ps1.GuardOnly.diff` 443CC9C0, pre-image `rb-chain.ps1.pre-GuardOnly`).
  - `rb-tools-test.ps1`: @TEST@ Console copies are in `rbt-logs/`.

"""

def once(hay, needle, what):
    n = hay.count(needle)
    if n != 1:
        sys.exit('STOP: anchor %s found %d times; nothing written' % (what, n))
    return hay.index(needle)

i = once(t, '**Staged bins**', 'staged bins')
t = HEADER.replace('@NOW@', now) + t[i:]
j = once(t, '| `native3-bin` |', 'native3 row')
k = t.index('\n', j) + 1
t = t[:k] + ROW3D + t[k:]
a = 'S3 D1D66AC3716835AC... / EE0A661FB0C30FCB... (the S3 SDK rebuild relinked xenos too).'
once(t, a, 'rexruntime bullet')
t = t.replace(a, 'S3 and S3d D1D66AC3716835AC... / EE0A661FB0C30FCB... (the S3 SDK rebuild relinked xenos too; S3d did not rebuild\n  the SDK).')
s = once(t, '**S3d (next;', 'S3d section')
e = once(t, '**Live tree edit', 'live tree edit')
assert s < e
t = t[:s] + S3D_T14.replace('@TEST@', test_txt) + t[e:]
a = '`s3-tools-test.py`, `s3d-tools-test.ps1`; `stop-snap.ps1`; `splice-notes-top.py`.'
once(t, a, 'scripts list')
t = t.replace(a, '`s3-tools-test.py`, `s3d-tools-test.ps1`; `stop-snap.ps1`; `splice-notes-top.py`; task #14:\n'
              '  `make-rb-clones.py` (-> `prep-rb1.py`, `prep-rb2.py`, `prep-nb.py`, `run-rb1.ps1`, `run-rb2.ps1`), `run-nb.ps1`,\n'
              '  `rb-chain.ps1`, `rb-tools-test.ps1`, `rb-chain-guardonly-diff.py`, `notes-resume-t14.py`.')
a = 'every `*.pre-B`, `*.pre-nolr`, `*.pre-S3`, `*.pre-S3d`) until Agent 1 says otherwise. Free C: 254.4 GB at 02:47.'
once(t, a, 'keep line')
t = t.replace(a, 'every `*.pre-B`, `*.pre-nolr`, `*.pre-S3`, `*.pre-S3d`, `*.pre-RB`, `*.pre-GuardOnly`, `snap1-backup-S3d`;\n'
              '  snapB3 and snapB3-on once made) until Agent 1 says otherwise. Free C: 251.2 GB at 03:46.')
bd = os.path.join(R, 'build', 'agent2', 'notes-backup')
os.makedirs(bd, exist_ok=True)
bk = os.path.join(bd, 'agent2-baseline.md.' + time.strftime('%H%M%S'))
shutil.copy2(P, bk)
out = t.replace('\n', '\r\n') if crlf else t
open(P, 'wb').write(out.encode('utf-8'))
print('updated %s (%s, %d -> %d bytes); backup %s' % (P, 'CRLF' if crlf else 'LF', len(raw), len(out.encode('utf-8')), bk))
