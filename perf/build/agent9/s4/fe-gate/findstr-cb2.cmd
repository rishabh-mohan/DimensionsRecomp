@echo off
rem #41 (task #17 step 7): ori/hex forms of 0x82A9F718 / 0x82A9F5C8 in the A generated tree (baseline, as 41-step1.txt)
rem lis/addi forms were checked by cb_formation.py (41-cb-formation.txt: 33 addi sites, 0 matches)
findstr /n /i /c:",63256" /c:",62920" /c:"0xF718" /c:"0xF5C8" /c:"0x82A9F718" /c:"0x82A9F5C8" baseline\DimensionsRecomp\rexlego\generated\default\legodimensions_recomp.*.cpp > build\agent9\s4\fe-gate\findstr-cb2.txt
echo done %date% %time% >> build\agent9\s4\fe-gate\findstr-cb2.txt
