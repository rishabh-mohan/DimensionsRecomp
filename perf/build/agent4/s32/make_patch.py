"""S3.2 fix (task #12, step 1): build the patched draw.cpp on scratch copies only.

    python build/agent4/s32/make_patch.py

Reads the live draw.cpp, which must still hash to 50AA3B1D... (batch 2). Writes, next to this script:
  draw.before.cpp  exact copy of the live bytes
  draw.cpp         the same file with 5 CRLF lines inserted after line 1498 (PrepareDrawGeometry's first line)
  draw-s32.patch   git-style unified diff, paths relative to DimensionsRecomp/, CRLF content kept
It never writes the live file; the live write happens only at Agent 1's GO (step 2).
"""
import difflib
import hashlib
from pathlib import Path

here = Path(__file__).resolve().parent
workspace = here.parents[2]
live = workspace / 'DimensionsRecomp/rexlego/src/gpu_native/draw.cpp'
LIVE_SHA = '50AA3B1DEE61567838076EDF19CB7A5466727C3CC31BE3A80E6DCC3722D7BDD6'
ANCHOR_LINE = 1498
ANCHOR = b'bool PrepareDrawGeometry(ParallelDrawWork& work, bool resolve_misses = false) {'
INSERT = [
    b'  // DispatchDraw drops a draw whose vertex shader failed to bind, so its geometry is never used.',
    b'  // Planning it anyway looks up hash 0 (one shader cache miss warning per lookup).',
    b'  bool vertex_binding_failed = false;',
    b'  BoundShaderAddress(ShaderStage::kVertex, &vertex_binding_failed);',
    b'  if (vertex_binding_failed) return false;',
]
REL = b'rexlego/src/gpu_native/draw.cpp'


CRLF = b'\r\n'


def describe(name: str, data: bytes) -> str:
    crlf_lines = data.count(CRLF)
    return f'{name}: sha256 {hashlib.sha256(data).hexdigest().upper()} bytes {len(data):,} lines {crlf_lines:,}'


data = live.read_bytes()
sha = hashlib.sha256(data).hexdigest().upper()
assert sha == LIVE_SHA, f'live draw.cpp changed: {sha}'
parts = data.split(b'\r\n')
assert parts[-1] == b'', 'live file does not end with CRLF'
lines = parts[:-1]
assert not any(b'\r' in line or b'\n' in line for line in lines), 'bare CR or LF in the live file'
assert len(lines) == 5753, len(lines)
assert lines[ANCHOR_LINE - 1] == ANCHOR, lines[ANCHOR_LINE - 1]
assert data.count(ANCHOR) == 1
assert b'vertex_binding_failed' not in b''.join(lines[ANCHOR_LINE - 1:ANCHOR_LINE + 60])

patched_lines = lines[:ANCHOR_LINE] + INSERT + lines[ANCHOR_LINE:]
patched = b'\r\n'.join(patched_lines) + b'\r\n'
assert len(patched_lines) == 5758

old = data.splitlines(keepends=True)
new = patched.splitlines(keepends=True)
diff = difflib.diff_bytes(difflib.unified_diff, old, new, fromfile=b'a/' + REL, tofile=b'b/' + REL, n=3)
patch = b'diff --git a/' + REL + b' b/' + REL + b'\n' + b''.join(diff)

(here / 'draw.before.cpp').write_bytes(data)
(here / 'draw.cpp').write_bytes(patched)
(here / 'draw-s32.patch').write_bytes(patch)
print(describe('before', data))
print(describe('after ', patched))
print(f'patch : sha256 {hashlib.sha256(patch).hexdigest().upper()} bytes {len(patch):,}')
