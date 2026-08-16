@echo off
echo ========================================
echo   REINICIANDO SISTEMA DEZAFIRA 3.0
echo ========================================
echo.

echo [1/3] Parando processos anteriores...
taskkill /F /IM node.exe 2>nul
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo [2/3] Iniciando Backend...
start "Dezafira Backend" cmd /c "cd /d C:\Users\jonat\Desktop\dezafira3.0 && python server.py"
timeout /t 3 /nobreak >nul

echo [3/3] Iniciando Frontend...
start "Dezafira Frontend" cmd /c "cd /d C:\Users\jonat\Desktop\dezafira3.0\club-frontend && npx next dev"
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   SISTEMA INICIADO COM SUCESSO!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo Admin:    http://localhost:3000/admin
echo Ofertas:  http://localhost:3000/admin/fabrica-ofertas
echo.
echo Pressione qualquer tecla para fechar...
pause >nul
