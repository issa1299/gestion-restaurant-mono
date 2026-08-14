@echo off
title RestaurantPro - Caisse (impression silencieuse)
cd /d "%~dp0"

rem ============================================
rem   PC de caisse - RestaurantPro
rem   Ouvre la page de vente en mode kiosque
rem   avec impression silencieuse du ticket.
rem
rem   - --kiosk-printing : imprime directement
rem     sur l'imprimante par defaut, sans dialogue
rem   - --start-maximized : plein ecran
rem   - --guest : aucune session enregistree
rem ============================================

set URL=http://127.0.0.1:8001/ventes/

rem Chemin vers Microsoft Edge
set EDGE=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
if not exist "%EDGE%" set EDGE=C:\Program Files\Microsoft\Edge\Application\msedge.exe

if not exist "%EDGE%" (
    echo Edge introuvable. Verifiez le chemin ci-dessus.
    pause
    exit /b 1
)

start "" "%EDGE%" --kiosk-printing --start-maximized --guest "%URL%"