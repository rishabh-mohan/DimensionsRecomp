# S4-T1 (#21) `LEGO_NATIVE_CHAIN_PRIORITY`: staging index (Agent 7, task #17)

Staged only: nothing here is built, compiled or run. The base is `build/agent2/snap1/DimensionsRecomp/rexlego` (the
S4b sources native4b is built from). Diff revision 2 is from 22:48.

| file | what it is |
|---|---|
| [RATE-REQUEST.md](RATE-REQUEST.md) | for Agent 10: asks, hashes, apply steps, code, unset proof, thread table, risks, must-prove map, W8b arms |
| [s4-t1.diff](s4-t1.diff) | +51/-0, paths `a/src/gpu_native/...` relative to the rexlego dir |
| [SHA256SUMS.txt](SHA256SUMS.txt) | before/after/diff sha256, bytes and CRLF lines |
| `before/src/gpu_native/`, `after/src/gpu_native/` | byte copies of the 3 files (before = snap1) |
| [make_s4t1.py](make_s4t1.py) → [make_s4t1.out.txt](make_s4t1.out.txt) | generator plus proofs 1-6 (additive, reversible, call sites, unset path, untouched, link closure) |
| [FUNCTIONAL-ROWS.md](FUNCTIONAL-ROWS.md) | rows F1/F3/W1 with commands and pass rules, and the must-prove map with minutes |
| [matrix-s4t1-f1.json](matrix-s4t1-f1.json), [matrix-s4t1-f3.json](matrix-s4t1-f3.json) | row matrices (placeholders `<NATIVE4B>`, `<NATIVE4B-S4T1>`) |
| [matrix-w8b-draft.json](matrix-w8b-draft.json) | W8b draft: n0 / th3 / th3cp x4 plus a cold run (Agent 8 owns the final copy) |
| [matrix-s4t1-w1.json](matrix-s4t1-w1.json) | W1 = W8b pre-flight: the W8b arms x1, no cold run, N-d cvars (M7, 2026-11-25) |
| [THREADED-PROOFS-TODO.md](THREADED-PROOFS-TODO.md) | what the threaded-mode proofs still need (M7, 2026-11-25) |
| [queue-s4t1.jsonl](queue-s4t1.jsonl) | Agent 3 queue rows s4t1-f1, s4t1-f3, s4t1-w1 |
| [check_rows.py](check_rows.py) → [check_rows.out.txt](check_rows.out.txt) | static check of the matrices, the queue, the keys and the hashes |
| [check/DIFF-REVIEW.md](check/DIFF-REVIEW.md) | independent read-only review: no BLOCKER; S1 is fixed in revision 2; NITs N1-N6 |
| [check/MP4-STATIC.md](check/MP4-STATIC.md) | static MP4 proof and the restated wording |
| [check/verify_diff.py](check/verify_diff.py) | the reviewer's own verification script (revision 1) |
| [check/verify_rate_request.py](check/verify_rate_request.py) | checks RATE-REQUEST.md's code blocks and hashes against after/ and SHA256SUMS.txt (PASS 22:53) |

Checks run at 22:48, all read-only, at Below Normal, from the workspace root:

```powershell
python -B build/agent7/s4-t1/make_s4t1.py      # ALL PROOFS PASS, exit 0
python -B build/agent7/s4-t1/check_rows.py     # RESULT: ALL CHECKS PASS (0 failed)
cmd /c "git apply --check -v --directory=games/lego-dimensions-recomp/build/agent7/s4-t1/before build/agent7/s4-t1/s4-t1.diff"     # exit 0, 3 files
cmd /c "git apply --check -v -R --directory=games/lego-dimensions-recomp/build/agent7/s4-t1/after build/agent7/s4-t1/s4-t1.diff"  # exit 0
cmd /c "git apply --check --directory=games/lego-dimensions-recomp/build/agent7/s4-t1/after build/agent7/s4-t1/s4-t1.diff"        # exit 1 (negative control)
```

## Update 23:27 (after Agent 9's pre-read, `build/agent9/s4-t1-preread.md` §5)
- P1: line numbers in the 3 changed files are now after-file (revision 2) numbers everywhere:
  - FUNCTIONAL-ROWS.md L36-42 and L171-172 (its header L6-8 says so);
  - matrix-s4t1-f1.json L27 and L108, and matrix-w8b-draft.json L26 (note strings only);
  - RATE-REQUEST.md L80 and L86;
  - check/DIFF-REVIEW.md: rev-2 numbers beside each :383, and the addendum L15-16.
- P2: FUNCTIONAL-ROWS.md F1 has a cold-cache note, and check (b) is read on r2, where both bins are warm.
- No code, diff or hash changed. check_rows.py was re-run: ALL CHECKS PASS (23:26).
