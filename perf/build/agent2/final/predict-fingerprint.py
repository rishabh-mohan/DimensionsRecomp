"""Predict the native GPU fingerprint after FINAL-DEFAULTS.diff (read-only).
Reproduces generate-native-gpu-fingerprint.cmake from build/agent2/snap1-on: sha256 over the concatenated
lowercase hex sha256 of each input, first 16 hex chars. Then swaps in the after-hash of shaders.cpp."""
import hashlib, os, re, sys
WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))  # M10 N4
ON = os.path.join(WS, r'build\agent2\snap1-on')
NEW_SHADERS = os.path.join(WS, r'build\agent2\final\work\new\DimensionsRecomp\rexlego\src\gpu_native\shaders.cpp')
s = open(os.path.join(ON, 'generate-native-gpu-fingerprint.cmake'), encoding='utf-8').read()
inputs = re.search(r'set\(LEGO_NATIVE_GPU_FINGERPRINT_INPUTS "([^"]*)"\)', s).group(1).split(';')
pinned = open(os.path.join(ON, 'native-gpu-build.txt')).read().split()[-1]
def h(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
old_mat, new_mat, hit, total = '', '', 0, 0
for p in inputs:
    d = h(p); total += os.path.getsize(p)
    old_mat += d
    if p.replace('\\', '/').endswith('rexlego/src/gpu_native/shaders.cpp'):
        hit += 1
        print('shaders.cpp input:', p, d[:16].upper())
        d = h(NEW_SHADERS)
    new_mat += d
old_fp = hashlib.sha256(old_mat.encode()).hexdigest()[:16]
new_fp = hashlib.sha256(new_mat.encode()).hexdigest()[:16]
print(f'inputs {len(inputs)} ({total/1e6:.1f} MB), shaders.cpp matches {hit}')
print(f'pinned (snap1-on native-gpu-build.txt): {pinned}')
print(f'recomputed from current inputs:        {old_fp}  {"== pinned" if old_fp == pinned else "!= pinned"}')
print(f'predicted after FINAL-DEFAULTS.diff:   {new_fp}')
