"""LEGO_NATIVE_ELIDE_STATE_CALLS: opt-in skipping of repeated index buffer / blend factor calls.

Pastes the real draw.cpp helpers (ReadElideStateCalls .. SameDrawBlendFactor) into
bench/agent4/state_shadow_test.cpp at its marker and builds it with clang++ -std=c++20 -O2
-march=x86-64-v3 against the tree's draw_state_shadow.h, draw_cached_flag.h and
state_call_diagnostic.h. Then:
  1. unit tests: shadow keys and compares, lookup gates and tripwires, ledger columns, CSV, env parse;
  2. a randomized oracle, 4 seeds x 300k events (draws, list resets, raw index buffer / blend writes
     followed by notify calls, helper root signatures, draw-layout rebinds, raw compute, external
     SetDescriptorHeaps), with the variable set, unset, and under full preparation;
  3. negative controls: contract violations the oracle must report (exit 3);
  4. mutants of the helpers and of draw_state_shadow.h, each of which must be killed. ignore_serial
     is killed too: after a list reset, a plume bind of the draw layout before the first draw makes
     the tripwire flags valid again, so the recording serial in the key is required;
  5. a static audit of the call sites, of every other index buffer / blend factor writer in
     rexlego/src, of device.cpp's begin/serial and overlay/notify order, and of the plume flags;
  6. the microbench: --runs processes with the variable unset and --runs with it set to 1.
Usage (devshell): python bench/agent4/test_state_shadow.py [--tree T] [--out O] [--runs 5] [--no-bench]
Writes <out>/results.json and <out>/results.md.
"""
import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

from run_benches import cpu_load

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
VAR = 'LEGO_NATIVE_ELIDE_STATE_CALLS'
MARKER = '// @@EXTRACTED@@'
LOOKUP = 'DrawStateShadow* draw_shadow = InlineDrawStateShadow(preparation, commands, draw_device);'
TRIPWIRE = 'if (shadow && (!list->descriptorHeapsSet'
NO_TRIPWIRE = 'if (false && shadow && (!list->descriptorHeapsSet'
SERIAL = 'shadow.state.Begin(commands, view.recording_serial, view.pipeline_layout)'
NO_SERIAL = 'shadow.state.Begin(commands, 0, view.pipeline_layout)'

# name: (edited text, [(old, new)], run arguments, expected exit). Exit 3 = oracle mismatch,
# 1 = unit check failed.
MUTANTS = {
    'no_tripwire': ('draw', [(TRIPWIRE, NO_TRIPWIRE)], ['--oracle'], 3),
    'ignore_serial': ('draw', [(SERIAL, NO_SERIAL)], ['--oracle'], 3),
    'no_tripwire_ignore_serial': ('draw', [(TRIPWIRE, NO_TRIPWIRE), (SERIAL, NO_SERIAL)], ['--oracle'], 3),
    'no_heaps_check': ('draw', [('(!list->descriptorHeapsSet || !list->cachedGraphicsRootValid ||',
                                 '(!list->cachedGraphicsRootValid ||')], ['--oracle'], 3),
    'no_root_signature_check': ('draw', [(
        '!list->cachedGraphicsRootValid ||\n      list->cachedGraphicsRootSignature != '
        'g_inline_state_shadow.root_signature))', '!list->cachedGraphicsRootValid))')], ['--oracle'], 3),
    'full_prep_gate_removed': ('draw', [('CachedProcessFlag<NativeFullDrawPreparationEnabled>()', 'false')],
                               ['--oracle', '--full-prep'], 3),
    'preparation_gate_removed': ('draw', [('|| preparation ||', '||')], ['--unit'], 1),
    'env_parse_loose': ('draw', [("value && value[0] == '1' && !value[1]", "value && value[0] == '1'")],
                        ['--unit'], 1),
    'shadow_ignores_size': ('header', [('index_.address == value.address && index_.size == value.size &&',
                                        'index_.address == value.address &&')], ['--oracle'], 3),
    'shadow_ignores_format': ('header', [('index_.size == value.size &&\n        index_.format == value.format)',
                                          'index_.size == value.size)')], ['--oracle'], 3),
    'blend_float_compare': ('header', [('std::memcmp(blend_.data(), value.data(), sizeof(blend_)) == 0',
                                        'blend_ == value')], ['--oracle'], 3),
    'invalidate_keeps_blend': ('header', [('index_set_ = blend_set_ = false;', 'index_set_ = false;')],
                               ['--oracle'], 3),
    'begin_ignores_layout': ('header', [(' && layout == layout_) return false;', ') return false;')],
                             ['--unit'], 1),
}


def body_end(text: str, start: int) -> int:
    """Index just past the brace-matched body that follows `start`."""
    depth = 0
    for i in range(text.index('{', start), len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError(f'unbalanced braces after {start}')


def function(text: str, signature: str) -> str:
    start = text.index(signature)
    return text[start:body_end(text, start)]


def replace_once(text: str, old: str, new: str, what: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{what}: expected one {old!r}, found {count}')
    return text.replace(old, new)


def code_lines(path: Path):
    for number, line in enumerate(path.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
        yield number, line.split('//', 1)[0]


def writers(src: Path, pattern: str) -> dict[str, list[int]]:
    hits: dict[str, list[int]] = {}
    for path in sorted(src.rglob('*')):
        if path.suffix in ('.cpp', '.h', '.hpp', '.inl', '.cc'):
            for number, code in code_lines(path):
                if re.search(pattern, code):
                    hits.setdefault(path.name, []).append(number)
    return hits


def audit(tree: Path) -> list[tuple[str, bool]]:
    src = tree / 'rexlego/src'
    gpu = src / 'gpu_native'
    draw = (gpu / 'draw.cpp').read_text(encoding='utf-8')
    device = (gpu / 'device.cpp').read_text(encoding='utf-8')
    plume = (tree / 'thirdparty/plume/plume_d3d12.cpp').read_text(encoding='utf-8')
    checks: list[tuple[str, bool]] = []

    def check(what: str, ok: bool) -> None:
        checks.append((what, bool(ok)))

    dispatch = function(draw, 'bool DispatchDraw(D3DDevice* device,')
    check('draw.cpp: one shadow lookup, inside DispatchDraw',
          draw.count(LOOKUP) == 1 and dispatch.count(LOOKUP) == 1)
    check('DispatchDraw: the lookup precedes its first BindNativeDrawLayout (plume flags still unrevalidated)',
          LOOKUP in dispatch and dispatch.index(LOOKUP) < dispatch.find('BindNativeDrawLayout('))
    blend_guard = r'if \(!SameDrawBlendFactor\(draw_shadow, state_calls, recorded_blend\)\)\s*\n\s*' \
                  r'SetNativeBlendFactor\(commands, recorded_blend\);'
    check('draw.cpp: the only SetNativeBlendFactor call is guarded by SameDrawBlendFactor',
          draw.count('SetNativeBlendFactor(') == 1 and len(re.findall(blend_guard, dispatch)) == 1)
    index_guard = r'if \(!SameDrawIndexBuffer\(draw_shadow, state_calls, index_view\)\)\s*\n\s*' \
                  r'commands->setIndexBuffer\(&index_view\);'
    check('draw.cpp: both setIndexBuffer calls are guarded by SameDrawIndexBuffer',
          draw.count('setIndexBuffer(') == 2 and len(re.findall(index_guard, dispatch)) == 2)

    found = writers(src, r'setIndexBuffer\(')
    check(f'rexlego/src setIndexBuffer( = draw.cpp x2 + native_recording.cpp tape: {found}',
          set(found) == {'draw.cpp', 'native_recording.cpp'} and len(found['draw.cpp']) == 2)
    found = writers(src, r'IASetIndexBuffer')
    check(f'rexlego/src raw IASetIndexBuffer = native overlay only: {found}', set(found) == {'native_overlay_gpu.cpp'})
    found = writers(src, r'OMSetBlendFactor')
    check(f'rexlego/src OMSetBlendFactor = native_recording.cpp (tape replay, SetNativeBlendFactor): {found}',
          set(found) == {'native_recording.cpp'} and len(found['native_recording.cpp']) == 2)
    found = writers(src, r'SetNativeBlendFactor\(')
    check(f'rexlego/src SetNativeBlendFactor( = draw.cpp call + native_recording declaration/definition: {found}',
          set(found) == {'draw.cpp', 'native_recording.cpp', 'native_recording.h'} and len(found['draw.cpp']) == 1)
    found = writers(src, r'\b(ClearState|ExecuteBundle|ExecuteIndirect)\(')
    check(f'rexlego/src has no ClearState / ExecuteBundle / ExecuteIndirect: {found}', not found)
    found = writers(src, r'->begin\(\)')
    check(f'rexlego/src ->begin() = device.cpp frame list + native_recording.cpp tape: {found}',
          set(found) == {'device.cpp', 'native_recording.cpp'} and all(len(v) == 1 for v in found.values()))

    begin = device.find('commands->begin();')
    serial = device.find('++g_recording_serial;', begin)
    check('device.cpp: ++g_recording_serial follows the frame list begin() before it is returned',
          0 <= begin < serial < device.find('return commands;', begin))
    overlay = device.find('RenderNativeOverlays(')
    end = device.find('commands->end();', overlay)
    after = device[overlay:end]
    check('device.cpp: the native overlay is followed by both notify calls, then end(), with no draw between',
          device.count('RenderNativeOverlays(') == 1 and overlay < end and
          'overlay_commands->notifyDescriptorHeapWasChangedExternally();' in after and
          'overlay_commands->notifyCommandStateWasChangedExternally();' in after and
          not re.search(r'DispatchDraw\(|->draw\w*\(', after))

    def body(signature: str) -> str:
        return function(plume, signature)
    check('plume begin() calls notifyCommandStateWasChangedExternally',
          'notifyCommandStateWasChangedExternally();' in body('void D3D12CommandList::begin() {'))
    text = body('void D3D12CommandList::end() {')
    check('plume end() clears descriptorHeapsSet and calls notifyCommandStateWasChangedExternally',
          'descriptorHeapsSet = false;' in text and 'notifyCommandStateWasChangedExternally();' in text)
    check('plume notifyDescriptorHeapWasChangedExternally clears descriptorHeapsSet',
          'descriptorHeapsSet = false;' in body('void D3D12CommandList::notifyDescriptorHeapWasChangedExternally() {'))
    text = body('void D3D12CommandList::notifyCommandStateWasChangedExternally() {')
    check('plume notifyCommandStateWasChangedExternally nulls the graphics root signature and validity',
          'cachedGraphicsRootSignature = nullptr;' in text and 'cachedGraphicsRootValid = false;' in text)
    text = body('void D3D12CommandList::setGraphicsPipelineLayout(')
    check('plume setGraphicsPipelineLayout records the root signature and sets validity',
          'cachedGraphicsRootSignature = interfacePipelineLayout->rootSignature;' in text and
          'cachedGraphicsRootValid = true;' in text)
    check('plume sets cachedGraphicsRootValid / descriptorHeapsSet true in one place each',
          plume.count('cachedGraphicsRootValid = true') == 1 and plume.count('descriptorHeapsSet = true') == 1)
    text = body('void D3D12CommandList::setIndexBuffer(')
    check('plume setIndexBuffer binds (gpuVA + offset or 0, toDXGI(format), size): the shadow key',
          '(interfaceBuffer != nullptr) ? (interfaceBuffer->gpuVA + view->buffer.offset) : 0' in text and
          'bufferView.Format = toDXGI(view->format);' in text and 'bufferView.SizeInBytes = view->size;' in text)
    return checks


def build(out: Path, name: str, helpers: str, header: str | None, include: Path) -> tuple[Path | None, str]:
    work = out / name
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    template = (HERE / 'state_shadow_test.cpp').read_text(encoding='utf-8')
    source = work / 'state_shadow_test.cpp'
    source.write_text(replace_once(template, MARKER, helpers, 'state_shadow_test.cpp'), encoding='utf-8')
    if header is not None:  # found before -I paths: same directory as the including source
        (work / 'draw_state_shadow.h').write_text(header, encoding='utf-8')
    exe = work / 'state_shadow_test.exe'
    cmd = ['clang++', '-std=c++20', '-O2', '-march=x86-64-v3', '-D_CRT_SECURE_NO_WARNINGS',
           f'-I{HERE}', f'-I{include}', str(source), '-o', str(exe)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    (work / 'build.log').write_text(' '.join(cmd) + '\n' + r.stdout + r.stderr, encoding='utf-8')
    return (exe if r.returncode == 0 else None), r.stdout + r.stderr


def run(exe: Path, arguments: list[str], env: dict, log: Path) -> tuple[int, str]:
    r = subprocess.run([str(exe), *arguments], env=env, capture_output=True, text=True, timeout=900)
    log.write_text(r.stdout + r.stderr, encoding='utf-8')
    lines = [line for line in (r.stdout + r.stderr).splitlines() if line.strip()]
    return r.returncode, (lines[-1] if lines else '')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--tree', default=str(ROOT / 'DimensionsRecomp'))
    parser.add_argument('--out', default=str(ROOT / 'build/agent4/state_shadow'))
    parser.add_argument('--runs', type=int, default=5)
    parser.add_argument('--no-bench', action='store_true')
    args = parser.parse_args()
    tree, out = Path(args.tree).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    include = tree / 'rexlego/src/gpu_native'
    draw = (include / 'draw.cpp').read_text(encoding='utf-8')
    helpers = draw[draw.index('bool ReadElideStateCalls()'):body_end(draw, draw.index('bool SameDrawBlendFactor('))]
    header = (include / 'draw_state_shadow.h').read_text(encoding='utf-8')
    env_off = {k: v for k, v in os.environ.items() if k != VAR}
    env_on = dict(env_off, **{VAR: '1'})
    results = {'tree': str(tree), 'checks': [], 'audit': [], 'bench': {}}
    failures: list[str] = []

    exe, log = build(out, 'real', helpers, None, include)
    if exe is None:
        print(log)
        return 'build of the real helpers failed'
    print(f'built {exe}')
    cases = [
        ('unit', ['--unit', str(out / 'real' / 'unit')], 'on', 0),
        ('oracle elision', ['--oracle', '--expect-elision'], 'on', 0),
        ('oracle variable unset', ['--oracle', '--expect-none'], 'off', 0),
        ('oracle full preparation', ['--oracle', '--full-prep'], 'on', 0),
        ('negative: lookup after the layout bind', ['--oracle', '--check-after-binds'], 'on', 3),
        ('negative: external write without notify', ['--oracle', '--silent-external'], 'on', 3),
        ('negative: draw-layout rebind after external write', ['--oracle', '--rebind-after-external'], 'on', 3),
    ]
    for index, (name, arguments, variable, expected) in enumerate(cases):
        code, last = run(exe, arguments, env_on if variable == 'on' else env_off, out / 'real' / f'case{index}.log')
        ok = code == expected
        results['checks'].append({'build': 'real', 'case': name, 'args': arguments, 'variable': variable,
                                  'expected': expected, 'exit': code, 'last_line': last, 'ok': ok})
        print(f'{"ok  " if ok else "FAIL"} real: {name}: exit {code} (expected {expected}) {last}', flush=True)
        if not ok:
            failures.append(f'real {name}')

    for name, (target, edits, arguments, expected) in MUTANTS.items():
        mutated_helpers, mutated_header = helpers, None
        for old, new in edits:
            if target == 'draw':
                mutated_helpers = replace_once(mutated_helpers, old, new, name)
            else:
                mutated_header = replace_once(mutated_header or header, old, new, name)
        mutant_exe, log = build(out, f'mutant-{name}', mutated_helpers, mutated_header, include)
        if mutant_exe is None:
            print(log)
            failures.append(f'mutant {name} did not build')
            continue
        if arguments[0] == '--unit':
            arguments = ['--unit', str(out / f'mutant-{name}' / 'unit')]
        code, last = run(mutant_exe, arguments, env_on, out / f'mutant-{name}' / 'run.log')
        ok = code == expected
        verdict = ('killed' if code else 'survived') + ('' if ok else ' (UNEXPECTED)')
        results['checks'].append({'build': f'mutant {name}', 'case': ' '.join(arguments[:1] + arguments[2:]),
                                  'args': arguments, 'variable': 'on', 'expected': expected, 'exit': code,
                                  'last_line': last, 'ok': ok})
        print(f'{"ok  " if ok else "FAIL"} mutant {name}: {verdict}, exit {code} (expected {expected}) {last}',
              flush=True)
        if not ok:
            failures.append(f'mutant {name}')

    for what, ok in audit(tree):
        results['audit'].append({'check': what, 'ok': ok})
        print(f'{"ok  " if ok else "FAIL"} audit: {what}', flush=True)
        if not ok:
            failures.append(f'audit: {what}')

    if not args.no_bench:
        results['cpu_load_before'] = cpu_load()
        for label, env in (('off', env_off), ('on', env_on)):
            per_case: dict[str, list[float]] = {}
            for index in range(args.runs):
                code, _ = run(exe, ['--bench', label], env, out / 'real' / f'bench-{label}-{index}.log')
                if code:
                    failures.append(f'bench {label} run {index} exit {code}')
                    break
                for line in (out / 'real' / f'bench-{label}-{index}.log').read_text().splitlines():
                    if line.startswith('RESULT\t'):
                        _, _group, case, median, _low, _high = line.split('\t')
                        per_case.setdefault(case, []).append(float(median))
            results['bench'][label] = {case: {'median': statistics.median(v), 'min': min(v), 'max': max(v),
                                              'runs': v} for case, v in per_case.items()}
            for case, v in per_case.items():
                print(f'bench {VAR}={"1" if label == "on" else "unset"} {case:22s} median {statistics.median(v):8.3f}'
                      f' ns/draw (run medians {min(v):.3f}..{max(v):.3f}, n={len(v)})', flush=True)
        results['cpu_load_after'] = cpu_load()

    results['failures'] = failures
    (out / 'results.json').write_text(json.dumps(results, indent=1), encoding='utf-8')
    lines = ['| build | case | expected exit | exit | ok |', '|---|---|---:|---:|---|']
    lines += [f"| {c['build']} | {c['case']} | {c['expected']} | {c['exit']} | {'yes' if c['ok'] else 'NO'} |"
              for c in results['checks']]
    lines += ['', '| audit | ok |', '|---|---|']
    lines += [f"| {a['check'].replace('|', '/')} | {'yes' if a['ok'] else 'NO'} |" for a in results['audit']]
    if results['bench']:
        lines += ['', f'| {VAR} | case | median ns/draw | run medians |', '|---|---|---:|---|']
        for label, bench in results['bench'].items():
            for case, s in bench.items():
                lines.append(f"| {'1' if label == 'on' else 'unset'} | {case} | {s['median']:.3f} | "
                             f"{s['min']:.3f}-{s['max']:.3f} |")
        lines.append(f"\nCPU load {results['cpu_load_before']}% before, {results['cpu_load_after']}% after")
    (out / 'results.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    if failures:
        print('FAILED: ' + '; '.join(failures))
        return 1
    print(f'test_state_shadow: OK ({len(results["checks"])} runs, {len(results["audit"])} audit checks)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
