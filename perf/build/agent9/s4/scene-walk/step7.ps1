$ErrorActionPreference = 'Continue'
$env:PYTHONDONTWRITEBYTECODE = '1'
python build/agent9/s4/scene-walk/step7.py
exit $LASTEXITCODE
