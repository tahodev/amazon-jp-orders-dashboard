@echo off
setlocal
cd /d "%~dp0\.."
echo [amazon_jp_orders] This deletes local captured/sample data under:
echo   %CD%\data
echo.
echo Close start_amazon_jp_orders.bat / receiver window before running this.
echo Press Ctrl+C to cancel, or any key to continue.
pause >nul
if exist data (
  rmdir /s /q data
  echo [amazon_jp_orders] data directory removed.
) else (
  echo [amazon_jp_orders] data directory does not exist.
)
echo.
pause
endlocal
