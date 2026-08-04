@echo off
title RestaurantPro Mono - Serveur (version simple)
cd /d "%~dp0"
echo ========================================
echo   RestaurantPro Mono - Serveur
echo ========================================
echo.
echo Serveur demarre sur: http://127.0.0.1:8001
echo Fermez cette fenetre pour arreter le serveur.
echo.
venv\Scripts\python.exe -m daphne -b 0.0.0.0 -p 8001 config.asgi:application
pause
