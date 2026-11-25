#!/usr/bin/env python3
# deps-s33.py (M2, session 3): read-only. Which objects in snap1-sdk (Release) and snap1-off depend on the 4 files of
# the #33 patch? Uses `ninja -t deps` (reads .ninja_deps; builds nothing). Writes only --out.
import argparse, os, subprocess, sys

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
NINJA = r'C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe'
TARGETS = ['include/rex/graphics/d3d12/pipeline_cache.h', 'src/graphics/d3d12/command_processor.cpp',
           'src/graphics/d3d12/pipeline_cache.cpp', 'src/graphics/frame_stats.h',
           'include/rex/graphics/d3d12/command_processor.h']


def deps(bdir, f):
    args = [NINJA, '-C', bdir] + (['-f', f] if f else []) + ['-t', 'deps']
    p = subprocess.run(args, capture_output=True, text=True, creationflags=0x40)  # IDLE_PRIORITY_CLASS
    cur, out = None, {}
    for ln in p.stdout.splitlines():
        if ln and not ln.startswith(' '):
            cur = ln.split(':')[0]
            out[cur] = []
        elif ln.strip() and cur:
            out[cur].append(ln.strip().replace('\\', '/').lower())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    lines = []
    for nm, bdir, f in (('snap1-sdk Release', os.path.join(R, 'build/agent2/snap1-sdk'), 'build-Release.ninja'),
                        ('snap1-off', os.path.join(R, 'build/agent2/snap1-off'), None)):
        d = deps(bdir, f)
        lines.append('## %s: %d objects with deps' % (nm, len(d)))
        for t in TARGETS:
            hit = sorted(o for o, ds in d.items() if any(x.endswith('rexglue-sdk/' + t) for x in ds)
                         and ('/release/' in o.replace('\\', '/').lower() or f is None))
            lines.append('%s: %d' % (t, len(hit)))
            lines += ['    ' + h for h in hit]
        lines.append('')
    open(a.out, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    sys.exit(main())
