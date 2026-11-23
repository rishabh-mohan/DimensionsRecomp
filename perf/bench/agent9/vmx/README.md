# VMX scalar fallbacks → SSE forms (`vmx_vector_fallbacks`)

Flag: `ctx.config().vmxVectorFallbacks` (TOML `vmx_vector_fallbacks`, default **false**; the field was added to config.h/config.cpp by Agent 9).
With the flag off the emitted text is byte-identical to before. Two checks show it:
- gen check: 0 of 40 op×alias combinations differ;
- verify_unchanged: the file hash after putting the 8 original emitters back equals the hash recorded before the edit.

## Replaced emitters (`DimensionsRecomp/rexglue-sdk/src/codegen/builders/vector.cpp`)

Each one is `if (ctx.config().vmxVectorFallbacks ...) { <SSE text>; return true; }` followed by the old scalar code, unchanged.

| op | line | new form (simde, per instruction) | why it is bit-identical |
|---|---|---|---|
| vsubsws | [325](<workspace>/DimensionsRecomp/rexglue-sdk/src/codegen/builders/vector.cpp#L324-L360) | `diff=a-b; ovf=(a^b)&(a^diff); sat=srai(a,31)^0x7FFFFFFF; r=blendv_ps(diff,sat,ovf)` | Overflow iff a and b differ in sign and diff differs in sign from a. blendv_ps looks only at each lane's MSB, so the `srai(ovf,31)` of the requested form is not needed. sat is INT_MAX for a≥0 and INT_MIN for a<0. |
| vsrb | [918](<workspace>/DimensionsRecomp/rexglue-sdk/src/codegen/builders/vector.cpp#L917-L947) | 3 conditional shifts by 4, 2, 1: `x=blendv_epi8(x, srli_epi16(x,k)&mask_k, slli_epi16(s,5/6/7))` | `slli_epi16(s, 5/6/7)` moves count bit 2/1/0 of every byte into that byte's MSB, which is what blendv_epi8 tests. `srli_epi16` plus a byte mask is a per-byte logical shift. Count = vB&7, as in the scalar code. |
| vsrab | [950](<workspace>/DimensionsRecomp/rexglue-sdk/src/codegen/builders/vector.cpp#L949-L984) | `u=x^0x80`; the vsrb chain on u; `bias=pshufb({0x80,0x40,..,1,0..}, s&7)`; `r=u'-bias` | Identity `x>>c == ((x^0x80)>>>c) - (0x80>>>c)` (signed byte, c in 0..7). |
| vrlw | [1009](<workspace>/DimensionsRecomp/rexglue-sdk/src/codegen/builders/vector.cpp#L1008-L1040) | `sh=b&31; rsh=(32-sh)&31; r=sllv_epi32(a,sh)\|srlv_epi32(a,rsh)` | When sh=0 both shifts are by 0 and a\|a=a. Every count stays in 0..31, which keeps simde's non-AVX2 sllv/srlv defined. |
| vsraw | [1099](<workspace>/DimensionsRecomp/rexglue-sdk/src/codegen/builders/vector.cpp#L1098-L1119) | `srav_epi32(a, b&31)` | The scalar code's `vB.u8[4i]&0x1F` is the low byte of word i on a little-endian host, which equals `vB.u32[i]&0x1F`. |
| vsrw | [1122](<workspace>/DimensionsRecomp/rexglue-sdk/src/codegen/builders/vector.cpp#L1121-L1141) | `srlv_epi32(a, b&31)` | Same count argument as vsraw. |
| vpkuhus | [1234](<workspace>/DimensionsRecomp/rexglue-sdk/src/codegen/builders/vector.cpp#L1229-L1258) | `packus_epi16(min_epu16(vB,0xFF), min_epu16(vA,0xFF))` | The unsigned clamp first means the signed packus only sees 0..0xFF. **Used only when vD≠vA and vD≠vB.** |
| vpkuwus | [1277](<workspace>/DimensionsRecomp/rexglue-sdk/src/codegen/builders/vector.cpp#L1272-L1300) | `packus_epi32(min_epu32(vB,0xFFFF), min_epu32(vA,0xFFFF))` | Same as vpkuhus, including the alias condition. |

Left alone:
- vlogefp and vexptefp: these are approximations; changing them was ruled out.
- vpkd3d128 / vupkd3d128: not plain per-lane math.
- Every op that already had a vector form.

**VSCR.SAT:** no emitter writes `vscr_sat`, neither the old scalar forms nor the new ones. The harness checks that SAT (and the whole PPCContext, by memcmp) is unchanged by both.

## Method
1. **`gen.cpp`** links the real emitter code (`orig_emitters.inc` = the pre-edit text, `new_emitters.inc` = the live text, extracted by `extract.ps1`).
   - It prints each op for 5 alias patterns (distinct, d=a, d=b, a=b, all equal) with the flag off and on.
   - Flag off: identical to the original text in **40/40** combinations.
   - Flag on: the alias rule is never broken (0).
   - The printed statements are pasted into kernels (`gen_out`), so the harness runs exactly the text the recompiler emits.
2. **`harness.cpp`** runs the old and new kernels on the same PPCContext.
   - Inputs: 378 special 32-bit lane values (INT_MIN, INT_MAX, 0, ±1, 0x7F/0x80/0xFF/0x8000/0xFFFF boundaries, every shift count…) combined over lanes, plus 10,000,000 random cases per distinct-operand kernel and 2,000,000 per aliased kernel.
   - Each case compares all lanes, SAT, and a full-context memcmp, plus an independent reference model (`ref_*`).
3. **`verify_unchanged.ps1`**: hash check that only the 8 emitters changed in vector.cpp.
4. **`asm_count.ps1` / `asm_dump.ps1`**: instruction counts of each kernel (old vs new) in the harness asm, under the test flags (`-msse4.1 -mssse3`) and the game flags (`-march=x86-64-v3`).

## Results (`run.log`, `result_*.txt`)

| config | cases | lane mismatches | SAT mismatches | ctx | failing kernels |
|---|---|---|---|---|---|
| sse41 (`-msse4.1 -mssse3`, the ppc tests) | 148,555,140 | **0** | **0** | ok | 0 |
| v3 (game flags, `-march=x86-64-v3`) | 148,555,140 | **0** | **0** | ok | 0 |
| nonative (SSE2 only, simde emulation) | 148,555,140 | **0** | **0** | ok | 0 |

> [!WARNING]
> **Existing bug, found but not fixed:** the scalar vpkuhus/vpkuwus text writes vD byte by byte while it is still reading vA/vB, so it gives wrong results when vD aliases an input. The table below counts the wrong cases, measured against the reference model. Under aliasing the new code keeps the scalar text, so both columns are equal and the flag-off output stays byte-identical. The SSE form is correct in every alias pattern (ref_sse = 0). Applying it unconditionally would fix the bug, but that changes default output, so it should be a separate decision.

| op | d=a | d=b | all equal | cases each |
|---|---|---|---|---|
| vpkuhus | 710,837 | 834,844 | 792,469 | 2,065,536 |
| vpkuwus | 390,332 | 552,147 | 540,488 | 2,142,884 |

### Instruction counts per kernel (old → new, including loads/stores/ret)

| op | sse41 | v3 (game flags) |
|---|---|---|
| vsubsws | 12 → 14 | 11 → 12 |
| vsrb | 20 → 22 | 17 → 16 |
| vsrab | 35 → 27 | 29 → 21 |
| vrlw | 46 → 17 | 31 → 10 |
| vsraw | 22 → 20 | 8 → 6 |
| vsrw | 22 → 20 | 8 → 6 |
| vpkuhus | 7 → 7 | 7 → 6 |
| vpkuwus | 7 → 7 | 7 → 6 |

Rough timing, 20M calls each, in ns (old → new). This is a shared, loaded machine, so trust the instruction counts more than these:

| op | sse41 | v3 | nonative |
|---|---|---|---|
| vsubsws | 9.73 → 9.68 | 7.17 → 7.90 | 19.88 → 9.85 |
| vsrb | 15.85 → 14.12 | 8.16 → 7.89 | 10.63 → 24.11 |
| vsrab | 14.84 → 20.50 | 10.82 → 6.75 | 28.27 → 423.60 |
| vrlw | 8.29 → 13.13 | 8.25 → 6.62 | 12.68 → 26.75 |
| vsraw | 9.93 → 11.37 | 4.20 → 4.05 | 21.05 → 19.34 |
| vsrw | 14.14 → 11.90 | 4.78 → 4.39 | 20.96 → 22.51 |
| vpkuhus | 8.96 → 6.16 | 9.84 → 6.36 | 12.81 → 15.45 |
| vpkuwus | 5.51 → 10.34 | 9.85 → 4.02 | 14.33 → 15.86 |

## Findings
- **In isolated kernels, clang's SLP vectorizer already vectorizes the old scalar text** for vsubsws, vsrb, vsraw/vsrw and vpku*. The clear gains are in vsrab (−8 instructions) and vrlw (−21 instructions at v3). vsraw/vsrw/vpku* save 1–2 instructions at v3. In real generated functions (long, many live locals) SLP does not reliably fire, so the explicit form is the more robust choice.
- **vsubsws** with the requested form is one instruction longer than what clang makes of the old text. A shorter alternative, bit-identical by the same reasoning but **not harness-tested and not implemented**:
  `diff=a-b; ovf=cmpgt_epi32(b,a)^diff; sat=srai(diff,31)^0x80000000; r=blendv_ps(diff,sat,ovf)`.
- **Enable the flag only for the native targets: the game (x86-64-v3) and the ppc tests (SSE4.1).**
  - The vrlw/vsraw/vsrw forms use AVX2 `sllv/srlv/srav_epi32`. These are native at v3 and emulated by simde below that.
  - The vsrb/vsrab forms need SSE4.1 `blendv_epi8` and SSSE3 `pshufb`.
  - On an SSE2-only build simde emulates all of them, and vsrab becomes 15× slower (nonative column).
- LEGO uses of these ops: vpkuhus 14, vsrab 6, vsraw 44 (2 aliased), vsrw 19, vsubsws 26 (3 aliased). vsrb, vrlw and vpkuwus do not occur.

## Reproduce (one compile at a time, through cpu2)
```powershell
powershell -NoProfile -File bench/agent9/cpu2.ps1 -File bench/agent9/vmx/run.ps1 *> bench/agent9/vmx/run.log
powershell -NoProfile -File bench/agent9/vmx/verify_unchanged.ps1      # text only
powershell -NoProfile -File bench/agent9/vmx/asm_count.ps1             # text only, after run.ps1
powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "powershell -NoProfile -File bench/agent9/syntax-check.ps1 src/codegen/builders/vector.cpp"
```
