"""E16.1, build/agent16/pack (S5 phase 0.4b): input precheck and post-run checks for native4bp.py pack.

Generalized from build/agent4/s35/check_pack.py (Agent 4): the expected container set is the staged-input
manifest <run>/runtime-input/STAGED.tsv (name TAB sha256 TAB source) instead of the 4 hard-coded s35 files.

  precheck <dir> [--staged STAGED.tsv]
      Parse every *.bin placement container in <dir>. Read-only.
  prelookup <run-dir> --old-index X [--main-cache Y]
      The static part of 'post', run before any lookup is started (a failed lookup ends in std::abort).
  post <run-dir> --old-index X [--main-cache Y] --out <run-dir>/pack-check.json
      Check one pack run: compile output, index addition, merge, production-lookup logs. Writes only --out.

FAIL conditions: structure problems, sha mismatch vs STAGED.tsv, a container without index rows or without a
runtime-cache entry, cache entries that are not exactly the staged containers, merge not = old + addition,
lookup PASS count != number of staged containers. WARN only (recorded): container hash / signature already in the
old index, container already in the main cache.
Exit code 0 = PASS, 1 = FAIL, 2 = usage error.
"""
import argparse
import collections
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

PLACEMENT_FLAGS = (0x102A1100, 0x102A1101)  # test_placement_capture_lookup.py asserts these
INDEX_ROW = re.compile(r'\{\s*0x([0-9A-Fa-f]+),\s*0x([0-9A-Fa-f]+),\s*0x([0-9A-Fa-f]+),'
                       r'\s*(\d+),\s*(\d+),\s*0x([0-9A-Fa-f]+)\s*\}')
CACHE_ROW = re.compile(r'\{\s*0x([0-9A-Fa-f]+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\}')
PASS_LINE = re.compile(r'PASS: (\d+) captured containers')
NAME_RE = re.compile(r'^(vs|ps)-([0-9A-Fa-f]{16})\.bin$')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def be32(data, offset):
    return struct.unpack_from('>I', data, offset)[0]


def parse_container(path):
    path = Path(path)
    data = path.read_bytes()
    info = {'file': path.name, 'bytes': len(data), 'sha256': sha256(path), 'problems': []}
    problems = info['problems']
    if not NAME_RE.match(path.name):
        problems.append('file name is not vs-/ps-<16 hex>.bin')
    if len(data) < 0x24:
        problems.append('shorter than the 0x24-byte header')
        return info
    flags, virtual, physical = struct.unpack_from('>III', data)
    marker = len(data) >= virtual + 4 and be32(data, virtual) == physical
    base = virtual + (4 if marker else 0)
    shader = be32(data, 0x18)
    info.update(flags=f'{flags:08X}', virtual_size=virtual, physical_size=physical,
                marker=marker, physical_base=base, stage=1 if (flags & 1) == 0 else 0)
    if flags not in PLACEMENT_FLAGS:
        problems.append(f'flags {flags:08X} is not a placement VS/PS container')
    if be32(data, 0x1C) or be32(data, 0x20):
        problems.append('header words 0x1C/0x20 are not zero (the indexer would skip it)')
    if not marker:
        problems.append('no physical_size marker after the virtual section')
    if len(data) != base + physical:
        problems.append(f'length {len(data)} != virtual + marker + physical = {base + physical}')
    want_stage = 0 if path.name.startswith('vs-') else 1
    if info['stage'] != want_stage:
        problems.append(f'stage {info["stage"]} does not match the file name')
    if not (36 <= shader and shader + 8 <= virtual):
        problems.append('shader descriptor offset out of range')
        return info
    offset, size = struct.unpack_from('>II', data, shader)
    info.update(microcode_offset=offset, microcode_size=size)
    if size < 8 or offset + size > physical:
        problems.append('instruction stream lies outside the physical section')
    elif not any(data[base + offset:base + offset + size]):
        problems.append('instruction stream is all zero')
    return info


def read_staged(path):
    staged = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):
            continue
        c = line.split('\t')
        staged[c[0]] = c[1].upper()
    return staged


def precheck_dir(directory, staged=None):
    files = sorted(Path(directory).glob('*.bin'))
    names = sorted(f.name for f in files)
    fails = []
    if staged is not None and names != sorted(staged):
        fails.append(f'staged set mismatch: missing {sorted(set(staged) - set(names))}, '
                     f'extra {sorted(set(names) - set(staged))}')
    infos = []
    for f in files:
        info = parse_container(f)
        if staged is not None and f.name in staged and info['sha256'] != staged[f.name]:
            info['problems'].append('sha256 differs from STAGED.tsv')
        infos.append(info)
        fails += [f'{f.name}: {p}' for p in info['problems']]
    if not files:
        fails.append('no *.bin containers')
    return infos, fails


def print_containers(infos, limit=None):
    for i in infos[:limit]:
        print(f"  {i['file']:<26} {i['bytes']:>5} B  flags={i.get('flags')}  stage={i.get('stage')}  "
              f"physical={i.get('physical_size')}  microcode@{i.get('microcode_offset')}+{i.get('microcode_size')}  "
              f"{'OK' if not i['problems'] else 'PROBLEMS ' + '; '.join(i['problems'])}")
    if limit is not None and len(infos) > limit:
        print(f'  ... {len(infos) - limit} more')


def read_index(path):
    text = Path(path).read_text(encoding='ascii')
    rows = [(int(a, 16), int(b, 16), int(c, 16), int(d), int(e), int(f, 16))
            for a, b, c, d, e, f in INDEX_ROW.findall(text)]
    declared = re.search(r'g_shaderMicrocodeEntryCount\s*=\s*(\d+)', text)
    if not declared or int(declared.group(1)) != len(rows):
        raise ValueError(f'{path}: declared count does not match the {len(rows)} parsed rows')
    return rows


def read_cache(path):
    text = Path(path).read_text(encoding='ascii', errors='replace')
    rows = [(int(h, 16),) + tuple(int(x) for x in rest) for h, *rest in CACHE_ROW.findall(text)]
    sizes = {}
    for name in ('g_shaderCacheEntryCount', 'g_dxilCacheCompressedSize', 'g_dxilCacheDecompressedSize',
                 'g_spirvCacheCompressedSize', 'g_spirvCacheDecompressedSize'):
        m = re.search(name + r'\s*=\s*(\d+)', text)
        sizes[name] = int(m.group(1)) if m else None
    return rows, sizes


def post(args, lookups=True):
    run = Path(args.run).resolve()
    out = Path(args.out).resolve() if getattr(args, 'out', None) else None
    if out is not None and run not in out.parents:
        print(f'refusing to write {out}: not inside {run}')
        return 2
    report = {'run': str(run), 'checks': [], 'warnings': []}
    fails, warns = [], report['warnings']

    def check(name, ok, detail=None):
        report['checks'].append({'name': name, 'ok': bool(ok), 'detail': detail})
        if not ok:
            print(f"  [FAIL] {name}" + (f'  ({detail})' if detail is not None else ''))
            fails.append(name)
        return ok

    def warn(name, detail=None):
        warns.append({'name': name, 'detail': detail})
        print(f'  [warn] {name}' + (f'  ({detail})' if detail is not None else ''))

    staged = read_staged(run / 'runtime-input' / 'STAGED.tsv')
    n = len(staged)
    infos, input_fails = precheck_dir(run / 'runtime-input', staged)
    report['containers'] = infos
    check(f'inputs: exactly the {n} staged placement containers (STAGED.tsv), structure OK', not input_fails,
          input_fails)

    cache_path = run / 'runtime-cache.cpp'
    cache_rows, cache_sizes = read_cache(cache_path) if cache_path.exists() else ([], {})
    masks = collections.Counter(r[5] for r in cache_rows)
    report['runtime_cache'] = {'sha256': sha256(cache_path) if cache_path.exists() else None,
                               'bytes': cache_path.stat().st_size if cache_path.exists() else None,
                               'sizes': cache_sizes, 'entries': len(cache_rows),
                               'spec_constants_masks': {str(k): v for k, v in sorted(masks.items())}}
    check('runtime cache: declared entry count equals the parsed rows',
          cache_rows and cache_sizes.get('g_shaderCacheEntryCount') == len(cache_rows),
          f"declared {cache_sizes.get('g_shaderCacheEntryCount')}, parsed {len(cache_rows)}")
    cache_by_hash = {r[0]: r for r in cache_rows}

    addition = read_index(run / 'index-addition.cpp')
    old = read_index(args.old_index)
    new = read_index(run / 'lego-microcode-index.cpp')
    by_container = collections.defaultdict(list)
    for r in addition:
        by_container[r[2]].append(r)

    container_hashes = []
    for info in infos:
        name = info['file']
        m = NAME_RE.match(name)
        chash = int(m.group(2), 16) if m else None
        rows = by_container.get(chash)
        if not check(f'{name}: has index-addition rows (container hash = file name)', rows is not None):
            continue
        container_hashes.append(chash)
        sizes = sorted({r[3] for r in rows})
        info.update(container_hash=f'{chash:016X}', index_sizes=sizes)
        check(f'{name}: every index row has stage {info.get("stage")}',
              all(r[4] == info.get('stage') for r in rows), [r[4] for r in rows])
        check(f'{name}: whole-physical-section signature size {info.get("physical_size")}',
              info.get('physical_size') in sizes, sizes)
        check(f'{name}: instruction-stream signature size {info.get("microcode_size")}',
              info.get('microcode_size') in sizes, sizes)
        entry = cache_by_hash.get(chash)
        info['spec_constants_mask'] = entry[5] if entry else None
        check(f'{name}: compiled into runtime-cache.cpp (DXIL present)', entry is not None and entry[2] > 0,
              None if entry is None else f'dxilSize {entry[2]}')

    check(f'runtime cache: exactly one entry per staged container ({n}), nothing else',
          set(cache_by_hash) == set(container_hashes) and len(container_hashes) == n,
          f'cache {len(cache_by_hash)}, matched {len(container_hashes)}, '
          f'extra {sorted(f"{h:016X}" for h in set(cache_by_hash) - set(container_hashes))}')

    so, sn, sa = set(old), set(new), set(addition)
    check(f'merge: every old record preserved ({len(old)})', so <= sn, len(so - sn))
    check('merge: new index = old + addition, no duplicates', sn == so | sa and len(new) == len(sn),
          f'{len(new)} rows, {len(sn)} unique')
    report['index'] = {'old_rows': len(old), 'addition_rows': len(addition), 'new_rows': len(new),
                       'added_rows': len(sn - so),
                       'new_sha256': sha256(run / 'lego-microcode-index.cpp'),
                       'addition_sha256': sha256(run / 'index-addition.cpp')}
    report_path = run / 'merge-report.json'
    if report_path.exists():
        mr = json.loads(report_path.read_text(encoding='utf-8'))
        report['merge_report'] = mr
        check('merge-report.json agrees', mr.get('before') == len(old) and mr.get('after') == len(new)
              and mr.get('added') == len(sn - so), mr)
    else:
        check('merge-report.json exists', False)

    old_containers = {r[2] for r in old}
    dup = sorted(f'{h:016X}' for h in set(container_hashes) & old_containers)
    if dup:
        warn(f'{len(dup)} container hash(es) already in the old index', dup)
    old_sigs = {(r[0], r[1], r[3], r[4]) for r in old}
    dsig = [r for r in sa if (r[0], r[1], r[3], r[4]) in old_sigs]
    if dsig:
        warn(f'{len(dsig)} new signature(s) already in the old index (another container wins those)',
             sorted({f'{r[2]:016X}' for r in dsig}))
    if args.main_cache:
        main_rows, main_sizes = read_cache(args.main_cache)
        main_hashes = {r[0] for r in main_rows}
        report['main_cache'] = {'entries': len(main_rows), 'declared': main_sizes.get('g_shaderCacheEntryCount')}
        inmain = sorted(f'{h:016X}' for h in set(container_hashes) & main_hashes)
        if inmain:
            warn(f'{len(inmain)} container(s) already in the main cache ({len(main_rows)} entries)', inmain)

    for name in (('lookup', 'lookup-main') if lookups else ()):
        log = run / 'logs' / f'{name}.stdout.txt'
        text = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
        m = PASS_LINE.search(text)
        check(f'{name}: production FindShaderByMicrocode resolves all {n} (physical and instruction sections)',
              m is not None and int(m.group(1)) == n, text.strip()[-200:])

    hlsl = run / 'hlsl'
    report['hlsl_dump_files'] = len(list(hlsl.iterdir())) if hlsl.exists() else 0
    report['fails'] = fails
    report['verdict'] = 'PASS' if not fails else 'FAIL'
    if out is not None:
        out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"  {len(report['checks'])} checks, {len(fails)} FAIL, {len(warns)} warning(s); "
          f"index {len(old)} -> {len(new)} rows (+{len(sn - so)}); runtime cache {len(cache_rows)} entries, "
          f"spec masks {dict(sorted(masks.items()))}; hlsl files {report['hlsl_dump_files']}")
    print(f"  runtime-cache.cpp {report['runtime_cache']['sha256']}; index {report['index']['new_sha256']}")
    print('POST' if lookups else 'PRELOOKUP', report['verdict'])
    return 0 if not fails else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('precheck')
    p.add_argument('dir')
    p.add_argument('--staged')
    for m in ('prelookup', 'post'):
        p = sub.add_parser(m)
        p.add_argument('run')
        p.add_argument('--old-index', required=True)
        p.add_argument('--main-cache')
        p.add_argument('--out', required=(m == 'post'))
    args = parser.parse_args()
    if args.mode == 'precheck':
        infos, fails = precheck_dir(args.dir, read_staged(args.staged) if args.staged else None)
        print_containers(infos)
        print('PRECHECK', 'PASS' if not fails else 'FAIL', f'({len(infos)} containers)')
        for f in fails:
            print('  -', f)
        return 0 if not fails else 1
    if args.mode == 'prelookup':
        return post(args, lookups=False)
    return post(args)


if __name__ == '__main__':
    sys.exit(main())
