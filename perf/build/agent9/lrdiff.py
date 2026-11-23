#!/usr/bin/env python3
"""Agent 9 (task #8): check that two codegen variants differ only in lines that mention ctx.lr.

usage: py -3 lrdiff.py A_DIR B_DIR OUT.txt
  A_DIR, B_DIR: generated 'default' directories (e.g. batch with skip_lr, batch-nolr without it).
Every function (DEFINE_REX_FUNC(name) up to the next DEFINE_REX_FUNC or the end of its TU) is compared by name
after dropping each line that contains 'ctx.lr' and trailing whitespace. TU boundaries may differ between the
variants, so functions are matched by name, not by file. Reports the counts, the most common changed lines
(normalised: addresses/numbers replaced by #) over up to 5000 differing functions, and the first 12 differing
functions (unified diff of the stripped text). One process, one core.
"""
import collections
import difflib
import hashlib
import os
import re
import sys

TU_RE = re.compile(r'^legodimensions_recomp\.(\d+)\.cpp$')
FUNC_RE = re.compile(rb'^DEFINE_REX_FUNC\((\w+)\)', re.M)
NORM_RE = re.compile(r'0x[0-9A-Fa-f]+|\b(?:sub|loc|lbl)_[0-9A-Fa-f]+\b|\b\d+\b')
CLASSIFY_MAX = 5000


def functions(directory):
    tus = sorted((int(m.group(1)), n) for n in os.listdir(directory) if (m := TU_RE.match(n)))
    for _, name in tus:
        with open(os.path.join(directory, name), 'rb') as f:
            data = f.read()
        starts = list(FUNC_RE.finditer(data))
        for i, m in enumerate(starts):
            end = starts[i + 1].start() if i + 1 < len(starts) else len(data)
            yield m.group(1).decode(), data[m.start():end]


def strip(text):
    lines = text.rstrip().split(b'\n')
    kept = [line.rstrip() for line in lines if b'ctx.lr' not in line]
    return kept, len(lines) - len(kept)


def norm(line):
    return NORM_RE.sub('#', line.decode('utf-8', 'replace').strip())


def main():
    a_dir, b_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]
    a_hash, a_lr = {}, 0
    for name, text in functions(a_dir):
        kept, lr = strip(text)
        a_lr += lr
        a_hash[name] = hashlib.sha1(b'\n'.join(kept)).digest()
    b_names, b_lr, same, differ, only_b, diffs = set(), 0, 0, [], [], {}
    b_lr_funcs = 0
    b_kept_all = {}
    for name, text in functions(b_dir):
        kept, lr = strip(text)
        b_lr += lr
        b_lr_funcs += lr > 0
        b_names.add(name)
        h = a_hash.get(name)
        if h is None:
            only_b.append(name)
        elif h == hashlib.sha1(b'\n'.join(kept)).digest():
            same += 1
        else:
            differ.append(name)
            if len(diffs) < 12:
                diffs[name] = kept
            if len(b_kept_all) < CLASSIFY_MAX:
                b_kept_all[name] = kept
    only_a = [n for n in a_hash if n not in b_names]
    a_texts = {}
    if b_kept_all:
        for name, text in functions(a_dir):
            if name in b_kept_all:
                a_texts[name] = strip(text)[0]
    removed, added = collections.Counter(), collections.Counter()
    skipped_big = 0
    for name, kept in b_kept_all.items():
        a_lines = a_texts.get(name, [])
        if len(a_lines) + len(kept) > 6000:
            skipped_big += 1
            continue
        sm = difflib.SequenceMatcher(None, a_lines, kept, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                continue
            removed.update(norm(l) for l in a_lines[i1:i2])
            added.update(norm(l) for l in kept[j1:j2])
    lines = [
        f'A = {a_dir}',
        f'B = {b_dir}',
        f'functions: A {len(a_hash):,}, B {len(b_names):,}; only in A {len(only_a)}, only in B {len(only_b)}',
        f'lines with ctx.lr: A {a_lr:,}, B {b_lr:,} (in {b_lr_funcs:,} B functions)',
        f'identical after dropping ctx.lr lines: {same:,}; different: {len(differ):,}',
        f'changed lines over {len(b_kept_all) - skipped_big:,} differing functions ({skipped_big} over 6000 lines skipped): '
        f'removed {sum(removed.values()):,} '
        f'({len(removed):,} distinct), added {sum(added.values()):,} ({len(added):,} distinct)',
    ]
    if only_a[:10] or only_b[:10]:
        lines.append(f'only in A (first 10): {only_a[:10]}; only in B (first 10): {only_b[:10]}')
    lines.append('top removed (A only), normalised:')
    lines.extend(f'  {c:>9,}  {l}' for l, c in removed.most_common(30))
    lines.append('top added (B only), normalised:')
    lines.extend(f'  {c:>9,}  {l}' for l, c in added.most_common(30))
    if differ:
        lines.append(f'different (first 50): {differ[:50]}')
    for name, kept in diffs.items():
        lines.append(f'--- diff {name} (A -> B, ctx.lr lines dropped)')
        a_lines = [l.decode('utf-8', 'replace') for l in a_texts.get(name, [])]
        b_lines = [l.decode('utf-8', 'replace') for l in kept]
        lines.extend(difflib.unified_diff(a_lines, b_lines, lineterm='', n=1))
    text = '\n'.join(lines) + '\n'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(text)
    print('\n'.join(lines[:6]))


if __name__ == '__main__':
    main()
