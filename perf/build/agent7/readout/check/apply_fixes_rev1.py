# apply_fixes_rev1.py - apply check/fixes-rev1.txt (the 11 fixes from check/CHECK-W5b.md) to
# build/agent7/readout/W5b.md and W9.md.
# All-or-nothing: every OLD must occur exactly once in its file, in-place edits must not change
# the line count, and nothing is written unless every check passes. A re-run after success fails
# safely (the OLD strings are gone). Pre-fix copies are saved once as check/<stem>-rev0.md.
# Usage: python -B build/agent7/readout/check/apply_fixes_rev1.py
import hashlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent      # build/agent7/readout/check
READOUT = HERE.parent                                # build/agent7/readout
SPEC = HERE / 'fixes-rev1.txt'


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def parse(spec_text):
    edits, appends = {}, {}
    cur = old = None
    lines = spec_text.split('\n')
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip('\r')
        i += 1
        if ln.startswith('FILE '):
            cur = ln[5:].strip()
            edits.setdefault(cur, [])
        elif ln.startswith('OLD '):
            if old is not None:
                sys.exit('spec: OLD without NEW before line %d' % i)
            old = ln[4:]
        elif ln.startswith('NEW '):
            if old is None or cur is None:
                sys.exit('spec: NEW without OLD/FILE at line %d' % i)
            edits[cur].append((old, ln[4:]))
            old = None
        elif ln.startswith('APPEND '):
            name = ln[7:].strip()
            buf = []
            while i < len(lines) and lines[i].rstrip('\r') != 'ENDAPPEND':
                buf.append(lines[i].rstrip('\r'))
                i += 1
            if i >= len(lines):
                sys.exit('spec: APPEND without ENDAPPEND')
            i += 1
            appends[name] = buf
        elif ln.strip() == '' or ln.startswith('#'):
            continue
        else:
            sys.exit('spec: bad line %d: %r' % (i, ln[:60]))
    if old is not None:
        sys.exit('spec: dangling OLD')
    return edits, appends


def main():
    edits, appends = parse(SPEC.read_text(encoding='utf-8'))
    out, ok = {}, True
    for name in sorted(set(edits) | set(appends)):
        path = READOUT / name
        raw = path.read_bytes()
        text = raw.decode('utf-8')
        nl = '\r\n' if '\r\n' in text else '\n'
        n0 = text.count('\n')
        new = text
        for k, (o, nw) in enumerate(edits.get(name, []), 1):
            c = new.count(o)
            if c != 1:
                print('FAIL %s edit %d: OLD occurs %d times: %r' % (name, k, c, o[:70]))
                ok = False
                continue
            new = new.replace(o, nw)
            if new.count(nw) < 1:
                print('FAIL %s edit %d: NEW not found after replace' % (name, k))
                ok = False
        n1 = new.count('\n')
        if n1 != n0:
            print('FAIL %s: in-place edits changed the line count (%d -> %d)' % (name, n0, n1))
            ok = False
        if name in appends:
            if not new.endswith(nl):
                new += nl
            new += nl.join(appends[name]) + nl
        out[name] = (raw, new.encode('utf-8'), len(edits.get(name, [])), n0)
    if not ok:
        sys.exit('RESULT: FAIL, nothing written')
    for name, (raw, newb, ne, n0) in out.items():
        path = READOUT / name
        bak = HERE / (path.stem + '-rev0.md')
        if not bak.exists():
            bak.write_bytes(raw)
        path.write_bytes(newb)
        print('%s: %d in-place edits; newlines %d -> %d; bytes %d -> %d; sha256 %s -> %s; pre-fix copy check/%s' % (
            name, ne, n0, newb.decode('utf-8').count('\n'), len(raw), len(newb),
            sha(raw)[:16], sha(newb)[:16], bak.name))
    print('RESULT: APPLIED')


if __name__ == '__main__':
    main()
