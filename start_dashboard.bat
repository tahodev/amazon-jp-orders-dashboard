@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

where py >nul 2>&1
if not errorlevel 1 (
  set "PYTHON_CMD=py -3"
) else (
  where python >nul 2>&1
  if errorlevel 1 goto python_missing
  set "PYTHON_CMD=python"
)

echo [Amazon JP Orders] 起動前チェックを実行しています...
%PYTHON_CMD% scripts\doctor.py
if errorlevel 1 goto failed

echo.
echo [Amazon JP Orders] ローカル受信サービスを起動します。
echo [Amazon JP Orders] 利用中はこのウィンドウを閉じないでください。
echo [Amazon JP Orders] Chrome 拡張機能: %CD%\chrome_extension
echo.
%PYTHON_CMD% run.py serve --host 127.0.0.1 --port 8776 --open-browser
goto done

:python_missing
echo [エラー] Python 3.10 以降が見つかりません。
echo https://www.python.org/downloads/ からインストールしてください。
goto failed

:failed
echo.
echo 起動できませんでした。上のメッセージを確認してください。
pause
exit /b 1

:done
endlocal
