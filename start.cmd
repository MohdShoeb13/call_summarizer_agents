@echo off
cd /d "%~dp0"
call uv sync --frozen
if errorlevel 1 exit /b 1
if not exist .env copy .env.example .env
pushd frontend
call npm.cmd ci
if errorlevel 1 exit /b 1
call npm.cmd run build
if errorlevel 1 exit /b 1
popd
echo Open http://127.0.0.1:8018 in your browser.
call uv run uvicorn backend.main:app --host 127.0.0.1 --port 8018
