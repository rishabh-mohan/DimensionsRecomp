#### Batch 3 (task #12, applied {TIME}): the §S3.2 hash=0 guard

Agent 1 approved the fix as task #12 (02:47) and gave GO at {GO}, after Agent 10 rated it SAFE (03:31, [agent10-batch2-review.md](agent10-batch2-review.md) §13). It is my own patch; the cause, the fix and the safety argument are in §S3.2. It changes only the threaded preparation paths (N2/N3). The default serial path never calls `PrepareDrawGeometry`.

| File | sha256 | Bytes | Lines |
|---|---|---|---|
| draw.cpp before: batch 2 (above), also DimensionsRecomp HEAD `001336f`; saved as `build/agent4/scratch/draw.before-s32.cpp` | `50AA3B1DEE61567838076EDF19CB7A5466727C3CC31BE3A80E6DCC3722D7BDD6` | 306,221 | 5,753 |
| `build/agent4/s32/draw-s32.patch` (1 file, 1 hunk `@@ -1496,6 +1496,11 @@`, +5/−0) | `F54343258029F89A47BDBCC1392461B0B79686219A804A7FAE9473CF51852387` | 787 | — |
| draw.cpp after (written {MTIME}), also `build/agent4/s32/draw.cpp` | `5EA1F3576DCC2F90C7CBE410CFCDE093CB39D170A2BDD6259C3A85B41BE14410` | 306,557 | 5,758 |

**How it was applied** (no git writes), with `build/agent4/s32/apply_live.ps1` (its `-DryRun` passed at 03:16):
1. Checked the live hash (`50AA3B1D…`) and the patched copy's hash (`5EA1F357…`).
2. Saved the live file as `build/agent4/scratch/draw.before-s32.cpp` and re-hashed the backup.
3. Re-checked the live hash, then wrote the patched bytes with `[IO.File]::WriteAllBytes`. The write gives the file a new mtime, so ninja rebuilds it.
4. Re-hashed the live file: `5EA1F357…`, 306,557 B, {CRLF} CRLF line ends.
5. `git apply --check -R build/agent4/s32/draw-s32.patch` (read-only, in DimensionsRecomp) exits {RC}, and `git diff HEAD --numstat` shows `{NUMSTAT}`.

**Verification.** The written bytes are the bytes that step 1 compiled and tested on scratch copies (§S3.2 table): v3 and v2 full `-c` exit 0 with the same 77 warnings as batch 2; only `PrepareDrawGeometry` changed in the objects; fixtures 9/26 (SAME as batch 2); state shadow OK; `run_patched.py` 3/3. The in-game check is native3d's n0/n2/n3 (§S3.2, step 3).

**Line shift.** Batch-2 lines 1-1498 are unchanged; lines 1499-5753 are now at L + 5. §S3.2 cites batch-2 numbers.
