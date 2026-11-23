"""S3.3 contingency (task #12): static checks for `|| !vs` on a draw.cpp copy (read-only).

    python build/agent4/s33/static_check.py [draw.cpp ...]

Default: the live draw.cpp (batch 3) and build/agent4/s33/draw.cpp (patched). For each file it prints, and checks:
  1. PrepareDrawGeometry: where the guard is, whether it is the first statement, whether it has `|| !vs`,
     and that `vs` is used only by the guard there;
  2. every evaluated FindDxil( call (decltype is skipped) with its enclosing function; in PrepareDrawGeometry
     they must all come after the guard;
  3. GetPipeline: its `!vs` check comes before the only places that publish a pipeline
     (CompilePipelineAsync( and g_pipelines.emplace();
  4. DispatchDraw: the failed-bind drop, then the null-pipeline drop (`if (!pipeline) {` ... long-probe event
     draw_pipeline_unavailable ... `return false;`), and every FindDxil( call in DispatchDraw after that drop.
Exit 1 if a check fails.
"""
import re
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
workspace = here.parents[2]
DEFAULT = [workspace / 'DimensionsRecomp/rexlego/src/gpu_native/draw.cpp', here / 'draw.cpp']
FUNC = re.compile(r'^[A-Za-z_][\w:<>*&, ]*?\s+[*&]?(\w+)\(')
GUARD_S32 = ['  bool vertex_binding_failed = false;',
             '  BoundShaderAddress(ShaderStage::kVertex, &vertex_binding_failed);',
             '  if (vertex_binding_failed) return false;']
GUARD_S33 = ['  bool vertex_binding_failed = false;',
             '  const u32 vs = BoundShaderAddress(ShaderStage::kVertex, &vertex_binding_failed);',
             '  if (vertex_binding_failed || !vs) return false;']


def check(path: Path) -> bool:
    lines = path.read_bytes().decode('utf-8').split('\r\n')
    starts = []  # (line number, function name) of column-0 definitions
    for n, text in enumerate(lines, 1):
        m = FUNC.match(text)
        if m and not text.rstrip().endswith(';'):
            starts.append((n, m.group(1)))

    def enclosing(n: int):
        best = (0, '?')
        for s in starts:
            if s[0] <= n:
                best = s
            else:
                break
        return best

    def body_end(start: int) -> int:
        return next(n for n in range(start + 1, len(lines) + 1) if lines[n - 1] == '}')

    ok = True
    print(f'== {path}  ({len(lines) - 1} lines)')

    # 1. the guard
    pdg = next(n for n, name in starts if name == 'PrepareDrawGeometry')
    pdg_end = body_end(pdg)
    guard_at, kind = None, None
    for k in range(pdg + 1, pdg + 6):
        for name, guard in (('s32', GUARD_S32), ('s33 (|| !vs)', GUARD_S33)):
            if lines[k - 1:k + 2] == guard:
                guard_at, kind = k, name
    print(f'PrepareDrawGeometry {pdg}-{pdg_end}: guard ' + (f'{kind} at {guard_at}-{guard_at + 2}' if guard_at else 'absent'))
    if not guard_at:
        return False
    first = next(k for k in range(pdg + 1, guard_at + 3) if not lines[k - 1].strip().startswith('//'))
    print(f'  first statement at {first} is the guard: {first == guard_at}')
    ok &= first == guard_at
    vs_uses = [n for n in range(pdg, pdg_end + 1) if re.search(r'\bvs\b', lines[n - 1])]
    print(f'  lines naming `vs` in PrepareDrawGeometry: {vs_uses}')
    if kind.startswith('s33'):
        ok &= vs_uses == [guard_at + 1, guard_at + 2]
    else:
        ok &= vs_uses == []

    # 2. FindDxil calls
    find_calls = []
    for n, text in enumerate(lines, 1):
        if re.search(r'\bFindDxil\(', text) and 'decltype(FindDxil' not in text:
            fn_line, fn = enclosing(n)
            if fn_line != n:
                find_calls.append((n, fn, fn_line))
    print('FindDxil( calls: ' + ', '.join(f'{n} in {fn}' for n, fn, _ in find_calls))
    for n, fn, _ in find_calls:
        if fn == 'PrepareDrawGeometry' and n <= guard_at + 2:
            print(f'  FAIL: FindDxil at {n} comes before the guard')
            ok = False

    # 3. GetPipeline publishes a pipeline only after its !vs check
    gp = next(n for n, name in starts if name == 'GetPipeline')
    gp_end = body_end(gp)
    vs_check = [n for n in range(gp, gp_end) if lines[n - 1].strip() == 'if (!vs || (key.pixel_shader && !ps)) {']
    publish = [n for n in range(gp, gp_end) if 'CompilePipelineAsync(' in lines[n - 1] or 'g_pipelines.emplace(' in lines[n - 1]]
    vs_def = [n for n in range(gp, gp_end) if re.match(r'\s*auto\* vs = ', lines[n - 1])]
    print(f'GetPipeline {gp}-{gp_end}: vs defined at {vs_def}, !vs check at {vs_check}, publishes at {publish}')
    good = len(vs_check) == 1 and len(vs_def) == 1 and publish and vs_def[0] < vs_check[0] < min(publish)
    if not good:
        print('  FAIL: GetPipeline shape changed')
    ok &= bool(good)

    # 4. DispatchDraw drops
    dd = next(n for n, name in starts if name == 'DispatchDraw')
    dd_end = body_end(dd)
    failed_drop = next(n for n in range(dd, dd_end) if lines[n - 1].strip() == 'if (vertex_binding_failed) {')
    null_drop = next(n for n in range(dd, dd_end) if lines[n - 1].strip() == 'if (!pipeline) {')
    block = lines[null_drop - 1:null_drop + 10]
    close = next(i for i, text in enumerate(block) if text.strip() == '}')
    drop_ok = (any('"draw_pipeline_unavailable"' in text for text in block[:close])
               and block[close - 1].strip() == 'return false;')
    dd_finds = [n for n, fn, _ in find_calls if fn == 'DispatchDraw']
    print(f'DispatchDraw {dd}-{dd_end}: failed-bind drop at {failed_drop}, null-pipeline drop {null_drop}-{null_drop + close} '
          f'(returns: {drop_ok}), FindDxil at {dd_finds}')
    good = drop_ok and failed_drop < null_drop and all(n > null_drop + close for n in dd_finds)
    if not good:
        print('  FAIL: DispatchDraw order changed')
    ok &= bool(good)
    return ok


paths = [Path(p) for p in sys.argv[1:]] or DEFAULT
results = [check(p) for p in paths]
print('static check:', 'OK' if all(results) else 'FAIL')
sys.exit(0 if all(results) else 1)
