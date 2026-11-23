# Agent 10: codegen cross-review of Agent 9's SDK changes (task #15, job J4)

The verdicts here are mine. I re-checked claims 1, 2, 5 and 8 against the working tree at 18:31; the line numbers below are from that check.

**Detail:** [agent10-codegen-review-draft.md](agent10-codegen-review-draft.md) is the reviewer subagent's full write-up. It has the per-transfer coverage table, concrete miscompile sequences, test designs T1-T8, and a checklist for the pending rlwinm, flush, SO and musttail options.

**Snapshots:**
- `build/agent10/review/agent9-1759.patch` is the one reviewed.
- `agent9-1811.patch` matches it byte for byte in `include/rex/codegen` and `src/codegen`. Its only additions are the `src/core/threading_*` edits and the untracked `include/rex/threading_*.h`. Those are not codegen and are out of scope here.

## Review log

| When | What was reviewed | Result |
|---|---|---|
| 18:31 | Agent 9 diff at 17:59/18:11: register-localization fallback, plus 4 inert option keys. Files: config.h, function_types.h, builder_context.h, context.cpp, control_flow.cpp, codegen_writer.cpp, config.cpp, function_graph.cpp | 4 SAFE, 2 SAFE-IF, 1 insufficient, 1 UNSAFE config combination (below) |
| 19:25 | Agent 9 diff at 18:55/18:59/19:13: rlwinm lowering (`rotate_mask.h`, logical.cpp), VMX SIMD fallbacks (vector.cpp), musttail tail calls, handoff errors that fail `write()`, rejection of `non_argument` without `non_volatile`, 5 inert keys. Tests: `emit_interior_entries.cpp` rewrite, `instr_rlw_lowering.s` | See "Review 2" at the end: rows 9-15 are 6 SAFE (one of them inert keys) and 1 SAFE-IF (musttail). Rows 1, 5 and 8 are resolved. Asks A-E. |
| 19:44 | Re-snapshot `build/agent10/review/agent9-1944.patch` | The codegen diff is byte-identical to 19:13 (same SHA-256). Only `tests/ppc/asm/seq_tailcall_musttail.s` changed (19:22). I checked its five cases by hand (r3 = 0x16, 0x108, 0x25, 100; r4 = 0x20) and they are correct. Nothing new to send. |
| 20:46 | Re-snapshot | No codegen change since 19:13. Nothing to send. |
| 21:14 | `agent9-2114.patch` (SHA-256 1EEC27C8…; recipe `git -C DimensionsRecomp\rexglue-sdk diff -- src/codegen include/rex/codegen`): the `cr_compare_so_zero` consumer | See "Review 3" at the end: row 16 SAFE at the default (inert, byte-identical), sound when ON. Notes (a)-(e), ask F. |
| 21:38 | `agent9-2137.patch` (E839FB36…, 126,326 B) + `agent9-2137-tests.patch` (05F3213E…, `emit_interior_entries.cpp` 21:23:12): flush-mode elision (B), still in flight per Agent 9's RESUME | Superseded by Review 4. Per-file deltas in `build/agent10/review/delta-2114-2137/` (floating_point.cpp, memory.cpp, vector.cpp, new `builders/flush_mode.h`). |
| 23:13-23:40 | Final batch B: `agent9-2313.patch` (EB42B92C…, 68,631 B) + `agent9-2313-tests.patch` (3EB43EAB…, 29,111 B), byte-identical again at 23:19, 23:25 and 23:28. Agent 9's `bench/agent9/review/final-2316.patch` is the same 17-file diff. Tool `build/agent9/bin/rexglue.exe` 37B32713… (23:16:17); config `build/agent9/configs/batch.toml` (B2727250…, S2.10) | See "Review 4" at the end. Rows 17-20 (flush-mode elision, the skip_lr LR-user rule, test infra and fixture D, the inert-key removal) are SAFE at the default (byte-identical) and SAFE when ON. **Row 21: `skip_lr` itself is UNSAFE for LEGO.** Host code reads `ctx.lr` to identify the caller (the gpu_native `sub_83FC49E8` pool-copy drain and XexGetProcedureAddress), and under skip_lr guest code no longer writes it. Drop `skip_lr = true` from `batch.toml`/S2.10 and regenerate before Agent 2 builds B. The exposure scan of the LEGO output is done: the guest side is clean, so every blocker is in host code. (Corrected 23:46; until then this cell covered rows 17-20 only.) |
| 00:00-00:08 | Agent 9's regenerated batch without skip_lr: config `build/agent9/configs/batch-nolr.toml` (E60EAF1C…, 23:52:08) and install tree `build/agent9/install/batch-nolr` (`SHA256SUMS.txt` 24CE1493…, 872 files) | **Condition 1 met** (details there). Compared with the 23:28 tree, only the LR statements changed, and they now equal the all-off output's in all 165,023 functions. 7 hook `extern` declarations moved with the new TU split (430 TUs). Row 21 gains 2 more `ctx.lr` decisions that Agent 9 found. The game gate proposal is at the end. |

## Verdicts (diff at 17:59, unchanged at 18:11)

| # | Change | Verdict | Why (verified evidence) |
|---|---|---|---|
| 1 | `ValidateFunctionBodies` no longer rejects `body=` plus localization flags | **SAFE-IF** #2 holds. **Breaks a test.** | `tests/regression/emit_interior_entries.cpp:240-252` still loops over all 6 flags and expects `reject()`, so `regression_interior_entries` fails. It must become positive checks (draft T2). |
| 2 | `BuildRegisterFallback` (`codegen_writer.cpp:161-234`, used at `function_graph.cpp:567-568`) | **SAFE-IF** | Covers `body=` entries, entries inside another function's blocks, and direct calls, tail calls, `jumpTables()` and `config.switchTables` into them. Misses **jump tables found only during emission** (`function_graph.cpp:571, 643-646`, `lateJumpTables`). A localized function can reach an interior entry through one of these with live registers in locals; `check_register_handoff` logs an ERROR and generation still succeeds. A computed `bctr` with no table is also uncovered. Entries in a range gap are a pre-existing hole, not new. |
| 3 | Accessors honour `!registersInCtx` (`context.cpp:47-114`) | **SAFE** | The reviewer's grep found no emitted string that hard-codes a localized register name. The one hit is the pre-existing SEH catch at `function_graph.cpp:696`, which uses `ctx.r31`. |
| 4 | Save/restore elision requires `!registersInCtx` (`context.cpp:216-217`) | **SAFE** | ctx-mode callers make real `__save*`/`__rest*` calls. All helpers are in ctx whenever any interior entry exists (`codegen_writer.cpp:214-215`). |
| 5 | `check_register_handoff` (`context.cpp:177-181`; called at `:208`, `:351`, `control_flow.cpp:149`) | **SAFE but insufficient** | It only logs: `REXCODEGEN_ERROR` maps to `REXLOG_CAT_ERROR` (`codegen_logging.h:23`) and no error count is checked before writing. It should fail `write()`, or the fallback should also probe for emission-time tables. |
| 6 | New keys `rlwinm_lowering`, `flush_mode_elision`, `cr_compare_so_zero`, `musttail_calls` | **SAFE (inert)** | Default false, nothing consumes them, and they are not in `configFlags`, so the PCH and init.cpp are unchanged. Each one needs its own review when a consumer lands; the checklist is in the draft appendix. |
| 7 | Off path (all 6 localization flags off) | **SAFE** | `BuildRegisterFallback` returns at `:164-167`, so emitted code is unchanged. Confirm with T1, the all-off LEGO output diff against the pin. |
| 8 | Config `non_argument_as_local=true` with `non_volatile_as_local=false` | **UNSAFE** (pre-existing, now reachable for LEGO) | The FPR/VMX save/restore helpers take r12/r11 implicitly (`function_scanner.cpp:133-165`). Helper calls are elided only when `nonVolatileRegistersAsLocalVariables` is set (`context.cpp:216`). Otherwise the caller writes a local `r12` and the helper reads a stale `ctx.r12` or a zero local. Fix: reject this combination, or flush r11/r12 to ctx before non-elided helper calls. |

**PPC semantics.** No hunk changes how any instruction computes CR, XER (CA/SO/OV), FPSCR, rounding, NaNs, signed or unsigned edges, byte order or memory ordering. The diff only decides where registers live (locals vs `ctx`). The risk is control transfers that cross that boundary: rows 2, 5 and 8.

## Headers that every generated unit includes

- **None changed by Agent 9's diff.** `include/rex/ppc/*`, `context.h`, `pch_h.inja` and `init_cpp.inja` are untouched, and `config.h`/`function_types.h` are used only by the codegen tool.
- Caveat: turning on any existing localization flag (or `skip_lr`/`skip_msr`) rewrites `<project>_pch.h` (`pch_h.inja:11-18`) and `init.cpp`. So the first localized build is a full rebuild whatever the diff is.

## Asks for Agent 9 (differential tests: Agent 9 owns tests/ppc and tests/regression)

1. Rewrite `emit_interior_entries.cpp:240-252` as positive checks (T2): `write(true)` succeeds; the entry, the owner and the callers have no register locals; a control function still has them; `__save*` bodies use `ctx`.
2. Make a fired `check_register_handoff` fail `write()`, or feed emission-time jump tables into `BuildRegisterFallback` (T4 guards this).
3. Reject `non_argument_as_local && !non_volatile_as_local`, or sync r11/r12 before non-elided helper calls (T5).
4. Run T1: LEGO codegen with all flags off, diffed against the pin tool's output. It must be identical.
5. Report the fallback INFO count (the perf cost of #2). Also say whether any LEGO `body=` or interior entry is reached through a computed `bctr` or a late table.
6. T8: add a codegen-flags option to `recompile-tests` so `tests/ppc` can run with each new option on. This is needed before any of the 4 new options gets a consumer.

---

## Review 2 (19:25): Agent 9's diff at 18:55, 18:59 and 19:13, plus the new tests from 19:03 and 19:05

**Inputs**
- Snapshots in `build/agent10/review/`: `agent9-1855.patch`, `agent9-1859.patch` and `agent9-1913.patch`. The 18:59 and 19:13 snapshots are line-for-line identical in `include/rex/codegen` and `src/codegen`; the 18:55→18:59 delta is `delta-1855-1859.txt`.
- Untracked files, read in full: `src/codegen/builders/rotate_mask.h` (18:40, 6407 B) and `tests/ppc/asm/instr_rlw_lowering.s` (19:05, 35 tests).
- Test diff: `tests/regression/emit_interior_entries.cpp` (19:03, +143/−14).

### Verdicts

**Row 9: `rlwinm_lowering` (default off).** Code: `rotate_mask.h`, called from `logical.cpp:281` (rlwimi), `:301` (rlwinm) and `:319` (rlwnm). **Verdict: SAFE.**
- `classify()` only accepts sh/mb/me ≤ 31 with mb ≤ me. A wrapping mask (mb > me) returns nullopt and keeps the generic 64-bit form. That fallback is required, because with a wrapping mask the 64-bit result has a non-zero high word.
- Every lowered form is a u32 expression assigned to `.u64`, i.e. zero-extended. The forms are copy, mask, shl (± mask), shr (± mask) and `__builtin_rotateleft32` (± mask). For a non-wrapping mask, each equals the generic `rotl64(x‖x, sh) & MASK(mb+32, me+32)`.
- rlwnm uses `rB.u8 & 0x1F`, which is rB[59:63].
- rlwimi keeps `rA.u64 & ~zext(mask32)`, so rA's high word survives as in the generic form.
- The lowered and the generic paths both call `emitRecordFormCompare(ctx)` on the same final value (`logical.cpp:286/296`, `306/314`, `324/333`), so CR0 does not change.
- `hexLiteral` matches the generic `0x{:X}`.
- **Test check:** I re-derived every expected value in `instr_rlw_lowering.s` with an independent model of the 64-bit ISA text (scratch `rlw_check.cpp`): **35 tests, 77 register checks, 0 mismatches**. The tests cover each lowering class, the wrap fallbacks, rA == rS (== rB) aliasing, rB garbage/32/63, and the record forms with mfcr.
- **Limitation:** recompile-tests has no way to turn the flag on (T8 is still open: no test or tool references `rlwinm_lowering`). Today the file only exercises the generic path. It becomes the differential test once T8 lands.

**Row 10: `vmx_vector_fallbacks` (default off).** SIMD bodies for vsubsws, vsrb, vsrab, vrlw, vsraw, vsrw, vpkuhus and vpkuwus (`vector.cpp:325, 918, 950, 1009, 1099, 1122, 1234, 1277`). **Verdict: SAFE.** Needs differential test B before it is turned on.
- vsubsws: overflow = `(a^b) & (a^diff)` and the saturated value is `(a>>31) ^ 0x7FFFFFFF`, selected by blendv_ps on the overflow sign.
- vsrb: a blendv ladder keyed on `slli_epi16(s, 5/6/7)`, i.e. the per-byte count bits of `s & 7`.
- vsrab: bias by `x ^ 0x80`, then a pshufb table on `s & 7`.
- vrlw: right part shifted by `(32 − sh) & 31`, so sh = 0 is exact.
- vsraw/vsrw: `b & 0x1F` in each 32-bit lane equals the scalar `u8[i*4] & 0x1F` (the LE low byte), fed to srav/srlv_epi32.
- vpkuhus/vpkuwus: `packus(min_epu(vB), min_epu(vA))`. The min clamps first, so packus's signed view is safe, and vB lands in the low x86 half, which matches the scalar `u8[15-i] = sat(vA.u16[7-i])` layout. These run only when vD ≠ vA and vD ≠ vB.
- **Pre-existing bug, not new:** the scalar vpkuhus/vpkuwus path is wrong when vD == vB, because its first loop overwrites vB's high bytes before the second loop reads them. The aliased case still takes that path.

**Row 11: `musttail_calls` (default off).** Code: `context.cpp` ~184-275, `control_flow.cpp:23` (b, bctr) and `emit_conditional_branch`. **Verdict: SAFE-IF**, on these conditions:
- **Gating:** off for SEH-scoped bodies and for functions that call setjmp (`calls_setjmp` scans b/bc targets, relative and absolute). Only the plain `\tNAME(ctx, base);\n` line with an identifier NAME is rewritten.
- **bctr:** `return;` moved into the not-in-graph `REX_FATAL` branch. The in-graph branch goes through `emit_tail_call_line`, which prints the call plus `return;` when the flag is off, so the off-path text is unchanged.
- **Condition (a):** keep it off in Tracy/profiling builds. A zone object with a destructor is live at the call, and clang rejects `musttail` there. That's a compile error, not a miscompile.
- **Condition (b):** every REX_FUNC and import thunk must have the identical signature `(PPCContext&, uint8_t*)`. Otherwise the build fails to compile.
- **Condition (c):** no mid-asm hook may keep a pointer to a caller local across the call. Clang does not diagnose that.
- **Tests:** test C.

**Row 12: handoff errors.** Code: `function_types.h`, `context.cpp` `check_register_handoff`, `codegen_writer.cpp` ~486-516. **Verdict: SAFE. Resolves row 5 and ask 2.**
- A fired handoff check is now counted, and `write()` fails before flushing anything.
- So the late-jump-table and computed-`bctr` gaps from row 2 now fail codegen instead of emitting code with live registers stranded in locals.
- **Still untested:** test D.

**Row 13: new hard error for `non_argument_as_local` without `non_volatile_as_local`.** Code: `codegen_writer.cpp` ~383-392; test `reject(..., "localization-non-argument-only")`. **Verdict: SAFE. Resolves row 8 and ask 3.**
- The save/restore helpers read r11/r12 from ctx, so this combination was unsafe.
- Inert for LEGO: `DimensionsRecomp/rexlego/legodimensions_config.toml` sets no `*_as_local` key.
- Any other project that used this combination now fails codegen instead of miscompiling.

**Row 14: `emit_interior_entries.cpp` rewrite (19:03).** **Verdict: SAFE. Resolves row 1 and ask 1.** Row 1 becomes SAFE.
- It covers 7 localization sets: ctr, xer, reserved, cr, non-volatile, non-argument+non-volatile, and all six. For each one:
  - `write()` succeeds;
  - the entry, owner and partner functions (`sub_82000000/18/40/48`) declare no register local;
  - a control function without `body=` does get the expected locals (`ctr`, `xer`, `reserved`, `cr0`, `r0`, `r31`), which proves the flag took effect.
- The probe puts `lwarx r0,0,r31` in the shared block, so reserved, r0 and r31 would otherwise be localized there.
- Rejections go from 21 to 16 (6 removed, 1 added).
- **Limits:** it checks declarations, not uses, which is adequate because an undeclared register fails to compile. It does not cover a late jump table (test D).

**Row 15: `flush_mode_elision`, `cr_compare_so_zero`, `cr_bit_liveness`, `lazy_xer_ca`, `flush_mode_dataflow`.** **Verdict: SAFE (inert).**
- They are only parsed (`config.cpp:121-130`), with no consumer yet.
- Each needs its own review when a consumer lands. Agent 9 owns REX_SET_FLUSH_MODE elision.

### Headers that every generated unit includes (Review 2)
- Agent 9's diff still changes **none**. Everything is in the codegen tool.
- None of the new keys is in `configFlags` (`codegen_writer.cpp:287`), so the PCH and init.cpp don't change.
- Turning on `rlwinm_lowering`, `vmx_vector_fallbacks` or `musttail_calls` rewrites the generated .cpp text, so it means a full regen and rebuild.
- My own task-9 edits to `include/rex/ppc/intrinsics.h` and `include/rex/math.h` do reach every generated TU. They are tracked in `agent10-helpers.md`, "Session 2".

### Asks for Agent 9 (Review 2)
- **A. T8, still open:** a codegen-flags option for recompile-tests, so `tests/ppc` can run with `rlwinm_lowering`, `vmx_vector_fallbacks` and `musttail_calls` on. Until then, `instr_rlw_lowering.s` only exercises the generic path.
- **B. VMX fallbacks:** run each of the 8 ops with the flag on vs off over ≥ 10^6 random vector pairs plus edge cases:
  - counts 0 and max;
  - INT_MIN/INT_MAX for vsubsws;
  - the 0xFF/0x100 and 0xFFFF/0x10000 boundaries for the packs;
  - vD == vA and vD == vB, which must take the scalar path.
- **C. musttail:** compile every LEGO generated TU with `musttail_calls = true` (any violation is a hard compile error). Add a tail-chain depth test, e.g. 10^6 mutual `b`/`bctr` tail calls on a small stack.
- **D. Handoff:** a fixture where a late (emission-time) jump table reaches an interior entry from a localized function. `write()` must fail.
- **E. T1, still open:** LEGO codegen with every new option off must be byte-identical to the pin tool's output.

---

## Review 3 (21:47): the `cr_compare_so_zero` consumer, Agent 9's diff at 21:14

**Inputs**
- `build/agent10/review/agent9-2114.patch` (SHA-256 1EEC27C8…). Recipe: `git -C DimensionsRecomp\rexglue-sdk diff -- src/codegen include/rex/codegen` (no tests).
- Agent 9's T1 result: the all-off LEGO output matches the pin (883 of 886 files identical; the other 3 are `codegen.d` and stamps).

**Row 16: `cr_compare_so_zero` (default off). Verdict: SAFE at the default (inert, byte-identical). Sound when ON; turn it on only after ask F passes.**
- **Off path.** `PrepareEmitAnalyses` returns at `codegen_writer.cpp:338` when the option is off, so `xerWriters` stays null and `compareSoZero` is false for every body (`function_graph.cpp:571-573`). T1 confirms the byte-identity.
- **The rule when ON** (`function_graph.cpp:571-573`): a body compares with SO = 0 if it is not an SO writer **and** either its XER is a local (`xer_as_local` and not forced into ctx) or no body that keeps XER in ctx writes SO (`ctxXerWritten == false`). LEGO sets no `*_as_local` key, so XER is in ctx everywhere: the option is all-or-nothing for LEGO, and it does nothing if any LEGO body contains an `mtxer` or an `x`-register hook. Agent 9's INFO line reports the counts.
- **Why that is sound:**
  - The writer scan matches `mtspr XER, rS` for any rS (`kMtxerMask 0xFC1FFFFF`, `kMtxer 0x7C0103A6`, `codegen_writer.cpp:347-348`). It also counts mid-asm hooks that name an `x…` register.
  - It walks the same `blocks()` as emission (`codegen_writer.cpp:358-361` vs `function_graph.cpp:588`), following `body=` owners.
  - The function set is the whole graph minus imports and rexcrt (`codegen_writer.cpp:468-474`, `521-526`). Those are host code. A grep finds no `xer.so` writes in rexlego or the runtime except the save/restore copies at `xthread.cpp:1275` and `:1386`, which only the (mostly unimplemented) serialization Save/Restore uses (`:1414`, `:1457`).
  - The only builder that writes SO is mtxer (`system.cpp:356`). The OE forms set only `.ca`: the builders don't model OV/SO (pre-existing).
  - Hooks get registers by name only. `'x'` maps to `xer()` (`context.cpp:540-549`), and no hook takes the whole ctx, which matches the scan (`codegen_writer.cpp:342-346`).
  - A local XER is zero-initialised (`PPCXERRegister xer{}`, `function_graph.cpp:733`) and is never loaded from or stored to ctx.
  - A `{}` argument for `const XERRegister&` (`context.h:89`) is a value-initialised temporary, so SO = 0.
  - `stwcx.` already sets `cr0.so = 0` (`helpers.h:321-324`), so it is consistent.
  - Every context that the runtime or the generated code creates is zeroed: `ThreadState::context_storage_{}` (`thread_state.h:43`), `newCtx{}` (`function.h:464`), the `ImportFunction` `ctx{}` (`hook.h:152`) and the generated `PPCContext env{}` (`function_graph.cpp:758`).

**Notes for Agent 9 (none blocking)**
- **(a)** The comment at `codegen_writer.cpp:320-327` overstates the case. `rex::CallFrame` (`hook.h:90-94`) is documented as "NOT zero-initialized", so its `ctx.xer.so` is indeterminate. With the option ON, a callee that keeps XER in ctx compares with SO = 0 instead of stack garbage. That is not a regression (reading it was UB before), but the comment should say so, or `CallFrame` should value-initialise `xer`.
- **(b)** Only the helper-based compares use `compareXer`: `emitRecordFormCompare`, `emitCompareRegister`, `emitCompareImmediate`, andi. and andis. The other compare sites still read `ctx.xer()`. That is correct, just a missed optimisation.
- **(c)** Nothing wires up `tests/ppc/opt_config.toml`: `tests/ppc/CMakeLists.txt` is from 11:04:45, and no file mentions `opt_config` or `ppc_tests_opt`. Agent 9's RESUME lists the tests/ppc default-vs-opt run (A) as in flight.
- **(d)** Headers: `function_types.h` is used only by the codegen tool, and no generated-code header changes. The key is not in `configFlags`, so the PCH and init.cpp don't change. Turning it on means a regen and a full rebuild.
- **(e)** Maintenance: if a builder ever models OV/SO for the OE forms (addo, subfo, mullwo, divwo, …), the writer scan must count them too. Otherwise the option becomes unsound silently.

**Ask F (before a game build turns it on):** an ON-mode tests/ppc run (T8, `--config`) that includes an SO writer: `mtxer` with SO = 1, then record-form compares (`cmpw`, `cmpwi`, `andi.`) in the same function and in a callee. Both must still see SO = 1, which checks the all-or-nothing switch. Also the crso/crsoA variant diff (`build/agent9/chain.ps1`).

---

## Review 4 (23:45): flush-mode elision, the skip_lr LR-user rule and the test infrastructure (Agent 9's final batch B), plus skip_lr for LEGO

**Summary**
- **Default output:** byte-identical for everything in this review (rows 17-20).
- **When ON:**
  - `flush_mode_elision` is SAFE (row 17).
  - The new LR-user rule is correct. It only narrows upstream skip_lr's risk (row 18).
  - The test changes are SAFE (row 19).
- **`skip_lr` itself is UNSAFE for LEGO (row 21).** Host code reads `ctx.lr` to find out who called it, and under skip_lr no caller writes `ctx.lr`. The other 9 keys don't touch LR.
  - Resolved at 00:08: Agent 9 dropped it from the batch (`batch-nolr`), and my diff shows that only the LR statements changed (condition 1).

**Inputs**
- Live diff (read-only):
  - `build/agent10/review/agent9-2313.patch` (SHA-256 EB42B92C…, 68,631 B; `git diff -- src/codegen include/rex/codegen`);
  - `agent9-2313-tests.patch` (3EB43EAB…, 29,111 B; `git diff -- src/rexglue/commands/test_recompiler.cpp tests/regression/emit_interior_entries.cpp tests/ppc`).
  - The re-snapshots at 23:19, 23:25 and 23:28 (`agent9-chk3.patch`, `agent9-chk3-tests.patch`) are byte-identical. No codegen source has changed since 22:12:41, so the tool built at 23:16:17 (37B32713…) comes from this source. I did not check the binary itself.
- Agent 9's `bench/agent9/review/final-2316.patch` (10B39E23…, 99,827 B) equals those two files concatenated, except that it has a UTF-8 BOM and CRLF line endings (checked with `build/agent10/review/r4/cmp_final.py`).
  - It contains only the 17 tracked files, none of the 6 untracked ones.
  - `git apply` fails on it as-is.
- Untracked files (SHA-256 prefix, size, time):
  - `src/codegen/builders/flush_mode.h` B1A8F81B (1,192 B, 21:25:19);
  - `rotate_mask.h` 28559878 (6,407 B, 18:40:26; Review 2);
  - `tests/ppc/opt_config.toml` C74CD990 (507 B, 21:59:09);
  - `tests/ppc/asm/instr_cr_so_fold.s` F2413015 (1,904 B, 22:04:58);
  - `instr_rlw_lowering.s` 4625B4FC (11,407 B, 19:05:28; Review 2);
  - `seq_tailcall_musttail.s` 488CC191 (697 B, 19:22:01).
- Interdiffs since Review 3, both read in full: `build/agent10/review/r4/interdiff-2114-2137.patch` (30,623 B) and `r4/interdiff-2137-now.patch` (46,576 B).
- Agent 9's harness notes: `bench/agent9/flush/README.md` (4F74E3A8…).
- My scans of the LEGO output: `build/agent10/review/r4/skiplr-scan-off3.txt` and `skiplr-scan2.txt` (scripts `skiplr_scan.py` and `skiplr_scan2.py`).

**Row 17: `flush_mode_elision` (default off). Verdict: SAFE at the default (byte-identical by construction). SAFE when ON.**
- **Code:** `builders/flush_mode.h:20-26`, `emitFlushModeUnlessIndependent`.
  - With the flag set, it emits nothing and leaves `ctx.csrState` unchanged.
  - Otherwise it calls `emit_set_flush_mode` exactly as before.
  - Default false (`config.h:106`); parsed at `config.cpp:121-122`; not in `configFlags` (`codegen_writer.cpp:288`).
  - Only floating_point.cpp, memory.cpp and vector.cpp include it.
- **23 call sites**, matching the README and `baseline_scan.txt`:
  - floating_point.cpp (7): fabs, fnabs, fneg, fmr, fcfid, fctidz, fctiwz;
  - memory.cpp (9): lfd, lfdx, lfdu, lfdux, stfd, stfdx, stfdu, stfdux, stfiwx;
  - vector.cpp (7): vrfin, vrfiz, vctsxs, vctuxs, vcfsx, vcfux, vpkd3d128 (`:1335`).
- **Why skipping the switch is correct.** The switch changes only FTZ/DAZ, never the rounding mode. None of the 23 ops gives a different result under either FTZ/DAZ setting:
  - fabs/fnabs/fneg/fmr, the loads and stores, and stfiwx are bitwise or integer moves.
  - fcfid (cvtsi2sd) never produces a denormal. vcfsx (cvtdq2ps × 2^-k, k ≤ 31) gives 0 or a value ≥ 2^-31. vcfux is integer ops plus cvtepi32_ps and blendv.
  - fctidz/fctiwz, vctsxs (`intrinsics.h:179-188`) and vctuxs (`:195-204`) truncate. A denormal input gives 0 whether or not DAZ flushes it. Scaling by 2^k (k ≤ 31) keeps it below 1, and the range compares are against normal constants (2^31, 2^32).
  - vrfin/vrfiz use roundps with an explicit immediate, so a denormal gives ±0 either way.
  - vpkd3d128 (`vector.cpp:1332-1530`):
    - type 0 selects against 3.0f and 0x404000FF, so a denormal is never the value it returns;
    - types 1 and 4 are integer only;
    - type 2 clamps against the kPack2101010 constants (≈ 3.0);
    - types 3 and 5 extract f16 bits, with NaN and > 65504 checks;
    - type 6 is an `int32_t(f32)` truncation.
- **`ctx.csrState` stays exact when ON,** because the elided ops never touch MXCSR. The next mode-dependent op still emits the switch it needs. Calls, returns, hooks, interior entries, exception paths and imports are handled exactly as before; the option only removes switches in front of ops that don't depend on the mode.
- `code_emitter.h/.cpp` `CsrState`/`ensureCsrState` is a separate, unused abstraction (defined only at `code_emitter.cpp:15`, no callers).
- **Harness** (`bench/agent9/flush/README.md`):
  - 16 MXCSR modes per case; 368,252,256 evaluations;
  - exhaustive exponent-0 sweeps (vpkd3d128 types 0, 2, 3, 5 and 6 at rotations 0-3);
  - 5 controls detected; RESULT PASS.
  - Replaying the baseline reproduces all 136,802 switch lines. With the flag on there are 106,248 (−22.3%).
- **Residuals (none blocking):**
  - Host code (imports, MMIO handlers, hooks, CRT `log2f`) may now run in the other flush mode for longer. That could already happen before, depending on the path.
  - The optional `tests/ppc/asm/instr_flush_independent.s` was not written.
  - vpkd3d128 type 4, shift 3 writes `u16[8..9]` out of bounds. This is pre-existing (Agent 9 S2.9), and the harness excludes it.

**Row 18: the skip_lr LR-user rule (`codegen_writer.cpp:350-388`). Verdict: SAFE at the default (byte-identical). SAFE when ON as a change, because it only narrows upstream skip_lr's risk. Whether LEGO may use skip_lr at all is row 21.**
- **Off path.**
  - The scan runs only `if (config.skipLr)`, so `lrUsers` stays null and `keepLr` stays false.
  - `trackLr()` is `!skipLr || keepLr` (`context.cpp:41-42`), so it is true.
  - All 5 LR sites test `trackLr()`: build_bl (`control_flow.cpp:67`), blrl (`:104`), bctrl (`:190`), mflr (`system.cpp:245`) and mtlr (`:313`).
  - The live game TOML sets no skip_lr. Only `batch.toml` and `tests/ppc/opt_config.toml` do.
- **When ON**, a body keeps every LR write and read if it contains either of these:
  - a bclrl (`word & 0xFC0007FF == 0x4C000021`: opcode 19, XO 16, LK 1, any BO/BI);
  - a `bl` (AA 0, LK 1) whose `classifyTarget(target, pc, true)` is InternalLabel. Those are the arguments build_bl uses (`control_flow.cpp:72`), so the scan and the emitter agree on which `bl` becomes a local goto. The displacement decode `(int32_t(word << 6) >> 6) & ~3` is correct.
- **Scan scope.**
  - The scan walks `bodyOf(fn)->blocks()`, the same blocks that emission uses.
  - Results are keyed by `fn->base()` and looked up with `entry.base()` (`function_graph.cpp:577`).
  - `PrepareEmitAnalyses` runs at `codegen_writer.cpp:584` (write) and at `test_recompiler.cpp:396`.
- **Not covered, but not specific to skip_lr:**
  - `bla` can't reach image labels.
  - `bcl`/`bcla` (the `bcl 20,31,$+4` PIC idiom), conditional bclrl and conditional bcctrl have no builder (`instruction_dispatch.cpp:133-162`). They emit `REX_UNIMPLEMENTED` (`:657-661`) in both modes.
- **On the real LEGO output,** the rule finds exactly one LR user, `sub_83E5C830`. That matches the tool's INFO count of 1.
  - It looks like the CRT's `_CallSettingFrame`: `mtlr r3; blrl` calls a funclet whose address comes back from `sub_83E5B5B0`, an `_NLG_Notify`-style function that only stores r3-r5.
  - Upstream skip_lr would have dropped its `mtlr r3`, and `blrl` would have called through a stale LR. The rule keeps it. In the batch output this is the only function that still mentions `ctx.lr`, with the same 7 lines as the off output.

**Row 19: test infrastructure and fixture D. Verdict: SAFE (test-only; no change to game output).**
- **`src/codegen/test_support.cpp`:** only the tests call `AnalyzeTestBinary`. A `b`/`bc` to another test's entry now adds a tail-call edge. This fixes the 0xC0000409 crashes in seq.test_tailcall_chain and cond_taken.
- **`src/rexglue/commands/test_recompiler.cpp`:**
  - `--config` presets `filePath`/`outDirectoryPath`, then `Load`s the TOML. Each binary gets a copy of `options`. With no `--config`, the defaults equal the old code.
  - `PrepareEmitAnalyses` and the handoff count now run. They are inert at the defaults.
  - Under `cr_as_local`, `REGISTER_OUT cr…` expectations are dropped with a WARN.
  - `ParseTestSpecs`: the `pending`/`testLabel` logic fixes the label that was swallowed after an unannotated test (`test_tailcall_uncond`; 1496 → 1497 tests), and the label right after the outputs. A `#` comment inside a body still ends the scan, as before.
- **Fixture D** (`tests/regression/emit_interior_entries.cpp`):
  - 7 localization fallback cases.
  - 5 switch-table cases, including a precision case: a table that reaches no interior entry stays localized.
  - The handoff safety net, driven with an incomplete fallback: 1 error, then 0 once the dispatcher is in ctx. This answers Review 2 ask D.
  - 2 skip_lr LR cases. I decoded their words by hand: 0x7D6803A6 `mtlr r11`, 0x4E800021 `blrl`, 0x48000005 `bl $+4`, 0x7C6802A6 `mflr r3`, 0x7D8802A6 `mflr r12`, 0x4BFFFFDD `bl −0x24`, 0x7D8803A6 `mtlr r12`. The blrl and PIC bodies must emit the same text as the no-skip control, and the saver must have no `ctx.lr`.
  - 16 rejection cases.
  - Agent 9 reports run7 PASS on the final tool.
- **Not checked by hand:** the expected values in test F (`instr_cr_so_fold.s`). The T8 crso run covers it.

**Row 20: inert keys removed, and the comment fix. Verdict: SAFE.**
- `cr_bit_liveness`, `lazy_xer_ca` and `flush_mode_dataflow` were removed from `config.h`/`config.cpp` at 22:12. They had no consumer, and no TOML (live, batch or opt) sets them.
- The `codegen_writer.cpp` comment now documents the `rex::CallFrame` caveat. That resolves Review 3 note (a).

**Row 21: skip_lr for LEGO. The option is pre-existing; the batch turns it on for the first time. Verdict: UNSAFE for LEGO. Drop it from the batch.**
- **Why `ctx.lr` goes stale.** Under skip_lr, `bl` emits no `ctx.lr = <return address>` (`control_flow.cpp:67`) in any body that isn't an LR user. So a host function entered through a guest `bl` sees whatever value was last stored:
  - 0xBCBCBCBC inside `FunctionDispatcher::Execute` (`function_dispatcher.cpp:124-129`);
  - 0 in a fresh context;
  - or a value some host code wrote last.
- **Host code that makes decisions based on `ctx.lr`:**
  - **`rexlego/src/gpu_native/hooks_buffer.cpp:388-389` → `:268-276`.** The `sub_83FC49E8` hook calls `NativeWorkerDrainCapture` to drain the native worker's queued pool copies before XGOffsetResource rewrites a placement header. It does this only when the caller is 0x83F9B660. Under skip_lr the drain never runs, so the queued native path gets an ordering race against the header change.
  - **`rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_modules.cpp:155-177`.**
    - XexGetProcedureAddress passes `ctx.lr` as `caller_address`, and the thunk module is chosen from it (`kernel_module.cpp:55-71`, `user_module.cpp:239-251`).
    - With 0xBCBCBCBC, `AllocateThunk` fails ("not in any registered module", `function_dispatcher.cpp:334-339`), so a function export resolves to 0.
    - LEGO calls it at 3 sites: `sub_83FA60E8` (`off3` `legodimensions_recomp.68.cpp:34611`), and two version-gated lookups of ordinals 80 and 36 right after `XexGetModuleHandle` (`.232.cpp:35077`, `.262.cpp:35153`). All three check the status, so the likely effect is an optional feature that silently goes missing.
  - **`rexlego/src/native_slot_growth.cpp:63, 76`** (Agent 9 found these two at 00:02; I had missed them). The native slot heap's `Grow` and `Release` thunks return r3 = 0 unless `ctx.lr` is 0x82A33FC4 or 0x82A3B88C. The thunks are made with `AllocateThunk` (:86) and published in the provider vtable (:88-91). Under skip_lr the slot heap would never grow or release a region.
  - **`rexlego/src/settings_native_hooks.cpp:174`.** The `sub_839C4D08` hook draws the extra pause-menu Options rows only when `ctx.lr` is 0x839D11B0, the TU23 call site for the final Back row. Under skip_lr those rows would silently disappear.
- **Diagnostics that would only log wrong or missing values:**
  - `hooks_buffer.cpp:309-310, 326, 367, 400-402`;
  - `hooks_state.cpp:257` (the texture-fetch history caller);
  - `crash_reporter.h:77-79, 96` (the extra `0x82EBF270` dump would never fire);
  - `name_trace.cpp:79`; `draw.cpp:5748`;
  - `console_commands.cpp:947` (the hang fingerprint loses LR);
  - `xboxkrnl_rtl.cpp:524, 622, 655`.
  - `RtlCaptureContext` and `RtlUnwind` are stubs (`xboxkrnl_rtl.cpp:815-822`), so nothing unwinds through saved-LR slots.
- **The guest code itself is fine with skip_lr** (`skiplr-scan-off3.txt`, the all-off output):
  - 128,920 `mflr` in 165,023 functions.
  - 128,913 go into r12. Every one is either stored to an r1 slot (93,931, of which 93,878 at -8(r1)) or passed to `__savegprlr_N` (34,982).
  - 2 go into r0 and are stored.
  - 4 go into r31 and are only moved back with `mtlr r31`: `sub_83E562D0`, `sub_83E5C970`, `sub_83E5CA1C` and `sub_83E5CA40`.
  - 1 goes into r7, in the LR user `sub_83E5C830` (row 18).
  - 0 `mtlr` → `mflr` scratch uses.
  - So the only blockers are on the host side.
  - Agent 9's independent guest scan (`build/agent9/lrscan.py` → `build/agent9/diff/batch/lrscan.tsv`, S2.8) agrees:
    - It also counts 128,920 `mflr`.
    - Its one flag, the setjmp `sub_83E49CA0`, is no regression. The function saves LR into the jmp_buf, only a longjmp reads it, and the pin can't longjmp either. My scan lists it only among the 47 late `mflr` (into r0, then stored).
    - Neither guest scan can see the host readers above.
- **Options:**
  - (a) Leave skip_lr off. Recommended: it saves only one store per call, plus an LR copy per prologue and epilogue.
  - (b) Turn it on only after the owners remove all four `ctx.lr` decisions above: the gpu_native hook (e.g. identify the 0x83F9B65C call site with a mid-asm hook), XexGetProcedureAddress, the slot-heap thunks and the pause-menu hook.

**Headers that every generated unit includes (Review 4)**
- Still none changed. `flush_mode.h` is a codegen-tool header.
- No new `configFlags` entry. `skip_lr` is already there (`codegen_writer.cpp:289`), so dropping it from the batch changes `<project>_pch.h` and `init.cpp` back.

**Conditions before a game build turns the batch on** (status at 00:08)
1. **Met (00:08):** Agent 9 took `skip_lr = true` out and regenerated (`batch-nolr`, 23:53). Agent 9's handoff gate: 0 "Code generation blocked", 0 handoff errors. My check uses `build/agent10/review/r5/lrdiff.py`; the report is `r5/lrdiff-report.txt` (82D2978A…).
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
2. **Met:** T8 on tool 37B32713 (23:30), 1515 tests per config:
   - default 1514/1515 and crso 1514/1515;
   - opt 1513/1514, with test F's `test_call` excluded.
   - The one failure, `vupkd3d128.test_short2_3`, is the same in all three configs and its generated code is identical: a pre-existing emitter gap (S2.9).
   - Nice to have: an extra opt run without skip_lr, which would match the corrected game keys exactly.
3. **Met:** T1 `off4` with the final tool: 883/886 files equal the pin. The other 3 are `codegen.d` (−28 B) and 2 stamps, as for off3.
4. **First pass met:** heavy TUs 304, 233 and 52 compile at game flags with `musttail_calls` on (`bench/agent9/musttail/heavy_batch.txt`; `.obj` 88% and `.text` 84% of baseline). Agent 9's CPU-time follow-up didn't run (paused at 23:51), so HEAVYCPU and HEAVYTIME come from the first pass (`agent9-codegen.md:11`).
5. **Met:** fixture D run7 PASS.
6. **Open:** the game gate (Agent 8) on the native GPU build. My proposal for what it checks is in the next section.

**Optional ask:** `tests/ppc/asm/instr_flush_independent.s`, running the 23 ops on denormal inputs in both modes.

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

## B game gate on devoffB (OFF build): adapted pass list (02:40, for Agents 1, 3 and 8)

**Why it changes.** Tonight's B is an OFF build: `build/agent2/devoffB-bin` = S2 snap1 + the `install/batch-nolr` codegen (SHA256SUMS 24CE1493…), NATIVE_GPU=OFF. The baseline is `build/agent2/devoff2-bin`: the same S2 sources with the S1 codegen, so the codegen options are still the only difference. Agent 1 agreed that the native-hook part of the gate waits for a native B build, which isn't on tonight's plan.

**What OFF can and can't test** (checked against `rexlego/CMakeLists.txt:61-141` and the sources)
- **Deferred to a native B** (not compiled in OFF, or empty there):
  - `gpu_native/*`: the placement-buffer relocation (lr=83F9B660) and the `sub_83FC49E8` drain, the CPU pool-copy callers and the pool-copy contract lines.
  - The files compiled only with `LEGODIMENSIONS_NATIVE_GPU`:
    - `settings_native_hooks.cpp`: the `sub_839C4D08` pause rows, LR 0x839D11B0;
    - `native_slot_growth.cpp`: the LR-gated Grow/Release at 0x82A33FC4/0x82A3B88C, and "Native slot heap: registered/extended";
    - `native_skin_diagnostics.cpp`.
  - The five `NativeCelShading*` mid-asm hooks: their bodies are `#ifdef`'d, so they're empty in OFF.
- **Covered in OFF:**
  - The SDK's `XexGetProcedureAddress` module choice by `ctx.lr` (`xboxkrnl_modules.cpp:155-177`, the 3 LEGO lookups). The fail line is "not in any registered module".
  - `crash_guards.cpp`:
    - the mid-asm hooks `MissingAdventureTimeLookupNode` (0x83532E00) and `RepairDialogueLockReleaseOperand` (0x82E2C1B0);
    - the hand-written bodies `sub_83C01C08` (achievements list) and `sub_82A35B90` (Quit to Vorton → Quit Game). They set `ctx.lr`/r12 and call generated code and `__savegprlr`/`__restgprlr`. Both log "crash guard: …" when they skip a bad entry.
  - The other hand-written ctx hooks, which are built in OFF too: native_lock_elide (7 sites), native_constants (`sub_82B7ABF0`), native_markers (sets `ctx.lr`), native_saverest, native_memops, native_atomics.
  - Whole-game numerics under `flush_mode_elision`, `vmx_vector_fallbacks` and `rlwinm_lowering`; `musttail` stack depth; the `cr_compare_so_zero` residual (`sub_83E5C88C`).

**Setup**
- Two runs through Agent 8's slot, functional only: devoff2 first, then devoffB, both finished before 08:30. Both use the same save, toml, route script and harness flags.
- The 0013 matrix runs can't be the route baseline. They had no input, so they show only boot and title/attract.
- Route: Agent 3's virtual pad (`harness/run-game.ps1 -InputScript <route>`, which adds `--input_backend=xinput`), with the same script for both builds.
- Keep the harness defaults: `--native_settings_load=false`, `--audio_mute=true`, `--pause_when_unfocused=false`, `--discord_rpc=false`. Audio is muted and nobody is listening, so the clean-audio check moves to the user's window 4.
- Leave `LEGO_NATIVE_MEMOPS_VALIDATE` unset. Perf CSV on, for information only.

**Route.** Each step reaches host code that reads `ctx` state.
1. Boot, the title screen, load the save: the 3 export lookups.
2. A level with streaming and some combat: numerics, `musttail` depth, the lock-elision, atomics and memops hooks.
3. Pause, open Options, scroll to the last row, back out and unpause. OFF has no extra native rows, so the menu must match devoff2's.
4. A dialogue or cutscene (`RepairDialogueLockReleaseOperand`), and an Adventure Time area if the save reaches one (`MissingAdventureTimeLookupNode`).
5. Leave the level and load another.
6. Save. Open the achievements list if the route can reach it (`sub_83C01C08`). Then Quit to Vorton → Quit Game (`sub_82A35B90`), and WM_CLOSE if the game is still up.
   - Toy-pad add and remove: **not covered** tonight. Agent 1 (02:47): there are no generated tags without the user. The verdict lists it as not covered.

**If the harness can't drive the menus:** boot both builds, leave them on title/attract as long as the 0013 runs (~30 s after a ~7 s boot), then WM_CLOSE. Report that as "boot gate only", not a B pass.

**Fail if any of these happen in devoffB**
- A crash, a hang or watchdog fingerprint, or 0xC0000409, 0xC0000005 or 0xC00000FD.
- Any "not in any registered module" line.
- More unimplemented-instruction lines than devoff2 on the same route.
- logdiff shows any of these:
  - a NEW warning or error key that the route doesn't explain;
  - a MORE key;
  - a marker FLAG: a fail marker above devoff2's count, or no "Title terminated; hard-exiting process." line.
- A new kind of "crash guard:" line, or many more of a known kind than in devoff2.

**Must match devoff2**
- The boot markers, in order:
  - "Startup: overlays ready" through "constructing the runtime";
  - "Function table initialized for module: code=82620000-84113BAC";
  - "XEX patch applied successfully … new version: 0.0.23.3";
  - the Toypad lines.
- logdiff GONE: empty, apart from lines the route explains.
- The exit:
  - WM_CLOSE gives "Window closing, shutting down..." → "Execution complete" → "Title terminated; hard-exiting process.", and devoff2 exits 0 within ~1 s.
  - Quit Game goes through the CRT `exit()` that #27 replaces only in S3, so judge it against devoff2's run, not against exit code 0.
- Screenshots at 4 fixed points (title, level spawn, pause menu, a cutscene frame) look the same, if the route script can take them.
- Perf CSV: information only.

**Tool.** `python build\agent10\bgate\logdiff.py --base "<devoff2 run dir>" --cand "<devoffB run dir>"` (read-only). I self-tested it on the 0013 matrix (`build/agent10/bgate/selftest-0013-v2.txt`), with the baseline-bin base runs as the baseline:
- the devoff2 d0/d11 runs: 0 NEW, 0 MORE, 0 GONE, 0 flags;
- the native2 n0 runs: 5 NEW "Native GPU:" warning keys and 5 GONE xenos startup lines per log, so the tool catches a real build difference.
- Total warning counts vary between runs (devoff2 d11-r1 has 6, the others 40), so the gate compares message keys, not totals.
- Fix at 02:36: the 'fatal' marker had matched the normal exit line in every log. That line is now counted as clean-exit instead.

**Static check (02:45): PASS.**
- Agent 9's `build/agent9/mapcmp.py` (log `build/agent9/logs/mapcmp-AB.txt`):
  - the devoffB and devoff2 maps have the same 164,786 sub_ functions and `__imp__` aliases, and the same 27 hooked aliases;
  - .text is 159.3 → 142.6 MB (−10.52%);
  - B's 19 compiler warnings are snap1's 19, all `-Wdeprecated-declarations` in host code, none in a generated unit.
- My cross-check (`build/agent10/bgate/hookcheck.py` → `hookcheck-AB-0245.txt`) agrees:
  - the sub_ and `__imp__sub_` sets are equal;
  - the pass-list hook names appear the same number of times in both maps: the 2 crash-guard mid-asm hooks, the 5 `NativeCelShading*`, sub_83C01C08, sub_82A35B90, sub_82B7ABF0, sub_83E5C88C, `__savegprlr`/`__restgprlr`.
- Agent 9's rollback builds (rb1-nolocal, rb2-nomusttail; `build/agent9/repin/`) are for use only after a gate FAIL and Agent 1's GO.

**Boot level (02:59): PASS.** Agent 8's 120 s cold boot `build/agent8/runs/0247-devoffB` (exit 0, WM_CLOSE, no dialogs, no WER, 0 not-responding samples) was compared against two references:
- devoff2's cold boot, `matrix/20261122-0013/runs/0013-cold-d0`;
- devoff3's cold boot, `runs/0254-devoff3`.

Result (`build/agent10/bgate/boot-B-0300.txt`):
- all three logs: info=42, warning=40, no fail markers, clean-exit=1;
- 0 NEW, 0 MORE, 0 GONE, 0 flags.

This was the "boot gate only" fallback in case the route couldn't run before 08:30. The route ran at 03:01-03:26 (below).

**Route level (03:15-03:30): PASS for the front end, partial coverage.** The runs used Agent 3's harness through Agent 8's slot (FUNCTIONAL ONLY).
- **Covered:** boot, the title screen, the front-end menus and, in the tie-break only, ~70 s of the no-input attract sequence.
- **Not covered:** route steps 2-6 (level, pause/options, cutscene, level change, save/achievements/Quit Game) and the toy pad.

*Pair 1.* Route `harness/routes/b-gate-menus.txt` (CF803C22…, 37 steps). Runs:
- A = devoff2, `build/agent3/runs/20261122-030511-bgate-a`;
- B = devoffB, `…/20261122-030752-bgate-b`;
- a devoff2 dry run, `…/20261122-030135-bgate-dry`.

Results:
- **Fail items:** all clear in both.
  - Exit 0 via WM_CLOSE (A 3.1 s, B 0.83 s), with the exit lines in order.
  - 0 errors, 0 critical, 0 MISSING-FUNCTION, and 0 not-in-module, watchdog, crash-guard or unimplemented lines.
  - No WER reports or dumps; 37/37 steps.
- **logdiff** (`bgate/route-B-0315.txt`): NEW 0, MORE 0, flags 0, info 44 in both. GONE is 4 Toypad challenge-byte keys; the bytes are random in every run.
- **Marks 1-12 match** (Agent 3): first-frame 218/222, title 226/1022, after-start 226/1022, after-a1 220/528, and after-a2 through back-3 220/534.
- **One divergence, at `end`.** B left the 220/534 screen on its own: a 220/540 fade for 60 frames, then 218/222 and a 4th batch of 34 `d:\INSTALL0_*.DAT` probes. Those 34 lines are the whole 108 → 142 warning difference. A and the dry run stayed on the screen to the end.

*Tie-break.* Agent 1 gave the GO at 03:17; no build was running. Route `harness/routes/b-gate-menus-long.txt` (1F3559C8…): the same first 34 steps, then a 90 s idle tail with a mark every 10 s. Runs: devoff2 `…/20261122-031756-bgate-long-devoff2`, devoffB `…/20261122-032150-bgate-long-devoffB`.
- **Both clean:** exit 0 via WM_CLOSE, 54/54 steps, 0 errors, critical lines or MISSING-FUNCTION, no dumps.
- **logdiff** (`bgate/route-long-0326.txt`): NEW 0, MORE 0, flags 0. 142 warnings in both. GONE is the 4 Toypad challenge keys.
- **Both builds leave the screen**, the same way pair-1 B did:
  - the 220/540 fade, 218/222, the 34 INSTALL probes, 12 `XamUserReadProfileSettings` lines and the Toypad light command;
  - then the same no-input attract sequence, with the same scene signatures in the same order (Agent 3: 594/2813 → 644/2868 → 839/31674 → 790/31625 → 788/31613 → … 8019/1043795 …).

**Idle time** from the last pad press to the first 220/540 frame, or to the end of the run:
- These are Agent 9's counts (`build/agent9/idle_frames.py`, log `build/agent9/logs/idle-frames.txt`, ±2 frames).
- One perf.csv row is one frame. Seconds are frame time.
- My coarser counts agree (`bgate/idlecount.py`, logs `idlecount-0323.txt` and `idlecount-long-0326.txt`, ±60 frames).

| Run | Build | Idle frames | Idle seconds | fps | Left? |
|---|---|---|---|---|---|
| Pair 1, dry | devoff2 | 1,572 (to the end) | 26.46 | 59.4 | no |
| Pair 1, A | devoff2 | 1,119 (to the end) | 26.38 | 42.4 | no |
| Pair 1, B | devoffB | 1,199 | 20.35 | 58.9 | yes |
| Tie-break | devoff2 | 1,122 | 18.88 | 59.4 | yes |
| Tie-break | devoffB | 883 | 18.87 | 46.8 | yes |

What the table shows:
- **devoff2 itself does both** on the same route. It stayed 26.4 s idle twice without leaving, and left after 18.88 s once. So pair 1's divergence is run-to-run variation, not devoffB behaviour.
- **The timer doesn't count frames.**
  - devoffB's tie-break exit came after 883 frames at 46.8 fps. devoff2's came after 1,122 frames at 59.4 fps. The idle time was the same (18.87 s and 18.88 s).
  - devoff2's dry run stayed past 1,572 idle frames.
  - So the frame window in Agent 1's rule (both at 1,200 ± 100 frames) doesn't fit devoffB. The rule's rollback case (B leaves while devoff2 stays past ~1,300 frames) didn't happen either.
- **Agent 9 withdrew its ~1,200-frame model at 03:29.** No measure it tried separates the 3 exits from the 2 devoff2 no-exits: frames, frame time, or interrupt_dispatches (26.9k-31.1k at the exits, 36.4k-40.6k in the no-exit runs).
- **Inputs.** The game read every press in all five runs, with 10-15 active pad reads per press in both builds. framecmp (`bgate/framecmp-0318.txt`) can't show whether a press was acted on: there are no audio frames, and the presses change no draw counts.

**Verdict (03:32): OFF B front-end gate PASS, partial coverage.**
- No rollback is needed; rb1-nolocal and rb2-nomusttail stay unused.
- Still open: OFF steps 2-6, the toy pad, and every native item.

**Verdict rule.** PASS for the OFF part of B needs all three:
- the full route ran in both builds (without the toy-pad steps, which are reported as not covered);
- no fail item;
- every must-match item holds.

A boot-only run is reported as "boot gate only". The native items above stay open until a native B build exists. I send the verdict to Agents 1, 2, 9 and 8 within 20 minutes of the logs landing.

## nativeB gate (task #17 item 1, from 04:12; for Agents 1, 2, 8 and 9)

**What is compared.** nativeB = `build/agent2/snapB3` (snap1 at S3d + `build/agent9/install/batch-nolr`, SHA256SUMS 24CE1493…, config E60EAF1C…), NATIVE_GPU=ON, built by Agent 2 (`rb-chain.ps1 -Variant nb`: prep-nb 04:12:11-04:13:43, build from 04:14:19) and staged as `nativeB-bin`. A = `build/agent2/native3d-bin`: the same S3d sources and SDK with the pinned S1 codegen (exe B90DF683…). So the codegen options are again the only difference. This time the native-only host code that the OFF gate deferred is compiled in (the list under "What OFF can and can't test").

**1a. Static: inputs (04:15-04:25)**
- `build/agent10/nb/statecmp.py` against `snap1/STATE-S3d-0342.tsv` (`nb/statecmp-snapB3.txt`): **MATCH**. 23,843 rows: 0 missing, 0 extra, 0 size or sha differences. All of rexlego/ outside generated is hashed (299 files); the rest is compared by size and mtime. **`--full`** (`nb/statecmp-snapB3-full.txt`, 1,282 s) hashes every file: **MATCH**, 23,843 files, 1,258,816,135 B, 0 differences.
  - Two expected overrides, both matched:
    - `rexlego/legodimensions_config.toml` = batch-nolr's E60EAF1C… (prep-nb step 3 writes it; S3d's is 7F775847…);
    - `rexlego/legodimensions_manifest.toml` = snap1's 14A59E33…: live with game_root rewritten for the snapshot depth. The STATE row carries the live sha with the snap1 size, a quirk of the STATE file (also in snap1 itself), not of snapB3.
  - Two unlisted build outputs, equal to snap1's: `rexlego/out/native-gpu/lego-linked-dxil-cache.cpp` (501,838,026 B, BB93FEC1…) and `runtime-linked-dxil-cache.cpp` (639 B, A479268E…). The 15 STATE-listed native-bank files under rexlego/out match.
  - Self-tests: snap1 vs S3d: MATCH. snapB vs S2: only the 15 bank files are missing (the OFF prep-b skipped rexlego/out), so the tool does see real differences.
- `nb/sumscheck.py` against batch-nolr's SHA256SUMS.txt (`nb/sumscheck-snapB3.txt`): **MATCH**.
  - 872 entries: 0 missing, 0 mismatched, 0 extra under generated/ (430 TUs; 432 .cpp files, 463,858,444 B).
  - codegen.d equals the install's with the baseline rexlego path replaced by snapB3's (E93479A8…), which is gen-check's rewrite.
  - Self-test on snapB: MATCH.
- Agent 2's own prep checks agree (`build/agent2/snapB3-prep.txt`): the robocopy of 24,115 files is equal to snap1 in size and mtime, the 46 patched files hash-equal their last PATCHES row, and gen-check found 870/870 identical.

**1a. Static: generated code (04:18)**
- `nb/lrsites.py` snap1 gen vs snapB3 gen (`nb/lrsites-snap1-vs-snapB3.txt`, 160 s): **PASS**. Each of the 6 LR stores is present once in both trees and is immediately followed by its call (gap 0):
  - 0x83F9B660 → `sub_83FC49E8` (placement relocation and drain);
  - 0x839D11B0 → `sub_839C4D08` (pause/Options rows);
  - 0x82A33FC4 and 0x82A3B88C → the indirect slot-heap Grow/Release. In B the call is `REX_CALL_INDIRECT_FUNC(ctr.u32)`: the target comes from the local CTR, and only the call macro uses it;
  - 0x82BD2B44 → `sub_82BD2868` (pool-copy caller test) and 0x82B5819C → `sub_82BD2AA0` (the logged pool-copy caller).
  - The 7 mid-asm hook calls are the same: the 5 `NativeCelShading*` in sub_82BC4340, `MissingAdventureTimeLookupNode` and `RepairDialogueLockReleaseOperand`.
- Host side: statecmp shows rexlego/src is byte-identical to S3d, so the host gates are unchanged (hooks_buffer.cpp:273, :309-310 and :388-402; native_slot_growth.cpp:63 and :76; settings_native_hooks.cpp:174).
- **Why B can't change what the native hooks see.** B moves CTR, XER, CR0-7 and the lwarx reservation into C++ locals (Stage A) and drops flush-mode switches at mode-independent builders.
  - A grep of the 188 native-only host files in snapB3 (`gpu_native/*`, native_slot_growth, settings_native_hooks, native_effects, native_skin_diagnostics) finds no use of ctr, cr, xer, the reservation, fpscr or MXCSR. They read GPRs, guest memory and `ctx.lr` only, and `ctx.lr` stays in ctx in B (no skip_lr).
  - Every `ctx.cr`/`ctx.ctr` user in rexlego/src is a hand-ported guest function that OFF builds too (crash_guards, native_atomics, native_constants, native_lock_elide, native_memops, native_saverest), and the OFF B gate ran those.
  - No file in rexlego/src sets or reads MXCSR.
  - Residual, as in Agent 9's S2.5: host float code inside a hook runs under whatever flush mode the last guest FP/VMX instruction left. That is already true in A; B can change which mode is current at a given call site. It matters only for denormal operands in host float math.

**1a. Static: binaries (04:38-04:43).** nativeB-bin was staged at 04:34 (exe 01C4D5A3…, 299,045,376 B; map C9259B05…; MANIFEST E5CBF30A…).
- `nb/hookset.py`, native3d map vs nativeB map, `--src` snapB3 rexlego/src (`nb/hookset-native3d-vs-nativeB.txt`): **PASS**.
  - 181 hooked guest functions in both. Both criteria agree: the public is in a host object, and the `__imp__` alias is not at its public. Same set, each in the same host object; the per-object counts are identical (native_saverest 72, hooks_state 16, settings_native_hooks 12, hooks_buffer 8, draw 7, native_slot_growth 3, …).
  - The LR-gated hook functions are in the same objects: sub_83FC49E8 and sub_82BD2868 in hooks_buffer, sub_839C4D08 in settings_native_hooks, sub_836F9E48, sub_82A3B6D8 and sub_82A57FE0 in native_slot_growth.
  - The 7 mid-asm hook functions have the same symbol and object (the 5 `NativeCelShading*` in native_effects, 2 in crash_guards).
  - Source cross-check: 121 REX_HOOK targets in snapB3 rexlego/src. 8 are not hooked (area_watch, tt_lock_trace, icon_probe: compiled out), as in A. Every hooked function has a source.
- Agent 9's mapcmp (`build/agent9/logs/mapcmp-native.txt`):
  - the same 164,786 sub_ functions, the same `__imp__` alias set and the same 109 hooked aliases;
  - .text 161,476,587 → 144,715,307 B (−10.38%); sub_ code bytes −10.58% (68,370 shrank, 1,835 grew, 94,581 same). The OFF pair had the same shape (devoff2 vs devoffB: −10.52%);
  - the 133 fewer publics are constant-pool and string-literal symbols of the recompiled TUs (`__real@…`, `??_C@…`: 374 only in A, 241 only in B). They follow from the different code.
- Agent 9's fpcheck (`fpcheck-native.txt`): **PASS**.
  - Both fingerprints recompute to their recorded values from the same 271 inputs, in the same order. The 258 non-codegen inputs are equal. All 13 that differ are codegen inputs: the config toml and 12 generated files. So the change 335FF2D4… → 81D1C3A7… is fully explained by the codegen option.
  - **What the fingerprint keys at runtime** (snapB3 rexlego/src):
    - the PSO recipe file `<exe dir>/cache/native-pso-recipes.bin`. pipeline_recipes.h:247-256 rejects a file written under another fingerprint;
    - the trigger-loaded precompiled pack (shader_archive.cpp:152-158), which is loaded only through the pack trigger (shaders.cpp:404-430);
    - the `Native GPU` startup line (device.cpp:895/904) and the gpu-timestamps CSV column.
  - The embedded DXIL caches (lego-dxil-cache, lego-linked-dxil-cache, the runtime caches) have no fingerprint check.
  - `nb/fpscan.py` (`nb/fpscan-native3d-nativeB.txt`): each exe contains only its own fingerprint (native3d: 335FF2D4… 2×, 81D1C3A7… 0×; nativeB: the reverse). Neither exe embeds a LEGODX1 pack; the single 'LEGODX1' hit in each is the comparison literal in code.
  - Consequence for 1b: Agent 3's harness mirrors BinDir into a fresh run dir (run-game.ps1:10, :102-110), and neither bin dir has a `cache/` dir. So both runs of the pair start with no PSO cache, and the fingerprint change can't make one side warmer. The pipeline-cache lines (opened with 0 bytes, preparation counts) should match.
- Agent 9's warncmp (`warncmp-native.txt`): CHECK, not FAIL.
  - 225 warning lines, 50 signatures, 0 in generated code. 48 of the signatures appear in earlier native logs.
  - The other 2 are host-only and come from byte-identical sources (statecmp `--full` MATCH): `-Wswitch` in thirdparty/plume d3d12memalloc.cpp, and the `getenv` deprecation in tools/gpu-aot prelink_shader_cache.cpp.
  - snapB3-on is a fresh tree, so this log includes files that the earlier, incremental native builds didn't recompile.
- MANIFEST: 149 PASS / 0 FAIL / 34 NOTE (native3d: 103 / 0 / 34).
  - The 46 extra PASS rows are the snapshot-copy checks: each patched file's copy in snapB3 equals its PATCHES row (draw.cpp 5EA1F357, settings_registry 4EC71328, settings_preferences 9CBE6DBF, audio_system.cpp 4331A312, rex_app.cpp 11DE333F, …).
  - The NOTEs are of the same kinds as native3d's: SDK, tools and test files that the game tree doesn't compile, and "map differs".
- The non-exe files equal native3d-bin's: rexruntime.dll D1D66AC3…, rexgpu-xenos.dll EE0A661F…, TracyClient.dll, amd_fidelityfx_dx12.dll, the wav and the ttf.
- **1a verdict: PASS.** Inputs, generated code, hooks and binaries differ from native3d only in the ways the codegen option predicts.

**1b. Route pair (logs landed 05:07:31; checked 05:09-05:20).** Agent 8's slot ran `harness/routes/b-gate-menus-long.txt` on both, A first. This is the first native run of this route.
- A = native3d, `build/agent3/runs/20261122-045945-bgate-long-native3d` (exe B90DF683…). B = nativeB, `build/agent3/runs/20261122-050343-bgate-long-nativeB` (exe 01C4D5A3…). The two tomls differ only in user_data_root.
- Both arms: 54/54 steps, 0 timeouts, exit 0 by WM_CLOSE (A 2.7 s, B 1.16 s), threaded recording off (the serial path).
- **B is clean:** 1,851 lines: 184 warnings, 0 errors, 0 critical, no dump.
- **A is not:** 184 warnings plus 4 STUCK-LOCK errors and 1 critical. At 197.24 s the watchdog saw CS 0x84959edc held for 5 s and wrote `hang-63248.dmp` at 200.78 s. The stall cleared and A ran to the end. It is in the baseline arm. Agent 6 owns the triage, and I sent Agent 6 `nb/mapwhere-stucklock.txt`, the `nb/logwin-*` windows and `nb/framepso-native3d-vs-nativeB.txt`.
- `bgate/logdiff.py --base A --cand B` (`nb/logdiff-native3d-vs-nativeB.txt`): NEW 0, MORE 0, marker flags 0. GONE lists:
  - A's 5 stall lines;
  - the placement relocation line (below);
  - 9 Toypad byte patterns. The toy pad polls in both arms (A 9/9 reads/writes, B 11/11); only the bytes vary.
- `nb/warntypes.py` (`nb/warntypes-native3d-vs-nativeB.txt`): the 19 warning types common to both arms have equal counts. These include the INSTALL probes, query invalidated by failed draw 16/16, unrecognized VS/PS 8/8, placement-missing VS/PS 4/4, AOT miss 2/2 and hash0 0/0. The only differences are A's 5 stall lines.
- `nb/nativelines.py` (`nb/nativelines-native3d-vs-nativeB.txt`):
  - slot heap registered: MATCH, 9/9 with the same sizes (2 × 2,044,723 + 7 × 4,194,304);
  - pool copy: MATCH, 128/128 at lr=82BD2B44 caller=82B5819C VS=A58EBA12…. The large copies are the same (716,800, 131,072, 380,928). The small ones vary per frame: A 4096×15 + 8192×110, B 4096×18 + 8192×107;
  - all 9 fail lines are 0/0, including "not in any registered module", pool copy unsupported, POINTLIST contract mismatch, external detach verification failed and unimplemented-instruction;
  - not covered in either arm: slot heap Grow (lr 82A33FC4), cel/bloom diagnostics, memexport begin.
- The two arms ran the same content:
  - the same 26 native scene teardowns in the same order (skin=1…26);
  - the heaviest frame has the same 5,861 draws and 56 PSO creations in both. Per Agent 1, PSO times depend on arm order through the driver cache and are not read here.
- **One must-match DIFF: placement relocation lr=83F9B660, A 1 / B 0.** Agent 8's gate_logdiff flags the same item. I rate it as not caused by B:
  1. The line is logged per call (hooks_buffer.cpp:388-402). It fires only when an XGOffsetResource type query from 0x83F9B660 finds a header that `IsNativeBuffer()` accepts but that has no tracked native buffer or texture type. Whether a placement header lands on such an address depends on the guest heap layout.
  2. A's only hit is at 213.56 s, about 3 s before WM_CLOSE, in the idle tail of the route rather than at a route step. It came 55 ms after the last scene teardown (skin=26 object A78AA300), on the loader thread t83568, for resource A78AA718, which is that object + 0x418.
  3. The heap layout differs between the arms from the first teardown onwards (skin=1 A795A7A0 vs A7955D40 … skin=26 A78AA300 vs A78A8980), while the scene sequence is the same.
  4. B can't have lost the caller check:
     - the call site still stores `ctx.lr = 0x83F9B660` immediately before `sub_83FC49E8(ctx, base)` (lrsites SAME);
     - the hook is in the same host object (hookset);
     - hooks_buffer.cpp is byte-identical (statecmp `--full`).
  5. The line never appeared in the 18 native matrix runs (native2, native3, native3d on the n-row route; `nb/placescan.py` → `nb/placescan-all.txt`). It is rare and depends on heap layout; it is not a fixed event of the route.
  - So for B this item is **not covered at runtime** (covered statically only), rather than different.
  - A rerun can't settle it, since only 1 of 20 native runs has the line. The level-change route (gate step 5) exercises the relocation and the drain on every run, but it needs the user's toy pad.

**1b verdict (05:23): PASS for nativeB against native3d.** *(06:15: reopened on the front-end exit item only; see "1b tie-break (pair 2)" at the end.)* Two caveats: the placement-relocation item is not covered at runtime, and one run-to-run item is open (the front-end exit press; a tie-break is recommended). By the L508-513 rule: the full route ran in both builds, B has no fail item, and every must-match item that this route exercises holds. The placement relocation is not exercised by this route; see above.
- Covered at runtime:
  - boot, and export lookups (0 "not in any registered module");
  - slot heap registration;
  - the CPU pool copy and its caller;
  - front-end menus (54/54);
  - the attract scenes, with 26 native scene teardowns;
  - occlusion queries, shader adoption and the placement-shader warnings;
  - cold PSO creation and a clean exit.
- Not covered (static 1a only):
  - placement relocation and the pool-copy drain;
  - slot heap Grow, cel/bloom, memexport;
  - pause/Options rows, cutscene, level change;
  - toy pad, screenshots, audio (muted).
- The native3d stall is a baseline finding that Agent 6 is triaging. It says nothing about B: B carries the same draw.cpp guard and ran clean.
  - **Extras sent to Agent 6 at 05:38** (`nb/genfunc-82BCE1F8-snap1.txt`, `nb/mapsym-native3d.txt`, `nb/framealign-native3d.txt`):
    - The owner's `lr=82BCE244` is the return address of `bl 0x83FC6A58` at sub_82BCE1F8+0x48.
    - In native3d's map, sub_83FC6A58 is hooked by draw.cpp.obj: `gpu_native::DrawIndexedVerticesHookQueued` (draw.cpp:5748, body at L5205). Its `__imp__` is in TU 339.
    - With threaded recording off, `NativeWorkerShouldQueue()` is false, so `DrawIndexedVerticesHook` runs inline: `LockRecording()`, then `DispatchDraw`, which creates PSOs on a miss. This happens while the guest holds kGraphicsLock.
    - The hook leaves ctx.lr alone, so the owner shows 82BCE244 for the whole native call. That lr is not an RtlEnterCriticalSection, so there is no guest lock cycle.
    - r3=300BE000 is the hook's device argument, loaded from the global at 0x84950478 (`lis r7,-31595; lwz r3,1144(r7)`).
    - sub_82BCE1F8 looks like a DrawIndexedPrimitive wrapper: index count = prim count × table[type].mult + table[type].add, with the table at 0x82002378.
    - Still open: the dump's native stack for tid 0x13 would separate busy (pipeline creation) from blocked (`LockRecording`).
  - Alignment (`nb/framealign.py`, ±0.2 s):
    - frames.csv row #16321 (5,198 ms, 56 PSOs in 4,341 ms) spans log ~192.15→197.35 s, which matches the STUCK-LOCK wait (192.24→197.24 s);
    - row #16322 (3,658 ms) spans 197.35→201.01 s and covers the minidump write (197.24→200.78 s), so the dump itself caused that frame.
  - **05:46 update: not native- or B-specific; it comes with CPU starvation.** Sources: Agent 3's notes 7.4 "attract-long results" (`perf-notes/agent3-run-harness.md` L554-571) and Agent 8.
    - The same STUCK-LOCK (CS 0x84959EDC, waiter lr=82A2A270) also hit OFF runs on the saturated machine:
      - devoffB's attract-long, 4 times (05:24-05:25). The owner was tid 0x17 at lr 83FAF200/83FAF188, with the GPU thread on PM4 opcode 0x22 (DRAW_INDX) at a new read pointer each time. The frames were 5.1-16.4 s with pm 0, so they were not pipeline compiles (`hang-52704.dmp`).
      - devoff3 warm, once (05:32:12, owner lr=83FBF868, `hang-69196.dmp`).
      - devoff3 cold: none.
    - The machine was 97-100% busy, with the CPU at or below its base clock. One cause was other agents' recursive searches; my genfunc scan over snap1's 438 TUs at ~05:25 was one of them. Since Agent 1's 05:31 rule I have used targeted reads only.
    - Reading: the game's render thread holds kGraphicsLock across D3D work, and when the host is starved that work slows down past the 5 s watchdog.
      - In OFF builds the slow work is the GPU thread's progress through the ring.
      - In native3d it was the inline draw's PSO creation. My 05:38 "PSO creation on a cold cache" reading is the native case of the same thing, not a separate cause.
    - Single runs on a machine whose load varied can't be compared by count (devoffB 4, devoff3 warm 1, cold 0).
    - Watch item: if quiet-machine runs (window 4) show it only in B arms, reopen. The 1b verdict is unchanged.
- **Open run-to-run item (Agent 3's report, `build/agent3/logs/route-native*.txt`).** The front-end exit came at a different press.
  - B left at the 2nd B press: the INSTALL batch logged at 05:05:49.3, about 2 s after the press.
  - A left about 7 s after the 3rd B press (INSTALL batch at 05:01:56.8). A also logged a Toypad write/read pair right after its 1st B press; B did not.
  - Both exits are well before OFF's ~19 s idle exit, so the menu flow on this route depends on timing in any case.
  - The arms also booted at different speeds: first frame at +8.4 s vs +13.3 s, and 6,893 vs 5,312 frames at the title mark. A timed press can therefore land in a different screen state, for example during a transition.
  - From the INSTALL batch on, the two arms run the same content: the slot heaps and the 26 teardowns in order.
  - This is the same class as OFF pair 1's `end` divergence, which the tie-break showed to be run-to-run variation. One run per arm can't separate it.
- Recommendations:
  - No rollback.
  - If the slot has room before 08:30, run a tie-break pair in reversed order (nativeB first, then native3d). It re-tests the exit press, removes the driver-cache order effect (which also helps Agent 6's stall triage) and re-samples the placement relocation. If nativeB again exits at the 2nd B press and native3d at the 3rd, treat it as a real difference and reopen this verdict.
  - Add the level-change route for nativeB (with native3d as the baseline) to window 4.

**1b tie-break (pair 2, reversed order; 06:15): the exit split repeated, so 1b is reopened on that one item. Every other item passes again.**
- Runs: Agent 8's slot, FUNCTIONAL ONLY, same route `harness/routes/b-gate-menus-long.txt` (1F3559C8…).
  - nativeB first: `build/agent3/runs/20261122-055041-bgate-rev-nativeB` (05:50:43).
  - native3d second: `…/20261122-055439-bgate-rev-native3d` (05:54:40).
  - Tool: `nb/pairall.py --tag pair2` → `nb/pairall-pair2.log`, plus the per-tool files `nb/*-pair2.txt`.
- **Both clean:** exit 0 via WM_CLOSE (nativeB 1.21 s, native3d 4.04 s), 54/54 steps, 0 errors, 0 critical, 0 MISSING-FUNCTION, no dumps, and no STUCK-LOCK or watchdog line.
- **logdiff:** NEW 0, MORE 0, flags 0. GONE (present in native3d, absent in nativeB):
  - 8 Toypad challenge-byte keys, which are random in every run;
  - 1 info line, "re-registered placement shader";
  - the warning "completion callback GPU wait took # ms" (native3d 2, nativeB 0). native3d also had the run's longest frame, 1,449 ms.
- **nativelines:**
  - slot heap 9/9 with the same sizes;
  - pool copy 128/128 with the same lr 82BD2B44, caller 82B5819C and VS A58EBA12…;
  - all 9 fail lines 0/0;
  - not covered (0/0): placement relocation, slot heap Grow, cel/bloom, memexport.
- **Two differences, both run-to-run:**
  - **Pool copy bytes (in order):** this row was DIFF in pair 1 too. Source: `nb/poolbytes.py` → `nb/poolbytes-pairs.txt`, 4 runs.
    - The first 5 copies (175, 32, 1, 1 and 93 pages) match in all 4 runs. After that, the mix of 1- and 2-page copies changes from run to run.
    - native3d differs most from itself: 15 vs 66 one-page copies. nativeB had 18 in both runs.
  - **"re-registered placement shader":** native3d 0 then 1, nativeB 2 then 0.
- **warntypes:** the 19 shared types have equal counts, and the named signatures are equal (placement-missing VS/PS 4/4, unrecognized VS/PS 8/8, hash0 0/0).
- **placescan:** 0 hits in both. **PSO creations:** 187/187 (282.9 vs 284.4 ms).
- **Exit press: the same split as pair 1.** Source: `nb/exitpress-pair2.txt`.
  - nativeB's front-end exit batch came 2.22 s after its 2nd B press (harness 121.94 s).
  - native3d's came 8.14 s after its 3rd B press (harness 133.57 s).
  - Swapping the order didn't change it, so by the L651 rule this is a real difference until shown otherwise.
- **What the exit is.** Source: `nb/timermodel.py` → `nb/timermodel-all.txt`, 9 runs including the 5 OFF b-gate runs.
  - **It is the screen's own timer, not a response to B.** The lag after the nearest press ranges from 0.7 s to 8.1 s. OFF builds leave 220/534 with no press at all, 14-18 s after the last B (`nb/exitpress-offtb.txt`).
  - **Seconds from the first frame to the exit batch:**

| Build | Exit times (s) | Runs that left |
|---|---|---|
| native3d | 118.9, 120.5 | 2/2 |
| nativeB | 105.7, 108.9 | 2/2 |
| devoffB | 127.7, 133.0 | 2/2 |
| devoff2 | 130.6 | 1/3 (the other two were still on the screen at 139.1 and 139.4 s) |

  - **No clock I tried fits every run.** I tried wall time, frame count, and game time with dt clamped at 16.7-250 ms, each counted from the first frame, START, A1 or A2. For every combination, the runs that left are spread over at least 18.7 s.
    - The closest fit is 60 Hz-clamped game time from the first frame: native3d 112.5 and 112.2, devoff2 112.3.
    - It still fails: the B runs left at 90.5-105.2, and devoff2's pair-1 run passed 115.6 without leaving.
  - **Direction: B leaves earliest in both build types.**
    - Native: both nativeB runs left before both native3d runs. That split happens by chance 1 time in 6.
    - OFF: devoffB left in 2 of 2 runs, devoff2 in 1 of 3.
    - So B shortens the time to leave the screen by about 12 s on native, and probably by less on OFF.
  - **Unknown:** whether this is B running faster (for example, background work finishing sooner) or a behaviour change. The game's exit condition is not known, and it doesn't follow frames or a clamped clock.
  - **Unchanged:** from the exit on, both builds run the same content: 9 slot heaps, the teardowns, the attract scenes and the same warnings.
- **Revised verdict (06:15):**
  - 1b PASS on every must-match item.
  - The front-end exit timing is OPEN: it reproduced, it is linked to B, and the mechanism is unknown.
  - It is not a fail item: no error, no missing content, the same scene sequence. No rollback.
- **To close it (Agent 1 chooses):**
  - (a) Accept it under the 03:50 OFF standard (both builds show the idle exit, with the same scenes after it), and record that "B leaves 220/534 ~12 s earlier on native".
  - (b) Explain it. Agents 3 and 9 have the screen IDs, so they can find the guest code that starts the 220/540 fade. I then diff that function's codegen in snap1 vs snapB3 (`nb/genfunc.py`, `nb/lrsites.py`). If the code reads the timebase (mftb), or polls a shared flag that B now holds in a local, this is a B behaviour change.
  - (c) More runs. These only firm up the direction (a third pair would take the chance from 1 in 6 to 1 in 20); they don't explain it.
- **Agent 8's route-report (06:19) confirms it:** scenes match up to UP 2.
  - nativeB leaves on the 2nd B again: n2 at L40 (119.72 s), then n0 at L41 (124.79 s).
  - native3d leaves on the 3rd B: n2 through L44 (130.51 s), n0 at L46 (140.81 s), then n41.
  - native3d's pad poll rate was low around its 3rd B (about 35 fps).
- **Agent 1's decision (06:28): (a)+(b). This is recorded as an OPEN item, not as accepted.**
  - Open item: on native, nativeB leaves the front-end ~12 s earlier than native3d, and devoff leans the same way. It is not a fail item and needs no rollback.
  - (b) is in progress: Agents 3 and 9 locate the guest code that starts the front-end fade, and I diff that code's codegen in snap1 vs snapB3. Read-only, targeted reads until Agent 8 posts that its last run has ended, then at most 2 threads.
  - Due 08:15. If the code isn't found by then, the item goes to S4 as unexplained.
  - No (c) runs tonight.
- **(b) result (07:35): B's generated code is equivalent to A's in the front-end and clock code, and across the whole tree. These checks find no codegen change behind the earlier exit. The item stays OPEN and goes to S4 with the mechanism unidentified.**
  - **Question.** Does batch-nolr change what the guest code that arms, counts or expires the front-end page timer does? For example, does it read the timebase, or keep a polled flag or a callee's result in a local?
  - **Front-end and clock functions.** These are Agent 9's clock list (`build/agent9/b-clock/clock-list.md`, 11 functions) and run 2's 9 functions. Sources: `fe/run3-a9.txt` and `fe/run2-a9.txt`; outputs in `fe/out3/` and `fe/out2/`.
    - Every function has the same guest instruction sequence in snap1 and snapB3, with only B's mechanical rewrites:
      - run 3: cr 61, decl 11, flush 6, rlw 4, tail 4;
      - run 2: cr 85, decl 8, rlw 13, tail 6;
      - OTHER 0 in both.
    - None of them reads the timebase inline (tb 0). The two clock functions that read it (sub_83FAF088, sub_83FB2640) call the out-of-line Clock::QueryGuestTickCount() in both trees, and sub_83FAF088 is identical.
    - No SO writers. GPRs stay in ctx.rN and REX_LOAD/STORE are volatile, so both trees re-read a polled memory flag every time.
  - **Whole tree.** Source: `fe/feall.py`, output `fe/all/feall-summary.txt`.
    - 164,786 functions, 0 missing: 75,441 identical, 59,989 mechanical (fast path), 29,356 checked on the slow path. 0 have a sequence mismatch and 0 have an unexplained instruction.
    - rlw: 91,605 rewrites, all proven by evaluation (4,568 distinct proofs, 0 failed).
    - OTHER: 413 blocks in 166 functions, all of two known kinds:
      1. stwcx./stdcx. (255 + 49). Apart from the local `reserved`, the only change is `cr0.so = ctx.xer.so` → `cr0.so = 0`, which is the cr_compare_so_zero assumption.
      2. The vmx_vector_fallbacks bodies (vsraw128 44, vsubsws 26, vsrw128 19, vpkuhus128 14, vsrab 6), reviewed SAFE in Review 2 row 10.
  - **The SO = 0 assumption.** Source: `fe/livein.py A`, output `fe/livein-A.txt`.
    - In snap1 the only XER.SO writer is sub_83E5C88C's mtxer, the known residual (agent9-codegen.md:185-194). No function reads SO: no mfxer, mcrxr or bso/bns.
    - All 153 functions with stwcx./stdcx. have their own lwarx/ldarx, so no reservation crosses a call.
  - **B's locals.** feall treats ctx.cr6 and the local cr6 as the same thing, so they are checked separately.
    - `fe/livein.py B` (v2; classifier self-test 29/29; output `fe/livein-B2.txt`):
      - 70,213 functions have locals, with 349,842 keys (each CR bit, each XER field, ctr, reserved).
      - First use is a write for 328,220 keys; 21,594 are never used; 28 are read first.
    - **All 28 read-first keys are in one function, sub_83E49CA0.** It is a setjmp-style save: an mfcr of cr1-cr7, then LR and f14-f31, into the buffer at r3.
      - B saves 0 for cr1-cr7, where A saves the caller's CR.
      - Only a matching restore reads that word, and a non-local return can't work in either tree.
      - Its only direct caller is sub_82CD1D38 (2 sites, `if (setjmp(...) == 0)` shape), which is outside the front-end code.
    - **Reads after a call.** There are 41 textual hits in 37 functions where a call-volatile local is read and its last write comes before a non-tail call.
      - `fe/liveflow.py` (a CFG may-analysis; self-test 9/9; output `fe/liveflow.txt`) finds that none of these paths exists: all 37 functions are clean, and so are the 13 front-end and clock functions.
      - So no path reads a local where A would have read a value left by a callee.
  - **What the timer code does.** Source: `fe/show.py`.
    - **sub_82FE70C0 is the page-47 timer.**
      - Event 5 adds the dt from the event payload ([[r6+16]+20]) to the float at 0x849F5F88. It adds only while the timer is armed (byte 0x849F5F84 != 0) and the byte [app]+2288 is 0 (app = *(0x849F5E8C)).
      - Past the limit at 0x849F5F8C, it clears the armed byte and tail-calls sub_82FE6F98, which requests page 56.
      - Event 2 tail-calls sub_82FD4868.
    - **sub_82FD4868 arms the timer** (armed = 1, accumulator = *(0x82005CD0), limit = *(0x847D4A78)) only when sub_82FB9020 returns 1. That happens when:
      - the byte 0x848E2EA2, read by sub_82A75FD8, is 0;
      - and, in mode 3 ([[0x849F5640]+180] == 3), neither sub_82A832F8(*(0x848E1E8C), 3) nor sub_82A832F8(…, 6) returns true.
      - Otherwise it calls sub_82FBDFF8 without arming.
    - So when the timer starts, and whether it counts, depends on state that other code sets. That fits Agent 9's model (background work gates the arm or the page change) and Agent 3's load dependence (nativeB < native3d < OFF cold; warm runs earlier than cold).
    - A lis/stb scan finds no direct writer of 0x848E2EA2 or of [app]+2288 (`fe/flagw-848E2EA2.txt`, `fe/flag2288.txt`), so both are written through another base pointer.
      - Readers: 0x848E2EA2 is read by sub_82A75FD8 (callers sub_82FB9020, sub_82FD4868 ×2, sub_82FBA9E8) and sub_82A7EAA0 (caller sub_82FE6CC0).
      - [app]+2288 is read by sub_82FE70C0 and sub_82FB5670.
      - Source: `fe/callers.txt`.
  - **Verdict.**
    - B doesn't change the code that arms, counts or expires the front-end timer.
    - The static checks find no path in the tree where a B local holds a different value from A's ctx. The one exception is the setjmp CR word above, which no working path reads.
    - The earlier exit is most likely a timing effect: B's faster guest code lets the gating state settle sooner. That is not proven, so the item stays OPEN for S4. It is not a fail item and needs no rollback.
  - **For S4:**
    1. Find the writers of 0x848E2EA2 and of [app]+2288, and what sub_82A832F8's queries 3 and 6 report.
    2. Run one instrumented pair (native3d, nativeB) that logs the time of each sub_82FD4868 call, sub_82FB9020's result, and the first event 5 that adds dt.
    - If the arm time moves by about 12 s while the counting time stays the same, that is the mechanism.
- **Agent 3's narrowing (07:34, `build/agent3/logs/fe-11024.txt`).** On native, the GPU entry points are host hooks, so their B bodies never run: Swap 83FB33E0, KickOff 83FC0C10, KickOffSegment 83FC08D0, BlockOnFence 83FBF8A0, BlockUntilNotBusy 83FBF900, BlockUntilIdle 83FC0EC0, InsertCallback 83FC0F38, SyncToPresentationInterval 83FB2F20, CreateDevice 83FAF9A0, and the queries 83FB2360/83FB0738/83FB09E8/83FB05B0. sub_83FAF088 runs only via 83FBF1C8, 83FBF260, 83FCA768 or 83FCAD20, or via 83FBF7D0 when that is called from 83FBFB30, 83FC5730 or 83FC5D68.
  - All 8 of those callers are inside the whole-tree result (feall: 0 missing, 0 sequence mismatch). 7 have no OTHER block. sub_83FC5D68 has one `stwcx.` OTHER block (cr0.so = 0, the reviewed-SAFE class; the tree has 0 SO readers). sub_83FAF088 itself was clean in liveflow. The verdict doesn't change.
