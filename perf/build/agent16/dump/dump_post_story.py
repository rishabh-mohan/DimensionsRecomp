#!/usr/bin/env python3
"""dump_post_story.py (M16, S5): read-only read-out of one native4bp manual session run with
LEGO_DUMP_MISSING_SHADERS set (M3 kit, RUN-MANUAL.cmd dump), plus the target post-check.

usage:
  dump_post_story.py --run RUN_DIR --dumps DUMP_ROOT --trace TRACE_DIR --targets DUMP-TARGETS-story.txt
                     --out REPORT.txt [--stage PACK_INPUT_DIR] [--fingerprint 39129c4c059be5f0]

Reads only. Writes only --out and (optional) --stage, and refuses both unless they are under build\\agent16\\dump\\.
Reports:
  1. run.json exit fields; game.log: native GPU fingerprint, "shader miss cache OFF (...LEGO_DUMP_MISSING_SHADERS...)",
     "dumped missing shader" lines;
  2. dumps: every file per category (root = create path, placement-containers, placement-raw) with bytes, sha256,
     and whether the same file name is already in the attract pack input (pack-input-20261125-172422);
  3. trace: missing_placement_shader_identity events (stage, guest, container_hash) vs the 256-container cap, and the
     distinct guests of draw_missing_* / unrecognized_shader;
  4. target hit list: per target row, DUMPED (identity event with that stage+guest) / MISSING-NO-IDENTITY (the guest
     missed in this run but no identity event: same container already captured under another guest, cap, or a
     validation refusal) / NOT-SEEN (not missed in this run: covered by native4bp or content not reached).
--stage copies NEW placement-containers files (never root, never placement-raw) plus SHA256SUMS.txt; it refuses to
overwrite a file with different bytes.
Exit 0 = report written (the RESULT line says whether the dump looks usable).
"""
import argparse, collections, ctypes, hashlib, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ATTRACT = os.path.join(HERE, 'pack-input-20261125-172422')
CAP = 256
GRE = re.compile(r'guest(?:_vs|_ps)?=\s*(\d+)')
SRE = re.compile(r'stage=\s*(\d+)')
CRE = re.compile(r'container_hash=\s*(\d+)')
STAGE = {'6': 'VS', '7': 'PS'}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def inside(p):
    return os.path.normcase(os.path.abspath(p)).startswith(os.path.normcase(HERE) + os.sep)


def load_targets(path):
    rows = []
    for line in open(path, encoding='ascii'):
        if line.startswith('#') or line.startswith('stage\t') or not line.strip():
            continue
        p = line.rstrip('\r\n').split('\t')
        rows.append((p[0], int(p[2]), p[1], p[3], p[4]))  # stage, guest, hex, class, tag
    return rows


def main():
    ap = argparse.ArgumentParser()
    for a in ('--run', '--dumps', '--trace', '--targets', '--out'):
        ap.add_argument(a, required=True)
    ap.add_argument('--stage'); ap.add_argument('--fingerprint', default='39129c4c059be5f0')
    a = ap.parse_args()
    if not inside(a.out) or (a.stage and not inside(a.stage)):
        print('REFUSED: --out/--stage must be under ' + HERE); return 2
    try:
        k = ctypes.windll.kernel32; k.SetPriorityClass(k.GetCurrentProcess(), 0x00100000)  # background mode
    except Exception:  # noqa
        pass
    out, bad = [], []
    out.append(f'dump_post_story.py sha256 {sha(os.path.abspath(__file__))}')
    out.append(f'targets {a.targets} sha256 {sha(a.targets)}')
    # 1. run + game.log
    rj = os.path.join(a.run, 'run.json')
    if os.path.exists(rj):
        j = json.load(open(rj, encoding='utf-8-sig'))
        out.append('run.json ' + str({x: j.get(x) for x in ('mode', 'desktop', 'exit_code', 'exited_early', 'crashed') if x in j}))
        if j.get('crashed') or j.get('exited_early'):
            bad.append('run crashed or exited early')
    else:
        bad.append('no run.json'); out.append('run.json missing')
    gl = os.path.join(a.run, 'game.log'); fp = mc_off = False; dumped = 0
    if os.path.exists(gl):
        for line in open(gl, encoding='utf-8', errors='replace'):
            if a.fingerprint in line: fp = True
            if 'shader miss cache OFF' in line and 'LEGO_DUMP_MISSING_SHADERS' in line: mc_off = True
            if 'dumped missing shader' in line: dumped += 1
        out.append(f'game.log: fingerprint {a.fingerprint} {"seen" if fp else "NOT seen"}; dump mode line '
                   f'{"seen" if mc_off else "NOT seen"}; "dumped missing shader" {dumped} lines')
        if not fp: bad.append('fingerprint not seen (wrong bin?)')
        if not mc_off: bad.append('dump mode line missing (env not applied?)')
    else:
        bad.append('no game.log'); out.append('game.log missing')
    # 2. dumps
    attract = set(os.listdir(ATTRACT)) if os.path.isdir(ATTRACT) else set()
    files = collections.Counter(); new = []
    if os.path.isdir(a.dumps):
        for root, _, fns in os.walk(a.dumps):
            cat = os.path.relpath(root, a.dumps); cat = 'root' if cat == '.' else cat.replace('\\', '/')
            for fn in sorted(fns):
                p = os.path.join(root, fn); h = sha(p); files[cat] += 1
                tag = 'IN-ATTRACT-INPUT' if fn in attract else 'NEW'
                out.append(f'dump {cat}/{fn} {os.path.getsize(p)} B {h} {tag}')
                if tag == 'NEW' and cat == 'placement-containers':
                    new.append((fn, p, h))
        out.append(f'dump files per category {dict(files)}; NEW placement containers {len(new)}')
    else:
        bad.append('no dump dir'); out.append(f'dump root {a.dumps} missing')
    # 3. trace
    ev = os.path.join(a.trace, 'events.tsv'); ident = {}; missed = collections.Counter()
    if os.path.exists(ev):
        with open(ev, 'rb') as f:
            for l in f:
                p = l.split(b'\t', 5)
                if len(p) < 5: continue
                e = p[2]
                if e not in (b'missing_placement_shader_identity', b'draw_missing_vertex_shader',
                             b'draw_missing_pixel_shader', b'unrecognized_shader'):
                    continue
                det = p[4].decode('ascii', 'replace'); m = GRE.search(det)
                if not m: continue
                g = int(m.group(1))
                if e == b'draw_missing_vertex_shader': st = 'VS'
                elif e == b'draw_missing_pixel_shader': st = 'PS'
                else:
                    sm = SRE.search(det); st = STAGE.get(sm.group(1) if sm else '', '?')
                if e == b'missing_placement_shader_identity':
                    c = CRE.search(det)
                    ident.setdefault((st, g), []).append(f'{int(c.group(1)):016X}' if c else '?')
                else:
                    missed[(st, g)] += 1
        n_id = sum(len(v) for v in ident.values())
        out.append(f'trace: identity events {n_id} ({len(ident)} stage+guest); missed stage+guest {len(missed)}')
        if n_id >= CAP:
            out.append(f'WARNING: {CAP}-container cap reached; misses after the cap were not dumped')
        if n_id == 0: bad.append('no identity events')
        lost = [(s, g, c) for (s, g), cs in ident.items() for c in cs
                if not os.path.exists(os.path.join(a.dumps, 'placement-containers', f'{s.lower()}-{c}.bin'))]
        out.append(f'identity events without a placement-containers file: {len(lost)}')
    else:
        bad.append('no trace events.tsv'); out.append(f'trace {ev} missing')
    # 4. targets
    tg = load_targets(a.targets); res = collections.Counter(); seen = set()
    out.append(f'\ntarget hit list ({len(tg)} rows): stage guest class tag RESULT [container_hash]')
    for st, g, hx, cls, tag in tg:
        seen.add((st, g))
        if (st, g) in ident: r = 'DUMPED'; extra = ' ' + ','.join(ident[(st, g)])
        elif (st, g) in missed: r = 'MISSING-NO-IDENTITY'; extra = f' (missed x{missed[(st, g)]})'
        else: r = 'NOT-SEEN'; extra = ''
        res[(cls, r)] += 1
        out.append(f'  {st} {hx} {cls} {tag} {r}{extra}')
    out.append('target summary ' + ', '.join(f'{c}/{r} {n}' for (c, r), n in sorted(res.items())))
    untarget = sorted(k for k in ident if k not in seen)
    out.append(f'identity events for guests NOT in the target list: {len(untarget)}')
    for st, g in untarget:
        out.append(f'  {st} {g & 0xFFFFFFFF:08X} {",".join(ident[(st, g)])}')
    # stage
    if a.stage and new:
        os.makedirs(a.stage, exist_ok=True); sums = []
        for fn, p, h in new:
            dst = os.path.join(a.stage, fn)
            if os.path.exists(dst) and sha(dst) != h:
                out.append(f'STAGE REFUSED {dst}: exists with different bytes'); bad.append('stage clash'); continue
            if not os.path.exists(dst): shutil.copyfile(p, dst)
            sums.append(f'{h}  {fn}  (placement-containers)')
        open(os.path.join(a.stage, 'SHA256SUMS.txt'), 'w', encoding='ascii', newline='\r\n').write('\n'.join(sums) + '\n')
        out.append(f'staged {len(sums)} NEW placement containers into {a.stage}')
    out.append('RESULT: ' + ('USABLE' if not bad else 'CHECK: ' + '; '.join(bad)) + f' ({len(new)} new placement containers)')
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, 'w', encoding='utf-8', newline='\r\n').write('\n'.join(out) + '\n')
    print('\n'.join(out[-12:]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
