#!/usr/bin/env python3
"""Self-test helper: list the map entries analyze_profile.py derives for one guest address.

usage: map_hooks.py MAP GUEST_ADDR   ->  {"entries": [{"name", "kind", "rva", "obj"}, ...]}
kind is '' (plain guest function), 'hook' (sub_X defined away from __imp__sub_X) or
'hooked original' (the __imp__sub_X body of a hooked function).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import analyze_profile as ap  # noqa: E402

m = ap.MapTable(sys.argv[1])
g = int(sys.argv[2], 0)
print(json.dumps({'entries': [{'name': e[0], 'kind': e[3], 'rva': f'0x{r:X}', 'obj': e[1]}
                              for r, e in zip(m.rvas, m.entries) if e[4] == g]}))
