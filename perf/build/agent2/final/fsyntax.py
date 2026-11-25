#!/usr/bin/env python3
# fsyntax.py (M2, 2026-11-25): step 1 of BUILD-STEPS.md (D4 of rating C20B6FDB). `clang -fsyntax-only` of every
# FINAL-DEFAULTS TU with its own ccdb flags, before any real compile. Writes only build/agent2/final/b/fsyntax/.
#
#   python build/agent2/final/fsyntax.py [--jobs 8] [--dry-run]
#
# Needs prep-final.py's b/<leg>/list-on.tsv. For each set it runs `recompile.py --dry-run` (which builds the exact ON
# command lines into b/fsyntax/<set>/recompile-commands.txt and compiles nothing), then reruns each command with the
# `-o <obj>` pair removed and `-fsyntax-only` added after the compiler. recompile.py already refuses -MF/-MD/-MMD/
# -MT/-MQ, and this script re-checks that, so no file is written anywhere. Sets:
#   rt (8 SDK TUs) and gpu (shared_memory.cpp): snap1-sdk ccdb, /Release/ entries;
#   xe (gpu_wait_backoff.cpp, snap1-off flags) and xeoff (+ -DLEGO_GPU_WAIT_BACKOFF_DEFAULT_US=-1);
#   nat (shaders.cpp + the 3 header users, snap1-on flags, -I b/nat/gen-on first) and natoff
#   (+ -DLEGO_NATIVE_SHADER_MISS_CACHE_DEFAULT=0).
# PASS = every command exits 0. Diagnostics (warnings) are listed per TU; logs in b/fsyntax/<set>/<tu>.log.
import argparse, os, re, subprocess, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
A2 = os.path.join(R, 'build', 'agent2')
B = os.path.join(A2, 'final', 'b')
OV = os.path.join(B, 'DimensionsRecomp')
SNAP = os.path.join(A2, 'snap1', 'DimensionsRecomp')
HOLD = os.path.join(R, 'perf-notes', 'WINDOW-HOLD.txt')
SDK_CCDB = os.path.join(A2, 'snap1-sdk', 'compile_commands.json')
BAD = ('-MF', '-MD', '-MMD', '-MT', '-MQ', '/Fo', '/Fd', '-ftime-trace')


def pm(sub):
    o, s = os.path.join(OV, sub).replace('\\', '/'), os.path.join(SNAP, sub).replace('\\', '/')
    return '--flag=-fmacro-prefix-map=%s=%s' % (o, s)


SETS = [
    ('rt', 'rt', ['--ccdb', SDK_CCDB, '--obj-filter', '/Release/', pm('rexglue-sdk')]),
    ('gpu', 'gpu', ['--ccdb', SDK_CCDB, '--obj-filter', '/Release/', pm('rexglue-sdk')]),
    ('xe', 'xe', ['--ccdb', os.path.join(A2, 'snap1-off', 'compile_commands.json'), pm('rexlego')]),
    ('xeoff', 'xeoff', ['--ccdb', os.path.join(A2, 'snap1-off', 'compile_commands.json'), pm('rexlego'),
                        '--define', 'LEGO_GPU_WAIT_BACKOFF_DEFAULT_US=-1']),
    ('nat', 'nat', ['--ccdb', os.path.join(A2, 'snap1-on', 'compile_commands.json'), pm('rexlego'),
                    '--include-first', os.path.join(B, 'nat', 'gen-on')]),
    ('natoff', 'natoff', ['--ccdb', os.path.join(A2, 'snap1-on', 'compile_commands.json'), pm('rexlego'),
                          '--include-first', os.path.join(B, 'nat', 'gen-on'),
                          '--define', 'LEGO_NATIVE_SHADER_MISS_CACHE_DEFAULT=0']),
]


WANT_N = {'rt': 8, 'gpu': 1, 'xe': 1, 'xeoff': 1, 'nat': 4, 'natoff': 4}  # = 19 (final-build-rating S1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jobs', type=int, default=8)
    ap.add_argument('--dry-run', action='store_true', help='build the command lines only')
    a = ap.parse_args()
    if os.path.exists(HOLD):
        print('HOLD file exists: not starting')
        return 9
    out, fails, jobs = [], [], []

    def say(s):
        out.append(s)
        print(s, flush=True)

    top = os.path.join(B, 'fsyntax')
    os.makedirs(top, exist_ok=True)
    say('# fsyntax (M2) %s' % time.strftime('%Y-%m-%d %H:%M:%S'))
    for name, leg, args in SETS:
        d = os.path.join(top, name)
        cmd = [sys.executable, os.path.join(A2, 'recompile.py'), '--list', os.path.join(B, leg, 'list-on.tsv'),
               '--log-dir', d, '--fwd-src', '--priority', 'normal', '--dry-run'] + args
        p = subprocess.run(cmd, cwd=R, capture_output=True, text=True)
        if p.returncode != 0:
            say('FAIL %s: recompile.py --dry-run exit %d\n%s' % (name, p.returncode, (p.stdout + p.stderr)[-1500:]))
            fails.append(name)
            continue
        txt = open(os.path.join(d, 'recompile-commands.txt'), encoding='utf-8').read()
        for cwd, c in re.findall(r'^cwd: (.*)\nwas -o .*\ncmd: (.*)$', txt, re.M):
            toks = c.split(' ')
            io = toks.index('-o')
            tag = os.path.basename(toks[io + 1])
            del toks[io:io + 2]
            toks.insert(1, '-fsyntax-only')
            bad = [t for t in toks if t.startswith(BAD) or t == '-o']
            if bad:
                say('FAIL %s/%s: output flags left %s' % (name, tag, bad))
                fails.append('%s/%s' % (name, tag))
                continue
            jobs.append({'set': name, 'tag': tag, 'cwd': cwd, 'cmd': ' '.join(toks),
                         'log': os.path.join(d, tag[:-4] + '.fsyntax.log')})
        cnt = sum(1 for j in jobs if j['set'] == name)
        ok = cnt == WANT_N[name]
        say('%s %s: %d TU(s) (want %d)' % ('PASS' if ok else 'FAIL', name, cnt, WANT_N[name]))
        if not ok:
            fails.append('%s count' % name)
    with open(os.path.join(top, 'fsyntax-commands.txt'), 'w', encoding='utf-8', newline='\n') as f:
        for j in jobs:
            f.write('cwd: %s\ncmd: %s\n\n' % (j['cwd'], j['cmd']))
    if a.dry_run or fails:
        say('RESULT: %s' % ('dry run, %d command(s) in b/fsyntax/fsyntax-commands.txt' % len(jobs) if not fails
                            else 'FAIL (%s)' % ', '.join(fails)))
        return 1 if fails else 0
    t0 = time.time()
    pending, running = list(jobs), []
    while pending or running:
        if os.path.exists(HOLD):
            for j in running:
                subprocess.run('taskkill /T /F /PID %d' % j['p'].pid, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            say('HOLD file appeared: killed')
            return 30
        while pending and len(running) < min(a.jobs, 8):
            j = pending.pop(0)
            j['lf'] = open(j['log'], 'wb')
            j['p'] = subprocess.Popen(j['cmd'], cwd=j['cwd'], stdout=j['lf'], stderr=subprocess.STDOUT)
            running.append(j)
        for j in list(running):
            if j['p'].poll() is not None:
                j['lf'].close()
                running.remove(j)
        time.sleep(0.3)
    for j in jobs:
        rc = j['p'].returncode
        log = open(j['log'], encoding='utf-8', errors='replace').read()
        nw, ne = len(re.findall(r': warning:', log)), len(re.findall(r': (?:fatal )?error:', log))
        ok = rc == 0 and ne == 0
        say('%s %s/%s exit %d, %d warning(s), %d error(s)' % ('PASS' if ok else 'FAIL', j['set'], j['tag'], rc, nw,
                                                              ne))
        if not ok:
            fails.append('%s/%s' % (j['set'], j['tag']))
            say(log[-2000:])
        elif nw:
            for ln in re.findall(r'^.*: warning:.*$', log, re.M)[:5]:
                say('    ' + ln)
    say('wall %.1f s' % (time.time() - t0))
    say('RESULT: %s' % ('PASS (%d TUs)' % len(jobs) if not fails else 'FAIL (%s)' % ', '.join(fails)))
    with open(os.path.join(top, 'fsyntax.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
