"""Build and run the bench/agent4 microbenches.

clang++ -std=c++20 -O2 -march=x86-64-v3 (the shipped baseline), one compile at a time. Each bench
executable runs --runs times (default 5) as separate processes; each run prints the median of 9
interleaved reps per case. Reported: the median of the run medians and their min..max.
Usage (devshell): python bench/agent4/run_benches.py [--tree DimensionsRecomp] [--runs 5] [bench ...]
Writes build/agent4/bench/results.json and results.md.
"""
import argparse
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BENCHES = {
    'log_throttle': ['log_throttle_bench.cpp'],
    'cached_flag': ['cached_flag_bench.cpp', 'flag_tu.cpp', 'old_composite.cpp', 'new_composite.cpp'],
    'tls_accessor': ['tls_accessor_bench.cpp', 'tls_tu.cpp'],
    'query_scope': ['query_scope_bench.cpp'],
    'registry_lookup': ['registry_lookup_bench.cpp'],
}
FLAG_VARS = ['LEGO_NATIVE_TIMING', 'LEGO_NATIVE_TRACE_DIR', 'LEGO_NATIVE_PORTRAIT_TRACE']


def cpu_load() -> str:
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command',
                            '(Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage '
                            '-Average).Average'], capture_output=True, text=True, timeout=60)
        return r.stdout.strip() or 'n/a'
    except Exception as error:  # diagnostics only
        return f'n/a ({error})'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--tree', default=str(ROOT / 'DimensionsRecomp'))
    parser.add_argument('--runs', type=int, default=5)
    parser.add_argument('--out', default=str(ROOT / 'build/agent4/bench'))
    parser.add_argument('benches', nargs='*')
    args = parser.parse_args()
    tree, out = Path(args.tree).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k not in FLAG_VARS}
    include = tree / 'rexlego/src/gpu_native'
    results = {'tree': str(tree), 'runs': args.runs, 'cpu_load_before': cpu_load(), 'benches': {}}
    for name in args.benches or list(BENCHES):
        exe = out / f'{name}.exe'
        cmd = ['clang++', '-std=c++20', '-O2', '-march=x86-64-v3', '-D_CRT_SECURE_NO_WARNINGS',
               f'-I{HERE}', f'-I{include}', *[str(HERE / s) for s in BENCHES[name]], '-o', str(exe)]
        print('$', ' '.join(cmd), flush=True)
        subprocess.run(cmd, check=True)
        if name == 'cached_flag':
            on = dict(env, LEGO_NATIVE_TIMING='1', LEGO_NATIVE_TRACE_DIR=str(out / 'unused-trace-dir'),
                      LEGO_NATIVE_PORTRAIT_TRACE='1')
            r = subprocess.run([str(exe), '--expect-on'], env=on, capture_output=True, text=True)
            print(r.stdout.strip(), r.stderr.strip(), flush=True)
            if r.returncode:
                return f'{name} --expect-on failed'
        per_case: dict[str, list[float]] = {}
        for run in range(args.runs):
            r = subprocess.run([str(exe)], env=env, capture_output=True, text=True)
            if r.returncode:
                print(r.stdout, r.stderr)
                return f'{name} run {run} failed'
            for line in r.stdout.splitlines():
                if line.startswith('RESULT\t'):
                    _, _group, case, median, _low, _high = line.split('\t')
                    per_case.setdefault(case, []).append(float(median))
                elif run == 0:
                    print(line, flush=True)
        results['benches'][name] = {
            case: {'median': statistics.median(v), 'min': min(v), 'max': max(v), 'runs': v}
            for case, v in per_case.items()}
        for case, v in per_case.items():
            print(f'{name:13s} {case:52s} median {statistics.median(v):9.3f} ns '
                  f'(run medians {min(v):.3f}..{max(v):.3f}, n={len(v)})', flush=True)
    results['cpu_load_after'] = cpu_load()
    (out / 'results.json').write_text(json.dumps(results, indent=1))
    lines = ['| bench | case | median ns/op | run medians |', '|---|---|---:|---|']
    for name, cases in results['benches'].items():
        for case, s in cases.items():
            lines.append(f"| {name} | {case} | {s['median']:.3f} | {s['min']:.3f}-{s['max']:.3f} |")
    (out / 'results.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print(f"CPU load {results['cpu_load_before']}% before, {results['cpu_load_after']}% after")
    return 0


if __name__ == '__main__':
    sys.exit(main())
