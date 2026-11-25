import subprocess, os, hashlib, re
WS = r'<workspace>'
W = os.path.join(WS, r'build\agent2\final\work')
OUT = os.path.join(WS, r'build\agent2\final\FINAL-DEFAULTS.diff')
FILES = [
 'DimensionsRecomp/rexglue-sdk/src/core/clock.cpp',
 'DimensionsRecomp/rexglue-sdk/src/core/timer_queue.cpp',
 'DimensionsRecomp/rexglue-sdk/src/graphics/shared_memory.cpp',
 'DimensionsRecomp/rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_rtl.cpp',
 'DimensionsRecomp/rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_threading.cpp',
 'DimensionsRecomp/rexglue-sdk/src/system/runtime.cpp',
 'DimensionsRecomp/rexglue-sdk/src/system/xmemory.cpp',
 'DimensionsRecomp/rexglue-sdk/src/system/xobject.cpp',
 'DimensionsRecomp/rexglue-sdk/src/system/xthread.cpp',
 'DimensionsRecomp/rexlego/src/gpu_wait_backoff.cpp',
 'DimensionsRecomp/rexlego/src/gpu_native/shaders.cpp',
]
out = b''
for f in FILES:
    r = subprocess.run(['git', '-c', 'core.autocrlf=false', '-c', 'core.safecrlf=false', 'diff', '--no-index',
                        '--no-color', '--no-ext-diff', '--full-index', '-U3', 'base/' + f, 'new/' + f],
                       cwd=W, capture_output=True)
    assert r.returncode == 1, (f, r.returncode, r.stderr)
    d = r.stdout
    d = d.replace(b'a/base/' + f.encode(), b'a/' + f.encode()).replace(b'b/new/' + f.encode(), b'b/' + f.encode())
    d = re.sub(rb'^index [0-9a-f]+\.\.[0-9a-f]+ 100644\n', b'', d, flags=re.M)  # blob ids of scratch copies: drop
    assert b'base/' not in d.split(b'@@')[0] and b'new/' not in d.split(b'@@')[0], f
    out += d
open(OUT, 'wb').write(out)
print('wrote', OUT, len(out), hashlib.sha256(out).hexdigest()[:16].upper())
for f in FILES:
    b = hashlib.sha256(open(os.path.join(W, 'base', f), 'rb').read()).hexdigest().upper()
    n = hashlib.sha256(open(os.path.join(W, 'new', f), 'rb').read()).hexdigest().upper()
    print(b[:16], '->', n[:16], f)
