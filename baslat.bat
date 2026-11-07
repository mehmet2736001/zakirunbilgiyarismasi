@echo off
cd /d "%~dp0"
title ZAKIRUN.COM - KUR'AN VE HAFIZLIK MERKEZI 2026
cls

echo =====================================================================
echo    ZAKIRUN.COM - KUR'AN OGRENME VE YARISMA PLATFORMU
echo =====================================================================
echo  Konum: %~dp0
echo  Port: 8000
echo.
echo  Moduller:
echo   - Ana Lobi ve 20 Hafiz Bot Arenasi
echo   - Kur'an Ogrenme Portali, Tecvid ve Dinleme
echo   - Google ile Hizli Giris ve Supabase Hesap Merkezi
echo   - Okunan Kelimeyi Bul ve Sure Ezberleme (Kolay/Zor)
echo   - Ayet Tamamlama, Ayet Bloklari ve Kelime Oyunu
echo   - 11 Basamakli Bilgi Yarismasi Merdiveni
echo   - Hifz Karnesi, Turnuvalar ve Hata Takip Merkezi
echo =====================================================================
echo.

rem Port 8000 onceden aciksa temizle
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>nul

set "PY_EXE=C:\Users\xd\AppData\Local\Programs\Python\Python311\python.exe"

if not exist "%PY_EXE%" (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PY_EXE=python"
    ) else (
        echo [HATA] Python bulunamadi!
        echo Lutfen Python 3.11 kurulu oldugundan emin olun.
        echo.
        pause
        exit /b 1
    )
)

echo [1/2] Tarayici aciliyor: http://127.0.0.1:8000/
start http://127.0.0.1:8000/

echo [2/2] Zakirun Sunucusu baslatiliyor...
echo (Sunucunun acik kalmasi icin bu pencereyi kapatmayin)
echo.

"%PY_EXE%" server.py 8000

echo.
echo Sunucu kapandi.
pause
