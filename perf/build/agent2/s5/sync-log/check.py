#!/usr/bin/env python3
# check.py (M2, S5 1.2): makes sync-log.diff (rexglue-sdk-relative, vs a7e79c0), runs `git apply --check
# --cached` against the SDK index at a7e79c0 (no working-tree or index change), and compile-checks the
# patched pipeline_cache.cpp with the final2 gpu-leg flags (fsyntax + a real -c into s5/sync-log/obj/).
# Writes only build/agent2/s5/sync-log/.
import difflib, hashlib, os, re, shlex, subprocess, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
A2 = os.path.join(R, 'build', 'agent2')
S = os.path.join(A2, 's5', 'sync-log')
SDK = os.path.join(R, 'DimensionsRecomp', 'rexglue-sdk')
REL = 'src/graphics/d3d12/pipeline_cache.cpp'
NEW = os.path.join(S, 'ov', 'rexglue-sdk', *REL.split('/'))
SNAP_D3D12 = os.path.join(A2, 'snap1', 'DimensionsRecomp', 'rexglue-sdk', 'src', 'graphics', 'd3d12')
F2_CMDS = os.path.join(A2, 'final2', 'b', 'gpu', 'log-on', 'recompile-commands.txt')
out = []


def say(s):
    out.append(s)
    print(s, flush=True)


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


fails = []


def check(what, ok, detail=''):
    say('%s %s%s' % ('PASS' if ok else 'FAIL', what, (': ' + detail) if detail else ''))
    if not ok:
        fails.append(what)


head = subprocess.run(['git', '-C', SDK, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
check('SDK HEAD == a7e79c0', head.startswith('a7e79c0'), head)
base = subprocess.run(['git', '-C', SDK, 'cat-file', 'blob', 'a7e79c0:' + REL], capture_output=True).stdout
new = open(NEW, 'rb').read()
check('patched file is LF-only like the blob', b'\r' not in new and b'\r' not in base)
say('base blob %s %s' % (REL, sha(base)))
say('new       %s %s' % (REL, sha(new)))
d = ''.join(difflib.unified_diff(base.decode('utf-8').splitlines(True), new.decode('utf-8').splitlines(True),
                                 'a/' + REL, 'b/' + REL, n=3))
diff = os.path.join(S, 'sync-log.diff')
with open(diff, 'w', encoding='utf-8', newline='\n') as f:
    f.write('diff --git a/%s b/%s\n' % (REL, REL) + d)
say('diff %s sha256 %s (+%d/-%d)' % (os.path.relpath(diff, R), sha(open(diff, 'rb').read()),
                                     sum(1 for l in d.splitlines() if l.startswith('+') and not l.startswith('+++')),
                                     sum(1 for l in d.splitlines() if l.startswith('-') and not l.startswith('---'))))
p = subprocess.run(['git', '-C', SDK, 'diff', '--cached', '--quiet'], capture_output=True)
check('SDK index clean (== HEAD a7e79c0)', p.returncode == 0)
p = subprocess.run(['git', '-C', SDK, 'apply', '--check', '--cached', '-v', diff], capture_output=True, text=True)
check('git apply --check --cached vs a7e79c0', p.returncode == 0, (p.stdout + p.stderr).strip().replace('\n', ' | '))

# compile: the final2 gpu-leg command for d3d12/pipeline_cache.cpp, source/obj swapped. -iquote snap1's d3d12
# dir resolves the "../shaders/bytecode/..." includes; "../frame_stats.h" resolves next to the overlay file
# (ov/.../graphics/frame_stats.h == the a7e79c0 blob).
cmd = None
for ln in open(F2_CMDS, encoding='utf-8'):
    if ln.startswith('cmd: ') and ln.rstrip().endswith('/d3d12/pipeline_cache.cpp'):
        cmd = ln[5:].strip()
check('final2 gpu command for d3d12/pipeline_cache.cpp found', cmd is not None)
fs = os.path.join(S, 'ov', 'rexglue-sdk', 'src', 'graphics', 'frame_stats.h')
fsb = subprocess.run(['git', '-C', SDK, 'cat-file', 'blob', 'a7e79c0:src/graphics/frame_stats.h'],
                     capture_output=True).stdout
check('overlay frame_stats.h == a7e79c0 blob', open(fs, 'rb').read() == fsb)
if cmd and not fails:
    args = shlex.split(cmd, posix=False)
    src_i = len(args) - 1
    args[src_i] = NEW.replace('\\', '/')
    o_i = args.index('-o')
    os.makedirs(os.path.join(S, 'obj'), exist_ok=True)
    obj = os.path.join(S, 'obj', 'd3d12__pipeline_cache.cpp.obj')
    args[o_i + 1] = obj
    args = [a.replace('\\"', '"') if a.startswith('-DREXGLUE_BUILD_CONFIG') or a.startswith('-DCMAKE_INTDIR')
            else a for a in args]
    args.insert(1, '-iquote' + SNAP_D3D12.replace('\\', '/'))
    old_pm = [a for a in args if a.startswith('-fmacro-prefix-map=')]
    args = [a for a in args if not a.startswith('-fmacro-prefix-map=')]
    say('dropped %s (not needed for a check build)' % old_pm)
    for mode, extra in (('fsyntax', ['-fsyntax-only']), ('compile', [])):
        a = list(args)
        if extra:
            a = [x for i, x in enumerate(a) if not (x == '-o' or (i > 0 and a[i - 1] == '-o')) and x != '-c']
            a.insert(1, extra[0])
        t0 = time.time()
        p = subprocess.run(a, capture_output=True, text=True, creationflags=0x00000040)  # IDLE_PRIORITY_CLASS
        log = (p.stdout + p.stderr)
        open(os.path.join(S, mode + '.log'), 'w', encoding='utf-8').write(' '.join(a) + '\n\n' + log)
        mine = [l for l in log.splitlines() if 'pipeline_cache.cpp' in l and ('warning' in l or 'error' in l)]
        check('%s exit 0 (%.1f s)' % (mode, time.time() - t0), p.returncode == 0,
              '%d errors, %d warnings in pipeline_cache.cpp' % (log.count('error:'), len(mine)))
        for l in mine:
            say('    ' + l)
    if os.path.isfile(obj):
        say('obj %s %d B %s' % (os.path.relpath(obj, R), os.path.getsize(obj), sha(open(obj, 'rb').read())))
        ob = open(obj, 'rb').read()
        for n in ('d3d12_log_sync_pipeline_creation', 'sync pipeline #{} {:016X}'):
            check('needle in obj: %s' % n, n.encode() in ob)
say('RESULT: %s' % ('PASS' if not fails else 'FAIL (%s)' % '; '.join(fails)))
open(os.path.join(S, 'check.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
sys.exit(1 if fails else 0)
