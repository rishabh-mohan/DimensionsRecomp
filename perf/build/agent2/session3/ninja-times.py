#!/usr/bin/env python3
# ninja-times.py (M2, session 3): read-only. Per-output build times from .ninja_log for the TUs and links the
# session-3 bins rebuild (last entry per output). Writes only --out.
import argparse, os, sys

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
CG26 = [107, 116, 205, 321, 125, 153, 169, 284, 304, 432]
SDK_TU = ['d3d12/command_processor', 'd3d12/deferred_command_list', 'd3d12/graphics_system', 'd3d12/pipeline_cache',
          'd3d12/primitive_processor', 'd3d12/render_target_cache', 'd3d12/shared_memory', 'd3d12/texture_cache',
          'command_processor', 'shared_memory']


def load(p):
    last = {}
    for ln in open(p, encoding='utf-8', errors='replace'):
        if ln.startswith('#'):
            continue
        f = ln.rstrip('\n').split('\t')
        if len(f) >= 4:
            last[f[3].replace('\\', '/')] = (int(f[0]), int(f[1]))
    return last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    out = []
    g = load(os.path.join(R, 'build/agent2/snap1-off/.ninja_log'))
    out.append('## snap1-off (game, OFF): CG26 TUs')
    names = {}
    gen = os.path.join(R, 'build/agent2/snap1/DimensionsRecomp/rexlego/generated/default')
    tot = 0
    for k, (s, e) in g.items():
        for n in CG26:
            if k.endswith('generated/default/legodimensions_recomp.%d.cpp.obj' % n) or \
               k.endswith('generated/default/%d.cpp.obj' % n):
                names[n] = (k, (e - s) / 1000.0)
    for n in CG26:
        if n in names:
            tot += names[n][1]
            out.append('  %4d %7.1f s  %s' % (n, names[n][1], names[n][0]))
        else:
            out.append('  %4d  (no entry)' % n)
    out.append('  sum %.1f s (serial)' % tot)
    for k, (s, e) in g.items():
        if k.endswith('legodimensions.exe'):
            out.append('  link %s %.1f s' % (k, (e - s) / 1000.0))
    s = load(os.path.join(R, 'build/agent2/snap1-sdk/.ninja_log'))
    out.append('## snap1-sdk Release: #33 TUs and CTR TU')
    tot = 0
    for t in SDK_TU:
        key = 'src/graphics/CMakeFiles/rexgpu-xenos.dir/Release/%s.cpp.obj' % t
        if key in s:
            d = (s[key][1] - s[key][0]) / 1000.0
            tot += d
            out.append('  %7.1f s  %s' % (d, key))
        else:
            out.append('  (no entry) %s' % key)
    out.append('  sum %.1f s (serial)' % tot)
    for k, (st, e) in s.items():
        if k.lower().endswith('release/rexgpu-xenos.dll'):
            out.append('  link %s %.1f s' % (k, (e - st) / 1000.0))
    open(a.out, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
    print('\n'.join(out))


if __name__ == '__main__':
    sys.exit(main())
