@echo off
rem Step 5a: fresh clone of the DimensionsModManager submodule source (approved by Agent 6, 18:47)
rem into DR/research/DimensionsModManager at the gitlink commit 3c6f899b.
set DST=<workspace>\DimensionsRecomp\research\DimensionsModManager
echo start %DATE% %TIME%
rem core.longpaths=true (stored only in this fresh clone's .git/config): mods/SuperSonicInfinite/... exceeds
rem MAX_PATH under this deep workspace path ("Filename too long" on the first attempt).
git clone -c core.longpaths=true --no-checkout https://github.com/NeverCookFirst/DimensionsModLoader.git "%DST%" 2>&1
echo clone exit=%ERRORLEVEL% %TIME%
git -C "%DST%" checkout --detach 3c6f899b403ae2f144d59c3835e7100a2824a2ff 2>&1
echo checkout exit=%ERRORLEVEL% %TIME%
git -C "%DST%" rev-parse HEAD
git -C "%DST%" log -1 --format="%%H %%ci %%s"
git -C "%DST%" status --short
git -C "%DST%" submodule status
echo end %DATE% %TIME%
