@echo off
rem findstr-cb.cmd (Agent 9, run-2 task #17 step 7, #41 open item 1): who forms 0x82A9F718 / 0x82A9F5C8?
rem Both are lis -32086 (0x82AA) + a negative low half: 0xF718 -> -2280, 0xF5C8 -> -2616.
rem Matches the asm comment lines (",-2280" / ",-2616") in the A generated tree (baseline, as 41-step1.txt). Run at BelowNormal:
rem   cmd /c start "" /belownormal /wait /b build\agent9\s4\fe-gate\findstr-cb.cmd
cd /d %~dp0..\..\..\..
findstr /n /c:",-2280" /c:",-2616" baseline\DimensionsRecomp\rexlego\generated\default\legodimensions_recomp.*.cpp > build\agent9\s4\fe-gate\findstr-cb.txt
echo done %date% %time% >> build\agent9\s4\fe-gate\findstr-cb.txt
