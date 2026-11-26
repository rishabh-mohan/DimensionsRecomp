"""Run tools/gpu-aot/test_placement_capture_lookup.py unchanged, with crash dialogs off.

SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX) is inherited by the clang++ and
captured-lookup.exe children. A failed lookup (std::abort in the generated fixture) then exits with
an error code instead of leaving a Windows Error Reporting dialog on the user's desktop.
Copy of build/agent4/s35/run_lookup.py (Agent 4, 2026-11-22) for build/agent16/pack (E16.1, 2026-11-25).

Usage: python run_lookup.py <test_placement_capture_lookup.py> <captures> <index> <cache> <out> [--main-cache X]
"""
import ctypes
import runpy
import sys

SEM_FAILCRITICALERRORS = 0x0001
SEM_NOGPFAULTERRORBOX = 0x0002

ctypes.windll.kernel32.SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX)
script = sys.argv[1]
sys.argv = [script] + sys.argv[2:]
runpy.run_path(script, run_name='__main__')
