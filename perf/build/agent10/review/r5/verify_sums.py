#!/usr/bin/env python3
"""verify_sums.py <tree> : check <tree>/SHA256SUMS.txt against the files in <tree> (one thread)."""
import hashlib, os, sys

root = sys.argv[1]
sums = os.path.join(root, 'SHA256SUMS.txt')
listed = {}
with open(sums, 'r', encoding='utf-8-sig') as f:
    for line in f:
        line = line.rstrip('\r\n')
        if not line.strip():
            continue
        h, rest = line.split(None, 1)
        rest = rest.lstrip('*').strip()
        listed[os.path.normpath(rest)] = h.lower()
bad, missing = [], []
total = 0
for rel, h in listed.items():
    p = os.path.join(root, rel)
    if not os.path.isfile(p):
        missing.append(rel)
        continue
    d = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            d.update(chunk)
    total += os.path.getsize(p)
    if d.hexdigest() != h:
        bad.append(rel)
on_disk = set()
for dp, dn, fn in os.walk(root):
    for n in fn:
        on_disk.add(os.path.normpath(os.path.relpath(os.path.join(dp, n), root)))
unlisted = sorted(on_disk - set(listed) - {'SHA256SUMS.txt'})
print(f'{root}: listed {len(listed)}, hashed {len(listed) - len(missing)} files / {total} B, '
      f'mismatches {len(bad)}, missing {len(missing)}, on disk {len(on_disk)}, unlisted {len(unlisted)}')
for x in bad[:10]:
    print('  MISMATCH', x)
for x in missing[:10]:
    print('  MISSING', x)
for x in unlisted[:10]:
    print('  UNLISTED', x)
sys.exit(1 if bad or missing else 0)
