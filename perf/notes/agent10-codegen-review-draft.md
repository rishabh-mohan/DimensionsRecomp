# Agent 10: J4 CODEGEN CROSS-REVIEW of Agent 9's uncommitted rexglue-sdk changes (DRAFT)

Reviewer: Agent 10 subagent, 2026-11-21 17:58 to 18:30 local. The base is `DimensionsRecomp/rexglue-sdk` @ `2897c31` plus the working tree. This was a read-only review: nothing was built and nothing was edited. Every `file:line` below is in the **current working tree** unless marked `pin:`.

---

## (a) Snapshot and what changed since 16:50

| Snapshot | Time | What it contains |
|---|---|---|
| `build/agent10/review/agent9-1759.patch` | 17:59 | `git diff -- include src`. 17,749 B, 364 lines. **This is the patch reviewed.** |
| `build/agent10/review/agent9-1811.patch` | 18:11 | The same command again, 26,912 B. Its codegen part (`agent9-1811-codegen.patch`, i.e. `-- include/rex/codegen src/codegen`) is **byte-identical to 1759**. |
| `build/agent10/review/agent9-1650.utf8.patch` | 16:50 | The original was UTF-16; it was converted for diffing. |

**Extra in 18:11 (not reviewed, not codegen).** The working tree also has `src/core/threading_posix.cpp` (+11) and `src/core/threading_win.cpp` (+169), plus the untracked `include/rex/threading_timeout.h` and `include/rex/threading_timing.h`. These headers are included only by `threading_win.cpp:11-12` and `threading_posix.cpp:11`, so they cannot affect generated TUs. Whoever owns that work should get its own review.

**16:50 to 17:59 delta.** The only change is the new `BuilderContext::check_register_handoff`. It consists of:
- the declaration, `builder_context.h:238-243`;
- the definition, `context.cpp:177-181`;
- three call sites:
  - `context.cpp:208` (direct call or tail call);
  - `context.cpp:351` (conditional tail call);
  - `control_flow.cpp:149` (jump-table case).

Every other hunk is unchanged since 16:50.

Files in the reviewed diff:
- `include/rex/codegen/config.h`
- `include/rex/codegen/function_types.h`
- `src/codegen/builders/builder_context.h`
- `src/codegen/builders/context.cpp`
- `src/codegen/builders/control_flow.cpp`
- `src/codegen/codegen_writer.cpp`
- `src/codegen/config.cpp`
- `src/codegen/function_graph.cpp`

Nothing in `resources/templates`, `include/rex/ppc/*` or `tests/` is modified.

---

## (b) Verdict table

| # | Change | Files:lines | Intent | Verdict | One-line reason |
|---|---|---|---|---|---|
| 1 | Drop the `body=` "requires all localization options disabled" reject | `codegen_writer.cpp` `ValidateFunctionBodies`: pin lines 52-55 deleted (now between 52 and 53) | Let LEGO (5 `body=` entries) turn localization on | **SAFE-IF** | Safe only together with #2. It also **breaks `tests/regression/emit_interior_entries.cpp:240-252`**, which still expects each localization flag to be rejected. |
| 2 | `RegisterFallback` / `BuildRegisterFallback` and its wiring | `codegen_writer.cpp:149-234, 460-465`; `function_types.h:59-65`; `builder_context.h:101-103`; `function_graph.cpp:566-568, 666-667` | Interior entries, body owners, functions with a direct edge or jump table into an interior entry, and save/restore helpers keep **all** registers in `ctx` | **SAFE-IF** | Correct for every *graph-visible* transfer. It misses three things: (i) jump tables detected only at emission time (`function_graph.cpp:620-654`); (ii) entries that sit in a gap of the brancher's range rather than in a block; (iii) computed `bctr` with no table. Details in C2. |
| 3 | Accessors honour `!registersInCtx` | `context.cpp:47-50, 52-114` | Per-function ctx mode | **SAFE** | Every localizable register goes through these 7 accessors, and each returns `ctx.X` when `registersInCtx` is set. The localizable set is r0/r2/r11/r12, r14-31, f0, f14-31, v14-31/v32-63/v64-127, cr0-7, ctr, xer and reserved. |
| 4 | Save/restore helper elision also requires `!registersInCtx` | `context.cpp:216-220` | ctx-mode functions make real `__save*`/`__rest*` calls | **SAFE** | The helpers themselves are put in ctx mode whenever any ctx-mode function exists (`codegen_writer.cpp:216-217`). `inCtx` is non-empty exactly when `interior` is non-empty. |
| 5 | `check_register_handoff` | `context.cpp:177-181, 208, 351`; `control_flow.cpp:149` | Detect a localized function handing off to an interior entry | **SAFE** (it emits nothing) **but insufficient** | It only logs (`REXCODEGEN_ERROR` → `REXLOG_CAT_ERROR`, `codegen_logging.h:23`). `write()` still returns success (`codegen_writer.cpp:460-539` checks no error count), so the miscompile is emitted. |
| 6 | New keys `rlwinm_lowering`, `flush_mode_elision`, `cr_compare_so_zero`, `musttail_calls` | `config.h:104-108`; `config.cpp:119-126` | Future emission options | **SAFE (inert)** | All default to `false`. `MergeBool` overrides only when the TOML value is an explicit bool. There are no consumers in `src/`, `include/` or `resources/`, and the keys are not in `configFlags` (`codegen_writer.cpp:287-296`). |
| 7 | Off-path output | all | Byte-identical when off | **SAFE** | With all 6 localization flags off, `BuildRegisterFallback` returns at `:164-167`, the pointers stay null and `registersInCtx` is false everywhere. Output is identical. It is also identical with flags on and no overlapping entries (`:197-198`). |
| 8 | (config combination, not a hunk) `non_argument_as_local=true` with `non_volatile_as_local=false` | `context.cpp:54-55, 216`; helper ABI `function_scanner.cpp:134-135, 148-149, 161-162` | Agent 9 "stage B alone" | **UNSAFE** (pre-existing, newly reachable for LEGO) | The FPR and VMX helpers take r12 (and r11) implicitly. A localized caller writes a local `r12`, and the helper reads either `ctx.r12` (stale) or its own zero local. Before this diff, removed reject #1 kept LEGO from enabling any localization flag. Sequence in C6. |

---

## (c) Detail per change

### C1. Removal of the `ValidateFunctionBodies` reject (SAFE-IF)

- **What was removed.** At the pin (`git show 2897c31:src/codegen/codegen_writer.cpp`, lines 52-55), any of the six `*AsLocal*` flags plus any `body=` entry made validation fail with the message "interior body entries require all register localization options disabled". The current file goes straight from the chunk/alignment check (`:50-52`) to the nested-owner check (`:53-55`).
- **Safe only with #2.** Without the fallback, an interior entry E would read registers its jumping function holds in C++ locals. With #2, E, its owner and every direct brancher are in ctx mode (see C2 for what is still missed).
- **Regression test breaks.** `tests/regression/emit_interior_entries.cpp:240-252` loops over all six flags and calls `reject(invalid, "localization-N")`. That helper (`:211-218`) asserts `!rejected.write(true)` and that `out/generated` does not exist. Both checks now fail, so `regression_interior_entries` (wired at `tests/CMakeLists.txt:25,29`) and therefore `test_interior_entries.py` will fail.
  - **Required:** turn that loop into positive checks (design T2).

### C2. RegisterFallback (SAFE-IF): coverage of every transfer kind into an interior entry E

How the sets are built (`codegen_writer.cpp`):
- **`interior`** (`:174-196`): every `body=` entry, plus every non-import, non-helper graph entry that lies inside another function's **blocks**. This uses an ordered `std::set` with `lower_bound` and a half-open `[block.base, block.end())` range, so there are no off-by-ones.
- **`inCtx`** (`:174-228`): owners, plus direct callers, plus jump-table owners (graph `jumpTables()` at `:212-213` and `config.switchTables` at `:219-227`), plus helpers, plus everything in `interior`.
- **Consumption.** `function_graph.cpp:567-568` looks up `entry.base()`. For a `body=` entry, `write()` calls `owner->emitCpp(emitCtx, E)` (`codegen_writer.cpp:481-484`), so the lookup key is E (in ctx). The owner's own emission is keyed by the owner (in ctx through `:176`).

| Transfer into E | Caught by fallback? | `check_register_handoff` | If the brancher stays localized |
|---|---|---|---|
| `bl E`, graph call edge | yes, `:210` | `:208` | n/a |
| `b E` / `bc E` tail call with graph edge (`build_b` → `emit_function_call`, `control_flow.cpp:40-45`; `emit_conditional_branch` `context.cpp:345-356`) | yes, `:211` | `:208` / `:351` | n/a |
| Jump table recorded in `fn.jumpTables()` | yes, `:212-213` | `control_flow.cpp:149` | n/a |
| `config.switchTables` | yes, `:219-227` | `:149` | n/a |
| **Jump table found only during emission** (`function_graph.cpp:620-654`, kept in the local `lateJumpTables`) | **no** | `:149` logs ERROR, codegen succeeds | **silent miscompile** |
| **`b E` where E is inside the brancher's `[base,end)` but in a gap, not inside any other function's block** | **no**: `:186-196` checks blocks only, while `classifyTarget` treats any entry as a Function (Case 3, `function_graph.cpp:1350-1382`) | silent (E is not in `interiorEntries`) | silent miscompile if E uses live registers. The same hole existed at the pin for every localized build. |
| `mtctr; bctr` with no table (`control_flow.cpp:176-183`), `bctrl`, `blrl`, function pointer | no (dynamic target) | n/a | silent miscompile **only if** E expects non-ABI registers |
| Fall-through from the owner into E's code inside the owner's own C++ body | n/a, the code is inline | none | fine |
| `bdnz`/`bdz`/... out of function (`helpers.h:388-397`) | none | none | Pre-existing: emits `return;` and never transfers. Wrong regardless of localization. |

**Concrete UNSAFE sequence for the late-table row** (function F is localized and the table is not in `fn.jumpTables()`):

```asm
F:      mflr r12
        bl   __savegprlr_29
        stwu r1,-0x70(r1)
        lwz  r31,0(r3)              # r31 live -> local `r31` in F
        cmplwi cr6,r4,3
        bgt  cr6,F_default
        lis  r11,tbl@ha
        addi r11,r11,tbl@l
        rlwinm r0,r4,2,0,29
        lwzx r0,r11,r0
        mtctr r0
        bctr                        # detected at function_graph.cpp:620-654
tbl:    .long F_case0, E, ...       # E = interior entry (inside owner O's blocks) that reads r31
```

The emitted shape in F is roughly `switch (r4.u32) { case 1: sub_E(ctx, base); return; ... }` with `PPCRegister r31{};` declared locally. `sub_E` is in ctx mode and reads `ctx.r31`, which is stale. The only symptom is an ERROR line in the log.

**Required for SAFE.** Do one of the following:
- (a) make a fired `check_register_handoff` fail `write()`, for example with an error counter checked before `FlushPendingWrites()`; or
- (b) run the same `mtctr`/`bctr` + `detect_jump_table` probe inside `BuildRegisterFallback`.

Also do (c): report entries in a range gap, i.e. E with `F.base < E < F.end` and E not in any block of F, and add them to `interior` if F has an edge to them.

For the indirect row, the answer has to come from Agent 9 (question F2).

**Other C2 notes**
- **Mixed ctx/local calls keep the ABI.** r1, r3-r10, r13, f1-f13 and ctr/xer/cr/lr are passed through `ctx` or are volatile.
  - Localized functions never read or write `ctx.r14-31` (and the same for f and v), so a ctx-mode callee that saves and restores them through real helper calls cannot disturb a localized caller.
  - In the other direction, a localized callee leaves `ctx.r14-31` untouched for a ctx-mode caller.
  - CR fields 2-4 (non-volatile) follow the same argument: `mfcr`/`mtcrf` act on whichever storage the current function uses.
- **CTR, XER.CA and reserved** are volatile across calls. Inside one ctx-mode function they all flow through `ctx`, so transfers to E and from E are correct.
- **FPSCR** is never localized. `csrState` is reset at labels (`function_graph.cpp:597`) and after calls (`control_flow.cpp:82, 105, 191`). The `goto loc_E` at the top of a `body=` emission (`:577-578`) lands on a label, so it starts as Unknown, which is correct.
- **Helper classification by name** (`codegen_writer.cpp:169-172`). A non-helper whose name starts with `__save` or `__rest` is excluded from interior detection and forced into ctx mode. The ctx mode is harmless; missing it as an interior entry has negligible risk. Name-based elision at `context.cpp:216-217` already existed at the pin.
- **Behaviour change for other SDK users.** With localization on and overlapping entries but no `body=`, output now changes: more functions are in ctx mode. That is more conservative and arguably a bug fix, but it is not byte-identical for those users.
- **Generator C++ is OK.**
  - `unordered_set`s are used only for membership tests, so emission order is deterministic.
  - `registerFallback` (`:461`) outlives every use of `emitCtx` because emission is sequential (`:479-492`) and nothing escapes `write()`.
  - Aggregate order matches the member order (`builder_context.h:99-103` against `function_graph.cpp:666-667`, the only construction).
  - The other `EmitContext` constructions (`codegen_writer.cpp:455`, `test_recompiler.cpp:364`, `emit_interior_entries.cpp:202`) get null pointers by default.
  - `<set>` is included (`:18`).
  - The `callers` count in the INFO line can include interior functions that hold a switch `bctr` (`:225`). This is cosmetic.
- **Test-harness gap.** `recompile-tests` builds its own `EmitContext` with a default `RecompilerConfig` (`test_recompiler.cpp:348-364`). `BuildRegisterFallback` is file-local to `codegen_writer.cpp`, so `tests/ppc` can never exercise the fallback or any localization flag.

### C3. Accessor gating (SAFE)
- `context.cpp:52-114`. Each localizing branch is now `cfg.X && !registersInCtx`, and `localizeNonVolatiles()` (`:47-50`) adds `!registersInCtx`.
- When `registersInCtx=false`, behaviour is the same as at the pin.
- When `registersInCtx=true`, the accessors return `ctx.*`, and the local declarations (`function_graph.cpp:724-758`) are never set for those registers, so no dead `{}` locals are emitted.
- The `temp`, `v_temp`, `env` and `ea` scratch locals are unaffected. They are never live across a transfer.
- **Coverage check.** I grepped `src/codegen` for register names written directly into emitted strings instead of going through an accessor. The only hit is `function_graph.cpp:696` (the SEH catch, `ctx.r12 = ctx.r31 + N`, pre-existing, see C8). No string hard-codes a local register name. So every builder goes through the gated accessors, for example `arithmetic.cpp:34-86` (CA via `ctx.xer()`), `control_flow.cpp:181-258` (CTR via `ctx.ctr()`), `helpers.h:283-312` (reserved and SO) and `system.cpp:214, 308, 356-358`.

### C4. Helper elision (SAFE)
- `context.cpp:216-220`. In ctx mode, a call to `__savegprlr_N` and similar now executes, and the helper body is in ctx mode (`codegen_writer.cpp:216-217`).
- A ctx-mode caller sets `ctx.r12` (and `ctx.r11` for VMX) before the call, so the helper uses the right base address.
- Localized NV-mode callers still elide the call, as they did at the pin.
- SEH funclets (`sharesRegisters`) still elide helpers and use the sync at `context.cpp:226-238`. That behaviour is pre-existing and not changed by this diff.

### C5. `check_register_handoff` (SAFE, but only a diagnostic)
- It covers all three static emit sites that produce `sub_X(ctx, base)` for a graph function: `context.cpp:208`, `:351` and `control_flow.cpp:149`.
- It cannot cover `REX_CALL_INDIRECT_FUNC` sites.
- It logs only, so it does not protect anything (see C2, Required (a)).
- Precondition: `interiorEntries` is set only when `inCtx` is non-empty (`codegen_writer.cpp:462-465`), so the check is a no-op on the off path.

### C6. Stage B alone: concrete miscompile (UNSAFE configuration)
Config: `non_argument_as_local=true` and `non_volatile_as_local=false`.

```asm
C:      mflr r12
        bl   __savegprlr_29         # stores r29-r31 at -x(r1) and r12 (LR) at -8(r1)
        addi r12,r1,-0x20           # FPR save-area base  -> local `r12`
        bl   __savefpr_30           # helper: stfd f30,-0x10(r12) ; stfd f31,-0x8(r12) ; blr
        stwu r1,-0x80(r1)
        ...                         # clobbers f30/f31
        addi r12,r1,0x80-0x20
        bl   __restfpr_30           # lfd f30,-0x10(r12) ; lfd f31,-0x8(r12)
```

- In C: `r12.s64 = ctx.r1.s64 + -32; ... __savefpr_30(ctx, base);`. The call is **not** elided because `context.cpp:216` requires `nonVolatileRegistersAsLocalVariables`.
- In the helper, as of today:
  - If `inCtx` is non-empty (LEGO, which has body/interior entries), the store goes to `ctx.r12.u32 - 16`, which is stale: an arbitrary guest address.
  - Otherwise the helper is localized, `PPCRegister r12{}` is 0, and the store goes to `0xFFFFFFF0`.
- `__restfpr_30` later reloads f30 and f31 from a different wrong address, so the caller's caller loses its callee-saved FPRs.
- The VMX helpers fail the same way with r11 and r12 (`lvx/stvx[128] vN, r11, r12`, `function_scanner.cpp:148-149, 161-162`).
- This was already broken at the pin. Reject #1 was the only thing that kept LEGO's config (which has `body=` entries) from reaching it.
- **Required.** Do one of:
  - reject `non_argument_as_local && !non_volatile_as_local` in config validation; or
  - always put helpers in ctx mode whenever any flag is on, and emit `ctx.r11 = r11; ctx.r12 = r12;` before a non-elided helper call from a localized function.

### C7. New config keys (SAFE, inert)
- `config.h:104-108` and `config.cpp:119-126`. The TOML keys are root-level `rlwinm_lowering`, `flush_mode_elision`, `cr_compare_so_zero` and `musttail_calls`. All default to `false`. A non-bool value is ignored silently, which matches the existing keys.
- They have no consumers, so there is no output change.
- They are not in `buildTemplateData` `configFlags` (`codegen_writer.cpp:287-296`) or in `image_info`. That is fine now. When consumers land, adding them there would change `init.cpp` and could change the PCH (see (e)).

### C8. Pre-existing issues noticed (not in the diff, not introduced by it)
- **setjmp.**
  - In a localized function, `ctx = env` (`context.cpp:192-201`) restores ctx but not the local NVs or CR, so after a `longjmp` they hold post-setjmp values.
  - The fallback does not add callers of `setJmpAddress` to `inCtx`. Doing so is cheap and conservative.
  - LEGO's TOML sets no `setjmp`/`longjmp` keys (checked `rexlego/*.toml`). NEEDS-INFO: is it auto-detected?
- **SEH catch block.** `function_graph.cpp:696` hard-codes `ctx.r31`/`ctx.r12`. Under NV localization `r31` is a local, so the establisher frame is wrong. This only matters with `generate_exception_handlers`.
- **`blrl` under `skip_lr`.** `control_flow.cpp:101-104` reads `ctx.lr`, which is stale under `skip_lr`.
- **Out-of-function CTR branches.** `helpers.h:390-393` emits `return;` instead of a transfer for out-of-function `bdnz`-style CTR branches.
- **`REX_CONFIG_*` defines.** `pch_h.inja:11-18` emits them, but no header consumes them (the only hit is a comment at `context.h:277`). So ctx-mode functions in a localized build do not conflict with any macro.

---

## (d) Differential test designs

Constraints:
- `tests/ppc` is driven by `recompile-tests` with a **default** `RecompilerConfig` (`test_recompiler.cpp:348`), so it can only check the off path.
- The format is a `test_<name>:` label with `#_ REGISTER_IN rN v`, `#_ REGISTER_OUT rN v`, `#_ MEMORY_IN` and `#_ MEMORY_OUT`. The suite has 166 files, for example `seq_branch_carry.s` and `instr_addic.s`.
- Localization tests therefore belong in the `tests/regression/emit_interior_entries.cpp` producer style (a hand-built graph plus `CodegenWriter`, compiled and run by `test_interior_entries.py`), or need a new flags option on `recompile-tests`.

| ID | Catches | Design |
|---|---|---|
| T1 | Off-path drift | Run the LEGO codegen with the pin tool and with the new tool, all localization flags off, then `diff -r` the generated directories. Must be identical. Repeat with `ctr_as_local=cr_as_local=xer_as_local=true` on a synthetic image with no overlapping entries: it must also be identical to the pin. |
| T2 | C1 test break; fallback actually applied | Replace `emit_interior_entries.cpp:240-252`. For each flag alone and for all six together: (1) `write(true)` returns true; (2) the bodies of `sub_82000018` (entry), `sub_82000000` (owner) and any fixture caller with an edge to the entry contain **no** `PPCRegister r3x{}`, `PPCCRRegister crN{}`, `PPCRegister ctr{}` or `PPCXERRegister xer{}` declarations and do contain the `ctx.` forms; (3) a control function with no edge to the entry **does** declare locals, which proves the flag is live; (4) `__savegprlr_*` bodies use `ctx.r`, and ctx-mode functions emit `__savegprlr_N(ctx, base);` rather than eliding it. Then compile and run through `test_interior_entries.py` and compare the final `PPCContext` (r1, r3, r14-31, cr0-7, ctr, xer, and touched memory) from `xstart` between the all-off build and each flag build. They must be equal. |
| T3 | A missed ctx mode for the brancher, E or owner | Fixture. Owner O at `0x82000000`: prologue (`mflr r12; stw r12,-8(r1); stwu r1,-0x60(r1)`), then `mr r31,r3; li r30,7; cmpwi cr6,r4,0; mtctr r5`. E at `0x82000018` with `body=0x82000000`: uses ctr (`bdnz`), cr6, r31, r30 and CA (`addic r29,r31,-1; adde r3,r30,r29`), then the shared epilogue and `blr`. Separate function B at `0x82000060`: same frame setup, then `li r31,0x1234; li r30,5; cmpwi cr6,r4,1; li r0,3; mtctr r0; addic r0,r31,-1; b 0x82000018`. Run `xstart → B` under all-off and under each flag. r3 and memory must match. |
| T4 | Late jump table (C2) | A graph where function F has **no** `jumpTables()` entry but the bytes are `lwzx r0,r11,r0; mtctr r0; bctr` followed by a table whose entry 1 is the interior entry E. With any flag on, expect `write(true)` to fail (after Required (a)), or F to be emitted in ctx mode (after Required (b)). Today it passes silently. Keep this test as the gap's regression guard. |
| T5 | Stage B helper ABI (C6) | Fixture with the C6 caller and helpers `__savefpr_30: stfd f30,-0x10(r12); stfd f31,-0x8(r12); blr` and the matching `__restfpr_30`, plus the GPR pair. Use `MEMORY_OUT`-style checks: after the call, `[r1-0x30, r1-0x20)` holds the original f30/f31, nothing was written near `0xFFFFFFF0` or at stale `ctx.r12`, and f30/f31 survive the call. Run with `non_argument_as_local=true, non_volatile_as_local=false`. Today it should FAIL; after the fix it should be rejected or pass. Add a VMX variant with `li r11,-0x20; stvx v30,r11,r12`. |
| T6 | Gap entries (C2) | A one-off static report (or a `REXCODEGEN_WARN` in `BuildRegisterFallback`): for each function F and each entry E with `F.base < E < F.end` and E not in any block of F, list E and whether F has an edge to it. Expected for LEGO: empty, or every listed F already in `inCtx`. |
| T7 | setjmp (C8), optional | Localized function `bl setjmp; cmpwi r3,0; bne after; li r31,1; ... bl longjmp_path; after: mr r3,r31`. Expected: r3 is the r31 value from setjmp time. Compare with the all-off build. |
| T8 | Future option consumers | Add `--codegen-flag=<key>` (or `--config`) to `recompile-tests` and run the **whole** `tests/ppc` suite twice, with all options off and with each new option on, against the same `REGISTER_OUT`/`MEMORY_OUT`. For localization flags, compare only registers the active flags leave in ctx (r3-r10, r1, f1-f13, memory), because localized registers are invisible to the harness. Add asm cases for the pending rlwinm work, e.g. `instr_rlwinm_wrap.s`: (a) `rlwinm r3,r4,8,28,3` (MB>ME): REGISTER_OUT must include the upper word, which equals `rotl32(r4)`; (b) `rlwimi r3,r4,0,16,31` with `REGISTER_IN r3 0x12345678_9ABCDEF0`: the upper word of r3 is preserved; (c) `rlwnm r3,r4,r5,0,31` with r5=33: rotate by 1; (d) `rlwinm. r3,r4,0,0,0` giving 0x80000000: CR0 matches the old codegen. |

---

## (e) Header changes that force a full rebuild

- **None in this diff.**
  - `include/rex/codegen/config.h` and `include/rex/codegen/function_types.h` are tool-side only. They are included by `src/codegen/*`, `include/rex/codegen/{codegen_context,function_node,function_scanner,manifest}.h` and `project_recompiler.cpp`, and are never reached from generated TUs.
  - `include/rex/ppc/*`, `context.h`, `function.h`, `pch_h.inja` and `init_cpp.inja` are unchanged.
- The untracked `include/rex/threading_timeout.h` and `include/rex/threading_timing.h` (not Agent 9's codegen work) are included only by `src/core/threading_{win,posix}.cpp`. They cause a runtime-library rebuild only.
- **Caveat.** Flipping any of the 8 existing flags (`skip_lr`, `skip_msr`, and the six `*_as_local`) rewrites `<project>_pch.h` (`pch_h.inja:11-18`) and `init.cpp` (`init_cpp.inja:21-28`), so the first localized build is a full 1-2 h rebuild no matter what the codegen diff is. The four new keys are not in `configFlags`, so today they do not touch the PCH.

---

## (f) Questions for Agent 9

1. With localization on for LEGO, what does the INFO line `Register localization fallback: N functions keep registers in ctx (...)` report? That N, against the hot-function list, is the perf cost of the fallback.
2. For the 5 `body=` entries (`0x8307CA78`, `0x838052D8`, `0x839AAE60`, `0x82FD1520`, `0x82D41F28`) and the interior `{}` entries (for example the `0x8284A708-0x8284A7F8` and `0x8361E688-0x8361E728` runs):
   - is any reached by a computed `bctr` with no table, by a jump table found only at emission, or from code in a range gap?
   - does any expect non-ABI registers at entry? (The TOML comment at `legodimensions_config.toml:25-26` says yes, "live registers".)
3. Will you rewrite `tests/regression/emit_interior_entries.cpp:240-252` as positive checks (T2)? As it stands the regression suite fails.
4. Will `check_register_handoff` fail `write()`, or will `BuildRegisterFallback` also probe for emission-time jump tables (C2, Required (a)/(b))?
5. Will you enforce `non_argument_as_local ⇒ non_volatile_as_local`, or flush r11/r12 and always put helpers in ctx mode (C6)? Is "stage B alone" in your bench plan?
6. Should callers of `setJmpAddress`, and SEH owners when `generate_exception_handlers` is on, also join `inCtx` (C8)?
7. Has the rexglue tool been built with this diff, and did `bench/agent9/syntax-check.ps1` pass? Has an all-flags-off LEGO output diff against the pin (T1) been run?
8. Are the `src/core/threading_*` edits and the untracked `include/rex/threading_*.h` yours? They were out of scope here.
9. Will `recompile-tests` get a flags option so `tests/ppc` can cover the new options (T8)?

---

## Appendix: pre-review checklist for the pending option consumers (not in the diff yet)

- **`rlwinm_lowering`.** The work lives in `logical.cpp` and `builders/rotate_mask.h` (`bench/agent9/rlwinm/STATUS.md`).
  - MB>ME (wrap) masks must reproduce today's 64-bit upper word, which equals the `rotl32` result.
  - `rlwimi` with MB<=ME must preserve rA's upper 32 bits.
  - `rlwnm` uses `rB & 31`.
  - Record forms must keep the current CR0 compare width.
  - The rotate must have no `x << 32` UB when sh=0.
- **`flush_mode_elision`.** Compares (`fcmpu`/`fcmpo`/`vcmp*fp`), conversions (`frsp`, `fcti*`, `vcfux`/`vctsxs`) and any denormal-sensitive op depend on the mode. Only moves, loads/stores, logical ops and permutes are mode-independent. Do not carry `csrState` across labels (`function_graph.cpp:597`) or calls.
- **`cr_compare_so_zero`.** It is consistent with this SDK only because SO is written solely by `mtxer` (`system.cpp:355-357`; OE forms never set SO here). The image scan must catch every `mtspr 1` encoding, and the option needs a fresh look if host code ever writes `ctx.xer.so`.
- **`musttail_calls`.**
  - Use it only for `call; return;` pairs: `control_flow.cpp:43-44`, `context.cpp:354-355`, and the jump table at `control_flow.cpp:151,161`.
  - Never inside `SEH_TRY` (`function_graph.cpp:760-762`).
  - Never where code follows the call: the funclet sync at `context.cpp:233-236` and the setjmp path.
  - The signature and calling convention must match `DEFINE_REX_FUNC` exactly.
