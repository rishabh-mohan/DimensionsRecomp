# Agent 10, task #9: final helper designs (written before coding, 16:55)

Status: designs only. No SDK file has been edited yet. `old_intrinsics.h` here is a verbatim copy of
`include/rex/ppc/intrinsics.h` at pin 2897c31, with the namespace renamed to `old_ppc`. Create it with
`git -C DimensionsRecomp/rexglue-sdk show 2897c31:include/rex/ppc/intrinsics.h`, rename `namespace rex::ppc` to
`old_ppc`, and drop the trailing `using rex::ppc::...` lines.

## Semantics to preserve exactly (current code, for all inputs)
- **vslo/vsro.** n = bits 3..6 of x86 byte 0 (PPC byte 15). The `>= 16` branch is dead.
- **vsl.** count = low 3 bits of **x86 byte 15 (PPC byte 0)**. The ISA reads PPC byte 15 and leaves non-uniform vB
  undefined, so keep the current behaviour and report the difference. vsr reads x86 byte 0 and is unchanged.
- **Element shifts.**
  - `sllv_epi16`/`srlv_epi16`: count >= 16 gives 0.
  - `srav_epi16`: shifts by min(c, 15).
  - `sllv_epi8`: count >= 8 gives 0.

  These are AVX-512 semantics for the full count range. vrlh relies on srlv giving 0 at count 16.
- **vctuxs.** NaN gives 0, values < 1 give 0, values >= 2^32 give 0xFFFFFFFF, everything else is truncated.

## Designs
- **Tables.** Declare them `alignas(16) inline constexpr uint8_t VectorMaskL[] = {...}` (and the same for MaskR,
  ShiftTableL and ShiftTableR). Contents are unchanged and the global `using` aliases stay. Emitted C-style casts
  still compile.
- **perm_epi8_.** `e = andnot(c, set1_epi8(0xF))`, because 15-(c&15) == ~c&15. The blendv is unchanged.
- **vctuxs.**
  ```
  clamped = max_ps(src, 0)                 // NaN, -0 and negatives become +0 (maxps returns the 2nd operand)
  high    = cmpge_ps(src, 2^31)
  r       = cvttps_epi32(clamped - (high & 2^31)) | (high << 31)
  r      |= cmpge_ps(src, 2^32)
  ```
  The bench also tries a "maxadd" variant: `cvtt(c) + max_epi32(cvtt(c - 2^31), 0)`. It relies on cvtt returning
  0x80000000 for out-of-range inputs.
- **vsl.**
  ```
  n = and(srli_si128(b, 15), cvtsi32_si128(7))
  r = insert_ps(sll_epi64(a, n), sll_epi64(slli_si128(a, 4), n), 0xE0)   // src dword 3 into dst dword 2
  ```
  This is branch-free, mirrors vsr, and replaces both #if arms. Do **not** use `srl_epi64(.., 64-n)`: simde's
  portable srl_epi64 computes `>> 64` (UB) when the count is 64.
- **vslo.**
  ```
  n = shuffle_epi8(and(srli_epi16(b, 3), set1_epi8(0xF)), zero)
  r = shuffle_epi8(a, sub_epi8(setr(0..15), n))
  ```
  **vsro** is the same with `add_epi8(setr(0x70..0x7F), n)`. The bench also tries a 48-byte sliding-window LUT
  variant.
- **Variable shifts.**
  - **AVX2 path** (`SIMDE_X86_AVX2_NATIVE`). Split even/odd 16-bit lanes with 32-bit sllv/srlv/srav, then
    `blend_epi16(.., 0xAA)`.
  - **SSE path.**
    - sll: `n = min_epu16(c, 16)`, duplicate the low byte of each word with pshufb, then
      `pow2 = pshufb(setr(1,2,..,128, 0 x8), n + 0x6870)` and `mullo_epi16(a, pow2)`.
    - srl: `mulhi_epu16(a, pshufb(setr(128,64,..,1, 0 x8), n - 0x0109)) | (a & (c == 0))`.
    - sra: `srlv(a ^ s, c) ^ s`, where `s = srai(a, 15)`.

  Keep the AVX2 path only if the bench shows it wins at v3. To compare, build the SSE path with
  `-march=x86-64-v3 -mno-avx2`.
- **sllv_epi8.**
  ```
  pow2 = pshufb(setr(1,2,..,128, 0 x8), min_epu8(c, 8))
  r    = (mullo16(a, pow2 & 0xFF) & 0xFF) | mullo16(a & 0xFF00, pow2 >> 8)
  ```
- **math.h.**
  - `clamp_float`: the intermediate `float clamped_to_min` becomes `T`.
  - `rotate_left`: `(T(v) << sh) | (T(v) >> ((bits - sh) & (bits - 1)))`, which removes the UB at sh = 0.

## Test and bench plan
- **Files:** `ppc_ref.h` (scalar PPC models and byte-order helpers), `impls.h` (Old/New wrappers and the exact
  emitted codegen forms), `variants.h`, `test_intrinsics.cpp`, `test_math.cpp`, `bench_intrinsics.cpp`,
  `asm_probe.cpp` and `build.ps1`.
- **Configs:** `v3`, `v2`, `v3noavx2` and `portable` (`-DSIMDE_NO_NATIVE`).
- **Coverage:** exhaustive where feasible (epi16 shifts over all 2^32 (a, count) pairs, sllv_epi8 over 2^16, vctuxs
  over all 2^32 floats under two MXCSR values, vslo/vsro/vsl over every count byte), 10^7 random cases otherwise,
  plus a KAT replay of `tests/ppc/asm/instr_{vslo,vsro,vperm,vctuxs,vctsxs,lvsl,lvsr,vslb,vslh,vsrh,vsrah,vrlh,vsl,vsr}.s`.
- **Bench:** single thread pinned to a P-core, QueryThreadCycleTime, implementations interleaved, 9 reps, median.
