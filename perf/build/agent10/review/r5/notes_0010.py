#!/usr/bin/env python3
"""Splice the 00:10 updates into Agent 10's review notes (all anchors must match exactly once; else nothing is written)."""
import sys

CR = r'perf-notes\agent10-codegen-review.md'
B2 = r'perf-notes\agent10-batch2-review.md'

CR_OPS = [
('after', r"""(Corrected 23:46; until then this cell covered rows 17-20 only.) |
""", r"""| 00:00-00:08 | Agent 9's regenerated batch without skip_lr: config `build/agent9/configs/batch-nolr.toml` (E60EAF1C…, 23:52:08) and install tree `build/agent9/install/batch-nolr` (`SHA256SUMS.txt` 24CE1493…, 872 files) | **Condition 1 met** (details there). Compared with the 23:28 tree, only the LR statements changed, and they now equal the all-off output's in all 165,023 functions. 7 hook `extern` declarations moved with the new TU split (430 TUs). Row 21 gains 2 more `ctx.lr` decisions that Agent 9 found. The game gate proposal is at the end. |
"""),
('replace', r"""- **Blocks the batch config: `skip_lr` itself is UNSAFE for LEGO (row 21).** Host code reads `ctx.lr` to find out who called it, and under skip_lr no caller writes `ctx.lr`. Take `skip_lr = true` out of `batch.toml`/S2.10 and regenerate. The other 9 keys don't touch LR.
""", r"""- **`skip_lr` itself is UNSAFE for LEGO (row 21).** Host code reads `ctx.lr` to find out who called it, and under skip_lr no caller writes `ctx.lr`. The other 9 keys don't touch LR.
  - Resolved at 00:08: Agent 9 dropped it from the batch (`batch-nolr`), and my diff shows that only the LR statements changed (condition 1).
"""),
('after', r"""All three check the status, so the likely effect is an optional feature that silently goes missing.
""", r"""  - **`rexlego/src/native_slot_growth.cpp:63, 76`** (Agent 9 found these two at 00:02; I had missed them). The native slot heap's `Grow` and `Release` thunks return r3 = 0 unless `ctx.lr` is 0x82A33FC4 or 0x82A3B88C. The thunks are made with `AllocateThunk` (:86) and published in the provider vtable (:88-91). Under skip_lr the slot heap would never grow or release a region.
  - **`rexlego/src/settings_native_hooks.cpp:174`.** The `sub_839C4D08` hook draws the extra pause-menu Options rows only when `ctx.lr` is 0x839D11B0, the TU23 call site for the final Back row. Under skip_lr those rows would silently disappear.
"""),
('replace', r"""  - (b) Turn it on only after the owners remove both `ctx.lr` decisions: the gpu_native hook (e.g. identify the 0x83F9B65C call site with a mid-asm hook) and XexGetProcedureAddress.
""", r"""  - (b) Turn it on only after the owners remove all four `ctx.lr` decisions above: the gpu_native hook (e.g. identify the 0x83F9B65C call site with a mid-asm hook), XexGetProcedureAddress, the slot-heap thunks and the pause-menu hook.
"""),
('replace', r"""**Conditions before a game build turns the batch on** (status at 23:46, from Agent 9's S2.8 at 23:42)
""", r"""**Conditions before a game build turns the batch on** (status at 00:08)
"""),
('replace', r"""1. **OPEN, blocking:** remove `skip_lr = true` from `batch.toml`/S2.10 (row 21) and regenerate. Then re-take the 0-handoff-error gate and the S2.8 counts on the new output.
   - At 23:45, `build/agent9/configs/batch.toml` (B2727250…, 22:50:27) still sets it (line 26).
   - The install tree `build/agent9/install/batch` (23:28), which Agent 2's B build uses, was generated from that config.
""", r"""1. **Met (00:08):** Agent 9 took `skip_lr = true` out and regenerated (`batch-nolr`, 23:53). Agent 9's handoff gate: 0 "Code generation blocked", 0 handoff errors. My check uses `build/agent10/review/r5/lrdiff.py`; the report is `r5/lrdiff-report.txt` (82D2978A…).
   - Config: `build/agent9/configs/batch-nolr.toml` (E60EAF1C…, 23:52:08; the install tree has the same bytes) differs from `batch.toml` only by the `skip_lr = true` line and two comment lines.
   - Tree: `build/agent9/install/batch-nolr`. Its `SHA256SUMS.txt` (24CE1493…) matches all 872 files (481,074,943 B), and no file is unlisted (`r5/verify_sums.py`).
   - The TU split changes (430 TUs, was 412), so the compare is per function: against my copy of the 23:28 tree (`r5/batch-2328`) and against `off4` (all options off, final tool).
     - 165,023 functions on each side, none on one side only, no duplicates.
     - With the LR statements removed (`ctx.lr = <const>`, `ctx.lr = ctx.rN.u64` and `ctx.rN.u64 = ctx.lr`), 165,017 bodies are byte-identical. The other 6 differ only by 7 mid-asm hook `extern` declarations that moved with the split: the five `NativeCelShading*`, `MissingAdventureTimeLookupNode` and `RepairDialogueLockReleaseOperand`. A misplaced declaration fails to compile, so it can't change behaviour silently.
     - The per-TU header line set and the TU preambles don't differ.
     - The LR statements equal off4's in every function (129,043 functions have any): 128,920 `mflr` reads, plus 621,314 constant stores and 97,918 `mtlr` copies, which are the 719,232 writes in Agent 9's S2.8. The one other `ctx.lr` read (`auto old_lr = ctx.lr;` in `sub_83E5C830`) is unchanged.
     - Other files: `_pch.h` loses only `#define REX_CONFIG_SKIP_LR`, and `init.cpp` changes only `.skip_lr = true` to `false`. `funcs.h` (76EFB251…), `register.cpp` (747F2EDA…), `init.h` and `codegen.d` are identical. `sources.cmake` adds TUs 412-429. The partition and the stamps differ, as expected.
   - Agent 9's own diff agrees: 165,017 identical, and 6 that differ by the 7 moved declarations.
   - So B is the reviewed option set minus skip_lr. Agent 2 should build B from `install/batch-nolr` (SHA256SUMS 24CE1493…). The 23:28 `install/batch` stays for diffs only.
"""),
('replace', r"""Agent 9's CPU-time follow-up (HEAVYCPU) is due at 00:05.""",
 r"""Agent 9's CPU-time follow-up didn't run (paused at 23:51), so HEAVYCPU and HEAVYTIME come from the first pass (`agent9-codegen.md:11`)."""),
('replace', r"""6. **Open:** the game gate (Agent 8) on the native GPU build.
""", r"""6. **Open:** the game gate (Agent 8) on the native GPU build. My proposal for what it checks is in the next section.
"""),
('append', None, r"""
## B native game gate: proposal (00:10, for Agent 1 and Agent 8)

**What it covers.** Agent 9's tests check instructions one at a time. The game gate covers what they can't see:
- host code (hooks, thunks, kernel exports) that reads guest state from `ctx` while B changes how generated code keeps that state;
- whole-game numerics under `flush_mode_elision`, `vmx_vector_fallbacks` and `rlwinm_lowering`;
- long `musttail` chains (stack depth);
- Agent 9's accepted residual: a restored XER.SO = 1 under `cr_compare_so_zero` (`sub_83E5C88C`, `agent9-codegen.md:185-194`). The incoming-LR residual (:110) no longer applies, because skip_lr is gone.

**Setup**
- B: the S2 sources with the `install/batch-nolr` codegen, NATIVE_GPU=ON, built like `native-bin`. Baseline: the same S2 build with the S1 codegen, so the codegen options are the only difference.
- One run of each through Agent 8's slot: the same save, toml and route, with the perf CSV on.
- Leave `LEGO_NATIVE_MEMOPS_VALIDATE` unset. Agent 9 found that its checks report false mismatches under Stage A.
- Optional: a second B run with `LEGO_DUMP_MISSING_SHADERS=1`, which makes the pool-copy hook verify the copied bytes.

**Route.** Each step reaches host code that depends on `ctx` state.
1. Boot, title screen, load the save. This covers the 3 `XexGetProcedureAddress` lookups and the slot-heap registration ("Native slot heap: registered slot=…").
2. A level with cel-shaded characters on screen (the `NativeCelShading*` mid-asm hooks) and some streaming (the LR-gated slot-heap `Grow`).
3. Pause, open Options, scroll to the last row (Back), back out and unpause. The LR-gated `sub_839C4D08` hook must draw the extra rows.
4. A dialogue or cutscene (`RepairDialogueLockReleaseOperand`), and an Adventure Time area if the save reaches one (`MissingAdventureTimeLookupNode`).
5. Leave the level and load another. This covers the placement-buffer relocation (`sub_83FC49E8` called from 0x83F9B660) and the pool-copy drain.
6. Add and remove a toy-pad figure, with audio on throughout. Save, then Quit Game.

**Fail if any of these happen in B**
- A crash, a hang or watchdog fingerprint, 0xC0000409 or a stack overflow.
- Any of these log lines: "not in any registered module" (a failed `AllocateThunk`), "Native GPU: pool copy unsupported", "pool copy POINTLIST contract mismatch", "Native slot heap: external detach verification failed".
- More unimplemented-instruction (`REX_UNIMPLEMENTED`) lines than the baseline has. The `vupkd3d128` gap is pre-existing.

**Must match the baseline**
- "Native GPU: placement buffer relocation type … lr=83F9B660" lines appear at the same steps.
  - The line is logged only when the caller check that also gates the drain matches (`hooks_buffer.cpp:389`, `:400`).
  - The drain itself logs nothing. Agent 6 or 7 could add a counter for direct proof, but B keeps the LR writes, so the line is enough.
- The same set of callers in "Native GPU: CPU pool copy … caller=" (the first 128 copies are logged).
- "Native slot heap: registered …" appears, and "extended …" (the LR-gated `Grow`) too if the baseline logs it on this route.
- The extra pause-menu rows from step 3 are visible (screenshot).
- Export lookups: nothing logs a successful `XexGetProcedureAddress`. Short of adding a debug line, check for 0 "not in any registered module" in both runs. If Agent 11's kernel tracing can log the boot lookups (`sub_83FA60E8` and the ordinal 80 and 36 lookups), compare their status and address too.
- Screenshots at 4 fixed points (title screen, level spawn, pause menu, one cutscene frame) look the same, and the audio is clean.
- Perf CSV frame times are for information only. B is a CPU-side change, and matrix 1 was locked at 60 fps.
"""),
]

B2_OPS = [
('after', r"""  Making it the default is a one-line cvar flip (:48), so it fits batch 3. S2 takes the change at the default, OFF.
""", r"""- **Condition met (00:08).**
  - Agent 12's replica (`agent12-io-memory.md:556-566`; exe EFEF2094 unless noted): NEW had 0 HUNG and 0 CRASHED in 4,000 runs (1,000 each of h, p and b, plus 1,000 h on exe E5DA67F4). OLD h had 429 HUNG and 171 CRASHED in 1,000; OLD b had 2 CRASHED.
  - `-SyntaxOnly` on the 21:56 revision exited 0 at 22:23 (:416, :527).
  - Agent 1 accepted R1 (~23:57), so the ON flip goes into S3.
  - I confirm the ON rating when Agent 12 sends the one-line diff after quiet window 3.
"""),
('append', None, r"""
## 11. Agent 11: S3 proposal, `pause_safe_order` default ON (reviewed 00:00-00:10)

**Listing.** `agent11-kernel.md` "S3 proposal" (:1202-1290). Staged in `build/agent11/safeorder/`, not in the live tree:
- `safeorder.diff`: 56952876…, 2,101 B, 23:48:47, LF; 2 hunks, -5/+7, all in `src/ui/rex_app.cpp`.
- Staged `rex_app.cpp` 11DE333F…. The live file is still pristine (E1569868…, 19:43:51), as `safeorder_stage.ps1 -Apply` requires.
- Hunk 1 (:71-75) changes the default from false to true and says in the help text why. Hunk 2 (:741-745) changes the comment to "default on" and cites test G.
- No code changes, and the kill switch stays (`--pause_safe_order=false`).

**Verdict: SAFE.** The safe order (task #17, already in S2) removes the deadlock, and it gives up nothing that the original order did correctly.
- **What runs while guest threads are stopped** (`SetGuestPaused`, rex_app.cpp:745-788):
  - Pause: `audio->Pause()`, the thread snapshot (the object table lock and an allocation) and the log line all run first, while the guest runs (:751-765). Then only the `Suspend` loop runs (:767-769).
  - Unpause: the `Resume` loop runs first, over the pause's own list (:774-779). `audio->Resume()`, the log line and `entries.clear()` run after every thread is running again.
  - `XThread::Suspend` (xthread.cpp:1015-1044) holds the global critical region and the object table lock until the thread has really stopped, so no thread stops while holding either one. On Win32, `XThread::Resume` (:964-974) is an atomic decrement plus `ResumeThread`, with no lock, allocation or log. Both orders use these same two calls.
  - The original order (:790-812) suspends first and then waits in `audio->Pause()` for the audio worker, which may be inside a guest callback that needs the stopped threads. That is test G's hang. It also logs while threads are stopped, and its unpause allocates and takes the object table lock before it resumes anything.
- **The unpause resumes only what the pause suspended.** The original unpause takes a fresh snapshot, so it also resumes threads the pause never suspended:
  - a thread the guest created suspended in the meantime starts early;
  - a running thread gets its guest suspend count wrapped (the Win32 `fetch_sub` has no floor).
- **One small difference, harmless.** `Suspend` increments the guest count (:1018) before it calls the host. If the host call fails, the safe unpause skips that entry, so the count stays one higher, where the original unpause decremented it. In practice only an exiting or exited thread fails there, and nothing suspends or resumes it again.
- **Shared by both orders:** a guest thread created between the snapshot and its creator's suspension isn't suspended. The comment at :750 is why audio pauses before the snapshot: threads created during that wait are still caught.
- **Lifetime.** `GetSafeOrderPause()` is leaked on purpose (:104-107), so nothing releases thread references at process exit. `active` latches the path (:745), so flipping the cvar during a pause can't strand a thread.
- **Who it affects.** `SetGuestPaused` runs only on focus changes (:818, :825) and from the debug cycle (`debug_pause_cycle_ms`, default 0). The pause on focus loss needs `pause_when_unfocused`, which defaults to false (window.cpp:43; offered in the settings UI, ui_theme.cpp:99). No repo toml sets either cvar, rexlego never calls `SetGuestPaused`, and every runner passes `--pause_when_unfocused=false`. So the flip matters only for players who turn that setting on, and for them it removes a hang.
- **Evidence.** Test G (#23): the original order hung in 2 of 2 runs. The 23:22 dump shows the UI thread in `pause_fence_.Wait()`, the Audio Worker in the game's callback blocked in `KeWaitForMultipleObjects`, and every guest thread suspended. The safe order passed 100 of 100 pauses (50 with B OFF, 50 with B ON). Agent 11's checks: `safeorder_stage.ps1` PASS 11/11, and the pristine and staged files both pass `-fsyntax-only` with the same 3 pre-existing warnings.
- **Not fixed in either order** (Agent 11's :1254-1261): a stopped thread could still hold a host lock (G, T, the CRT heap or the logger) that the UI thread's message loop needs. Cosmetic: "Guest suspended" is logged just before the threads actually stop.
- **With #22's ON flip in S3.** `Pause()` and `Resume()` don't change. The worker's `leave()`/`reenter()` are uncontended CAS operations unless Shutdown runs, so test G's result carries over. Worth doing: Agent 11's optional test G half 1 on the S3 build without an explicit `--pause_safe_order` (:1290), so that the default itself is tested.

**Landing (agent11-kernel.md:1284-1289).** Agent 12 runs `bench\agent11\safeorder_stage.ps1 -Apply` after quiet window 3 and before S3 is cut. The script refuses unless the live file still equals pristine E1569868…. Then `safeorder_stage.ps1 -Check` (`staged (applied)`) and `safeorder_syntax.ps1 -Live`, which is a compile, so not during a quiet window. To undo: `-Revert`.
"""),
]


def apply(path, ops):
    with open(path, encoding='utf-8', newline='') as f:
        text = f.read()
    if '\r\n' in text:
        print(f'{path}: has CRLF line endings; aborting')
        sys.exit(1)
    orig = text
    for kind, anchor, content in ops:
        if kind == 'append':
            if not text.endswith('\n'):
                text += '\n'
            text += content
            continue
        n = text.count(anchor)
        if n != 1:
            print(f'{path}: anchor found {n} times: {anchor[:90]!r}')
            sys.exit(1)
        text = text.replace(anchor, anchor + content if kind == 'after' else content, 1)
    return orig, text


results = [(p, *apply(p, ops)) for p, ops in ((CR, CR_OPS), (B2, B2_OPS))]
for path, orig, text in results:
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    print(f'{path}: {orig.count(chr(10))} -> {text.count(chr(10))} lines, {len(orig.encode())} -> {len(text.encode())} B')
