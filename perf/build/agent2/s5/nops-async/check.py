#!/usr/bin/env python3
# check.py (M2, S5 Phase 2.1 nops-async): checks nops-async.diff (rexglue-sdk-relative, vs a7e79c0).
#   static (default): SDK HEAD/index, `git apply --check --cached` vs a7e79c0 (no index/worktree change),
#     composition with ../sync-log/sync-log.diff in both orders (scratch git repo in stk/), writes the
#     stacked file stk/<REL> (a7e79c0 + sync-log + nops-async = the TU for the test bin), and source needles
#     (cvar default false, kRequiresRestart, OFF path == HEAD condition).
#   --compile: also fsyntax of the nops-only file and fsyntax + -c of the stacked file, with the final2
#     gpu-leg command for d3d12/pipeline_cache.cpp (as sync-log/check.py), idle priority.
# Writes only build/agent2/s5/nops-async/.
import hashlib, os, shlex, shutil, subprocess, sys, time

S = os.path.dirname(os.path.abspath(__file__))
R = os.path.abspath(os.path.join(S, '..', '..', '..', '..'))
A2 = os.path.join(R, 'build', 'agent2')
SDK = os.path.join(R, 'DimensionsRecomp', 'rexglue-sdk')
REL = 'src/graphics/d3d12/pipeline_cache.cpp'
DIFF = os.path.join(S, 'nops-async.diff')
SYNC_DIFF = os.path.join(A2, 's5', 'sync-log', 'sync-log.diff')
NOPS_FILE = os.path.join(S, 'ov', *REL.split('/'))
STK = os.path.join(S, 'stk')
SNAP_D3D12 = os.path.join(A2, 'snap1', 'DimensionsRecomp', 'rexglue-sdk', 'src', 'graphics', 'd3d12')
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


def blob(path):
    return subprocess.run(['git', '-C', SDK, 'cat-file', 'blob', 'a7e79c0:' + path], capture_output=True).stdout


say('mode: %s' % ('static + compile' if COMPILE else 'static only (no compiler)'))
head = git('-C', SDK, 'rev-parse', 'HEAD').stdout.strip()
check('SDK HEAD == a7e79c0', head.startswith('a7e79c0'), head)
check('SDK index clean (== HEAD)', subprocess.run(['git', '-C', SDK, 'diff', '--cached', '--quiet']).returncode == 0)
base = blob(REL)
say('base blob %s %s' % (REL, sha(base)))
d = open(DIFF, 'rb').read()
say('nops-async.diff %s' % sha(d))
say('sync-log.diff   %s' % sha(open(SYNC_DIFF, 'rb').read()))
check('diff is LF-only', b'\r' not in d)
check('diff touches only %s' % REL,
      [l for l in d.decode().splitlines() if l.startswith('diff --git')] == ['diff --git a/%s b/%s' % (REL, REL)])
p = git('-C', SDK, 'apply', '--check', '--cached', '-v', DIFF)
check('git apply --check --cached vs a7e79c0', p.returncode == 0, (p.stdout + p.stderr).strip().replace('\n', ' | '))

# Composition in a scratch repo (both orders); the stacked file is kept for the test bin.
for order, diffs in (('sync-log then nops-async', [SYNC_DIFF, DIFF]), ('nops-async then sync-log', [DIFF, SYNC_DIFF])):
    tmp = os.path.join(S, 'stk-tmp')
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(os.path.dirname(os.path.join(tmp, *REL.split('/'))))
    open(os.path.join(tmp, *REL.split('/')), 'wb').write(base)
    git('init', '-q', cwd=tmp)
    ok, msg = True, []
    for df in diffs:
        p = git('apply', '-v', df, cwd=tmp)
        ok = ok and p.returncode == 0
        msg.append(os.path.basename(df) + ': ' + (p.stdout + p.stderr).strip().replace('\n', ' | '))
    res = open(os.path.join(tmp, *REL.split('/')), 'rb').read()
    check('compose %s' % order, ok, ' || '.join(msg))
    say('    result %s' % sha(res))
    if order.startswith('sync-log'):
        stacked = res
    else:
        check('both orders give the same file', res == stacked)
    shutil.rmtree(tmp, ignore_errors=True)
stk_file = os.path.join(STK, *REL.split('/'))
os.makedirs(os.path.dirname(stk_file), exist_ok=True)
open(stk_file, 'wb').write(stacked)
check('stacked file is LF-only', b'\r' not in stacked)
say('stacked file %s %s' % (os.path.relpath(stk_file, R), sha(stacked)))

# The overlay file must equal a7e79c0 + nops-async.diff.
tmp = os.path.join(S, 'stk-tmp')
shutil.rmtree(tmp, ignore_errors=True)
os.makedirs(os.path.dirname(os.path.join(tmp, *REL.split('/'))))
open(os.path.join(tmp, *REL.split('/')), 'wb').write(base)
git('init', '-q', cwd=tmp)
git('apply', DIFF, cwd=tmp)
check('ov file == a7e79c0 + nops-async.diff',
      open(os.path.join(tmp, *REL.split('/')), 'rb').read() == open(NOPS_FILE, 'rb').read())
shutil.rmtree(tmp, ignore_errors=True)

src = open(NOPS_FILE, encoding='utf-8').read()
for n in ('REXCVAR_DEFINE_BOOL(d3d12_async_depth_only_pipelines, false, "GPU/D3D12",',
          'bool async_depth_only_pipelines = false;',
          '      use_async || (async_depth_only_pipelines && pixel_shader == nullptr &&',
          '!vertex_shader->shader().memexport_eM_written()',
          'RenderTargetCache::Path::kHostRenderTargets',
          '  bool use_async = REXCVAR_GET(async_shader_compilation) && !creation_threads_.empty() &&\n'
          '                   pixel_shader != nullptr;\n'):
    check('needle in source: %s' % n.strip().splitlines()[0][:70], n in src)
i = src.index('REXCVAR_DEFINE_BOOL(d3d12_async_depth_only_pipelines')
check('cvar is kRequiresRestart', '.lifecycle(rex::cvar::Lifecycle::kRequiresRestart);' in src[i:i + 600].split(';')[0] + ';')
check('the only use of the latch outside Initialize is create_async',
      src.count('async_depth_only_pipelines &&') == 1 and src.count('if (async_depth_only_pipelines)') == 1)
check('if (use_async) replaced only in ConfigurePipeline (HEAD had 1)',
      base.decode().count('  if (use_async) {') == 1 and src.count('  if (use_async) {') == 0)

if COMPILE:
    cmd = None
    for ln in open(F2_CMDS, encoding='utf-8'):
        if ln.startswith('cmd: ') and ln.rstrip().endswith('/d3d12/pipeline_cache.cpp'):
            cmd = ln[5:].strip()
    check('final2 gpu command for d3d12/pipeline_cache.cpp found', cmd is not None)
    fsb = blob('src/graphics/frame_stats.h')
    for root in (os.path.join(S, 'ov'), STK):  # "../frame_stats.h" resolves next to the file
        open(os.path.join(root, 'src', 'graphics', 'frame_stats.h'), 'wb').write(fsb)
    if cmd and not fails:
        base_args = shlex.split(cmd, posix=False)
        base_args = [a.replace('\\"', '"') if a.startswith('-DREXGLUE_BUILD_CONFIG') or
                     a.startswith('-DCMAKE_INTDIR') else a for a in base_args]
        base_args.insert(1, '-iquote' + SNAP_D3D12.replace('\\', '/'))
        base_args = [a for a in base_args if not a.startswith('-fmacro-prefix-map=')]
        os.makedirs(os.path.join(S, 'obj'), exist_ok=True)
        obj = os.path.join(S, 'obj', 'stacked__pipeline_cache.cpp.obj')
        for name, f, modes in (('nops', NOPS_FILE, ('fsyntax',)), ('stacked', stk_file, ('fsyntax', 'compile'))):
            for mode in modes:
                a = list(base_args)
                a[len(a) - 1] = f.replace('\\', '/')
                a[a.index('-o') + 1] = obj
                if mode == 'fsyntax':
                    a = [x for i, x in enumerate(a) if not (x == '-o' or (i > 0 and a[i - 1] == '-o')) and x != '-c']
                    a.insert(1, '-fsyntax-only')
                t0 = time.time()
                p = subprocess.run(a, capture_output=True, text=True, creationflags=0x00000040)  # IDLE
                log = p.stdout + p.stderr
                open(os.path.join(S, '%s-%s.log' % (name, mode)), 'w', encoding='utf-8').write(' '.join(a) + '\n\n' + log)
                mine = [l for l in log.splitlines() if 'pipeline_cache.cpp' in l and ('warning' in l or 'error' in l)]
                check('%s %s exit 0 (%.1f s)' % (name, mode, time.time() - t0), p.returncode == 0,
                      '%d errors, %d warnings in pipeline_cache.cpp' % (log.count('error:'), len(mine)))
                for l in mine:
                    say('    ' + l)
        if os.path.isfile(obj):
            ob = open(obj, 'rb').read()
            say('obj %s %d B %s' % (os.path.relpath(obj, R), len(ob), sha(ob)))
            for n in ('d3d12_async_depth_only_pipelines', 'd3d12_log_sync_pipeline_creation',
                      'sync pipeline #{} {:016X}'):
                check('needle in obj: %s' % n, n.encode() in ob)

say('RESULT: %s' % ('PASS' if not fails else 'FAIL (%s)' % '; '.join(fails)))
open(os.path.join(S, 'check-compile.txt' if COMPILE else 'check.txt'), 'w', encoding='utf-8',
     newline='\n').write('\n'.join(out) + '\n')
sys.exit(1 if fails else 0)
