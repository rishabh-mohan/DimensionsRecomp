"""Agent 5 item 2 driver: compile bench/agent5/test_decode_poison_sdk.cpp around the production
textures.cpp decode loop (extracted like tools/gpu-aot/test_texture_upload_retention_sdk.py does)
and two mutants that must fail: the loop without the row-padding zeroing and without the
alignment-gap zeroing.
Usage (devshell, workspace root):
  python bench/agent5/test_decode_poison_sdk.py --sdk build/sdk/install --runtime-dir build/sdk/install/bin
"""
from pathlib import Path
import argparse, shutil, subprocess, sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--sdk', type=Path, required=True)
p.add_argument('--runtime-dir', type=Path, required=True)
p.add_argument('--out', type=Path, default=None)
a = p.parse_args()
root = Path(__file__).resolve().parents[2]
src = root / 'DimensionsRecomp/rexlego/src'
out = (a.out or root / 'build/agent5/decode-poison').resolve(); out.mkdir(parents=True, exist_ok=True)
sdk = a.sdk.resolve()
text = (src / 'gpu_native/textures.cpp').read_text()
format_text = (src / 'gpu_native/format.cpp').read_text()


def block(text, signature):
    start = text.index(signature); end = text.index('{', start) + 1; depth = 1
    while depth: depth += (text[end] == '{') - (text[end] == '}'); end += 1
    return text[start:end]


helpers = '\n'.join([block(text, s) for s in ['bool ReadableUploadSpan(', 'bool CopyTextureUploadSpan(', 'u32 AlignUp(',
                     'u32 MipDimension(', 'u32 RowPitch(', 'u32 RowCount(', 'u32 LevelSize(']] +
                    [block(format_text, s) for s in ['bool IsBlockCompressedFormat(', 'u32 FormatBlockBytes(']])
upload = block(text, 'bool UploadTextureResourceStorage(')
start = upload.index('    u32 destination_offset = 0;', upload.index('TextureDecodeScratch decoded(upload_size)'))
loop = upload[start:upload.index('    DumpTextureUpload', start)]
gap = 'std::memset(mapped + destination_offset, 0, aligned_offset - destination_offset);'
assert loop.count(gap) == 1 and loop.count('ZeroTextureRowPadding(') == 3, 'decode loop changed; update the mutants'
variants = [('production', loop, 0),
            ('no-row-padding', '#define ZeroTextureRowPadding(...) ((void)0)\n' + loop, 23),
            ('no-gap-zero', loop.replace(gap, '(void)0;'), 23)]
shutil.copy2(a.runtime_dir / 'rexruntime.dll', out / 'rexruntime.dll')
(out / 'retained-helpers.inc').write_text(helpers)
fixture = Path(__file__).with_name('test_decode_poison_sdk.cpp')
failed = False
for label, code, expected in variants:
    (out / 'retained-decode.inc').write_text(code)
    exe = out / (label + '.exe')
    r = subprocess.run(['clang-cl', str(fixture), '/std:c++latest', '/O2', '/MD', '/EHsc', '/D_CRT_SECURE_NO_WARNINGS',
                        '/I' + str(out), '/I' + str(src), '/I' + str(sdk / 'include'),
                        '/I' + str(root / 'DimensionsRecomp/thirdparty/plume'), '/Fo' + str(out) + '/', '/Fe' + str(exe),
                        '/link', str(sdk / 'lib/rexruntime.lib'), 'kernel32.lib', 'user32.lib'],
                       capture_output=True, text=True, timeout=120)
    (out / (label + '-compile.log')).write_text(r.stdout + r.stderr)
    if r.returncode:
        print(f'{label}: COMPILE FAILED (see {out / (label + "-compile.log")})\n{r.stdout[-3000:]}{r.stderr[-3000:]}')
        failed = True; continue
    r = subprocess.run([str(exe)], cwd=out, capture_output=True, text=True, timeout=300)
    (out / (label + '.log')).write_text(r.stdout + r.stderr)
    ok = r.returncode == expected
    failed |= not ok
    print(f'{label}: exit {r.returncode} (expected {expected}) {"ok" if ok else "FAIL"}: '
          f'{(r.stdout + r.stderr).strip()[:400]}')
sys.exit(1 if failed else 0)
