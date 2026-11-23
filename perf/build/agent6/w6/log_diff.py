# Read-only log analysis for W6 expected lines (agent6 helper). python -B log_diff.py > log-diff.txt
import os, re, json, sys
from collections import Counter, OrderedDict

R = 'build/agent3/runs/'
RUNS = OrderedDict([
    ('s4b01',   R + '20261122-205356-s4b-01-off'),
    ('s4bL0',   R + '20261122-210059-s4b-L0-off-level'),
    ('gateA',   R + '20261122-210906-w6-gateA-p2fcv-level'),
    ('side2',   R + '20261122-211914-w6-side2-p2fc'),
    ('side1',   R + '20261122-212406-w6-side1-p2f'),
    ('p2fiL',   R + '20261122-213421-s4b-23-w6-p2fi-level'),
    ('g3q_s0',  R + 'g3q-20261122-2128/runs/2129-s0-r1'),
    ('g3q_p2',  R + 'g3q-20261122-2128/runs/2130-p2-r1'),
    ('g3q_p2f', R + 'g3q-20261122-2128/runs/2131-p2f-r1'),
    ('g3q_p2fc', R + 'g3q-20261122-2128/runs/2132-p2fc-r1'),
])
DIFFS = [('gateA', 's4bL0'), ('p2fiL', 's4bL0'), ('side1', 's4b01'), ('side2', 's4b01'),
         ('side2', 'side1'), ('g3q_p2', 'g3q_s0'), ('g3q_p2f', 'g3q_s0'), ('g3q_p2fc', 'g3q_s0'),
         ('g3q_s0', 's4b01')]

LINE = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\] \[(\w+)\] \[(\w+)\] \[t\d+\] ?(.*)$')
PATH = re.compile(r'\\runs\\\S*\\')
TOY = re.compile(r'^(Toypad\[(?:Write|Read ?)\]) ((?:[0-9A-F]{2} ){0,3}[0-9A-F]{2})')
T_HEX0X = re.compile(r'0x[0-9A-Fa-f]+')
T_HEXMIX = re.compile(r'\b(?=[0-9A-Fa-f]*\d)(?=[0-9A-Fa-f]*[A-Fa-f])[0-9A-Fa-f]{3,}\b')
T_NUM = re.compile(r'(?<![A-Za-z])\d+(?:\.\d+)?')

RULES = [
    (r'C1 keep-watch:', 'a', 'C1 keep-watch (keep_watch+hold_global_lock)'),
    (r'C1 verify', 'b', 'physical_protect_keep_watch_verify'),
    (r'S4 upload hash:', 'b', 'shared_memory_upload_hash_log'),
    (r'slow frame #', 'b', 'slow_frame_log_ms'),
    (r'memexport flush reasons', 'b', 'slow_frame_log_ms'),
    (r'memexport', 'b?', 'memexport diag'),
    (r'Recovered stale physical page protection|Unhandled guest physical write fault|PhysicalHeap::Protect failed|BaseHeap::Protect', 'd', 'FORBIDDEN'),
    (r'STUCK-LOCK|hang dump|[Hh]ang-|minidump', 'd', 'STUCK-LOCK / hang (gate A)'),
    (r'Toypad|Portal', 'c', 'Toypad/route'),
    (r'NtCreateFile|INSTALL0_', 'c', 'file probes'),
    (r'[Ss]tub|STUB', 'c', 'stubs'),
    (r'Xam|XUser|[Pp]rofile|[Aa]chievement|XLive|Xnet|XNet', 'c', 'XAM/profile'),
    (r'[Hh]andle', 'c', 'handles'),
    (r'Window closing|Execution complete|Title terminated|hard-exiting|shutting down', 'c', 'shutdown'),
]
RULES = [(re.compile(a), b, c) for a, b, c in RULES]

COUNT_PATS = [
    'STUCK-LOCK', 'still not acquired after',
    'Recovered stale physical page protection', 'Unhandled guest physical write fault',
    'PhysicalHeap::Protect failed', 'BaseHeap::Protect',
    'C1 keep-watch:', 'C1 keep-watch: on (with physical_protect_hold_global_lock)',
    'C1 keep-watch: on, but blocked', 'C1 keep-watch: on, but physical_protect_hold_global_lock is off',
    'C1 keep-watch: first kept protect at', 'protects kept so far', 'C1 keep-watch: blocked for this process',
    'C1 verify:', 'C1 verify: on', 'C1 verify K:', 'C1 verify F:',
    'S4 upload hash:', 'slow frame #', 'memexport full-buffer', 'memexport flush reasons',
    'MISSING-FUNCTION', 'Reserving the guest memory arena', 'Title terminated',
]
KEPT = re.compile(r'C1 keep-watch: (\d+) protects kept so far')
FULLBUF = re.compile(r'memexport full-buffer (\d+)x \(total (\d+)\)')


def classify(t):
    for rx, c, lab in RULES:
        if rx.search(t):
            return c, lab
    return 'd?', 'unclassified'


def files_of(d):
    rot = []
    for f in os.listdir(d):
        m = re.match(r'^game\.(\d+)\.log$', f)
        if m:
            rot.append((int(m.group(1)), f))
    rot.sort(reverse=True)
    out = [os.path.join(d, f) for _, f in rot]
    if os.path.exists(os.path.join(d, 'game.log')):
        out.append(os.path.join(d, 'game.log'))
    return out


def norm(msg):
    msg = PATH.sub(r'\\runs\\<RUN>\\', msg.rstrip())
    m = TOY.match(msg)
    if m:
        return m.group(1) + ' ' + m.group(2), True
    return msg, False


def templ(key):
    t = T_HEX0X.sub('#', key)
    t = T_HEXMIX.sub('#', t)
    t = T_NUM.sub('#', t)
    return t


def scan(name, d):
    st = OrderedDict()
    exact = Counter(); tmpl = Counter(); example = {}
    levels = Counter(); counts = Counter()
    files = files_of(d)
    st['files'] = [os.path.basename(f) + ':' + str(os.path.getsize(f)) for f in files]
    first_ts = last_ts = None
    n = 0; idx = 0; c1init_idx = reserve_idx = None; kept_max = 0; fb_total = 0; fb_lines_nonzero = 0
    first_kept_ts = None; first_line = None
    for fp in files:
        with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
            for raw in fh:
                raw = raw.rstrip('\r\n')
                if not raw.strip():
                    continue
                n += 1
                if first_line is None:
                    first_line = raw[:140]
                m = LINE.match(raw)
                if m:
                    ts, lvl, cat, msg = m.groups()
                    if first_ts is None:
                        first_ts = ts
                    last_ts = ts
                    levels[lvl] += 1
                    msg_n, toy = norm(msg)
                    key = '[%s] [%s] %s' % (lvl, cat, msg_n)
                    tk = key if toy else templ(key)
                else:
                    msg = raw
                    key = '(cont) ' + raw.rstrip()
                    tk = templ(key)
                exact[key] += 1
                tmpl[tk] += 1
                if tk not in example:
                    example[tk] = key[:300]
                for p in COUNT_PATS:
                    if p in msg:
                        counts[p] += 1
                if 'C1 keep-watch: on' in msg and c1init_idx is None:
                    c1init_idx = n
                if 'Reserving the guest memory arena' in msg and reserve_idx is None:
                    reserve_idx = n
                if 'first kept protect at' in msg and first_kept_ts is None:
                    first_kept_ts = m.group(1) if m else '?'
                km = KEPT.search(msg)
                if km:
                    kept_max = max(kept_max, int(km.group(1)))
                fm = FULLBUF.search(msg)
                if fm:
                    fb_total = max(fb_total, int(fm.group(2)))
                    if int(fm.group(1)):
                        fb_lines_nonzero += 1
    st['lines'] = n; st['first_line'] = first_line; st['first_ts'] = first_ts; st['last_ts'] = last_ts
    st['levels'] = dict(levels); st['counts'] = dict((p, counts[p]) for p in COUNT_PATS)
    st['c1init_line'] = c1init_idx; st['reserve_line'] = reserve_idx; st['first_kept_ts'] = first_kept_ts
    st['kept_max'] = kept_max; st['fullbuf_total_max'] = fb_total; st['fullbuf_lines_nonzero'] = fb_lines_nonzero
    st['distinct_exact'] = len(exact); st['distinct_tmpl'] = len(tmpl)
    return st, exact, tmpl, example


def runinfo(d):
    p = os.path.join(d, 'run.json')
    if not os.path.exists(p):
        return 'no run.json'
    try:
        j = json.load(open(p, 'r', encoding='utf-8-sig'))
    except Exception as e:
        return 'run.json error %s' % e
    out = []
    for k, v in j.items():
        if re.search(r'cvar|input|route|status|result|halt|exit|bin', k, re.I):
            s = json.dumps(v)
            out.append('%s=%s' % (k, s[:300]))
    return '; '.join(out)


def main():
    data = {}
    for name, d in RUNS.items():
        if not os.path.isdir(d):
            print('== %s MISSING %s' % (name, d)); continue
        st, exact, tmpl, ex = scan(name, d)
        data[name] = (st, exact, tmpl, ex)
        print('== RUN %s  %s' % (name, d))
        print('   runinfo:', runinfo(d))
        for k, v in st.items():
            print('   %s: %s' % (k, v))
        sys.stdout.flush()
    for a, b in DIFFS:
        if a not in data or b not in data:
            continue
        ta, tb = data[a][2], data[b][2]
        exa, exb = data[a][3], data[b][3]
        print('\n== DIFF %s (run) vs %s (base): templates whose count differs' % (a, b))
        rows = []
        for t in set(ta) | set(tb):
            ca, cb = ta.get(t, 0), tb.get(t, 0)
            if ca != cb:
                c, lab = classify(t)
                tag = 'NEW' if cb == 0 else ('GONE' if ca == 0 else 'CNT')
                rows.append((c, tag, lab, cb, ca, t, exa.get(t) or exb.get(t)))
        rows.sort(key=lambda r: (r[0], r[2], r[1], r[5]))
        byc = Counter(r[0] for r in rows)
        print('   classes:', dict(byc))
        for c, tag, lab, cb, ca, t, e in rows:
            print('   (%s) %-4s %6d -> %-6d [%s] %s' % (c, tag, cb, ca, lab, t[:220]))
            if e != t:
                print('                  e.g. %s' % (e or '')[:220])
        sys.stdout.flush()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.stdout = open(sys.argv[1], 'w', encoding='utf-8')
    main()
    sys.stdout.flush()
