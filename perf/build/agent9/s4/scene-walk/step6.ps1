$ErrorActionPreference = 'Continue'
$env:PYTHONDONTWRITEBYTECODE = '1'
python build/agent9/s4/scene-walk/step6.py
exit $LASTEXITCODE
