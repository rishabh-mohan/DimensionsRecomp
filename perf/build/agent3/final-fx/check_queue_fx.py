"""check_queue_fx.py (M3, 11-25): checks the FINAL F1-F7 queue draft (build/agent3/final-fx/queue-final-fx.jsonl) before
it is installed into build/agent3/s4b/queue.jsonl. Read-only, except --dryrun, which runs harness/run-game.ps1 -DryRun per
run-game row with -RunsRoot build/agent3/final-fx/dryrun (bin mirror + toml + env + input-script load; no game launch) and
checks the run.json it writes.

Usage: python -B check_queue_fx.py [queue file] [--live build/agent3/s4b/queue.jsonl] [--dryrun] [--fg-sha8 <rated final_gate sha8>]
Exit 0 = ALL CHECKS PASS, 1 = a check failed, 2 = usage / unreadable.
Spec: M10 final-defaults-rating C20B6FDB "Functional set", M10 final-gate-rating AE8EB2A5 (G1, bins: F3 devfinal-off,
F6 nativefinal-off), M12 FINAL-F-GATES E5797623, M2 BIN-PINS FE4CD4FF.
"""
import glob, hashlib, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
A2 = os.path.join(REPO, 'build', 'agent2')
FXD = 'build\\agent3\\final-fx'
READY = 'build\\agent3\\s4b\\ready-s4b-off'
GO, OPT = FXD + '\\go-fx', FXD + '\\go-fx-opt'
OFF12 = ('shared_memory_single_hold_rearm=false;physical_protect_hold_global_lock=false;physical_protect_keep_watch=false;'
         'host_timer_resolution_ms=0;host_timer_throttling_optout=false;precise_guest_sleep=false;wait_timeout_round_up=false;'
         'cs_spin=false;spinlock_pause_spin=false;clock_lockfree=false;tls_bounds_fix=false;timer_queue_precise_wait=false')
W8A = 'native_settings_frontend=false;native_fps_limit=0;framerate_limit=0'
ROUTE = FXD + '\\level-l-tail.txt'
LEVEL_L = os.path.join(REPO, 'build', 'agent3', 'toypad', 'routes', 'level-l.txt')
MATRIX = FXD + '\\matrix-fx5.json'


def kv(s):
    out = {}
    for item in (s or '').split(';'):
        if item.strip():
            k, _, v = item.partition('=')
            out[k.strip()] = v.strip()
    return out


# id: bin, cvars, env, seconds, input script, toypad, needs (beyond READY + GO), optional
SPEC = {
    'fx1': ('devfinal-bin', kv('framerate_limit=0'), {}, 240, None, False, [], False),
    'fx3': ('devfinal-off-bin', kv('framerate_limit=0;' + OFF12), {'LEGO_GPU_WAIT_BACKOFF_US': 'off'}, 240, None, False,
            [FXD + '\\fx-ok-fx1'], False),
    'fx2': ('devfinal-bin', kv('framerate_limit=0'), {}, 840, ROUTE, True, [FXD + '\\fx-ok-fx3'], False),
    'fx4': ('devfinal-bin', kv('framerate_limit=0'), {'LEGO_GPU_WAIT_BACKOFF_US': '500'}, 240, None, False,
            [OPT, FXD + '\\fx-ok-fx1'], True),
    'fx5': ('matrix', None, None, None, None, False, [FXD + '\\fx-ok-fx2', MATRIX], False),
    'fx6': ('nativefinal-off-bin', kv(W8A), {}, 240, None, False, [FXD + '\\fx-ok-fx5w'], False),
    'fx7': ('nativefinal-bin', kv(W8A), {}, 840, ROUTE, True, [FXD + '\\fx-ok-fx6'], False),
}
ORDER = ['fx1', 'fx3', 'fx2', 'fx4', 'fx5', 'fx6', 'fx7']  # fx3e/fx6e dropped (Overseer 07:55 ruling 2)
FX_ROW = {'fx1': 'F1', 'fx2': 'F2', 'fx3': 'F3', 'fx4': 'F4', 'fx5': 'F5', 'fx6': 'F6', 'fx7': 'F7'}
FINAL_GATE = os.path.join(REPO, 'build', 'agent12', 'session3', 'final_gate.py')
FG_PIN = []  # --fg-sha8 <sha8 M10 rated>: required at install (M12 is still revising final_gate at draft time)


def check_final_gate():
    """final_gate: sha = the rated one (if --fg-sha8), and its ROW_BIN agrees with the queue bins (F3/F6 on the OFF bins)."""
    import ast
    s = sha(FINAL_GATE)[:8] if os.path.isfile(FINAL_GATE) else 'missing'
    if FG_PIN:
        T(s == FG_PIN[0], f'final_gate.py sha {s} = rated {FG_PIN[0]}')
    else:
        print(f'  note final_gate.py sha {s} (not pinned; pass --fg-sha8 <rated sha8> at install)')
    m = re.search(r'^ROW_BIN = (\{.*?\})', open(FINAL_GATE, encoding='utf-8').read(), re.M | re.S)
    rb = ast.literal_eval(m.group(1)) if m else {}
    for rid, row in FX_ROW.items():
        if SPEC[rid][0] != 'matrix':
            T(rb.get(row) == SPEC[rid][0], f'final_gate ROW_BIN[{row}] {rb.get(row)} = {rid} bin {SPEC[rid][0]}')
    T(rb.get('F5') == rb.get('F5w') == 'nativefinal-bin', f'final_gate ROW_BIN F5/F5w {rb.get("F5")}/{rb.get("F5w")} = matrix bin nativefinal-bin')

ok_n = bad_n = 0


def T(cond, text):
    global ok_n, bad_n
    ok_n += bool(cond)
    bad_n += (not cond)
    print(('  ok   ' if cond else '  FAIL ') + text)
    return cond


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def pins():
    t = open(os.path.join(A2, 'final', 'BIN-PINS.md'), encoding='utf-8-sig').read()
    return {m.group(1): m.group(2) for m in re.finditer(r'^\| \S+ \| (\S+-bin) \| ([0-9A-F]{64}) \|', t, re.M)}


def args_map(args):
    m, i = {}, 0
    while i < len(args):
        a = args[i]
        if a.startswith('-') and i + 1 < len(args) and not args[i + 1].startswith('-'):
            if a in m:
                m[a] += ';' + args[i + 1]
            else:
                m[a] = args[i + 1]
            i += 2
        else:
            m[a] = True
            i += 1
    return m


def load_jsonl(path):
    rows = []
    for n, line in enumerate(open(path, encoding='utf-8-sig'), 1):
        if line.strip() and not line.strip().startswith('#'):  # s4b-queue.ps1 skips '#' lines
            try:
                rows.append(json.loads(line))
            except ValueError as e:
                T(False, f'{os.path.basename(path)} line {n} is not JSON: {e}')
    return rows


def check_matrix():
    p = os.path.join(REPO, MATRIX)
    mx = json.load(open(p, encoding='utf-8-sig'))
    arms = {a['id']: a for a in mx.get('arms', [])}
    T(list(arms) == ['fx5', 'fx5w'], f'matrix arms in order fx5, fx5w: {list(arms)}')
    T(mx.get('order') == 'fixed' and mx.get('repeats') == 1 and mx.get('cold_run') is False,
      f'matrix order fixed / repeats 1 / cold_run false: {mx.get("order")} {mx.get("repeats")} {mx.get("cold_run")}')
    T((mx.get('warmup_s'), mx.get('measure_s'), mx.get('warmup_from'), mx.get('min_window_after_ff_s')) == (55, 50, 'firstframe', 60),
      'matrix W8a window: 55 s warm-up from the first frame, 50 s, floor 60 s')
    for aid, a in arms.items():
        T(a.get('bin') == 'build/agent2/nativefinal-bin', f'{aid} bin {a.get("bin")}')
        T(a.get('cvars') == W8A.split(';'), f'{aid} cvars = W8a {a.get("cvars")}')
        env = a.get('env') or {}
        T(set(env) == {'LEGO_NATIVE_FRAME_METRICS'}, f'{aid} env only LEGO_NATIVE_FRAME_METRICS (plain launch): {sorted(env)}')
        T(a.get('frames') == 'native' and a.get('repeats') == 1, f'{aid} frames native, repeats 1')
    T(arms.get('fx5', {}).get('ref') is True and 'seed_cache' not in arms.get('fx5', {}), 'fx5 = ref, no seed (first launch)')
    T(arms.get('fx5w', {}).get('seed_cache') == 'fx5' and not arms.get('fx5w', {}).get('seed_recipes_only'),
      'fx5w seed_cache fx5, both files (native-pso.bin + native-pso-recipes.bin)')


def check_route():
    p = os.path.join(REPO, ROUTE)
    t = open(p, encoding='ascii').read().splitlines()
    src = open(LEVEL_L, encoding='utf-8-sig').read().splitlines()
    head = [i for i, l in enumerate(t) if l.startswith('#') and i < 10]
    body = t[len(head):]
    T(sha(LEVEL_L)[:8] == '6F9E6009', f'level-l.txt sha {sha(LEVEL_L)[:8]} (6F9E6009 = s4bV0f/s4b07f route)')
    T(body[:len(src) - 13] == src[12:-1] and src[-1].strip() == 'stop',
      f'level-l-tail = level-l lines 13-{len(src) - 1} unchanged ({len(src) - 13} lines) + tail')
    tail = [l.split('#')[0].strip() for l in body[len(src) - 13:]]
    T(tail == ['sleep 180', 'mark tail', 'stop'], f'tail steps {tail}')
    T(any(l.split('#')[0].strip() == 'mark vortex' for l in body), 'route has mark vortex (final_gate F2/F7)')
    T('level' in os.path.basename(p), 'route file name has "level" (final_gate F2/F7)')


def dryrun(row, spec):
    bin_, cv, env, secs, script, _tp, _n, _o = spec
    out = os.path.join(REPO, FXD, 'dryrun')
    os.makedirs(out, exist_ok=True)
    before = set(os.listdir(out))
    cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(REPO, 'harness', 'run-game.ps1')] + \
          [str(a) for a in row['args']] + ['-DryRun', '-RunsRoot', out]
    cp = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    new = sorted(set(os.listdir(out)) - before)
    if not T(cp.returncode == 0 and len(new) == 1, f'{row["id"]} run-game -DryRun exit {cp.returncode}, new dirs {new}'):
        print('       ' + (cp.stdout + cp.stderr).strip().replace('\n', '\n       ')[-800:])
        return
    rj = json.load(open(os.path.join(out, new[0], 'run.json'), encoding='utf-8-sig'))
    T(os.path.basename(rj['bin_dir'].rstrip('\\/')) == bin_, f'{row["id"]} dry run.json bin_dir {rj["bin_dir"]}')
    T({k: str(v) for k, v in (rj.get('cvars') or {}).items()} == cv, f'{row["id"]} dry run.json cvars = spec ({len(cv)})')
    e = {k: v for k, v in (rj.get('env') or {}).items() if k.startswith('LEGO_') and k != 'LEGO_NATIVE_FRAME_METRICS'}
    T(e == env, f'{row["id"]} dry run.json env (LEGO_*, no metrics) {e}')
    exe = os.path.join(A2, bin_, 'legodimensions.exe')
    T((rj.get('exe_sha256') or '').upper() == sha(exe), f'{row["id"]} dry exe_sha256 = {bin_} exe {sha(exe)[:16]}')
    if script:
        isr = rj.get('input_script') or {}
        T(isr.get('steps_total') and isr.get('script_sha256', '').upper() == sha(os.path.join(REPO, script)),
          f'{row["id"]} input script loaded: {isr.get("steps_total")} steps, sha {str(isr.get("script_sha256"))[:8]}')


def main(argv):
    a = [x for x in argv[1:] if not x.startswith('--')]
    q = a[0] if a else os.path.join(HERE, 'queue-final-fx.jsonl')
    live = os.path.join(REPO, 'build', 'agent3', 's4b', 'queue.jsonl')
    if '--live' in argv:
        live = argv[argv.index('--live') + 1]
        a = [x for x in a if x != live]
        q = a[0] if a else os.path.join(HERE, 'queue-final-fx.jsonl')
    if '--fg-sha8' in argv:
        FG_PIN.append(argv[argv.index('--fg-sha8') + 1].upper())
        a = [x for x in a if x.upper() != FG_PIN[0]]
        q = a[0] if a else os.path.join(HERE, 'queue-final-fx.jsonl')
    if not os.path.isfile(q):
        print('no queue file', q)
        return 2
    print(f'# check_queue_fx {q} (sha {sha(q)[:8]})')
    rows = load_jsonl(q)
    ids = [r.get('id') for r in rows]
    T(ids == ORDER, f'ids in order {ids}')
    T(len(set(ids)) == len(ids), 'ids unique in the draft')
    old = {r.get('id') for r in load_jsonl(live)} if os.path.isfile(live) else set()
    st = os.path.join(REPO, 'build', 'agent3', 's4b', 'queue-state.jsonl')
    done = {r.get('id') for r in load_jsonl(st)} if os.path.isfile(st) else set()
    T(not (set(ids) & old), f'no id already in the live queue {sorted(set(ids) & old)}')
    T(not (set(ids) & done), f'no id already in queue-state (would count as done) {sorted(set(ids) & done)}')
    T(os.path.isfile(os.path.join(REPO, READY)), f'{READY} exists')
    for m in [GO, OPT] + [FXD + '\\fx-ok-' + i for i in ORDER + ['fx5w']]:
        T(not os.path.exists(os.path.join(REPO, m)), f'marker {m} absent before install')
    pin = pins()
    for b in ('devfinal-bin', 'devfinal-off-bin', 'nativefinal-bin', 'nativefinal-off-bin'):
        mp = os.path.join(A2, b, 'MANIFEST.txt')
        T(os.path.isfile(mp) and sha(mp) == pin.get(b), f'{b} MANIFEST {sha(mp)[:16] if os.path.isfile(mp) else "missing"} = BIN-PINS {str(pin.get(b))[:16]}')
        T(not os.path.exists(os.path.join(A2, b, 'cache')), f'{b} has no cache/ (D7: first native launch is cold)')
    est = 0
    for r in rows:
        rid = r.get('id')
        if rid not in SPEC:
            T(False, f'{rid}: no spec')
            continue
        bin_, cv, env, secs, script, tp, needs, opt = SPEC[rid]
        want_needs = [READY, GO] + needs
        T(r.get('needs') == want_needs, f'{rid} needs {r.get("needs")}')
        for n in r.get('needs') or []:
            T(n.startswith('build\\agent3\\'), f'{rid} need under build\\agent3: {n}')
        T(bool(r.get('toypad')) == tp, f'{rid} toypad {bool(r.get("toypad"))}')
        if bin_ == 'matrix':
            T(r.get('matrix') == MATRIX and r.get('args') == [] and r.get('matrix_args') == ['-NoCold'],
              f'{rid} matrix row {r.get("matrix")} {r.get("matrix_args")}')
            T(r.get('est', 0) >= 420, f'{rid} est {r.get("est")} >= 420 (PlanOnly says ~5 min)')
            check_matrix()
        else:
            m = args_map(r.get('args') or [])
            T(m.get('-BinDir') == 'build\\agent2\\' + bin_, f'{rid} -BinDir {m.get("-BinDir")}')
            T(kv(m.get('-Cvar')) == cv, f'{rid} cvars = spec ({len(cv)} keys)')
            T(kv(m.get('-Env')) == env, f'{rid} env = spec {env}')
            T(int(m.get('-Seconds', 0)) == secs, f'{rid} -Seconds {m.get("-Seconds")}')
            T(m.get('-InputScript') == script if script else '-InputScript' not in m, f'{rid} input script {m.get("-InputScript")}')
            T(r.get('est', 0) >= secs + 30, f'{rid} est {r.get("est")} >= Seconds + 30')
            T(str(m.get('-Tag', '')).startswith(rid + '-'), f'{rid} tag {m.get("-Tag")}')
            T(not set(m) - {'-BinDir', '-Seconds', '-Tag', '-Cvar', '-Env', '-InputScript'}, f'{rid} no other switch {sorted(set(m))}')
            if '--dryrun' in argv:
                dryrun(r, SPEC[rid])
        if not opt:
            est += r.get('est', 0)
    check_route()
    check_final_gate()
    print(f'core rows est {est} s = {est / 60:.0f} min of queue time (optional rows +{sum(r["est"] for r in rows if SPEC.get(r["id"], (0,) * 8)[7])} s)')
    print(('ALL CHECKS PASS' if not bad_n else f'CHECKS FAILED: {bad_n}') + f' ({ok_n} ok)')
    return 0 if not bad_n else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
