"""S3.2 fix (task #12): static checks on a draw.cpp copy (read-only).

    python build/agent4/s32/static_check.py [draw.cpp ...]

Default: the live draw.cpp (before) and build/agent4/s32/draw.cpp (patched). For each file it prints:
  - where PrepareDrawGeometry starts and whether the failed-bind guard is its first statement;
  - every evaluated FindDxil( call (decltype is skipped) with its enclosing function;
  - every call of PrepareDrawGeometryLegacy(, PrepareDrawGeometry( and CaptureDrawGeometry( with its
    enclosing function and the nearest ShaderBindingsScope above it in that function (if any);
  - the recorder's failed-bind drop in DispatchDraw.
Exit 1 if, in a file that has the guard, a FindDxil or PrepareDrawGeometryLegacy call inside
PrepareDrawGeometry comes before the guard, or a Legacy call sits outside PrepareDrawGeometry.
"""
import re
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
workspace = here.parents[2]
DEFAULT = [workspace / 'DimensionsRecomp/rexlego/src/gpu_native/draw.cpp', here / 'draw.cpp']
FUNC = re.compile(r'^[A-Za-z_][\w:<>*&, ]*?\s+[*&]?(\w+)\(')
GUARD = ['  bool vertex_binding_failed = false;',
         '  BoundShaderAddress(ShaderStage::kVertex, &vertex_binding_failed);',
         '  if (vertex_binding_failed) return false;']


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

    def scope_above(n: int):
        start = enclosing(n)[0]
        for k in range(n - 1, start - 1, -1):
            if 'ShaderBindingsScope' in lines[k - 1]:
                return f'{k}: {lines[k - 1].strip()}'
        return 'none in this function'

    ok = True
    print(f'== {path}  ({len(lines) - 1} lines)')
    pdg = next(n for n, name in starts if name == 'PrepareDrawGeometry')
    body = lines[pdg:pdg + 5]
    guard_at = None
    for k in range(len(body) - 2):
        if [body[k], body[k + 1], body[k + 2]] == GUARD:
            guard_at = pdg + 1 + k
    print(f'PrepareDrawGeometry at {pdg}: guard ' + (f'at {guard_at}-{guard_at + 2}' if guard_at else 'absent'))
    if guard_at:
        first = next(k for k in range(pdg + 1, guard_at + 3) if not lines[k - 1].strip().startswith('//'))
        print(f'  first statement at {first} is the guard: {first == guard_at}')
        ok &= first == guard_at
    for name in ('FindDxil', 'PrepareDrawGeometryLegacy', 'PrepareDrawGeometry', 'CaptureDrawGeometry'):
        print(f'{name}( calls:')
        for n, text in enumerate(lines, 1):
            if not re.search(r'\b' + name + r'\(', text) or 'decltype(' + name in text:
                continue
            fn_line, fn = enclosing(n)
            if fn_line == n:
                continue  # the definition itself
            note = ''
            if name in ('PrepareDrawGeometry', 'CaptureDrawGeometry'):
                note = f'  [scope: {scope_above(n)}]'
            if guard_at and fn == 'PrepareDrawGeometry' and name in ('FindDxil', 'PrepareDrawGeometryLegacy'):
                after = n > guard_at + 2
                note = f'  [after guard: {after}]'
                ok &= after
            if guard_at and name == 'PrepareDrawGeometryLegacy' and fn != 'PrepareDrawGeometry':
                note = '  [OUTSIDE PrepareDrawGeometry]'
                ok = False
            print(f'  {n} in {fn} ({fn_line}){note}')
    dispatch = next(n for n, name in starts if name == 'DispatchDraw')
    drop = next(n for n in range(dispatch, len(lines)) if lines[n - 1].strip() == 'if (vertex_binding_failed) {')
    print(f'DispatchDraw at {dispatch}: failed-bind drop at {drop}')
    return ok


paths = [Path(p) for p in sys.argv[1:]] or DEFAULT
results = [check(p) for p in paths]
print('static check:', 'OK' if all(results) else 'FAIL')
sys.exit(0 if all(results) else 1)
