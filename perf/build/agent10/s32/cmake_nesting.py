"""Show the if()/endif() nesting that encloses every draw.cpp mention in rexlego/CMakeLists.txt.

Usage: python cmake_nesting.py <CMakeLists.txt>
Prints, for each line mentioning draw.cpp, the stack of enclosing if() conditions, plus the
list()/set() command the line belongs to (to tell a compiled source list from a fingerprint list).
"""
import re
import sys

path = sys.argv[1]
lines = open(path, encoding="utf-8").read().splitlines()
stack = []  # (line_no, text)
cmd_start = None  # (line_no, text) of the command whose argument list is open
depth = 0
for no, raw in enumerate(lines, 1):
    line = raw.split("#", 1)[0] if not raw.lstrip().startswith("\"") else raw
    s = line.strip()
    if depth == 0 and s:
        m = re.match(r"([A-Za-z_]+)\s*\(", s)
        if m:
            cmd_start = (no, s[:100])
    depth += line.count("(") - line.count(")")
    if re.match(r"if\s*\(", s):
        stack.append((no, s))
    elif re.match(r"endif\s*\(", s):
        opened = stack.pop()
        if opened[1].startswith("if(LEGODIMENSIONS_NATIVE_GPU)"):
            print(f"block {opened[0]} '{opened[1]}' closes at {no}")
    if "draw.cpp" in raw:
        enclosing = " > ".join(f"{n}:{t}" for n, t in stack) or "<top level>"
        print(f"{no}: {raw.strip()}\n    in: {enclosing}\n    cmd: {cmd_start}")
print("unclosed:", stack)
