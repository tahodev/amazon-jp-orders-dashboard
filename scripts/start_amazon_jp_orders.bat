@echo off
setlocal
cd /d "%~dp0\.."
set PYTHONIOENCODING=utf-8
echo [amazon_jp_orders] Starting local receiver on http://127.0.0.1:8776
echo [amazon_jp_orders] Keep this window open while using the Chrome extension.
echo.
echo Extension folder:
echo   %CD%\chrome_extension
echo.
start "" "http://127.0.0.1:8776/dashboard"
python run.py serve --host 127.0.0.1 --port 8776
pause
endlocal
