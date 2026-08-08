@echo off
REM ============================================================
REM  🚀 Chrome real + Obscura — start com 1 clique
REM  Sobe o Chrome REAL (instalado) com debugging remoto na 9223
REM  e profile persistente (.chrome-profile), para o bridge
REM  desbloquear o Google (SERP/PAA reais) nos agentes de dores.
REM  O Obscura (9222) continua sendo o fallback automático.
REM  Parar: feche a janela "Chrome real (CDP 9223)".
REM ============================================================
setlocal
cd /d "%~dp0SniperVideoEngine"

set CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe
if not exist "%CHROME%" set CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe
if not exist "%CHROME%" (
    echo [!] Chrome nao encontrado. Instale o Google Chrome.
    pause
    exit /b 1
)

set PROFILE=%CD%\.chrome-profile
if not exist "%PROFILE%" mkdir "%PROFILE%"

echo [1/2] Subindo Chrome real (CDP 9223) com profile persistente...
set PROXY_URL=
for /f "usebackq tokens=1,* delims==" %%a in ("%CD%\.env") do (
    if "%%a"=="OBSCURA_PROXY_URL" if not "%%b"=="" set PROXY_URL=%%b
)
if defined PROXY_URL (
    echo    [proxy] residencial ativo: %PROXY_URL%
) else (
    echo    [proxy] nao configurado (OBSCURA_PROXY_URL vazio no .env)
)
set PROXY_ARG=
if defined PROXY_URL set PROXY_ARG=--proxy-server="%PROXY_URL%"
start "Chrome real (CDP 9223)" "%CHROME%" --remote-debugging-port=9223 --remote-debugging-address=127.0.0.1 --user-data-dir="%PROFILE%" --no-first-run --no-default-browser-check --disable-blink-features=AutomationControlled %PROXY_ARG% about:blank

echo [2/2] Verificando CDP na 9223...
timeout /t 6 /nobreak >nul
curl -s http://127.0.0.1:9223/json/version | findstr /i "Browser"
echo.
echo Chrome de pe em ws://127.0.0.1:9223/devtools/browser
echo O bridge usa Chrome para Google; Obscura (9222) fica de fallback.
pause
