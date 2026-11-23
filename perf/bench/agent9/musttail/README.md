# musttail guest tail calls (`musttail_calls`)

## What changes
Flag: `ctx.config().musttailCalls` (TOML `musttail_calls`, default **false**; the field already existed, config.h/.cpp untouched).
With the flag on, a guest tail call
```c
	sub_8200ABCD(ctx, base);
	return;
```
is emitted as
```c
	[[clang::musttail]] return sub_8200ABCD(ctx, base);
```
The same applies to the `\t\t` form inside conditional tail branches and bctr jump tables. This is valid for `void` because all guest functions share one signature. clang must then lower each of these to a `jmp` at every optimization level, so the host stack stops growing along guest tail-call chains.

Code (all in `DimensionsRecomp/rexglue-sdk/src/codegen/builders/`):
- [context.cpp L186-303](<workspace>/DimensionsRecomp/rexglue-sdk/src/codegen/builders/context.cpp#L186-L303) holds a doc comment and the helpers `calls_setjmp`, `musttail_allowed`, `is_identifier`, `emit_tail_call_line`, `emit_tail_call`.
- [context.cpp L476, L485](<workspace>/DimensionsRecomp/rexglue-sdk/src/codegen/builders/context.cpp#L470-L490): `emit_conditional_branch` tail calls use `emit_tail_call_line`.
- [control_flow.cpp L23-25](<workspace>/DimensionsRecomp/rexglue-sdk/src/codegen/builders/control_flow.cpp#L23-L25): forward declarations.
- control_flow.cpp L47 and L56: `build_b` (2 sites) uses `emit_tail_call`.
- control_flow.cpp L153: the bctr jump-table entry that targets a function uses `emit_tail_call_line`.

Flag off, the output is **byte-identical**:
- `emit_tail_call_line` prints the same two lines as before.
- `emit_tail_call` is `emit_function_call(address)` followed by `\treturn;`, the original text (checked with a read-only `git diff`).
- emit_test checks this over every call form.

## Why it is valid where it is emitted

| requirement | finding |
|---|---|
| Identical signature | Every guest function and import is declared through `REX_FUNC(x)` = `void x([[maybe_unused]] PPCContext& __restrict ctx, uint8_t* base)` (pch_h.inja; `REX_EXTERN` = `extern "C" REX_FUNC`). `DEFINE_REX_FUNC` defines `__imp__name` with that signature, and `name` is a weak alias of it (non-Apple; the Apple variant already uses `[[clang::musttail]]`). The tail call passes the caller's own `ctx, base` through and returns void. |
| `__restrict` mismatch | Harmless. `pos_restrict.cpp`, a callee without `__restrict` plus an indirect call through `PPCFunc*` (func.h:30, no `__restrict`), is accepted. |
| No local with a non-trivial destructor | All generated locals (function_graph.cpp:725-756) are trivially destructible: `PPCRegister` ctr/r/f/temp, `PPCXERRegister`, `PPCCRRegister`, `PPCVRegister` v/vTemp, and `PPCContext env` (the setjmp copy). `static_assert`s in proof.cpp check this against the real pch. |
| Profiling prologue | `REX_FUNC_PROLOGUE` is empty unless `REXGLUE_PROFILE_GUEST_FUNCTIONS && REXGLUE_ENABLE_PROFILING`, which adds a Tracy `ZoneNamedN` (non-trivial destructor). In that build **clang rejects every musttail** (`neg_tracy.cpp`). Codegen cannot see the preprocessor state, which is why the template proposal below exists. |
| SEH | `SEH_TRY` is `__try {` (Win32) or `{ ::rex::SehGuard __seh_guard; try` (POSIX, guard with a destructor). A musttail cannot leave either one (`neg_seh.cpp`, `neg_try.cpp`), and the handler would no longer cover the callee. Such functions are skipped. |
| setjmp | `ppc_setjmp` saves this frame. If a callee longjmps after a musttail released the frame, the jump lands in a dead frame. Such functions are skipped. |
| Imports / thunks | Declared through the same `REX_FUNC`/`REX_EXTERN`, so they have the same signature (emit_test "import" form `__imp__XamInputGetState`). |
| Indirect calls | Not touched (bctr/bctrl through the function table keep their text). |

## Skip rules (the old text is kept)
1. **Flag off.**
2. **SEH-wrapped bodies**: `generateExceptionHandlers && fn.hasExceptionInfo()` with SEH scopes that are not empty. This is the same test `FunctionNode::recompile` uses to emit `SEH_TRY`.
3. **Functions that call setjmp**: `calls_setjmp()`. Any `b`/`bc` in the function whose target equals `setJmpAddress`, under either the relative or the absolute reading (conservative). A function that cannot be translated contributes nothing.
4. **Any call form other than a plain one-line call**. `emit_tail_call` rewrites only exactly `\t<identifier>(ctx, base);\n` as produced by `emit_function_call`. These keep their text plus `return;`: `ppc_longjmp`, `ppc_setjmp`, elided `__save*/__rest*` (inline register moves), the SEH-funclet register handoff, `REX_FATAL` for unresolved targets, multi-line output, member calls, and non-identifiers.
5. **Indirect tail calls**: these would need a template macro for the indirect form (for example `REX_TAIL_CALL_INDIRECT_FUNC`).
6. **Profiling builds** (`REXGLUE_PROFILE_GUEST_FUNCTIONS` + `REXGLUE_ENABLE_PROFILING`): this cannot be detected in codegen, so keep `musttail_calls` off there, or adopt the `REX_MUSTTAIL` macro below.

Hook contract: mid-asm hooks receive localized registers by reference (`r(N)`, `v(N)`, `cr()`, context.cpp:520-594). With musttail the frame is released before the tail-called function runs, so a hook must not keep those references after it returns.

## Evidence

### 1. emit_test: the live helper code, text in every case. `480 checks, 0 failures`
`extract_helpers.ps1` copies the helper block out of the current context.cpp (L213-304) into `gen_out/helpers.inc`. `emit_test.cpp` compiles it against a fake `BuilderContext`.

There are 15 call forms:
- rewritable: function, import, restgpr;
- must not be rewritten: longjmp, setjmp, save_rest_elided, funclet_handoff, fatal_unresolved, fatal_no_target, double_tab, member_call, two_calls, digit_start, bare_parens, no_newline.

There are 16 scenarios:
- flag_off, flag_off_seh, flag_on;
- seh_scopes, seh_no_scopes, seh_handlers_off, exc_not_seh;
- setjmp_bl, setjmp_b, setjmp_bc, bl_elsewhere, setjmp_bl_past_block_end, setjmp_bl_second_block, setjmp_unset, block_outside_image.

Each combination runs with and without preceding output: 15 × 16 × 2 = 480 checks.

### 2. proof.cpp: generated-style functions with the real `legodimensions_pch.h` and the game flags
The game flags include `-fasync-exceptions -march=x86-64-v3 -msse4.1`. Each cell is call_callee / jmp_callee / ret (instruction count). ctx_regs and locals contain one ordinary non-tail `bl`, so `call=1` is expected there.

| function | -O2 today | -O2 musttail | -O0 today | -O0 musttail |
|---|---|---|---|---|
| proof_ctx_regs | 1/1/0 (49) | 1/1/0 (49) | 2/0/1 (75) | 1/1/0 (71) |
| proof_locals | 1/1/0 (24) | 1/1/0 (24) | 2/0/1 (53) | 1/1/0 (51) |
| **proof_escaped** (hook gets `r31` by reference) | **1/0/1 (20)** | **0/1/0 (18)** | 1/0/1 (20) | 0/1/0 (17) |
| proof_cond (conditional tail calls) | 0/2/0 (10) | 0/2/0 (10) | 2/0/1 (26) | 0/2/0 (24) |
| proof_switch (jump table) | 0/1/0 (6) | 0/1/0 (6) | 3/0/1 (27) | 0/3/0 (25) |
| proof_vector | 0/1/0 (4) | 0/1/0 (4) | 1/0/1 (63) | 0/1/0 (58) |

- At -O2, clang already tail-calls when no local escapes. It does **not** when a localized register escapes to a hook: today it emits `call callee_c; nop; add rsp,40; pop; pop; ret`, and with musttail `add rsp,40; pop; pop; jmp callee_c`. See `proof_asm_excerpt.txt`.
- At -O0 every tail site becomes a jmp.
- `-O2 -fstack-protector-strong` with musttail is accepted and still emits jmp (escaped: 30 instructions, jmp 1).
- Full asm is in `gen_out/proof_*.s`; counts are in `proof_counts.txt`.

### 3. Acceptance (`-fsyntax-only`, game flags, `acceptance.txt`)

| file | expected | result | clang diagnostic |
|---|---|---|---|
| neg_tracy.cpp (real Tracy prologue) | reject | rejected | jump exits scope of variable with non-trivial destructor (expanded from `REX_FUNC_PROLOGUE`) |
| neg_seh.cpp | reject | rejected | jump exits __try block |
| neg_try.cpp | reject | rejected | jump exits try block / scope of variable with non-trivial destructor |
| neg_sig.cpp | reject | rejected | target function has different number of parameters; requires the return value to be a function call |
| pos_restrict.cpp | accept | accepted | none |

### 4. A real LEGO TU (`real_tu.ps1` → `real_tu.txt`)
The TU is `legodimensions_recomp.61.cpp`, with 336 functions and 139 tail-call sites, all unconditional. Its text was transformed exactly as `emit_tail_call` prints it and compiled with the real game flags.

| | -O3 today | -O3 musttail | -O0 today | -O0 musttail |
|---|---|---|---|---|
| compiles | yes | **yes** | yes | **yes** |
| guest tail `jmp` | 73 | **101** | 0 | **139** |
| call → epilogue → ret (tail call not lowered) | 19 | **0** | 86 | **0** |
| `ret` | 308 | 277 | 507 | 408 |
| calls to guest functions | 1126 | 1095 | 1242 | 1103 |
| compile time (noisy) | 20.9 s | 17.4 s | 11.8 s | 14.5 s |

- The 139 sites contain 101 distinct (function, target) pairs: 38 to `sub_*` and 63 to `__restgprlr_*`/`__savegpr*` helpers.
- At -O3, branch folding merges identical tail jumps. With musttail all 101 pairs become `jmp`: 38 to `sub_`, 63 to helpers.
- Today clang already tail-calls all 38 `sub_` pairs, but only 35 of the 63 restore/save-helper tail calls.
- At -O0 today none of the 139 is a jmp; with musttail all 139 are (139 `# TAILCALL`).

### 5. Baseline sites across the LEGO generated code (`count_sites.ps1`)
- 438 TUs, 165,023 functions.
- **63,167 sites affected**: 63,119 unconditional `b`, 48 conditional, 0 jump-table.
- 0 functions with `SEH_TRY` and 0 with `ppc_setjmp`, so in LEGO no function falls under skip rules 2 or 3.

## Template proposal (not done: templates are off-limits)
For `pch_h.inja`:
```c
#if defined(__clang__) && !(defined(REXGLUE_PROFILE_GUEST_FUNCTIONS) && defined(REXGLUE_ENABLE_PROFILING))
#define REX_MUSTTAIL [[clang::musttail]]
#else
#define REX_MUSTTAIL
#endif
```
Then `kMustTailReturn` becomes `"REX_MUSTTAIL return "`. That is a one-line codegen change. A profiling build or a non-clang compiler would then get a plain `return f(ctx, base);`, which is still valid for void, instead of a compile error. Also suggested: move the two helper declarations from control_flow.cpp into builder_context.h, which this task was not allowed to edit.

## Test
`DimensionsRecomp/rexglue-sdk/tests/ppc/asm/seq_tailcall_musttail.s` covers:
- an unconditional tail chain (`b` into a function that does `addi r3,5; blr`);
- a conditional tail call, both taken and not taken.

It was not run here, because building ppc_tests is not allowed. The ppc suite generates with default flags (off). Exercising the ON path needs `musttail_calls = true` in the test generator config.

## Reproduce (one compile at a time, through cpu2)
```powershell
powershell -NoProfile -File bench/agent9/cpu2.ps1 -File bench/agent9/musttail/run.ps1 *> bench/agent9/musttail/run.log      # emit_test + proof + acceptance
powershell -NoProfile -File bench/agent9/musttail/proof_stats.ps1                                                             # text only: proof_counts.txt, proof_asm_excerpt.txt
powershell -NoProfile -File bench/agent9/cpu2.ps1 -File bench/agent9/musttail/real_tu.ps1 *> bench/agent9/musttail/real_tu.log  # real TU, -O3 and -O0
powershell -NoProfile -File bench/agent9/musttail/count_sites.ps1                                                             # text only: LEGO site counts
```

## Batch 2 (Agent 10's ask C, from Agent 9 at 21:01)

The batch-2 scripts hold no CPU slot themselves. Each compile (and each test run) takes ONE Agent 9
slot through `slot1.ps1`, which follows the same rules as `cpu2.ps1`: it waits while
`bench/agent9/QUIET` exists, takes whichever slot mutex is free, and checks QUIET again once it holds
the slot. A quiet window therefore pauses the loops between compiles.

### 1. Regenerated musttail variant
- Command: `build\agent9\gen.ps1 -Variant musttail -Options 'musttail_calls = true'`, run 21:05-21:22.
- Result: exit 0. The tool itself ran 151.9 s, after waiting 881 s for a slot. It used the rexglue.exe built at 21:08 (sha A8036AC8947D70BA).
- Output: `build/agent9/generated/musttail/default`, 888 files, 468.4 MB. Log: `gen_musttail.log`.

### 2. Tail-chain depth test (`chain.cpp`, `chain_hook.cpp`, `chain.ps1` → `chain.txt`)
The test runs `chain_a → chain_b → chain_c → chain_a …` for 1,000,000 hops. Each function is written the way the generator writes them:
- It uses the real `legodimensions_pch.h`: `DEFINE_REX_FUNC` is a weak alias from `name` to the body `__imp__name`, with signature `(PPCContext& __restrict, uint8_t*)`, plus `REX_FUNC_PROLOGUE`.
- It has a `PPCRegister r31{}` local.
- It ends with a guest tail call after `if (ctx.r3.s64 <= 0) return;`.

With `ESCAPE=1`, `r31` is passed by reference to an opaque hook in another TU (the mid-asm-hook shape). The builds use the real game flags and the default 1 MB main-thread stack. All 8 builds compiled and linked with the real headers, so the stand-in was not needed.

| build | local escapes | today's text | `musttail_calls` text |
|---|---|---|---|
| -O0 | no  | **STACK OVERFLOW** (0xC00000FD); 3 × `call` | **PASS**, 1,000,000 hops; 3 × `jmp … # TAILCALL` |
| -O0 | yes | **STACK OVERFLOW**; 3 × `call` | **PASS**; 3 × `jmp … # TAILCALL` |
| -O2 | no  | PASS: clang sibcalls on its own (3 × `jg … # TAILCALL`) | PASS; 3 × `jg … # TAILCALL` |
| -O2 | yes | **STACK OVERFLOW**; 3 × `call` | **PASS**; 3 × `jmp … # TAILCALL` |

The `call chain_a` left in every build is `main`'s entry call. At -O2 with no escape, clang folds
`if (..) return; f()` into a conditional tail call, `jg f`, with or without the attribute. Today's text survives a deep guest
tail chain only when clang happens to sibcall it (-O2 and no escaped local). With musttail it survives at every
optimisation level, including when a local escapes.

### 3. Text check, musttail vs flag-off (`textcheck.ps1` → `textcheck.txt`), pending
No compile. Every function of the musttail variant is compared with the same function of the
flag-off variant (`build/agent9/generated/off`), after the off text is rewritten exactly as
`emit_tail_call` prints it. Functions that also differ for reasons unrelated to tail calls (the 21:08
exe adds the SO fold) are split out by comparing per-function musttail-site counts. The quiet windows
killed it twice (21:57, 22:29); it runs in one slot after the second window.

### 4. Heavy TUs on identical function sets: baseline vs batch (`heavy_batch.ps1` → `heavy_batch.txt`), pending
Agent 9's plan from 22:26 replaces the musttail-only alltu/heavy runs.
- **baseline**: `build/agent2/gen-noflag/default` (pin codegen). TU N is compiled as-is.
- **batch**: `build/agent9/generated/batch/default`, with all Agent 9 options on: skip_lr,
  ctr/xer/reserved/cr_as_local, cr_compare_so_zero, rlwinm, flush elision, musttail and vmx.
- **TUs**: N = 304, 233, 52 and 61.

The batch variant is partitioned differently, because localization shrinks the code. So
`gen_out/batch_tuN.cpp` holds baseline TU N's `DEFINE_REX_FUNC` list, in TU N's order, with each
function copied from the batch variant. The script fails if a function is missing, defined twice, or
its chunk is not one whole function.

Each generated TU starts with only `#include "legodimensions_funcs.K.h"`, and that header declares
only what TU K references. So `batch_tuN.cpp` starts with the union of the `#include` lines of the
batch TUs its functions come from, rather than the preamble of a single batch TU.
`DECLARE_REX_FUNC` is two `extern "C"` declarations, so repeating them is legal.

Flags are the real game Release entry of `legodimensions_recomp.61.cpp` in
`build/dev/compile_commands.json`, the entry `env/compile-one.ps1` picks (`game_flags.ps1`,
`$GameFlagsFull`: `-O3 -DNDEBUG -gline-tables-only -march=x86-64-v3 -msse4.1 -fasync-exceptions …`).
Two changes are made:
- the `-I…/rexlego/generated/default` flag points at the variant;
- the CMake PCH is replaced by a PCH of that variant's own `legodimensions_pch.h`, built with the same
  flags. Each variant gets its own PCH because localization rewrites the batch PCH.

Each compile records exit code, wall time, CPU time, `.obj` bytes, `.text` bytes (the sum of
`.text*` sections in `llvm-objdump -h`) and musttail sites. Each compile takes one slot.

### 5. Dropped and optional
- Dropped by Agent 9 at 22:26: the musttail-variant `alltu` (about 440 TUs at one slot is too long;
  Agent 2's full build compiles every TU anyway) and `heavy.ps1` (musttail vs baseline at -O2).
  `batch2.ps1` and `heavy.ps1` are superseded.
- Lowest priority, only when slots are free: `alltu.ps1 -Variant batch` → `alltu_batch.tsv` and
  `alltu_batch_summary.txt`. This is a `-fsyntax-only` compile of every batch recomp TU with the
  game Release flags and the variant's own PCH. It can be paused and resumed with `-Resume`.

### Reproduce (batch 2)
```powershell
powershell -NoProfile -File bench/agent9/musttail/chain.ps1                       # 2. chain depth test
powershell -NoProfile -ExecutionPolicy Bypass -Command ". .\bench\agent9\musttail\slot1.ps1; Invoke-InSlot { powershell -NoProfile -ExecutionPolicy Bypass -File bench/agent9/musttail/textcheck.ps1 *> bench/agent9/musttail/textcheck.log }"   # 3.
powershell -NoProfile -File bench/agent9/musttail/heavy_batch.ps1 *> bench/agent9/musttail/heavy_batch.log      # 4. [-Tus '304,233,52,61'] [-Batch <dir>]
powershell -NoProfile -File bench/agent9/musttail/alltu.ps1 -Variant batch *> bench/agent9/musttail/alltu_batch.log  # 5. [-Resume]
```
