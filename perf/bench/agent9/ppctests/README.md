# T8: tests/ppc asm suite with codegen options on (default vs opt vs crso)

Owner: subagent A of Agent 9. Outputs: `build/agent9/ppctests/{default,opt,crso,opt9}`. Scripts: `bench/agent9/ppctests/`.

> Session 3 (02:21, Agent 9): **opt9** = opt without skip_lr, i.e. build B's 9 keys. 1515 tests: 1513 pass, 1 FAIL (the same vupkd3d128.test_short2_3), 0 CRASH, 1 excluded (cr_so_fold.test_call), the same as opt. Its `ppc_test_functions.cpp` differs from opt's only in 9 `ctx.lr` lines; the other 3 generated files are byte-identical. default and crso, rerun alongside, are unchanged. Details: `perf-notes/agent9-codegen.md` S3.3.

> Status (23:30): first pass and rerun are complete. The rerun used tool sha256 37B32713B7516402 (23:16) and covered default, opt (now with flush_mode_elision), crso and test F. Each variant has exactly one FAIL, the same test in all three: vupkd3d128.test_short2_3. The parser fix generated that test for the first time. It exposes an emitter gap in the SHORT2 unpack, not an option bug. See [Rerun](#rerun-tool-sha256-37b32713b7516402-231617) and [Failures](#failures).

## Summary

| variant | codegen options | tests | pass | FAIL | CRASH | excluded |
|---|---|---|---|---|---|---|
| default (first pass) | none (built-in defaults) | 1496 | 1494 | 0 | 2 | 0 |
| opt (first pass) | opt_config.toml without flush_mode_elision | 1496 | 1488 | 6 | 2 | 0 |
| default (rerun) | none | 1515 | 1514 | 1 | 0 | 0 |
| opt (rerun) | opt_config.toml incl. flush_mode_elision | 1515 | 1513 | 1 | 0 | 1 |
| crso (rerun) | cr_compare_so_zero only | 1515 | 1514 | 1 | 0 | 0 |
| opt9 (session 3) | opt_config.toml without skip_lr (build B's 9 keys) | 1515 | 1513 | 1 | 0 | 1 |

**Rerun (tool 37B32713B7516402).**
- The only non-passing test is `vupkd3d128.test_short2_3`. Its generated code and its FAIL are identical in all three variants.
  - It was generated for the first time in this run.
  - It expects the quiet NaN 0x7FC00000 for a SHORT2 value of -32768. The emitter produces 0x403F8000.
- The opt exclusion is `cr_so_fold.test_call`, shape (b) of test F. Run on its own, it gives SO = 0, as predicted.

**First pass (tool E35C3D09AB3DA2B6).** None of the non-passing tests was a miscompile.
- The 2 CRASH, in every variant: recompile-tests could not resolve a `b`/`beq` to another symbol, so it emitted REX_FATAL. Fixed in the rerun tool.
- The 6 FAIL in opt: these are the only tests that read the CR from ctx (`#_ REGISTER_OUT cr`), and cr_as_local keeps the CR in locals. The rerun tool drops those expectations under cr_as_local and logs a warning.

Details are under [Failures](#failures).

## Variants

- **default**: `rexglue recompile-tests` with no `--config`.
- **opt**: `--config DimensionsRecomp/rexglue-sdk/tests/ppc/opt_config.toml`.
  - Root keys set to true: skip_lr, ctr_as_local, xer_as_local, reserved_as_local, cr_as_local, rlwinm_lowering, cr_compare_so_zero, musttail_calls, vmx_vector_fallbacks, flush_mode_elision.
  - Deliberately off: skip_msr, non_argument_as_local, non_volatile_as_local.
  - The rerun passes the SDK TOML directly.
  - The first pass ran without flush_mode_elision and went through `build/agent9/ppctests/opt_local.toml`. That file is an `includes` of the SDK TOML plus a dummy `file_path`. Tools older than the --config fix needed it; it is now obsolete. See [Infra findings](#test-infra-findings) 1.
- **crso** (for test F): `--config bench/agent9/ppctests/crso_config.toml`.
  - Only `cr_compare_so_zero = true`, so XER stays in ctx (no xer_as_local).
- **opt9** (session 3): `--config bench/agent9/ppctests/opt9_config.toml`, which is opt_config.toml without skip_lr. These are build B's 9 keys (perf-notes S2.10).
  - `gen.ps1`, `compile.ps1`, `link.ps1` and `runtests.ps1` take `-Variant opt9`. `runtests.ps1` excludes `opt9=cr_so_fold.test_call` by default, as it does for opt.
  - Its cases TU is byte-identical to opt's, so `link.ps1` links opt's cases object. Driver: `build/agent9/ppctests/chainOpt9.ps1`. LR-only diff against opt: `build/agent9/ppctests/opt9_lrdiff.py`.

## Pipeline

Run everything from the workspace root. Each step that compiles or generates takes one Agent 9 CPU slot (`bench/agent9/cpu2.ps1`). Check `bench/agent9/QUIET` before each step.

```powershell
# 1. as + ld + nm for every tests/ppc/asm/*.s, as tests/ppc/CMakeLists.txt + cmake/ppc_test_pipeline.cmake do
#    (-Only <stem glob> for a subset)
powershell -NoProfile -File bench/agent9/cpu2.ps1 -File bench/agent9/ppctests/asm.ps1
# 2. generate the Catch2 sources, one variant per slot
powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "powershell -NoProfile -File bench/agent9/ppctests/gen.ps1 -Variant default"
powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "powershell -NoProfile -File bench/agent9/ppctests/gen.ps1 -Variant opt"
powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "powershell -NoProfile -File bench/agent9/ppctests/gen.ps1 -Variant crso"
# 3. compile, one TU per slot (pin ppc_tests flags, -O3)
powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "powershell -NoProfile -File bench/agent9/ppctests/compile.ps1 -Variant default -Tu cases"
powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "powershell -NoProfile -File bench/agent9/ppctests/compile.ps1 -Variant default -Tu functions"
#    (likewise for -Variant opt / crso; a variant only needs its own cases TU when its ppc_test_cases.cpp differs from default's)
# 4. link (pin link line + pin rexruntime.dll/TracyClient.dll copied next to the exe)
powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "powershell -NoProfile -File bench/agent9/ppctests/link.ps1 -Variant default"
# 5. run and compare, then extract the generated code of every non-passing test
powershell -NoProfile -File bench/agent9/ppctests/runtests.ps1
powershell -NoProfile -File bench/agent9/ppctests/extract.ps1
```

### Build decisions

- **Flags.** Compile and link flags are the pin build's. They come from `ninja -f build-Release.ninja -t commands ppc_tests` in `build/sdk` and go through response files.
- **Headers.** Rex headers come from the dev tree, `DimensionsRecomp/rexglue-sdk/include`. That is what the dev-tree tool generates code for.
  - Libraries and DLLs are the pin build's: `baseline/DimensionsRecomp/rexglue-sdk/out/win-amd64/Release`.
  - `rex::memory::Memory` (used from rexruntime.dll) gains only a non-virtual method in the dev `xmemory.h`, so its layout is unchanged.
- **`shim_logfloor.cpp`.** The dev `logging/api.h` references `rex::detail::SharedLogLevelFloor()`, which the pin rexruntime.dll does not export.
  - The shim returns a floor of 0, which changes no output.
  - It is linked only with dev headers. `compile.ps1`/`link.ps1 -Headers pin` builds against the pin headers instead.
- **nm map workaround.** Agent 2 reported this crash. The Cygwin `nm` in tools/binutils crashes when its stdout is redirected to a file. `asm.ps1` takes nm's output through a pipe and writes the .map with LF.
- **Test order and isolation.**
  - Catch2 3.12 runs in random order by default, so `runtests.ps1` uses `--order decl`.
  - The `[seq_tailcall_musttail]` tests run one per process. Their REX_FATAL ends the process with 0xC0000409, and in a shared process it would cut the run short.
  - Under CTest every test already runs in its own process.
- **Timings, first pass.**
  - asm: 168 files in 51 s.
  - gen: 1.4 s (default) and 2.6 s (opt).
  - compile functions TU: 41.6 s (default) and 25.6 s (opt).
  - compile cases TU: 124.5 s.
  - link: 0.5 s.
  - Main test pass: ~1.7 s.

## First pass (tool sha256 E35C3D09AB3DA2B6, 21:27:51)

- Gen output, per variant:
  - 1496 TEST_CASEs and 1523 functions.
  - `ppc_config.h`, `ppc_test_decls.h` and `ppc_test_cases.cpp` were byte-identical between default and opt. Only `ppc_test_functions.cpp` differed (888,636 vs 889,332 bytes).
- Assembly: 166 of the 168 .s files produced symbols. `instr_vpkpx.s` and `instr_vpkuhum128.s` are fully commented out, so they give an empty .bin, which the tool skips.

| test | default | opt | detail (opt) |
|---|---|---|---|
| divdu.test_10 | pass | FAIL | `cr_actual == 0x80000000` => 0 |
| divdu.test_11 | pass | FAIL | `cr_actual == 0x20000000` => 0 |
| divwu.test_13 | pass | FAIL | `cr_actual == 0x80000000` => 0 |
| divwu.test_14 | pass | FAIL | `cr_actual == 0x20000000` => 0 |
| mulhwu.test_7 | pass | FAIL | `cr_actual == 0x20000000` => 0 |
| mulhwu.test_8 | pass | FAIL | `cr_actual == 0x20000000` => 0 |
| seq.test_tailcall_chain | CRASH(0xC0000409) | CRASH(0xC0000409) | REX_FATAL, unresolved `b` |
| seq.test_tailcall_cond_taken | CRASH(0xC0000409) | CRASH(0xC0000409) | REX_FATAL, unresolved `beq` |

Every other test passes in both variants. That includes:
- the rlw* tests, among them instr_rlw_lowering;
- cmp*;
- stwcx.;
- seq.test_tailcall_cond_not_taken (its branch is not taken);
- the VMX tests.

## Rerun (tool sha256 37B32713B7516402, 23:16:17)

The tool contains:
- Agent 9's recompile-tests fixes: `--config` takes the SDK TOML directly, and REGISTER_OUT cr expectations are dropped under cr_as_local.
- The test_support.cpp fixes: a real tail call for a `b`/`bc` to another test's entry, and the ParseTestSpecs label fix.
- Agent 9's skip_lr LR-user fix.

The run took 23:17-23:26. The compiles used two cpu2 slots in parallel (`build/agent9/ppctests/chainA.ps1`, `chainB.ps1`, one cpu2 call per compile).
- asm: only `instr_cr_so_fold.s` was assembled, in 0.9 s. Its .map has 4 symbols and its .bin is 100 bytes. No other .s file was newer than its .bin.

| step | default | opt | crso |
|---|---|---|---|
| gen | 8.6 s | 0.8 s | 1.1 s |
| TEST_CASEs / functions | 1515 / 1527 | 1515 / 1527 | 1515 / 1527 |
| compile cases TU (-O3) | 87.0 s | 83.6 s | uses default's obj (identical source) |
| compile functions TU (-O3) | 31.0 s | 41.8 s | 20.5 s |
| link | 0.6 s | 0.5 s | 0.3 s |
| main test pass | 5.7 s | 4.3 s | 4.1 s |
| result | 1514 pass, 1 FAIL | 1513 pass, 1 FAIL, 1 excluded | 1514 pass, 1 FAIL |

- **Generated files** (sha256 prefix, bytes):
  - `ppc_config.h` and `ppc_test_decls.h` are identical in all three variants.
  - `ppc_test_cases.cpp`: default and crso are identical (6B8F026A74EA, 733,997). opt is 788EA1AAE365 (732,341) because its 6 cr expectations are dropped.
  - `ppc_test_functions.cpp`: default 3DB9332B6EDD (894,535), opt E2CE8404C608 (892,944), crso 2AF6AC190897 (893,260).
- **crso vs default functions.** Exactly 255 lines differ. In every one, a compare's XER argument changes from `ctx.xer` to `{}`.
  - The cr_compare_so_zero analysis runs per test binary, and only instr_cr_so_fold writes XER.
  - All those tests still pass.
- **gen.log:**
  - opt: `cr_compare_so_zero: 3 functions write XER.SO (0 keep XER in ctx); the others compare with SO = 0` and `cr_as_local: dropped 6 REGISTER_OUT cr expectations (CR is a function local)`.
  - crso: `cr_compare_so_zero: 3 functions write XER.SO (3 keep XER in ctx); the others compare with SO = 0 where their XER is local`.
- **Test count.** 1515 = 1496 (first pass) + 1 (seq.test_tailcall_uncond) + 3 (test F) + 15 v(u)pkd3d128 tests the parser fix brought back. [Infra findings](#test-infra-findings) 3 lists them.

Per-test differences, from `build/agent9/ppctests/compare.md`:

| test | default | opt | crso | detail |
|---|---|---|---|---|
| cr_so_fold.test_call | pass | excluded | pass | opt, run on its own: FAIL with r3 = 0x48000020 (SO = 0, by design of xer_as_local) |
| vupkd3d128.test_short2_3 | FAIL | FAIL | FAIL | `ctx.v3.u32[2] == 0x7FC00000` gives 0x403F8000. Emitter gap, see [Failures](#failures). |

The other 1513 tests pass in all three variants. Among them:
- the 6 cr tests in opt;
- all 4 seq tail-call tests, using musttail in opt;
- rlw*, cmp*, stwcx. and the VMX tests;
- 14 of the 15 v(u)pkd3d128 tests that were brought back.

## Test F: XER.SO in compare results

File: `DimensionsRecomp/rexglue-sdk/tests/ppc/asm/instr_cr_so_fold.s`. Catch2 names are `cr_so_fold.*`.

The tests set XER.SO with `lis r11,0x8000; mtxer r11`. They then run `cmpw cr1,r4,r5`, `cmpwi cr6,r4,5` and `andi. r6,r4,4` with r4=5 and r5=7, and read the CR with `mfcr r3`.
- With SO set, the expected CR is `0x59000030`: cr0 GT|SO, cr1 LT|SO, cr6 EQ|SO.
- With SO clear, it is `0x48000020`.

| test | shape | expected r3 | default | crso | opt |
|---|---|---|---|---|---|
| cr_so_fold.test_same | (a) mtxer and the compares in one function | 0x59000030 | pass | pass | pass |
| cr_so_fold.test_call | (b) mtxer, then `bl test_cr_so_fold_callee` (compares + mfcr in the callee) | 0x59000030 | pass | pass | excluded (run on its own: FAIL, r3 = 0x48000020, as predicted) |
| cr_so_fold.test_clear | control: mtxer with SO clear, compares in the same function | 0x48000020 | pass | pass | pass |

- **crso, shape (b).** The callee has no mtxer. The caller, however, keeps XER in ctx and writes it, so `ctxXerWritten` is true and the callee still reads `ctx.xer.so`.
- **opt, shape (b): excluded by design.** With xer_as_local, XER is a per-function zero-initialized local that a call does not carry. The callee therefore compares with SO = 0, with or without cr_compare_so_zero.
  - `runtests.ps1 -Exclude opt=cr_so_fold.test_call` takes it out of the opt run.
  - It is then run once on its own, for the record. The expected result is r3 = 0x48000020, and that is what the rerun gave.

The callee `test_cr_so_fold_callee` (`instr_cr_so_fold_82010050`) as generated in the rerun. Full listings for every variant are in `build/agent9/ppctests/instr_cr_so_fold.md`.

```cpp
// default and crso (identical): the compares read ctx.xer, which the caller's mtxer wrote
ctx.cr1.compare<int32_t>(ctx.r4.s32, ctx.r5.s32, ctx.xer);
ctx.cr6.compare<int32_t>(ctx.r4.s32, 5, ctx.xer);
ctx.cr0.compare<int32_t>(ctx.r6.s32, 0, ctx.xer);
// opt: CR fields are locals, and XER is not carried across the call, so SO = 0
cr1.compare<int32_t>(ctx.r4.s32, ctx.r5.s32, {});
cr6.compare<int32_t>(ctx.r4.s32, 5, {});
cr0.compare<int32_t>(ctx.r6.s32, 0, {});
```

- In opt, the caller's mtxer writes its own `PPCXERRegister xer{}` local. Nothing reads it.
- In shape (a), opt passes that local to the compares (`cr1.compare<int32_t>(ctx.r4.s32, ctx.r5.s32, xer);`), so SO = 1.

## Failures

### vupkd3d128.test_short2_3: FAIL in every variant (rerun)

- **Test.** The input is `v3 = [CDCDCDCD, CDCDCDCD, CDCDCDCD, 00008000]`, followed by `vupkd3d128 v3, v3, 1` (SHORT2).
  - Expected: `[40400000, 7FC00000, 00000000, 3F800000]`.
  - Got: element 1 (`ctx.v3.u32[2]`) is `0x403F8000` instead of `0x7FC00000`. The other elements match.
- **Cause.** The emitter computes 3.0 + s16·2^-22 as an integer add on the bit pattern: `0x40400000 + (-32768) = 0x403F8000`.
  - For that negative-overflow value the test expects a quiet NaN, `0x7FC00000`. That matches Xenia's SHORT2 unpack, which turns 0x403F8000 into 0x7FC00000.
  - The generated code is identical in default, opt and crso, so this is not an option issue. See `instr_vupkd3d128_82010020` in `failures.md`.
- **Why it is new.** The test had never been generated. The old ParseTestSpecs swallowed its label because it directly follows the previous test's REGISTER_OUT line, with no blank line in between. The rerun tool's parser fix brought it back.
- **Fix.** Either replace 0x403F8000 with 0x7FC00000 per element in the vupkd3d128 SHORT2 emitter, or exclude the test.

```cpp
DEFINE_REX_FUNC(instr_vupkd3d128_82010020) {   // identical in all variants
	REX_FUNC_PROLOGUE();
	PPCRegister temp{};
	PPCVRegister vTemp{};
	// vupkd3d128 v3,v3,4
	temp.f32 = 3.0f;
	temp.s32 += ctx.v3.s16[1];
	vTemp.f32[3] = temp.f32;
	temp.f32 = 3.0f;
	temp.s32 += ctx.v3.s16[0];
	vTemp.f32[2] = temp.f32;
	vTemp.f32[1] = 0.0f;
	vTemp.f32[0] = 1.0f;
	ctx.v3 = vTemp;
	// blr
	return;
}
```

### seq.test_tailcall_chain, seq.test_tailcall_cond_taken: CRASH 0xC0000409 in the first pass, fixed in the rerun

**Rerun (tool 37B32713B7516402).** All four seq tail-call tests pass in every variant: chain, cond_taken, cond_not_taken and the newly generated uncond. A `b`/`beq` to another test's entry is now a real tail call:

```cpp
// default: seq_tailcall_musttail_82010010 (b 0x82010008) and the taken branch of 82010018 (beq cr6,0x82010000)
seq_tailcall_musttail_82010008(ctx, base);
return;
if (ctx.cr6.eq) {
	seq_tailcall_musttail_82010000(ctx, base);
	return;
}
// opt (musttail_calls)
[[clang::musttail]] return seq_tailcall_musttail_82010008(ctx, base);
if (cr6.eq) {
	[[clang::musttail]] return seq_tailcall_musttail_82010000(ctx, base);
}
```

The first-pass analysis is kept below for the record.

**First pass.** recompile-tests did not resolve a `b`/`bcc` from one test symbol to another, so the generated code called REX_FATAL. In opt the code was the same, with `cr6` as a local.

```cpp
DEFINE_REX_FUNC(seq_tailcall_musttail_82010010) {   // seq.test_tailcall_chain
	// b 0x82010008
	// FATAL: unresolved function 0x82010008 (no CallTarget in FunctionNode)
	REX_FATAL("Unresolved call from 0x82010014 to 0x82010008");
	return;
}
DEFINE_REX_FUNC(seq_tailcall_musttail_82010018) {   // seq.test_tailcall_cond_taken
	ctx.cr6.compare<int32_t>(ctx.r3.s32, 0, ctx.xer);
	ctx.r3.u64 = ctx.r4.u64;
	if (ctx.cr6.eq) REX_FATAL("Unresolved branch from 0x82010020 to 0x82010000 in sub_82010018");
	ctx.r3.s64 = 100;
	return;
}
```

- All four branching functions of seq_tailcall_musttail.s contain REX_FATAL: 82010008, 82010010, 82010018 and 8201002C.
- So the musttail tail-call tests check nothing yet. cond_not_taken passes only because its branch is not taken.
- **Root cause:** `AnalyzeTestBinary` (src/codegen/test_support.cpp) registers a CallTarget only for `bl`.
  - A `b`/`bc` to another test function's entry is classified as a tail call (`classifyTarget` gives Function). The emitter's `findCallTarget(pc)` then finds no CallTarget and emits REX_FATAL.
  - `build_b` → `emit_tail_call` → `emit_function_call` produces "no CallTarget in FunctionNode". `emit_conditional_branch` produces "Unresolved branch".
- **Suggested fix (second pass of AnalyzeTestBinary):** also register the edge for a branch without link whose target is the entry of another test function.
  ```cpp
  if (decoded.branch_target.has_value()) {
    uint32_t target = decoded.branch_target.value();
    if (decoded.is_call() || target < fnAddr || target >= nextAddr)
      if (auto* targetNode = ctx.graph.getFunction(target))
        ctx.graph.addCallToFunction(fnAddr, pc, CallTarget::function(targetNode));
  }
  ```
- `bl` to a `test_` symbol is already resolved (seq_jumptable_constants; test F's `bl`).

### divdu.test_10/11, divwu.test_13/14, mulhwu.test_7/8: FAIL in opt only (cr_as_local, by design)

These are the only six tests with `#_ REGISTER_OUT cr`. The test template reads `ctx.cr0..cr7`. Under cr_as_local the compare writes a local, so ctx.cr stays 0:

```cpp
DEFINE_REX_FUNC(instr_divdu_820100C4) {   // opt
	PPCCRRegister cr0{};
	ctx.r0.u64 = ctx.r0.u64 ? ctx.r3.u64 / ctx.r0.u64 : 0;
	cr0.compare<int32_t>(ctx.r0.s32, 0, {});
	return;
}
```

In the rerun, the new tool drops these REGISTER_OUT cr expectations under cr_as_local and logs `cr_as_local: dropped 6 REGISTER_OUT cr expectations (CR is a function local)`. All six pass in opt, and their GPR expectations are still checked.

## Test-infra findings

1. **`recompile-tests --config <SDK toml>` failed with "Missing required field: file_path".**
   - `RecompilerConfig::Load` calls `FinalizeConfig`, which requires `file_path`.
   - Worked around with `opt_local.toml`. Agent 9 fixed it in test_recompiler.cpp: options load once, with file_path/out_directory_path preset.
   - Verified in the rerun (tool 37B32713B7516402): opt passes the SDK TOML directly.
2. **`ppc_config.h` missing from the custom command's OUTPUT.** recompile-tests now writes it (template `test/ppc_config_h.inja`), but tests/ppc/CMakeLists.txt does not list it as an OUTPUT. The proposal below adds it.
3. **ParseTestSpecs drops the test that follows a label without annotations.**
   - The loop that skips to the output annotations runs on to the next `#` line, which is the next test's REGISTER_IN. That consumes the next test's label.
   - Result: `test_tailcall_uncond` in seq_tailcall_musttail.s (after the bare `test_tailcall_target:`) has never been generated as a test. There are 1496 tests, not 1497.
   - Suggested fix: in that loop, stop at a line whose label is in `symbols` and parse it as the next spec.
   - **Fixed in the rerun tool, together with the `b` fix.** seq.test_tailcall_uncond is generated and passes.
   - The same bug dropped every test whose label directly follows the previous test's last REGISTER_OUT line, with no blank line in between. The fix brought back 15 such tests:
     - vpkd3d128 (12): d3dcolor_1_1, d3dcolor_1_3, d3dcolor_2_1, d3dcolor_2_3, d3dcolor_3_1, d3dcolor_3_3, d3dcolor_invalid_1, float16_2_0, float16_4_0, short2_1, short2_invalid_1, uint_2101010_1.
     - vupkd3d128 (3): short2_1, short2_3, uint_2101010_1.
   - That makes 1496 + 1 + 3 (test F) + 15 = 1515 tests. Of the 15, only vupkd3d128.test_short2_3 fails (see [Failures](#failures)).
4. **Only `test_` symbols become functions.** AnalyzeTestBinary ignores other labels. A `bl` to a label without the `test_` prefix lands inside the previous function, gets no CallTarget, and becomes REX_FATAL. Test F's callee is therefore named `test_cr_so_fold_callee`.
5. **Category tag (cosmetic).** CategoryFromStem tags `instr_cr_so_fold` as `[floating_point]` because the stem contains `_f`.

## (c) Proposed tests/ppc/CMakeLists.txt change: ppc_tests_opt (text only, not applied)

The proposal turns everything after `get_property(TEST_MAPS ...)` into a function and calls it twice. Both suites share the assembled .bin/.map files.

```cmake
# One Catch2 suite generated from the shared test binaries.
# CONFIG: codegen options TOML (root keys) for recompile-tests --config.
# SPEC:   Catch2 test spec for test discovery (e.g. exclusions).
function(ppc_add_test_suite target gen_dir prefix)
    cmake_parse_arguments(ARG "" "CONFIG;SPEC" "" ${ARGN})
    file(MAKE_DIRECTORY ${gen_dir})
    set(config_args)
    if(ARG_CONFIG)
        set(config_args --config=${ARG_CONFIG})
    endif()
    add_custom_command(
        OUTPUT ${gen_dir}/ppc_test_functions.cpp
               ${gen_dir}/ppc_test_cases.cpp
               ${gen_dir}/ppc_test_decls.h
               ${gen_dir}/ppc_config.h
        COMMAND $<TARGET_FILE:rexglue> recompile-tests
                --output=${gen_dir}
                --bin-dir=${PPC_BIN_DIR}
                --asm-dir=${CMAKE_CURRENT_SOURCE_DIR}/asm
                ${config_args}
        DEPENDS ${TEST_BINS} ${TEST_MAPS} ${ASM_FILES} ${ARG_CONFIG} rexglue
        COMMENT "Generating Catch2 test code for ${target} with rexglue"
        VERBATIM
    )
    add_executable(${target}
        ${gen_dir}/ppc_test_functions.cpp
        ${gen_dir}/ppc_test_cases.cpp
    )
    target_include_directories(${target} PRIVATE ${PROJECT_SOURCE_DIR}/include ${gen_dir})
    target_link_libraries(${target} PRIVATE simde rexruntime fmt::fmt Catch2::Catch2WithMain)
    # Delay-load FidelityFX DLLs so the suite can run without them.
    if(WIN32)
        if(TARGET amd_fidelityfx_vk)
            target_link_options(${target} PRIVATE
                "LINKER:/DELAYLOAD:$<TARGET_FILE_NAME:amd_fidelityfx_vk>")
        endif()
        if(TARGET amd_fidelityfx_dx12)
            target_link_options(${target} PRIVATE
                "LINKER:/DELAYLOAD:$<TARGET_FILE_NAME:amd_fidelityfx_dx12>")
        endif()
        if(TARGET amd_fidelityfx_vk OR TARGET amd_fidelityfx_dx12)
            target_link_libraries(${target} PRIVATE delayimp)
        endif()
    endif()
    set_target_properties(${target} PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY $<TARGET_FILE_DIR:rexruntime>
    )
    if(UNIX AND NOT APPLE)
        set_target_properties(${target} PROPERTIES
            INSTALL_RPATH "$ORIGIN"
            BUILD_WITH_INSTALL_RPATH ON
        )
    endif()
    target_compile_options(${target} PRIVATE
        -UTRACY_ENABLE -UREXGLUE_ENABLE_PROFILING
        -UREXGLUE_ENABLE_PERF_COUNTERS -UREXGLUE_PROFILE_GUEST_FUNCTIONS
        -msse4.1 -mssse3
    )
    set(spec_args)
    if(ARG_SPEC)
        set(spec_args TEST_SPEC ${ARG_SPEC})
    endif()
    catch_discover_tests(${target}
        ${spec_args}
        TEST_PREFIX "${prefix}"
        PROPERTIES
            LABELS "ppc;instructions"
            TIMEOUT 60
    )
endfunction()

include(Catch)
ppc_add_test_suite(ppc_tests ${PPC_GEN_DIR} "ppc.")

option(REXGLUE_PPC_TESTS_OPT
       "Also build ppc_tests_opt: the asm tests recompiled with tests/ppc/opt_config.toml" ON)
if(REXGLUE_PPC_TESTS_OPT)
    # xer_as_local: XER does not cross calls, so the mtxer-in-caller test cannot see SO in the callee.
    ppc_add_test_suite(ppc_tests_opt ${CMAKE_BINARY_DIR}/tests/ppc/generated_opt "ppc_opt."
        CONFIG ${CMAKE_CURRENT_SOURCE_DIR}/opt_config.toml
        SPEC "~cr_so_fold.test_call")
endif()
```

Notes:
- The proposal depends on Agent 9's two recompile-tests fixes:
  - `--config` takes the SDK TOML directly;
  - REGISTER_OUT cr is dropped under cr_as_local.
  
  Without the second fix, the opt suite would also need `SPEC` exclusions for the six CR-output tests.
- The `set_source_files_properties(... GENERATED TRUE)` block can go: custom command outputs are marked GENERATED automatically.
- With the rerun tool (37B32713B7516402), both suites pass everything except vupkd3d128.test_short2_3. That test is an emitter gap and fails in both suites until the SHORT2 unpack is fixed. The seq tail-call tests pass in both suites.

## Files

- **SDK (tests/ppc only):**
  - `tests/ppc/opt_config.toml`
  - `tests/ppc/asm/instr_cr_so_fold.s` (test F)
- **bench/agent9/ppctests:**
  - scripts: `asm.ps1`, `gen.ps1`, `compile.ps1`, `link.ps1`, `runtests.ps1`, `extract.ps1`
  - `shim_logfloor.cpp`, `crso_config.toml`, `STATUS.md`, this README
- **Results in build/agent9/ppctests:**
  - `compare.md`: per-test, all variants
  - `failures.md`: generated code of non-passing tests and their callees
  - `instr_cr_so_fold.md`: all test F functions, per variant
  - `<variant>/gen.log`, `<variant>/results.xml`, `isolated.txt`, `excluded.txt`
  - `logs/compile.log`
  - `chainA.ps1`, `chainB.ps1`: the rerun's two compile chains, one cpu2 call per compile
