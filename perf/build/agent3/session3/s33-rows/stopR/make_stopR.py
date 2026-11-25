"""make_stopR.py (M3, 11-25): builds the re-timed queue draft for #33 row 4 (option iii, Overseer 16:20Z).
Reads the live build/agent3/s4b/queue.jsonl and writes build/agent3/session3/s33-rows/stopR/queue.jsonl.stopR:
byte-identical except the held lines s33stop3..7, where only -Seconds, est (= S + 30) and note change.
Read-only on the live file. Usage: python -B make_stopR.py
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
LIVE = os.path.join(REPO, 'build', 'agent3', 's4b', 'queue.jsonl')
OUT = os.path.join(HERE, 'queue.jsonl.stopR')
# id -> re-timed -Seconds (STOPR.md: burst-locked replay, window [S-1.9, S+0.1] before the close line)
RETIME = {'s33stop3': 153, 's33stop4': 146, 's33stop5': 230, 's33stop6': 231, 's33stop7': 192}


def main():
    raw = open(LIVE, 'rb').read()
    lines = raw.split(b'\n')
    done = set()
    for n, ln in enumerate(lines):
        s = ln.decode('utf-8-sig').strip()
        if not s or s.startswith('#'):
            continue
        r = json.loads(s)
        rid = r.get('id')
        if rid not in RETIME:
            continue
        a = r['args']
        i = a.index('-Seconds')
        old = a[i + 1]
        a[i + 1] = str(RETIME[rid])
        r['est'] = RETIME[rid] + 30
        k = sorted(RETIME, key=lambda x: int(x[7:])).index(rid) + 1
        r['note'] = ('#33 row 4 onstop, re-timed run %d/5 (was -Seconds %s; STOPR.md, burst-locked). Gate go-%s. '
                     'Budget: stop after 3 counted or after 5 re-timed runs. Postcheck: s4b_check (short), '
                     'RUN-S33-LOGDIFF, s33_onstop.py (exit 3 = does not count, not a FAIL).' % (k, old, rid))
        cr = b'\r' if ln.endswith(b'\r') else b''
        lines[n] = json.dumps(r).encode('utf-8') + cr
        done.add(rid)
    if done != set(RETIME):
        print('missing ids in live queue:', sorted(set(RETIME) - done))
        return 1
    open(OUT, 'wb').write(b'\n'.join(lines))
    print('wrote', OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
