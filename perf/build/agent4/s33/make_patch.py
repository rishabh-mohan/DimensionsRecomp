"""S3.3 contingency (task #12, step 3): `|| !vs` on scratch copies only. NOT APPLIED.

Agent 1 (03:35): if native3d's n2/n3 still log hash=0, prepare `|| !vs` with its proof; don't apply it.

    python build/agent4/s33/make_patch.py

Reads the live draw.cpp, which must still hash to 5EA1F357... (batch 3, the S3.2 guard). Writes, next to this script:
  draw.before.cpp  exact copy of the live bytes
  draw.cpp         the same file with the guard's first comment line and its two code lines replaced
                   (line count unchanged, so no line numbers move)
  draw-s33.patch   git-style unified diff, paths relative to DimensionsRecomp/, CRLF content kept
It never writes the live file; a live write needs Agent 10's SAFE and Agent 1's GO.
"""
import difflib
import hashlib
from pathlib import Path

here = Path(__file__).resolve().parent
workspace = here.parents[2]
live = workspace / 'DimensionsRecomp/rexlego/src/gpu_native/draw.cpp'
LIVE_SHA = '5EA1F3576DCC2F90C7CBE410CFCDE093CB39D170A2BDD6259C3A85B41BE14410'
ANCHOR_LINE = 1498
ANCHOR = b'bool PrepareDrawGeometry(ParallelDrawWork& work, bool resolve_misses = false) {'
# 1-based line number -> (old bytes, new bytes)
CHANGES = {
    1499: (b'  // DispatchDraw drops a draw whose vertex shader failed to bind, so its geometry is never used.',
           b'  // DispatchDraw drops a draw whose vertex shader failed to bind or is unbound (address 0 never gets a pipeline),'
           b' so its geometry is never used.'),
    1502: (b'  BoundShaderAddress(ShaderStage::kVertex, &vertex_binding_failed);',
           b'  const u32 vs = BoundShaderAddress(ShaderStage::kVertex, &vertex_binding_failed);'),
    1503: (b'  if (vertex_binding_failed) return false;',
           b'  if (vertex_binding_failed || !vs) return false;'),
}
KEPT = {
    1500: b'  // Planning it anyway looks up hash 0 (one shader cache miss warning per lookup).',
    1501: b'  bool vertex_binding_failed = false;',
}
REL = b'rexlego/src/gpu_native/draw.cpp'
CRLF = b'\r\n'


def describe(name: str, data: bytes) -> str:
    return f'{name}: sha256 {hashlib.sha256(data).hexdigest().upper()} bytes {len(data):,} lines {data.count(CRLF):,}'


data = live.read_bytes()
sha = hashlib.sha256(data).hexdigest().upper()
assert sha == LIVE_SHA, f'live draw.cpp changed: {sha}'
parts = data.split(CRLF)
assert parts[-1] == b'', 'live file does not end with CRLF'
lines = parts[:-1]
assert not any(b'\r' in line or b'\n' in line for line in lines), 'bare CR or LF in the live file'
assert len(lines) == 5758, len(lines)
assert lines[ANCHOR_LINE - 1] == ANCHOR, lines[ANCHOR_LINE - 1]
assert data.count(ANCHOR) == 1
for n, text in KEPT.items():
    assert lines[n - 1] == text, (n, lines[n - 1])
patched_lines = list(lines)
for n, (old, new) in CHANGES.items():
    assert lines[n - 1] == old, (n, lines[n - 1])
    patched_lines[n - 1] = new
patched = CRLF.join(patched_lines) + CRLF
assert len(patched_lines) == 5758

old_lines = data.splitlines(keepends=True)
new_lines = patched.splitlines(keepends=True)
diff = difflib.diff_bytes(difflib.unified_diff, old_lines, new_lines, fromfile=b'a/' + REL, tofile=b'b/' + REL, n=3)
patch = b'diff --git a/' + REL + b' b/' + REL + b'\n' + b''.join(diff)

(here / 'draw.before.cpp').write_bytes(data)
(here / 'draw.cpp').write_bytes(patched)
(here / 'draw-s33.patch').write_bytes(patch)
print(describe('before', data))
print(describe('after ', patched))
print(f'patch : sha256 {hashlib.sha256(patch).hexdigest().upper()} bytes {len(patch):,}')
