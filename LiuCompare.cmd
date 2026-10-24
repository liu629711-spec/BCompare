@echo off
rem LiuCompare launcher - double-click or run: LiuCompare.cmd [leftFile rightFile]
rem No args = open the LiuCompare home window; with two file paths = compare them.
setlocal
set "ROOT=%~dp0"
set "GUI=%ROOT%product\gui\WpfHost\bin\Release\net8.0-windows\reacmp-gui.exe"
if not exist "%GUI%" set "GUI=%ROOT%product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.exe"
if not exist "%GUI%" (
  echo LiuCompare is not built. Run:  dotnet build "%ROOT%product\gui\WpfHost" -c Release
  exit /b 1
)
if "%~2"=="" (
  if "%~1"=="" (
    "%GUI%" --menu-spec "%ROOT%product\gui\spec\menu-spec.json" --view "Home" --show
  ) else (
    echo Usage: LiuCompare.cmd leftFile rightFile
    "%GUI%" --menu-spec "%ROOT%product\gui\spec\menu-spec.json" --dispatch "%~1" "%~1" --show
  )
) else (
  "%GUI%" --menu-spec "%ROOT%product\gui\spec\menu-spec.json" --dispatch "%~1" "%~2" --show
)
