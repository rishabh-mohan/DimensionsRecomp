> **RESUME (session 3, task #12, 03:15 on 2026-11-22).** `draw.cpp` is still mine. Other agents send me draw.cpp patches; nobody else edits it. Live draw.cpp is still `50AA3B1D…BDD6` (306,221 B, mtime 21:24:30; checked at 02:52, 02:59 and 03:11). Nothing has been patched since batch 2.
> - **Task #12 (from Agent 1, 02:47): the §S3.2 hash=0 fix, in three steps.** Up to 1 subagent (none used). Files: `bench/agent4/**`, `build/agent4/**`, these notes, draw.cpp.
>   - **Step 1, DONE at 03:15:** the patch was built and checked on scratch copies only, with results in §S3.2. Files are in `build/agent4/s32/`: `draw.cpp` (patched copy, `5EA1F357…4410`), `draw.before.cpp`, `draw-s32.patch` (`F5434325…2387`) and the scripts. The scratch tree is `build/agent4/s32tree/`. Sent to Agent 10 (for a rating) and Agent 1.
>   - **Step 2, only at Agent 1's GO, after Agent 10 rates it SAFE:**
>     - re-check that live draw.cpp is `50AA3B1D…`;
>     - save it to `build/agent4/scratch/draw.before-s32.cpp`;
>     - `[IO.File]::WriteAllBytes` the bytes of `build/agent4/s32/draw.cpp`, with hash checks before and after;
>     - re-hash: expect `5EA1F357…4410`;
>     - log it in §S2.11 and §S3.2;
>     - send the final sha256 to Agents 1, 2, 8 and 10 (Agent 2 needs it for native3d-bin).
>     - No git writes.
>   - **Step 3:**
>     - Agent 2 builds native3d-bin (S3 plus this one-file delta).
>     - Agent 8 runs n0/n2/n3 on it as functional runs.
>     - I check those runs with `check_n_rows.py`. Expect no hash=0 lines and no new warning type. If hash=0 lines remain, suspect address-0 vertex shaders (§S3.2) and tell Agent 1.
>     - Then put th3 back into the matrix (§S3.4) with native3d-bin for every arm and at most 45 min (4 arms ×3 repeats), and send it to Agent 8.
>     - All game runs end by 08:30.
>   - Finish with `@@done 12: …`.
> - **Task #3 (session 3): DONE at 02:30.** It covered N1-N3 against §S2.12 (§S3.1), perf.csv against native-frames.csv (§S3.3) and the matrix trim to n0/th1/th2 ×4 (§S3.4).
> - **N1-N3 verdict:** N1 passes every check. N2 and N3 pass every check except one new warning type, `Native GPU shader cache miss: hash=0x0` (N2 67,220 lines, N3 44,968). Task #12 fixes it (§S3.2). N3 prints no "Native draw batches" line, which is correct (§S3.1).
> - **Waiting:** Agent 10's rating, then Agent 1's GO for step 2. T1–T13 (§S2.12) still wait for native timing data (my matrix, in a later window). Don't send `@@done 24` before then unless Agent 1 says so, because it releases draw.cpp.
> - **Native builds:**
>   - `build/agent2/native2-bin` (S2, exe `5D1B2DC6…`) was used by N1-N3, window 3's n0 and the current matrix. It needs `native_settings_frontend=false` (§S2.13).
>   - `build/agent2/native3-bin` (S3 with fix-a and S2's draw.cpp; exe `7F7F8586D219465C`, fingerprint `8f849b69907d4006`) was staged by Agent 2 at 02:50.
>   - native3d-bin (native3 plus §S3.2) comes after step 2. The matrix moves every arm to it together.
