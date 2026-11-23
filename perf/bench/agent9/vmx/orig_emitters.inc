bool build_vsubsws(BuilderContext& ctx) {
  // TODO: vectorize
  for (size_t i = 0; i < 4; i++) {
    ctx.println("\t{}.s64 = int64_t({}.s32[{}]) - int64_t({}.s32[{}]);", ctx.temp(),
                ctx.v(ctx.insn.operands[1]), i, ctx.v(ctx.insn.operands[2]), i);
    ctx.println("\t{}.s32[{}] = {}.s64 > INT_MAX ? INT_MAX : {}.s64 < INT_MIN ? INT_MIN : {}.s64;",
                ctx.v(ctx.insn.operands[0]), i, ctx.temp(), ctx.temp(), ctx.temp());
  }
  return true;
}

bool build_vsrb(BuilderContext& ctx) {
  // TODO(tomc): vectorize
  for (size_t i = 0; i < 16; i++)
    ctx.println("\t{}.u8[{}] = {}.u8[{}] >> ({}.u8[{}] & 0x7);", ctx.v(ctx.insn.operands[0]), i,
                ctx.v(ctx.insn.operands[1]), i, ctx.v(ctx.insn.operands[2]), i);
  return true;
}

bool build_vsrab(BuilderContext& ctx) {
  // TODO(tomc): vectorize
  for (size_t i = 0; i < 16; i++)
    ctx.println("\t{}.s8[{}] = {}.s8[{}] >> ({}.u8[{}] & 0x7);", ctx.v(ctx.insn.operands[0]), i,
                ctx.v(ctx.insn.operands[1]), i, ctx.v(ctx.insn.operands[2]), i);
  return true;
}

bool build_vrlw(BuilderContext& ctx) {
  // TODO(tomc): vectorize
  for (size_t i = 0; i < 4; i++) {
    ctx.println("\t{{ uint32_t sh = {}.u32[{}] & 0x1F;", ctx.v(ctx.insn.operands[2]), i);
    ctx.println("\t{}.u32[{}] = ({}.u32[{}] << sh) | (sh ? ({}.u32[{}] >> (32 - sh)) : 0); }}",
                ctx.v(ctx.insn.operands[0]), i, ctx.v(ctx.insn.operands[1]), i,
                ctx.v(ctx.insn.operands[1]), i);
  }
  return true;
}

bool build_vsraw(BuilderContext& ctx) {
  // TODO(tomc): vectorize
  for (size_t i = 0; i < 4; i++)
    ctx.println("\t{}.s32[{}] = {}.s32[{}] >> ({}.u8[{}] & 0x1F);", ctx.v(ctx.insn.operands[0]), i,
                ctx.v(ctx.insn.operands[1]), i, ctx.v(ctx.insn.operands[2]), i * 4);
  return true;
}

bool build_vsrw(BuilderContext& ctx) {
  // TODO(tomc): vectorize
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

