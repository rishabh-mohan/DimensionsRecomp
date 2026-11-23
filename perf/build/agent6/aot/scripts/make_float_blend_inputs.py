"""Write <HASH:016X>-vs-0-input.hlsl for every VERTEX dump file, byte-for-byte as
DimensionsRecomp/tools/gpu-aot/build_temporal_shader_bank.py would (its lines 19-23
source scan + line 33 'prepared' text for spec 0), WITHOUT running DXC / the motion
transform.  The result is a valid --source dir for build_float_blend_indices_bank.py
(which only globs '*-vs-0-input.hlsl').

Usage:
  make_float_blend_inputs.py <out-dir> --source <hlsl-dump> [--source ...]
                             [--compare <dir with reference *-vs-0-input.hlsl>]
                             [--blendindices-only]
Exit codes: 0 ok, 3 compare mismatch, 4 float-blend precheck would fail.
"""
import argparse
import hashlib
import re
import sys
import time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('output', type=Path)
p.add_argument('--source', type=Path, action='append', required=True)
p.add_argument('--compare', type=Path)
p.add_argument('--blendindices-only', action='store_true',
               help="write only VS containing 'BLENDINDICES0' (a superset of the float-blend selection)")
a = p.parse_args()
t0 = time.time()
out = a.output.resolve(); out.mkdir(parents=True, exist_ok=True)

# ---- verbatim: build_temporal_shader_bank.py lines 19-23 ----
sources={}
for folder in a.source:
 for path in folder.glob('*.hlsl'):
  text=path.read_text();match=re.search(r'// (vertex|pixel) shader\s+hash=0x([0-9A-Fa-f]+)',text[:300])
  if match:sources[int(match[2],16)]=(path,text,'vs' if match[1]=='vertex' else 'ps')
t_scan = time.time() - t0

# ---- line 31-33 (compile_shader), spec 0, vertex stage only ----
spec = 0
written = []
for hash_, (path, text, stage) in sorted(sources.items()):
    if stage != 'vs':
        continue
    if a.blendindices_only and 'BLENDINDICES0' not in text:
        continue
    stem = f'{hash_:016X}-{stage}-{spec}'
    prepared = out/(stem+'-input.hlsl')
    prepared.write_text(text.replace('uint g_SpecConstants();', f'uint g_SpecConstants() {{ return {spec}; }}'))
    written.append(prepared)

nvs = sum(1 for v in sources.values() if v[2] == 'vs')
nps = len(sources) - nvs
print(f'sources={len(sources)} (vs={nvs} ps={nps}) written={len(written)} scan_s={t_scan:.1f} total_s={time.time()-t0:.1f}')

# ---- precheck: mimic build_float_blend_indices_bank.py selection + its raise conditions (no DXC) ----
pat = r'\bin\s+uint4\s+iBlendIndices0\s*:\s*BLENDINDICES0\b'
sel = 0; problems = []
for path in sorted(out.glob('*-vs-0-input.hlsl')):
    text = path.read_text()
    if not re.search(pat, text):
        continue
    sel += 1
    if not re.search(r'// vertex shader\s+hash=0x([0-9A-Fa-f]+)', text[:300]): problems.append((path.name, 'identity'))
    if 'packoffset(c38)' not in text: problems.append((path.name, 'packoffset(c38)'))
    if text.count('uint g_SpecConstants() { return 0; }') != 1: problems.append((path.name, 'spec count'))
    if len(re.findall(pat, text)) != 1: problems.append((path.name, 'uint BLENDINDICES0 count'))
print(f'float-blend precheck: selected_vs={sel} jobs={2*sel} problems={len(problems)}')
for name, why in problems[:50]:
    print(f'  PROBLEM {name}: {why}')

rc = 0
if a.compare:
    refs = sorted(a.compare.glob('*-vs-0-input.hlsl'))
    same = diff = missing = 0
    for ref in refs:
        mine = out/ref.name
        rb = ref.read_bytes()
        if not mine.exists():
            missing += 1; print(f'  MISSING {ref.name}'); continue
        mb = mine.read_bytes()
        ok = mb == rb
        same += ok; diff += (not ok)
        print(f'  {"SAME" if ok else "DIFF"} {ref.name} {len(rb)} {hashlib.sha256(rb).hexdigest().upper()}'
              + ('' if ok else f' mine={len(mb)} {hashlib.sha256(mb).hexdigest().upper()}'))
    extra = sorted(set(x.name for x in written) - set(r.name for r in refs))
    print(f'compare: refs={len(refs)} identical={same} different={diff} missing={missing} extra_in_mine={len(extra)}')
    if diff or missing or extra:
        rc = 3
if problems and rc == 0:
    rc = 4
sys.exit(rc)
