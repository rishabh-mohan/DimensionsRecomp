"""Agent 10 (task #9): check the full-content scan against the fast scan and the sent S3 TSV. Read-only.
Usage: python build\\agent10\\s3\\cmp-full.py <full scan> <fast scan> <tsv>"""
import re
import sys

full_p, fast_p, tsv_p = sys.argv[1:4]


def changed(p):
    out = []
    for ln in open(p, encoding='utf-8', errors='replace'):
        if ln.startswith('CHANGED'):
            out.append(ln.rstrip('\r\n').replace('\\', '/'))
    return out


full, fast = changed(full_p), changed(fast_p)
rows = [l.rstrip('\n').split('\t') for l in open(tsv_p, encoding='ascii') if l.strip() and not l.startswith('#')][1:]
print('full CHANGED %d, fast CHANGED %d, line sets equal: %s' % (len(full), len(fast), sorted(full) == sorted(fast)))
print('first full line: %s' % full[0][:260])
ok = 0
for r in rows:
    rel, live = r[1], r[2].lower()
    hit = [l for l in full if re.search(r'(^|\s|/)' + re.escape(rel) + r'(\s|$)', l)]
    sha_ok = [l for l in hit if live in l.lower()]
    if len(hit) == 1 and len(sha_ok) == 1:
        ok += 1
    else:
        print('MISMATCH %s path hits %d, sha hits %d' % (rel, len(hit), len(sha_ok)))
print('TSV rows found with the same live sha in the full scan: %d of %d' % (ok, len(rows)))
extra = [l for l in full if not any(re.search(r'(^|\s|/)' + re.escape(r[1]) + r'(\s|$)', l) for r in rows)]
print('full-scan CHANGED rows not in the TSV: %d' % len(extra))
for l in extra:
    print('  ' + l[:260])
