"""Run gpu-aot portable fixtures against one source tree, one at a time (CPU is shared).

Usage (devshell, so clang++ is on PATH):
  python bench/agent4/run_fixtures.py <tree-root> <out-dir> [test.py ...]
<tree-root> is a DimensionsRecomp checkout (dev tree or baseline/DimensionsRecomp).
Writes <out-dir>/results.json and prints one PASS/FAIL line per fixture.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

DEFAULT = [
    'test_long_probe.py', 'test_query_retirement.py', 'test_query_sample_pool.py',
    'test_constant_timing.py', 'test_binding_caches.py', 'test_cull_state.py',
    'test_shader_binding_failures.py', 'test_draw_index_bounds.py',
    'test_nonindexed_buffer_windows.py', 'test_quad_buffer_windows.py',
    'test_preparation_metadata.py', 'test_portrait_probe.py', 'test_frame_cadence.py',
    'test_snapshot_selection.py', 'test_temporal_draw_route.py', 'test_buffer_variants.py',
    'test_buffer_view_generation.py', 'test_draw_upload.py', 'test_frame_ring_transaction.py',
    'test_submission_waits.py', 'test_texture_authority_probe.py',
    'test_texture_binding_failures.py', 'test_texture_depth_upload.py', 'test_texture_prepare.py',
    'test_texture_source_residency.py', 'test_texture_use_refresh.py',
]


def main() -> int:
    tree = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve()
    tests = sys.argv[3:] or DEFAULT
    out.mkdir(parents=True, exist_ok=True)
    results = {}
    for name in tests:
        script = tree / 'tools/gpu-aot' / name
        work = out / name.removesuffix('.py')
        if work.exists():
            # Some fixtures insist on a fresh output directory.
            for p in sorted(work.rglob('*'), reverse=True):
                p.unlink() if p.is_file() else p.rmdir()
        start = time.perf_counter()
        try:
            r = subprocess.run([sys.executable, str(script), str(work)], capture_output=True,
                               text=True, timeout=600)
            code, text = r.returncode, (r.stdout + r.stderr)
        except subprocess.TimeoutExpired as e:
            code, text = -999, f'TIMEOUT\n{e.stdout or ""}{e.stderr or ""}'
        seconds = time.perf_counter() - start
        tail = '\n'.join(text.strip().splitlines()[-25:])
        results[name] = {'code': code, 'seconds': round(seconds, 1), 'tail': tail}
        print(f"{'PASS' if code == 0 else 'FAIL'} {name} ({seconds:.1f}s)"
              + ('' if code == 0 else f" rc={code}: {tail.splitlines()[-1] if tail else ''}"),
              flush=True)
    (out / 'results.json').write_text(json.dumps(results, indent=1))
    failed = [n for n, r in results.items() if r['code'] != 0]
    print(f'{len(results) - len(failed)}/{len(results)} passed; failed: {failed}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
