@echo off
title INSTALADOR E INICIALIZADOR DEZAFIRA LOCAL STUDIO
color 0b

echo =====================================================================
echo           INICIALIZANDO PLATAFORMA DEZAFIRA LOCAL STUDIO
echo                Automacao Global e Foco em Monetizacao
echo =====================================================================
echo.

:: 1. Verificar dependencias do Node.js e instalar no frontend se necessario
echo [*] Configurando ambiente Frontend (Next.js)...
cd open-generative-ai
if not exist node_modules (
    echo [!] node_modules nao encontrado no Frontend. Executando npm install...
    call npm install
) else (
    echo [OK] Dependencias do Frontend ja instaladas.
)

:: Iniciar o Frontend em segundo plano em uma nova janela de terminal
echo [*] Iniciando servidor do Frontend na porta 3000...
start "Dezafira Frontend (Next.js)" cmd /c "npm run dev"
cd ..

:: 2. Verificar dependencias do Python e instalar no Backend se necessario
echo [*] Configurando ambiente Backend (FastAPI)...
cd SniperVideoEngine
if not exist venv (
    echo [!] Criando ambiente virtual Python venv...
    python -m venv venv
)
call venv\Scripts\activate
echo [*] Instalando dependencias do requirements.txt...
pip install -r requirements.txt

:: 2.5. Iniciar Chrome real (CDP 9223) para o Obscura desbloquear o Google
echo [*] Iniciando Chrome real (CDP 9223) para SERP/Obscura...
if not exist ".chrome-profile" mkdir ".chrome-profile"
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
start "Chrome real (CDP 9223)" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9223 --remote-debugging-address=127.0.0.1 --user-data-dir="%~dp0SniperVideoEngine\.chrome-profile" --no-first-run --no-default-browser-check --disable-blink-features=AutomationControlled %PROXY_ARG% about:blank
timeout /t 5 /nobreak >nul

:: Iniciar o Backend
echo [*] Iniciando servidor do Backend na porta 8000...
echo.
echo =====================================================================
echo     [SUCESSO] A DEZAFIRA ESTA SUBINDO LOCALMENTE!
echo     - Front-end: http://localhost:3000
echo     - Back-end API: http://localhost:8000
echo =====================================================================
echo.
echo Pressione CTRL+C nesta janela para encerrar o backend.
echo.
uvicorn server:app --reload --port 8000
