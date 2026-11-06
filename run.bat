@echo off
chcp 65001 >nul
echo ====================================================================
echo             FRESHMART — SIÊU THỊ THỰC PHẨM TRỰC TUYẾN
echo                 Đồ Án Lập Trình Python Kì 1
echo ====================================================================
echo.

cd /d "%~dp0"

echo [*] Đang kiểm tra Python...
set PYTHON_CMD=py
%PYTHON_CMD% --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    set PYTHON_CMD=python
    %PYTHON_CMD% --version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [!] Khong tim thay Python. Vui long cai dat Python 3 tu python.org!
        pause
        exit /b 1
    )
)

echo [+] Su dung: %PYTHON_CMD%
echo.

echo [*] Dang cai dat/kiem tra thu vien can thiet tu requirements.txt...
%PYTHON_CMD% -m pip install -r requirements.txt

echo.
echo [*] Khoi tao co so du lieu SQLite (neu chua co)...
%PYTHON_CMD% database.py

echo.
echo ====================================================================
echo  [+] KHOI DONG SERVER FRESHMART THANH CONG!
echo  - Dia chi website: http://127.0.0.1:5000
echo  - Tai khoan Admin: admin / admin123
echo  - Tai khoan Khach: khachhang / 123456
echo ====================================================================
echo.

start http://127.0.0.1:5000

%PYTHON_CMD% app.py

pause
