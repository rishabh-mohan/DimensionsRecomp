"""Eye-check samples for the rlw* lowering: off3 vs batch.

Reads the first batch TUs, picks functions with lowered rlw* sites (generic text gone),
one with a 32-bit rotate, and lists the rlw* sites still in generic form (expected:
wrapping masks, mb > me). Finds the same functions in off3 and prints both forms of
each rlw* site. Light: a few TUs plus an early-exit scan of off3. Usage:
  py -3 build/agent9/rlwsample.py [OUT]
"""
import glob
import os
import re
import sys

ROOT = os.path.join('build', 'agent9', 'generated')
RLW = re.compile(rb'^\t// (rlwinm|rlwimi|rlwnm|rotlwi|rotrwi|rotlw|slwi|srwi|extrwi|extlwi|insrwi|inslwi|clrrwi|clrlslwi)\.? ?(.*)$')
FN = re.compile(rb'DEFINE_REX_FUNC\((sub_[0-9A-F]+)\) \{')


def tus(variant):
    files = glob.glob(os.path.join(ROOT, variant, 'default', 'legodimensions_recomp.*.cpp'))
    return sorted(files, key=lambda p: int(p.rsplit('.', 2)[1]))


def functions(data):
    starts = [(m.start(), m.group(1).decode()) for m in FN.finditer(data)]
    for i, (pos, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(data)
        yield name, data[pos:end]


def sites(text):
    """[(comment, [code lines])] for each rlw* instruction in the function text."""
    lines = text.split(b'\n')
    out = []
    i = 0
    while i < len(lines):
        m = RLW.match(lines[i])
        if m:
            code = []
            j = i + 1
            while j < len(lines) and not lines[j].startswith(b'\t//') and not lines[j].startswith(b'loc_') and lines[j] != b'}':
                code.append(lines[j].strip())
                j += 1
            out.append((lines[i].strip(), code))
            i = j
        else:
            i += 1
    return out


def generic(code):
    return any(b'__builtin_rotateleft64(' in c for c in code)


def main():
    out = open(sys.argv[1], 'w', encoding='utf-8') if len(sys.argv) > 1 else sys.stdout
    batch = tus('batch')
    picked = {}  # role -> name
    remaining = []  # (fn, comment, code)
    lowered_total = generic_total = 0
    for path in batch[:3]:
        data = open(path, 'rb').read()
        for name, text in functions(data):
            s = sites(text)
            low = [x for x in s if not generic(x[1])]
            gen = [x for x in s if generic(x[1])]
            lowered_total += len(low)
            generic_total += len(gen)
            for c, code in gen:
                remaining.append((name, c, code))
            if low and 'lowered' not in picked and len(low) >= 3:
                picked['lowered'] = name
            if any(b'__builtin_rotateleft32(' in l for _, code in low for l in code) and 'rotl32' not in picked:
                picked['rotl32'] = name
            if any(m.group(1) == b'rlwimi' for m in (RLW.match(b'\t' + c) for c, code in low) if m) and 'rlwimi' not in picked:
                picked['rlwimi'] = name
            if gen and 'generic' not in picked:
                picked['generic'] = name
    print(f'batch TUs 0-2: {lowered_total} rlw* sites lowered, {generic_total} still generic', file=out)
    wrap = 0
    for name, c, code in remaining:
        m = re.search(rb'(rlwinm|rlwimi|rlwnm)\.? r\d+,r\d+,(r?\d+),(\d+),(\d+)', c)
        if m and int(m.group(3)) > int(m.group(4)):
            wrap += 1
    print(f'generic sites with mb > me (wrapping mask): {wrap} of {len(remaining)}', file=out)
    for name, c, code in remaining[:8]:
        print(f'  {name}: {c.decode()}  ->  {code[0].decode() if code else ""}', file=out)
    print(f'picked: {picked}', file=out)
    want = set(picked.values())
    btext, otext = {}, {}
    for path in batch[:3]:
        data = open(path, 'rb').read()
        for name, text in functions(data):
            if name in want:
                btext[name] = text
    for path in tus('off3'):
        if len(otext) == len(want):
            break
        data = open(path, 'rb').read()
        for name in want - set(otext):
            key = b'DEFINE_REX_FUNC(' + name.encode() + b') {'
            pos = data.find(key)
            if pos >= 0:
                end = data.find(b'\nDEFINE_REX_FUNC(', pos + 1)
                otext[name] = data[pos:end if end >= 0 else len(data)]
    for role, name in picked.items():
        print(f'\n== {role}: {name} (off3 -> batch)', file=out)
        if name not in otext:
            print('  not found in off3', file=out)
            continue
        so, sb = sites(otext[name]), sites(btext[name])
        print(f'  {len(so)} rlw* sites in off3, {len(sb)} in batch', file=out)
        for (co, codeo), (cb, codeb) in list(zip(so, sb))[:6]:
            same = 'SAME COMMENT' if co == cb else 'COMMENT DIFFERS'
            print(f'  {cb.decode()}   [{same}]', file=out)
            for l in codeo:
                print(f'    - {l.decode()}', file=out)
            for l in codeb:
                print(f'    + {l.decode()}', file=out)


if __name__ == '__main__':
    main()
