"""Agent 4, build/agent4/s35 (task (b) scratch AOT pack, notes S3.5): input precheck and post-run checks.

  precheck <dir>
      Parse the 4 pinned placement containers. Read-only.
  prelookup <run-dir> --old-index X [--main-cache Y]
      The static part of 'post', run before any lookup is started (a failed lookup ends in
      std::abort, so run_pack.ps1 starts none that cannot pass). Writes nothing.
  post <run-dir> --old-index X [--main-cache Y] --out <run-dir>/pack-check.json
      Check one run_pack.ps1 run: compile output, index addition, merge, production-lookup logs.
      Writes only --out, which must be inside the run dir.

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

EXPECTED = {
    'vs-ACAF01F01E1C03D2.bin': '6C4F65C3161DF6BEE23F9C551F34971D60275BB49C3DB6327CFF9084F4317A66',
    'ps-75A4D1ABA62F7594.bin': '09D05274AFBC26A2605D0B91E5C2A0E0C95303C4C0C84F4D463105EB678D66EE',
    'vs-CCD7655302B54D80.bin': 'F4EE30B28DEE9E4AB5AE2E9204D54195A0AC9D8D5497B7F2C8FAC11D90EEC65E',
    'ps-E81FD692C3AB35E1.bin': '58B4FA21E35500529895AA400F4B307F0DD09BBBBDB71F5C7C8E8748B31170F1',
}
LABELS = {
    'vs-ACAF01F01E1C03D2.bin': 'placement VS 0xAC449538 (backing 0xED23D3E0)',
    'ps-75A4D1ABA62F7594.bin': 'placement PS 0xAC448F28 (backing 0xED23D540, zero-prefix bucket)',
    'vs-CCD7655302B54D80.bin': 'second placement VS (pairs with ps-E81FD692)',
    'ps-E81FD692C3AB35E1.bin': 'second placement PS (pairs with vs-CCD76553)',
}
INDEX_ROW = re.compile(r'\{\s*0x([0-9A-Fa-f]+),\s*0x([0-9A-Fa-f]+),\s*0x([0-9A-Fa-f]+),'
                       r'\s*(\d+),\s*(\d+),\s*0x([0-9A-Fa-f]+)\s*\}')
CACHE_ROW = re.compile(r'\{\s*0x([0-9A-Fa-f]+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\}')
PASS_LINE = re.compile(r'PASS: (\d+) captured containers')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def be32(data, offset):
    return struct.unpack_from('>I', data, offset)[0]


def parse_container(path):
    data = path.read_bytes()
    info = {'file': path.name, 'label': LABELS.get(path.name, ''), 'bytes': len(data),
            'sha256': sha256(path), 'problems': []}
    problems = info['problems']
    if len(data) < 0x24:
        problems.append('shorter than the 0x24-byte header')
        return info
    flags, virtual, physical = struct.unpack_from('>III', data)
    marker = len(data) >= virtual + 4 and be32(data, virtual) == physical
    base = virtual + (4 if marker else 0)
    shader = be32(data, 0x18)
    # generate_microcode_index.cpp:66 -> 0 = vertex, 1 = pixel
    info.update(flags=f'{flags:08X}', virtual_size=virtual, physical_size=physical,
                marker=marker, physical_base=base, stage=1 if (flags & 1) == 0 else 0)
    if flags not in (0x102A1100, 0x102A1101):
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
    words = min(4, physical // 4)
    info['physical_first_words'] = ' '.join(f'{be32(data, base + 4 * i):08X}' for i in range(words))
    return info


def precheck_dir(directory):
    files = sorted(Path(directory).glob('*.bin'))
    names = sorted(f.name for f in files)
    fails = []
    if names != sorted(EXPECTED):
        fails.append(f'expected exactly {sorted(EXPECTED)}, found {names}')
    infos = []
    for f in files:
        info = parse_container(f)
        if f.name in EXPECTED and info['sha256'] != EXPECTED[f.name]:
            info['problems'].append('sha256 differs from the pinned value')
        infos.append(info)
        fails += [f'{f.name}: {p}' for p in info['problems']]
    return infos, fails


def print_containers(infos):
    for i in infos:
        print(f"  {i['file']:<26} {i['bytes']:>5} B  flags={i.get('flags')}  stage={i.get('stage')}  "
              f"physical={i.get('physical_size')}  microcode@{i.get('microcode_offset')}+{i.get('microcode_size')}  "
              f"first={i.get('physical_first_words')}  {'OK' if not i['problems'] else 'PROBLEMS'}")


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
    report = {'run': str(run), 'checks': []}
    fails = []

    def check(name, ok, detail=None):
        report['checks'].append({'name': name, 'ok': bool(ok), 'detail': detail})
        print(f"  [{'ok' if ok else 'FAIL'}] {name}" + (f'  ({detail})' if detail is not None and not ok else ''))
        if not ok:
            fails.append(name)

    infos, input_fails = precheck_dir(run / 'runtime-input')
    report['containers'] = infos
    check('inputs: exactly the 4 pinned placement containers, structure OK', not input_fails, input_fails)

    cache_path = run / 'runtime-cache.cpp'
    cache_rows, cache_sizes = read_cache(cache_path) if cache_path.exists() else ([], {})
    report['runtime_cache'] = {'sha256': sha256(cache_path) if cache_path.exists() else None,
                               'bytes': cache_path.stat().st_size if cache_path.exists() else None,
                               'sizes': cache_sizes,
                               'entries': [{'hash': f'{r[0]:016X}', 'dxilOffset': r[1], 'dxilSize': r[2],
                                            'spirvOffset': r[3], 'spirvSize': r[4], 'specConstantsMask': r[5]}
                                           for r in cache_rows]}
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
        rows, how = None, None
        try:
            name_hash = int(name.split('-', 1)[1].split('.', 1)[0], 16)
        except ValueError:
            name_hash = None
        if name_hash in by_container:
            rows, how, chash = by_container[name_hash], 'file name = container hash', name_hash
        else:
            matches = [h for h, rs in by_container.items()
                       if any(r[3] == info.get('physical_size') and r[4] == info.get('stage') for r in rs)]
            if len(matches) == 1:
                rows, how, chash = by_container[matches[0]], 'matched by physical size and stage', matches[0]
        if rows is None:
            check(f'{name}: has index rows', False, 'no index-addition rows could be matched')
            continue
        container_hashes.append(chash)
        sizes = sorted({r[3] for r in rows})
        info.update(container_hash=f'{chash:016X}', container_hash_source=how,
                    index_rows=[{'prefix': f'{r[0]:016X}', 'microcode_hash': f'{r[1]:016X}', 'size': r[3],
                                 'stage': r[4], 'texture_mask': f'{r[5]:08X}'} for r in rows])
        check(f'{name}: every index row has stage {info.get("stage")}',
              all(r[4] == info.get('stage') for r in rows), [r[4] for r in rows])
        check(f'{name}: whole-physical-section signature, size {info.get("physical_size")} '
              f'(literal block included)', info.get('physical_size') in sizes, sizes)
        check(f'{name}: instruction-stream signature, offset {info.get("microcode_offset")} '
              f'size {info.get("microcode_size")}', info.get('microcode_size') in sizes, sizes)
        entry = cache_by_hash.get(chash)
        info['spec_constants_mask'] = entry[5] if entry else None
        check(f'{name}: compiled into runtime-cache.cpp (DXIL present)', entry is not None and entry[2] > 0,
              None if entry is None else f'dxilSize {entry[2]}')

    check('runtime cache: exactly one entry per container, nothing else',
          set(cache_by_hash) == set(container_hashes) and len(container_hashes) == len(EXPECTED),
          sorted(f'{h:016X}' for h in cache_by_hash))

    so, sn, sa = set(old), set(new), set(addition)
    check(f'merge: every old record preserved ({len(old)})', so <= sn, len(so - sn))
    check('merge: new index = old + addition, no duplicates', sn == so | sa and len(new) == len(sn),
          f'{len(new)} rows, {len(sn)} unique')
    check('merge: added records are exactly the addition', sn - so == sa - so, len(sn - so))
    report['index'] = {'old_rows': len(old), 'addition_rows': len(addition), 'new_rows': len(new),
                       'added_rows': len(sn - so),
                       'new_sha256': sha256(run / 'lego-microcode-index.cpp'),
                       'addition_sha256': sha256(run / 'index-addition.cpp')}
    report_path = run / 'merge-report.json'
    if report_path.exists():
        merge_report = json.loads(report_path.read_text(encoding='utf-8'))
        report['merge_report'] = merge_report
        check('merge-report.json agrees', merge_report.get('before') == len(old)
              and merge_report.get('after') == len(new) and merge_report.get('added') == len(sn - so),
              merge_report)
    else:
        check('merge-report.json exists', False)

    old_containers = {r[2] for r in old}
    check('negative control: none of the 4 container hashes is in the old index (why they missed)',
          not (set(container_hashes) & old_containers),
          sorted(f'{h:016X}' for h in set(container_hashes) & old_containers))
    old_sigs = {(r[0], r[1], r[3], r[4]) for r in old}
    check('negative control: none of the new signatures is in the old index',
          not any((r[0], r[1], r[3], r[4]) in old_sigs for r in sa))
    if args.main_cache:
        main_rows, main_sizes = read_cache(args.main_cache)
        main_hashes = {r[0] for r in main_rows}
        report['main_cache'] = {'entries': len(main_rows), 'declared': main_sizes.get('g_shaderCacheEntryCount')}
        check(f'main cache ({len(main_rows)} entries) does not already contain the 4 containers',
              not (set(container_hashes) & main_hashes))

    old_prefix = collections.Counter((r[0], r[4]) for r in old)
    report['prefix_buckets'] = [{'prefix': f'{r[0]:016X}', 'stage': r[4], 'size': r[3],
                                 'container': f'{r[2]:016X}',
                                 'old_rows_same_prefix_and_stage': old_prefix[(r[0], r[4])]}
                                for r in sorted(sa - so, key=lambda r: (r[2], r[3]))]

    for name in (('lookup', 'lookup-main') if lookups else ()):
        log = run / 'logs' / f'{name}.stdout.txt'
        text = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
        m = PASS_LINE.search(text)
        check(f'{name}: production FindShaderByMicrocode resolves all 4 (physical and instruction sections)',
              m is not None and int(m.group(1)) == len(EXPECTED), text.strip()[-200:])

    hlsl = run / 'hlsl'
    report['hlsl_dump'] = sorted(p.name for p in hlsl.iterdir()) if hlsl.exists() else []
    report['fails'] = fails
    report['verdict'] = 'PASS' if not fails else 'FAIL'
    if out is not None:
        out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print_containers(infos)
    for info in infos:
        print(f"  {info['file']}: container {info.get('container_hash')} ({info.get('container_hash_source')}), "
              f"spec mask {info.get('spec_constants_mask')}, rows {[r['size'] for r in info.get('index_rows', [])]}")
    for b in report['prefix_buckets']:
        print(f"  added row prefix {b['prefix']} stage {b['stage']} size {b['size']}: "
              f"{b['old_rows_same_prefix_and_stage']} old rows share prefix+stage")
    print(f"  index {len(old)} -> {len(new)} rows; runtime cache {len(cache_rows)} entries; "
          f"hlsl files {len(report['hlsl_dump'])}")
    print('POST' if lookups else 'PRELOOKUP', report['verdict'])
    return 0 if not fails else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('precheck')
    p.add_argument('dir')
    p = sub.add_parser('prelookup')
    p.add_argument('run')
    p.add_argument('--old-index', required=True)
    p.add_argument('--main-cache')
    p = sub.add_parser('post')
    p.add_argument('run')
    p.add_argument('--old-index', required=True)
    p.add_argument('--main-cache')
    p.add_argument('--out', required=True)
    args = parser.parse_args()
    if args.mode == 'precheck':
        infos, fails = precheck_dir(args.dir)
        print_containers(infos)
        print('PRECHECK', 'PASS' if not fails else 'FAIL')
        for f in fails:
            print('  -', f)
        return 0 if not fails else 1
    if args.mode == 'prelookup':
        return post(args, lookups=False)
    return post(args)


if __name__ == '__main__':
    sys.exit(main())
