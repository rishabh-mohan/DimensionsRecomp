"""native3 boot check (Agent 7, task #6, session 3): frontend on, no throw, bilinear present.

Usage:
  python bench\\agent7\\native3_boot_check.py <run dir> [--bin-dir build\\agent2\\native3-bin]
         [--ref build\\agent8\\matrix\\20261122-0013\\runs\\0030-n0-r1] [--min-frames 600]
         [--seconds 50] [--tail-skip 2]

<run dir> is one of Agent 8's run dirs, from run-timing.ps1 or a functional boot. It holds run.json,
game.log, legodimensions.toml, native-frames.csv, perf.csv, frames.json, MANIFEST.txt and
rexruntime.dll. Files missing from the run dir are taken from --bin-dir.
The check prints one PASS / FAIL / WARN / INFO line per check, then a verdict per group, then an
overall verdict.
  A. Frontend on: the effective native_settings_frontend must be true. Precedence (cvar.cpp: the
     command line outranks the config): run.json args --native_settings_frontend[=v] > the run dir's
     legodimensions.toml (the runner writes toml_set into it) > run.json toml_set > the default
     (false, settings_native_hooks.cpp:16).
     Nothing logs at boot when NativeSettingsRuntime is built, so the proof that it was built and
     didn't throw comes from A together with B.
  B. No throw:
     - none of the throw/fatal lines in game.log (the S2 crash was
       "Native setting is not registered: ...", then 0xE06D7363);
     - a present line after "Native write tracking", which is the S2 throw point;
     - run.json OK: status, exited_early, werfault_seen, exit code;
     - no *.dmp or wer-* files;
     - at least --min-frames native rows.
  C. Bilinear present:
     - spatial_fsr_presented (FSR 1 presented) and fsr_enabled (= native FSR 3) are 0 on every
       native row;
     - no "Native FSR 1:" warnings.
     rexruntime.dll is classified by the cvar names it defines (the exe is no use: rexlego names
     the present_fsr_* cvars itself, settings_registry.cpp:41-42):
      - FidelityFX-header SDK (option (b)): present_fsr_quality_mode / present_cas_additional_sharpness,
        which presenter.cpp defines only under REX_HAS_FIDELITYFX_SDK. present_effect='fsr' can be
        selected; flagged WARN.
      - native FSR 1 cvars only (present_fsr_sharpness_reduction / present_fsr_max_upsampling_passes
        without the FFX-only ones: the native-fsr1 SDK patch): present_effect accepts 'fsr' and the
        native renderer runs its own FSR 1. WARN if the run-dir toml selects 'fsr', else INFO.
      - present_effect alone: a non-FFX SDK, bilinear-only, the toml's 'fsr' is rejected. INFO.
     An amd_fidelityfx_dx12 reference in rexruntime.dll (the FFX runtime) is INFO only: the native
     bins ship amd_fidelityfx_dx12.dll without loading it, and option (b) needs no runtime.
     C assumes option (a) or bilinear.
  D. Info:
     - build identity: MANIFEST fix (a) hashes, and the native GPU fingerprint against game.log;
     - perf.csv rows = native rows + 1, and frame contiguity;
     - the adapter, swap-chain, gamma and present lines;
     - interval_ms over the runner window (frames.json) or the last --seconds;
     - swap_present_cpu_ms;
     - with --ref (a native2 run): the last-row config, log lines and fps against it. Differences
       are WARN.
Exit 0 = no FAIL, 1 = any FAIL, 2 = usage error. Stdlib only, one thread.
"""
import argparse
import glob
import hashlib
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import native_frames_summary as nfs  # noqa: E402

THROW_PATTERNS = (
    "Native setting is not registered",
    "0xE06D7363",
    "Unhandled exception",
    "[FATAL]",
    "Crashed on a host thread",
    "Native preferences recovery failed",
    "Native GPU initialization failed",
)
PRESENT_PATTERNS = ("display gamma updated", "presented internal texture", "swap-chain max frame latency")
INFO_PATTERNS = (
    "D3D12 ready on",
    "threaded recording",
    "swap chain ready",
    "swap-chain max frame latency",
    "display gamma updated",
    "presentation cap override",
    "presented internal texture",
    "present override",
    "committed native settings",
    "Native settings:",
)
CONFIG_COLS = nfs.NATIVE_LAST
EXPECT = (("settings_registry.cpp", ("4EC71328", "8BA19C5F")),
          ("settings_preferences.cpp", ("9CBE6DBF",)))


class Report:
    def __init__(self):
        self.items = []
        self.group = None

    def start(self, group, title):
        self.group = group
        print("%s. %s" % (group, title))

    def add(self, level, text):
        self.items.append((self.group, level))
        print("  %-4s %s" % (level, text))

    def verdict(self, group):
        levels = [lv for g, lv in self.items if g == group]
        warns = levels.count("WARN")
        return ("FAIL" if "FAIL" in levels else "PASS") + ("(%d WARN)" % warns if warns else "")

    def failed(self):
        return any(lv == "FAIL" for _, lv in self.items)


def read_lines(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:  # MANIFEST.txt starts with a BOM
        return f.read().splitlines()


def parse_bool(v):
    v = str(v).strip().strip("'\"").lower()
    if v in ("true", "1", "yes", "on"):
        return True
    if v in ("false", "0", "no", "off"):
        return False
    return None


def short(line, n=170):
    line = line.strip()
    return line if len(line) <= n else line[:n - 3] + "..."


def sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16].upper()


def find_file(name, run_dir, bin_dir):
    for d in (run_dir, bin_dir):
        if d and os.path.exists(os.path.join(d, name)):
            return os.path.join(d, name)
    return None


def first_line(lines, pattern, start=0):
    for i in range(start, len(lines)):
        if pattern in lines[i]:
            return i
    return None


def norm_msg(line, pattern):
    """The message from `pattern` on, with 16-hex fingerprints and digits masked."""
    msg = line[line.index(pattern):] if pattern in line else line
    msg = re.sub(r"\b[0-9a-fA-F]{16}\b", "<hex>", msg)
    return re.sub(r"\d+", "#", msg).strip()


def window_stats(run_dir, rows, perf_t, seconds, tail_skip):
    t = [nfs.to_float(r.get("interval_ms")) for r in rows]
    wins, note = nfs.runner_window(run_dir, t, perf_t or [])
    if wins and "native" in wins:
        lo, hi = wins["native"]
        kind = "runner window"
    else:
        lo, hi, _ = nfs.tail_window(t, seconds, tail_skip)
        kind = "last %gs before a %gs tail skip" % (seconds, tail_skip)
    return lo, hi, kind, nfs.stats(t[lo:hi]), note


def check_frontend(rep, rj, toml_lines, have_toml):
    rep.start("A", "frontend on (NativeSettingsRuntime is built)")
    rj = rj or {}
    args = [str(x) for x in rj.get("args") or []]
    cli = None
    for arg in args:
        m = re.match(r"^--?native_settings_frontend(?:=(.*))?$", arg)
        if m:
            cli = (True if m.group(1) is None else parse_bool(m.group(1)), arg)  # the last one wins
    ts = None
    toml_set = rj.get("toml_set") or {}
    pairs = toml_set.items() if isinstance(toml_set, dict) else (str(x).partition("=")[::2] for x in toml_set)
    for k, v in pairs:
        if str(k).split(".")[-1].strip() == "native_settings_frontend":
            ts = (parse_bool(v), "run.json toml_set %s=%s" % (k, v))
    tf = None
    for i, line in enumerate(toml_lines, 1):
        m = re.match(r"^\s*native_settings_frontend\s*=\s*([^#\s]+)", line)
        if m:
            tf = (parse_bool(m.group(1)), "run-dir legodimensions.toml:%d '%s'" % (i, line.strip()))
    if not have_toml:
        rep.add("WARN", "no legodimensions.toml in the run dir")
    env = [k for k in (rj.get("env_set") or rj.get("env") or {}) if "native_settings_frontend" in str(k).lower()]
    if env:
        rep.add("WARN", "the environment sets %s; the environment is not a cvar source here, so it is ignored" % env)
    if ts and tf and ts[0] != tf[0]:
        rep.add("WARN", "toml_set (%s) disagrees with the run-dir toml (%s)" % (ts[1], tf[1]))
    if cli is not None:
        val, src = cli[0], "the command line '%s'" % cli[1] + (", which outranks %s" % tf[1] if tf else "")
    elif tf is not None:
        val, src = tf[0], tf[1] + ", with no command-line override"
    elif ts is not None:
        val, src = ts
    else:
        val, src = False, "the default (settings_native_hooks.cpp:16); no command-line or toml setting"
    if val is True:
        rep.add("PASS", "effective native_settings_frontend=true from %s" % src)
    else:
        rep.add("FAIL", "effective native_settings_frontend=%s from %s: NativeSettingsRuntime isn't built, so "
                "this run doesn't exercise fix (a)" % (str(val).lower(), src))
    load = [x for x in args if "native_settings_load" in x]
    if load:
        rep.add("INFO", "also on the command line: %s (the saved-settings load is skipped)" % ", ".join(load))


def check_no_throw(rep, rj, run_dir, log, rows, perf_t, min_frames):
    rep.start("B", "no throw (it boots past NativeSettingsRuntime and presents)")
    if log is None:
        rep.add("FAIL", "game.log missing")
    else:
        hits = [(i, x) for i, x in enumerate(log) if any(p in x for p in THROW_PATTERNS)]
        if hits:
            rep.add("FAIL", "game.log: %d throw/fatal line(s), the first at L%d: %s" % (
                len(hits), hits[0][0] + 1, short(hits[0][1])))
            for i, x in hits[1:4]:
                rep.add("INFO", "  L%d: %s" % (i + 1, short(x)))
        else:
            rep.add("PASS", "game.log: %d lines, none matching the %d throw/fatal patterns" % (len(log), len(THROW_PATTERNS)))
        wt = first_line(log, "Native write tracking")
        pr = None
        for i in range((wt + 1) if wt is not None else 0, len(log)):
            if any(p in log[i] for p in PRESENT_PATTERNS):
                pr = i
                break
        if wt is not None and pr is not None:
            rep.add("PASS", "present line at L%d, after 'Native write tracking' at L%d (the S2 throw point): %s" % (
                pr + 1, wt + 1, short(log[pr], 120)))
        elif wt is not None:
            rep.add("FAIL", "'Native write tracking' at L%d, but no present line after it: the run stopped where "
                    "the S2 build threw" % (wt + 1))
        elif pr is not None:
            rep.add("WARN", "present line at L%d, but no 'Native write tracking' line" % (pr + 1))
        else:
            rep.add("FAIL", "no present line: native GPU init or the first present never happened")
        saved = [x for x in log if "Native saved settings:" in x]
        if saved:
            rep.add("WARN", "%d 'Native saved settings:' line(s): %s" % (len(saved), short(saved[0])))
        restored = [x for x in log if "committed native settings" in x]
        if restored:
            rep.add("INFO", short(restored[0]))
    if rj is None:
        rep.add("FAIL", "run.json missing or unreadable")
    else:
        bad, desc = [], []
        st = rj.get("status")
        if st is not None:
            desc.append("status=%s" % st)
            if st != "OK":
                bad.append("status=%s problems=%s" % (st, rj.get("problems")))
        ee = rj.get("exited_early")
        desc.append("exited_early=%s" % ee)
        if ee:
            bad.append("exited early at %ss (phase %s)" % (rj.get("exited_at_s"), rj.get("exited_phase")))
        wf = rj.get("werfault_seen")
        desc.append("werfault_seen=%s" % wf)
        if wf:
            bad.append("werfault_seen")
        ec = rj.get("exit_code")
        desc.append("exit_code=%s" % ec)
        if ec not in (0, None):
            bad.append("exit_code=%s (%s)" % (ec, rj.get("exit_code_hex")))
        if bad:
            rep.add("FAIL", "run.json: " + "; ".join(bad))
        else:
            rep.add("PASS", "run.json: " + " ".join(desc))
        if ec is None and not ee:
            rep.add("WARN", "run.json has no exit code (still running, or killed?)")
        close = rj.get("close") or {}
        if close and close.get("clean") is False:
            rep.add("WARN", "the close was not clean: killed=%s exit_wait_s=%s" % (close.get("killed"), close.get("exit_wait_s")))
        nr = rj.get("not_responding_window_samples") or 0
        if nr:
            rep.add("WARN", "not_responding_window_samples=%s" % nr)
    dumps = sorted(set(glob.glob(os.path.join(run_dir, "*.dmp")) + glob.glob(os.path.join(run_dir, "wer-*"))))
    arts = [x for x in (rj or {}).get("artifacts") or [] if str(x).lower().endswith(".dmp")]
    if dumps or arts:
        rep.add("FAIL", "crash artifacts: %s" % ", ".join(sorted(set(os.path.basename(x) for x in dumps + arts))))
    else:
        rep.add("PASS", "no *.dmp or wer-* files in the run dir or in run.json artifacts")
    metrics_env = "LEGO_NATIVE_FRAME_METRICS" in ((rj or {}).get("env_set") or (rj or {}).get("env") or {})
    if rows is None and not metrics_env and perf_t:
        n = len([x for x in perf_t if x > 0])
        rep.add("WARN", "no native-frames.csv (LEGO_NATIVE_FRAME_METRICS not set); perf.csv has %d frames" % n)
        if n < min_frames:
            rep.add("FAIL", "perf.csv: %d frames, fewer than --min-frames %d" % (n, min_frames))
    elif rows is None:
        rep.add("FAIL", "native-frames.csv missing: no frame was presented")
    elif len(rows) < min_frames:
        rep.add("FAIL", "native-frames.csv: %d rows, fewer than --min-frames %d" % (len(rows), min_frames))
    else:
        rep.add("PASS", "native-frames.csv: %d rows (at least %d)" % (len(rows), min_frames))


# presenter.cpp (rexglue-sdk) defines these two only under REX_HAS_FIDELITYFX_SDK.
FFX_ONLY_CVARS = (b"present_fsr_quality_mode", b"present_cas_additional_sharpness")
# Defined under REX_HAS_FIDELITYFX_SDK and, with the native-fsr1 patch, in non-FFX builds too.
FSR1_CVARS = (b"present_fsr_sharpness_reduction", b"present_fsr_max_upsampling_passes")


def classify_present_sdk(data):
    """(has present_effect, FFX-only cvar names, FSR 1 cvar names, FFX runtime referenced) of a binary."""
    names = lambda ns: [n.decode() for n in ns if n in data]
    return (b"present_effect" in data, names(FFX_ONLY_CVARS), names(FSR1_CVARS),
            b"amd_fidelityfx_dx12" in data.lower())


def check_bilinear(rep, run_dir, bin_dir, log, rows, toml_lines):
    rep.start("C", "bilinear present (no FSR 1, no native FSR 3)")
    if not rows:
        rep.add("FAIL", "no native rows: the present mode is unknown")
    else:
        for col, what in (("spatial_fsr_presented", "FSR 1 presented"), ("fsr_enabled", "native FSR 3 on")):
            vals = [nfs.to_float(r.get(col)) for r in rows]
            known = [v for v in vals if not math.isnan(v)]
            if not known:
                rep.add("WARN", "column %s missing" % col)
                continue
            on = [i for i, v in enumerate(vals) if not math.isnan(v) and v != 0]
            if on:
                rep.add("FAIL", "%s != 0 (%s) on %d of %d rows, first at frame %s" % (
                    col, what, len(on), len(rows), rows[on[0]].get("frame")))
            else:
                rep.add("PASS", "%s = 0 on all %d rows" % (col, len(known)))
        r0 = rows[0]
        rep.add("INFO", "first row: scene %sx%s, present source %sx%s, output %sx%s" % tuple(
            r0.get(c) for c in ("scene_render_width", "scene_render_height", "present_source_width",
                                "present_source_height", "output_width", "output_height")))
    if log is not None:
        fsr1 = [x for x in log if "Native FSR 1:" in x]
        if fsr1:
            rep.add("FAIL", "%d 'Native FSR 1:' line(s): FSR 1 was requested and its setup failed, so the present "
                    "fell back to the spatial copy: %s" % (len(fsr1), short(fsr1[0])))
        else:
            rep.add("PASS", "no 'Native FSR 1:' warnings (FSR 1 was not requested)")
        offered = [x for x in log if "is no longer offered" in x]
        if offered:
            rep.add("WARN", short(offered[0]))
        pit = [x for x in log if "presented internal texture" in x]
        if pit:
            rep.add("INFO", short(pit[0]))
    eff = [x.strip() for x in toml_lines if re.match(r"^\s*present_effect\s*=", x)]
    toml_fsr = bool(eff) and re.sub(r"\s*#.*$", "", eff[0].split("=", 1)[1]).strip().strip("'\"").lower() == "fsr"
    if eff:
        rep.add("INFO", "run-dir toml has %s ('fsr' is accepted by an SDK with the FidelityFX headers or the "
                "native-fsr1 patch)" % eff[0])
    dll = find_file("rexruntime.dll", run_dir, bin_dir)
    if not dll:
        rep.add("WARN", "no rexruntime.dll in the run dir or --bin-dir")
        return
    with open(dll, "rb") as f:
        data = f.read()
    has_effect, ffx, fsr1, ffx_rt = classify_present_sdk(data)
    tag = "%s (sha256 %s)" % (os.path.relpath(dll), sha16(dll))
    if ffx:
        rep.add("WARN", "%s has %s: an SDK with the FidelityFX headers (option (b)?), so present_effect='fsr' "
                "can be selected and bilinear is not the expected present" % (tag, "/".join(ffx)))
    elif fsr1 and has_effect:
        rep.add("WARN" if toml_fsr else "INFO",
                "%s: native FSR 1 cvars (%s) without the FFX-only ones (native-fsr1 SDK), so present_effect "
                "accepts 'fsr' and the native renderer runs its own FSR 1%s" % (
                    tag, "/".join(fsr1), "; the toml selects it, so bilinear is not the expected present"
                    if toml_fsr else ""))
    elif has_effect:
        rep.add("INFO", "%s: a non-FFX SDK (present_effect is there, the FSR cvars aren't), so present_effect "
                "is bilinear-only and the toml's 'fsr' is rejected" % tag)
    else:
        rep.add("WARN", "%s: no present_effect string" % tag)
    if ffx_rt:
        rep.add("INFO", "%s references amd_fidelityfx_dx12 (the FFX runtime)" % tag)


def check_info(rep, run_dir, bin_dir, rj, log, rows, perf_t, ref_dir, seconds, tail_skip):
    rep.start("D", "build identity, frame accounting, present path (info)")
    man = find_file("MANIFEST.txt", run_dir, bin_dir)
    log_fp = None
    if log is not None:
        log_fp = next((m.group(1) for m in (re.search(r"Native GPU \[([0-9a-fA-F]{16})\]", x) for x in log) if m), None)
    if man:
        mlines = read_lines(man)
        rep.add("INFO", "%s: %s" % (os.path.relpath(man), short(mlines[0] if mlines else "(empty)", 120)))
        for name, want in EXPECT:
            hits = [m for m in (re.search(r"%s:\s*(\S+)\s*->\s*(\S+)" % re.escape(name), x) for x in mlines) if m]
            if not hits:
                rep.add("WARN", "MANIFEST lists no %s patch, so fix (a) isn't in this build (pre-S3?)" % name)
            elif any(hits[-1].group(2).upper().startswith(w) for w in want):
                rep.add("PASS", "MANIFEST: %s %s -> %s (fix (a))" % (name, hits[-1].group(1), hits[-1].group(2)))
            else:
                rep.add("WARN", "MANIFEST: %s %s -> %s; expected %s" % (
                    name, hits[-1].group(1), hits[-1].group(2), " or ".join(want)))
        man_fp = next((m.group(1) for m in (re.search(r"native GPU ([0-9a-f]{16})", x, re.I) for x in mlines) if m), None)
        if man_fp and log_fp:
            rep.add("PASS" if man_fp.lower() == log_fp.lower() else "WARN",
                    "native GPU fingerprint: MANIFEST %s, game.log %s" % (man_fp, log_fp))
    else:
        rep.add("WARN", "no MANIFEST.txt in the run dir or --bin-dir")
    if bin_dir:
        for name in ("legodimensions.exe", "rexruntime.dll"):
            a, b = os.path.join(run_dir, name), os.path.join(bin_dir, name)
            if os.path.exists(a) and os.path.exists(b):
                ha, hb = sha16(a), sha16(b)
                rep.add("PASS" if ha == hb else "WARN", "%s: run dir %s, --bin-dir %s" % (name, ha, hb))
    if perf_t is not None and rows is not None:
        d = len(perf_t) - len(rows)
        rep.add("PASS" if d == 1 else "WARN", "rows: perf.csv %d, native-frames.csv %d (perf - native = %+d; "
                "expect +1, perf.csv's leading 0 row)" % (len(perf_t), len(rows), d))
    if rows:
        frames = []
        for r in rows:
            try:
                frames.append(int(r.get("frame")))
            except (TypeError, ValueError):
                pass
        gaps = sum(1 for x, y in zip(frames, frames[1:]) if y != x + 1)
        rep.add("PASS" if gaps == 0 and frames else "WARN", "native frame column %s..%s, %d gap(s)" % (
            frames[0] if frames else "?", frames[-1] if frames else "?", gaps))
    if log is not None:
        if log_fp:
            rep.add("INFO", "game.log native GPU fingerprint %s" % log_fp)
        for p in INFO_PATTERNS:
            i = first_line(log, p)
            if i is not None:
                rep.add("INFO", "L%d: %s" % (i + 1, short(log[i][log[i].index(p):], 150)))
    st = None
    if rows:
        lo, hi, kind, st, note = window_stats(run_dir, rows, perf_t, seconds, tail_skip)
        rep.add("INFO", "interval_ms, %s rows %d-%d: %s" % (kind, lo + 1, hi, nfs.fmt(st)))
        if "MISMATCH" in note:
            rep.add("WARN", "runner window: " + note)
        w = rows[lo:hi]
        means = []
        for c in ("swap_present_cpu_ms", "present_cpu_ms", "draw_calls"):
            vals = [v for v in (nfs.to_float(r.get(c)) for r in w) if not math.isnan(v)]
            if vals:
                means.append("%s=%.3f" % (c, sum(vals) / len(vals)))
        rep.add("INFO", "window means: " + " ".join(means))
    if not ref_dir:
        return
    ref_rows_path = os.path.join(ref_dir, "native-frames.csv")
    if not os.path.exists(ref_rows_path):
        rep.add("WARN", "--ref has no native-frames.csv")
        return
    ref_rows = nfs.read_native_csv(ref_rows_path)
    if rows and ref_rows:
        diffs = [(c, rows[-1].get(c), ref_rows[-1].get(c)) for c in CONFIG_COLS if rows[-1].get(c) != ref_rows[-1].get(c)]
        if diffs:
            rep.add("WARN", "last-row config differs from --ref: " + ", ".join("%s=%s (ref %s)" % x for x in diffs))
        else:
            rep.add("PASS", "last-row config matches --ref: " + " ".join("%s=%s" % (c, rows[-1].get(c)) for c in CONFIG_COLS))
        ref_perf = os.path.join(ref_dir, "perf.csv")
        ref_perf_t = nfs.read_perf_csv(ref_perf) if os.path.exists(ref_perf) else None
        _, _, kind, rst, _ = window_stats(ref_dir, ref_rows, ref_perf_t, seconds, tail_skip)
        if st and rst:
            rep.add("INFO", "fps %.2f vs --ref %.2f (%+.1f%%; ref %s)" % (
                st["fps"], rst["fps"], 100.0 * (st["fps"] / rst["fps"] - 1.0), kind))
    ref_log_path = os.path.join(ref_dir, "game.log")
    if log is not None and os.path.exists(ref_log_path):
        ref_log = read_lines(ref_log_path)
        same, notes = 0, []
        for p in INFO_PATTERNS:
            i, j = first_line(log, p), first_line(ref_log, p)
            if j is not None and i is None:
                rep.add("WARN", "'%s' is in --ref's game.log but not in this one" % p)
            elif i is not None and j is None:
                rep.add("INFO", "'%s' is new against --ref: %s" % (p, short(log[i])))
            elif i is not None:
                a, b = norm_msg(log[i], p), norm_msg(ref_log[j], p)
                if a == b:
                    same += 1
                else:
                    notes.append(p)
                    rep.add("WARN", "'%s' differs from --ref: %s | ref: %s" % (
                        p, short(log[i][log[i].index(p):], 90), short(ref_log[j][ref_log[j].index(p):], 90)))
        rep.add("INFO", "%d log line(s) match --ref with digits and fingerprints masked" % same)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run_dir")
    ap.add_argument("--bin-dir", help="staged bin dir; used for files missing from the run dir")
    ap.add_argument("--ref", help="a native2 run dir to compare the config, log lines and fps with")
    ap.add_argument("--min-frames", type=int, default=600)
    ap.add_argument("--seconds", type=float, default=50.0)
    ap.add_argument("--tail-skip", type=float, default=2.0)
    a = ap.parse_args()
    for label, d in (("run dir", a.run_dir), ("--bin-dir", a.bin_dir), ("--ref", a.ref)):
        if d and not os.path.isdir(d):
            print("%s not found: %s" % (label, d), file=sys.stderr)
            return 2
    p = lambda name: os.path.join(a.run_dir, name)
    rj = nfs.load_json(p("run.json"))
    log = read_lines(p("game.log")) if os.path.exists(p("game.log")) else None
    rows = nfs.read_native_csv(p("native-frames.csv")) if os.path.exists(p("native-frames.csv")) else None
    perf_t = nfs.read_perf_csv(p("perf.csv")) if os.path.exists(p("perf.csv")) else None
    have_toml = os.path.exists(p("legodimensions.toml"))
    toml_lines = read_lines(p("legodimensions.toml")) if have_toml else []
    print("== native3 boot check: %s%s%s" % (a.run_dir, "  bin dir %s" % a.bin_dir if a.bin_dir else "",
                                           "  ref %s" % a.ref if a.ref else ""))
    if rj:
        print("   bin_dir in run.json: %s; tag %s; start %s" % (rj.get("bin_dir"), rj.get("tag"), rj.get("start")))
    rep = Report()
    check_frontend(rep, rj, toml_lines, have_toml)
    check_no_throw(rep, rj, a.run_dir, log, rows, perf_t, a.min_frames)
    check_bilinear(rep, a.run_dir, a.bin_dir, log, rows, toml_lines)
    check_info(rep, a.run_dir, a.bin_dir, rj, log, rows, perf_t, a.ref, a.seconds, a.tail_skip)
    code = 1 if rep.failed() else 0
    print("VERDICT %s -> %s (exit %d)" % (" ".join("%s=%s" % (g, rep.verdict(g)) for g in "ABCD"),
                                          "FAIL" if code else "PASS", code))
    return code


if __name__ == "__main__":
    sys.exit(main())
