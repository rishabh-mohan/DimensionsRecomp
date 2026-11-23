#!/usr/bin/env python3
"""mapprobe_sub2.py - read-only structure probe of lld-link /MAP files (sub2 of Agent 2).

Prints header / non-symbol lines with line numbers, symbol-line counts per section,
tail-token shapes (flags/object), and the most common object descriptors.
Usage: python mapprobe_sub2.py MAP [MAP ...]
"""
import re
import sys
import time
from collections import Counter, defaultdict

SYM_RE = re.compile(r'^ ([0-9A-Fa-f]{4}):([0-9A-Fa-f]{8})\s+(.*)$')
HEX16_RE = re.compile(r'\s([0-9A-Fa-f]{16})(?=\s|$)')


def probe(path):
    t0 = time.time()
    section = 'preamble'
    sec_counts = Counter()
    headers = []
    blank_by_sec = Counter()
    tail_shapes = Counter()
    tail_examples = defaultdict(list)
    obj_counts = Counter()
    libs = Counter()
    unparsed = []
    nlines = 0
    with open(path, 'r', encoding='utf-8', errors='surrogateescape', newline='') as f:
        for ln, raw in enumerate(f, 1):
            nlines = ln
            line = raw.rstrip('\r\n')
            if not line.strip():
                blank_by_sec[section] += 1
                continue
            m = SYM_RE.match(line)
            if m and section in ('publics', 'statics', 'sections?'):
                rest = m.group(3)
                h = HEX16_RE.search(' ' + rest)
                if not h:
                    unparsed.append((ln, line))
                    continue
                tail = (' ' + rest)[h.end():].strip()
                toks = tail.split()
                shape = []
                for t in toks[:-1]:
                    shape.append(t if t in ('f', 'i') else '<tok>')
                shape.append('<obj>' if toks else '<none>')
                key = (section, ' '.join(shape))
                tail_shapes[key] += 1
                if len(tail_examples[key]) < 3:
                    tail_examples[key].append((ln, line))
                obj = toks[-1] if toks else ''
                if section == 'publics':
                    obj_counts[tail] += 1
                    if ':' in tail and not tail.startswith('<'):
                        libs[tail.split(':', 1)[0]] += 1
                sec_counts[section] += 1
                continue
            # non-symbol, non-blank line
            headers.append((ln, line))
            s = line.strip()
            if 'Publics by Value' in s:
                section = 'publics'
            elif s.startswith('Static symbols'):
                section = 'statics'
            elif s.startswith('entry point at'):
                section = 'entry'
            elif s.startswith('Exports'):
                section = 'exports'
            elif s.startswith('Start') and 'Length' in s:
                section = 'sectable'
    print(f'== {path}')
    print(f'lines {nlines}  ({time.time() - t0:.1f}s)')
    print('non-symbol, non-blank lines (first 80 / last 20):')
    shown = headers[:80] + ([(-1, '...')] if len(headers) > 100 else []) + (headers[-20:] if len(headers) > 80 else [])
    for ln, line in shown:
        if section != 'sectable' and line.startswith(' 000') and ln > 0 and False:
            continue
        print(f'  {ln:>8}: {line[:150]}')
    print(f'  total non-symbol lines: {len(headers)}')
    print('symbol lines per section:', dict(sec_counts))
    print('blank lines per section:', dict(blank_by_sec))
    print('tail shapes:')
    for key, n in sorted(tail_shapes.items()):
        print(f'  {key}: {n}')
        for ln, line in tail_examples[key]:
            print(f'      {ln}: {line[:160]}')
    print(f'unparsed symbol-like lines: {len(unparsed)}')
    for ln, line in unparsed[:10]:
        print(f'  {ln}: {line[:160]}')
    print(f'distinct public object descriptors: {len(obj_counts)}')
    for o, n in obj_counts.most_common(25):
        print(f'  {n:>8}  {o}')
    print('non-recomp objects with most publics:')
    k = 0
    for o, n in obj_counts.most_common():
        if 'legodimensions_recomp.' in o:
            continue
        print(f'  {n:>8}  {o}')
        k += 1
        if k >= 40:
            break
    print('libs (lib:obj prefixes) by public count:')
    for l, n in libs.most_common(40):
        print(f'  {n:>8}  {l}')


def main():
    for p in sys.argv[1:]:
        probe(p)
    print('RESULT: PASS (probe done)')


if __name__ == '__main__':
    main()
