# Flush-mode switch elision (`flush_mode_elision`)

Every FP/VMX builder starts with `ctx.emit_set_flush_mode(enable)`. When `ctx.csrState` differs from the
required mode, this emits `ctx.fpscr.enableFlushMode[Unconditional]()` (VMX: MXCSR FTZ|DAZ on) or
`disableFlushMode[Unconditional]()` (FPU: off). There are 75 such builders.

With `flush_mode_elision = true` (`RecompilerConfig::flushModeElision`, default **false**), the 23 builders
below call `emitFlushModeUnlessIndependent(ctx, enable)` from `src/codegen/builders/flush_mode.h`.
- Flag on: it emits nothing and leaves `ctx.csrState` unchanged, so the next mode-dependent op still
  switches exactly when it needs to.
- Flag off: it calls `ctx.emit_set_flush_mode(enable)`, so the generated text is byte-identical by
  construction.

A site is elided only if its emitted statements give **bit-identical results with FTZ/DAZ on or off,
under all 4 rounding modes**. The harness below checks this by machine.

## SDK files changed (DimensionsRecomp/rexglue-sdk)
| file | change |
|---|---|
| `src/codegen/builders/flush_mode.h` | new: `emitFlushModeUnlessIndependent` |
| `src/codegen/builders/floating_point.cpp` | `#include "flush_mode.h"` (line 13); sites 23 fabs, 30 fnabs, 37 fneg, 48 fmr, 54 fcfid, 71 fctidz, 91 fctiwz |
| `src/codegen/builders/memory.cpp` | include (13); sites 224 lfd, 233 lfdx, 263 lfdu, 273 lfdux, 451 stfd, 461 stfdx, 471 stfdux, 480 stfiwx, 510 stfdu |
| `src/codegen/builders/vector.cpp` | include (13); sites 221 vrfin, 237 vrfiz, 759 vctsxs, 771 vcfsx, 787 vcfux, 805 vctuxs, 1335 vpkd3d128 |

Line numbers are as of 2026-11-21 21:31. Another agent edits vector.cpp, so its line numbers can drift.
Aliases are elided with their builders:
- vcfpsxws128 uses vctsxs;
- vcfpuxws128 uses vctuxs;
- vcsxwfp128 uses vcfsx;
- vcuxwfp128 uses vcfux;
- vrfin128 uses vrfin;
- vrfiz128 uses vrfiz.

All three TUs pass `bench/agent9/syntax-check.ps1` (exit 0, 0 errors).

## How to run
```
powershell -NoProfile -File bench/agent9/cpu2.ps1 -File bench/agent9/flush/build.ps1
#   -NoHarness | -NoScan | -HarnessArgs nosweep | -HarnessArgs <scale> | -ScanList build_fabs,build_fmr,...
```
- `flush_harness.cpp` → `flush_harness.exe` → `results.txt`. Takes about 11 minutes on one thread. Exits 1 if an
  elided site fails or a control goes undetected.
- `scan_baseline.cpp` → `scan_baseline.exe <generated dir> [builder list]` → `baseline_scan.txt`. Takes about 10 s.

Compiler flags are those of the game's generated-code TUs (`build/baseline/compile_commands.json`):
- clang 23.1.6;
- `-O3 -DNDEBUG -std=gnu++23 -D_DLL -D_MT -Xclang --dependent-lib=msvcrt -msse4.1 -fasync-exceptions -march=x86-64-v3`;
- `-DNOMINMAX -DWIN32_LEAN_AND_MEAN`.

The harness prints this build line:
`__AVX2__=1 __FMA__=1 __SSE4_1__=1 SIMDE_X86_SSE4_1_NATIVE=1 SIMDE_X86_AVX2_NATIVE=1`.
So simde lowers to native SSE4.1/AVX2 instructions, as it does in the game.

Headers:
- The harness uses the dev tree's `include/` and `thirdparty/simde`.
- The baseline game build used the installed SDK (`build/sdk/install/include`). Its `context.h` is identical.
- Its `intrinsics.h` differs, notably in `simde_mm_vctuxs`. The harness therefore tests **both** vctuxs bodies:
  - the dev one;
  - `old_sdk::simde_mm_vctuxs`, copied verbatim from `install/include/rex/ppc/intrinsics.h:193-223`.

## Method
- **Exact statements.** Each op body is the text the builder prints:
  - The format strings are copied and the operands filled in as the builder does.
  - `REX_LOAD_*`/`REX_STORE_*`/`REX_MM_STORE_*` are expanded the way `resources/templates/codegen/pch_h.inja` expands them.
  - The MMIO store is a logging stub, and its log is compared.
  - The vct/vcf immediates are printed as `1u<<k`, or `ldexp(1,-k)` as a hex float bit pattern, exactly as the builder prints them.
- **Modes.** Every case is evaluated with:
  - the reference MXCSR `0x1F80 | RC<<13` (flush off);
  - ref|FTZ, ref|DAZ and ref|FTZ|DAZ;
  - each of the 4 rounding modes (RN, RM, RP, RZ).

  That is 16 evaluations per case. Each run is compared with the flush-off reference for the same RC.
- **State compared, bit-exact (NaN payloads included).** The full 352-byte context snapshot:
  - v1-v4, vTemp, r3, r4, f1-f4, temp, cr0-cr7, ea;
  - fpscr csr, vscr_sat;
  - the MMIO log and 128 bytes of guest memory.

  MXCSR sticky exception flags are recorded but only informational ("flag diffs"). No guest-visible path
  reads them: `mffs` returns only RN (`loadFromHost`), and every exception is masked (`InitHost`).
- **Inputs:**
  - 342 double / 330 float special patterns: each base value with both signs and ±1 ulp.
    - Base values: 0, denormal min/max, normal min/max, 0.5/1.5/2.5 ties, 1, inf, and qNaN/sNaN with payloads.
    - Integer boundaries as doubles and floats: 2^31, 2^31−1, 2^31±0.5, 2^32, 2^32−1, 2^63, 2^64, 65504/65520.
  - Scalar ops: every single special, then all ordered pairs of specials in operands 1-2, with operand 3
    cycling through the specials.
  - Plus random patterns: random bits, small half-integers, and specials ±2 ulp.
  - Vector cases put a different special in each lane, plus random lanes.
  - Every immediate: k = 0..31 for vct*/vcf*, and every vpkd3d128 type/shift/rotate combination
    except type 4 shift 3 (see the notes).
- **Exhaustive sweeps.** All 2^24 f32 patterns with exponent 0 (every ±denormal and ±0), under all 4 RC,
  FTZ|DAZ vs off, for:
  - vrfin, vrfiz, vrfim and vrfip;
  - vctsxs, vctuxs (dev) and vctuxs (old SDK) at every k = 0..31;
  - vpkd3d128 types 0, 2, 3, 5 and 6 at rotations 0..3.
- **Controls that must fail** (they prove the harness sees mode dependence): frsp, fcmpu, fadd, lfs and
  vrfim. All 5 were detected.

## Result
```
RESULT: PASS | sites 75 (elide 23, control 5, keep 47) | elide failures 0 | controls missed 0 |
        keep sites with no dependence seen 0 | 368252256 case evals | 644.0 s
```
Every KEEP site showed real mode dependence. None of them is a missed elision.

| # | op | file:line | verdict | cases | evals | mism FTZ / DAZ / both | sweep lane-evals / mism | reason |
|---|---|---|---|---|---|---|---|---|
| 0 | fabs | floating_point.cpp:23 | **ELIDE** | 210342 | 3365472 | 0 / 0 / 0 | - | integer AND on the bit pattern |
| 1 | fnabs | floating_point.cpp:30 | **ELIDE** | 210342 | 3365472 | 0 / 0 / 0 | - | integer OR on the bit pattern |
| 2 | fneg | floating_point.cpp:37 | **ELIDE** | 210342 | 3365472 | 0 / 0 / 0 | - | integer XOR on the bit pattern |
| 3 | fmr | floating_point.cpp:48 | **ELIDE** | 210342 | 3365472 | 0 / 0 / 0 | - | 64-bit register copy, no arithmetic |
| 4 | fcfid | floating_point.cpp:54 | **ELIDE** | 210342 | 3365472 | 0 / 0 / 0 | - | cvtsi2sd: integer input; result is 0 or \|x\|>=1, never denormal (RC is unchanged by the switch) |
| 5 | fctid | floating_point.cpp | KEEP | 210342 | 3365472 | 0 / 53843 / 53843 | - | cvtsd2si honours RC: +denormal gives 1 under RP (-1 under RM) without DAZ |
| 6 | fctidz | floating_point.cpp:71 | **ELIDE** | 210342 | 3365472 | 0 / 0 / 0 | - | cvttsd2si: denormal gives 0 either way; compares are against normal constants (flag diffs 430744, informational) |
| 7 | fctiw | floating_point.cpp | KEEP | 210342 | 3365472 | 0 / 53843 / 53843 | - | cvtsd2si honours RC: denormal gives ±1 under RP/RM without DAZ |
| 8 | fctiwz | floating_point.cpp:91 | **ELIDE** | 210342 | 3365472 | 0 / 0 / 0 | - | cvttsd2si: denormal gives 0 either way; compares against normal constants (flag diffs 430744) |
| 9 | frsp | floating_point.cpp | control ✔ | 210342 | 3365472 | 186127 / 186127 / 186127 | - | cvtsd2ss: DAZ/FTZ |
| 10 | fcmpu | floating_point.cpp | control ✔ | 216964 | 3471424 | 0 / 36520 / 36520 | - | ucomisd: DAZ makes denormal == 0 (fcmpo uses build_fcmpu) |
| 11 | fadd | floating_point.cpp | control ✔ | 216964 | 3471424 | 33928 / 139190 / 139786 | - | addsd: DAZ/FTZ |
| 12 | fadds | floating_point.cpp | KEEP | 216964 | 3471424 | 95558 / 114969 / 115048 | - | arithmetic + cvtsd2ss |
| 13 | fsub | floating_point.cpp | KEEP | 216964 | 3471424 | 33716 / 139244 / 139800 | - | arithmetic |
| 14 | fsubs | floating_point.cpp | KEEP | 216964 | 3471424 | 95579 / 114890 / 114968 | - | arithmetic + cvtsd2ss |
| 15 | fmul | floating_point.cpp | KEEP | 216964 | 3471424 | 88586 / 172270 / 185222 | - | arithmetic |
| 16 | fmuls | floating_point.cpp | KEEP | 216964 | 3471424 | 127100 / 138992 / 138992 | - | arithmetic + cvtsd2ss |
| 17 | fdiv | floating_point.cpp | KEEP | 216964 | 3471424 | 63614 / 212035 / 231292 | - | arithmetic |
| 18 | fdivs | floating_point.cpp | KEEP | 216964 | 3471424 | 71694 / 188386 / 188386 | - | arithmetic + cvtsd2ss |
| 19 | fmadd | floating_point.cpp | KEEP | 497856 | 7965696 | 91661 / 320952 / 321986 | - | FMA |
| 20 | fmadds | floating_point.cpp | KEEP | 497856 | 7965696 | 154094 / 231091 / 231137 | - | FMA + cvtsd2ss |
| 21 | fmsub | floating_point.cpp | KEEP | 497856 | 7965696 | 91645 / 320190 / 321200 | - | FMA |
| 22 | fmsubs | floating_point.cpp | KEEP | 497856 | 7965696 | 154046 / 232601 / 232647 | - | FMA + cvtsd2ss |
| 23 | fnmadd | floating_point.cpp | KEEP | 497856 | 7965696 | 91661 / 320952 / 321986 | - | FMA |
| 24 | fnmadds | floating_point.cpp | KEEP | 497856 | 7965696 | 154094 / 231091 / 231137 | - | FMA + cvtsd2ss |
| 25 | fnmsub | floating_point.cpp | KEEP | 497856 | 7965696 | 91645 / 320190 / 321200 | - | FMA |
| 26 | fnmsubs | floating_point.cpp | KEEP | 497856 | 7965696 | 154046 / 232601 / 232647 | - | FMA + cvtsd2ss |
| 27 | fres | floating_point.cpp | KEEP | 210342 | 3365472 | 27314 / 135000 / 135000 | - | divsd + cvtsd2ss |
| 28 | frsqrte | floating_point.cpp | KEEP | 210342 | 3365472 | 9291 / 170863 / 170863 | - | sqrtsd/divsd + cvtsd2ss |
| 29 | fsqrt | floating_point.cpp | KEEP | 210342 | 3365472 | 0 / 215372 / 215372 | - | sqrtsd: DAZ |
| 30 | fsqrts | floating_point.cpp | KEEP | 210342 | 3365472 | 43007 / 150779 / 150779 | - | sqrtsd + cvtsd2ss |
| 31 | fsel | floating_point.cpp | KEEP | 497856 | 7965696 | 0 / 171484 / 171484 | - | -denormal >= 0.0 is true under DAZ |
| 32 | lfd | memory.cpp:224 | **ELIDE** | 102312 | 1636992 | 0 / 0 / 0 | - | 64-bit integer load |
| 33 | lfdx | memory.cpp:233 | **ELIDE** | 68208 | 1091328 | 0 / 0 / 0 | - | 64-bit integer load |
| 34 | lfs | memory.cpp | control ✔ | 101880 | 1630080 | 0 / 83964 / 83964 | - | cvtss2sd reads float denormals (DAZ) |
| 35 | lfsx | memory.cpp | KEEP | 67920 | 1086720 | 0 / 55976 / 55976 | - | cvtss2sd (DAZ) |
| 36 | lfdu | memory.cpp:263 | **ELIDE** | 34104 | 545664 | 0 / 0 / 0 | - | 64-bit integer load + integer EA update |
| 37 | lfdux | memory.cpp:273 | **ELIDE** | 34104 | 545664 | 0 / 0 / 0 | - | 64-bit integer load + integer EA update |
| 38 | lfsu | memory.cpp | KEEP | 33960 | 543360 | 0 / 27988 / 27988 | - | cvtss2sd (DAZ) |
| 39 | lfsux | memory.cpp | KEEP | 33960 | 543360 | 0 / 27988 / 27988 | - | cvtss2sd (DAZ) |
| 40 | stfd | memory.cpp:451 | **ELIDE** | 204624 | 3273984 | 0 / 0 / 0 | - | 64-bit integer store (the MMIO path is integer too) |
| 41 | stfdx | memory.cpp:461 | **ELIDE** | 136416 | 2182656 | 0 / 0 / 0 | - | 64-bit integer store (the MMIO path is integer too) |
| 42 | stfdux | memory.cpp:471 | **ELIDE** | 34104 | 545664 | 0 / 0 / 0 | - | 64-bit integer store + integer EA update |
| 43 | stfiwx | memory.cpp:480 | **ELIDE** | 136416 | 2182656 | 0 / 0 / 0 | - | 32-bit integer store of the low word |
| 44 | stfs | memory.cpp | KEEP | 204624 | 3273984 | 172146 / 44376 / 172146 | - | cvtsd2ss |
| 45 | stfsx | memory.cpp | KEEP | 136416 | 2182656 | 114764 / 29584 / 114764 | - | cvtsd2ss |
| 46 | stfdu | memory.cpp:510 | **ELIDE** | 34104 | 545664 | 0 / 0 / 0 | - | 64-bit integer store + integer EA update |
| 47 | stfsu | memory.cpp | KEEP | 34104 | 545664 | 28691 / 7396 / 28691 | - | cvtsd2ss |
| 48 | stfsux | memory.cpp | KEEP | 68208 | 1091328 | 57382 / 14792 / 57382 | - | cvtsd2ss |
| 49 | vaddfp | vector.cpp | KEEP | 208900 | 3342400 | 82992 / 306502 / 307830 | - | addps |
| 50 | vsubfp | vector.cpp | KEEP | 208900 | 3342400 | 83528 / 318190 / 319642 | - | subps |
| 51 | vmulfp128 | vector.cpp | KEEP | 208900 | 3342400 | 274340 / 422255 / 449598 | - | mulps |
| 52 | vmaddfp | vector.cpp | KEEP | 158900 | 2542400 | 146041 / 263542 / 263846 | - | mulps/addps |
| 53 | vnmsubfp | vector.cpp | KEEP | 158900 | 2542400 | 143449 / 259746 / 260114 | - | mulps/subps |
| 54 | vmaxfp | vector.cpp | KEEP | 208900 | 3342400 | 0 / 356172 / 356172 | - | maxps treats denormals as 0 under DAZ |
| 55 | vminfp | vector.cpp | KEEP | 208900 | 3342400 | 0 / 396884 / 396884 | - | minps treats denormals as 0 under DAZ |
| 56 | vrefp | vector.cpp | KEEP | 145243 | 2323888 | 9264 / 385610 / 390658 | - | divps |
| 57 | vrsqrtefp | vector.cpp | KEEP | 145243 | 2323888 | 0 / 425128 / 425128 | - | sqrtps/divps |
| 58 | vexptefp | vector.cpp | KEEP | 145243 | 2323888 | 82213 / 243683 / 243683 | - | roundps(-inf)/subps/mulps |
| 59 | vlogefp | vector.cpp | KEEP | 145243 | 2323888 | 0 / 322680 / 322680 | - | calls the CRT log2f (host code) |
| 60 | vmsum3fp128 | vector.cpp | KEEP | 208900 | 3342400 | 75061 / 131999 / 132080 | - | dpps |
| 61 | vmsum4fp128 | vector.cpp | KEEP | 208900 | 3342400 | 61616 / 111783 / 111965 | - | dpps |
| 62 | vrfim | vector.cpp | control ✔ | 145243 | 2323888 | 0 / 322940 / 322940 | 67108864 / 33554428 | roundps(-inf): -denormal gives -1 without DAZ |
| 63 | vrfin | vector.cpp:221 | **ELIDE** | 145243 | 2323888 | 0 / 0 / 0 | 67108864 / 0 | roundps(nearest), explicit imm: ±denormal gives ±0 either way |
| 64 | vrfip | vector.cpp | KEEP | 145243 | 2323888 | 0 / 322680 / 322680 | 67108864 / 33554428 | roundps(+inf): +denormal gives +1 without DAZ |
| 65 | vrfiz | vector.cpp:237 | **ELIDE** | 145243 | 2323888 | 0 / 0 / 0 | 67108864 / 0 | roundps(zero), explicit imm: ±denormal gives ±0 either way |
| 66 | vcmpbfp | vector.cpp | KEEP | 417800 | 6684800 | 0 / 145024 / 145024 | - | cmpps treats denormals as 0 under DAZ |
| 67 | vcmpeqfp | vector.cpp | KEEP | 417800 | 6684800 | 0 / 182832 / 182832 | - | cmpps treats denormals as 0 under DAZ |
| 68 | vcmpgefp | vector.cpp | KEEP | 417800 | 6684800 | 0 / 102128 / 102128 | - | cmpps treats denormals as 0 under DAZ |
| 69 | vcmpgtfp | vector.cpp | KEEP | 417800 | 6684800 | 0 / 103248 / 103248 | - | cmpps treats denormals as 0 under DAZ |
| 70 | vctsxs | vector.cpp:759 | **ELIDE** | 991680 | 15866880 | 0 / 0 / 0 | 2147483648 / 0 | denormal × 2^k (k<=31) is <1, so cvttps gives 0; saturation is bitwise (flag diffs 5018284) |
| 71 | vcfsx | vector.cpp:771 | **ELIDE** | 991680 | 15866880 | 0 / 0 / 0 | - | cvtdq2ps gives 0 or \|x\|>=1; × 2^-k (k<=31) stays normal |
| 72 | vcfux | vector.cpp:787 | **ELIDE** | 991680 | 15866880 | 0 / 0 / 0 | - | integer ops + cvtdq2ps give 0 or >=1; × 2^-k stays normal |
| 73 | vctuxs | vector.cpp:805 | **ELIDE** | 1983360 | 31733760 | 0 / 0 / 0 | 4294967296 / 0 | maxps(x,0) then cvttps: a denormal gives 0 either way. Both the dev and the old-SDK body pass (flag diffs 10125896) |
| 74 | vpkd3d128 | vector.cpp:1335 | **ELIDE** | 2600490 | 41607840 | 0 / 0 / 0 | 1342177280 / 0 | compares against normal constants, selects, integer ops, cvttss2si (flag diffs 8323656) |

How to read the columns:
- *cases* is the number of input tuples; *evals* = cases × 16 (4 RC × {ref, FTZ, DAZ, FTZ+DAZ}).
- *mism* counts test evaluations whose snapshot differs from the reference.
- *sweep* counts lanes over the exhaustive exponent-0 sweep, × 4 RC.

`results.txt` also lists the first differing field for each dependent site.

## Baseline impact (`baseline_scan.txt`)
`scan_baseline` replays the codegen csrState machine over the baseline generated code
(`baseline/DimensionsRecomp/rexlego/generated/default`: 440 files, 165,023 functions, 6,983,219 instructions).
The rules come from the sources:
- reset to Unknown at function entry (function_graph.cpp:564), at every emitted `loc_X:` label (:597), and
  after `bl` to a function/import (control_flow.cpp:84), `blrl` and `bctrl`;
- `bl` to an internal label is a `goto` and does not reset;
- a switch is emitted iff `csrState != required`, with the `Unconditional` suffix iff the state is known.

- **Validation PASS.** The replay with the flag off reproduces every one of the 136,802 actual switch lines at
  the same instruction, with the same text: 0 mismatches and 0 unattributed lines.
- **Sites affected.** The 23 elided builders are reached by **113,605** baseline instructions, out of 716,428
  instructions at the 75 builders. Today they carry 38,850 switch lines.
- **Effect of the flag.** Switch lines drop from 136,802 to **106,248** (**−30,554, −22.3%**).
  - Unconditional switches: 1,749 → 1,675.
  - Conditional switches by cause: entry 6,325 → 5,067, label 64,591 → 50,057, call 64,137 → 49,449.
  - The other 8,296 switches move to the next mode-dependent op.
- **Dataflow estimate, for a possible pass in function_graph.cpp.** This is an optimistic per-function
  fixpoint: each label takes the meet of its gotos and its fallthrough; calls reset the state; code after an
  unconditional goto, a `return;` or a jump-table trap is dead.
  - Result: 99,793 switch lines with the flag off and **76,587** with it on.
  - It removes most label-caused switches: 64,591 → 27,454 with the flag off.
  - Call resets (64,137) remain. Removing them would need a cross-function convention.
  - Labels with a known state: 59,710 of 404,446.

## Accepted non-equivalence (and why it is not guest-visible)
After an elided op, MXCSR can stay in the other flush mode longer than before. Example: `fmr` no longer turns
FTZ/DAZ off after a VMX op. Host code on the guest thread runs on whatever MXCSR the guest left. That
includes imports/kernel exports, MMIO handlers (`REX_MM_STORE_*`), mid-asm hooks, SEH/trap handlers and the
CRT `log2f` (vlogefp). Such code could see FTZ/DAZ set at points where it used to be clear, or the reverse.
Why this does not change guest-visible behaviour:
1. **Already path-dependent today.** Integer ops, branches, loads/stores of GPRs and calls never switch the
   mode. Host code reached via `bl` therefore already runs in whatever mode the last FP/VMX op set: for
   example after a `vaddfp` followed by integer code. The elision only lengthens these stretches. It creates
   no state the old code could not be in.
2. **The flush bits are not architected guest state.**
   - `mffs` returns only RN (`loadFromHost`).
   - `mtfsf`/`mtfsfi` (`storeFromGuest`) change only RN and keep the flush bits.
   - Every MXCSR exception is masked (`InitHost`), so the sticky flags never trap and nothing reads them.
3. **Every mode-dependent op still establishes its mode.** `csrState` is left untouched by elided ops, so it
   stays accurate. The 52 kept builders emit exactly the switch they need: unconditional when the state is
   known, conditional on the cached csr when it is Unknown (after labels, calls and entry).
4. **The saved/restored paths are unchanged.** `restoreGuestBits` (ExecuteTrap, function_dispatcher.cpp:183;
   RestoreNonVolatiles, context.h:477) restores RN and the flush bits as before. Other host threads have their
   own MXCSR.

Residual risks (outside this proof):
- Host FP code that is denormal-sensitive and called right after an elided op. It already sees either mode
  today, depending on the path.
- The harness checks the statements as compiled with the game's flags. The per-site arguments in the table
  are analytic, so they also hold for any other lowering of the same statements.
- LLVM assumes the default FP environment and may constant-fold or move FP ops across the csr write. This
  issue exists today and is not changed by the elision.

## Notes / open items
- **vpkd3d128 type 4 (NORMSHORT4), shift 3: pre-existing bug, not related to flush mode.** That case
  writes `u16[8..9]` of a 128-bit vector (u16[0..7]), which is out of bounds. The harness excludes that
  combination.
- **vlogefp** calls the CRT `log2f`, which is host code. It is kept, and its result depends on the mode.
- **Installed vs dev `intrinsics.h`.** The baseline game build used the installed SDK, whose
  `simde_mm_vctuxs` differs from the dev tree. Both bodies are proven, so the elision is valid for either.
- **Not machine-checked:** the asm test `tests/ppc/asm/instr_flush_independent.s` was not written, and no SDK
  target was built. Agent 9 runs the tool rebuild, the T1 flag-off identity check and the flush regen.
