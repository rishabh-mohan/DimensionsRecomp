"""Build and run bench/agent7/present_microbench.cpp (one thread, no GPU, no game).

Usage (from the repo root, in a shell where env/devshell.ps1 has been dot-sourced):
    python bench/agent7/run_microbench.py [--runs 5] [extra args for the exe, e.g. --only-timer]
Output: build/agent7/bench/present_microbench-<HHMMSS>.txt (also printed).
"""
import argparse
import datetime
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "bench" / "agent7" / "present_microbench.cpp"
OUT = ROOT / "build" / "agent7" / "bench"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compiler", default="clang++")
    parser.add_argument("--runs", default="5")
    args, extra = parser.parse_known_args()
    OUT.mkdir(parents=True, exist_ok=True)
    exe = OUT / "present_microbench.exe"
    subprocess.run([args.compiler, "-std=c++20", "-O2", str(SRC), "-o", str(exe)], check=True)
    started = datetime.datetime.now()
    result = subprocess.run([str(exe), "--runs", args.runs, *extra], check=True, capture_output=True,
                            text=True, timeout=900)
    header = (f"# present_microbench {started:%Y-%m-%d %H:%M:%S}, runs={args.runs}, args={extra}\n"
              f"# machine shared with other agents' builds; numbers are medians, see the cpp header\n")
    text = header + result.stdout
    path = OUT / f"present_microbench-{started:%H%M%S}.txt"
    path.write_text(text)
    sys.stdout.write(text)
    print(f"# written to {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
