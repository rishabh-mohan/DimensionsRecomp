#!/usr/bin/env python3
# holdrun.py (Agent 2, board run 2 task #1): run ONE command at Below Normal priority under the HOLD rule
# (used for the CG26 codegen run, which has no HOLD handling of its own).
#
#   python build/agent2/holdrun.py --cwd DIR --log FILE [--timeout SECONDS] -- COMMAND ARGS...
#
# Refuses to start while perf-notes/WINDOW-HOLD.txt exists; polls it every 2 s while the command runs and kills the
# command's process tree (taskkill /T /F) if it appears -> exit 30 (wait for Agent 1's resume). --timeout kills it
# too (exit 31). The command's stdout + stderr go to --log. Give the program as an ABSOLUTE path (Windows resolves a
# relative program against this process's directory, not --cwd; an absolute build/agent2/... path also lets
# build/agent2/stop-snap.ps1 find it). Exit code = the command's exit code.
import argparse, os, subprocess, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
HOLD = os.path.join(R, 'perf-notes', 'WINDOW-HOLD.txt')
BELOW_NORMAL = 0x00004000
PRIO = {'idle': 0x00000040, 'belownormal': BELOW_NORMAL}


def kill(p):
    subprocess.run('taskkill /T /F /PID %d' % p.pid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cwd', required=True)
    ap.add_argument('--log', required=True)
    ap.add_argument('--timeout', type=float, default=0.0)
    ap.add_argument('--priority', choices=sorted(PRIO), default='idle')  # session 3: Idle by default
    ap.add_argument('cmd', nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == '--' else a.cmd
    if not cmd:
        print('FAIL: no command after --')
        return 2
    if not os.path.isabs(cmd[0]):
        print('FAIL: give the program as an absolute path: %s' % cmd[0])
        return 2
    if os.path.exists(HOLD):
        print('HOLD file exists: not starting')
        return 9
    log = os.path.abspath(a.log)
    os.makedirs(os.path.dirname(log), exist_ok=True)
    t0 = time.time()
    with open(log, 'wb') as lf:
        lf.write(('# holdrun %s  cwd %s\n# cmd: %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), os.path.abspath(a.cwd),
                                                         subprocess.list2cmdline(cmd))).encode('utf-8'))
        lf.flush()
        p = subprocess.Popen(cmd, cwd=a.cwd, stdout=lf, stderr=subprocess.STDOUT, creationflags=PRIO[a.priority])
        print('started pid %d at %s (%s); log %s' % (p.pid, time.strftime('%H:%M:%S'), a.priority,
                                                    os.path.relpath(log, R)))
        sys.stdout.flush()
        while p.poll() is None:
            if os.path.exists(HOLD):
                kill(p)
                print('HOLD file appeared: killed the command tree after %.1f s (exit 30)' % (time.time() - t0))
                return 30
            if a.timeout and time.time() - t0 > a.timeout:
                kill(p)
                print('TIMEOUT after %.1f s: killed the command tree (exit 31)' % (time.time() - t0))
                return 31
            time.sleep(2)
    print('exit %d, wall %.1f s, ended %s' % (p.returncode, time.time() - t0, time.strftime('%H:%M:%S')))
    return p.returncode


if __name__ == '__main__':
    sys.exit(main())
