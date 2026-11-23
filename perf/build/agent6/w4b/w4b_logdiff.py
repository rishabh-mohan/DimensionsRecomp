#!/usr/bin/env python3
"""Agent 6, task #31: W4b game.log logdiff, every arm against d0. Read-only, stdlib only.

  python -B build/agent6/w4b/w4b_logdiff.py <matrix_dir> [--base RE] [--arm-regex RE] [--list] [--out DIR] [--top N]

Finds every dir under <matrix_dir> that holds game*.log (rotations included) and groups the runs by arm. The arm is
a path token like d0 or d11t, or group 1 of --arm-regex applied to the relative path. For every arm except the base
(default ^d0$), against the pooled base runs, it reports:
  - crash evidence per run: run.json exit code, close method, exited_early and wer; *.dmp files; the clean-exit line;
    STUCK lines; gate_logdiff.py FAIL findings (A = each base run, B = the arm run) and its notes;
  - NEW warnings: warning/error/critical keys in an arm run and in no base run;
    MORE: arm run count > base max + max(5, base max), Agent 10's logdiff rule;
    GONE: in every base run but missing from an arm run, any level;
  - Toypad lines: Read/Write counts and rate per minute, payload prefixes (first 3 bytes), any other Toypad line;
  - ONLY: messages at any level that the arm logs and no base run logs (the 'only d11t logs' list), with the other
    arms that also log them.
A key is '[level] [category] message', with absolute paths turned into <path> and then gate_logdiff.norm() applied
(hex, numbers, run dirs).
bench/agent8/run/gate_logdiff.py is imported read-only. sys.dont_write_bytecode is set, so no __pycache__ is written.
"""
import sys
sys.dont_write_bytecode = True
import argparse, datetime, glob, importlib.util, json, os, re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
_spec = importlib.util.spec_from_file_location('gate_logdiff', os.path.join(ROOT, 'bench', 'agent8', 'run', 'gate_logdiff.py'))
gl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gl)

PATH_RE = re.compile(r'[A-Za-z]:[\\/][^\s\'"<>|,;)\]]*')
TOY_RE = re.compile(r'Toypad\s*\[\s*([A-Za-z]+)\s*\]')
ARM_TOK = re.compile(r'(?i)^d\d+[a-z]*$')
EXIT_LINE = 'Title terminated; hard-exiting process'
WARN = ('warning', 'error', 'critical')
UNIMPL = re.compile(gl.UNIMPL_DEFAULT)


def find_runs(mdir):
    out = []
    for dp, dns, fns in os.walk(mdir):
        dns.sort()
        if any(gl.ROT_RE.match(f) for f in fns):
            out.append(dp)
    return out


def load_json(p):
    try:
        with open(p, encoding='utf-8-sig') as fh:
            return json.load(fh)
    except Exception as e:  # noqa: BLE001
        return {'_error': str(e)}


def arm_of(mdir, rd, arm_regex):
    rel = os.path.relpath(rd, mdir)
    if arm_regex:
        m = re.search(arm_regex, rel.replace('\\', '/'))
        return m.group(1).lower() if m else '?'
    srcs = [rel]
    rj = os.path.join(rd, 'run.json')
    if os.path.exists(rj):
        srcs.append(str(load_json(rj).get('tag') or ''))
    for src in srcs:
        for tok in re.split(r'[\\/_\-. ]+', src):
            if ARM_TOK.match(tok):
                return tok.lower()
    return rel.split(os.sep)[0]


def run_facts(rd):
    f = {}
    rj = os.path.join(rd, 'run.json')
    if os.path.exists(rj):
        d = load_json(rj)
        for k in ('tag', 'bin_dir', 'exit_code', 'exit_code_hex', 'close_method', 'exited_early', 'wer_seen',
                  'elapsed_s', 'mode', '_error'):
            if k in d:
                f[k] = d[k]
        for k, v in d.items():
            if k not in f and re.search(r'crash|dump|wer|hang|stuck|fault', k, re.I):
                f[k] = len(v) if isinstance(v, (list, dict)) else v
    else:
        f['run_json'] = 'missing'
    f['dumps'] = sorted(os.path.relpath(x, rd) for x in glob.glob(os.path.join(rd, '**', '*.dmp'), recursive=True))
    f['dir_files'] = sorted(os.listdir(rd))[:40]
    return f


def ts_s(ts):
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.datetime.strptime(ts, fmt).timestamp()
        except (ValueError, TypeError):
            pass
    return None


def key_of(lvl, cat, msg):
    return '[%s] [%s] %s' % (lvl, cat, gl.norm(PATH_RE.sub('<path>', msg)))


def scan_run(rd):
    r = dict(files=[], lines=0, levels=Counter(), keys=Counter(), ex={}, toy=Counter(), toy_prefix=Counter(),
             toy_other=Counter(), exit_line=0, stuck=0, first_ts=None, last_ts=None)
    for fp in gl.log_files(rd):
        r['files'].append((os.path.basename(fp), os.path.getsize(fp)))
        with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
            for raw in fh:
                line = raw.rstrip('\r\n')
                if not line:
                    continue
                r['lines'] += 1
                m = gl.LINE_RE.match(line)
                if m:
                    lvl, cat, msg = m.group('lvl'), m.group('cat'), m.group('msg')
                    r['first_ts'] = r['first_ts'] or m.group('ts')
                    r['last_ts'] = m.group('ts')
                else:
                    lvl, cat, msg = 'raw', '', line
                r['levels'][lvl] += 1
                if EXIT_LINE in msg:
                    r['exit_line'] += 1
                if 'STUCK' in msg:
                    r['stuck'] += 1
                t = TOY_RE.search(msg)
                if t:
                    kind = t.group(1).capitalize()
                    r['toy']['%s %s' % (lvl, kind)] += 1
                    r['toy_prefix']['%s %s' % (kind, ' '.join(msg[t.end():].split()[:3]))] += 1
                    continue
                k = key_of(lvl, cat, msg)
                if 'toypad' in msg.lower():
                    r['toy_other'][k] += 1
                    r['ex'].setdefault(k, line[:300])
                    continue
                r['keys'][k] += 1
                r['ex'].setdefault(k, line[:300])
    a, b = ts_s(r['first_ts']), ts_s(r['last_ts'])
    r['dur_s'] = (b - a) if (a is not None and b is not None) else None
    return r


def lvl_of(k):
    return k[1:k.index(']')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('matrix')
    ap.add_argument('--base', default=r'^d0$', help='regex for the base arm name(s), default ^d0$')
    ap.add_argument('--arm-regex', help='regex on the relative run path; group 1 is the arm name')
    ap.add_argument('--list', action='store_true', help='only list the run dirs and arms')
    ap.add_argument('--out', help='output dir (default build/agent6/w4b/out-<matrix name>)')
    ap.add_argument('--top', type=int, default=30)
    a = ap.parse_args()
    mdir = os.path.abspath(a.matrix)
    runs = find_runs(mdir)
    arms = defaultdict(list)
    for rd in runs:
        arms[arm_of(mdir, rd, a.arm_regex)].append(rd)
    rel = lambda rd: os.path.relpath(rd, mdir)  # noqa: E731
    head = ['matrix %s: %d run dirs with game*.log' % (mdir, len(runs))]
    for arm in sorted(arms):
        head.append('  %-8s %d: %s' % (arm, len(arms[arm]), ', '.join(rel(r) for r in arms[arm])))
    print('\n'.join(head))
    if a.list:
        return 0
    base_arms = sorted(x for x in arms if re.search(a.base, x))
    base_runs = [r for x in base_arms for r in arms[x]]
    if not base_runs:
        print('no base runs match --base %s' % a.base)
        return 2
    out_dir = a.out or os.path.join(HERE, 'out-' + os.path.basename(mdir.rstrip('\\/')))
    os.makedirs(out_dir, exist_ok=True)

    S = {rd: scan_run(rd) for rd in runs}
    F = {rd: run_facts(rd) for rd in runs}
    G = {}

    def gscan(rd):
        if rd not in G:
            G[rd] = gl.scan(rd, UNIMPL)
        return G[rd]

    key_arms = defaultdict(set)
    for arm, rs in arms.items():
        for rd in rs:
            for k in S[rd]['keys']:
                key_arms[k].add(arm)
            for k in S[rd]['toy_other']:
                key_arms[k].add(arm)

    def run_line(rd):
        s, f = S[rd], F[rd]
        toy_r = sum(v for k, v in s['toy'].items() if k.endswith('Read'))
        toy_w = sum(v for k, v in s['toy'].items() if k.endswith('Write'))
        per_min = ('%.1f/%.1f per min' % (toy_r * 60 / s['dur_s'], toy_w * 60 / s['dur_s'])) if s['dur_s'] else '-'
        return ('  %s: exit=%s close=%s early=%s wer=%s dumps=%s exit_line=%d stuck=%d | %d lines %s, %s..%s (%s s) '
                '| levels %s | Toypad R/W %d/%d (%s)%s' % (
                    rel(rd), f.get('exit_code', '?'), f.get('close_method', '?'), f.get('exited_early', '?'),
                    f.get('wer_seen', '?'), len(f['dumps']) if f['dumps'] else 0, s['exit_line'], s['stuck'],
                    s['lines'], '+'.join('%s %d' % fb for fb in s['files']), s['first_ts'], s['last_ts'],
                    ('%.0f' % s['dur_s']) if s['dur_s'] else '?',
                    ' '.join('%s=%d' % kv for kv in sorted(s['levels'].items())), toy_r, toy_w, per_min,
                    (' | DUMPS %s' % f['dumps']) if f['dumps'] else ''))

    bk = [S[b]['keys'] for b in base_runs]
    base_union = set().union(*[set(c) for c in bk])
    base_all = set.intersection(*[set(c) for c in bk])
    base_max = Counter()
    for c in bk:
        for k, v in c.items():
            base_max[k] = max(base_max[k], v)
    base_toy_other = set().union(*[set(S[b]['toy_other']) for b in base_runs])
    base_prefix = set().union(*[set(S[b]['toy_prefix']) for b in base_runs])

    summary = ['W4b game.log logdiff vs %s (Agent 6, task #31)' % '+'.join(base_arms)] + head + ['',
               'base runs:'] + [run_line(rd) for rd in base_runs]
    data = dict(matrix=mdir, base_arms=base_arms, arms={k: [rel(r) for r in v] for k, v in arms.items()},
                runs={rel(rd): dict(facts=F[rd], lines=S[rd]['lines'], levels=dict(S[rd]['levels']),
                                    exit_line=S[rd]['exit_line'], stuck=S[rd]['stuck'], toy=dict(S[rd]['toy']),
                                    dur_s=S[rd]['dur_s'], files=S[rd]['files']) for rd in runs}, per_arm={})
    for arm in sorted(arms):
        if arm in base_arms:
            continue
        rs = arms[arm]
        n = len(rs)
        new, more, gone, only = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
        for rd in rs:
            c = S[rd]['keys']
            for k, v in c.items():
                if k not in base_union:
                    only[k].append(v)
                    if lvl_of(k) in WARN:
                        new[k].append(v)
                elif lvl_of(k) in WARN and v > base_max[k] + max(5, base_max[k]):
                    more[k].append((v, base_max[k]))
            for k in base_all:
                if k not in c:
                    gone[k].append(rel(rd))
        ex = {}
        for rd in rs:
            for k, e in S[rd]['ex'].items():
                ex.setdefault(k, e)
        fails, notes = Counter(), Counter()
        for rd in rs:
            for b in base_runs:
                findings, nts, _match, _diff = gl.compare(gscan(b), gscan(rd), a.top)
                for x in findings:
                    fails['%s: %s' % (rel(rd), x.split('. First:')[0])] += 1
                for x in nts:
                    notes[x] += 1
        w = []
        w.append('== arm %s (%d runs) vs %s (%d runs)' % (arm, n, '+'.join(base_arms), len(base_runs)))
        w.extend(run_line(rd) for rd in rs)
        w.append('gate_logdiff FAIL findings (B = arm run, A = each base run): %s' % ('none' if not fails else ''))
        for x, c in sorted(fails.items()):
            w.append('  !!! %s   [vs %d of %d base runs]' % (x, c, len(base_runs)))
        for x, c in sorted(notes.items()):
            w.append('  note %s [%d]' % (x, c))
        w.append('NEW warning/error/critical keys (in an arm run, in no base run): %d' % len(new))
        for k, vs in sorted(new.items(), key=lambda kv: (-len(kv[1]), -sum(kv[1])))[:a.top]:
            w.append('  %d/%d runs, counts %s  %s\n      e.g. %s' % (len(vs), n, vs, k[:200], ex.get(k, '')[:240]))
        w.append('MORE (arm run count > base max + max(5, base max)): %d' % len(more))
        for k, vs in sorted(more.items(), key=lambda kv: -len(kv[1]))[:a.top]:
            w.append('  %d/%d runs, (arm, base max) %s  %s' % (len(vs), n, vs, k[:200]))
        w.append('GONE (in every base run, missing from an arm run; any level): %d' % len(gone))
        for k, rl in sorted(gone.items(), key=lambda kv: -len(kv[1]))[:a.top]:
            w.append('  missing in %d/%d runs  %s' % (len(rl), n, k[:200]))
        toy_lines = []
        for rd in rs:
            s = S[rd]
            np_ = sorted(set(s['toy_prefix']) - base_prefix)
            no_ = sorted(set(s['toy_other']) - base_toy_other)
            nonInfo = {k: v for k, v in s['toy'].items() if not k.startswith('info ')}
            toy_lines.append('  %s: %s; non-info Toypad %s; prefixes not in base %s; other Toypad lines not in base %s'
                             % (rel(rd), dict(s['toy']), nonInfo or '-', np_[:8] or '-', no_[:5] or '-'))
        w.append('Toypad (base: %s)' % '; '.join('%s %s' % (rel(b), dict(S[b]['toy'])) for b in base_runs))
        w.extend(toy_lines)
        w.append('ONLY in %s (any level, not Toypad; in no base run): %d keys' % (arm, len(only)))
        for k, vs in sorted(only.items(), key=lambda kv: (-len(kv[1]), -sum(kv[1])))[:a.top]:
            others = sorted(key_arms[k] - {arm} - set(base_arms))
            w.append('  %d/%d runs, counts %s, also in %s  %s\n      e.g. %s' % (
                len(vs), n, vs, others or '-', k[:200], ex.get(k, '')[:240]))
        txt = '\n'.join(w)
        with open(os.path.join(out_dir, 'report-%s.txt' % arm), 'w', encoding='utf-8') as fh:
            fh.write(txt + '\n')
        summary.append('')
        summary.append('%s: runs %d; FAIL findings %d; NEW %d; MORE %d; GONE %d; ONLY %d; dumps %d; exit lines %s; exits %s'
                       % (arm, n, len(fails), len(new), len(more), len(gone), len(only),
                          sum(len(F[rd]['dumps']) for rd in rs), [S[rd]['exit_line'] for rd in rs],
                          [F[rd].get('exit_code', '?') for rd in rs]))
        data['per_arm'][arm] = dict(
            fails=dict(fails), notes=dict(notes),
            new=[dict(key=k, counts=v, example=ex.get(k)) for k, v in new.items()],
            more=[dict(key=k, arm_vs_base_max=v) for k, v in more.items()],
            gone=[dict(key=k, missing_in=v) for k, v in gone.items()],
            only=[dict(key=k, counts=v, also_in=sorted(key_arms[k] - {arm} - set(base_arms)), example=ex.get(k))
                  for k, v in only.items()])
        print(txt)
        print()
    with open(os.path.join(out_dir, 'summary.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(summary) + '\n')
    with open(os.path.join(out_dir, 'data.json'), 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=1, default=str)
    print('\n'.join(summary))
    print('\nwrote %s' % out_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
