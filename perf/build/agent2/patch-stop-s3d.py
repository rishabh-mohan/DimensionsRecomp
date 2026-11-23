"""Agent 2 - add run-s3d.ps1 to stop-snap.ps1's driver list (backup stop-snap.ps1.pre-S3d; refuses if it exists).
  python build\\agent2\\patch-stop-s3d.py
"""
import difflib
import hashlib
import os

A = os.path.dirname(os.path.abspath(__file__))
NAME = 'stop-snap.ps1'
EDITS = [
    (r"""#    driver and run-s3.ps1.)
""",
     r"""#    driver and run-s3.ps1; 02:59: run-s3d.ps1, the native3d driver.)
"""),
    (r"""$drivers = 'build-snap\.ps1|run-s2\.ps1|run-s3\.ps1|run-b\.ps1|prep-b\.py|b-chain\.ps1'
""",
     r"""$drivers = 'build-snap\.ps1|run-s2\.ps1|run-s3\.ps1|run-s3d\.ps1|run-b\.ps1|prep-b\.py|b-chain\.ps1'
"""),
]


def main():
    path = os.path.join(A, NAME)
    backup = path + '.pre-S3d'
    if os.path.exists(backup):
        raise SystemExit('%s exists: already patched? nothing written' % backup)
    raw = open(path, 'rb').read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    body = raw[3:] if bom else raw
    crlf = b'\r\n' in body
    if crlf and body.count(b'\r\n') != body.count(b'\n'):
        raise SystemExit('%s has mixed line endings; nothing written' % NAME)
    old = body.decode('utf-8').replace('\r\n', '\n')
    new = old
    for i, (s, r) in enumerate(EDITS):
        n = new.count(s)
        if n != 1:
            raise SystemExit('edit %d: search text found %d times in %s (want 1); nothing written' % (i, n, NAME))
        new = new.replace(s, r)
    out = new.replace('\n', '\r\n') if crlf else new
    out = (b'\xef\xbb\xbf' if bom else b'') + out.encode('utf-8')
    with open(backup, 'wb') as f:
        f.write(raw)
    if open(backup, 'rb').read() != raw:
        raise SystemExit('backup readback mismatch; %s left unchanged' % NAME)
    tmp = path + '.new'
    with open(tmp, 'wb') as f:
        f.write(out)
    os.replace(tmp, path)
    ddir = os.path.join(A, 'S3d-diffs')
    os.makedirs(ddir, exist_ok=True)
    diff = ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), NAME + '.pre-S3d', NAME, n=1))
    dpath = os.path.join(ddir, NAME + '.S3d.diff')
    with open(dpath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(diff)
    sha = lambda b: hashlib.sha256(b).hexdigest().upper()[:16]
    print('patched %s: %d edits | %s -> %s | backup %s | diff %s (sha256 %s) | %s, %s' % (
        NAME, len(EDITS), sha(raw), sha(open(path, 'rb').read()), os.path.basename(backup), os.path.basename(dpath),
        sha(open(dpath, 'rb').read()), 'CRLF' if crlf else 'LF', 'BOM' if bom else 'no BOM'))


if __name__ == '__main__':
    main()
