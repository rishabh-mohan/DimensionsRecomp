# Agent 7 session 3 (M7, task S3T-7), 2026-11-25, paper only

HOLD held throughout: no build, compile, syntax check, codegen or game run. No git writes. Minecraft and other
processes untouched. Scripts ran at Below Normal, `python -B`, one at a time. Wrote only under `build/agent7/`.

## 1. #19 (S4 R1 stage 2) still applies to SDK 5350b1d
- `session3/check-19-5350.ps1` -> `check-19-5350.out.txt` (5B0C07CC...): RESULT PASS.
- diff 06B0D371686CD384, RATE-REQUEST.md 1C2B8688A43ED4DC, SOAK.md F6A340A2: unchanged; all 12 SHA256SUMS.txt entries match.
- SDK HEAD 5350b1de (perf/opt); the 6 touched blobs == `orig/sdk/` == live worktree (eol lf).
- Scratch copy `session3/scratch-5350/sdk/`: `git -c core.autocrlf=false apply --check` and the real apply exit 0; results byte-equal `new/sdk/`.
- Caveats for whoever applies it: the WS is no longer inside a git repo (CHECKS.txt `--directory=games/...` form is stale; from the WS root paths are cwd-relative), and the global `core.autocrlf=true` makes `git apply` on a non-repo tree write CRLF; use `-c core.autocrlf=false` or copy `new/sdk/`.

## 2. Soak counter-line checker (SOAK.md rules 3-5)
- `s4-r1s2/soak-check/soak_check.py` (CAB5CB2C...), `test_soak_check.py` (F56D03DB...), `selftest.out.txt` (E31C3F8F...): SELFTEST PASS 26/26 on synthetic logs.
- Usage: `python -B build/agent7/s4-r1s2/soak-check/soak_check.py <run dir|game.log> [--row e|j] [--max-queued 3] [--min-lines 2] [--json out]`; exit 0 PASS / 1 FAIL / 2 INCOMPLETE.
- SOAK.md / RATE-REQUEST.md / README.md not edited (M10 is rating #19).

## 3. #21 (S4-T1) W1 matrix and proof list
- New `s4-t1/matrix-s4t1-w1.json` (269E1DBC...): W8b arms n0 / th3 / th3cp, x1, cold_run false, template timing, N-d cvars, native4b pin 9b40acbbef4c57b3 in notes.
- `s4-t1/queue-s4t1.jsonl` (290E792B -> 57245EDA): row s4t1-w1 now needs/uses `build\agent3\s4b\s4t1\matrix-s4t1-w1.json`.
- `s4-t1/check_rows.py` (701584E7 -> E5FCF544): W1 in EXPECT, ENV-KEYS-F1 check for W1, W1 arms == W8b arms. Run: ALL CHECKS PASS (0 failed), out 32D6016A.
- Originals of those 3 files: `session3/orig-s4t1/`.
- before/ == snap1 == live DimensionsRecomp gpu_native (HEAD c9e215f); `git apply --check` of s4-t1.diff from the WS root passes (before 0, -R after 0, negative 1).
- `s4-t1/THREADED-PROOFS-TODO.md` (8CEB1266...): what the proofs still need. README.md got 2 index rows.

## 4. S3T-7 (successor M7), 2026-11-25 ~02:35, paper only
Same HOLD rules. Offline tests only, Below Normal, all before 03:40. Hashes: `session3/SHA256SUMS-r19.txt`, `session3/mp/SHA256SUMS.txt`.

### A) #19 rows package (`session3/`)
- `queue-r19.jsonl` (A17F398B): 5 refs on devoff4b-bin (r19r11, r19r10, r19r13, r19r15, r19r25; the S4b refs never ran) + #19 rows a,b,i,c,g,j,d,f,e on the PLACEHOLDER bin `build\agent2\devoff4b-r19-bin`. Markers: ready-r19 + go-quiet + chain `r19-ok-<prev>`; ON rows also need go-r19on; `<N>` rows need ready-N; g needs ready-dbg.
- `r19_gate.py` (1DD4A89E): per-row gate, imports soak_check.py (CAB5CB2C) unchanged. Exit codes: 0 PASS, 1 FAIL, 2 INCOMPLETE, 3 FLAG (watchdog).
- `check_queue_r19.py` (298BB3EC): ALL CHECKS PASS, 183 checks.
- `test_r19.py` (B017F62C): SELFTEST PASS 50/50.
- `ROWS-R19.md` (5BC93446): gates, proof lines, soak_check mapping, fallback A.
- Offline controls on old runs give the expected verdicts: a/s4b01 PASS, a/cg26b0 PASS, a/N16 FAIL, i/N16 INCOMPLETE, d/N16 FAIL+INC, b/L0 FAIL, e/L0 FAIL.

### B) #21 MP2/MP3 (`session3/mp/`, Employee E7.1, verified by M7)
- `mp2_same_frames.py` (442E2AFC), `mp3_query_seq.py` (B63DD35A), `test_mp.py` (710EF192), `README-MP.md` (1ADBAF96).
- M7 reran the selftest: 25/25 OK. M7 reran the 0313 s0-vs-s0 check: spread-k 0 gives exit 1 (r3 LS 0.0001 outside the band), spread-k 1 gives exit 0, matching the saved outputs.
- All 18 SHA256SUMS entries match.
- Open questions: native perf.csv draw_calls is all 0, so the DC proxy is vacuous; the literal 2-run band is too tight (spread-k 1 recommended); LS is timing-based; F3 needs a level route with successful queries; the MP3 parser has never been checked against a real trace line.
