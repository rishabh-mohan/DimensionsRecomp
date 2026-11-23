// Extracted from context.cpp lines 213-304 by extract_helpers.ps1. Do not edit.
namespace {

constexpr std::string_view kMustTailReturn = "[[clang::musttail]] return ";

// Whether a direct branch in this function targets setJmpAddress, so that
// emit_function_call() puts ppc_setjmp() in this frame. Both readings of the
// displacement (relative, and absolute for AA=1) count, which is conservative.
bool calls_setjmp(const BuilderContext& ctx) {
  const uint32_t target = ctx.config().setJmpAddress;
  if (target == 0)
    return false;
  for (const auto& block : ctx.fn.blocks()) {
    const uint8_t* p = ctx.emitCtx.binary.translate(block.base);
    if (!p)
      continue;
    for (uint32_t addr = block.base; addr < block.end(); addr += 4, p += 4) {
      const uint32_t w = (uint32_t(p[0]) << 24) | (uint32_t(p[1]) << 16) |
                         (uint32_t(p[2]) << 8) | uint32_t(p[3]);
      int32_t disp;
      if ((w >> 26) == 18)  // b, ba, bl, bla: LI
        disp = (int32_t(w << 6) >> 6) & ~3;
      else if ((w >> 26) == 16)  // bc, bca, bcl, bcla: BD
        disp = int32_t(int16_t(w & 0xFFFC));
      else
        continue;
      if (addr + uint32_t(disp) == target || uint32_t(disp) == target)
        return true;
    }
  }
  return false;
}

bool musttail_allowed(const BuilderContext& ctx) {
  const auto& cfg = ctx.config();
  if (!cfg.musttailCalls)
    return false;
  // The generateSeh test of FunctionNode::recompile(): the body is in SEH_TRY.
  if (cfg.generateExceptionHandlers && ctx.fn.hasExceptionInfo()) {
    const auto* seh = ctx.fn.exceptionInfo()->asSeh();
    if (seh && !seh->scopes.empty())
      return false;
  }
  return !calls_setjmp(ctx);
}

bool is_identifier(std::string_view s) {
  if (s.empty() || (s[0] >= '0' && s[0] <= '9'))
    return false;
  for (char c : s) {
    if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_'))
      return false;
  }
  return true;
}

}  // namespace

// `<indent>NAME(ctx, base);` and `<indent>return;`, or the single line
// `<indent>[[clang::musttail]] return NAME(ctx, base);` where musttail is
// allowed. Used by the conditional tail calls below and by bctr jump tables.
void emit_tail_call_line(BuilderContext& ctx, std::string_view indent, std::string_view name) {
  if (musttail_allowed(ctx)) {
    ctx.println("{}{}{}(ctx, base);", indent, kMustTailReturn, name);
    return;
  }
  ctx.println("{}{}(ctx, base);", indent, name);
  ctx.println("{}return;", indent);
}

// A `b` tail call: emit_function_call() followed by `return;`. Where musttail
// is allowed and the call came out as the plain line `\tNAME(ctx, base);`, that
// line becomes the musttail return; every other form keeps its text and the
// `return;`.
void emit_tail_call(BuilderContext& ctx, uint32_t address) {
  const size_t mark = ctx.out.size();
  ctx.emit_function_call(address);
  if (musttail_allowed(ctx)) {
    constexpr std::string_view kCallEnd = "(ctx, base);\n";
    const std::string_view call = std::string_view(ctx.out).substr(mark);
    if (call.size() > 1 + kCallEnd.size() && call.front() == '\t' && call.ends_with(kCallEnd)) {
      const std::string_view name = call.substr(1, call.size() - 1 - kCallEnd.size());
      if (is_identifier(name)) {
        std::string line = fmt::format("\t{}{}(ctx, base);\n", kMustTailReturn, name);
        ctx.out.resize(mark);
        ctx.out += line;
        return;
      }
    }
  }
  ctx.println("\treturn;");
}

