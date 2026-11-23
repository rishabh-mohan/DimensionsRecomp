#!/usr/bin/env python3
"""Which hook objects are linked into each binary (read-only map scan)."""
import os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
maps = ['devoff2-bin', 'native2-bin', 'native3d-bin']
pats = ['settings_native_hooks.cpp.obj', 'main_menu_extras.cpp.obj', 'native_memops.cpp.obj',
        'native_markers.cpp.obj', 'native_saverest.cpp.obj', 'gpu_native', 'draw.cpp.obj',
        'queries.cpp.obj', 'hooks_device.cpp.obj', 'scene_distance.cpp.obj', 'native_settings_frontend',
        'tt_lock_trace.cpp.obj', 'area_watch', 'icon_probe.cpp.obj']
syms = ['sub_83E46040', 'sub_83E45090', 'sub_82A3E238', 'sub_82EFEFA0', 'sub_82FBE7A8', 'sub_82F03C40', 'sub_82FE4A80',
        'sub_82EFCB70', 'sub_82F0CCD8', 'sub_82EF3180', 'sub_83FB33E0', 'sub_83FB09E8']
for m in maps:
    path = os.path.join(ROOT, 'build', 'agent2', m, 'legodimensions.map')
    counts = {p: 0 for p in pats}
    shown = {p: 0 for p in pats}
    symlines = []
    with open(path, 'r', encoding='latin-1') as f:
        for line in f:
            for p in pats:
                if p in line:
                    counts[p] += 1
                    if shown[p] < 3:
                        shown[p] += 1
                        print('%s [%s] %s' % (m, p, line.rstrip()[:200]))
            if 'sub_8' in line:
                for s in syms:
                    if s in line:
                        symlines.append(line.rstrip()[:200])
                        break
    print('%s COUNTS %s' % (m, ' '.join('%s=%d' % (k, v) for k, v in counts.items())))
    for s in symlines[:60]:
        print('%s SYM %s' % (m, s))
    sys.stdout.flush()
