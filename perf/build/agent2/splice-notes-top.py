"""Agent 2: replace the RESUME block at the top of perf-notes/agent2-baseline.md with a new top file.

usage: python build/agent2/splice-notes-top.py <new-top.md> <tag>
Reads the notes into memory first, backs them up to build/agent2/notes-backup-<tag>.md, writes <notes>.new and then
os.replace()s it, so the notes are never read and written in one expression.
"""
import hashlib
import os
import shutil
import sys

NOTES = 'perf-notes/agent2-baseline.md'
MARKER = b'  details live in this file.\n'


def main():
    top_path, tag = sys.argv[1], sys.argv[2]
    old = open(NOTES, 'rb').read()
    top = open(top_path, 'rb').read().replace(b'\r\n', b'\n')
    if not old.startswith(b'# Agent 2: build pipeline - RESUME NOTE'):
        sys.exit('unexpected start of notes; nothing written')
    if not top.startswith(b'# Agent 2: build pipeline - RESUME NOTE') or not top.endswith(MARKER):
        sys.exit('unexpected new top; nothing written')
    i = old.index(MARKER) + len(MARKER)
    if i > 12000:
        sys.exit('RESUME block end marker too far down (%d); nothing written' % i)
    backup = 'build/agent2/notes-backup-%s.md' % tag
    shutil.copyfile(NOTES, backup)
    out = top + old[i:]
    tmp = NOTES + '.new'
    with open(tmp, 'wb') as f:
        f.write(out)
    os.replace(tmp, NOTES)
    check = open(NOTES, 'rb').read()
    print('old %d B sha %s | new %d B sha %s, %d lines | old block %d B -> new block %d B | backup %s (%d B) | %s' % (
        len(old), hashlib.sha256(old).hexdigest()[:16], len(check), hashlib.sha256(check).hexdigest()[:16],
        check.count(b'\n'), i, len(top), backup, os.path.getsize(backup),
        'readback OK' if check == out else 'READBACK MISMATCH'))


if __name__ == '__main__':
    main()
