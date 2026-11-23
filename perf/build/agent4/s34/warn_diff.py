"""S3.4: compare the clang warnings of the patched and control shaders.cpp compiles, per ISA.

    python build/agent4/s34/warn_diff.py

Warnings are keyed by (file name, message, flag); line and column numbers are dropped because the patch shifts
shaders.cpp lines. Prints the counts and every key whose count differs between control and patched.
"""
import re
from collections import Counter
from pathlib import Path

here = Path(__file__).resolve().parent
WARN = re.compile(r'^(?P<file>.*?)(?:\((?P<l1>\d+),(?P<c1>\d+)\)|:(?P<l2>\d+):(?P<c2>\d+)):\s*warning:\s*(?P<msg>.*?)(?:\s*\[(?P<flag>-W[^\]]+)\])?\s*$')


def warnings(log: Path) -> Counter:
    keys = Counter()
    for line in log.read_text(encoding='utf-8', errors='replace').splitlines():
        m = WARN.match(line.strip())
        if m:
            keys[(Path(m.group('file').replace('\\', '/')).name, m.group('msg'), m.group('flag') or '')] += 1
    return keys


status = 0
for isa in ('v3', 'v2'):
    control_log, patched_log = here / f'compile-{isa}-control.log', here / f'compile-{isa}-patched.log'
    if not (control_log.exists() and patched_log.exists()):
        print(f'{isa}: missing log(s)')
        status = 1
        continue
    control, patched = warnings(control_log), warnings(patched_log)
    print(f'{isa}: control {sum(control.values())} warnings, patched {sum(patched.values())} warnings')
    in_shaders = sum(n for (name, _, _), n in patched.items() if name == 'shaders.cpp')
    print(f'{isa}: patched warnings located in shaders.cpp itself: {in_shaders}')
    changed = sorted(k for k in set(control) | set(patched) if control[k] != patched[k])
    for key in changed:
        print(f'  {isa} DIFF control={control[key]} patched={patched[key]} :: {key[0]} :: {key[1]} {key[2]}')
        status = 1
    if not changed:
        print(f'{isa}: identical warning set (by file, message, flag)')
raise SystemExit(status)
