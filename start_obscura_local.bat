@echo off
REM ============================================================
REM  🕵️ Obscura — Motor headless (start com 1 clique)
REM  Baixa o binario se faltar, sobe o servidor CDP com stealth
REM  (4 workers) e mostra o status via bridge.
REM  Parar: feche a janela "Obscura (motor headless)".
REM ============================================================
setlocal
cd /d "%~dp0SniperVideoEngine"

set BIN_DIR=.obscura-bin
set EXE=%BIN_DIR%\obscura.exe
set PORT=9222
set ZIP_URL=https://github.com/h4ckf0r0day/obscura/releases/latest/download/obscura-x86_64-windows-stealth.zip

echo [1/4] Verificando binario...
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
if exist "%EXE%" goto :have_bin

echo    Binario nao encontrado. Baixando do GitHub (v0.1.11, stealth)...
curl -sL --max-time 300 -o "%BIN_DIR%\obscura.zip" "%ZIP_URL%"
if errorlevel 1 (
    echo    curl falhou — tentando com PowerShell...
    powershell -Command "Invoke-WebRequest -Uri '%ZIP_URL%' -OutFile '%BIN_DIR%\obscura.zip'"
)
echo    Extraindo...
powershell -Command "Expand-Archive -Path '%BIN_DIR%\obscura.zip' -DestinationPath '%BIN_DIR%' -Force"

:have_bin
echo [2/4] Verificando porta %PORT%...
netstat -ano | findstr ":%PORT% " >nul 2>&1
if not errorlevel 1 (
    echo    Obscura ja esta rodando na porta %PORT%. Veja o status abaixo.
    goto :status
)

echo [3/4] Subindo o motor (workers 4, stealth)...
start "Obscura" cmd /k ""%EXE%" serve --port %PORT% --workers 4 --stealth"
timeout /t 5 /nobreak >nul

:status
echo [4/4] Status via bridge CDP...
python -c "import asyncio; from services.obscura_bridge import get_obscura_status; print(asyncio.run(get_obscura_status()))"
echo.
echo Pronto! No painel admin: pagina 🕵️ Obscura mostra telemetria de todos os agentes.
endlocal
