#!/usr/bin/env python3
# build-bin.py (M2 successor, session 3, 11-25 night): build ONE rexgpu-xenos.dll variant from a prep-s33.py overlay
# (build/agent2/s33/<tag>/) and stage it as build/agent2/<bin> = devoff4b-bin with only rexgpu-xenos.dll replaced.
#
#   python build/agent2/session3/build-bin.py --tag devoff4bv --bin devoff4bv-bin --title "..." [--ctl]
#          [--want NEEDLE ...] [--absent NEEDLE ...] [--jobs 12] [--no-stage]
#   CTR mode (objects already compiled): --ctr (uses build/agent2/ctr/obj-ctl|obj-on, no recompile)
#
# Steps: [CTL recompile + relink --compare devoff4b DLL] -> ON recompile (overlay source, --include-first overlay
# include if it exists) -> ON relink -> needle checks (ON has --want and not --absent; devoff4b DLL has none of
# --want) -> stage-variant.py (atomic: .tmp dir + rename) -> verify-bins.py on the new bin + devoff4b, cg26, native4b
# -> shared DLL snap1-sdk/install/bin/rexgpu-xenos.dll still E3CB99CF. Nothing outside build/agent2 is written;
# the relink writes only into its --out-dir. Log: build/agent2/s33/<tag>/build-bin.txt (ctr: build/agent2/ctr/).
import argparse, hashlib, os, re, subprocess, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
A2 = os.path.join(R, 'build', 'agent2')
SDKB = os.path.join(A2, 'snap1-sdk')
CCDB = os.path.join(SDKB, 'compile_commands.json')
NINJA = os.path.join(SDKB, 'build-Release.ninja')
TARGET = os.path.join(A2, 'snap1', 'DimensionsRecomp', 'rexglue-sdk', 'out', 'win-amd64', 'Release',
                      'rexgpu-xenos.dll')
BASE = os.path.join(A2, 'devoff4b-bin')
SHARED = os.path.join(SDKB, 'install', 'bin', 'rexgpu-xenos.dll')
SHARED_SHA = 'E3CB99CFDEA95E66EF093BF1B2A500076757FB727E60B046D70EBA01E05C9939'
SHARED_BINS = ['devoff4b-bin', 'devoff4b-cg26-bin', 'native4b-bin']
PY = sys.executable


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag')
    ap.add_argument('--bin', required=True)
    ap.add_argument('--title', required=True)
    ap.add_argument('--note', action='append', default=[])
    ap.add_argument('--ctl', action='store_true', help='also recompile + relink the control (proves the method)')
    ap.add_argument('--ctr', action='store_true')
    ap.add_argument('--want', action='append', default=[])
    ap.add_argument('--absent', action='append', default=[])
    ap.add_argument('--have', action='append', default=[], help='needle must be in ON DLL (may already be in devoff4b)')
    ap.add_argument('--jobs', type=int, default=8)  # recompile.py caps at 8
    ap.add_argument('--no-stage', action='store_true')
    ap.add_argument('--dry-run', action='store_true', help='recompile/relink --dry-run only; no compile, link, stage')
    a = ap.parse_args()
    top = os.path.join(A2, 'ctr') if a.ctr else os.path.join(A2, 's33', a.tag)
    out, notes, fails = [], [], []
    t_all = time.time()

    def say(s):
        out.append(s)
        print(s, flush=True)

    def check(what, ok, detail=''):
        say('%s %s%s' % ('PASS' if ok else 'FAIL', what, (': ' + detail) if detail else ''))
        if not ok:
            fails.append(what)
        return ok

    def run(name, cmd):
        if a.dry_run and name != 'stage':
            cmd = cmd + ['--dry-run']
        t0 = time.time()
        say('$ ' + ' '.join(cmd))
        p = subprocess.run(cmd, cwd=R, capture_output=True, text=True)
        txt = (p.stdout + p.stderr).rstrip()
        dt = time.time() - t0
        for ln in txt.splitlines():
            say('    ' + ln)
        say('%s: exit %d, %.1f s' % (name, p.returncode, dt))
        return p.returncode, txt, dt

    def finish():
        say('RESULT: %s (total %.1f s)' % ('PASS' if not fails else 'FAIL (%s)' % '; '.join(fails),
                                          time.time() - t_all))
        with open(os.path.join(top, 'build-bin.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out) + '\n')
        return 1 if fails else 0

    say('# build-bin %s  %s -> build/agent2/%s' % (time.strftime('%Y-%m-%d %H:%M:%S'), os.path.relpath(top, R), a.bin))
    notes.append('tools (sha256/16): ' + ', '.join('%s %s' % (os.path.basename(p), sha(p)[:16]) for p in (
        os.path.abspath(__file__), os.path.join(A2, 'recompile.py'), os.path.join(A2, 'relink.py'),
        os.path.join(A2, 'stage-variant.py'), os.path.join(A2, 'session3', 'verify-bins.py'),
        os.path.join(A2, 'session3', 'prep-s33.py'))))
    say(notes[-1])
    if os.path.exists(os.path.join(R, 'perf-notes', 'WINDOW-HOLD.txt')):
        say('HOLD file exists: not starting')
        fails.append('HOLD')
        return finish()
    check('shared DLL before (%s)' % os.path.relpath(SHARED, R), sha(SHARED) == SHARED_SHA)
    if os.path.exists(os.path.join(A2, a.bin)):
        check('bin dir is new', False, a.bin)
    if fails:
        return finish()
    rc_link = ['--ninja', NINJA, '--target', TARGET, '--priority', 'normal']
    rc_comp = ['--ccdb', CCDB, '--obj-filter', '/Release/', '--jobs', str(a.jobs), '--priority', 'normal', '--fwd-src']
    times = {}
    if a.ctr:
        ctl_rep = ['--replace', 'src/graphics/CMakeFiles/rexgpu-xenos.dir/Release/d3d12/deferred_command_list.cpp.obj='
                   + os.path.join(top, 'obj-ctl', 'deferred_command_list.cpp.obj')]
        on_rep = ['--replace', 'src/graphics/CMakeFiles/rexgpu-xenos.dir/Release/d3d12/deferred_command_list.cpp.obj='
                  + os.path.join(top, 'obj-on', 'deferred_command_list.cpp.obj')]
        for k in ('obj-ctl', 'obj-on'):
            p = os.path.join(top, k, 'deferred_command_list.cpp.obj')
            notes.append('CTR object %s/deferred_command_list.cpp.obj %s (compiled 11-25 01:36 by the predecessor; '
                         'ON with -DREX_D3D12_DEFERRED_COUNTERS=1, snap1 source)' % (k, sha(p)[:16]))
        a.ctl = True
    else:
        ctl_rep = ['--replace-file', os.path.join(top, 'replace-ctl.txt')]
        on_rep = ['--replace-file', os.path.join(top, 'replace-on.txt')]
        for ln in open(os.path.join(top, 'prep.txt'), encoding='utf-8'):
            m = re.match(r'^(PASS patch sha256 \S+: \S+|before .*|after .*)$', ln.rstrip())
            if m:
                notes.append('prep: ' + m.group(1))
    if a.ctl:
        if not a.ctr:
            rc, _, times['ctl compile'] = run('CTL recompile', [PY, os.path.join(A2, 'recompile.py')] + rc_comp + [
                '--list', os.path.join(top, 'list-ctl.tsv'), '--log-dir', os.path.join(top, 'log-ctl')])
            if not check('CTL recompile', rc == 0):
                return finish()
        rc, txt, times['ctl link'] = run('CTL relink', [PY, os.path.join(A2, 'relink.py')] + rc_link + ctl_rep + [
            '--out-dir', os.path.join(top, 'link-ctl'), '--compare', os.path.join(BASE, 'rexgpu-xenos.dll')])
        m = re.search(r'^(PASS|DIFF) compare .*$', txt, re.M)
        if a.dry_run:
            m = re.match('.*', 'dry run')
        if not check('CTL relink == devoff4b-bin rexgpu-xenos.dll except timestamps', rc == 0,
                     m.group(0).strip() if m else 'no compare line'):
            return finish()
        notes.append('control: ' + m.group(0).strip())
    if not a.ctr:
        inc = os.path.join(top, 'sdk', 'include')
        cmd = [PY, os.path.join(A2, 'recompile.py')] + rc_comp + ['--list', os.path.join(top, 'list-on.tsv'),
                                                                  '--log-dir', os.path.join(top, 'log-on')]
        if os.path.isdir(inc):
            cmd += ['--include-first', inc]
        # __FILE__ of overlay sources/headers -> the snap1 path, so .rdata strings match the control build
        ovf = os.path.join(top, 'sdk').replace('\\', '/')
        snf = os.path.join(A2, 'snap1', 'DimensionsRecomp', 'rexglue-sdk').replace('\\', '/')
        cmd += ['--flag=-fmacro-prefix-map=%s=%s' % (ovf, snf)]
        rc, txt, times['on compile'] = run('ON recompile', cmd)
        if not check('ON recompile', rc == 0):
            return finish()
        for ln in txt.splitlines():
            if ln.startswith('PASS ') and ' obj ' in ln:
                notes.append('ON object ' + ln[5:].strip())
    rc, txt, times['on link'] = run('ON relink', [PY, os.path.join(A2, 'relink.py')] + rc_link + on_rep + [
        '--out-dir', os.path.join(top, 'link-on')])
    dll = os.path.join(top, 'link-on', 'rexgpu-xenos.dll')
    if a.dry_run:
        check('ON relink dry run', rc == 0)
        say('dry run: stopping before needles/stage')
        return finish()
    if not check('ON relink', rc == 0 and os.path.isfile(dll)):
        return finish()
    dsha = sha(dll)
    check('ON DLL differs from the shared E3CB99CF', dsha != SHARED_SHA, dsha)
    data, based = open(dll, 'rb').read(), open(os.path.join(BASE, 'rexgpu-xenos.dll'), 'rb').read()
    for n in a.want:
        check('needle in ON DLL: %s' % n, n.encode() in data)
        check('needle NOT in devoff4b-bin DLL: %s' % n, n.encode() not in based)
    for n in a.absent:
        check('needle NOT in ON DLL: %s' % n, n.encode() not in data)
    for n in a.have:
        check('needle in ON DLL: %s' % n, n.encode() in data)
        say('  (devoff4b-bin DLL %s it)' % ('also has' if n.encode() in based else 'lacks'))
    if a.want or a.absent:
        notes.append('needles: ON has %s; ON lacks %s; devoff4b-bin DLL lacks %s' % (
            a.want or '-', a.absent or '-', a.want or '-'))
    if a.have:
        notes.append('needles: ON also has %s (%s)' % (a.have, ', '.join(
            '%s %s in devoff4b-bin DLL' % (n, 'also' if n.encode() in based else 'not') for n in a.have)))
    notes.append('times: ' + ', '.join('%s %.1f s' % kv for kv in times.items()))
    if fails or a.no_stage:
        return finish()
    rc, txt, _ = run('stage', [PY, os.path.join(A2, 'stage-variant.py'), '--base', BASE, '--out',
                               os.path.join(A2, a.bin), '--replace', 'rexgpu-xenos.dll=' + dll, '--title',
                               a.title + ' [M2 successor, build/agent2/session3/build-bin.py]'] +
                     sum([['--note', n] for n in a.note + notes], []))
    if not check('stage %s' % a.bin, rc == 0):
        return finish()
    rc, txt, _ = run('verify', [PY, os.path.join(A2, 'session3', 'verify-bins.py'), os.path.join(A2, a.bin)] +
                     [os.path.join(A2, b) for b in SHARED_BINS])
    check('verify-bins new + shared bins 0 FAIL', rc == 0)
    check('shared DLL after (%s)' % os.path.relpath(SHARED, R), sha(SHARED) == SHARED_SHA)
    nb = os.path.join(A2, a.bin)
    for fn in ('legodimensions.exe', 'rexruntime.dll', 'rexgpu-xenos.dll'):
        say('  %s/%s %s' % (a.bin, fn, sha(os.path.join(nb, fn))))
    check('exe == devoff4b-bin', sha(os.path.join(nb, 'legodimensions.exe')) ==
          sha(os.path.join(BASE, 'legodimensions.exe')))
    check('rexruntime == devoff4b-bin', sha(os.path.join(nb, 'rexruntime.dll')) ==
          sha(os.path.join(BASE, 'rexruntime.dll')))
    check('no cache/ in the bin', not os.path.exists(os.path.join(nb, 'cache')))
    return finish()


if __name__ == '__main__':
    sys.exit(main())
