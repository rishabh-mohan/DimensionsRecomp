#!/usr/bin/env python3
"""Run gradient_compiler over shard input dirs, N at a time, each process pinned to its own CPU (Agent 6 / subagent A).

Each shard: XENOS_RECOMP_DXIL_ONLY=1, XENOS_RECOMP_HLSL_DUMP=<out>/shardNN/hlsl-dump,
            gradient_compiler <shards>/shardNN <out>/shardNN/lego-dxil-cache.cpp <shader_common.h>
The process is created suspended, its affinity set to exactly one CPU (SetProcessAffinityMask), then resumed, so it
never runs elsewhere. A shard is complete when <out>/shardNN/done.json exists; it is written only after the process
exited 0 (all OK) or 2 (some recompile failures; partial cache written). Re-running the driver skips complete shards
and restarts incomplete ones from scratch (their out dir is wiped first) -> a kill at any moment loses only in-flight
shards.

usage: run_shards.py --shards-dir D --out-dir O --exe gradient_compiler.exe --common shader_common.h
                     [--cpus 4-11] [--stop-launch-at HH:MM[:SS]] [--kill-at HH:MM[:SS]] [--only 0,5,7]
"""
import argparse
import ctypes
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
from ctypes import wintypes

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
ntdll = ctypes.WinDLL('ntdll')
k32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
k32.SetProcessAffinityMask.restype = wintypes.BOOL
k32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
k32.GetProcessTimes.restype = wintypes.BOOL
ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
ntdll.NtResumeProcess.restype = ctypes.c_long
CREATE_SUSPENDED = 0x00000004


def cpu_seconds(handle):
    c, e, k, u = (wintypes.FILETIME() for _ in range(4))
    if not k32.GetProcessTimes(handle, ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u)):
        return None
    ft = lambda f: ((f.dwHighDateTime << 32) | f.dwLowDateTime) / 1e7
    return round(ft(k) + ft(u), 2)


def parse_cpus(s):
    out = []
    for part in s.split(','):
        if '-' in part:
            lo, hi = part.split('-')
            out.extend(range(int(lo), int(hi) + 1))
        else:
            out.append(int(part))
    return out


def at_today(hhmm):
    if not hhmm:
        return None
    parts = [int(x) for x in hhmm.split(':')]
    while len(parts) < 3:
        parts.append(0)
    now = dt.datetime.now()
    return now.replace(hour=parts[0], minute=parts[1], second=parts[2], microsecond=0)


def now_s():
    return dt.datetime.now().strftime('%H:%M:%S')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--shards-dir', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--exe', required=True)
    ap.add_argument('--common', required=True)
    ap.add_argument('--cpus', default='4-11')
    ap.add_argument('--stop-launch-at')
    ap.add_argument('--kill-at')
    ap.add_argument('--only')
    a = ap.parse_args()
    shards_dir = os.path.abspath(a.shards_dir)
    out_dir = os.path.abspath(a.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    cpus = parse_cpus(a.cpus)
    stop_launch = at_today(a.stop_launch_at)
    kill_at = at_today(a.kill_at)
    names = sorted(n for n in os.listdir(shards_dir) if re.fullmatch(r'shard\d+', n))
    if a.only:
        keep = {int(x) for x in a.only.split(',')}
        names = [n for n in names if int(n[5:]) in keep]
    pending = [n for n in names if not os.path.exists(os.path.join(out_dir, n, 'done.json'))]
    skipped = [n for n in names if n not in pending]
    log_path = os.path.join(out_dir, 'driver.log')
    log = open(log_path, 'a', encoding='utf-8', buffering=1)

    def say(msg):
        line = f'[{now_s()}] {msg}'
        print(line, flush=True)
        log.write(line + '\n')

    say(f'start: {len(names)} shards, {len(skipped)} already complete, {len(pending)} to run, cpus={cpus}, '
        f'stop_launch_at={a.stop_launch_at} kill_at={a.kill_at}')
    free = list(cpus)
    running = {}  # name -> dict
    finished, failed, killed = [], [], []
    t_start = time.time()

    def write_status():
        st = {'time': now_s(), 'complete': sorted(skipped + finished), 'failed': failed, 'killed': killed,
              'running': {n: {'cpu': r['cpu'], 'pid': r['proc'].pid, 'started': r['started']}
                          for n, r in running.items()},
              'pending': pending}
        tmp = os.path.join(out_dir, 'status.json.tmp')
        with open(tmp, 'w', encoding='utf-8') as fh:
            json.dump(st, fh, indent=1)
        os.replace(tmp, os.path.join(out_dir, 'status.json'))

    while pending or running:
        now = dt.datetime.now()
        if kill_at and now >= kill_at and running:
            for n, r in list(running.items()):
                r['proc'].kill()
                r['proc'].wait()
                r['fo'].close()
                r['fe'].close()
                killed.append(n)
                say(f'KILLED {n} on cpu {r["cpu"]} (kill-at {a.kill_at})')
                del running[n]
            break
        # reap
        for n, r in list(running.items()):
            rc = r['proc'].poll()
            if rc is None:
                continue
            cpu_s = cpu_seconds(int(r['proc']._handle))
            r['fo'].close()
            r['fe'].close()
            wall = round(time.time() - r['t0'], 2)
            d = os.path.join(out_dir, n)
            cpp = os.path.join(d, 'lego-dxil-cache.cpp')
            stdout = open(os.path.join(d, 'stdout.log'), encoding='utf-8', errors='replace').read()
            stderr = open(os.path.join(d, 'stderr.log'), encoding='utf-8', errors='replace').read()
            cov = re.search(r'AOT coverage: (\d+) of (\d+)', stdout)
            fail = re.search(r'Recompile failures: (\d+) of (\d+)', stderr)
            info = {'shard': n, 'exit': rc, 'cpu': r['cpu'], 'wall_s': wall, 'cpu_s': cpu_s,
                    'inputs': r['inputs'], 'started': r['started'], 'ended': now_s(),
                    'compiled': int(cov[1]) if cov else 0, 'discovered': int(cov[2]) if cov else None,
                    'failures': int(fail[1]) if fail else 0, 'output': os.path.exists(cpp),
                    'output_bytes': os.path.getsize(cpp) if os.path.exists(cpp) else 0}
            if rc in (0, 2) and (os.path.exists(cpp) or (cov and int(cov[1]) == 0)):
                with open(os.path.join(d, 'done.json'), 'w', encoding='utf-8') as fh:
                    json.dump(info, fh, indent=1)
                finished.append(n)
                say(f'done {n} exit={rc} compiled={info["compiled"]}/{info["discovered"]} failures={info["failures"]} '
                    f'wall={wall}s cpu={cpu_s}s cpu#{r["cpu"]}')
            else:
                failed.append(info)
                say(f'FAILED {n} exit={rc} (no done.json) wall={wall}s')
            free.append(r['cpu'])
            del running[n]
        # launch
        while pending and free and not (stop_launch and dt.datetime.now() >= stop_launch):
            n = pending.pop(0)
            cpu = free.pop(0)
            d = os.path.join(out_dir, n)
            if os.path.exists(d):
                shutil.rmtree(d)
            os.makedirs(os.path.join(d, 'hlsl-dump'))
            inp = os.path.join(shards_dir, n)
            env = dict(os.environ, XENOS_RECOMP_DXIL_ONLY='1', XENOS_RECOMP_HLSL_DUMP=os.path.join(d, 'hlsl-dump'))
            env.pop('XENOS_RECOMP_ONLY_HASH', None)
            fo = open(os.path.join(d, 'stdout.log'), 'wb')
            fe = open(os.path.join(d, 'stderr.log'), 'wb')
            p = subprocess.Popen([a.exe, inp, os.path.join(d, 'lego-dxil-cache.cpp'), a.common], cwd=d, env=env,
                                 stdout=fo, stderr=fe, stdin=subprocess.DEVNULL, creationflags=CREATE_SUSPENDED)
            h = int(p._handle)
            if not k32.SetProcessAffinityMask(h, 1 << cpu):
                p.kill()
                raise SystemExit(f'SetProcessAffinityMask failed for {n}: {ctypes.get_last_error()}')
            if ntdll.NtResumeProcess(h) != 0:
                p.kill()
                raise SystemExit(f'NtResumeProcess failed for {n}')
            running[n] = {'proc': p, 'cpu': cpu, 't0': time.time(), 'started': now_s(), 'fo': fo, 'fe': fe,
                          'inputs': len(os.listdir(inp))}
            say(f'launch {n} on cpu {cpu} (mask 0x{1 << cpu:X}) pid={p.pid} inputs={running[n]["inputs"]}')
        if stop_launch and dt.datetime.now() >= stop_launch and pending and not running:
            say(f'stop-launch time {a.stop_launch_at} reached with {len(pending)} shards not started')
            break
        write_status()
        time.sleep(1.0)
    write_status()
    complete = sorted(skipped + finished)
    say(f'end: complete={len(complete)}/{len(names)} finished_now={len(finished)} failed={len(failed)} '
        f'killed={killed} not_started={pending} elapsed={round(time.time() - t_start, 1)}s')
    return 0 if len(complete) == len(names) else 1


if __name__ == '__main__':
    sys.exit(main())
