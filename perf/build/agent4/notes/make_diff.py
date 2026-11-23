"""Write build/agent4/session2-diff.patch: Agent 4's owned edits vs baseline/ (unified, LF)."""
import difflib
from pathlib import Path

GPU = 'rexlego/src/gpu_native/'
FILES = ['draw.cpp', 'queries.cpp', 'long_probe.h', 'state_call_diagnostic.h',
         'draw_cached_flag.h', 'draw_log_throttle.h', 'draw_state_shadow.h']
out = []
for name in FILES:
    base = Path('baseline/DimensionsRecomp') / GPU / name
    dev = Path('DimensionsRecomp') / GPU / name
    a = base.read_text(encoding='utf-8').splitlines(keepends=False) if base.exists() else []
    b = dev.read_text(encoding='utf-8').splitlines(keepends=False)
    diff = list(difflib.unified_diff(a, b, f'a/{GPU}{name}' if a else '/dev/null', f'b/{GPU}{name}',
                                     n=3, lineterm=''))
    added = sum(1 for l in diff if l.startswith('+') and not l.startswith('+++'))
    removed = sum(1 for l in diff if l.startswith('-') and not l.startswith('---'))
    print(f'{name}: +{added} -{removed}')
    out += diff
Path('build/agent4/session2-diff.patch').write_text('\n'.join(out) + '\n', encoding='utf-8', newline='\n')
