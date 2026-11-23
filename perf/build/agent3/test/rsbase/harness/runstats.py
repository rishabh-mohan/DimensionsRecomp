#!/usr/bin/env python3
"""Summarises Dimensions Recompiled harness runs: game.log markers and frames.csv frame times.

  runstats.py RUN_DIR [--warmup S] [--write]   one run; --write saves summary.json + summary.txt
  runstats.py --aggregate RUN_DIR...          medians across runs (the measuring rule is >= 5 runs
                                              on the same machine, noting what else was running)

Inputs in RUN_DIR (written by harness/run-game.ps1):
  run.json    what the harness did: command line, env, exit code, how the game was closed,
              crash events, dumps, screenshots, process CPU/memory samples
  game*.log   the --log_file log: "[time] [level] [category] [tid] message"
  frames.csv  LEGO_NATIVE_FRAME_METRICS, one row per present (rexlego/src/gpu_native/device.cpp)
  perf.csv    --perf_log_csv, one row per guest swap (rexglue-sdk/src/core/perf/counter.cpp); the only
              frame series the emulated-GPU (NATIVE_GPU=OFF) baseline writes
  samples.csv the harness's 1 s process samples; the file sizes give the first frame to within ~1-2 s
  gpu.csv     run-game.ps1 -GpuLog: NVML GPU state once per sample (pstate, clocks, temperature, power,
              utilization, clock-limit reasons), summarised from the first frame + --warmup

interval_ms in frames.csv is the wall time between two consecutive presents. That is the frame
time a player sees, whatever the bottleneck is (guest CPU code, GPU, or present pacing).
frame_time_us in perf.csv is the wall time between guest swaps. Both start at the first frame, so
--warmup counts from the first frame, not from launch.
"""
import argparse
import csv
import glob
import json
import os
import re
import statistics
import sys
from datetime import datetime

LOG_LINE = re.compile(r"^\[(?P<ts>\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\] \[(?P<level>\w+)\] "
                      r"\[(?P<cat>[^\]]*)\] (?:\[t(?P<tid>\d+)\] )?(?P<msg>.*)$")
MARKERS = {
    "xex_patch": re.compile(r"XEX patch applied successfully: base version: (?P<base>[\d.]+), "
                            r"new version: (?P<new>[\d.]+)"),
    "module_launch": re.compile(r"Startup: launching the module"),
    "gpu_caps": re.compile(r"Native GPU capabilities: (?P<caps>.*\buma=(?P<uma>\w+).*)"),
    "swap_chain": re.compile(r"Native GPU init: swap chain ready \(vsync (?P<vsync>\w+)\)"),
    "gpu_ready": re.compile(r"Native GPU \[(?P<fingerprint>[^\]]*)\]: (?P<backend>\S+) ready on "
                            r"'(?P<adapter>[^']*)' \((?P<width>\d+)x(?P<height>\d+), (?P<images>\d+) images\)"),
    "fps_cap_override": re.compile(r"presentation cap override=(?P<value>-?\d+)"),
    "config_saved": re.compile(r"Saved config to (?P<path>.*)"),
    # Emulated-GPU (NATIVE_GPU=OFF) builds:
    "dxgi_adapter": re.compile(r"DXGI adapter: (?P<adapter>.*?)(?: \(vendor (?P<vendor>0x[0-9A-Fa-f]+), "
                               r"device (?P<device>0x[0-9A-Fa-f]+), (?P<vram_mb>\d+) MB dedicated\))?$"),
    "shader_storage": re.compile(r"Initializing shader storage"),
}
MISSING = re.compile(r"MISSING-FUNCTION 0x(?P<addr>[0-9A-Fa-f]{8})")
UNKNOWN_CVAR = re.compile(r"Config: unknown cvar '(?P<name>[^']*)'")
BAD_LEVELS = ("error", "critical")


def pct(sorted_vals, p):
    """Linear-interpolated percentile of an already sorted list."""
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * p / 100.0
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def r(x, nd=2):
    return None if x is None else round(x, nd)


def ri(x):
    return None if x is None else int(round(x))


def scan_log(run):
    files = sorted(glob.glob(os.path.join(run, "game*.log")), key=os.path.getmtime)
    out = dict(files=[os.path.basename(f) for f in files], lines=0, levels={}, markers={},
               errors=[], missing_functions=0, unknown_cvars=[], first_ts=None, last_ts=None)
    missing, unknown, t0 = set(), [], None
    for path in files:
        with open(path, encoding="utf-8", errors="replace") as f:
            for raw in f:
                out["lines"] += 1
                m = LOG_LINE.match(raw.rstrip("\r\n"))
                if not m:
                    continue
                level, msg = m["level"].lower(), m["msg"]
                out["levels"][level] = out["levels"].get(level, 0) + 1
                try:
                    ts = datetime.strptime(m["ts"], "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    ts = None
                if ts and t0 is None:
                    t0 = ts
                    out["first_ts"] = m["ts"]
                if ts:
                    out["last_ts"] = m["ts"]
                at = r((ts - t0).total_seconds(), 2) if ts and t0 else None
                for name, rx in MARKERS.items():
                    if name in out["markers"]:
                        continue
                    mm = rx.search(msg)
                    if mm:
                        out["markers"][name] = dict(at_s=at, **{k: v for k, v in mm.groupdict().items()})
                mm = MISSING.search(msg)
                if mm:
                    missing.add(mm["addr"].upper())
                mm = UNKNOWN_CVAR.search(msg)
                if mm and mm["name"] not in unknown:
                    unknown.append(mm["name"])
                if level in BAD_LEVELS and len(out["errors"]) < 12:
                    out["errors"].append(f"{at}s [{level}] {msg[:300]}")
    out["missing_functions"] = len(missing)
    out["unknown_cvars"] = unknown
    if t0 and out["last_ts"]:
        out["duration_s"] = r((datetime.strptime(out["last_ts"], "%Y-%m-%d %H:%M:%S.%f") - t0).total_seconds())
    return out


def num(row, key, cast=float):
    v = row.get(key)
    if v in (None, ""):
        return None
    try:
        return cast(v)
    except ValueError:
        try:
            return cast(float(v))
        except ValueError:
            return None


def frame_stats(run, warmup_s):
    path = os.path.join(run, "frames.csv")
    if not os.path.isfile(path):
        return None
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        rows = [row for row in csv.DictReader(f) if row.get("interval_ms") not in (None, "")]
    iv = [num(row, "interval_ms") or 0.0 for row in rows]
    out = dict(frames_total=len(iv), seconds_total=r(sum(iv) / 1000.0), warmup_s=warmup_s)
    if not iv:
        return out
    t, start = 0.0, len(iv)
    for i, v in enumerate(iv):
        if t >= warmup_s * 1000.0:
            start = i
            break
        t += v
    body, body_rows = iv[start:], rows[start:]
    timeline, acc, win = [], [], 0.0
    for v in iv:
        acc.append(v)
        win += v
        if win >= 10000.0:
            timeline.append(r(1000.0 * len(acc) / win, 1))
            acc, win = [], 0.0
    out["fps_per_10s"] = timeline
    pcs = [num(x, "pipeline_creations", int) or 0 for x in rows]
    pcms = [num(x, "pipeline_creation_ms") or 0.0 for x in rows]
    out["pipeline_creations"] = sum(pcs)
    out["pipeline_creation_ms"] = r(sum(pcms), 1)
    last = rows[-1]
    out["last"] = {k: last.get(k) for k in (
        "scene_render_width", "scene_render_height", "output_width", "output_height", "native_vsync",
        "native_fps_limit_cvar", "fsr_enabled", "spatial_fsr_presented", "presentation_borderless",
        "presentation_refresh_hz") if k in last}
    if not body:
        out["frames_measured"] = 0
        return out
    s = sorted(body)
    total = sum(body)
    focused = [num(x, "presentation_focused", int) for x in body_rows]
    focused = [x for x in focused if x is not None]
    draws = sorted(num(x, "draw_calls", int) or 0 for x in body_rows)
    sync_ms = sorted(num(x, "sync_ms") or 0.0 for x in body_rows)
    out.update(
        frames_measured=len(body), seconds_measured=r(total / 1000.0),
        mean_ms=r(total / len(body), 3), median_ms=r(pct(s, 50), 3), p90_ms=r(pct(s, 90), 3),
        p95_ms=r(pct(s, 95), 3), p99_ms=r(pct(s, 99), 3), max_ms=r(s[-1], 3), min_ms=r(s[0], 3),
        stdev_ms=r(statistics.pstdev(body), 3),
        fps_mean=r(1000.0 * len(body) / total, 2), fps_median=r(1000.0 / pct(s, 50), 2) if pct(s, 50) else None,
        fps_1pct_low=r(1000.0 / pct(s, 99), 2) if pct(s, 99) else None,
        hitches_over_50ms=sum(1 for v in body if v > 50.0), hitches_over_100ms=sum(1 for v in body if v > 100.0),
        draw_calls_median=pct(draws, 50), sync_ms_median=r(pct(sync_ms, 50), 3),
        focused_share=r(sum(focused) / len(focused), 3) if focused else None,
        pipeline_creations_measured=sum(pcs[start:]),
    )
    return out


def perf_stats(run, warmup_s):
    """perf.csv (--perf_log_csv): one row per guest swap, frame_time_us = wall time between swaps.

    The file starts at the first guest frame, so the warm-up counts from the first frame (not from
    launch). The game flushes it every 60 rows, so the last <60 frames may be missing after a kill.
    """
    path = os.path.join(run, "perf.csv")
    if not os.path.isfile(path):
        return None
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        rows = [row for row in csv.DictReader(f) if (num(row, "frame_time_us") or 0) > 0]
    iv = [num(row, "frame_time_us") / 1000.0 for row in rows]
    out = dict(source="perf.csv", frames_total=len(iv), seconds_total=r(sum(iv) / 1000.0), warmup_s=warmup_s,
               bytes=os.path.getsize(path))
    if not iv:
        return out
    t, start = 0.0, len(iv)
    for i, v in enumerate(iv):
        if t >= warmup_s * 1000.0:
            start = i
            break
        t += v
    fps_tl, draws_tl, verts_tl, acc, dacc, vacc, win = [], [], [], 0, [], [], 0.0
    for v, row in zip(iv, rows):
        acc += 1
        win += v
        dacc.append(num(row, "draw_calls", int) or 0)
        vacc.append(num(row, "vertices_processed", int) or 0)
        if win >= 10000.0:
            fps_tl.append(r(1000.0 * acc / win, 1))
            draws_tl.append(int(statistics.median(dacc)))
            verts_tl.append(int(statistics.median(vacc)))
            acc, dacc, vacc, win = 0, [], [], 0.0
    out["fps_per_10s"], out["draws_per_10s"], out["vertices_per_10s"] = fps_tl, draws_tl, verts_tl
    for k in ("pipeline_cache_misses", "texture_cache_misses", "command_buffer_stalls"):
        out[k] = sum(num(x, k, int) or 0 for x in rows)
    body, body_rows = iv[start:], rows[start:]
    if not body:
        out["frames_measured"] = 0
        return out
    s, total = sorted(body), sum(body)
    draws = sorted(num(x, "draw_calls", int) or 0 for x in body_rows)
    out.update(
        frames_measured=len(body), seconds_measured=r(total / 1000.0),
        mean_ms=r(total / len(body), 3), median_ms=r(pct(s, 50), 3), p90_ms=r(pct(s, 90), 3),
        p95_ms=r(pct(s, 95), 3), p99_ms=r(pct(s, 99), 3), p999_ms=r(pct(s, 99.9), 3), max_ms=r(s[-1], 3),
        min_ms=r(s[0], 3), stdev_ms=r(statistics.pstdev(body), 3),
        fps_mean=r(1000.0 * len(body) / total, 2), fps_median=r(1000.0 / pct(s, 50), 2) if pct(s, 50) else None,
        fps_1pct_low=r(1000.0 / pct(s, 99), 2) if pct(s, 99) else None,
        hitches_over_50ms=sum(1 for v in body if v > 50.0), hitches_over_100ms=sum(1 for v in body if v > 100.0),
        draw_calls_p10=pct(draws, 10), draw_calls_median=pct(draws, 50), draw_calls_p90=pct(draws, 90),
        pipeline_cache_misses_measured=sum(num(x, "pipeline_cache_misses", int) or 0 for x in body_rows),
    )
    # Scenes: on OFF builds the perf.csv counters change only when the scene changes, not with the attract
    # loop's fast/slow stretches. The intro alternates between two near-identical pairs (218/222 and
    # 219/226, about half each); the title/attract scene sits at 226/1022. Group the measured frames by
    # (draw_calls, vertices_processed), fold each pair into a bigger group within 2 draws and 5 % vertices
    # (at least 8), and drop scenes under max(30 frames, 2 %). Only the 200 biggest pairs are folded, so
    # counters that change every frame (gameplay) stay cheap and simply give no scene lines.
    groups = {}
    for v, row in zip(body, body_rows):
        groups.setdefault((num(row, "draw_calls", int) or 0, num(row, "vertices_processed", int) or 0), []).append(v)
    merged = []  # [draw_calls, vertices, frame times, pairs folded in]
    for (dc, vp), vs in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:200]:
        for m in merged:
            if abs(dc - m[0]) <= 2 and abs(vp - m[1]) <= max(8, 0.05 * m[1]):
                m[2].extend(vs)
                m[3] += 1
                break
        else:
            merged.append([dc, vp, list(vs), 1])
    scenes = []
    for dc, vp, vs, npairs in sorted(merged, key=lambda m: -len(m[2]))[:4]:
        if len(vs) < max(30, 0.02 * len(body)):
            continue
        sv = sorted(vs)
        scenes.append(dict(draw_calls=dc, vertices=vp, pairs=npairs, frames=len(vs), seconds=r(sum(vs) / 1000.0),
                           fps=r(1000.0 * len(vs) / sum(vs), 2), median_ms=r(pct(sv, 50), 3), p99_ms=r(pct(sv, 99), 3)))
    out["scenes"] = scenes
    return out


THROTTLE = ((0x1, "idle"), (0x4, "power_cap"), (0x8, "hw_slowdown"), (0x60, "thermal"))


def first_write_s(run):
    """Seconds from launch to the first samples.csv row where perf.csv or frames.csv holds more than a header
    (> 1024 bytes). perf.csv is flushed every 60 rows, so this is the first frame to within ~1-2 s."""
    path = os.path.join(run, "samples.csv")
    if not os.path.isfile(path):
        return None
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if max(num(row, "perf_csv_bytes") or 0, num(row, "frames_csv_bytes") or 0) > 1024:
                return num(row, "t_s")
    return None


def gpu_stats(run, warmup_s, first_s):
    """gpu.csv (run-game.ps1 -GpuLog): NVML once per sampling pass, t_s on the samples.csv clock (from launch).
    Window: from the first frame + warm-up to the last sample (the harness stops sampling when it closes the game)."""
    path = os.path.join(run, "gpu.csv")
    if not os.path.isfile(path):
        return None
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        rows = [row for row in csv.DictReader(f) if num(row, "t_s") is not None]
    temps = [v for v in (num(x, "temp_c") for x in rows) if v is not None]
    start = (first_s or 0.0) + warmup_s
    body = [x for x in rows if num(x, "t_s") >= start]
    out = dict(samples_total=len(rows), temp_max_c=ri(max(temps)) if temps else None, window_from_s=r(start, 1),
               samples=len(body))
    if not body:
        return out

    def col(k):
        return sorted(v for v in (num(x, k) for x in body) if v is not None)

    util, gr, mem, pw, tc = col("util_gpu"), col("gr_mhz"), col("mem_mhz"), col("power_w"), col("temp_c")
    ps = [x["pstate"] for x in body if x.get("pstate")]
    mode = max(sorted(set(ps)), key=ps.count) if ps else None
    out.update(window_to_s=num(body[-1], "t_s"), util_median=r(pct(util, 50), 1), util_p90=r(pct(util, 90), 1),
               util_mean=r(statistics.mean(util), 1) if util else None, util_max=ri(util[-1]) if util else None,
               gr_mhz_median=ri(pct(gr, 50)), gr_mhz_p10=ri(pct(gr, 10)), gr_mhz_max=ri(gr[-1]) if gr else None,
               mem_mhz_median=ri(pct(mem, 50)), power_w_median=r(pct(pw, 50), 2), power_w_max=pw[-1] if pw else None,
               temp_median_c=r(pct(tc, 50), 1), temp_window_max_c=ri(tc[-1]) if tc else None,
               pstate_mode=mode, pstate_mode_share=r(ps.count(mode) / len(ps), 3) if ps else None)
    reasons = []
    for x in body:
        try:
            reasons.append(int(x.get("throttle") or "", 16))
        except ValueError:
            pass
    if reasons:
        out["limit_reason_share"] = {name: r(sum(1 for v in reasons if v & bit) / len(reasons), 3) for bit, name in THROTTLE}
    return out


def primary(s):
    """The frame series to report: native frames.csv if it has frames, else perf.csv."""
    fr = s.get("frames") or {}
    return fr if fr.get("frames_total") else (s.get("perf") or {})


def verdict(s):
    run, markers = s.get("run") or {}, s["log"]["markers"]
    n = primary(s).get("frames_total", 0)
    crashed = bool(run.get("crash_events") or run.get("dumps") or run.get("wer_seen")) or (
        run.get("exited_early") and run.get("exit_code") not in (0, None))
    if crashed:
        return "CRASHED"
    if run.get("exited_early"):
        return "EXITED EARLY"
    up = markers.get("gpu_ready") or markers.get("dxgi_adapter")
    if up and n >= 60:
        return "RUNNING"
    if up:
        return "RENDERER UP, FEW FRAMES"
    return "NO RENDERER"


def summarise(run, warmup_s):
    s = dict(run_dir=os.path.abspath(run))
    rj = os.path.join(run, "run.json")
    if os.path.isfile(rj):
        with open(rj, encoding="utf-8-sig") as f:
            s["run"] = json.load(f)
    s["log"] = scan_log(run)
    s["frames"] = frame_stats(run, warmup_s)
    s["perf"] = perf_stats(run, warmup_s)
    s["first_frame_s"] = first_write_s(run)
    s["gpu"] = gpu_stats(run, warmup_s, s["first_frame_s"])
    s["verdict"] = verdict(s)
    return s


def fmt(v, unit=""):
    return "-" if v is None else f"{v}{unit}"


def text(s):
    run, lg, fr, mk = s.get("run") or {}, s["log"], s.get("frames"), s["log"]["markers"]
    out = [f"run      {s['run_dir']}"]
    if run.get("mode"):
        out.append(f"mode     {run['mode']}")
    if run:
        close = run.get("close_method")
        how = {"wm_close": f"closed by WM_CLOSE in {run.get('close_seconds')} s",
               "killed": f"did not exit {run.get('close_timeout')} s after WM_CLOSE, killed",
               "exited": f"exited by itself after {run.get('elapsed_s')} s"}.get(close, close)
        out.append(f"result   {s['verdict']}; {how}; exit code {run.get('exit_code_hex')}")
        if run.get("crash_events"):
            for e in run["crash_events"][:3]:
                out.append(f"         event {e.get('id')} {e.get('provider')}: {e.get('summary')}")
        if run.get("dumps"):
            out.append(f"         dumps: {', '.join(run['dumps'][:3])}")
        cpu = run.get("process") or {}
        if cpu:
            out.append(f"process  cpu {fmt(cpu.get('cpu_s'))} s over {fmt(run.get('elapsed_s'))} s "
                       f"(avg {fmt(cpu.get('avg_cores'))} cores); peak working set {fmt(cpu.get('peak_ws_mb'))} MB, "
                       f"peak private {fmt(cpu.get('peak_private_mb'))} MB")
    else:
        out.append(f"result   {s['verdict']}")
    boot = []
    if "xex_patch" in mk:
        boot.append(f"TU patch {mk['xex_patch']['base']} -> {mk['xex_patch']['new']} at {mk['xex_patch']['at_s']} s")
    if "gpu_ready" in mk:
        g = mk["gpu_ready"]
        boot.append(f"{g['backend']} on '{g['adapter']}' {g['width']}x{g['height']} at {g['at_s']} s")
    if "gpu_caps" in mk:
        boot.append(f"uma={mk['gpu_caps']['uma']}")
    if "swap_chain" in mk:
        boot.append(f"vsync {mk['swap_chain']['vsync']}")
    if "dxgi_adapter" in mk:
        g = mk["dxgi_adapter"]
        boot.append(f"DXGI adapter '{g['adapter']}'" + (f" ({g['vram_mb']} MB)" if g.get("vram_mb") else "")
                    + f" at {g['at_s']} s")
    if "shader_storage" in mk:
        boot.append(f"shader storage init at {mk['shader_storage']['at_s']} s")
    if s.get("first_frame_s") is not None:
        boot.append(f"frames first written {s['first_frame_s']} s after launch")
    out.append("boot     " + ("; ".join(boot) if boot else "no boot markers in the log"))
    lv = lg["levels"]
    out.append(f"log      {lg['lines']} lines over {fmt(lg.get('duration_s'))} s: {lv.get('warning', 0)} warnings, "
               f"{lv.get('error', 0)} errors, {lv.get('critical', 0)} critical; "
               f"{lg['missing_functions']} MISSING-FUNCTION addresses"
               + (f"; unknown cvars: {', '.join(lg['unknown_cvars'][:8])}" if lg["unknown_cvars"] else ""))
    for e in lg["errors"][:5]:
        out.append(f"         {e}")
    if not fr:
        out.append("frames   no frames.csv (native builds only)")
    elif not fr.get("frames_measured"):
        out.append(f"frames   {fr['frames_total']} presented over {fr['seconds_total']} s; none left after "
                   f"the {fr['warmup_s']} s warm-up")
    else:
        out.append(f"frames   {fr['frames_total']} presented over {fr['seconds_total']} s; {fr['frames_measured']} "
                   f"measured after a {fr['warmup_s']} s warm-up:")
        out.append(f"         mean {fr['mean_ms']} ms ({fr['fps_mean']} fps)  median {fr['median_ms']}  "
                   f"p95 {fr['p95_ms']}  p99 {fr['p99_ms']}  max {fr['max_ms']} ms  "
                   f">50 ms: {fr['hitches_over_50ms']}  1% low {fr['fps_1pct_low']} fps")
        last = fr.get("last", {})
        out.append(f"         draws/frame median {fmt(fr.get('draw_calls_median'))}; PSO creations "
                   f"{fr['pipeline_creations']} ({fr['pipeline_creation_ms']} ms), {fr['pipeline_creations_measured']} "
                   f"after warm-up; scene {last.get('scene_render_width')}x{last.get('scene_render_height')} -> "
                   f"output {last.get('output_width')}x{last.get('output_height')}; cap "
                   f"{last.get('native_fps_limit_cvar')}; vsync {last.get('native_vsync')}; focused "
                   f"{fmt(fr.get('focused_share'))}")
    if fr and fr.get("fps_per_10s"):
        out.append("timeline fps per 10 s: " + " ".join(str(x) for x in fr["fps_per_10s"]))
    pf = s.get("perf")
    if pf is None:
        out.append("perf     no perf.csv")
    elif not pf.get("frames_measured"):
        out.append(f"perf     {pf['frames_total']} guest frames over {pf['seconds_total']} s in perf.csv; none left "
                   f"after the {pf['warmup_s']} s warm-up (counted from the first frame)")
    else:
        out.append(f"perf     {pf['frames_total']} guest frames over {pf['seconds_total']} s (perf.csv); "
                   f"{pf['frames_measured']} measured from {pf['warmup_s']} s after the first frame:")
        out.append(f"         mean {pf['mean_ms']} ms ({pf['fps_mean']} fps)  median {pf['median_ms']}  p95 {pf['p95_ms']}  "
                   f"p99 {pf['p99_ms']}  p99.9 {pf['p999_ms']}  max {pf['max_ms']} ms  >50 ms: {pf['hitches_over_50ms']}  "
                   f">100 ms: {pf['hitches_over_100ms']}  1% low {pf['fps_1pct_low']} fps")
        out.append(f"         draws/frame p10/p50/p90 {pf['draw_calls_p10']}/{pf['draw_calls_median']}/{pf['draw_calls_p90']}; "
                   f"pipeline cache misses {pf['pipeline_cache_misses']} ({pf['pipeline_cache_misses_measured']} after "
                   f"warm-up); texture cache misses {pf['texture_cache_misses']}")
        for sc in pf.get("scenes") or []:
            near = sc.get("pairs", 1) - 1
            extra = f" (+{near} near pair{'s' if near > 1 else ''})" if near > 0 else ""
            out.append(f"         scene draws {sc['draw_calls']} / vertices {sc['vertices']}{extra}: {sc['frames']} frames over "
                       f"{sc['seconds']} s, {sc['fps']} fps, median {sc['median_ms']} ms, p99 {sc['p99_ms']} ms")
    if pf and pf.get("fps_per_10s"):
        out.append("perf     per 10 s from the first frame (warm-up included), fps: " + " ".join(str(x) for x in pf["fps_per_10s"]))
        out.append("         median draws per 10 s: " + " ".join(str(x) for x in pf["draws_per_10s"]))
        if pf.get("vertices_per_10s"):
            out.append("         median vertices per 10 s: " + " ".join(str(x) for x in pf["vertices_per_10s"]))
    g, gl = s.get("gpu"), run.get("gpu_log") or {}
    if g and g.get("samples"):
        lr = g.get("limit_reason_share") or {}
        out.append(f"gpu      {gl.get('device') or 'GPU 0'} (NVML, 1 Hz): {g['samples']} samples from {g['window_from_s']} to "
                   f"{g['window_to_s']} s: util median {g['util_median']} % (p90 {g['util_p90']}, max {g['util_max']}); "
                   f"graphics clock median {g['gr_mhz_median']} MHz (p10 {g['gr_mhz_p10']}, max {g['gr_mhz_max']}); "
                   f"memory clock {g['mem_mhz_median']} MHz")
        out.append(f"         power median {g['power_w_median']} W (max {g['power_w_max']}); temperature median "
                   f"{g['temp_median_c']} C (max {g['temp_window_max_c']}, {g['temp_max_c']} over the whole run); "
                   f"{g['pstate_mode']} in {fmt(g['pstate_mode_share'])} of samples; clock limit reasons (share of samples): "
                   + (", ".join(f"{k} {v}" for k, v in lr.items()) or "-"))
    elif g:
        out.append(f"gpu      {g['samples_total']} NVML samples, none after {g['window_from_s']} s")
    elif gl.get("note"):
        out.append(f"gpu      no GPU log: {gl['note']}")
    if run.get("screenshots"):
        out.append("shots    " + ", ".join(run["screenshots"]))
    return "\n".join(out)


AGG_KEYS = ("fps_mean", "mean_ms", "median_ms", "p95_ms", "p99_ms", "p999_ms", "max_ms", "fps_1pct_low",
            "hitches_over_50ms", "hitches_over_100ms", "draw_calls_median")


def adapter_of(s):
    mk = s["log"]["markers"]
    return (mk.get("gpu_ready") or mk.get("dxgi_adapter") or {}).get("adapter")


def aggregate(runs, warmup_s):
    rows = []
    for d in runs:
        sj = os.path.join(d, "summary.json")
        if os.path.isfile(sj):
            with open(sj, encoding="utf-8") as f:
                rows.append(json.load(f))
        else:
            rows.append(summarise(d, warmup_s))
    lines = [f"{len(rows)} runs"]
    for s in rows:
        fr = primary(s)
        lines.append(f"  {os.path.basename(s['run_dir'])}: {s['verdict']}, {adapter_of(s) or '?'}, "
                     f"fps_mean {fr.get('fps_mean')}, median {fr.get('median_ms')} ms, p99 {fr.get('p99_ms')} ms")
    agg = {}
    for k in AGG_KEYS:
        vals = [primary(s).get(k) for s in rows]
        vals = [v for v in vals if v is not None]
        if vals:
            agg[k] = dict(median=r(statistics.median(vals), 3), min=r(min(vals), 3), max=r(max(vals), 3), n=len(vals))
            lines.append(f"  {k:<18} median {agg[k]['median']:<10} min {agg[k]['min']:<10} max {agg[k]['max']:<10} (n={len(vals)})")
    adapters = {adapter_of(s) for s in rows}
    if len(adapters) > 1:
        lines.append(f"  WARNING: runs used different adapters: {adapters}")
    untimed = [os.path.basename(s["run_dir"]) for s in rows if "NOT FOR TIMING" in ((s.get("run") or {}).get("mode") or "")]
    if untimed:
        lines.append(f"  WARNING: not timing results (profile or hidden desktop): {', '.join(untimed)}")
    if len(rows) < 5:
        lines.append("  note: fewer than 5 runs; the measuring rule asks for medians of >= 5")
    return dict(runs=[s["run_dir"] for s in rows], aggregate=agg), "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--warmup", type=float, default=10.0, help="seconds of frames to drop (default 10)")
    ap.add_argument("--write", action="store_true", help="write summary.json and summary.txt into the run dir")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--json", help="also write the result as JSON to this file")
    a = ap.parse_args()
    if a.aggregate:
        data, txt = aggregate(a.runs, a.warmup)
    else:
        if len(a.runs) != 1:
            sys.exit("give one run dir, or --aggregate with several")
        data = summarise(a.runs[0], a.warmup)
        txt = text(data)
        if a.write:
            with open(os.path.join(a.runs[0], "summary.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            with open(os.path.join(a.runs[0], "summary.txt"), "w", encoding="utf-8") as f:
                f.write(txt + "\n")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    print(txt)


if __name__ == "__main__":
    main()
