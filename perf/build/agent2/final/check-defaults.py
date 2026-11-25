#!/usr/bin/env python3
"""check-defaults.py - prove from a game.log which defaults a launch actually ran.

M2, build/agent2/final (FINAL-DEFAULTS.diff). Reads one game.log and prints the effective value and source
of every switch the final build changed, then PASS/FAIL against the expected set.

Modes (--mode):
  xenos   plain launch of the FINAL Xenos bin (default). Expects the WC win3 arm exactly, every SDK key with
          source "default": both "Final defaults" lines, the 1 ms timer line, C1 keep-watch on, TimerQueue
          precise wait, "GPU wait back-off: ON (quantum 500 us, spin 30 us); stats OFF; GetData hook built."
          (the full timed line, M10 S1), exactly once each.
  native  plain launch of a FINAL native bin built on the new SDK. Same runtime line; the GPU line is
          optional (checked if present); C1 keep-watch reports "blocked ... (native renderer)"; no back-off
          line (the q500 TU is Xenos-only, N3); "Native GPU: shader miss cache ON (build default)" once.
  native-old  a FINAL native exe staged with the OLD SDK DLLs (snap1-sdk, BUILD-PLAN option N-A = W8a "mc"
          exactly as timed): no "Final defaults" (runtime or GPU) / 1 ms / C1 / precise-wait / back-off lines, and
          "Native GPU: shader miss cache ON (build default)" once.
  off     a new-bin OFF arm (old behaviour set explicitly): runtime/GPU keys at the OLD values (any source),
          "GPU wait back-off: OFF (LEGO_GPU_WAIT_BACKOFF_US=off)" once, no C1 keep-watch / precise-wait /
          1 ms lines.
  legacy  an old-bin log (no "Final defaults" lines, e.g. tonight's win3 runs on devoff4b-bin, where the
          values came from cvars/env). Checks only the proof lines of the xenos mode. Use it to show that a
          FINAL plain launch prints the same proof lines as the timed win3 arm.

Always: none of the 4 bad strings, no "C1 verify: on", no "is not a plain number".
Exit code 0 = PASS, 1 = FAIL, 2 = usage / unreadable log.  --json prints the parsed table as JSON.
"""
import argparse
import json
import re
import sys

# key -> (win3 / final default, old default). Values as the cvar getter prints them.
RUNTIME_KEYS = {
    "physical_protect_hold_global_lock": ("true", "false"),
    "physical_protect_keep_watch": ("true", "false"),
    "host_timer_resolution_ms": ("1", "0"),
    "host_timer_throttling_optout": ("true", "false"),
    "precise_guest_sleep": ("true", "false"),
    "wait_timeout_round_up": ("true", "false"),
    "cs_spin": ("true", "false"),
    "spinlock_pause_spin": ("true", "false"),
    "clock_lockfree": ("true", "false"),
    "tls_bounds_fix": ("true", "false"),
    "timer_queue_precise_wait": ("true", "false"),
}
GPU_KEYS = {
    "shared_memory_single_hold_rearm": ("true", "false"),
    "physical_protect_keep_watch_verify": ("false", "false"),  # unchanged; logged to prove it stays off
}

L_RUNTIME = "Final defaults: "
L_GPU = "Final defaults (GPU): "
L_TIMER = "Host timer resolution set to 1 ms (background opt-out on)"
L_C1 = "C1 keep-watch: on (with physical_protect_hold_global_lock)"
L_C1_NATIVE = "C1 keep-watch: on, but blocked for this process (native renderer)"
L_TQ = "TimerQueue: precise wait (timer_queue_precise_wait)"
# M10 S1: the full timed line (0319-win3-r1), so a STATS run or an exe without the GetData hook cannot PASS
L_BO_ON = "GPU wait back-off: ON (quantum 500 us, spin 30 us); stats OFF; GetData hook built."
L_BO_OFF = "GPU wait back-off: OFF (LEGO_GPU_WAIT_BACKOFF_US=off)."
L_MC_ON = "Native GPU: shader miss cache ON (build default)"
BAD = [
    "Recovered stale physical page protection",
    "Unhandled guest physical write fault",
    "PhysicalHeap::Protect failed",
    "is not a plain number",
    "C1 verify: on",
]
PAIR = re.compile(r"(\w+)=(\S+?)(?:\((\w+|\?)\))?(?=\s|$)")


def msg(line):
    # "[ts] [info] [core] [t123] message" -> "message"
    m = re.match(r"^\[[^\]]*\] \[[^\]]*\] \[[^\]]*\] \[[^\]]*\] (.*)$", line)
    return m.group(1) if m else line


def parse_pairs(text):
    return {k: (v, s or "") for k, v, s in PAIR.findall(text)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("log")
    ap.add_argument("--mode", choices=["xenos", "native", "native-old", "off", "legacy"], default="xenos")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        lines = [msg(l.rstrip("\r\n")) for l in open(a.log, encoding="utf-8", errors="replace")]
    except OSError as e:
        print(f"cannot read {a.log}: {e}")
        return 2

    fails, notes = [], []

    def count(s, exact=False):
        return sum(1 for l in lines if (l == s if exact else l.startswith(s)))

    def want(s, n, label, exact=False):
        c = count(s, exact)
        (notes if c == n else fails).append(f"{label}: {c} (want {n}) '{s}'")

    rt = [l for l in lines if l.startswith(L_RUNTIME)]
    gp = [l for l in lines if l.startswith(L_GPU)]
    table = {}
    if rt:
        table.update(parse_pairs(rt[0][len(L_RUNTIME):]))
    if gp:
        table.update(parse_pairs(gp[0][len(L_GPU):]))

    if a.mode not in ("legacy", "native-old"):
        if len(rt) != 1:
            fails.append(f"'Final defaults:' lines: {len(rt)} (want 1)")
        if a.mode == "native":
            if len(gp) > 1:
                fails.append(f"'Final defaults (GPU):' lines: {len(gp)} (want 0 or 1)")
        elif len(gp) != 1:
            fails.append(f"'Final defaults (GPU):' lines: {len(gp)} (want 1)")
        keys = dict(RUNTIME_KEYS)
        if gp or a.mode != "native":
            keys.update(GPU_KEYS)
        for k, (new, old) in keys.items():
            if k not in table:
                fails.append(f"{k}: missing from the Final defaults lines")
                continue
            v, src = table[k]
            if a.mode == "off":
                if v != old:
                    fails.append(f"{k}={v}({src}): want old value {old}")
            elif v != new or src != "default":
                fails.append(f"{k}={v}({src}): want {new}(default)")
        extra = sorted(set(table) - set(keys))
        if extra:
            notes.append(f"extra keys in the dump: {extra}")

    if a.mode in ("xenos", "legacy"):
        want(L_TIMER, 1, "1 ms timer line", exact=True)
        want(L_C1, 1, "C1 keep-watch on line", exact=True)
        want(L_TQ, 1, "TimerQueue precise line", exact=True)
        want(L_BO_ON, 1, "back-off ON 500/30, stats OFF, GetData hook line", exact=True)
        want("GPU wait back-off:", 1, "back-off lines of any kind")
        want("GPU wait back-off: OFF", 0, "back-off OFF line")
    elif a.mode == "native":
        want(L_TIMER, 1, "1 ms timer line", exact=True)
        want(L_C1_NATIVE, 1, "C1 keep-watch blocked (native) line", exact=True)
        want(L_TQ, 1, "TimerQueue precise line", exact=True)
        want("GPU wait back-off:", 0, "back-off line (Xenos-only TU)")
        want(L_MC_ON, 1, "miss cache ON (build default) line", exact=True)
    elif a.mode == "native-old":
        want(L_RUNTIME, 0, "'Final defaults:' line (old SDK has none)")
        want(L_GPU, 0, "'Final defaults (GPU):' line (old rexgpu-xenos has none; M10 N3)")
        want("Host timer resolution set to", 0, "host timer line")
        want("C1 keep-watch: on", 0, "C1 keep-watch line")
        want(L_TQ, 0, "TimerQueue precise line", exact=True)
        want("GPU wait back-off:", 0, "back-off line (Xenos-only TU)")
        want(L_MC_ON, 1, "miss cache ON (build default) line", exact=True)
    elif a.mode == "off":
        want(L_BO_OFF, 1, "back-off OFF (off) line", exact=True)
        want("GPU wait back-off: ON", 0, "back-off ON line")
        want("C1 keep-watch: on", 0, "C1 keep-watch on line")
        want(L_TQ, 0, "TimerQueue precise line", exact=True)
        want("Host timer resolution set to", 0, "host timer line")

    for b in BAD:
        c = sum(1 for l in lines if b in l)
        (fails if c else notes).append(f"bad string '{b}': {c}")

    print(f"log:  {a.log}")
    print(f"mode: {a.mode}")
    if table:
        print(f"{'key':38} {'value':8} source")
        for k in list(RUNTIME_KEYS) + list(GPU_KEYS):
            if k in table:
                print(f"{k:38} {table[k][0]:8} {table[k][1]}")
    elif a.mode != "legacy":
        print("(no 'Final defaults' lines found)")
    for n in notes:
        print("  ok   " + n)
    for f in fails:
        print("  FAIL " + f)
    print("RESULT", "PASS" if not fails else f"FAIL ({len(fails)})")
    if a.json:
        print(json.dumps({"log": a.log, "mode": a.mode, "table": table, "fails": fails}, indent=1))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
