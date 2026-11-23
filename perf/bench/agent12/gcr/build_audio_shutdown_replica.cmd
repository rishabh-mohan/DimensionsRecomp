@echo off
rem Task #22 (Agent 12): builds build\agent12\gcr\audio_shutdown_replica.exe (1 TU, 1 thread).
rem Usage: bench\agent12\gcr\build_audio_shutdown_replica.cmd
setlocal
set "SRC=%~dp0audio_shutdown_replica.cpp"
set "OUT=%~dp0..\..\..\build\agent12\gcr"
if not exist "%OUT%" mkdir "%OUT%"
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
set "VSDIR="
for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSDIR=%%i"
if not defined VSDIR (
  echo vswhere found no Visual Studio with the x64 C++ tools
  exit /b 1
)
call "%VSDIR%\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++20 /W3 /MT "%SRC%" /Fo"%OUT%\audio_shutdown_replica.obj" /Fe"%OUT%\audio_shutdown_replica.exe" /Fd"%OUT%\audio_shutdown_replica.pdb"
exit /b %ERRORLEVEL%
