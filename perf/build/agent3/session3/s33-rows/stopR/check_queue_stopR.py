"""check_queue_stopR.py (M3, 11-25): checks the re-timed #33 row 4 queue draft (stopR/queue.jsonl.stopR) against the
live build/agent3/s4b/queue.jsonl before it replaces it. The installed check_queue_s33.py is not used for this (its
SPEC pins the old 203..211 seconds). Read-only, except --dryrun: harness/run-game.ps1 -DryRun per re-timed row with
-RunsRoot stopR/dryrun (no game launch), then checks the run.json it writes.

Usage: python -B check_queue_stopR.py [--dryrun] [--installed]
  --installed: after install the live file must equal the draft, and queue.jsonl.bak-stopR must be the old live file.
Exit 0 = ALL CHECKS PASS, 1 = a check failed, 2 = usage / unreadable.
"""
import hashlib, importlib.util, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
S4B = os.path.join(REPO, 'build', 'agent3', 's4b')
LIVE = os.path.join(S4B, 'queue.jsonl')
BAK = os.path.join(S4B, 'queue.jsonl.bak-stopR')
DRAFT = os.path.join(HERE, 'queue.jsonl.stopR')
S3 = 'build\\agent3\\session3\\'
RETIME = {'s33stop3': 153, 's33stop4': 146, 's33stop5': 230, 's33stop6': 231, 's33stop7': 192}
PIN_LIVE_QUEUE = '69C77DA7'   # live queue.jsonl at the #33 install (09:58), before stopR
PIN_CHECK = '3DDF1A55'        # live s4b_check.py (#33 install)
PIN_POST = '36DC0E05'         # live postcheck.ps1 (#33 install)
ON = {'slow_frame_log_ms': '1', 'd3d12_pipeline_creation_no_wait': 'true'}
ROUTE = 'harness\\routes\\attract-long.txt'

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


def jl(path):
    out = {}
    for ln in open(path, encoding='utf-8-sig'):
        s = ln.strip()
        if s and not s.startswith('#'):
            r = json.loads(s)
            out.setdefault(r.get('id'), r)
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


def kv(s):
    return {k.strip().lower(): v.strip().lower() for k, _, v in (x.partition('=') for x in (s or '').split(';')) if k.strip()}


def main(argv):
    installed = '--installed' in argv
    old_path = BAK if installed else LIVE
    for p in (old_path, DRAFT):
        if not os.path.isfile(p):
            print('missing', p)
            return 2
    print('# check_queue_stopR: draft %s (sha %s), old %s (sha %s)' % (
        os.path.basename(DRAFT), sha(DRAFT)[:8], os.path.relpath(old_path, REPO), sha(old_path)[:8]))
    T(sha(old_path)[:8] == PIN_LIVE_QUEUE, 'old queue = the #33-install live queue %s' % PIN_LIVE_QUEUE)
    if installed:
        T(sha(LIVE) == sha(DRAFT), 'live queue.jsonl = draft (installed)')
    T(sha(os.path.join(S4B, 's4b_check.py'))[:8] == PIN_CHECK, 'live s4b_check.py %s' % PIN_CHECK)
    T(sha(os.path.join(S4B, 'postcheck.ps1'))[:8] == PIN_POST, 'live postcheck.ps1 %s' % PIN_POST)
    old_raw = open(old_path, 'rb').read().split(b'\n')
    new_raw = open(DRAFT, 'rb').read().split(b'\n')
    T(len(old_raw) == len(new_raw), 'same line count %d / %d' % (len(old_raw), len(new_raw)))
    changed = [n for n, (a, b) in enumerate(zip(old_raw, new_raw)) if a != b]
    ids = []
    for n in changed:
        try:
            ids.append(json.loads(new_raw[n].decode('utf-8-sig')).get('id'))
        except ValueError:
            ids.append('?line%d' % (n + 1))
    T(sorted(ids) == sorted(RETIME), 'only the s33stop3..7 lines differ (lines %s: %s)' % ([n + 1 for n in changed], ids))
    T(all(old_raw[n].endswith(b'\r') == new_raw[n].endswith(b'\r') for n in changed), 'line endings kept')
    old, new = jl(old_path), jl(DRAFT)
    for rid, S in RETIME.items():
        o, r = old.get(rid) or {}, new.get(rid) or {}
        T(r.get('needs') == o.get('needs') == ['build\\agent3\\s4b\\ready-s4b-off', S3 + 'go-s33r', S3 + 'go-' + rid],
          '%s needs unchanged %s' % (rid, r.get('needs')))
        mo, mn = args_map(o.get('args') or []), args_map(r.get('args') or [])
        T(mn.get('-Seconds') == str(S), '%s -Seconds %s (was %s)' % (rid, mn.get('-Seconds'), mo.get('-Seconds')))
        T({k: v for k, v in mn.items() if k != '-Seconds'} == {k: v for k, v in mo.items() if k != '-Seconds'},
          '%s every other arg identical' % rid)
        T(len(r.get('args') or []) == len(o.get('args') or []), '%s arg count %d' % (rid, len(r.get('args') or [])))
        T(set(r) == set(o) and all(r[k] == o[k] for k in r if k not in ('args', 'est', 'note')),
          '%s no other field changed' % rid)
        T(r.get('est') == S + 30, '%s est %s = S + 30' % (rid, r.get('est')))
        T(mn.get('-BinDir') == 'build\\agent2\\devoff4b-s33-bin' and kv(mn.get('-Cvar')) == ON and
          mn.get('-InputScript') == ROUTE and mn.get('-GpuLog') is True and '-SeedXenos' not in mn,
          '%s onstop arm (devoff4b-s33-bin, no_wait=true, sf=1, attract-long, cold)' % rid)
        T(not os.path.exists(os.path.join(REPO, S3 + 'go-' + rid)), '%s marker go-%s absent' % (rid, rid))
    st = os.path.join(S4B, 'queue-state.jsonl')
    done = set()
    if os.path.isfile(st):
        for ln in open(st, encoding='utf-8-sig'):
            if ln.strip():
                x = json.loads(ln)
                if not x.get('aborted'):
                    done.add(x.get('id'))
    T(not (set(RETIME) & done), 'no re-timed id in queue-state (would count as done) %s' % sorted(set(RETIME) & done))
    T({'s33stop1', 's33stop2'} <= done, 's33stop1/2 recorded in queue-state (they stay exit 3)')
    # the live tools route these ids with no code change (option iii)
    pc = open(os.path.join(S4B, 'postcheck.ps1'), encoding='utf-8-sig').read()
    rx = re.findall(r"'\^s33stop\\d\$'", pc)
    T(len(rx) == 1 and all(re.match(r'^s33stop\d$', i) for i in RETIME), 'postcheck row-4 case ^s33stop\\d$ covers the ids')
    T(re.search(r"\^\(s33onsf\|s33stop\\d\|", pc) is not None, 'postcheck Check case covers s33stop\\d (allow-new $S33ON)')
    sys.path.insert(0, os.path.join(REPO, 'build', 'agent3', 's4a'))
    spec = importlib.util.spec_from_file_location('s4b_check_live', os.path.join(S4B, 's4b_check.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for rid in RETIME:
        x = mod.S33X.get(rid) or {}
        T(x.get('mode') == 'on' and x.get('cvars') == ON and x.get('short') is True and not x.get('seed'),
          '%s live s4b_check S33X mode on / short / cold' % rid)
        T((mod.POSTWIN.get(rid) or {}).get('bin') == 'devoff4b-s33-bin', '%s live POSTWIN bin devoff4b-s33-bin' % rid)
    if '--dryrun' in argv:
        out = os.path.join(HERE, 'dryrun')
        os.makedirs(out, exist_ok=True)
        for rid, S in RETIME.items():
            before = set(os.listdir(out))
            cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                   os.path.join(REPO, 'harness', 'run-game.ps1')] + [str(a) for a in new[rid]['args']] + \
                  ['-DryRun', '-RunsRoot', out]
            cp = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
            nd = sorted(set(os.listdir(out)) - before)
            if not T(cp.returncode == 0 and len(nd) == 1, '%s run-game -DryRun exit %d, new dirs %s' % (rid, cp.returncode, nd)):
                print('       ' + (cp.stdout + cp.stderr).strip()[-800:])
                continue
            rj = json.load(open(os.path.join(out, nd[0], 'run.json'), encoding='utf-8-sig'))
            # run-game's DryRun run.json (line 208) has no seconds field; exit 0 means -Seconds bound to [int].
            sv = str(args_map(new[rid]['args']).get('-Seconds'))
            T('seconds_requested' not in rj and re.fullmatch(r'\d+', sv) is not None and int(sv) == S,
              '%s dry -Seconds %s bound to [int] (DryRun run.json records no seconds)' % (rid, sv))
            T(os.path.basename(str(rj.get('bin_dir', '')).rstrip('\\/')) == 'devoff4b-s33-bin', '%s dry bin_dir' % rid)
            T({str(k).lower(): str(v).lower() for k, v in (rj.get('cvars') or {}).items()} == ON, '%s dry cvars' % rid)
            T(not rj.get('seed_xenos'), '%s dry cold (no seed_xenos)' % rid)
            isr = rj.get('input_script') or {}
            T(isr.get('steps_total') and str(isr.get('script_sha256', '')).upper() == sha(os.path.join(REPO, ROUTE)),
              '%s dry input script %s steps' % (rid, isr.get('steps_total')))
    print(('ALL CHECKS PASS' if not bad_n else 'CHECKS FAILED: %d' % bad_n) + ' (%d ok)' % ok_n)
    return 0 if not bad_n else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
