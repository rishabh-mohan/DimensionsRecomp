# Agent 11, task #25 pass B: read-only peek at the formal sources (07:16).
# Prints head lines + pattern hits for each source, and SESSION2's tail, to stdout (redirect to a file).
import re, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')

def lines_of(path):
    with open(path, 'rb') as f:
        b = f.read()
    if b.startswith(b'\xff\xfe') or b.startswith(b'\xfe\xff'):
        t = b.decode('utf-16')
    else:
        t = b.decode('utf-8', errors='replace')
    return re.split(r'\r\n|\n|\r', t)

def show(path, head, pats, maxhits=40, width=700):
    print('=' * 8, path)
    if not os.path.exists(path):
        print('MISSING'); return
    st = os.stat(path)
    L = lines_of(path)
    print('size', st.st_size, 'lines', len(L))
    for i in range(min(head, len(L))):
        print('H%d: %s' % (i + 1, L[i][:width]))
    n = 0
    for i, s in enumerate(L):
        if i < head:
            continue
        if any(re.search(p, s) for p in pats):
            print('M%d: %s' % (i + 1, s[:width]))
            n += 1
            if n >= maxhits:
                print('...more'); break

mode = sys.argv[1] if len(sys.argv) > 1 else 'src'
if mode == 'src':
    show('build/agent7/readout/W9.md', 40, [r'[Vv]erdict', r'q0\b', r'flag', r'burst', r'0\.72', r'[Pp]ass 2'], 30)
    show('build/agent7/readout/pool-W5b.md', 40, [r'[Vv]erdict', r'23\.17', r'1\.97', r'2\.08', r'best_perf', r'no-slow|without'], 30)
    show('build/agent7/readout/tail-check.md', 25, [r'16\.7', r'0221'], 15)
    show('build/agent7/readout/cluster-0221.txt', 45, [r'[Vv]erdict', r'[Cc]onclu'], 15)
    show('build/agent3/f10/RESULTS.md', 45, [r'n = 2|n=2', r'0/4|4/6|0\.07', r'5-30|5–30', r'[Ff]ollow'], 20)
    show('build/agent10/t27/f10-rating.md', 40, [r'WARN', r's4bLV', r'third'], 15)
elif mode == 's2':
    start = int(sys.argv[2])
    L = lines_of('perf-notes/SESSION2.md')
    print('SESSION2 lines', len(L))
    for i in range(start - 1, len(L)):
        print('%d: %s' % (i + 1, L[i][:1500]))
