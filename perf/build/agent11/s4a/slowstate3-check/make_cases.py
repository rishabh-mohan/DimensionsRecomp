# make_cases.py - builds the synthetic test tree for checking bench/agent11/timerq_slowstate_3mode.ps1
# (Agent 11 task #10 helper). Run from the workspace root:  python build/agent11/s4a/slowstate3-check/make_cases.py
# Writes ONLY under build/agent11/s4a/slowstate3-test/ (test data) and
# build/agent11/s4a/slowstate3-check/synth-expected.json (expected results).
# Each case dir gets copies of ONLY sys.csv, run.json and (if needed) game.log from a real W5 run dir
# (build/agent8/matrix/20261122-1756/runs/...), then run.json / game.log are edited. The --log_file arg is
# rewritten or removed in EVERY case so the real run's game.log is never read.
import json, os, shutil

SRC = os.path.join('build', 'agent8', 'matrix', '20261122-1756', 'runs')
TROOT = os.path.join('build', 'agent11', 's4a', 'slowstate3-test')
CHK = os.path.join('build', 'agent11', 's4a', 'slowstate3-check')
MAT = '20990101-0000'      # main synthetic matrix (cases a..j plus extras)
MAT_LONG = '20990101-0001' # separate matrix for the column-width probe
RUNS = os.path.join(TROOT, MAT, 'runs')
LOGS = os.path.join(TROOT, 'logs')  # logs reachable only via --log_file (not inside a run dir)
PRECISE = b'TimerQueue: precise wait (timer_queue_precise_wait)'
PREC, BASE, COLD = '1815-d11p-r2', '1817-base-r2', '1756-cold-base'
ENV_ON = {'REX_TIMER_WAIT_BLOCKING': '1'}
# per-run numbers of the source sys.csv files, taken from the FROZEN ORIGINAL's output (orig-since-1756.txt)
NUMS = {PREC: ('2', '70', '113', '1/0'), BASE: ('4', '78', '113', '1/0'), COLD: ('-', '0', '91', '1/0')}
WS = os.path.abspath(os.getcwd())


def guard(p):
    ap = os.path.abspath(p)
    assert ap.startswith(os.path.abspath(TROOT) + os.sep), ap
    return ap


def load_rj(src):
    with open(os.path.join(SRC, src, 'run.json'), encoding='utf-8-sig') as f:
        return json.load(f)


def log_bytes(src, edit):
    with open(os.path.join(SRC, src, 'game.log'), 'rb') as f:
        b = f.read()
    lines = b.splitlines(keepends=True)
    if edit == 'copy':
        return b
    if edit == 'strip':
        out = [ln for ln in lines if PRECISE not in ln]
        assert len(out) == len(lines) - 1, 'strip: expected exactly one precise line in ' + src
        return b''.join(out)
    if edit == 'dup':
        out = []
        for ln in lines:
            out.append(ln)
            if PRECISE in ln:
                out.append(ln)
        assert len(out) == len(lines) + 1
        return b''.join(out)
    raise ValueError(edit)


def set_pcvar(j, state):
    params = j.setdefault('params', {})
    cv = [c for c in (params.get('cvar') or []) if 'timer_queue_precise_wait' not in str(c)]
    args = [a for a in (j.get('args') or []) if 'timer_queue_precise_wait' not in str(a)]
    if state == 'true':
        cv.append('timer_queue_precise_wait=true'); args.append('--timer_queue_precise_wait=true')
    elif state == 'false':
        cv.append('timer_queue_precise_wait=false'); args.append('--timer_queue_precise_wait=false')
    elif state == 'bare':
        args.append('--timer_queue_precise_wait')
    elif state == 'split_false':
        args += ['--timer_queue_precise_wait', 'false']
    elif state is not None:
        raise ValueError(state)
    params['cvar'] = cv
    j['args'] = args


def set_logfile_arg(j, value):
    args = [a for a in (j.get('args') or []) if not str(a).lower().startswith('--log_file=')]
    if value is not None:
        args.insert(0, '--log_file=' + value)
    j['args'] = args


expected = []


def case(mat, name, src, *, desc, sys_src=None, log=None, log_where='dir', logfile_arg='own', env='keep',
         pcvar='keep', tag='keep', ff='keep', no_sys=False, expect=None):
    runs = os.path.join(TROOT, mat, 'runs')
    d = guard(os.path.join(runs, name))
    os.makedirs(d)
    if not no_sys:
        shutil.copyfile(os.path.join(SRC, sys_src or src, 'sys.csv'), os.path.join(d, 'sys.csv'))
    j = load_rj(src)
    ext_log = guard(os.path.join(LOGS, name + '.game.log'))
    if log is not None:
        dest = os.path.join(d, 'game.log') if log_where == 'dir' else ext_log
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'wb') as f:
            f.write(log_bytes(*log))
    if logfile_arg == 'own':
        set_logfile_arg(j, os.path.join(d, 'game.log'))  # d is absolute (guard); the file may or may not exist
    elif logfile_arg == 'none':
        set_logfile_arg(j, None)
    elif logfile_arg == 'ext_abs':
        set_logfile_arg(j, ext_log)
    elif logfile_arg == 'ext_rel_quoted':
        set_logfile_arg(j, '"' + os.path.relpath(ext_log, WS) + '"')
    elif logfile_arg == 'missing':
        set_logfile_arg(j, guard(os.path.join(LOGS, 'does-not-exist.game.log')))
    else:
        raise ValueError(logfile_arg)
    if env != 'keep':
        j['env_set'] = env
    if pcvar != 'keep':
        set_pcvar(j, pcvar)
    if tag is None:
        j.pop('tag', None)
    elif tag != 'keep':
        j['tag'] = tag
    if ff == 'delete':
        j.pop('ff_signal_epoch_s', None)
    elif ff != 'keep':
        j['ff_signal_epoch_s'] = ff
    with open(os.path.join(d, 'run.json'), 'w', encoding='utf-8', newline='\r\n') as f:
        json.dump(j, f, indent=2)
    e = {'matrix': mat, 'run': name, 'desc': desc, 'included': expect is not None}
    if expect is not None:
        onset, slow, span, fg = NUMS[sys_src or src]
        e.update({'onset_s': onset, 'slow_pct': slow, 'span_s': span, 'fg': fg})
        e.update(expect)
    expected.append(e)


def main():
    for m in (MAT, MAT_LONG):
        p = guard(os.path.join(TROOT, m))
        if os.path.isdir(p):
            shutil.rmtree(p)
    if os.path.isdir(guard(LOGS)):
        shutil.rmtree(guard(LOGS))
    os.makedirs(RUNS)
    os.makedirs(LOGS)
    X = lambda arm, mode, env, pcvar, precise, ms1, flags: dict(arm=arm, mode=mode, env=env, pcvar=pcvar,
                                                              precise=str(precise), ms1=str(ms1), flags=flags)
    # ---- the 10 required cases (a..j) ----
    case(MAT, '0001-a-r1', PREC, desc='(a) cvar on, game.log without precise line, env off',
         log=(PREC, 'strip'), pcvar='true', env={}, tag='a-r1',
         expect=X('a', 'spin', 'False', 'True', 0, 1, 'precise_cvar_no_line'))
    case(MAT, '0002-b-r1', PREC, desc='(b) cvar on, game.log without precise line, env on',
         log=(PREC, 'strip'), pcvar='true', env=ENV_ON, tag='b-r1',
         expect=X('b', 'blocking', 'True', 'True', 0, 1, 'precise_cvar_no_line'))
    case(MAT, '0003-c-r1', PREC, desc='(c) precise line present, no cvar, env off',
         log=(PREC, 'copy'), pcvar=None, env={}, tag='c-r1',
         expect=X('c', 'precise', 'False', 'False', 1, 1, 'precise_line_no_cvar'))
    case(MAT, '0004-d-r1', PREC, desc='(d) env on + cvar + precise line',
         log=(PREC, 'copy'), pcvar='true', env=ENV_ON, tag='d-r1',
         expect=X('d', 'precise', 'True', 'True', 1, 1, 'env+precise'))
    case(MAT, '0005-e-r1', PREC, desc='(e) two precise lines (cvar on, env off)',
         log=(PREC, 'dup'), pcvar='true', env={}, tag='e-r1',
         expect=X('e', 'precise', 'False', 'True', 2, 1, 'precise_lines>1'))
    case(MAT, '0006-f-r1', BASE, desc='(f) no game.log, no --log_file, no cvar, env on',
         log=None, logfile_arg='none', pcvar=None, env=ENV_ON, tag='f-r1',
         expect=X('f', 'blocking', 'True', 'False', 0, 0, 'no_log'))
    case(MAT, '0007-g-r1', PREC, desc='(g) no game.log, no --log_file, cvar on, env off',
         log=None, logfile_arg='none', pcvar='true', env={}, tag='g-r1',
         expect=X('g', 'unknown', 'False', 'True', 0, 0, 'no_log'))
    case(MAT, '0008-h-r1', BASE, desc='(h) ff_signal_epoch_s = 0 -> run skipped',
         log=(BASE, 'copy'), ff=0, tag='h-r1', expect=None)
    case(MAT, '0009-x-r1', BASE, desc='(i) arm x run 1: spin',
         log=(BASE, 'copy'), pcvar=None, env={}, tag='x-r1',
         expect=X('x', 'spin', 'False', 'False', 0, 0, ''))
    case(MAT, '0010-x-r2', PREC, desc='(i) arm x run 2: precise -> arm x MIXED',
         log=(PREC, 'copy'), pcvar='true', env={}, tag='x-r2',
         expect=X('x', 'precise', 'False', 'True', 1, 1, ''))
    case(MAT, '0011-j-r1', PREC, desc='(j) cvar timer_queue_precise_wait=false (args + params.cvar), no precise line',
         log=(PREC, 'strip'), pcvar='false', env={}, tag='j-r1',
         expect=X('j', 'spin', 'False', 'False', 0, 1, ''))
    # ---- extra probes ----
    case(MAT, '0012-k-r1', PREC, desc='(k) no game.log in dir; --log_file=<absolute path> to a log with the line',
         log=(PREC, 'copy'), log_where='ext', logfile_arg='ext_abs', pcvar='true', env={}, tag='k-r1',
         expect=X('k', 'precise', 'False', 'True', 1, 1, ''))
    case(MAT, '0013-l-r1', PREC, desc='(l) no game.log in dir; --log_file="<relative path, quoted>" to a log with the line',
         log=(PREC, 'copy'), log_where='ext', logfile_arg='ext_rel_quoted', pcvar='true', env={}, tag='l-r1',
         expect=X('l', 'precise', 'False', 'True', 1, 1, ''))
    case(MAT, '0014-m-r1', BASE, desc='(m) no game.log; --log_file points to a missing file; env on',
         log=None, logfile_arg='missing', pcvar=None, env=ENV_ON, tag='m-r1',
         expect=X('m', 'blocking', 'True', 'False', 0, 0, 'no_log'))
    case(MAT, '0015-n-r1', BASE, desc='(n) env_set {"REX_TIMER_WAIT_BLOCKING":"0"} (presence-only test => blocking)',
         log=(BASE, 'copy'), pcvar=None, env={'REX_TIMER_WAIT_BLOCKING': '0'}, tag='n-r1',
         expect=X('n', 'blocking', 'True', 'False', 0, 0, ''))
    case(MAT, '0016-o-r1', BASE, desc='(o) env_set as a list ["REX_TIMER_WAIT_BLOCKING=1"]',
         log=(BASE, 'copy'), pcvar=None, env=['REX_TIMER_WAIT_BLOCKING=1'], tag='o-r1',
         expect=X('o', 'blocking', 'True', 'False', 0, 0, ''))
    case(MAT, '0017-p-r1', BASE, desc='(p) args "--timer_queue_precise_wait" "false" as two tokens (regex false positive expected)',
         log=(BASE, 'copy'), pcvar='split_false', env={}, tag='p-r1',
         expect=X('p', 'spin', 'False', 'True', 0, 0, 'precise_cvar_no_line'))
    case(MAT, '0018-q-r1', PREC, desc='(q) bare flag "--timer_queue_precise_wait" (no value) + precise line',
         log=(PREC, 'copy'), pcvar='bare', env={}, tag='q-r1',
         expect=X('q', 'precise', 'False', 'True', 1, 1, ''))
    case(MAT, '0019-r-r1', COLD, desc='(r) no "tag" in run.json (arm from dir name); sys.csv without a slow state',
         log=(COLD, 'copy'), pcvar=None, env={}, tag=None,
         expect=X('r', 'spin', 'False', 'False', 0, 0, ''))
    case(MAT, '0020-s-r1', BASE, desc='(s) ff_signal_epoch_s key absent -> run skipped',
         log=(BASE, 'copy'), ff='delete', tag='s-r1', expect=None)
    case(MAT, '0021-t-r1', BASE, desc='(t) no sys.csv -> run skipped',
         log=(BASE, 'copy'), no_sys=True, tag='t-r1', expect=None)
    case(MAT, '0022-Y-r1', BASE, desc='(u) tag "Y-r1" (arm differs from u2 only by case)',
         log=(BASE, 'copy'), pcvar=None, env={}, tag='Y-r1',
         expect=X('Y', 'spin', 'False', 'False', 0, 0, ''))
    case(MAT, '0023-y-r2', BASE, desc='(u) tag "y-r2"',
         log=(BASE, 'copy'), pcvar=None, env={}, tag='y-r2',
         expect=X('y', 'spin', 'False', 'False', 0, 0, ''))
    case(MAT, '0024-w-r1', PREC, desc='(w) no game.log, no --log_file, cvar on AND env on -> unknown wins over blocking',
         log=None, logfile_arg='none', pcvar='true', env=ENV_ON, tag='w-r1',
         expect=X('w', 'unknown', 'True', 'True', 0, 0, 'no_log'))
    # ---- column-width probe (separate matrix so the main table stays parseable) ----
    os.makedirs(os.path.join(TROOT, MAT_LONG, 'runs'))
    case(MAT_LONG, '0001-long-r1', PREC, desc='(z) 140-char arm name + a flag: does the run table drop/truncate columns?',
         log=(PREC, 'strip'), pcvar='true', env={}, tag='L' * 140 + '-r1',
         expect=X('L' * 140, 'spin', 'False', 'True', 0, 1, 'precise_cvar_no_line'))
    case(MAT_LONG, '0002-n-r1', BASE, desc='(z) normal companion run',
         log=(BASE, 'copy'), pcvar=None, env={}, tag='n-r1',
         expect=X('n', 'spin', 'False', 'False', 0, 0, ''))
    with open(os.path.join(CHK, 'synth-expected.json'), 'w', encoding='utf-8') as f:
        json.dump(expected, f, indent=1)
    print('cases written:', len(expected))
    for e in expected:
        print(e['matrix'], e['run'], 'included' if e['included'] else 'SKIP', e.get('mode', ''), e.get('flags', ''))


if __name__ == '__main__':
    main()
