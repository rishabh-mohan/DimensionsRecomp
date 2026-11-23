"""Rebuild a 'previous live-decode' textures.cpp for
DimensionsRecomp/tools/gpu-aot/test_texture_upload_retention_sdk.py --previous-textures.

git has no textures.cpp between the live-decode code (d94c2fd, whose upload function was still
called UploadTextureResource and declared endian_xor inside the decode region) and the
retained-source code (127e04b, v0.2.0). This starts from the v0.2.0 baseline textures.cpp and puts
back, verbatim from d94c2fd, the two pre-retention pieces the test probes:
  1. the decode loop's live guest-memory source pointer (instead of retained->Slice), and
  2. the old ReadableUploadSpan (no inherited E/F alias handling).
Usage: python bench/agent5/make_previous_textures.py build/agent5/prev/textures-previous-live.cpp
"""
from pathlib import Path
import subprocess, sys

root = Path(__file__).resolve().parents[2]
baseline = (root / 'baseline/DimensionsRecomp/rexlego/src/gpu_native/textures.cpp').read_text()
old = subprocess.run(['git', '-C', str(root / 'DimensionsRecomp'), 'show',
                      'd94c2fd:rexlego/src/gpu_native/textures.cpp'],
                     capture_output=True, text=True, check=True).stdout.replace('\r\n', '\n')


def block(text, signature):  # same brace matcher as the retention test
    start = text.index(signature); end = text.index('{', start) + 1; depth = 1
    while depth: depth += (text[end] == '{') - (text[end] == '}'); end += 1
    return text[start:end]


retained_source = ('      const auto source_bytes = retained->Slice(level != 0,base,\n'
                   '          TextureEndianExtent(guest_level.array_slice_data_extent_bytes,endian_xor));\n'
                   '      if (source_bytes.empty()) return false;\n'
                   '      const auto* source = source_bytes.data();\n')
live_source = ('      const auto* source = base < 0x20000000u\n'
               '          ? REX_KERNEL_MEMORY()->TranslatePhysical<const u8*>(base)\n'
               '          : REX_KERNEL_MEMORY()->TranslateVirtual<const u8*>(base);\n')
assert baseline.count(retained_source) == 1 and old.count(live_source) == 1
text = baseline.replace(retained_source, live_source)
text = text.replace(block(text, 'bool ReadableUploadSpan('), block(old, 'bool ReadableUploadSpan('))
assert block(text, 'bool ReadableUploadSpan(') == block(old, 'bool ReadableUploadSpan(')
out = Path(sys.argv[1]); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(text)
print(f'wrote {out} ({len(text)} chars)')
