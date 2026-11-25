"""final_gate.py (M12, session 3): F1-F7 gates for M2's FINAL bins, per M10 final-defaults-rating.md (C20B6FDB)
"Functional set before a confirmation window (F)". Read-only on run dirs; writes only a joined log copy under
build/agent12/session3/final/tmp (check-defaults reads one file; rotated logs are joined oldest first).

Usage:
  python -B final_gate.py <run dir> <row> [--ref <native4b n0 run dir>] [--first <run dir>] [--pair <F1 run dir>]
  row = F1 F2 F3 F4 F5 F5w F6 F7   (F5w = F5's second launch, own run dir reusing F5's cache/; needs --first = F5 run)
  bins: F1 F2 F4 devfinal-bin; F3 devfinal-off-bin; F5 F5w F7 nativefinal-bin; F6 nativefinal-off-bin (Overseer 13:44Z)
  python -B final_gate.py --selftest
Exit 0 = PASS, 1 = FAIL, 2 = usage / unreadable. NOTE lines don't change the verdict; HOLD lines (exit 4) stop the
chain until the Overseer rules (M10 final-gate-rating AE8EB2A5 G4). Each run dir must hold exactly one launch (G1);
row_gate.py alone is never a gate on a FINAL bin (G2).
v2 (M10 S1-S3, N1, N5, N6): automatic miss-cache HOLD/FAIL for F5w/F6/F7, F2 xenos HOLD, OFF bins for F3/F6,
elapsed recorded, tmp name = parent_dir__run_dir__pathsha8, F5w loaded vs saved NOTE.
v3 (Overseer 13:55Z): F2/F7 route = a known level route (script_sha256); wait_log timeouts only on that route's by-design
lines (count = listed lines), steps n/n and stopped_by_script; any other timeout FAILs.
"""
import datetime, glob, hashlib, json, os, re, subprocess, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
A2 = os.path.join(REPO, 'build', 'agent2')
CHECK_DEFAULTS = os.path.join(A2, 'final', 'check-defaults.py')
CHECK_DEFAULTS_SHA16 = 'D9936C56C5E04B98'  # rated in final-build-rating.md (94CC9FA7)
BIN_PINS = os.path.join(A2, 'final', 'BIN-PINS.md')
NAT_BUILD_TXT = os.path.join(A2, 'final', 'b', 'nat', 'gen-on', 'native-gpu-build.txt')
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'final', 'tmp')
NEW_FP, OLD_FP = b'1616ce65e973c583', b'9b40acbbef4c57b3'
OFF_SET = {  # DEFAULTS-TABLE.md L92 (old values) = the D7 OFF/ref arm cvars
    'shared_memory_single_hold_rearm': 'false', 'physical_protect_hold_global_lock': 'false',
    'physical_protect_keep_watch': 'false', 'host_timer_resolution_ms': '0', 'host_timer_throttling_optout': 'false',
    'precise_guest_sleep': 'false', 'wait_timeout_round_up': 'false', 'cs_spin': 'false',
    'spinlock_pause_spin': 'false', 'clock_lockfree': 'false', 'tls_bounds_fix': 'false',
    'timer_queue_precise_wait': 'false'}
ROW_BIN = {'F1': 'devfinal-bin', 'F2': 'devfinal-bin', 'F3': 'devfinal-off-bin', 'F4': 'devfinal-bin',
           'F5': 'nativefinal-bin', 'F5w': 'nativefinal-bin', 'F6': 'nativefinal-off-bin', 'F7': 'nativefinal-bin'}
ROW_MODE = {'F1': 'xenos', 'F2': 'xenos', 'F3': 'off', 'F4': 'xenos',
            'F5': 'native-old', 'F5w': 'native-old', 'F6': 'native-old', 'F7': 'native-old'}
BAD = ['Recovered stale physical page protection', 'Unhandled guest physical write fault', 'PhysicalHeap::Protect failed',
       'BaseHeap::Protect failed', 'is not a plain number', 'C1 verify: on', 'STUCK-LOCK', 'REX_FATAL',
       'Minidump written to', 'still not acquired after']
MISS_KEYS = ['shader not present in AOT cache', 'missing from AOT index', 'unrecognized vertex shader resource',
             'unrecognized pixel shader resource']
L_C1 = 'C1 keep-watch: on (with physical_protect_hold_global_lock)'
L_MC_ON = 'Native GPU: shader miss cache ON (build default)'
L_MC_OFF = 'Native GPU: shader miss cache OFF (LEGO_NATIVE_SHADER_MISS_CACHE set)'
L_MC_OFF_BUILD = 'Native GPU: shader miss cache OFF (build default)'  # nativefinal-off, env unset
L_MC_ANY = 'Native GPU: shader miss cache '
MC_ABSENT = 'miss cache ON (build default) line: 0 (want 1)'  # check-defaults native-old FAIL text, line absent
L_EXIT = 'Title terminated'
# Level routes F2/F7 may use (script_sha256 -> by-design wait_log timeout lines in THAT file). level-l lines 55 (amber
# fade, 60 s) and 58-116 even (press-A-until-orange, 5 s each) time out by design; how many do varies by run (27-31 over
# 20 level-l runs, 22-25 Nov). level-l-tail = level-l lines 13-130 at line - 7 (+ sleep 180 / mark tail), so the same
# waits sit 7 lines earlier. Any timeout outside the set (e.g. line 22, the tags wait; 117, the 240 s orange wait) FAILs.
_LL = [55] + list(range(58, 117, 2))
ROUTE_TIMEOUTS = {
    '6F9E600963440B451B591899A17DAD9A5941A8930AA502B597155CBB636F9A63': ('level-l.txt', set(_LL)),
    'BE08A7908005B3B6113BE199274C1D0E9F4D76B7C2116FA1B860B27F00184ABC': ('level-l-tail.txt', {n - 7 for n in _LL}),
}
ROUTE_FILES = {'level-l.txt': os.path.join(REPO, 'build', 'agent3', 'toypad', 'routes', 'level-l.txt'),
               'level-l-tail.txt': os.path.join(REPO, 'build', 'agent3', 'final-fx', 'level-l-tail.txt')}


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest().upper()


def contains(path, needle):
    tail = b''
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 22), b''):
            if needle in tail + chunk:
                return True
            tail = chunk[-len(needle):]
    return False


def msg(line):  # "[ts] [lvl] [mod] [tid] message" -> message (as check-defaults.py)
    m = re.match(r'^\[[^\]]*\] \[[^\]]*\] \[[^\]]*\] \[[^\]]*\] (.*)$', line)
    return m.group(1) if m else line


def log_files(run):
    """game.N.log (highest N = oldest) ... game.1.log, then game.log (current)."""
    rot = []
    for p in glob.glob(os.path.join(run, 'game.*.log')):
        m = re.match(r'game\.(\d+)\.log$', os.path.basename(p))
        if m:
            rot.append((int(m.group(1)), p))
    out = [p for _, p in sorted(rot, reverse=True)]
    if os.path.exists(os.path.join(run, 'game.log')):
        out.append(os.path.join(run, 'game.log'))
    return out


def read_lines(run):
    lines = []
    for p in log_files(run):
        with open(p, encoding='utf-8', errors='replace') as f:
            lines += [l.rstrip('\r\n') for l in f]
    return lines


def parse_pins(text):
    """BIN-PINS.md -> {bin dir: {'manifest': sha64, 'files': {name: sha16 or None}}}"""
    ids, pins = {}, {}
    for m in re.finditer(r'^\| (\S+) \| (\S+-bin) \| ([0-9A-F]{64}) \|', text, re.M):
        ids[m.group(1)] = m.group(2)
        pins[m.group(2)] = {'manifest': m.group(3), 'files': {}}
    sec = text.split('## File hashes', 1)[1].split('\n## ', 1)[0]
    head = None
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if cells and cells[0] == 'file':
            head = [ids[c] for c in cells[1:]]
        elif head and len(cells) == len(head) + 1 and '.' in cells[0]:
            for b, c in zip(head, cells[1:]):
                pins[b]['files'][cells[0]] = None if c == '-' else c.split()[0].upper()
    return pins


def run_switches(rj):
    """(cvars dict, env dict, kind) for a harness run.json (cvars/env) or a run-matrix run.json (params.cvar/env_set)."""
    if 'env_set' in rj or 'params' in rj:
        cv = {}
        for kv in (rj.get('params') or {}).get('cvar') or []:
            k, _, v = kv.partition('=')
            cv[k] = v
        for k, v in (rj.get('toml_set') or {}).items():
            cv.setdefault(k, str(v))
        return cv, dict(rj.get('env_set') or {}), 'matrix'
    return ({k: str(v) for k, v in (rj.get('cvars') or {}).items()}, dict(rj.get('env') or {}), 'harness')


def miss_counts(lines):
    return {k: sum(1 for l in lines if k in l) for k in MISS_KEYS}


def cd_fails(out):
    return [l.strip()[5:] for l in out.splitlines() if l.strip().startswith('FAIL ')]


def tmp_name(run):
    """N5: '<parent dir>__<run dir>__<sha8 of the full path>.joined.log'. The parent of a run-matrix run dir is
    always 'runs', so parent__run alone can still collide across matrices; the path hash makes it unique."""
    p = os.path.normcase(os.path.abspath(run.rstrip('\\/')))
    h8 = hashlib.sha256(p.encode('utf-8')).hexdigest()[:8].upper()
    return f'{os.path.basename(os.path.dirname(p))}__{os.path.basename(p)}__{h8}.joined.log'


def elapsed(rj):
    """N1: harness run.json elapsed_s; run-matrix end - start (process lifetime); (None, 'absent') otherwise."""
    if rj.get('elapsed_s') is not None:
        try:
            return float(rj['elapsed_s']), 'elapsed_s'
        except (TypeError, ValueError):
            pass
    try:
        f = lambda s: datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f')
        return round((f(rj['end']) - f(rj['start'])).total_seconds(), 2), 'end-start'
    except (KeyError, TypeError, ValueError):
        return None, 'absent'


def route_timeouts(isr):
    """F2/F7 (Overseer 13:55Z): the route must be a known level route (script_sha256) and every wait_log timeout must be
    one of that route's by-design lines; the count must match the listed lines. Returns [(level, text)]."""
    out = []
    rs = str(isr.get('script_sha256') or '').upper()
    known = ROUTE_TIMEOUTS.get(rs)
    out.append(('PASS' if known else 'FAIL', f'route script_sha256 {rs[:8] or None} = ' + (known[0] if known else 'unknown route')))
    raw = isr.get('timeout_lines')
    tl = [int(x) for x in (raw.split() if isinstance(raw, str) else (raw or []))]
    n = isr.get('timeouts') or 0
    out.append(('PASS' if n == len(tl) else 'FAIL', f'timeouts {n} = timeout_lines count {len(tl)}'))
    if known:
        extra = sorted(set(tl) - known[1])
        out.append(('PASS' if not extra else 'FAIL',
                    f'timeouts on by-design wait lines only: {len(tl)} of {len(known[1])} by-design' +
                    (f'; NOT by design: {extra}' if extra else '')))
        if not extra and len(tl) != len(known[1]):
            out.append(('NOTE', f'{len(known[1]) - len(tl)} by-design waits did not time out '
                                f'(lines {sorted(known[1] - set(tl))}); normal on level-l (27-31 seen)'))
    return out


def gate(run, row, ref=None, first=None, pair=None, _selftest_nobin=False):
    """_selftest_nobin: selftest fixtures only (not reachable from the CLI) - skips the run-dir file hash /
    exe fingerprint checks, which need real staged binaries; recorded as NOTE 'skipped (selftest)'."""
    res = []  # (level, text) level in PASS FAIL NOTE HOLD

    def P(ok, text, soft=None):
        res.append(('PASS' if ok else (soft or 'FAIL'), text))

    if not os.path.isabs(run):
        run = os.path.join(REPO, run)
    rj = json.load(open(os.path.join(run, 'run.json'), encoding='utf-8-sig'))
    cv, env, kind = run_switches(rj)
    lines = read_lines(run)
    msgs = [msg(l) for l in lines]
    res.append(('NOTE', f'run {run} ({kind}); logs {[os.path.basename(p) for p in log_files(run)]}, {len(lines)} lines'))
    el, el_src = elapsed(rj)
    res.append(('NOTE', f'elapsed {el} s ({el_src})'))  # N1
    res.append(('NOTE', f'cvars {cv}; env (LEGO_*) { {k: v for k, v in env.items() if k.startswith("LEGO_") and "METRICS" not in k} }'))

    # --- validity (F1 'valid run', F2/F7 'clean')
    P(rj.get('exit_code') == 0, f'exit_code {rj.get("exit_code")} ({rj.get("exit_code_hex")})')
    P(not rj.get('exited_early'), f'exited_early {rj.get("exited_early")}')
    P(not (rj.get('wer_seen') or rj.get('werfault_seen')), f'WER {rj.get("wer_seen", rj.get("werfault_seen"))}')
    P(not rj.get('dialogs'), f'dialogs {rj.get("dialogs")}')
    P(not rj.get('crash_events'), f'crash_events {rj.get("crash_events")}')
    dmps = glob.glob(os.path.join(run, '**', '*.dmp'), recursive=True)
    P(not dmps and not rj.get('dumps'), f'dumps {len(dmps)} in dir, run.json {rj.get("dumps")}')
    close = rj.get('close_method') or ('wm_close' if (rj.get('close') or {}).get('wm_close_posted') and not (rj.get('close') or {}).get('killed') else (rj.get('close') or {}))
    P(close == 'wm_close', f'close {close}')
    P(sum(1 for m in msgs if m.startswith(L_EXIT)) == 1, f'"{L_EXIT}" x{sum(1 for m in msgs if m.startswith(L_EXIT))} (clean exit)')
    for b in BAD:
        c = sum(1 for l in lines if b in l)
        P(c == 0, f'bad string "{b}" x{c}')

    # --- bin identity (F1 'bin id in run.json'; F5 MANIFEST rexruntime/rexgpu)
    pins = parse_pins(open(BIN_PINS, encoding='utf-8-sig').read())
    want_bin = ROW_BIN[row]
    bd = rj.get('bin_dir') or ''
    P(os.path.basename(bd.rstrip('\\/')).lower() == want_bin, f'run.json bin_dir {bd} (want build/agent2/{want_bin})')
    pin = pins[want_bin]
    man = os.path.join(A2, want_bin, 'MANIFEST.txt')
    P(sha(man) == pin['manifest'], f'{want_bin} MANIFEST {sha(man)[:16]} = BIN-PINS {pin["manifest"][:16]}')
    if os.path.exists(os.path.join(run, 'MANIFEST.txt')):
        P(sha(os.path.join(run, 'MANIFEST.txt')) == pin['manifest'], 'run-dir MANIFEST.txt copy = pin')
    P((rj.get('exe_sha256') or ('' if _selftest_nobin else sha(os.path.join(run, 'legodimensions.exe')))).upper().startswith(pin['files']['legodimensions.exe']),
      'run.json exe_sha256 = pin' if rj.get('exe_sha256') else 'run-dir exe = pin')
    for fn in ('legodimensions.exe', 'rexruntime.dll', 'rexgpu-xenos.dll'):
        p = os.path.join(run, fn)
        if _selftest_nobin:
            res.append(('NOTE', f'run-dir {fn} hash: skipped (selftest)'))
        elif os.path.exists(p):
            h = sha(p)
            P(h.startswith(pin['files'][fn]), f'run-dir {fn} {h[:16]} (pin {pin["files"][fn]})')
        else:
            P(False, f'run-dir {fn} missing')

    # --- switches per row
    gw = {k: v for k, v in env.items() if k.startswith('LEGO_GPU_WAIT')}
    sdk = {k: v for k, v in cv.items() if k in OFF_SET}
    if row in ('F1', 'F4'):
        P(cv == {'framerate_limit': '0'}, f'cvars only framerate_limit=0: {cv}')
    if row == 'F2':
        P(not sdk, f'no SDK default key set on the command line/toml: {sdk}')
        P(cv.get('framerate_limit') == '0', f'framerate_limit=0 ({cv.get("framerate_limit")})', soft='NOTE')
    if row in ('F1', 'F2'):
        P(not gw, f'env has no LEGO_GPU_WAIT_*: {gw}')
    if row == 'F3':
        P(sdk == OFF_SET, f'the 12 old values set: {"all" if sdk == OFF_SET else {k: (sdk.get(k), v) for k, v in OFF_SET.items() if sdk.get(k) != v}}')
        P(env.get('LEGO_GPU_WAIT_BACKOFF_US') == 'off', f'env LEGO_GPU_WAIT_BACKOFF_US={env.get("LEGO_GPU_WAIT_BACKOFF_US")} (want off, lowercase)')
    if row == 'F4':
        P(gw == {'LEGO_GPU_WAIT_BACKOFF_US': '500'}, f'env LEGO_GPU_WAIT_* = {gw} (want BACKOFF_US=500 only)')
    if row.startswith('F5') or row == 'F7':
        P('LEGO_NATIVE_SHADER_MISS_CACHE' not in env, f'plain launch: LEGO_NATIVE_SHADER_MISS_CACHE unset ({env.get("LEGO_NATIVE_SHADER_MISS_CACHE")})')
    if row == 'F6':  # S3: nativefinal-off-bin; env unset (build-default OFF) or 0 (env OFF), both accepted
        mce = env.get('LEGO_NATIVE_SHADER_MISS_CACHE')
        P(mce in (None, '0'), f'env LEGO_NATIVE_SHADER_MISS_CACHE={mce} (want unset -> \"{L_MC_OFF_BUILD}\", or 0 -> \"{L_MC_OFF}\")')
        res.append(('NOTE', 'F6 variant: ' + ('env unset, build-default OFF' if mce is None else f'env {mce}')))
    if row in ('F5', 'F5w', 'F6', 'F7'):
        P(not sdk and not gw, f'no SDK key / back-off env on the old-SDK native bin: {sdk} {gw}')

    # --- check-defaults (rated tool, joined log)
    cds = sha(CHECK_DEFAULTS)[:16]
    P(cds == CHECK_DEFAULTS_SHA16, f'check-defaults.py {cds} (rated {CHECK_DEFAULTS_SHA16})')
    os.makedirs(TMP, exist_ok=True)
    joined = os.path.join(TMP, tmp_name(run))  # N5: parent_dir__run_dir, no collision across matrices
    with open(joined, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    mode = ROW_MODE[row]
    cp = subprocess.run([sys.executable, '-B', CHECK_DEFAULTS, joined, '--mode', mode], capture_output=True, text=True)
    fails = cd_fails(cp.stdout)
    res.append(('NOTE', f'check-defaults --mode {mode} exit {cp.returncode}; ' + (cp.stdout.strip().splitlines() or ['?'])[-1]))
    for fl in fails:
        res.append(('NOTE', '  check-defaults FAIL ' + fl))
    tot_miss = sum(miss_counts(lines).values())
    mc_absent = bool(fails) and all(MC_ABSENT in fl for fl in fails)
    if row == 'F6':
        rest = [fl for fl in fails if 'miss cache ON (build default) line' not in fl]
        P(cp.returncode in (0, 1) and not rest, f'check-defaults native-old: no FAIL apart from the miss-cache ON line ({len(rest)} other)')
        want_line = L_MC_OFF if env.get('LEGO_NATIVE_SHADER_MISS_CACHE') == '0' else L_MC_OFF_BUILD
        c_want, c_on = msgs.count(want_line), msgs.count(L_MC_ON)
        c_any = sum(1 for m in msgs if m.startswith(L_MC_ANY))
        if c_any == 0:  # M10 N1: the line is logged on the first miss only
            if tot_miss == 0:
                res.append(('HOLD', f'no miss-cache line and 0 shader-miss warnings (S1/N1: no miss on this route; cannot prove OFF)'))
            else:
                P(False, f'no miss-cache line but {tot_miss} shader-miss warnings (defect)')
        else:
            P(c_want == 1 and c_on == 0 and c_any == 1, f'"{want_line}" x{c_want}, ON line x{c_on}, miss-cache lines of any kind x{c_any}')
    elif row in ('F7', 'F5w') and cp.returncode == 1 and mc_absent:
        if tot_miss == 0:
            res.append(('HOLD', 'check-defaults native-old: only the miss-cache ON line is absent and 0 shader-miss warnings '
                                '(S1/N1: no miss on this route); the Overseer rules, citing 0 misses'))
        else:
            P(False, f'check-defaults native-old: miss-cache ON line absent but {tot_miss} shader-miss warnings (defect)')
    elif row == 'F2' and cp.returncode != 0:
        if not sdk and not gw:  # S2: switches clean, so a xenos-mode miss is unexplained
            res.append(('HOLD', 'check-defaults xenos not PASS on F2 with clean switches (S2); the Overseer rules'))
        else:
            res.append(('NOTE', 'check-defaults xenos not PASS on F2; the switch FAILs above explain it'))
    else:
        P(cp.returncode == 0, f'check-defaults --mode {mode} PASS')
    if row == 'F2':
        c = msgs.count(L_C1)
        P(c == 1, f'"{L_C1}" x{c}')
    if row in ('F2', 'F7'):
        isr = rj.get('input_script') or {}
        P(el is not None and el >= 590, f'elapsed {el} s ({el_src}; level route, >= 10 min; 590 s floor)')
        marks = []
        ic = os.path.join(run, 'input.csv')
        if os.path.exists(ic):
            marks = [m.group(1) for m in (re.search(r',mark,([^,\s]+)', l) for l in open(ic, encoding='utf-8', errors='replace')) if m]
        P('level' in os.path.basename(str(isr.get('script') or '')), f'route {isr.get("script")}')
        P('vortex' in marks, f'vortex mark reached (marks {marks[-4:]})')
        P(isr.get('steps_done') is not None and isr.get('steps_done') == isr.get('steps_total') and isr.get('stopped_by_script') is True,
          f'route steps {isr.get("steps_done")}/{isr.get("steps_total")}, stopped_by_script {isr.get("stopped_by_script")}')
        for l, t in route_timeouts(isr):
            res.append((l, t))
        tp = sum(1 for l in lines if 'Toypad' in l)
        P(tp > 0, f'Toypad lines {tp}')

    # --- F4 vs F1: same proof lines
    if row == 'F4' and pair:
        proof = ('Final defaults', 'Host timer resolution set', 'C1 keep-watch', 'TimerQueue:', 'GPU wait back-off:')
        a = [m for m in msgs if m.startswith(proof)]
        b = [msg(l) for l in read_lines(pair if os.path.isabs(pair) else os.path.join(REPO, pair))]
        b = [m for m in b if m.startswith(proof)]
        norm = lambda xs: [re.sub(r'\((env|default)\)', '(src)', x) for x in xs]
        P(norm(a) == norm(b), f'proof lines = F1 run ({len(a)} vs {len(b)}); env-source differences ignored')
        res.append(('NOTE', 'F4 documents q500 R3: check-defaults cannot tell env 500 from unset; run.json env is the proof'))

    # --- F5 native identity, miss warnings, warm path
    if row in ('F5', 'F5w', 'F6', 'F7'):
        exe = os.path.join(run, 'legodimensions.exe')
        if _selftest_nobin:
            res.append(('NOTE', 'run-dir exe fingerprint: skipped (selftest)'))
        else:
            P(contains(exe, NEW_FP) and not contains(exe, OLD_FP), f'run-dir exe has fingerprint {NEW_FP.decode()}, not {OLD_FP.decode()}')
        nb = open(NAT_BUILD_TXT, encoding='utf-8', errors='replace').read().strip()
        P(nb == 'LEGO Dimensions native GPU ' + NEW_FP.decode(), f'native-gpu-build.txt: {nb!r}')
        mt = open(os.path.join(A2, want_bin, 'MANIFEST.txt'), encoding='utf-8-sig').read().upper()
        P('A33801D1538D6175' in mt and 'E3CB99CFDEA95E66' in mt, f'{want_bin} MANIFEST lists rexruntime A33801D1 + rexgpu E3CB99CF')
    if row in ('F5', 'F5w'):
        mc = miss_counts(lines)
        if ref:
            rc = miss_counts(read_lines(ref if os.path.isabs(ref) else os.path.join(REPO, ref)))
            P(all(mc[k] <= rc[k] for k in MISS_KEYS) and sum(mc.values()) <= sum(rc.values()),
              f'shader-miss warnings {mc} (total {sum(mc.values())}) <= native4b n0 ref {rc} (total {sum(rc.values())})')
        else:
            P(False, f'shader-miss warnings {mc}: no --ref native4b n0 run given', soft='HOLD')
    if row == 'F5w':
        sv = []
        if not first:
            P(False, 'F5w needs --first <F5 first-launch run dir>')
        else:
            fl = [msg(l) for l in read_lines(first if os.path.isabs(first) else os.path.join(REPO, first))]
            sv = [int(m.group(1)) for m in (re.match(r'Native GPU: saved (\d+) startup pipeline recipes', x) for x in fl) if m]
            P(sv and max(sv) >= 1, f'first launch saved recipes {sv}')
        ld = [m for m in (re.match(r'Native GPU: startup pipelines loaded=(\d+) compiled=(\d+) failed=(\d+)', x) for x in msgs) if m]
        P(ld and int(ld[0].group(1)) >= 1 and int(ld[0].group(3)) == 0,
          f'second launch: startup pipelines loaded/compiled/failed {[(g.group(1), g.group(2), g.group(3)) for g in ld]}')
        if ld and sv:  # N6 (NOTE only)
            n_ld = int(ld[0].group(1))
            res.append(('NOTE', f'N6: loaded {n_ld} vs first launch max saved {max(sv)}: ' + ('equal' if n_ld == max(sv) else 'DIFFER')))
        c0 = sum(1 for x in msgs if x.startswith('Native GPU: no startup pipeline recipes yet'))
        c1 = sum(1 for x in msgs if x.startswith('Native GPU: ignoring invalid or incompatible pipeline recipes'))
        P(c0 == 0 and c1 == 0, f'"no startup pipeline recipes yet" x{c0}, "ignoring invalid or incompatible" x{c1}')
    return res


def verdict(res):
    lv = [l for l, _ in res]
    return 'FAIL' if 'FAIL' in lv else ('HOLD' if 'HOLD' in lv else 'PASS')


def selftest():
    ok = 0; bad = 0

    def T(c, name):
        nonlocal ok, bad
        ok += bool(c); bad += (not c)
        print(('  ok   ' if c else '  BAD  ') + name)

    T(msg('[2026-11-25 07:00:00.000] [info] [core] [t1] Native GPU: x') == 'Native GPU: x', 'msg strips 4 brackets')
    pins = parse_pins(open(BIN_PINS, encoding='utf-8-sig').read())
    T(set(pins) == {'devfinal-bin', 'devfinal-off-bin', 'nativefinal-bin', 'nativefinal-off-bin'}, 'BIN-PINS 4 bins')
    T(pins['nativefinal-bin']['files']['rexruntime.dll'] == 'A33801D1538D6175', 'pins nativefinal rexruntime')
    T(pins['devfinal-bin']['files']['amd_fidelityfx_dx12.dll'] is None, 'pins devfinal no fidelityfx')
    T(run_switches({'params': {'cvar': ['framerate_limit=0']}, 'env_set': {'A': '1'}}) == ({'framerate_limit': '0'}, {'A': '1'}, 'matrix'), 'matrix switches')
    T(run_switches({'cvars': {'x': 1}, 'env': {}}) == ({'x': '1'}, {}, 'harness'), 'harness switches')
    T(cd_fails('  ok   a\n  FAIL b: 0 (want 1)\nRESULT FAIL (1)') == ['b: 0 (want 1)'], 'cd_fails parse')
    os.makedirs(TMP, exist_ok=True)
    d = os.path.join(TMP, 'selftest-rot')
    os.makedirs(d, exist_ok=True)
    for n, t in (('game.2.log', 'a'), ('game.1.log', 'b'), ('game.log', 'c')):
        open(os.path.join(d, n), 'w').write(t + '\n')
    T(read_lines(d) == ['a', 'b', 'c'], 'rotated logs joined oldest first')
    T(miss_counts(['x shader not present in AOT cache, hash', 'missing from AOT index']) ==
      {MISS_KEYS[0]: 1, MISS_KEYS[1]: 1, MISS_KEYS[2]: 0, MISS_KEYS[3]: 0}, 'miss_counts')
    # v2 units: N5 tmp name, N1 elapsed
    ta, tb, tc = tmp_name(r'C:\x\m1\runs\r1'), tmp_name('C:\\x\\m2\\runs\\r1\\'), tmp_name('C:\\X\\M1\\RUNS\\R1')
    T(ta.startswith('runs__r1__') and ta.endswith('.joined.log') and ta != tb and ta.upper() == tc.upper(),
      'N5 tmp name = parent__run__pathhash (two matrices differ)')
    T(elapsed({'elapsed_s': 612.5}) == (612.5, 'elapsed_s') and
      elapsed({'start': '2026-11-25 04:00:51.529', 'end': '2026-11-25 04:02:47.349'}) == (115.82, 'end-start') and
      elapsed({}) == (None, 'absent'), 'N1 elapsed (harness / matrix / absent)')
    # v2 synthetic fixtures (harness layout); run-dir binary checks skipped, everything else real (BIN-PINS, check-defaults)
    import importlib.util, shutil
    spec = importlib.util.spec_from_file_location('cdmod', CHECK_DEFAULTS)
    cdm = importlib.util.module_from_spec(spec); spec.loader.exec_module(cdm)
    PFX = '[2026-11-25 07:00:00.000] [info] [core] [t1] '
    FX = os.path.join(TMP, 'selftest-fx')

    def fx(name, b, body, cvars=None, env=None, extra=None, marks=None):
        d = os.path.join(FX, name)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        rj = {'exit_code': 0, 'exit_code_hex': '0x00000000', 'exited_early': False, 'wer_seen': False, 'dumps': [],
              'crash_events': [], 'close_method': 'wm_close', 'bin_dir': os.path.join(A2, b),
              'exe_sha256': pins[b]['files']['legodimensions.exe'] + '0' * 48,
              'cvars': cvars if cvars is not None else {}, 'env': env or {}, 'elapsed_s': 30.0}
        rj.update(extra or {})
        json.dump(rj, open(os.path.join(d, 'run.json'), 'w'))
        open(os.path.join(d, 'game.log'), 'w').write(''.join(PFX + l + '\n' for l in body + ['Title terminated; hard-exiting process.']))
        if marks:
            open(os.path.join(d, 'input.csv'), 'w').write('t,kind,arg\n' + ''.join(f'{i}.0,mark,{m}\n' for i, m in enumerate(marks)))
        return d

    def lv(r, level, needle):
        return any(l == level and needle in t for l, t in r)

    xen = ['Final defaults: ' + ' '.join(f'{k}={v[0]}(default)' for k, v in cdm.RUNTIME_KEYS.items()),
           'Final defaults (GPU): ' + ' '.join(f'{k}={v[0]}(default)' for k, v in cdm.GPU_KEYS.items()),
           cdm.L_TIMER, cdm.L_C1, cdm.L_TQ, cdm.L_BO_ON]
    TAIL = 'BE08A7908005B3B6113BE199274C1D0E9F4D76B7C2116FA1B860B27F00184ABC'
    tail_tl = sorted(ROUTE_TIMEOUTS[TAIL][1])
    route = {'elapsed_s': 600.0, 'input_script': {'script': r'C:\r\level-l-tail.txt', 'script_sha256': TAIL, 'steps_done': 121,
                                                  'steps_total': 121, 'stopped_by_script': True, 'timeouts': 31,
                                                  'timeout_lines': ' '.join(map(str, tail_tl))}}
    r = gate(fx('f1', 'devfinal-bin', xen, {'framerate_limit': 0}), 'F1', _selftest_nobin=True)
    T(verdict(r) == 'PASS' and lv(r, 'PASS', 'check-defaults --mode xenos PASS') and lv(r, 'NOTE', 'elapsed 30.0 s'), 'fx F1 positive -> PASS')
    r = gate(fx('f1-gw', 'devfinal-bin', xen, {'framerate_limit': 0}, {'LEGO_GPU_WAIT_BACKOFF_US': '500'}), 'F1', _selftest_nobin=True)
    T(verdict(r) == 'FAIL' and lv(r, 'FAIL', 'LEGO_GPU_WAIT'), 'fx F1 with back-off env -> FAIL')
    r = gate(fx('f1-binoff', 'devfinal-off-bin', xen, {'framerate_limit': 0}), 'F1', _selftest_nobin=True)
    T(verdict(r) == 'FAIL' and lv(r, 'FAIL', 'bin_dir'), 'fx F1 on devfinal-off-bin -> FAIL (bin)')
    f2 = [l for l in xen if l != cdm.L_TQ] + ['Toypad: connected']
    r = gate(fx('f2', 'devfinal-bin', f2, {'framerate_limit': 0}, extra=route, marks=['a1', 'vortex']), 'F2', _selftest_nobin=True)
    T(verdict(r) == 'HOLD' and lv(r, 'HOLD', 'S2'), 'fx F2 xenos miss, clean switches -> HOLD (S2)')
    r = gate(fx('f2-sdk', 'devfinal-bin', f2, {'framerate_limit': 0, 'cs_spin': 'false'}, extra=route, marks=['vortex']), 'F2', _selftest_nobin=True)
    T(verdict(r) == 'FAIL' and not lv(r, 'HOLD', 'S2'), 'fx F2 xenos miss with an SDK key -> FAIL, no HOLD')
    nat = ['Native GPU: renderer up', 'Toypad: connected']
    r = gate(fx('f7', 'nativefinal-bin', nat, extra=route, marks=['vortex']), 'F7', _selftest_nobin=True)
    T(verdict(r) == 'HOLD' and lv(r, 'HOLD', 'S1/N1'), 'fx F7 no miss-cache line, 0 misses -> HOLD (S1)')
    r = gate(fx('f7-miss', 'nativefinal-bin', nat + ['Native GPU: shader not present in AOT cache 0x1'], extra=route, marks=['vortex']),
             'F7', _selftest_nobin=True)
    T(verdict(r) == 'FAIL' and lv(r, 'FAIL', '1 shader-miss warnings (defect)'), 'fx F7 no miss-cache line, 1 miss -> FAIL')
    r = gate(fx('f7-ok', 'nativefinal-bin', nat + [L_MC_ON], extra=route, marks=['vortex']), 'F7', _selftest_nobin=True)
    T(verdict(r) == 'PASS', 'fx F7 with the miss-cache ON line -> PASS')
    r = gate(fx('f7-short', 'nativefinal-bin', nat + [L_MC_ON], extra=dict(route, elapsed_s=500.0), marks=['vortex']), 'F7', _selftest_nobin=True)
    T(verdict(r) == 'FAIL' and lv(r, 'FAIL', 'elapsed 500.0'), 'fx F7 500 s -> FAIL (590 s floor)')
    r = gate(fx('f6', 'nativefinal-off-bin', nat + [L_MC_OFF_BUILD]), 'F6', _selftest_nobin=True)
    T(verdict(r) == 'PASS' and lv(r, 'NOTE', 'build-default OFF'), 'fx F6 nativefinal-off, env unset, build-default OFF line -> PASS')
    r = gate(fx('f6-env0', 'nativefinal-off-bin', nat + [L_MC_OFF], env={'LEGO_NATIVE_SHADER_MISS_CACHE': '0'}), 'F6', _selftest_nobin=True)
    T(verdict(r) == 'PASS', 'fx F6 nativefinal-off, env 0, env OFF line -> PASS')
    r = gate(fx('f6-wrong', 'nativefinal-off-bin', nat + [L_MC_OFF_BUILD], env={'LEGO_NATIVE_SHADER_MISS_CACHE': '0'}), 'F6', _selftest_nobin=True)
    T(verdict(r) == 'FAIL', 'fx F6 env 0 but build-default line -> FAIL')
    r = gate(fx('f6-on', 'nativefinal-bin', nat + [L_MC_ON]), 'F6', _selftest_nobin=True)
    T(verdict(r) == 'FAIL' and lv(r, 'FAIL', 'bin_dir'), 'fx F6 on nativefinal-bin (ON line) -> FAIL')
    r = gate(fx('f6-none', 'nativefinal-off-bin', nat), 'F6', _selftest_nobin=True)
    T(verdict(r) == 'HOLD', 'fx F6 no miss-cache line, 0 misses -> HOLD')
    f5 = fx('f5', 'nativefinal-bin', nat + [L_MC_ON, 'Native GPU: saved 3 startup pipeline recipes'])
    wl = ['Native GPU: startup pipelines loaded=3 compiled=0 failed=0 resident=3 elapsed_ms=5', 'Toypad: connected']
    r = gate(fx('f5w', 'nativefinal-bin', wl), 'F5w', ref=f5, first=f5, _selftest_nobin=True)
    T(verdict(r) == 'HOLD' and lv(r, 'HOLD', 'S1/N1') and lv(r, 'NOTE', 'N6: loaded 3 vs first launch max saved 3: equal'),
      'fx F5w no miss-cache line, 0 misses -> HOLD (S1), N6 equal')
    r = gate(fx('f5w-ok', 'nativefinal-bin', wl + [L_MC_ON]), 'F5w', ref=f5, first=f5, _selftest_nobin=True)
    T(verdict(r) == 'PASS', 'fx F5w with the miss-cache ON line -> PASS')
    r = gate(fx('f5w-noref', 'nativefinal-bin', wl + [L_MC_ON]), 'F5w', first=f5, _selftest_nobin=True)
    T(verdict(r) == 'HOLD', 'fx F5w without --ref -> HOLD (G4)')
    r = gate(f5, 'F5', ref=f5, _selftest_nobin=True)
    T(verdict(r) == 'PASS', 'fx F5 first launch -> PASS')
    T(os.path.exists(os.path.join(TMP, tmp_name(f5))) and tmp_name(f5).startswith('selftest-fx__f5__'), 'N5 joined log named selftest-fx__f5__<hash>')
    # v3: F3 positive on devfinal-off-bin (S3)
    off = ['Final defaults: ' + ' '.join(f'{k}={v[1]}(cvar)' for k, v in cdm.RUNTIME_KEYS.items()),
           'Final defaults (GPU): ' + ' '.join(f'{k}={v[1]}(cvar)' for k, v in cdm.GPU_KEYS.items()), cdm.L_BO_OFF]
    f3cv = dict(OFF_SET, framerate_limit='0')
    r = gate(fx('f3', 'devfinal-off-bin', off, f3cv, {'LEGO_GPU_WAIT_BACKOFF_US': 'off'}), 'F3', _selftest_nobin=True)
    T(verdict(r) == 'PASS' and lv(r, 'PASS', 'check-defaults --mode off PASS'), 'fx F3 devfinal-off-bin + 12 old values + BACKOFF_US=off -> PASS')
    r = gate(fx('f3-on', 'devfinal-bin', off, f3cv, {'LEGO_GPU_WAIT_BACKOFF_US': 'off'}), 'F3', _selftest_nobin=True)
    T(verdict(r) == 'FAIL' and lv(r, 'FAIL', 'bin_dir'), 'fx F3 on devfinal-bin -> FAIL (bin)')
    # v3: F2/F7 route timeouts (Overseer 13:55Z)
    rf = {k: open(p, encoding='utf-8').read().splitlines() for k, p in ROUTE_FILES.items()}
    T(all(sha(ROUTE_FILES[n]) == s for s, (n, _) in ROUTE_TIMEOUTS.items()), 'route files on disk = ROUTE_TIMEOUTS shas')
    T(all(rf['level-l.txt'][n - 1] == rf['level-l-tail.txt'][n - 8] and rf['level-l.txt'][n - 1].startswith('wait_log') for n in _LL)
      and rf['level-l.txt'][116] == rf['level-l-tail.txt'][109] and 109 + 1 not in ROUTE_TIMEOUTS[TAIL][1],
      'tail by-design lines = level-l lines - 7 (same wait_log text); the 240 s orange wait is not in the set')
    rt = lambda **kw: route_timeouts(dict(route['input_script'], **kw))
    T(all(l == 'PASS' for l, _ in rt()), 'route_timeouts: tail, 31 by-design -> PASS')
    r = rt(timeouts=29, timeout_lines=' '.join(map(str, tail_tl[2:])))
    T(all(l != 'FAIL' for l, _ in r) and any(l == 'NOTE' and '2 by-design waits' in t for l, t in r), 'route_timeouts: tail, 29 of 31 -> PASS + NOTE')
    T(any(l == 'FAIL' and 'NOT by design: [110]' in t for l, t in rt(timeouts=32, timeout_lines=' '.join(map(str, tail_tl + [110])))),
      'route_timeouts: extra timeout on the 240 s orange wait -> FAIL')
    T(any(l == 'FAIL' and 'NOT by design' in t for l, t in rt(timeout_lines=' '.join(map(str, sorted(ROUTE_TIMEOUTS[
        '6F9E600963440B451B591899A17DAD9A5941A8930AA502B597155CBB636F9A63'][1]))))),
      'route_timeouts: level-l numbering on the tail route -> FAIL')
    T(any(l == 'FAIL' and 'timeout_lines count' in t for l, t in rt(timeouts=30)), 'route_timeouts: count != listed lines -> FAIL')
    T(any(l == 'FAIL' and 'unknown route' in t for l, t in rt(script_sha256='00' * 32)), 'route_timeouts: unknown route sha -> FAIL')
    r = gate(fx('f2-x', 'devfinal-bin', f2 + [cdm.L_TQ], {'framerate_limit': 0},
                extra=dict(route, input_script=dict(route['input_script'], timeouts=32, timeout_lines=' '.join(map(str, tail_tl + [15])))),
                marks=['vortex']), 'F2', _selftest_nobin=True)
    T(verdict(r) == 'FAIL' and lv(r, 'FAIL', 'NOT by design: [15]'), 'fx F2 with an extra (non-design) timeout -> FAIL')
    r = gate(fx('f2-steps', 'devfinal-bin', f2 + [cdm.L_TQ], {'framerate_limit': 0},
                extra=dict(route, input_script=dict(route['input_script'], steps_done=120, stopped_by_script=False)),
                marks=['vortex']), 'F2', _selftest_nobin=True)
    T(verdict(r) == 'FAIL' and lv(r, 'FAIL', 'route steps 120/121'), 'fx F2 steps 120/121, not stopped by script -> FAIL')
    r = gate(fx('f2-ok', 'devfinal-bin', f2 + [cdm.L_TQ], {'framerate_limit': 0}, extra=route, marks=['vortex']), 'F2', _selftest_nobin=True)
    T(verdict(r) == 'PASS', 'fx F2 tail route, 31 by-design timeouts, xenos PASS -> PASS')
    # real level-l runs (old bins): route/timeout items and the common checks except bin
    ar = os.path.join(REPO, 'build', 'agent3', 'runs')
    common = ('exit_code', 'exited_early', 'WER', 'dialogs', 'crash_events', 'dumps', 'close', '"Title terminated"', 'bad string')
    for d in ('20261125-062932-s4b-V0f-c1off-verify-level-vfix', '20261125-063859-s4b-07f-c1v-level-vfix'):
        if os.path.isdir(os.path.join(ar, d)):
            r = gate(os.path.join(ar, d), 'F2', _selftest_nobin=True)
            rr = [(l, t) for l, t in r if t.startswith(('route', 'timeouts', 'vortex', 'Toypad'))]
            cm = [(l, t) for l, t in r if t.startswith(common)]
            T(len(rr) == 7 and all(l == 'PASS' for l, _ in rr), f'{d[16:24]} as F2: route name/sha, steps, 31 timeouts by design, vortex, Toypad PASS')
            bad_cm = [t for l, t in cm if l != 'PASS']  # these rows ran physical_protect_keep_watch_verify=true by design
            T(len(cm) == 18 and bad_cm == ['bad string "C1 verify: on" x1'],
              f'{d[16:24]} as F2: common checks (exit .. bad strings) PASS except "C1 verify: on" (verify=1 row): {bad_cm}')
            T(lv(r, 'FAIL', 'bin_dir'), f'{d[16:24]} as F2: bin FAIL (old bin)')
    d = os.path.join(ar, '20261122-222313-w6-gateB-p2fc-level')
    if os.path.isdir(d):
        T(lv(gate(d, 'F2', _selftest_nobin=True), 'FAIL', 'NOT by design: [22]'), 'w6-gateB (timeout on line 22) as F2 -> timeout FAIL')
    d = os.path.join(ar, '20261125-025738-cg26L-level')
    if os.path.isdir(d):
        r = route_timeouts(json.load(open(os.path.join(d, 'run.json'), encoding='utf-8-sig'))['input_script'])
        T(all(l != 'FAIL' for l, _ in r) and any(l == 'NOTE' for l, _ in r), 'cg26L (27 of 31 timeouts) -> timeouts PASS + NOTE')
    # negative controls on real old-bin runs: must FAIL closed
    w8 = os.path.join(REPO, 'build', 'agent8', 'matrix', '20261125-0359', 'runs')
    n0 = os.path.join(w8, '0400-n0-r1')
    if os.path.isdir(n0):
        r = gate(n0, 'F5', ref=n0)
        txt = [t for l, t in r if l == 'FAIL']
        T(verdict(r) == 'FAIL' and any('bin_dir' in t for t in txt) and any('check-defaults --mode native-old PASS' in t for t in txt),
          'native4b n0 as F5 -> FAIL (bin, no miss-cache line)')
        T(any(l == 'PASS' and 'shader-miss warnings' in t for l, t in r), 'n0 vs itself: miss warnings <= ref')
    wc = os.path.join(REPO, 'build', 'agent8', 'matrix', '20261125-0315', 'runs', '0319-win3-r1')
    if os.path.isdir(wc):
        r = gate(wc, 'F1')
        txt = [t for l, t in r if l == 'FAIL']
        T(verdict(r) == 'FAIL' and any('bin_dir' in t for t in txt) and any('check-defaults --mode xenos PASS' in t for t in txt),
          'win3 (devoff4b) as F1 -> FAIL (bin, no Final defaults lines)')
        r = gate(wc, 'F3')
        T(verdict(r) == 'FAIL' and any(l == 'FAIL' and 'devfinal-off-bin' in t for l, t in r), 'win3 (devoff4b) as F3 -> FAIL (bin devfinal-off)')
    if os.path.isdir(n0):
        r = gate(n0, 'F6')
        T(verdict(r) == 'FAIL' and any(l == 'FAIL' and 'nativefinal-off-bin' in t for l, t in r), 'native4b n0 as F6 -> FAIL (bin nativefinal-off)')
    print(f'SELFTEST {ok}/{ok + bad}')
    return 0 if not bad else 1


def main(argv):
    if argv[1:2] == ['--selftest']:
        return selftest()
    if len(argv) < 3 or argv[2] not in ROW_BIN:
        print(__doc__)
        return 2
    opts = {}
    a = argv[3:]
    for i in range(0, len(a) - 1, 2):
        opts[a[i].lstrip('-')] = a[i + 1]
    try:
        res = gate(argv[1], argv[2], ref=opts.get('ref'), first=opts.get('first'), pair=opts.get('pair'))
    except (OSError, ValueError, KeyError) as e:
        print('cannot gate:', repr(e))
        return 2
    for l, t in res:
        print(f'{l:5} {t}')
    v = verdict(res)
    print(f'F-GATE {argv[2]} {os.path.basename(argv[1].rstrip(chr(92) + "/"))}: {v}')
    return {'PASS': 0, 'FAIL': 1, 'HOLD': 4}[v]


if __name__ == '__main__':
    sys.exit(main(sys.argv))
