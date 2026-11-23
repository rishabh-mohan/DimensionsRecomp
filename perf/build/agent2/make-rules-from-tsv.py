"""Agent 2: write a snap-patch.py rules file from an include TSV in Agent 10's format (build/agent10/b3/S2-include.tsv).
TSV columns: action, rel, live_sha256, s1_sha256, live_mtime, owner, item, verdict_at_default; action INCLUDE or EXCLUDE.
  INCLUDE -> '<owner> | <rel> | <live sha256>'  (the plan stops if the live file no longer has the reviewed hash)
  EXCLUDE -> '!<owner> | <rel>'                 (keeps the snap1 version; the plan lists it as HELD BACK 'excluded')
Run:  python build\\agent2\\make-rules-from-tsv.py <tsv> <expected tsv sha256 prefix> <out rules file>
"""
import hashlib
import sys
import time

src, want, dst = sys.argv[1], sys.argv[2].lower(), sys.argv[3]
with open(src, 'rb') as f:
    raw = f.read()
h = hashlib.sha256(raw).hexdigest()
if not h.startswith(want):
    raise SystemExit('%s has sha256 %s, not %s...; stopping' % (src, h, want))
inc, exc, head = [], [], []
for ln in raw.decode('utf-8-sig').splitlines():
    if not ln.strip():
        continue
    if ln.startswith('#'):
        head.append(ln)
        continue
    c = ln.split('\t')
    if c[0] == 'action':
        continue
    if len(c) < 8 or c[0] not in ('INCLUDE', 'EXCLUDE'):
        raise SystemExit('unexpected row: %r' % ln)
    (inc if c[0] == 'INCLUDE' else exc).append([x.strip() for x in c])
out = ['# snap-patch.py rules generated %s by build/agent2/make-rules-from-tsv.py' % time.strftime('%Y-%m-%d %H:%M:%S'),
       '# source: %s (sha256 %s)' % (src, h)]
out += ['#   ' + x for x in head]
out.append('# INCLUDE (%d): the live file must still have the reviewed sha256' % len(inc))
for c in inc:
    rel, live, s1, mt, owner, item, verdict = c[1:8]
    if len(live) != 64:
        raise SystemExit('INCLUDE row without a full live sha256: %r' % rel)
    out.append('# %s; S1 %s; live mtime %s; %s' % (item, s1[:16], mt, verdict))
    out.append('%s | %s | %s' % (owner.replace('|', '/'), rel, live.lower()))
out.append('# EXCLUDE (%d): keep the snap1 (S1) version' % len(exc))
for c in exc:
    rel, owner = c[1], c[5]
    out.append('!%s | %s' % (owner.replace('|', '/'), rel))
with open(dst, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(out) + '\n')
print('wrote %s: %d include, %d exclude rules (tsv sha256 %s)' % (dst, len(inc), len(exc), h[:16]))
