# Agent 10, #15 Review 4: rebuild Agent 9's codegen files at 21:14 (raw patch) and 21:37 (UTF-16 patch)
# from HEAD + the saved patches, check the applier against the current patch, and write interdiffs.
# Read-only on the repo (git show / git diff --no-index with GIT_OPTIONAL_LOCKS=0).
import os, re, subprocess, sys, pathlib

ROOT = pathlib.Path(r'<workspace>')
SDK = ROOT / 'DimensionsRecomp' / 'rexglue-sdk'
REV = ROOT / 'build' / 'agent10' / 'review'
OUT = REV / 'r4'
ENV = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
HUNK = re.compile(rb'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')


def load_patch(p):
    b = p.read_bytes()
    if b[:2] == b'\xff\xfe':
        t = b[2:].decode('utf-16-le')
        return t.replace('\r\n', '\n').encode('utf-8'), True
    return b, False


def parse_patch(data):
    files = {}
    cur = None
    lines = data.split(b'\n')
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith(b'diff --git '):
            m = re.match(rb'diff --git a/(.*?) b/(.*)$', ln.rstrip(b'\r'))
            cur = {'path': m.group(2).decode(), 'hunks': []}
            files[cur['path']] = cur
            i += 1
            continue
        if cur is not None and ln.startswith(b'@@ '):
            m = HUNK.match(ln)
            h = {'os': int(m.group(1)), 'ol': int(m.group(2) if m.group(2) is not None else 1),
                 'ns': int(m.group(3)), 'nl': int(m.group(4) if m.group(4) is not None else 1), 'lines': []}
            cur['hunks'].append(h)
            i += 1
            o = n = 0
            while i < len(lines):
                l = lines[i]
                if l.startswith(b'\\'):
                    h['lines'].append(('\\', b''))
                    i += 1
                    continue
                if o >= h['ol'] and n >= h['nl']:
                    break
                tag = l[:1]
                body = l[1:]
                if tag == b' ':
                    o += 1; n += 1
                elif tag == b'-':
                    o += 1
                elif tag == b'+':
                    n += 1
                elif l == b'':
                    tag = b' '; o += 1; n += 1
                else:
                    raise ValueError('bad hunk line in %s: %r' % (cur['path'], l[:60]))
                h['lines'].append((tag.decode(), body))
                i += 1
            continue
        i += 1
    return files


def apply(base, fp, strip_cr=False):
    if strip_cr:
        base = base.replace(b'\r\n', b'\n')
    trailing = base.endswith(b'\n')
    bl = base.split(b'\n')
    if trailing:
        bl = bl[:-1]
    out = []
    pos = 0
    new_trailing = trailing
    for h in fp['hunks']:
        start = h['os'] - 1 if h['ol'] > 0 else h['os']
        if start < pos:
            raise ValueError('overlapping hunk in %s' % fp['path'])
        out.extend(bl[pos:start])
        pos = start
        prev = None
        for tag, body in h['lines']:
            if tag in (' ', '-'):
                if pos >= len(bl) or bl[pos] != body:
                    got = bl[pos][:80] if pos < len(bl) else b'<EOF>'
                    raise ValueError('mismatch %s line %d: want %r got %r' % (fp['path'], pos + 1, body[:80], got))
                if tag == ' ':
                    out.append(body)
                pos += 1
            elif tag == '+':
                out.append(body)
            elif tag == '\\':
                if prev in ('+', ' '):
                    new_trailing = False
                elif prev == '-':
                    new_trailing = True
            prev = tag if tag != '\\' else prev
    out.extend(bl[pos:])
    res = b'\n'.join(out)
    if new_trailing:
        res += b'\n'
    return res


def git_show_head(rel):
    r = subprocess.run(['git', '-C', str(SDK), 'show', 'HEAD:' + rel], capture_output=True, env=ENV)
    if r.returncode != 0:
        return None
    return r.stdout


def write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def interdiff(a_dir, b_dir, rels, out_name):
    chunks = []
    stats = []
    for rel in rels:
        a = a_dir / rel
        b = b_dir / rel
        if not a.exists() or not b.exists():
            continue
        r = subprocess.run(['git', 'diff', '--no-index', '--no-color', '-U6', '--',
                            str(a.relative_to(OUT)), str(b.relative_to(OUT))],
                           capture_output=True, cwd=str(OUT), env=ENV)
        if r.stdout:
            chunks.append(r.stdout)
            plus = sum(1 for l in r.stdout.split(b'\n') if l.startswith(b'+') and not l.startswith(b'+++'))
            minus = sum(1 for l in r.stdout.split(b'\n') if l.startswith(b'-') and not l.startswith(b'---'))
            stats.append('  %-55s +%d/-%d' % (rel, plus, minus))
    data = b''.join(chunks)
    write(OUT / out_name, data)
    print('%s: %d bytes' % (out_name, len(data)))
    for s in stats:
        print(s)


def main():
    cur_data, _ = load_patch(REV / 'agent9-2313.patch')
    tst_data, _ = load_patch(REV / 'agent9-2313-tests.patch')
    cur = parse_patch(cur_data)
    cur.update(parse_patch(tst_data))
    p2114 = parse_patch(load_patch(REV / 'agent9-2114.patch')[0].replace(b'\r\n', b'\n'))
    p2137 = parse_patch(load_patch(REV / 'agent9-2137.patch')[0])
    p2137.update(parse_patch(load_patch(REV / 'agent9-2137-tests.patch')[0]))
    rels = sorted(cur)
    print('current files: %d; 2114 files: %d; 2137 files: %d' % (len(rels), len(p2114), len(p2137)))
    extra = sorted(set(p2114) - set(cur)) + sorted(set(p2137) - set(cur))
    if extra:
        print('files in old patches but not current:', extra)
    ok = True
    for rel in rels:
        head = git_show_head(rel)
        if head is None:
            print('NO HEAD for', rel); ok = False; continue
        live = (SDK / rel).read_bytes()
        write(OUT / 'head' / rel, head)
        write(OUT / 'now' / rel, live)
        try:
            rebuilt = apply(head, cur[rel])
            print('%-55s applier check: %s' % (rel, 'OK' if rebuilt == live else 'DIFFERS'))
            ok &= rebuilt == live
        except ValueError as e:
            print('applier check FAILED:', e); ok = False
        v = head
        if rel in p2114:
            try:
                v = apply(head, p2114[rel])
            except ValueError as e:
                print('2114 apply FAILED:', e)
        write(OUT / 'v2114' / rel, v)
        v = head.replace(b'\r\n', b'\n')
        if rel in p2137:
            try:
                v = apply(head, p2137[rel], strip_cr=True)
            except ValueError as e:
                print('2137 apply FAILED:', e)
        write(OUT / 'v2137' / rel, v)
        write(OUT / 'now-lf' / rel, live.replace(b'\r\n', b'\n'))
    print('applier verified on all current files:', ok)
    interdiff(OUT / 'v2114', OUT / 'now', rels, 'interdiff-2114-now.patch')
    interdiff(OUT / 'v2114', OUT / 'v2137', rels, 'interdiff-2114-2137.patch')
    interdiff(OUT / 'v2137', OUT / 'now-lf', rels, 'interdiff-2137-now.patch')


if __name__ == '__main__':
    main()
