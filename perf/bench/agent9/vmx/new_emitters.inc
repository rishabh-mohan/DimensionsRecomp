bool build_vsubsws(BuilderContext& ctx) {
  if (ctx.config().vmxVectorFallbacks) {
    // SSE form (vmx_vector_fallbacks), same scheme as vaddsws. a - b overflows iff a and b
    // differ in sign and the wrapped difference differs in sign from a; the saturated value is
    // INT_MAX for a >= 0 and INT_MIN for a < 0. Bit-identical to the scalar form below in every
    // lane (bench/agent9/vmx). Like the scalar form, it does not update VSCR.SAT.
    auto vD = ctx.v(ctx.insn.operands[0]);
    auto vA = ctx.v(ctx.insn.operands[1]);
    auto vB = ctx.v(ctx.insn.operands[2]);
    ctx.println("\t{{");
    ctx.println("\t\tsimde__m128i a = simde_mm_load_si128((simde__m128i*){}.u8);", vA);
    ctx.println("\t\tsimde__m128i b = simde_mm_load_si128((simde__m128i*){}.u8);", vB);
    ctx.println("\t\tsimde__m128i diff = simde_mm_sub_epi32(a, b);");
    ctx.println(
        "\t\tsimde__m128i overflow = simde_mm_and_si128(simde_mm_xor_si128(a, b), "
        "simde_mm_xor_si128(a, diff));");
    ctx.println(
        "\t\tsimde__m128i sat_val = simde_mm_xor_si128(simde_mm_srai_epi32(a, 31), "
        "simde_mm_set1_epi32(0x7FFFFFFF));");
    ctx.println(
        "\t\tsimde_mm_store_si128((simde__m128i*){}.u8, "
        "simde_mm_castps_si128(simde_mm_blendv_ps("
        "simde_mm_castsi128_ps(diff), "
        "simde_mm_castsi128_ps(sat_val), "
        "simde_mm_castsi128_ps(overflow))));",
        vD);
    ctx.println("\t}}");
    return true;
  }
  // Scalar form (default; output unchanged when the flag is off).
  for (size_t i = 0; i < 4; i++) {
    ctx.println("\t{}.s64 = int64_t({}.s32[{}]) - int64_t({}.s32[{}]);", ctx.temp(),
                ctx.v(ctx.insn.operands[1]), i, ctx.v(ctx.insn.operands[2]), i);
    ctx.println("\t{}.s32[{}] = {}.s64 > INT_MAX ? INT_MAX : {}.s64 < INT_MIN ? INT_MIN : {}.s64;",
                ctx.v(ctx.insn.operands[0]), i, ctx.temp(), ctx.temp(), ctx.temp());
  }
  return true;
}

bool build_vsrb(BuilderContext& ctx) {
  if (ctx.config().vmxVectorFallbacks) {
    // SSE form (vmx_vector_fallbacks): per-byte logical shift right by (vB & 7), done as three
    // conditional shifts by 4, 2 and 1. blendv_epi8 selects on each byte's MSB, and
    // slli_epi16(s, 5/6/7) moves count bit 2/1/0 of every byte into that byte's MSB.
    // srli_epi16 plus a byte mask is a per-byte logical shift.
    auto vD = ctx.v(ctx.insn.operands[0]);
    auto vA = ctx.v(ctx.insn.operands[1]);
    auto vB = ctx.v(ctx.insn.operands[2]);
    ctx.println("\t{{");
    ctx.println("\t\tsimde__m128i x = simde_mm_load_si128((simde__m128i*){}.u8);", vA);
    ctx.println("\t\tsimde__m128i s = simde_mm_load_si128((simde__m128i*){}.u8);", vB);
    ctx.println(
        "\t\tx = simde_mm_blendv_epi8(x, simde_mm_and_si128(simde_mm_srli_epi16(x, 4), "
        "simde_mm_set1_epi8(0x0F)), simde_mm_slli_epi16(s, 5));");
    ctx.println(
        "\t\tx = simde_mm_blendv_epi8(x, simde_mm_and_si128(simde_mm_srli_epi16(x, 2), "
        "simde_mm_set1_epi8(0x3F)), simde_mm_slli_epi16(s, 6));");
    ctx.println(
        "\t\tx = simde_mm_blendv_epi8(x, simde_mm_and_si128(simde_mm_srli_epi16(x, 1), "
        "simde_mm_set1_epi8(0x7F)), simde_mm_slli_epi16(s, 7));");
    ctx.println("\t\tsimde_mm_store_si128((simde__m128i*){}.u8, x);", vD);
    ctx.println("\t}}");
    return true;
  }
  // Scalar form (default; output unchanged when the flag is off).
  for (size_t i = 0; i < 16; i++)
    ctx.println("\t{}.u8[{}] = {}.u8[{}] >> ({}.u8[{}] & 0x7);", ctx.v(ctx.insn.operands[0]), i,
                ctx.v(ctx.insn.operands[1]), i, ctx.v(ctx.insn.operands[2]), i);
  return true;
}

bool build_vsrab(BuilderContext& ctx) {
  if (ctx.config().vmxVectorFallbacks) {
    // SSE form (vmx_vector_fallbacks): arithmetic shift through the logical one. With
    // u = x ^ 0x80 (= x + 128), x >> c == (u >>> c) - (0x80 >>> c) for c = vB & 7. The logical
    // shift is the vsrb chain; 0x80 >>> c comes from a pshufb table.
    auto vD = ctx.v(ctx.insn.operands[0]);
    auto vA = ctx.v(ctx.insn.operands[1]);
    auto vB = ctx.v(ctx.insn.operands[2]);
    ctx.println("\t{{");
    ctx.println("\t\tsimde__m128i s = simde_mm_load_si128((simde__m128i*){}.u8);", vB);
    ctx.println(
        "\t\tsimde__m128i x = simde_mm_xor_si128(simde_mm_load_si128((simde__m128i*){}.u8), "
        "simde_mm_set1_epi8(-128));",
        vA);
    ctx.println(
        "\t\tx = simde_mm_blendv_epi8(x, simde_mm_and_si128(simde_mm_srli_epi16(x, 4), "
        "simde_mm_set1_epi8(0x0F)), simde_mm_slli_epi16(s, 5));");
    ctx.println(
        "\t\tx = simde_mm_blendv_epi8(x, simde_mm_and_si128(simde_mm_srli_epi16(x, 2), "
        "simde_mm_set1_epi8(0x3F)), simde_mm_slli_epi16(s, 6));");
    ctx.println(
        "\t\tx = simde_mm_blendv_epi8(x, simde_mm_and_si128(simde_mm_srli_epi16(x, 1), "
        "simde_mm_set1_epi8(0x7F)), simde_mm_slli_epi16(s, 7));");
    ctx.println(
        "\t\tsimde__m128i bias = simde_mm_shuffle_epi8(simde_mm_setr_epi8(-128, 64, 32, 16, 8, 4, "
        "2, 1, 0, 0, 0, 0, 0, 0, 0, 0), simde_mm_and_si128(s, simde_mm_set1_epi8(7)));");
    ctx.println("\t\tsimde_mm_store_si128((simde__m128i*){}.u8, simde_mm_sub_epi8(x, bias));", vD);
    ctx.println("\t}}");
    return true;
  }
  // Scalar form (default; output unchanged when the flag is off).
  for (size_t i = 0; i < 16; i++)
    ctx.println("\t{}.s8[{}] = {}.s8[{}] >> ({}.u8[{}] & 0x7);", ctx.v(ctx.insn.operands[0]), i,
                ctx.v(ctx.insn.operands[1]), i, ctx.v(ctx.insn.operands[2]), i);
  return true;
}

bool build_vrlw(BuilderContext& ctx) {
  if (ctx.config().vmxVectorFallbacks) {
    // SSE form (vmx_vector_fallbacks): (a << sh) | (a >> ((32 - sh) & 31)) with sh = vB & 31.
    // For sh == 0 both shifts are by 0 and a | a == a, so every count stays in 0..31 (simde's
    // non-AVX2 sllv/srlv fallback is only well-defined for counts below 32).
    auto vD = ctx.v(ctx.insn.operands[0]);
    auto vA = ctx.v(ctx.insn.operands[1]);
    auto vB = ctx.v(ctx.insn.operands[2]);
    ctx.println("\t{{");
    ctx.println("\t\tsimde__m128i a = simde_mm_load_si128((simde__m128i*){}.u8);", vA);
    ctx.println(
        "\t\tsimde__m128i sh = simde_mm_and_si128(simde_mm_load_si128((simde__m128i*){}.u8), "
        "simde_mm_set1_epi32(0x1F));",
        vB);
    ctx.println(
        "\t\tsimde__m128i rsh = simde_mm_and_si128(simde_mm_sub_epi32(simde_mm_set1_epi32(32), "
        "sh), simde_mm_set1_epi32(0x1F));");
    ctx.println(
        "\t\tsimde_mm_store_si128((simde__m128i*){}.u8, "
        "simde_mm_or_si128(simde_mm_sllv_epi32(a, sh), simde_mm_srlv_epi32(a, rsh)));",
        vD);
    ctx.println("\t}}");
    return true;
  }
  // Scalar form (default; output unchanged when the flag is off).
  for (size_t i = 0; i < 4; i++) {
    ctx.println("\t{{ uint32_t sh = {}.u32[{}] & 0x1F;", ctx.v(ctx.insn.operands[2]), i);
    ctx.println("\t{}.u32[{}] = ({}.u32[{}] << sh) | (sh ? ({}.u32[{}] >> (32 - sh)) : 0); }}",
                ctx.v(ctx.insn.operands[0]), i, ctx.v(ctx.insn.operands[1]), i,
                ctx.v(ctx.insn.operands[1]), i);
  }
  return true;
}

bool build_vsraw(BuilderContext& ctx) {
  if (ctx.config().vmxVectorFallbacks) {
    // SSE form (vmx_vector_fallbacks), as vslw. The scalar form's vB.u8[i * 4] is the low byte
    // of word i, so (vB.u32[i] & 31) is the same count.
    auto vD = ctx.v(ctx.insn.operands[0]);
    auto vA = ctx.v(ctx.insn.operands[1]);
    auto vB = ctx.v(ctx.insn.operands[2]);
    ctx.println("\t{{");
    ctx.println("\t\tsimde__m128i a = simde_mm_load_si128((simde__m128i*){}.u8);", vA);
    ctx.println("\t\tsimde__m128i b = simde_mm_load_si128((simde__m128i*){}.u8);", vB);
    ctx.println("\t\tsimde__m128i shift = simde_mm_and_si128(b, simde_mm_set1_epi32(0x1F));");
    ctx.println("\t\tsimde_mm_store_si128((simde__m128i*){}.u8, simde_mm_srav_epi32(a, shift));",
                vD);
    ctx.println("\t}}");
    return true;
  }
  // Scalar form (default; output unchanged when the flag is off).
  for (size_t i = 0; i < 4; i++)
    ctx.println("\t{}.s32[{}] = {}.s32[{}] >> ({}.u8[{}] & 0x1F);", ctx.v(ctx.insn.operands[0]), i,
                ctx.v(ctx.insn.operands[1]), i, ctx.v(ctx.insn.operands[2]), i * 4);
  return true;
}

bool build_vsrw(BuilderContext& ctx) {
  if (ctx.config().vmxVectorFallbacks) {
    // SSE form (vmx_vector_fallbacks), as vslw (see vsraw for the count).
    auto vD = ctx.v(ctx.insn.operands[0]);
    auto vA = ctx.v(ctx.insn.operands[1]);
    auto vB = ctx.v(ctx.insn.operands[2]);
    ctx.println("\t{{");
    ctx.println("\t\tsimde__m128i a = simde_mm_load_si128((simde__m128i*){}.u8);", vA);
    ctx.println("\t\tsimde__m128i b = simde_mm_load_si128((simde__m128i*){}.u8);", vB);
    ctx.println("\t\tsimde__m128i shift = simde_mm_and_si128(b, simde_mm_set1_epi32(0x1F));");
    ctx.println("\t\tsimde_mm_store_si128((simde__m128i*){}.u8, simde_mm_srlv_epi32(a, shift));",
                vD);
    ctx.println("\t}}");
    return true;
  }
  // Scalar form (default; output unchanged when the flag is off).
  for (size_t i = 0; i < 4; i++)
    ctx.println("\t{}.u32[{}] = {}.u32[{}] >> ({}.u8[{}] & 0x1F);", ctx.v(ctx.insn.operands[0]), i,
                ctx.v(ctx.insn.operands[1]), i, ctx.v(ctx.insn.operands[2]), i * 4);
  return true;
}

bool build_vpkuhus(BuilderContext& ctx) {
  // Vector Pack Unsigned Halfword Unsigned Saturate
  // NOTE(tomc): _mm_packus_epi16 treats inputs as signed, so we need custom saturation for
  // unsigned. Unsigned halfwords >= 0x8000 would be interpreted as negative and clamped to 0
  // instead of 0xFF.
  if (ctx.config().vmxVectorFallbacks && ctx.insn.operands[0] != ctx.insn.operands[1] &&
      ctx.insn.operands[0] != ctx.insn.operands[2]) {
    // SSE form (vmx_vector_fallbacks): min_epu16(x, 0xFF) clamps as unsigned first, so the
    // signed packus only sees 0..0xFF. vB fills the low host bytes, as in vpkshus.
    // Only when vD is neither vA nor vB: the scalar form below writes vD byte by byte while it
    // still reads vA/vB, so with aliasing its result differs from this one (and from the ISA).
    ctx.println(
        "\tsimde_mm_store_si128((simde__m128i*){}.u8, simde_mm_packus_epi16("
        "simde_mm_min_epu16(simde_mm_load_si128((simde__m128i*){}.u16), "
        "simde_mm_set1_epi16(0xFF)), "
        "simde_mm_min_epu16(simde_mm_load_si128((simde__m128i*){}.u16), "
        "simde_mm_set1_epi16(0xFF))));",
        ctx.v(ctx.insn.operands[0]), ctx.v(ctx.insn.operands[2]), ctx.v(ctx.insn.operands[1]));
    return true;
  }
  for (size_t i = 0; i < 8; i++) {
    ctx.println("\t{}.u8[{}] = {}.u16[{}] > 0xFF ? 0xFF : (uint8_t){}.u16[{}];",
                ctx.v(ctx.insn.operands[0]), 15 - i, ctx.v(ctx.insn.operands[1]), 7 - i,
                ctx.v(ctx.insn.operands[1]), 7 - i);
    ctx.println("\t{}.u8[{}] = {}.u16[{}] > 0xFF ? 0xFF : (uint8_t){}.u16[{}];",
                ctx.v(ctx.insn.operands[0]), 7 - i, ctx.v(ctx.insn.operands[2]), 7 - i,
                ctx.v(ctx.insn.operands[2]), 7 - i);
  }
  return true;
}

bool build_vpkuwus(BuilderContext& ctx) {
  // Vector Pack Unsigned Word Unsigned Saturate

  // NOTE(tomc): _mm_packus_epi32 treats inputs as signed, so we need custom saturation for unsigned
  // Saturate each u32 to [0, 0xFFFF], then pack to u16
  if (ctx.config().vmxVectorFallbacks && ctx.insn.operands[0] != ctx.insn.operands[1] &&
      ctx.insn.operands[0] != ctx.insn.operands[2]) {
    // SSE form (vmx_vector_fallbacks): min_epu32(x, 0xFFFF) then packus_epi32, as vpkuwum.
    // Only when vD is neither vA nor vB, for the same reason as vpkuhus.
    ctx.println(
        "\tsimde_mm_store_si128((simde__m128i*){}.u16, simde_mm_packus_epi32("
        "simde_mm_min_epu32(simde_mm_load_si128((simde__m128i*){}.u32), "
        "simde_mm_set1_epi32(0xFFFF)), "
        "simde_mm_min_epu32(simde_mm_load_si128((simde__m128i*){}.u32), "
        "simde_mm_set1_epi32(0xFFFF))));",
        ctx.v(ctx.insn.operands[0]), ctx.v(ctx.insn.operands[2]), ctx.v(ctx.insn.operands[1]));
    return true;
  }
  for (size_t i = 0; i < 4; i++) {
    ctx.println("\t{}.u16[{}] = {}.u32[{}] > 0xFFFF ? 0xFFFF : (uint16_t){}.u32[{}];",
                ctx.v(ctx.insn.operands[0]), 7 - i, ctx.v(ctx.insn.operands[1]), 3 - i,
                ctx.v(ctx.insn.operands[1]), 3 - i);
    ctx.println("\t{}.u16[{}] = {}.u32[{}] > 0xFFFF ? 0xFFFF : (uint16_t){}.u32[{}];",
                ctx.v(ctx.insn.operands[0]), 3 - i, ctx.v(ctx.insn.operands[2]), 3 - i,
                ctx.v(ctx.insn.operands[2]), 3 - i);
  }
  return true;
}

