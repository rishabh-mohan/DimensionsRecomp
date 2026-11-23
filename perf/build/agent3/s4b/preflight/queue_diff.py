"""Preflight: compare build/agent3/s4b/queue.jsonl with Agent 7's queue-s4b.jsonl and QUEUE.md table (read only)."""
import json
import os
import re
import sys

R = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
A3 = os.path.join(R, 'build', 'agent3', 's4b', 'queue.jsonl')
A7 = os.path.join(R, 'build', 'agent7', 's4b-queue', 'queue-s4b.jsonl')
QMD = os.path.join(R, 'build', 'agent7', 's4b-queue', 'QUEUE.md')
BINS = {'<S4B-OFF>': r'build\agent2\devoff4b-bin', '<S4B-NAT>': r'build\agent2\native4b-bin',
        '<S4B-CTR>': r'build\agent2\devoff4b-ctr-bin', '<S4B-CG26>': r'build\agent2\devoff4b-cg26-bin'}
SCN = {'M': {'-Seconds': '420', '-InputScript': r'harness\routes\b-gate-menus-long.txt'},
       'A': {'-Seconds': '420', '-StatsWarmup': '20', '-InputScript': r'harness\routes\attract-long.txt'},
       'B90': {'-Seconds': '90'},
       'T180': {'-Seconds': '180', '-StatsWarmup': '20'}}
EST = {'M': 265, 'A': 440, 'B90': 115, 'T180': 205}


def load(p):
    rows = {}
    with open(p, encoding='utf-8') as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith('#'):
                continue
            j = json.loads(ln)
            nd = j.get('needs') or []
            if isinstance(nd, str):
                nd = [nd]
            j['needs'] = nd
            rows[j['id']] = j
    return rows


def argmap(args):
    d, i = {}, 0
    while i < len(args):
        k = args[i]
        v = args[i + 1] if i + 1 < len(args) and not str(args[i + 1]).startswith('-') else None
        d[k] = v
        i += 2 if v is not None else 1
    return d


def sub(v):
    return BINS.get(v, v)


def main():
    a3, a7 = load(A3), load(A7)
    out = []
    say = out.append
    say('ids only in A3: %s' % (sorted(set(a3) - set(a7)) or '-'))
    say('ids only in A7: %s' % (sorted(set(a7) - set(a3)) or '-'))
    for rid in sorted(set(a3) & set(a7)):
        x, y = a3[rid], a7[rid]
        ya = [sub(v) for v in y['args']]
        d = []
        if x['est'] != y['est']:
            d.append('est %s vs %s' % (x['est'], y['est']))
        if x['args'] != ya:
            d.append('args A3 %s vs A7 %s' % (x['args'], ya))
        if sorted(x['needs']) != sorted(y['needs']):
            extra = [os.path.basename(n) for n in x['needs'] if n not in y['needs']]
            miss = [os.path.basename(n) for n in y['needs'] if n not in x['needs']]
            d.append('needs: A3 adds %s%s' % (extra or '-', ('; A3 lacks %s' % miss) if miss else ''))
        say('%s: %s' % (rid, '; '.join(d) if d else 'identical (placeholders substituted)'))
    # QUEUE.md table cross-check
    say('--- QUEUE.md table vs A3 queue.jsonl')
    md = {}
    with open(QMD, encoding='utf-8') as f:
        for ln in f:
            m = re.match(r'^\| (\d+) \| (.*)$', ln.rstrip('\n'))
            if not m:
                continue
            cols = [c.strip() for c in ln.strip().strip('|').split('|')]
            md[int(cols[0])] = cols
    for num in sorted(md):
        cols = md[num]
        rid = 's4b%02d' % num
        binph = re.search(r'`(<S4B-[A-Z0-9]+>)`', cols[2])
        scn = re.match(r'(M|A|B90|T180|L)\b', cols[4])
        cv = cols[3]
        env = re.findall(r'-Env (\S+?)`?(?:\s|$)', cv.replace('`', ' '))
        cvars = []
        m_as = re.match(r'as row (\d+)(?:, plus `([^`]*)`)?', cv)
        if m_as:
            base = md[int(m_as.group(1))][3]
            cvars = [c for c in re.findall(r'`([^`]*)`', base) if not c.startswith('-Env')]
            if m_as.group(2):
                cvars.append(m_as.group(2))
        elif not cv.startswith('none') and not cv.startswith('row '):
            cvars = [c for c in re.findall(r'`([^`]*)`', cv) if not c.startswith('-Env')]
        cvset = set(i for c in cvars for i in c.split(';') if i)
        desc = 'bin %s scn %s cvars %s env %s' % (binph.group(1) if binph else '?', scn.group(1) if scn else '?',
                                                  ';'.join(sorted(cvset)) or '-', ';'.join(env) or '-')
        if rid not in a3:
            say('%s: NOT IN A3 queue (%s; user %s)' % (rid, desc, cols[7] if len(cols) > 7 else '?'))
            continue
        am = argmap(a3[rid]['args'])
        d = []
        if binph and am.get('-BinDir') != BINS.get(binph.group(1)):
            d.append('bin %s vs %s' % (am.get('-BinDir'), binph.group(1)))
        if scn and scn.group(1) in SCN:
            want = SCN[scn.group(1)]
            for k in ('-Seconds', '-StatsWarmup', '-InputScript'):
                if am.get(k) != want.get(k):
                    d.append('%s %s vs %s' % (k, am.get(k), want.get(k)))
            if a3[rid]['est'] != EST[scn.group(1)]:
                d.append('est %s vs %s' % (a3[rid]['est'], EST[scn.group(1)]))
        got_cv = set(i for i in (am.get('-Cvar') or '').split(';') if i)
        if got_cv != cvset:
            d.append('cvars A3 %s vs MD %s' % (sorted(got_cv), sorted(cvset)))
        got_env = set(i for i in (am.get('-Env') or '').split(';') if i)
        want_env = set(i for e in env for i in e.split(';') if i)
        if got_env != want_env:
            d.append('env A3 %s vs MD %s' % (sorted(got_env), sorted(want_env)))
        say('%s: %s' % (rid, '; '.join(d) if d else 'matches QUEUE.md (%s)' % desc))
    print('\n'.join(out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
