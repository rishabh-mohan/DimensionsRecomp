#!/usr/bin/env python3
"""Small read-only regex grep over source trees (findstr chokes on big files).

usage: pgrep.py REGEX ROOT... [--ext .cpp,.h,...] [--skip DIRNAME,...] [--max N]
Prints path:line: text for each hit (text cut to 220 chars).
"""
import os
import re
import sys


def main(argv):
    exts = {'.c', '.cc', '.cpp', '.cxx', '.h', '.hpp', '.inl', '.inc', '.ps1', '.psm1', '.py', '.cmake', '.txt', '.toml', '.json', '.md'}
    skip = {'.git', 'generated', 'out', 'node_modules', '__pycache__', 'build-tmp'}
    maxhits = 400
    args = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--ext':
            exts = {e if e.startswith('.') else '.' + e for e in argv[i + 1].split(',') if e}
            i += 2
            continue
        if a == '--skip':
            skip |= {s for s in argv[i + 1].split(',') if s}
            i += 2
            continue
        if a == '--max':
            maxhits = int(argv[i + 1])
            i += 2
            continue
        args.append(a)
        i += 1
    if len(args) < 2:
        print(__doc__)
        return 2
    rx = re.compile(args[0])
    hits = 0
    files = 0
    for root in args[1:]:
        if os.path.isfile(root):
            walk = [(os.path.dirname(root), [], [os.path.basename(root)])]
        else:
            walk = os.walk(root)
        for dirpath, dirnames, filenames in walk:
            dirnames[:] = [d for d in dirnames if d not in skip]
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() not in exts:
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    if os.path.getsize(p) > 64 * 1024 * 1024:
                        continue
                    with open(p, 'r', encoding='utf-8', errors='replace') as f:
                        files += 1
                        for n, line in enumerate(f, 1):
                            if rx.search(line):
                                hits += 1
                                if hits <= maxhits:
                                    print('%s:%d: %s' % (p, n, line.rstrip()[:220]))
                except OSError as e:
                    print('ERR %s: %s' % (p, e))
    print('-- %d hits in %d files scanned' % (hits, files))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
