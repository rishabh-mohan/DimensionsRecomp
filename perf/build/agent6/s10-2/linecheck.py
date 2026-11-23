# Agent 6, task #8: read-only line check of the #32 patched pipeline_cache.cpp against live.
# usage: python linecheck.py <live> <snap> [--out file]
import difflib, hashlib, pathlib, sys

args = sys.argv[1:]
out_path = None
if '--out' in args:
    i = args.index('--out'); out_path = args[i + 1]; del args[i:i + 2]
live, snap = map(pathlib.Path, args[:2])
OLD, NEW = 'creation_thread_original_count', 'creation_thread_needed_count'
EXPECT_LINE = 564

out = []
def info(p):
    b = p.read_bytes()
    crlf = b.count(b'\r\n')
    return b, hashlib.sha256(b).hexdigest().upper(), len(b), crlf, b.count(b'\n') - crlf

lb, lh, ln, lcrlf, llf = info(live)
sb, sh, sn, scrlf, slf = info(snap)
out.append(f'live {live}: {ln} B  sha256 {lh}  CRLF {lcrlf}  bare LF {llf}')
out.append(f'snap {snap}: {sn} B  sha256 {sh}  CRLF {scrlf}  bare LF {slf}')
out.append(f'size delta snap-live = {sn - ln} B (expected {len(NEW) - len(OLD)})')
ll = lb.splitlines(keepends=True); sl = sb.splitlines(keepends=True)
out.append(f'lines: live {len(ll)}  snap {len(sl)}')

ops = [o for o in difflib.SequenceMatcher(a=ll, b=sl, autojunk=False).get_opcodes() if o[0] != 'equal']
out.append(f'differing hunks: {len(ops)}')
for tag, i1, i2, j1, j2 in ops:
    out.append(f'  {tag}: live L{i1 + 1}-{i2}  snap L{j1 + 1}-{j2}')
    for k in range(i1, i2): out.append(f'    - L{k + 1}: {ll[k]!r}')
    for k in range(j1, j2): out.append(f'    + L{k + 1}: {sl[k]!r}')

ok = False
if len(ops) == 1:
    tag, i1, i2, j1, j2 = ops[0]
    if tag == 'replace' and i2 - i1 == 1 and j2 - j1 == 1 and i1 == j1 == EXPECT_LINE - 1:
        a, b = ll[i1], sl[j1]
        o, n = OLD.encode(), NEW.encode()
        ok = a.count(o) == 1 and n not in a and a.replace(o, n) == b
ok = ok and (sn - ln) == len(NEW) - len(OLD) and (lcrlf, llf) == (scrlf, slf) or False
out.append('context (snap):')
for k in range(max(0, EXPECT_LINE - 4), min(len(sl), EXPECT_LINE + 3)):
    out.append(f'  {k + 1}: {sl[k].rstrip()}')
out.append(f'VERDICT: {"PASS" if ok else "FAIL"} - exactly one changed line at L{EXPECT_LINE}, {OLD} -> {NEW}, nothing else'
           if ok else 'VERDICT: FAIL - differences are not exactly the one expected line (see hunks above)')
text = '\n'.join(out)
print(text)
if out_path:
    pathlib.Path(out_path).write_text(text + '\n', encoding='utf-8')
