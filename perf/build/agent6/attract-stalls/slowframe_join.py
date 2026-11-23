#!/usr/bin/env python3
"""slowframe_join.py: join `slow_frame_log_ms` lines in game.log to perf.csv rows.

Agent 6, follow-up to task #18 (perf-notes/agent6-attract-stalls.md, section 11).
Read-only on the run dir, single-threaded, standard library only.

  python slowframe_join.py <run_dir> [--min-ms 250] [--rows 8274,9630] [--out FILE]
  python slowframe_join.py --selftest [--perf <perf.csv>]

perf.csv row k is the GPU thread's wall time from swap k-1 entry to swap k entry (note section 1).
The slow-frame line (d3d12/command_processor.cpp:242-284) covers the same span: it is logged at
IssueSwap entry, right after Profiler::Flip. Its frame number can be offset from the perf.csv row
number by a constant, which is found here by matching the ms values.

remainder = frame - gpu-thread idle - host-gpu wait - shader translate - pipeline create - texture load.
Translate and create are timed only on the synchronous path. With async creation (the default) the
EndSubmission wait for the creation threads is untimed, so on P0/P1 rows the remainder is mostly that
wait. Readback "stalled" is printed separately because it may overlap host-gpu wait.
"""
import argparse
import csv
import os
import random
import re
import shutil
import statistics
import sys

SLOW_RE = re.compile(
    r"slow frame #(?P<idx>\d+): (?P<ms>[\d.]+) ms \| gpu-thread idle (?P<idle>[\d.]+) \| "
    r"host-gpu wait (?P<fence>[\d.]+) \((?P<fence_n>\d+)x\) \| "
    r"shader translate (?P<xlate>[\d.]+) \((?P<xlate_n>\d+)x\) \| "
    r"pipeline create (?P<create>[\d.]+) \((?P<create_n>\d+)x\), new (?P<new>\d+) \| "
    r"texture load (?P<tex>[\d.]+) \((?P<tex_n>\d+)x\) \| "
    r"readback (?P<rb_n>\d+)x (?P<rb_kb>\d+) KB, (?P<rb_us>\d+) stalled")
FLOATS = ("ms", "idle", "fence", "xlate", "create", "tex")
H0_SIG = (2823, 366575)   # H0 anchor row (draws, vertices); agent3-run-harness.md section 7.4
LOAD_SIG = (219, 226)     # the PRE load frame (devoff2 r8274, devoffB r8130)
CLASSES = ("P0", "P1", "PRE", "P2", "heavy", "none")


def load_slow(path):
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = SLOW_RE.search(line)
            if not m:
                continue
            d = {k: (float(v) if k in FLOATS else int(v)) for k, v in m.groupdict().items()}
            d["rb_ms"] = d["rb_us"] / 1000.0
            out.append(d)
    return out


def load_perf(path):
    rows, t = [], 0.0
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for i, r in enumerate(csv.DictReader(f), 1):
            try:
                ms = int(r["frame_time_us"]) / 1000.0
                row = dict(row=i, ms=ms, t0=t, draws=int(r["draw_calls"]),
                           verts=int(r["vertices_processed"]), cb=int(r["command_buffer_stalls"]),
                           pm=int(r["pipeline_cache_misses"]), tm=int(r["texture_cache_misses"]))
            except (KeyError, ValueError, TypeError):
                break  # truncated last line of a live or killed run
            rows.append(row)
            t += ms / 1000.0  # t0 = start of the row, in seconds since the first row
    return rows


def classify(rows, k):
    """Classes of note section 1 (P0, P1, PRE, P2, heavy, none); k is a 0-based index."""
    def pm(j):
        return rows[j]["pm"] if 0 <= j < len(rows) else 0
    if pm(k):
        return "P0"
    if pm(k - 1):
        return "P1"
    if pm(k + 1) or pm(k + 2):
        return "PRE"
    if pm(k - 2):
        return "P2"
    return "heavy" if rows[k]["draws"] >= 5000 else "none"


def tol(ms):
    return max(1.0, 0.02 * ms)


def align(slow, rows):
    """Find d with perf index (0-based) = frame# + d - 1 matching most lines, then join each line."""
    best = (0, -1)
    for d in range(-5, 6):
        hits = 0
        for s in slow:
            j = s["idx"] + d - 1
            if 0 <= j < len(rows) and abs(rows[j]["ms"] - s["ms"]) <= tol(s["ms"]):
                hits += 1
        if hits > best[1]:
            best = (d, hits)
    d = best[0]
    joined, shifted, unmatched = {}, 0, []
    for s in slow:
        j0 = s["idx"] + d - 1
        for j in (j0, j0 - 1, j0 + 1):
            if 0 <= j < len(rows) and j not in joined and abs(rows[j]["ms"] - s["ms"]) <= tol(s["ms"]):
                joined[j] = s
                shifted += j != j0
                break
        else:
            unmatched.append(s)
    return d, joined, shifted, unmatched


def remainder(s):
    return s["ms"] - s["idle"] - s["fence"] - s["xlate"] - s["create"] - s["tex"]


def pct(x, total):
    return 100.0 * x / total if total > 0 else 0.0


def analyze(run_dir, min_ms=250.0, extra_rows=(), game_log=None, perf_csv=None):
    """Return (report text, result dict)."""
    slow = load_slow(game_log or os.path.join(run_dir, "game.log"))
    rows = load_perf(perf_csv or os.path.join(run_dir, "perf.csv"))
    out = [f"run: {run_dir}", f"perf.csv rows: {len(rows)}; slow-frame lines: {len(slow)}"]
    res = {"lines": len(slow), "rows": len(rows)}
    if not slow or not rows:
        out.append("nothing to join (slow_frame_log_ms not set, or wrong run dir)")
        return "\n".join(out), res

    d, joined, shifted, unmatched = align(slow, rows)
    deltas = [abs(rows[j]["ms"] - s["ms"]) for j, s in joined.items()]
    thr = min(s["ms"] for s in slow)
    med = statistics.median(deltas) if deltas else float("nan")
    out.append(f"alignment: perf row = frame# + {d}; matched {len(joined)}/{len(slow)} "
               f"(shifted by one row: {shifted}); median |d ms| {med:.2f}; smallest logged frame {thr:.1f} ms")
    cut = thr + tol(thr)
    missing = [rows[k]["row"] for k in range(1, len(rows)) if rows[k]["ms"] >= cut and k not in joined]
    out.append(f"perf rows >= {cut:.1f} ms without a line: {len(missing)}"
               + (f" (first {missing[:8]})" if missing else ""))
    res.update(offset=d, matched=len(joined), shifted=shifted, unmatched=len(unmatched), missing=len(missing))

    h0 = next((k for k, r in enumerate(rows) if (r["draws"], r["verts"]) == H0_SIG), None)
    base = rows[h0]["t0"] if h0 is not None else 0.0
    out.append(f"H0: row {rows[h0]['row']} (the time column is H0+s)" if h0 is not None
               else "H0 anchor not found: the time column is seconds since the first perf.csv row")

    sel = sorted({k for k, r in enumerate(rows) if r["ms"] > min_ms}
                 | {r - 1 for r in extra_rows if 0 < r <= len(rows)})
    out.append("")
    out.append(f"rows over {min_ms:.0f} ms (plus --rows); component columns are ms from the slow-frame line:")
    out.append(f"{'row':>6} {'t':>8} {'ms':>7} {'class':>5} {'draws':>6} {'pm':>3} {'pm-1':>4} {'cb':>4} | "
               f"{'idle':>7} {'fence':>7} {'xlate':>7} {'create':>7} {'new':>3} {'tex':>6} {'rb_st':>6} "
               f"{'rem':>7} {'rem%':>5}")
    agg = {}
    for k in sel:
        r = rows[k]
        c = classify(rows, k)
        pm_prev = rows[k - 1]["pm"] if k else 0
        left = (f"{r['row']:>6} {r['t0'] - base:>+8.2f} {r['ms']:>7.0f} {c:>5} {r['draws']:>6} "
                f"{r['pm']:>3} {pm_prev:>4} {r['cb']:>4}")
        s = joined.get(k)
        if s is None:
            out.append(left + " | (no slow-frame line)")
            continue
        rem = remainder(s)
        out.append(left + f" | {s['idle']:>7.1f} {s['fence']:>7.1f} {s['xlate']:>7.1f} {s['create']:>7.1f} "
                          f"{s['new']:>3} {s['tex']:>6.1f} {s['rb_ms']:>6.1f} {rem:>7.1f} {pct(rem, s['ms']):>5.0f}")
        a = agg.setdefault(c, dict(n=0, ms=0.0, idle=0.0, fence=0.0, xlate=0.0, create=0.0, tex=0.0, rem=0.0))
        a["n"] += 1
        a["rem"] += rem
        for key in FLOATS:
            a[key] += s[key]

    out.append("")
    out.append("per class (the rows above that have a line): share of frame time")
    for c in CLASSES:
        if c in agg:
            a = agg[c]
            out.append(f"{c:>5}: {a['n']:>3} rows {a['ms'] / 1000:7.2f} s | idle {pct(a['idle'], a['ms']):3.0f}% "
                       f"fence {pct(a['fence'], a['ms']):3.0f}% xlate {pct(a['xlate'], a['ms']):3.0f}% "
                       f"create {pct(a['create'], a['ms']):3.0f}% tex {pct(a['tex'], a['ms']):3.0f}% "
                       f"rem {pct(a['rem'], a['ms']):3.0f}%")
    res["classes"] = agg

    out.append("")
    out.append("decision hints (note section 11):")
    # Q1: the PRE load frame(s). Menu frames share the signature but are fast,
    # so only rows that have a line are printed, plus a count of the rest.
    res["q1"] = []
    sig = [k for k, r in enumerate(rows) if (r["draws"], r["verts"]) == LOAD_SIG]
    unjoined = [k for k in sig if joined.get(k) is None]
    if not sig:
        out.append(f"Q1: no load-signature row ({LOAD_SIG[0]} draws / {LOAD_SIG[1]} verts) in perf.csv")
    elif unjoined:
        out.append(f"Q1: {len(unjoined)} of {len(sig)} load-signature rows have no line (under the threshold; "
                   f"menu frames share the signature), first row {rows[unjoined[0]]['row']}")
    for k in sig:
        s = joined.get(k)
        if s is None:
            continue
        idle, tex, fence = s["idle"] / s["ms"], s["tex"] / s["ms"], s["fence"] / s["ms"]
        rem = remainder(s) / s["ms"]
        if idle >= 0.6:
            v = "guest side (game code or file loading): neither warm storage nor S4 helps"
        elif tex >= 0.4:
            v = "texture loads (uploads)"
        elif fence >= 0.4:
            v = "host-GPU fence wait"
        elif rem >= 0.4:
            v = "GPU thread busy in untimed work (compile wait or other emulation)"
        else:
            v = "mixed, no single cause"
        res["q1"].append(v)
        out.append(f"Q1 load frame row {rows[k]['row']} ({s['ms']:.0f} ms): idle {idle:.0%}, tex {tex:.0%}, "
                   f"fence {fence:.0%}, rem {rem:.0%} -> {v}")

    # Q3 needs the burst row; Q2 looks just after it.
    lo = h0 if h0 is not None else 0
    imax = max(range(lo, len(rows)), key=lambda k: rows[k]["pm"]) if lo < len(rows) else None
    if imax is None or rows[imax]["pm"] < 20:
        out.append("Q2/Q3: no burst row (pm >= 20) after H0")
    else:
        cbk = [k for k in range(imax + 1, min(imax + 11, len(rows))) if rows[k]["cb"] >= 100 and k in joined]
        if cbk:
            f_ms = sum(joined[k]["fence"] for k in cbk)
            t_ms = sum(joined[k]["ms"] for k in cbk)
            sh = f_ms / t_ms if t_ms else 0.0
            v = "host-GPU fence wait confirmed" if sh >= 0.6 else "not mainly fence wait"
            res["q2"] = dict(rows=[rows[k]["row"] for k in cbk], fence_share=sh, verdict=v)
            out.append(f"Q2 cb>=100 rows {[rows[k]['row'] for k in cbk]}: host-gpu wait {sh:.0%} of {t_ms:.0f} ms -> {v}")
        else:
            out.append("Q2: no cb>=100 row with a line within 10 rows after the burst")
        pair = [k for k in (imax, imax + 1) if k in joined]
        xl = sum(joined[k]["xlate"] for k in pair)
        cr = sum(joined[k]["create"] for k in pair)
        tot = sum(joined[k]["ms"] for k in pair)
        rem = sum(remainder(joined[k]) for k in pair)
        if not pair:
            out.append(f"Q3 burst row {rows[imax]['row']}: no line")
        elif xl + cr < 0.1 * tot:
            v = "untimed here (async creation): run arm B (d3d12_pipeline_creation_threads=0)"
            res["q3"] = dict(share=None, verdict=v, remainder_share=rem / tot)
            out.append(f"Q3 burst rows {[rows[k]['row'] for k in pair]} (pm {rows[imax]['pm']}, {tot:.0f} ms): "
                       f"translate+create {xl + cr:.0f} ms, remainder {rem / tot:.0%} -> {v}")
        else:
            sh = xl / (xl + cr)
            if sh >= 0.4:
                v = "translation dominates: do S4 (a), note section 10.1"
            elif sh <= 0.2:
                v = "creation dominates: skip (a); warm storage (section 7) is the remedy"
            else:
                v = f"grey zone: (a) saves at most ~{sh:.0%} of the burst"
            res["q3"] = dict(share=sh, verdict=v, remainder_share=rem / tot)
            out.append(f"Q3 burst rows {[rows[k]['row'] for k in pair]} (pm {rows[imax]['pm']}, {tot:.0f} ms): "
                       f"translate {xl:.0f} ms, create {cr:.0f} ms, share {sh:.2f} -> {v}")

    # Q4: heavy rows with a line.
    hv = [k for k in joined if classify(rows, k) == "heavy" and (h0 is None or k >= h0)]
    if hv:
        t_ms = sum(joined[k]["ms"] for k in hv)
        idle = sum(joined[k]["idle"] for k in hv) / t_ms
        fence = sum(joined[k]["fence"] for k in hv) / t_ms
        v = ("guest side" if idle >= 0.5 else
             "host-GPU bound" if fence >= 0.5 else "GPU-thread draw processing (throughput)")
        res["q4"] = dict(rows=len(hv), idle=idle, fence=fence, verdict=v)
        out.append(f"Q4 heavy rows with a line: {len(hv)} ({t_ms:.0f} ms): idle {idle:.0%}, fence {fence:.0%} -> {v}")
    else:
        out.append("Q4: no heavy row with a line")
    return "\n".join(out), res


def selftest(perf_src):
    """Build synthetic arm A/B fixtures from a real perf.csv and check the joins and verdicts."""
    here = os.path.dirname(os.path.abspath(__file__))
    rows = load_perf(perf_src)
    rnd = random.Random(18)
    imax = max(range(len(rows)), key=lambda k: rows[k]["pm"])

    def fractions(k, arm):
        r = rows[k]
        f = dict(idle=0.3, fence=0.1, xlate=0.0, create=0.0, tex=0.05)
        if (r["draws"], r["verts"]) == LOAD_SIG:
            f.update(idle=0.7, tex=0.1)
        elif r["cb"] >= 100:
            f.update(idle=0.05, fence=0.75)
        elif k in (imax, imax + 1):
            f.update(idle=0.05, fence=0.02)
            if arm == "B":
                f.update(xlate=0.45, create=0.35)
        elif r["draws"] >= 5000 and not r["pm"]:
            f.update(idle=0.1, fence=0.2)
        return f

    ok = True
    for arm in ("A", "B"):
        out_dir = os.path.join(here, "fixture-slowframe", arm)
        os.makedirs(out_dir, exist_ok=True)
        shutil.copyfile(perf_src, os.path.join(out_dir, "perf.csv"))
        n = 0
        with open(os.path.join(out_dir, "game.log"), "w", encoding="utf-8", newline="\n") as g:
            g.write("[03:17:56.000] [t1000] [info] unrelated line\n")
            for k, r in enumerate(rows):
                if k == 0 or r["ms"] < 50:
                    continue  # the first swap never logs (cp:259-266)
                ms = r["ms"] + rnd.uniform(-0.3, 0.3)
                f = fractions(k, arm)
                g.write(f"[03:20:00.000] [t4242] [info] slow frame #{k + 2}: {ms:.1f} ms | gpu-thread idle "
                        f"{f['idle'] * ms:.1f} | host-gpu wait {f['fence'] * ms:.1f} (3x) | shader translate "
                        f"{f['xlate'] * ms:.1f} ({30 if f['xlate'] else 0}x) | pipeline create "
                        f"{f['create'] * ms:.1f} ({30 if f['create'] else 0}x), new {r['pm']} | texture load "
                        f"{f['tex'] * ms:.1f} (2x) | readback 0x 0 KB, 0 stalled | cpu-write invalidations 0x 0 KB "
                        f"(on memexport pages 0x 0 KB) | memexport syncs 0 (0 KB), on demand 0 (0 KB)\n")
                n += 1
        text, res = analyze(out_dir)
        with open(os.path.join(out_dir, "report.txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
        checks = [
            ("lines parsed", res["lines"] == n),
            ("offset recovered (-1)", res.get("offset") == -1),
            ("all lines matched", res.get("matched") == n and res.get("unmatched") == 0),
            ("no missing rows", res.get("missing") == 0),
            ("Q1 guest side", bool(res.get("q1")) and all(v.startswith("guest") for v in res["q1"])),
            ("Q2 fence share ~0.75", abs(res.get("q2", {}).get("fence_share", 0) - 0.75) < 0.02),
        ]
        if arm == "A":
            checks.append(("Q3 says use arm B", res.get("q3", {}).get("share", 1) is None))
        else:
            checks.append(("Q3 share 0.5625", abs((res.get("q3", {}).get("share") or 0) - 0.5625) < 0.01))
            checks.append(("Q3 verdict (a)", res.get("q3", {}).get("verdict", "").startswith("translation")))
        for name, good in checks:
            print(f"selftest arm {arm}: {'PASS' if good else 'FAIL'}  {name}")
            ok &= good
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", nargs="?")
    ap.add_argument("--min-ms", type=float, default=250.0, help="table threshold on perf.csv ms (default 250)")
    ap.add_argument("--rows", default="", help="extra 1-based perf.csv rows to list, comma-separated")
    ap.add_argument("--out", help="also write the report to this file")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--perf", help="perf.csv for --selftest (default: the devoff2 tie-break run)")
    a = ap.parse_args()
    if a.selftest:
        here = os.path.dirname(os.path.abspath(__file__))
        src = a.perf or os.path.normpath(os.path.join(
            here, "..", "..", "agent3", "runs", "20261122-031756-bgate-long-devoff2", "perf.csv"))
        return selftest(src)
    if not a.run_dir:
        ap.error("run_dir is required (or --selftest)")
    extra = [int(x) for x in a.rows.split(",") if x.strip()]
    text, _ = analyze(a.run_dir, a.min_ms, extra)
    print(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
