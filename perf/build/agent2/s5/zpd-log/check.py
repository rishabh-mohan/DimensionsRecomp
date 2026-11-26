#!/usr/bin/env python3
# check.py (M2, S5 S1 zpd-log): checks zpd-log.diff (rexglue-sdk-relative, vs a7e79c0).
#   static (default): SDK HEAD/index, base/ == a7e79c0 blob == snap1 file (LF-normalised),
#     `git apply --check --cached` vs a7e79c0 (no index/worktree change), ov == a7e79c0 + diff in a
#     scratch repo, LF-only, source needles (cvar default false, log only behind the cvar).
#   --compile: also fsyntax + -c of the ov file with the final2 gpu-leg command for
#     d3d12/command_processor.cpp, idle priority.
# Writes only build/agent2/s5/zpd-log/.
import hashlib, os, shlex, shutil, subprocess, sys, time

S = os.path.dirname(os.path.abspath(__file__))
R = os.path.abspath(os.path.join(S, '..', '..', '..', '..'))
A2 = os.path.join(R, 'build', 'agent2')
SDK = os.path.join(R, 'DimensionsRecomp', 'rexglue-sdk')
REL = 'src/graphics/d3d12/command_processor.cpp'
DIFF = os.path.join(S, 'zpd-log.diff')
OV_FILE = os.path.join(S, 'ov', *REL.split('/'))
BASE_FILE = os.path.join(S, 'base', 'command_processor.cpp')
SNAP_D3D12 = os.path.join(A2, 'snap1', 'DimensionsRecomp', 'rexglue-sdk', 'src', 'graphics', 'd3d12')
F2_OV = os.path.join(A2, 'final2', 'b', 'DimensionsRecomp', 'rexglue-sdk', 'src', 'graphics')
F2_CMDS = os.path.join(A2, 'final2', 'b', 'gpu', 'log-on', 'recompile-commands.txt')
COMPILE = '--compile' in sys.argv
out, fails = [], []


def say(s):
    out.append(s)
    print(s, flush=True)


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def check(what, ok, detail=''):
    say('%s %s%s' % ('PASS' if ok else 'FAIL', what, (': ' + detail) if detail else ''))
    if not ok:
        fails.append(what)


def git(*a, cwd=None):
    pre = ['-c', 'core.autocrlf=false', '-c', 'core.eol=lf'] if cwd else []  # scratch repos: keep LF
    return subprocess.run(['git'] + pre + list(a), capture_output=True, text=True, cwd=cwd)


say('mode: %s' % ('static + compile' if COMPILE else 'static only (no compiler)'))
head = git('-C', SDK, 'rev-parse', 'HEAD').stdout.strip()
check('SDK HEAD == a7e79c0', head.startswith('a7e79c0'), head)
check('SDK index clean (== HEAD)', subprocess.run(['git', '-C', SDK, 'diff', '--cached', '--quiet']).returncode == 0)
blob = subprocess.run(['git', '-C', SDK, 'cat-file', 'blob', 'a7e79c0:' + REL], capture_output=True).stdout
base = open(BASE_FILE, 'rb').read()
snap = open(os.path.join(F2_OV, 'd3d12', 'command_processor.cpp'), 'rb').read()
say('a7e79c0 blob %s %s' % (REL, sha(blob)))
check('base/ == a7e79c0 blob (LF)', base == blob.replace(b'\r\n', b'\n'), sha(base))
check('final2 overlay file (the devfinal2 TU) == a7e79c0 blob (LF-normalised)',
      snap.replace(b'\r\n', b'\n') == base, sha(snap))
d = open(DIFF, 'rb').read()
say('zpd-log.diff %s' % sha(d))
check('diff is LF-only', b'\r' not in d)
check('diff touches only %s' % REL,
      [l for l in d.decode().splitlines() if l.startswith('diff --git')] == ['diff --git a/%s b/%s' % (REL, REL)])
check('diff only adds lines', not [l for l in d.decode().splitlines() if l.startswith('-') and not l.startswith('---')])
p = git('-C', SDK, 'apply', '--check', '--cached', '-v', DIFF)
check('git apply --check --cached vs a7e79c0', p.returncode == 0, (p.stdout + p.stderr).strip().replace('\n', ' | '))

tmp = os.path.join(S, 'tmp')
shutil.rmtree(tmp, ignore_errors=True)
os.makedirs(os.path.dirname(os.path.join(tmp, *REL.split('/'))))
open(os.path.join(tmp, *REL.split('/')), 'wb').write(base)
git('init', '-q', cwd=tmp)
p = git('apply', '-v', DIFF, cwd=tmp)
check('git apply in scratch copy', p.returncode == 0, (p.stdout + p.stderr).strip().replace('\n', ' | '))
ov = open(OV_FILE, 'rb').read()
check('ov file == a7e79c0 + zpd-log.diff', open(os.path.join(tmp, *REL.split('/')), 'rb').read() == ov)
shutil.rmtree(tmp, ignore_errors=True)
check('ov file is LF-only', b'\r' not in ov)
say('ov file %s %s' % (os.path.relpath(OV_FILE, R), sha(ov)))

src = ov.decode('utf-8')
for n in ('REXCVAR_DEFINE_BOOL(d3d12_log_occlusion_queries, false, "GPU/D3D12",',
          '  if (!REXCVAR_GET(d3d12_log_occlusion_queries)) {\n    return;\n  }\n',
          '  OcclusionQueryPacketScope occlusion_query_packet_scope(frame_current_);\n',
          '  LogOcclusionQueries("shutdown", frame_current_);\n  ShutdownOcclusionQueryResources();\n'):
    check('needle in source: %s' % n.strip().splitlines()[0][:70], n in src)
check('REXGPU_INFO for the counters only inside LogOcclusionQueries',
      src.count('"d3d12_occlusion_queries (') == 1 and
      src.index('"d3d12_occlusion_queries (') > src.index('void LogOcclusionQueries('))

if COMPILE:
    cmd = None
    for ln in open(F2_CMDS, encoding='utf-8'):
        if ln.startswith('cmd: ') and ln.rstrip().endswith('/d3d12/command_processor.cpp'):
            cmd = ln[5:].strip()
    check('final2 gpu command for d3d12/command_processor.cpp found', cmd is not None)
    for h in ('frame_stats.h', 'memexport_trace.h', 'gpu_inventory.h'):  # "../x.h" resolves next to the file
        shutil.copyfile(os.path.join(F2_OV, h), os.path.join(S, 'ov', 'src', 'graphics', h))
    if cmd and not fails:
        base_args = shlex.split(cmd, posix=False)
        base_args = [a.replace('\\"', '"') if a.startswith('-DREXGLUE_BUILD_CONFIG') or
                     a.startswith('-DCMAKE_INTDIR') else a for a in base_args]
        base_args.insert(1, '-iquote' + SNAP_D3D12.replace('\\', '/'))  # "../x.h" from snap1's d3d12/
        base_args = [a for a in base_args if not a.startswith('-fmacro-prefix-map=')]
        os.makedirs(os.path.join(S, 'obj'), exist_ok=True)
        obj = os.path.join(S, 'obj', 'zpd__command_processor.cpp.obj')
        for mode in ('fsyntax', 'compile'):
            a = list(base_args)
            a[len(a) - 1] = OV_FILE.replace('\\', '/')
            a[a.index('-o') + 1] = obj
            if mode == 'fsyntax':
                a = [x for i, x in enumerate(a) if not (x == '-o' or (i > 0 and a[i - 1] == '-o')) and x != '-c']
                a.insert(1, '-fsyntax-only')
            t0 = time.time()
            p = subprocess.run(a, capture_output=True, text=True, creationflags=0x00000040)  # IDLE
            log = p.stdout + p.stderr
            open(os.path.join(S, 'zpd-%s.log' % mode), 'w', encoding='utf-8').write(' '.join(a) + '\n\n' + log)
            mine = [l for l in log.splitlines() if 'command_processor.cpp' in l and ('warning' in l or 'error' in l)]
            check('zpd %s exit 0 (%.1f s)' % (mode, time.time() - t0), p.returncode == 0,
                  '%d errors, %d warnings in command_processor.cpp' % (log.count('error:'), len(mine)))
            for l in mine:
                say('    ' + l)
        if os.path.isfile(obj):
            ob = open(obj, 'rb').read()
            say('obj %s %d B %s' % (os.path.relpath(obj, R), len(ob), sha(ob)))
            for n in ('d3d12_log_occlusion_queries', 'd3d12_occlusion_queries ({}): frame={}',
                      'end without an active query'):
                check('needle in obj: %s' % n, n.encode() in ob)

say('RESULT: %s' % ('PASS' if not fails else 'FAIL (%s)' % '; '.join(fails)))
open(os.path.join(S, 'check-compile.txt' if COMPILE else 'check.txt'), 'w', encoding='utf-8',
     newline='\n').write('\n'.join(out) + '\n')
sys.exit(1 if fails else 0)
