"""check_queue_s33.py (M3, 11-25): checks the #33 rows 2, 4, 5, 6, (d) queue draft
(build/agent3/session3/s33-rows/queue-s33-rows.jsonl) before it is appended to build/agent3/s4b/queue.jsonl.
Read-only, except --dryrun: harness/run-game.ps1 -DryRun per row with -RunsRoot build/agent3/session3/s33-rows/dryrun
(bin mirror + toml + seed copy + input-script load; no game launch), then checks the run.json it writes.

Usage: python -B check_queue_s33.py [queue file] [--live build/agent3/s4b/queue.jsonl] [--dryrun]
Exit 0 = ALL CHECKS PASS, 1 = a check failed, 2 = usage / unreadable.
Spec: M6 build/agent6/s33-popin/TESTPLAN.md section 2 (rows 2, 4, 5, 6, (d)) and harness-s33.json (arm bins, cvars,
seconds); the draft s4b_check.py S33X table next to this file must agree with both.
"""
import hashlib, importlib.util, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
S3 = 'build\\agent3\\session3\\'
READY = 'build\\agent3\\s4b\\ready-s4b-off'
GO = S3 + 'go-s33r'
ROUTE = 'harness\\routes\\attract-long.txt'
SEED_RUN = '20261125-071741-s33-offsf'
SEED = 'build\\agent3\\runs\\' + SEED_RUN + '\\user\\cache\\shaders\\shareable'
# queue id -> (harness-s33.json arm, -Seconds, seeded)
SPEC = {'s33onsf': ('onsf', 540, False)}
for _i, _s in zip(range(1, 8), (203, 205, 207, 209, 211, 206, 210)):
    SPEC['s33stop%d' % _i] = ('onstop', _s, False)
SPEC.update({'s33offw': ('offwarm', 540, True), 's33onw': ('onwarm', 540, True),
             's33gthr0': ('gthr0', 300, False), 's33gasync': ('gasync', 300, False), 's33gbind': ('gbindful', 300, False),
             's33offd': ('offd', 540, False), 's33ond': ('ond', 540, False)})
ORDER = ['s33onsf'] + ['s33stop%d' % i for i in range(1, 8)] + ['s33offw', 's33onw', 's33gthr0', 's33gasync', 's33gbind',
                                                                 's33offd', 's33ond']
SPARE = {'s33stop6', 's33stop7'}
# TESTPLAN mode per arm: off = no no_wait text; on = INFO once; gate = one "ignored" WARN
MODE = {'onsf': 'on', 'onstop': 'on', 'offwarm': 'off', 'onwarm': 'on', 'gthr0': 'gate', 'gasync': 'gate',
        'gbindful': 'gate', 'offd': 'off', 'ond': 'on'}

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


def kv(s):
    out = {}
    for item in (s if isinstance(s, list) else (s or '').split(';')):
        if item.strip():
            k, _, v = item.partition('=')
            out[k.strip().lower()] = v.strip().lower()
    return out


def args_map(args):
    m, i = {}, 0
    while i < len(args):
        a = args[i]
        if a.startswith('-') and i + 1 < len(args) and not args[i + 1].startswith('-'):
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


def load_draft_check():
    sys.path.insert(0, os.path.join(REPO, 'build', 'agent3', 's4a'))
    spec = importlib.util.spec_from_file_location('s4b_check_draft', os.path.join(HERE, 's4b_check.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dryrun(row, arm):
    out = os.path.join(HERE, 'dryrun')
    os.makedirs(out, exist_ok=True)
    before = set(os.listdir(out))
    cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(REPO, 'harness', 'run-game.ps1')] + \
          [str(a) for a in row['args']] + ['-DryRun', '-RunsRoot', out]
    cp = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    new = sorted(set(os.listdir(out)) - before)
    if not T(cp.returncode == 0 and len(new) == 1, f'{row["id"]} run-game -DryRun exit {cp.returncode}, new dirs {new}'):
        print('       ' + (cp.stdout + cp.stderr).strip().replace('\n', '\n       ')[-800:])
        return None
    return json.load(open(os.path.join(out, new[0], 'run.json'), encoding='utf-8-sig'))


def main(argv):
    a = [x for x in argv[1:] if not x.startswith('--')]
    live = os.path.join(REPO, 'build', 'agent3', 's4b', 'queue.jsonl')
    if '--live' in argv:
        live = argv[argv.index('--live') + 1]
        a = [x for x in a if x != live]
    q = a[0] if a else os.path.join(HERE, 'queue-s33-rows.jsonl')
    if not os.path.isfile(q):
        print('no queue file', q)
        return 2
    print(f'# check_queue_s33 {q} (sha {sha(q)[:8]})')
    hs = json.load(open(os.path.join(REPO, 'build', 'agent6', 's33-popin', 'harness-s33.json'), encoding='utf-8-sig'))
    arms = {x['id']: x for x in hs['arms']}
    dc = load_draft_check()
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
    for m in [GO] + [S3 + 'go-' + i for i in ORDER]:
        T(not os.path.exists(os.path.join(REPO, m)), f'marker {m} absent before install')
    # seed source: the row 1b offsf run, static, both storage files
    sd = os.path.join(REPO, SEED)
    sf = sorted(f for f in os.listdir(sd) if f.endswith(('.xsh', '.xpso'))) if os.path.isdir(sd) else []
    T(len(sf) >= 1, f'seed dir {SEED} has storage files {sf}')
    T(dc.S33_SEED == SEED_RUN, f'draft s4b_check S33_SEED {dc.S33_SEED}')
    est = 0
    for r in rows:
        rid = r.get('id')
        if rid not in SPEC:
            T(False, f'{rid}: no spec')
            continue
        arm, secs, seeded = SPEC[rid]
        ha = arms[arm]
        want_bin = ha['bin'].replace('/', '\\')
        T(r.get('needs') == [READY, GO, S3 + 'go-' + rid], f'{rid} needs {r.get("needs")}')
        m = args_map(r.get('args') or [])
        T(m.get('-BinDir') == want_bin, f'{rid} -BinDir {m.get("-BinDir")} = arm {arm} bin')
        T(kv(m.get('-Cvar')) == kv(ha['cvars']), f'{rid} cvars = arm {arm} {ha["cvars"]}')
        hsec = ha['seconds']
        T(int(m.get('-Seconds', 0)) == secs and (secs in hsec if isinstance(hsec, list) else secs == hsec) or rid in SPARE,
          f'{rid} -Seconds {m.get("-Seconds")} (arm {arm}: {hsec}{"; spare" if rid in SPARE else ""})')
        T(m.get('-GpuLog') is True and m.get('-InputScript') == ROUTE, f'{rid} -GpuLog + {m.get("-InputScript")}')
        T((m.get('-SeedXenos') == SEED) if seeded else ('-SeedXenos' not in m), f'{rid} seed {m.get("-SeedXenos", "-")}')
        T(r.get('est', 0) >= secs + 30, f'{rid} est {r.get("est")} >= Seconds + 30')
        T(str(m.get('-Tag', '')).startswith('s33-'), f'{rid} tag {m.get("-Tag")}')
        T(not set(m) - {'-BinDir', '-Seconds', '-GpuLog', '-Tag', '-InputScript', '-Cvar', '-SeedXenos'}, f'{rid} no other switch')
        # the draft s4b_check must read this row the same way
        x = dc.S33X.get(rid) or {}
        T(x.get('mode') == MODE[arm], f'{rid} s4b_check mode {x.get("mode")} = TESTPLAN {MODE[arm]}')
        T(x.get('cvars') == kv(ha['cvars']), f'{rid} s4b_check cvars = arm cvars')
        T(bool(x.get('seed')) == seeded and bool(x.get('short')) == (secs < 540) and bool(x.get('diag')) == arm.endswith('d'),
          f'{rid} s4b_check seed/short/diag {bool(x.get("seed"))}/{bool(x.get("short"))}/{bool(x.get("diag"))}')
        pw = dc.POSTWIN.get(rid) or {}
        bdir = os.path.join(REPO, want_bin)
        T(pw.get('bin') == os.path.basename(want_bin), f'{rid} s4b_check POSTWIN bin {pw.get("bin")}')
        for fn, h in (pw.get('sha') or {}).items():
            T(sha(os.path.join(bdir, fn))[:16] == h, f'{rid} {os.path.basename(want_bin)}\\{fn} = {h}')
        if '--dryrun' in argv:
            rj = dryrun(r, arm)
            if rj:
                T(os.path.basename(rj['bin_dir'].rstrip('\\/')) == os.path.basename(want_bin), f'{rid} dry run.json bin_dir')
                T({str(k).lower(): str(v).lower() for k, v in (rj.get('cvars') or {}).items()} == kv(ha['cvars']), f'{rid} dry run.json cvars')
                sx = rj.get('seed_xenos') or {}
                src = os.path.normpath(str(sx.get('source_dir') or '')) if isinstance(sx, dict) else ''
                want = os.path.join(SEED_RUN, 'user', 'cache', 'shaders', 'shareable')
                T(src.lower().endswith(want.lower()) and len(sx.get('files') or []) == len(sf) if seeded else not sx,
                  f'{rid} dry run.json seed_xenos {src or "-"} ({len(sx.get("files") or []) if isinstance(sx, dict) else 0} files)')
                isr = rj.get('input_script') or {}
                T(isr.get('steps_total') and str(isr.get('script_sha256', '')).upper() == sha(os.path.join(REPO, ROUTE)),
                  f'{rid} dry input script {isr.get("steps_total")} steps')
        if rid not in SPARE:
            est += r.get('est', 0)
    print(f'core rows est {est} s = {est / 60:.0f} min of queue time (spares +{sum(r["est"] for r in rows if r["id"] in SPARE)} s)')
    print(('ALL CHECKS PASS' if not bad_n else f'CHECKS FAILED: {bad_n}') + f' ({ok_n} ok)')
    return 0 if not bad_n else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
