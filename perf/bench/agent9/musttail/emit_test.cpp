// emit_test.cpp - musttail emission, step 1 (text).
//
// Compiles the live tail-call helpers of context.cpp (gen_out/helpers.inc, written by
// extract_helpers.ps1) against a minimal stand-in for BuilderContext and checks the exact text
// they print:
//   - flag off: byte-identical to the pre-change emission (old_b / old_line below, copied from
//     the git diff of control_flow.cpp and context.cpp) for every call form;
//   - flag on: only the plain one-line call `\tNAME(ctx, base);` becomes
//     `\t[[clang::musttail]] return NAME(ctx, base);`; every other form keeps its text + return;
//   - SEH-wrapped functions and functions that branch to setJmpAddress keep the old text.
// Exit code = number of failed checks.
#include <cstdint>
#include <cstdio>
#include <format>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace fmt {
using std::format;
}

struct RecompilerConfig {
  bool musttailCalls = false;
  bool generateExceptionHandlers = false;
  uint32_t setJmpAddress = 0;
  uint32_t longJmpAddress = 0;
};
struct Block {
  uint32_t base = 0, size = 0;
  uint32_t end() const { return base + size; }
};
struct SehInfo {
  std::vector<int> scopes;
};
struct ExceptionInfo {
  std::optional<SehInfo> seh;
  const SehInfo* asSeh() const { return seh ? &*seh : nullptr; }
};
struct FunctionNode {
  std::vector<Block> blocks_;
  std::optional<ExceptionInfo> exc;
  const std::vector<Block>& blocks() const { return blocks_; }
  bool hasExceptionInfo() const { return exc.has_value(); }
  const ExceptionInfo* exceptionInfo() const { return exc ? &*exc : nullptr; }
};
struct Binary {
  uint32_t base = 0x82000000;
  std::vector<uint8_t> image = std::vector<uint8_t>(0x4000, 0);
  const uint8_t* translate(uint32_t addr) const {
    if (addr < base || addr - base >= image.size()) return nullptr;
    return image.data() + (addr - base);
  }
  void put(uint32_t addr, uint32_t w) {
    uint8_t* p = image.data() + (addr - base);
    p[0] = uint8_t(w >> 24), p[1] = uint8_t(w >> 16), p[2] = uint8_t(w >> 8), p[3] = uint8_t(w);
  }
};
struct EmitContext {
  Binary binary;
};

struct BuilderContext {
  std::string out;
  RecompilerConfig cfg;
  FunctionNode fn;
  EmitContext emitCtx;
  std::string call_text;  // what emit_function_call() appends in the current case
  const RecompilerConfig& config() const { return cfg; }
  template <class... Args>
  void println(std::format_string<Args...> f, Args&&... args) {
    out += std::format(f, std::forward<Args>(args)...);
    out += '\n';
  }
  void emit_function_call(uint32_t) { out += call_text; }
};

#include "gen_out/helpers.inc"

// Pre-change emission (git diff): build_b printed emit_function_call() + "\treturn;";
// emit_conditional_branch and the bctr jump-table case printed these two lines.
void old_b(BuilderContext& ctx, uint32_t target) {
  ctx.emit_function_call(target);
  ctx.println("\treturn;");
}
void old_line(BuilderContext& ctx, std::string_view name) {
  ctx.println("\t\t{}(ctx, base);", name);
  ctx.println("\t\treturn;");
}

namespace {
int g_checks = 0, g_fail = 0;
std::string esc(std::string_view s) {
  std::string r;
  for (char c : s) r += c == '\t' ? "\\t" : c == '\n' ? "\\n" : std::string(1, c);
  return r;
}
void check(const std::string& what, const std::string& got, const std::string& want) {
  ++g_checks;
  if (got == want) return;
  ++g_fail;
  std::printf("FAIL %s\n  got:  %s\n  want: %s\n", what.c_str(), esc(got).c_str(), esc(want).c_str());
}

struct Form {
  const char* name;
  std::string text;      // emit_function_call() output (copied from context.cpp)
  const char* fn_name;   // non-null: plain one-line call, rewritten when musttail is allowed
};
const Form kForms[] = {
    {"function", "\tsub_82001000(ctx, base);\n", "sub_82001000"},
    {"import", "\t__imp__XamInputGetState(ctx, base);\n", "__imp__XamInputGetState"},
    {"restgpr", "\t__restgprlr_14(ctx, base);\n", "__restgprlr_14"},
    {"longjmp", "\tppc_longjmp(ctx.r3.u32, ctx.r4.s32);\n", nullptr},
    {"setjmp",
     "\tenv = ctx;\n\ttemp.s64 = ppc_setjmp(ctx.r3.u32);\n\tif (temp.s64 != 0) ctx = env;\n"
     "\tctx.r3 = temp;\n",
     nullptr},
    {"save_rest_elided", "", nullptr},
    {"funclet_handoff",
     "\tctx.r14 = r14;\n\tctx.r31 = r31;\n\tsub_82001000(ctx, base);\n\tr14 = ctx.r14;\n"
     "\tr31 = ctx.r31;\n",
     nullptr},
    {"fatal_unresolved",
     "\t// FATAL: unresolved function 0x82001000\n"
     "\tREX_FATAL(\"Unresolved call from 0x82000010 to 0x82001000\");\n",
     nullptr},
    {"fatal_no_target",
     "\t// FATAL: unresolved function 0x82001000 (no CallTarget in FunctionNode)\n"
     "\tREX_FATAL(\"Unresolved call from 0x82000010 to 0x82001000\");\n",
     nullptr},
    // Not produced today; must not be rewritten either.
    {"double_tab", "\t\tsub_82001000(ctx, base);\n", nullptr},
    {"member_call", "\tobj.f(ctx, base);\n", nullptr},
    {"two_calls", "\tsub_82001000(ctx, base);\n\tsub_82001004(ctx, base);\n", nullptr},
    {"digit_start", "\t1sub(ctx, base);\n", nullptr},
    {"bare_parens", "\t(ctx, base);\n", nullptr},
    {"no_newline", "\tsub_82001000(ctx, base);", nullptr},
};

// Run emit_tail_call() / emit_tail_call_line() on a context set up by `setup`, and compare
// against the expected text, which is the old text unless `expect_musttail`.
template <class Setup>
void run_cases(const char* scenario, bool expect_musttail_if_plain, Setup setup) {
  for (const char* prefix : {"", "\t// b 0x82001000\n"}) {
    for (const Form& f : kForms) {
      BuilderContext ctx, ref;
      setup(ctx);
      setup(ref);
      ctx.out = ref.out = prefix;
      ctx.call_text = ref.call_text = f.text;
      emit_tail_call(ctx, 0x82001000);
      old_b(ref, 0x82001000);
      std::string want = ref.out;
      if (expect_musttail_if_plain && f.fn_name)
        want = std::string(prefix) + "\t[[clang::musttail]] return " + f.fn_name + "(ctx, base);\n";
      check(std::format("{} emit_tail_call {} prefix={}", scenario, f.name, *prefix ? 1 : 0), ctx.out,
            want);
    }
  }
  for (const char* name : {"sub_82001000", "__imp__XamInputGetState"}) {
    BuilderContext ctx, ref;
    setup(ctx);
    setup(ref);
    ctx.out = ref.out = "\tif (!ctx.cr6.eq) {\n";
    emit_tail_call_line(ctx, "\t\t", name);
    old_line(ref, name);
    std::string want = ref.out;
    if (expect_musttail_if_plain)
      want = std::string("\tif (!ctx.cr6.eq) {\n\t\t[[clang::musttail]] return ") + name + "(ctx, base);\n";
    check(std::format("{} emit_tail_call_line {}", scenario, name), ctx.out, want);
  }
}

constexpr uint32_t kFn = 0x82000000;       // function under test: one block of 0x40 bytes
constexpr uint32_t kSetJmp = 0x82002000;   // setJmpAddress
uint32_t enc_b(uint32_t at, uint32_t target, bool lk) {  // b / bl, AA=0
  return (18u << 26) | ((target - at) & 0x03FFFFFCu) | (lk ? 1u : 0u);
}
uint32_t enc_bc(uint32_t at, uint32_t target) {  // bc 12,2 (beq), AA=0, LK=0
  return (16u << 26) | (12u << 21) | (2u << 16) | ((target - at) & 0xFFFCu);
}
void one_block(BuilderContext& c, uint32_t size = 0x40) { c.fn.blocks_ = {Block{kFn, size}}; }
}  // namespace

int main() {
  // 1. Flag off: old text for everything, whatever the function looks like.
  run_cases("flag_off", false, [](BuilderContext& c) { one_block(c); });
  run_cases("flag_off_seh", false, [](BuilderContext& c) {
    one_block(c);
    c.cfg.generateExceptionHandlers = true;
    c.fn.exc = ExceptionInfo{SehInfo{{1}}};
  });
  // 2. Flag on, plain function: musttail for the plain forms only.
  run_cases("flag_on", true, [](BuilderContext& c) {
    one_block(c);
    c.cfg.musttailCalls = true;
  });
  // 3. SEH: skipped only when the body is really wrapped (handlers on and scopes present).
  run_cases("seh_scopes", false, [](BuilderContext& c) {
    one_block(c);
    c.cfg.musttailCalls = c.cfg.generateExceptionHandlers = true;
    c.fn.exc = ExceptionInfo{SehInfo{{1, 2}}};
  });
  run_cases("seh_no_scopes", true, [](BuilderContext& c) {
    one_block(c);
    c.cfg.musttailCalls = c.cfg.generateExceptionHandlers = true;
    c.fn.exc = ExceptionInfo{SehInfo{}};
  });
  run_cases("seh_handlers_off", true, [](BuilderContext& c) {
    one_block(c);
    c.cfg.musttailCalls = true;
    c.fn.exc = ExceptionInfo{SehInfo{{1}}};
  });
  run_cases("exc_not_seh", true, [](BuilderContext& c) {
    one_block(c);
    c.cfg.musttailCalls = c.cfg.generateExceptionHandlers = true;
    c.fn.exc = ExceptionInfo{std::nullopt};
  });
  // 4. setjmp: any direct branch to setJmpAddress in the function disables musttail.
  auto setjmp_case = [](uint32_t insn_at, uint32_t word, uint32_t block_size = 0x40) {
    return [=](BuilderContext& c) {
      one_block(c, block_size);
      c.cfg.musttailCalls = true;
      c.cfg.setJmpAddress = kSetJmp;
      c.emitCtx.binary.put(insn_at, word);
    };
  };
  run_cases("setjmp_bl", false, setjmp_case(kFn + 8, enc_b(kFn + 8, kSetJmp, true)));
  run_cases("setjmp_b", false, setjmp_case(kFn + 0x3C, enc_b(kFn + 0x3C, kSetJmp, false)));
  run_cases("setjmp_bc", false, setjmp_case(kFn + 0x10, enc_bc(kFn + 0x10, kSetJmp)));
  run_cases("bl_elsewhere", true, setjmp_case(kFn + 8, enc_b(kFn + 8, kSetJmp + 4, true)));
  run_cases("setjmp_bl_past_block_end", true, setjmp_case(kFn + 0x40, enc_b(kFn + 0x40, kSetJmp, true)));
  run_cases("setjmp_bl_second_block", false, [](BuilderContext& c) {
    c.fn.blocks_ = {Block{kFn, 0x10}, Block{kFn + 0x100, 0x20}};
    c.cfg.musttailCalls = true;
    c.cfg.setJmpAddress = kSetJmp;
    c.emitCtx.binary.put(kFn + 0x118, enc_b(kFn + 0x118, kSetJmp, true));
  });
  run_cases("setjmp_unset", true, [](BuilderContext& c) {
    one_block(c);
    c.cfg.musttailCalls = true;
    c.cfg.setJmpAddress = 0;
    c.emitCtx.binary.put(kFn + 8, enc_b(kFn + 8, 0, true));
  });
  run_cases("block_outside_image", true, [](BuilderContext& c) {
    c.fn.blocks_ = {Block{0x90000000, 0x40}};
    c.cfg.musttailCalls = true;
    c.cfg.setJmpAddress = kSetJmp;
  });
  std::printf("emit_test: %d checks, %d failures\n", g_checks, g_fail);
  return g_fail;
}
