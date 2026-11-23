"""S3.3 contingency (task #12): build the scratch tree build/agent4/s33tree/DimensionsRecomp (read-only on live).

    python build/agent4/s33/make_tree.py

1. Compares every file of build/agent4/s32tree/DimensionsRecomp (made at 03:00 from live, no junctions) with live
   DimensionsRecomp, by sha256. draw.cpp is expected to match too (s32tree holds 5EA1F357..., which is live now).
2. Copies s32tree to s33tree (files only), refreshes from live every file that differs, and reports them.
3. Writes build/agent4/s33/draw.cpp (the `|| !vs` copy) into s33tree and checks its hash.
If step 1 finds a difference in a file that draw.cpp's compile reads (gpu_native or rexglue-sdk headers), the s32
objects are no longer a clean objdiff control: it says so, and a control must be compiled from s32tree refreshed.
Never writes outside build/agent4/.
"""
import hashlib
import shutil
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
workspace = here.parents[2]
live = workspace / 'DimensionsRecomp'
ref = workspace / 'build/agent4/s32tree/DimensionsRecomp'
dst = workspace / 'build/agent4/s33tree/DimensionsRecomp'
DRAW = Path('rexlego/src/gpu_native/draw.cpp')
LIVE_DRAW_SHA = '5EA1F3576DCC2F90C7CBE410CFCDE093CB39D170A2BDD6259C3A85B41BE14410'
S33_SHA = 'D348B82092F93A56DEF251806A17EC0A5AF0B9D14ACD006CECC49C3B1FA9A8D7'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


if dst.exists():
    print(f'FATAL: {dst} exists; remove it first')
    sys.exit(2)
rels = sorted(p.relative_to(ref) for p in ref.rglob('*') if p.is_file())
differ, missing = [], []
for rel in rels:
    src = live / rel
    if not src.is_file():
        missing.append(rel)
    elif sha(src) != sha(ref / rel):
        differ.append(rel)
print(f's32tree files: {len(rels)}; differ from live: {len(differ)}; missing in live: {len(missing)}')
for rel in differ:
    print(f'  differs: {rel.as_posix()}')
for rel in missing:
    print(f'  missing: {rel.as_posix()}')
assert sha(live / DRAW) == LIVE_DRAW_SHA, 'live draw.cpp changed'
compile_inputs = [r for r in differ if r.parts[:3] == ('rexlego', 'src', 'gpu_native') or r.parts[0] == 'rexglue-sdk']
if compile_inputs:
    print('NOTE: draw.cpp compile inputs changed since 03:00; compile a fresh control before objdiff')

shutil.copytree(ref, dst, symlinks=False)
for rel in differ:
    shutil.copy2(live / rel, dst / rel)
shutil.copy2(here / 'draw.cpp', dst / DRAW)
got = sha(dst / DRAW)
print(f's33tree draw.cpp: {got} ({"OK" if got == S33_SHA else "MISMATCH"})')
sys.exit(0 if got == S33_SHA else 1)
