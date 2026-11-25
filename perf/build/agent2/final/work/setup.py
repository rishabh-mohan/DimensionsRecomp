import hashlib, shutil, os
WS = r'<workspace>'
W = os.path.join(WS, r'build\agent2\final\work')
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
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest().upper()
for f in FILES:
    live = os.path.join(WS, f)
    snap = os.path.join(WS, 'build', 'agent2', 'snap1', f) if not f.startswith('DimensionsRecomp/rexglue-sdk') else os.path.join(WS, 'build','agent2','snap1-sdk', f[len('DimensionsRecomp/rexglue-sdk/'):])
    hl = sha(live)
    hs = sha(snap) if os.path.exists(snap) else 'MISSING'
    crlf = b'\r\n' in open(live,'rb').read()
    for side in ('base','new'):
        d = os.path.join(W, side, f)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copyfile(live, d)
    print(f'{hl[:16]} snap={hs[:16]} {"SAME" if hl==hs else "DIFF"} crlf={crlf} {f}')
