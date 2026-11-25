# Rebuild the M10-rated build-final.py / fsyntax.py by reversing the post-rating edits, check their
# hashes, and write unified diffs rated -> current to build/agent2/final/work/.
import difflib, hashlib, os
F = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(F, 'work')

EDITS = {
    'build-final.py': ('740E59450887B338', [(
        "        check('leg output dir is new (b/%s/link-on)' % lg, not os.path.exists(os.path.join(top, 'link-on')))\n"
        "        if a.leg in ('rt', 'gpu', 'xe', 'nat'):\n"
        "            check('CTL output dir is new (b/%s/link-ctl)' % lg, not os.path.exists(os.path.join(top, 'link-ctl')))\n",
        "        # a --dry-run relink creates the out dirs (command/rsp text only); a real output file means \"not new\"\n"
        "        check('leg output is new (b/%s/link-on/%s)' % (lg, L['out']),\n"
        "              not os.path.exists(os.path.join(top, 'link-on', L['out'])))\n"
        "        if a.leg in ('rt', 'gpu', 'xe', 'nat'):\n"
        "            check('CTL output is new (b/%s/link-ctl/%s)' % (lg, L['out']),\n"
        "                  not os.path.exists(os.path.join(top, 'link-ctl', L['out'])))\n")]),
    'fsyntax.py': ('E9E4E131', [
        ("        say('%s: %d TU(s)' % (name, sum(1 for j in jobs if j['set'] == name)))\n",
         "        cnt = sum(1 for j in jobs if j['set'] == name)\n"
         "        ok = cnt == WANT_N[name]\n"
         "        say('%s %s: %d TU(s) (want %d)' % ('PASS' if ok else 'FAIL', name, cnt, WANT_N[name]))\n"
         "        if not ok:\n"
         "            fails.append('%s count' % name)\n"),
        ("def main():\n",
         "WANT_N = {'rt': 8, 'gpu': 1, 'xe': 1, 'xeoff': 1, 'nat': 4, 'natoff': 4}  # = 19 (final-build-rating S1)\n"
         "\n\ndef main():\n")]),
}

h16 = lambda b: hashlib.sha256(b).hexdigest().upper()[:16]
for name, (want, edits) in EDITS.items():
    raw = open(os.path.join(F, name), 'rb').read()
    crlf = b'\r\n' in raw
    cur = raw.decode('utf-8').replace('\r\n', '\n')
    old = cur
    for before, after in edits:
        assert old.count(after) == 1, (name, after[:40])
        old = old.replace(after, before)
    oldb = old.replace('\n', '\r\n').encode() if crlf else old.encode()
    got = h16(oldb)
    print('%s rated rebuilt %s (M10 rated %s) %s; current %s' % (
        name, got, want, 'MATCH' if got.startswith(want) else 'MISMATCH', h16(raw)))
    d = ''.join(difflib.unified_diff(old.splitlines(True), cur.splitlines(True),
                                     'a/' + name + ' (rated ' + got + ')', 'b/' + name + ' (current ' + h16(raw) + ')'))
    out = os.path.join(W, name.replace('.py', '') + '-rated-to-current.diff')
    open(out, 'w', encoding='utf-8', newline='\n').write(d)
    print('  diff -> %s sha256/16 %s' % (out, h16(d.encode())))
