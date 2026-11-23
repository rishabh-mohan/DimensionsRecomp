#!/usr/bin/env python3
# test_cg26_check.py -- Agent 9, run-2 task #18: tests cg26_check.py without a regen, build or game run.
# It builds a mock CG26 regen under build/agent9/cg26-check/mock/ from the pinned A tree (only read) by doing what the
# staged build_db16cyc does with db16cyc_pause: insert '\tsimde_mm_pause();' after every '\t// db16cyc ' line of the 10 A
# TUs. It adds a mock stamp and codegen.d, the staged new-A toml and a mock bin with a MANIFEST. Then it runs the checker
# once per case, one case at a time:
#   - the PASS case;
#   - Agent 2's real pre-regen cg26 tree, with the real nativeB-bin MANIFEST (expected FAIL);
#   - one-fault mutations of the mock (content only: each keeps the file's mtime, and is restored after its case);
#   - a no --bin run (expected INCOMPLETE) and a run with a stop file present (expected HELD, exit 3).
# perf-notes/WINDOW-HOLD.txt: checked before the mock build, during it (per file), before every case and every second
# while a case runs. If it appears, the running checker is killed, the case's mutation is restored, and the test stops
# with exit 3 and keeps the mock; resume later with --reuse-mock [--only ids]. It writes only under
# build/agent9/cg26-check/.
# Run from the workspace root:
#   cmd /c start "" /belownormal /wait /b python build\agent9\cg26-check\test_cg26_check.py [--keep-mock]
#       [--reuse-mock] [--only P0,F4,...]
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.getcwd()
HERE = os.path.join(ROOT, 'build', 'agent9', 'cg26-check')
CHECK = os.path.join(HERE, 'cg26_check.py')
HOLD = os.path.join(ROOT, 'perf-notes', 'WINDOW-HOLD.txt')
PIN = os.path.join(ROOT, 'build', 'agent2', 'snap1', 'DimensionsRecomp', 'rexlego', 'generated')
CG = os.path.join(ROOT, 'build', 'agent2', 'cg26')
CG_GEN = os.path.join(CG, 'DimensionsRecomp', 'rexlego', 'generated')
CG_TOML = os.path.join(CG, 'DimensionsRecomp', 'rexlego', 'legodimensions_config.toml')
CG_MANI = os.path.join(CG, 'DimensionsRecomp', 'rexlego', 'legodimensions_manifest.toml')
NEW_TOOL = os.path.join(CG, 'tool', 'rexglue.exe')
OLD_TOOL = os.path.join(ROOT, 'build', 'agent9', 'bin', 'rexglue.exe')
NATIVEB_BIN = os.path.join(ROOT, 'build', 'agent2', 'nativeB-bin')
STAGE = os.path.join(ROOT, 'build', 'agent9', 's4', 'spin', 'db16cyc-pause')
NEW_A = os.path.join(STAGE, 'toml', 'new-A', 'rexlego', 'legodimensions_config.toml')
BASE_A = os.path.join(STAGE, 'toml', 'base-A', 'rexlego', 'legodimensions_config.toml')
MOCK = os.path.join(HERE, 'mock')
MGEN = os.path.join(MOCK, 'rexlego', 'generated')
MCD = os.path.join(MGEN, 'default')
MTOML = os.path.join(MOCK, 'rexlego', 'legodimensions_config.toml')
MBIN = os.path.join(MOCK, 'bin')
READY = os.path.join(MOCK, 'READY.json')
FAKE_HOLD = os.path.join(MOCK, 'HOLD-TEST.txt')
TUS = {107: 8, 116: 2, 321: 2, 205: 2, 169: 1, 153: 1, 432: 1, 304: 1, 284: 1, 125: 1}   # R2.17, arm A
PAUSE = b'\tsimde_mm_pause();'
SITE = b'\t// db16cyc '
HELD = 3


class Held(Exception):
    pass


def rd(p):
    with open(p, 'rb') as f:
        return f.read()


def wr(p, data):
    # Never write through an existing file: remove it first, so no write can reach another tree via a hard link.
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.lexists(p):
        os.remove(p)
    with open(p, 'wb') as f:
        f.write(data)


def sha(p):
    return hashlib.sha256(rd(p)).hexdigest().upper()


def fwd(p):
    return os.path.abspath(p).replace('\\', '/')


def tu_path(tu):
    return os.path.join(MCD, 'legodimensions_recomp.%d.cpp' % tu)


def watched():
    """The mock files a run changes or a case mutates, for READY.json."""
    ps = [tu_path(tu) for tu in sorted(TUS)] + [tu_path(108), MTOML] + [
        os.path.join(MCD, n) for n in ('codegen.partition.json', 'codegen.stamp', 'codegen.build.stamp', 'codegen.d')]
    if os.path.isdir(MBIN):
        ps += [os.path.join(MBIN, n) for n in sorted(os.listdir(MBIN))]
    return ps


def count_files(root):
    return sum(len(fns) for _dp, _dns, fns in os.walk(root))


def hold_copy(src, dst, *, follow_symlinks=True):
    if os.path.exists(HOLD):
        raise Held()
    return shutil.copy2(src, dst, follow_symlinks=follow_symlinks)


def build_mock(log):
    t0 = time.time()
    if os.path.isdir(MOCK):
        shutil.rmtree(MOCK)
    shutil.copytree(PIN, MGEN, copy_function=hold_copy)   # copy2: sizes and mtimes as in the pinned tree
    wr(MTOML, rd(NEW_A))
    now = time.time()
    os.utime(MTOML, (now - 600, now - 600))          # the toml landed 10 minutes before the mock regen
    for tu, n in sorted(TUS.items()):
        lines = rd(tu_path(tu)).split(b'\n')
        out, added = [], 0
        for ln in lines:
            out.append(ln)
            if ln.startswith(SITE):
                out.append(PAUSE + (b'\r' if ln.endswith(b'\r') else b''))
                added += 1
        if added != n:
            sys.exit('mock: TU%d has %d db16cyc lines, expected %d' % (tu, added, n))
        wr(tu_path(tu), b'\n'.join(out))
    fp = hashlib.md5(b'mock cg26 regen\n' + rd(MTOML)).hexdigest()
    st = json.loads(rd(os.path.join(MCD, 'codegen.stamp')).decode('utf-8'))
    st['fingerprint'] = fp
    wr(os.path.join(MCD, 'codegen.stamp'), (json.dumps(st, indent=2) + '\n').encode('utf-8'))
    wr(os.path.join(MCD, 'codegen.build.stamp'), (fp + '\n').encode('ascii'))
    dep = '%s: \\\n  %s \\\n  %s \\\n  %s\n' % (fwd(os.path.join(MCD, 'codegen.build.stamp')),
                                              fwd(os.path.join(ROOT, 'game', 'disc', 'Default.xex')), fwd(MTOML),
                                              fwd(CG_MANI))
    wr(os.path.join(MCD, 'codegen.d'), dep.encode('utf-8'))
    time.sleep(1.1)
    files = {'legodimensions.exe': b'MZ mock CG26 exe (Agent 9 test, not a build)\n' * 64,
             'legodimensions.map': b' mock map\n' * 64,
             'rexruntime.dll': b'MZ mock runtime\n' * 64}
    rows = []
    for name, data in files.items():
        p = os.path.join(MBIN, name)
        wr(p, data)
        rows.append('%s\t%d\t%s\t%s\t%s' % (name, len(data), time.strftime('%Y-%m-%d %H:%M:%S'), sha(p),
                                            'build\\agent9\\cg26-check\\mock (generated by the test)'))
    man = ['# mock CG26 bin (Agent 9 test_cg26_check.py): not a real build; stage-variant.py / nativeB-bin row format.',
           '# codegen tool %s (sha256 %s) with %s (sha256 %s)' % (NEW_TOOL, sha(NEW_TOOL), MTOML, sha(MTOML)),
           '# ON TUs: ' + ' '.join('%d=%s' % (tu, sha(tu_path(tu))[:16]) for tu in sorted(TUS)),
           '# name\tsize\tmtime\tsha256\tsource'] + rows + ['# checks: none (mock)']
    wr(os.path.join(MBIN, 'MANIFEST.txt'), ('\r\n'.join(man) + '\r\n').encode('ascii'))
    ready = {'files': count_files(MGEN), 'sha256': {os.path.relpath(p, MOCK): sha(p) for p in watched()}}
    wr(READY, json.dumps(ready, indent=1).encode('utf-8'))
    log('mock built in %.1f s: %s (pinned copy + 20 pause lines + mock stamps), %s, %s' % (
        time.time() - t0, os.path.relpath(MGEN, ROOT), os.path.relpath(MTOML, ROOT), os.path.relpath(MBIN, ROOT)))


def mock_ok(log):
    if not os.path.isfile(READY):
        log('mock: no READY.json, rebuilding')
        return False
    ready = json.loads(rd(READY).decode('utf-8'))
    bad = [rel for rel, h in ready['sha256'].items()
           if not os.path.isfile(os.path.join(MOCK, rel)) or sha(os.path.join(MOCK, rel)) != h]
    n = count_files(MGEN)
    if bad or n != ready['files']:
        log('mock: changed since it was built (%s; %d files, READY %d), rebuilding' % (' '.join(bad[:5]), n,
                                                                                      ready['files']))
        return False
    return True


class Mut:
    """Remember a file's bytes and times so a case can change its content (keeping the mtime) and put it back."""

    def __init__(self, path):
        self.path, self.data = path, rd(path)
        s = os.stat(path)
        self.times = (s.st_atime, s.st_mtime)

    def write(self, data):
        wr(self.path, data)
        os.utime(self.path, self.times)

    def restore(self):
        wr(self.path, self.data)
        os.utime(self.path, self.times)


def m_remove_first_pause(tu):
    def f():
        m = Mut(tu_path(tu))
        lines = m.data.split(b'\n')
        k = next(i for i, ln in enumerate(lines) if ln.rstrip(b'\r') == PAUSE)
        del lines[k]
        m.write(b'\n'.join(lines))
        return [m]
    return f


def m_extra_pause(tu, at):
    def f():
        m = Mut(tu_path(tu))
        lines = m.data.split(b'\n')
        lines.insert(at, PAUSE + (b'\r' if lines[at - 1].endswith(b'\r') else b''))
        m.write(b'\n'.join(lines))
        return [m]
    return f


def m_move_pause_down(tu):
    def f():
        m = Mut(tu_path(tu))
        lines = m.data.split(b'\n')
        k = next(i for i, ln in enumerate(lines) if ln.rstrip(b'\r') == PAUSE)
        if lines[k + 1].startswith(SITE):
            sys.exit('m_move_pause_down: TU%d line after the pause is a db16cyc line' % tu)
        lines[k], lines[k + 1] = lines[k + 1], lines[k]
        m.write(b'\n'.join(lines))
        return [m]
    return f


def m_append(path, extra):
    def f():
        m = Mut(path)
        m.write(m.data + extra)
        return [m]
    return f


def m_flip_byte(path, at):
    def f():
        m = Mut(path)
        b = bytearray(m.data)
        b[at] ^= 0x01
        m.write(bytes(b))
        return [m]
    return f


def m_edit_line(tu, at):
    def f():
        m = Mut(tu_path(tu))
        lines = m.data.split(b'\n')
        cr = lines[at].endswith(b'\r')
        lines[at] = lines[at].rstrip(b'\r') + b' // edited' + (b'\r' if cr else b'')
        m.write(b'\n'.join(lines))
        return [m]
    return f


def m_stamp_older_than_toml():
    def f():
        p = os.path.join(MCD, 'codegen.stamp')
        m = Mut(p)
        t = os.path.getmtime(MTOML) - 3600
        os.utime(p, (t, t))
        return [m]
    return f


def m_build_stamp(text):
    def f():
        m = Mut(os.path.join(MCD, 'codegen.build.stamp'))
        m.write(text)
        return [m]
    return f


class FakeHold:
    """A stop file inside the mock (never the real perf-notes/WINDOW-HOLD.txt), removed after its case."""

    def __call__(self):
        wr(FAKE_HOLD, b'test stop file (Agent 9 test_cg26_check.py)\n')
        return [self]

    def restore(self):
        if os.path.exists(FAKE_HOLD):
            os.remove(FAKE_HOLD)


def args_mock(**kw):
    a = {'--arm': 'A', '--gen': MGEN, '--ref': PIN, '--config': MTOML, '--tool': NEW_TOOL, '--bin': MBIN}
    a.update(kw)
    return a


CASES = [
    # id, title, expected exit code, expected failing gates, checker args, mutation
    ('P0', 'mock CG26 regen + mock bin: expected PASS', 0, '', args_mock(), None),
    ('F1', "Agent 2's real cg26 tree before the regen (pinned copy, ON toml, new tool) + the real nativeB-bin MANIFEST",
     1, 'ab', {'--arm': 'A', '--gen': CG_GEN, '--ref': PIN, '--config': CG_TOML, '--tool': NEW_TOOL,
               '--bin': NATIVEB_BIN}, None),
    ('F2', 'one pause line missing (TU116, first site): 19 pauses', 1, 'ab', args_mock(), m_remove_first_pause(116)),
    ('F3', 'an extra pause line in TU108, not an arm TU', 1, 'abc', args_mock(), m_extra_pause(108, 200)),
    ('F4', 'the TU125 pause moved one line down (no longer right after its db16cyc line)', 1, 'b', args_mock(),
     m_move_pause_down(125)),
    ('F5', 'codegen.partition.json changed (one byte appended)', 1, 'c', args_mock(),
     m_append(os.path.join(MCD, 'codegen.partition.json'), b' ')),
    ('F6', 'staged exe changed after staging (one byte flipped): MANIFEST hash mismatch', 1, 'd', args_mock(),
     m_flip_byte(os.path.join(MBIN, 'legodimensions.exe'), 100)),
    ('F7', 'old codegen tool (build/agent9/bin/rexglue.exe, no db16cyc_pause option)', 1, 'a',
     args_mock(**{'--tool': OLD_TOOL}), None),
    ('F8', 'config toml without the line (staged base-A)', 1, 'a', args_mock(**{'--config': BASE_A}), None),
    ('F9', 'codegen.stamp older than the toml (the line landed after the regen)', 1, 'a', args_mock(),
     m_stamp_older_than_toml()),
    ('F10', 'a non-pause edit in TU205 (line 20)', 1, 'b', args_mock(), m_edit_line(205, 19)),
    ('F11', 'codegen.build.stamp from another regen', 1, 'a', args_mock(),
     m_build_stamp(b'0123456789abcdef0123456789abcdef\n')),
    ('I1', 'no --bin: expected INCOMPLETE (exit 2)', 2, '', {k: v for k, v in args_mock().items() if k != '--bin'},
     None),
    ('H1', 'a stop file present (--hold points at a test file in the mock): expected HELD (exit 3), no report', 3, '',
     args_mock(**{'--hold': FAKE_HOLD}), FakeHold()),
]


def failing_gates(report):
    gates, cur = set(), None
    for ln in report.splitlines():
        if ln.startswith('== ('):
            cur = ln[4]
        elif ln.startswith('FAIL ') and cur:
            gates.add(cur)
    return ''.join(sorted(gates))


def run_case(cmd, stdout_path):
    """Run one checker; poll the real stop file every second and kill the checker if it appears."""
    with open(stdout_path, 'w', encoding='utf-8', errors='replace') as so:
        p = subprocess.Popen(cmd, stdout=so, stderr=subprocess.STDOUT, cwd=ROOT)
        while True:
            try:
                return p.wait(timeout=1.0), False
            except subprocess.TimeoutExpired:
                if os.path.exists(HOLD):
                    p.kill()
                    p.wait()
                    return None, True


def main():
    ap = argparse.ArgumentParser(description='tests for cg26_check.py (Agent 9, task #18)')
    ap.add_argument('--keep-mock', action='store_true', help='keep build/agent9/cg26-check/mock at the end')
    ap.add_argument('--reuse-mock', action='store_true', help='reuse the mock if READY.json still matches it')
    ap.add_argument('--only', default='', help='comma-separated case ids (default: all)')
    a = ap.parse_args()
    only = {x.strip() for x in a.only.split(',') if x.strip()}
    tag = time.strftime('%Y%m%d-%H%M%S')
    outdir = os.path.join(HERE, 'test-' + tag)
    os.makedirs(outdir)
    logp = os.path.join(HERE, 'test-%s.txt' % tag)
    lines = []

    def log(s):
        lines.append(s)
        print(s, flush=True)
        with open(logp, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(lines) + '\n')

    log('# test_cg26_check.py (Agent 9, task #18)  %s  checker sha256 %s  test sha256 %s' % (
        time.strftime('%Y-%m-%d %H:%M:%S'), sha(CHECK), sha(os.path.abspath(__file__))))
    for name, p in (('new tool', NEW_TOOL), ('old tool', OLD_TOOL)):
        b = rd(p)
        log('# %s %s sha256 %s: db16cyc_pause %s, \\tsimde_mm_pause(); %s' % (
            name, os.path.relpath(p, ROOT), hashlib.sha256(b).hexdigest().upper()[:16],
            'yes' if b'db16cyc_pause' in b else 'no', 'yes' if b'\tsimde_mm_pause();' in b else 'no'))
    if os.path.exists(HOLD):
        log('HOLD present before the mock build: stop')
        return HELD
    try:
        if a.reuse_mock and os.path.isdir(MOCK) and mock_ok(log):
            log('mock reused (READY.json matches)')
        else:
            build_mock(log)
    except Held:
        log('HOLD appeared during the mock build: stop (partial mock left; the next run rebuilds it)')
        return HELD
    ok_all, ran = True, 0
    for cid, title, want_code, want_gates, args, mut in CASES:
        if only and cid not in only:
            continue
        if os.path.exists(HOLD):
            log('HOLD present before %s: stop (mock kept; resume with --reuse-mock --only ...)' % cid)
            return HELD
        cdir = os.path.join(outdir, cid)
        os.makedirs(cdir, exist_ok=True)
        muts = mut() if mut else []
        try:
            cmd = [sys.executable, CHECK, '--out', cdir]
            for k, v in args.items():
                cmd += [k, v]
            t0 = time.time()
            code, held = run_case(cmd, os.path.join(cdir, 'stdout.txt'))
            dt = time.time() - t0
        finally:
            for m in muts:
                m.restore()
        if held or (code == HELD and want_code != HELD and os.path.exists(HOLD)):
            log('')
            log('HOLD appeared during %s: checker killed, mutation restored; stop (mock kept; resume with '
                '--reuse-mock --only ...)' % cid)
            return HELD
        ran += 1
        rpt = os.path.join(cdir, 'report.txt')
        report = open(rpt if os.path.isfile(rpt) else os.path.join(cdir, 'stdout.txt'), encoding='ascii',
                      errors='replace').read()
        gates = failing_gates(report)
        ok = code == want_code and gates == want_gates
        if want_code == HELD:
            ok = ok and not os.path.isfile(rpt)
        ok_all = ok_all and ok
        res = [ln for ln in report.splitlines() if ln.startswith('RESULT:') or ln.startswith('HOLD')]
        log('')
        log('%s %s: %s' % ('OK  ' if ok else 'BAD ', cid, title))
        log('     exit %d (want %d), failing gates "%s" (want "%s"), %.1f s; %s' % (
            code, want_code, gates, want_gates, dt, res[0] if res else 'no RESULT line'))
        for ln in [x for x in report.splitlines() if x.startswith('FAIL ')][:8]:
            log('     ' + ln[:230])
        if code not in (0, 1, 2, 3) or 'Traceback' in report:
            log('     output: ' + report.strip()[-600:])
    log('')
    log('TESTS: %s (%d of %d cases run)  -> %s' % ('ALL OK' if ok_all else 'SOME BAD', ran, len(CASES),
                                                   os.path.relpath(outdir, ROOT)))
    if not a.keep_mock:
        shutil.rmtree(MOCK)
        log('mock removed (use --keep-mock to keep it)')
    return 0 if ok_all else 1


if __name__ == '__main__':
    sys.exit(main())
