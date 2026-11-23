#!/usr/bin/env python3
"""Agent 9 (task #8): compare codegen variants (counts, per-function sizes, samples).

usage: python count2.py OUTDIR NAME=DIR [NAME=DIR ...]
  DIR is a generated 'default' directory. The first variant is the reference for the
  per-function comparison; samples compare the reference with the last variant.
Writes OUTDIR/counts.tsv, OUTDIR/funcs.tsv (reference vs last), OUTDIR/summary.txt and
OUTDIR/samples/<fn>.<variant>.cpp, and prints the summary. One process, one core.
"""
import os
import re
import sys

TU_RE = re.compile(r'^legodimensions_recomp\.(\d+)\.cpp$')
FUNC_RE = re.compile(rb'^DEFINE_REX_FUNC\((\w+)\)', re.M)
# Whole-file counts over the TU files (legodimensions_recomp.N.cpp).
PATTERNS = [
    ('functions', b'DEFINE_REX_FUNC('),
    ('ctx_refs', b'ctx.'),
    ('flush_switches', b'FlushMode'),
    ('rotl64', b'__builtin_rotateleft64('),
    ('rlw_pin_form', b'.u64 << 32), '),
    ('rotl32', b'__builtin_rotateleft32('),
    ('musttail', b'[[clang::musttail]]'),
    ('lr_writes', b'ctx.lr = '),
    ('cmp_xer_local', b', xer);'),
    ('cmp_xer_ctx', b', ctx.xer);'),
    ('cmp_so_zero', b', {});'),
    ('lines', b'\n'),
]
# Per-function counts, used to pick samples.
FN_PATTERNS = [b'ctx.', b'FlushMode', b'[[clang::musttail]]', b'__builtin_rotateleft32(', b', {});', b'ctx.lr = ']
FN_CTX, FN_FLUSH, FN_TAIL, FN_ROTL32, FN_SO0, FN_LR = range(len(FN_PATTERNS))
NAMED_SAMPLES = ['sub_83E5C88C', 'sub_8307C528']


def scan(directory):
    """Return (totals, counts, funcs). funcs: name -> (size, path, start, end, fn_counts)."""
    totals = {'files': 0, 'bytes': 0, 'tus': 0, 'last_tu': -1}
    counts = {name: 0 for name, _ in PATTERNS}
    funcs = {}
    for root, _, files in os.walk(directory):
        for fname in files:
            path = os.path.join(root, fname)
            totals['files'] += 1
            totals['bytes'] += os.path.getsize(path)
            m = TU_RE.match(fname)
            if not m:
                continue
            totals['tus'] += 1
            totals['last_tu'] = max(totals['last_tu'], int(m.group(1)))
            with open(path, 'rb') as f:
                data = f.read()
            for name, pat in PATTERNS:
                counts[name] += data.count(pat)
            starts = [(mm.start(), mm.group(1).decode()) for mm in FUNC_RE.finditer(data)]
            for i, (s, fn) in enumerate(starts):
                e = starts[i + 1][0] if i + 1 < len(starts) else len(data)
                body = data[s:e]
                if fn in funcs:
                    raise SystemExit(f'{directory}: {fn} defined twice')
                funcs[fn] = (e - s, path, s, e, tuple(body.count(p) for p in FN_PATTERNS))
    return totals, counts, funcs


def quantile(sorted_vals, q):
    if not sorted_vals:
        return float('nan')
    i = min(len(sorted_vals) - 1, max(0, int(round(q * (len(sorted_vals) - 1)))))
    return sorted_vals[i]


def read_func(entry):
    _, path, s, e, _ = entry
    with open(path, 'rb') as f:
        f.seek(s)
        return f.read(e - s)


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    outdir = sys.argv[1]
    variants = []
    for arg in sys.argv[2:]:
        name, _, directory = arg.partition('=')
        if not directory or not os.path.isdir(directory):
            raise SystemExit(f'bad variant argument: {arg}')
        variants.append((name, directory))
    os.makedirs(os.path.join(outdir, 'samples'), exist_ok=True)
    data = {}
    for name, directory in variants:
        print(f'scanning {name} = {directory}', flush=True)
        data[name] = scan(directory)
    names = [n for n, _ in variants]
    ref, last = names[0], names[-1]
    out = []

    # Totals and counts.
    rows = [('files', 0), ('bytes', 0), ('tus', 0), ('last_tu', 0)]
    with open(os.path.join(outdir, 'counts.tsv'), 'w', newline='\n') as f:
        f.write('metric\t' + '\t'.join(names) + '\n')
        for key, _ in rows:
            f.write(key + '\t' + '\t'.join(str(data[n][0][key]) for n in names) + '\n')
        for key, _ in PATTERNS:
            f.write(key + '\t' + '\t'.join(str(data[n][1][key]) for n in names) + '\n')
    width = max(len(n) for n in names) + 2
    out.append('metric'.ljust(16) + ''.join(n.rjust(max(width, 14)) for n in names) +
               ''.join(f'  d({n}-{ref})'.rjust(18) for n in names[1:]))
    for key, _ in rows:
        vals = [data[n][0][key] for n in names]
        out.append(key.ljust(16) + ''.join(f'{v:,}'.rjust(max(width, 14)) for v in vals) +
                   ''.join(f'{v - vals[0]:+,}'.rjust(18) for v in vals[1:]))
    for key, _ in PATTERNS:
        vals = [data[n][1][key] for n in names]
        out.append(key.ljust(16) + ''.join(f'{v:,}'.rjust(max(width, 14)) for v in vals) +
                   ''.join(f'{v - vals[0]:+,}'.rjust(18) for v in vals[1:]))

    # Function sets and per-function sizes, each variant against the reference.
    rf = data[ref][2]
    for n in names[1:]:
        vf = data[n][2]
        only_ref = sorted(set(rf) - set(vf))
        only_var = sorted(set(vf) - set(rf))
        common = [fn for fn in rf if fn in vf]
        ratios = sorted(vf[fn][0] / rf[fn][0] for fn in common if rf[fn][0])
        sref = sum(rf[fn][0] for fn in common)
        svar = sum(vf[fn][0] for fn in common)
        out.append('')
        out.append(f'{n} vs {ref}: {len(common):,} common functions, {len(only_ref)} only in {ref}, '
                   f'{len(only_var)} only in {n}' + (f' (e.g. {(only_ref + only_var)[:5]})' if only_ref or only_var else ''))
        out.append(f'  function text {sref:,} -> {svar:,} B ({(svar - sref) / sref * 100:+.2f}%); '
                   f'smaller {sum(r < 1 for r in ratios):,}, equal {sum(r == 1 for r in ratios):,}, '
                   f'larger {sum(r > 1 for r in ratios):,}')
        out.append('  size ratio quantiles: ' + ', '.join(
            f'p{int(q * 100)}={quantile(ratios, q):.3f}' for q in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)))

    # Reference vs last: per-function table, top changes, samples.
    lf = data[last][2]
    common = [fn for fn in rf if fn in lf]
    with open(os.path.join(outdir, 'funcs.tsv'), 'w', newline='\n') as f:
        f.write(f'function\t{ref}_bytes\t{last}_bytes\tdelta\t{ref}_ctx\t{last}_ctx\t{ref}_flush\t{last}_flush\t'
                f'{last}_musttail\t{last}_rotl32\t{last}_so0\n')
        for fn in sorted(common):
            a, b = rf[fn], lf[fn]
            f.write(f'{fn}\t{a[0]}\t{b[0]}\t{b[0] - a[0]}\t{a[4][FN_CTX]}\t{b[4][FN_CTX]}\t{a[4][FN_FLUSH]}\t'
                    f'{b[4][FN_FLUSH]}\t{b[4][FN_TAIL]}\t{b[4][FN_ROTL32]}\t{b[4][FN_SO0]}\n')
    deltas = sorted(common, key=lambda fn: lf[fn][0] - rf[fn][0])
    out.append('')
    out.append(f'top shrink ({last} - {ref}, B): ' + ', '.join(
        f'{fn} {rf[fn][0]:,}->{lf[fn][0]:,}' for fn in deltas[:8]))
    out.append(f'top growth ({last} - {ref}, B): ' + ', '.join(
        f'{fn} {rf[fn][0]:,}->{lf[fn][0]:,}' for fn in reversed(deltas[-8:])))

    picks = []
    big = [fn for fn in common if rf[fn][0] >= 2048]
    if big:
        med = quantile(sorted(lf[fn][0] / rf[fn][0] for fn in big), 0.5)
        picks.append(('median_ratio', min(big, key=lambda fn: (abs(lf[fn][0] / rf[fn][0] - med), rf[fn][0]))))
    if deltas:
        picks.append(('max_shrink', deltas[0]))

    def smallest(pred, floor=800):
        cand = [fn for fn in common if lf[fn][0] >= floor and pred(lf[fn][4], rf[fn][4])]
        return min(cand, key=lambda fn: lf[fn][0]) if cand else None

    for label, pred, floor in [
        ('musttail', lambda b, a: b[FN_TAIL] >= 2, 800),
        ('rlwinm', lambda b, a: b[FN_ROTL32] >= 3, 800),
        ('flush_elided', lambda b, a: a[FN_FLUSH] - b[FN_FLUSH] >= 2, 800),
        ('so_zero', lambda b, a: b[FN_SO0] >= 3, 800),
        ('lr_kept', lambda b, a: b[FN_LR] >= 1, 0),
    ]:
        fn = smallest(pred, floor)
        if fn:
            picks.append((label, fn))
    for fn in NAMED_SAMPLES:
        if fn in rf or fn in lf:
            picks.append(('named', fn))
    out.append('')
    out.append('samples (OUTDIR/samples/<fn>.<variant>.cpp):')
    seen = set()
    for label, fn in picks:
        if fn in seen:
            continue
        seen.add(fn)
        sizes = []
        for n in names:
            entry = data[n][2].get(fn)
            if entry is None:
                sizes.append(f'{n}=-')
                continue
            with open(os.path.join(outdir, 'samples', f'{fn}.{n}.cpp'), 'wb') as f:
                f.write(read_func(entry))
            e4 = entry[4]
            sizes.append(f'{n}={entry[0]:,}B ctx={e4[FN_CTX]} flush={e4[FN_FLUSH]} tail={e4[FN_TAIL]} '
                         f'rotl32={e4[FN_ROTL32]} so0={e4[FN_SO0]} lr={e4[FN_LR]}')
        out.append(f'  {label:13} {fn}: ' + '; '.join(sizes))

    text = '\n'.join(out) + '\n'
    with open(os.path.join(outdir, 'summary.txt'), 'w', newline='\n') as f:
        f.write(text)
    print(text)


if __name__ == '__main__':
    main()
