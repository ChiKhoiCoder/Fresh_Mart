# Script khởi chạy nhanh FreshMart trên Windows PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "====================================================================" -ForegroundColor Green
Write-Host "            FRESHMART — SIÊU THỊ THỰC PHẨM TRỰC TUYẾN" -ForegroundColor Yellow
Write-Host "                Đồ Án Lập Trình Python Kì 1" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Green

Set-Location $PSScriptRoot

$pythonCmd = "py"
try {
    & $pythonCmd --version | Out-Null
} catch {
    $pythonCmd = "python"
}

Write-Host "[+] Sử dụng lệnh Python: $pythonCmd" -ForegroundColor Cyan
Write-Host "[*] Đang cài đặt thư viện..." -ForegroundColor Gray
& $pythonCmd -m pip install -r requirements.txt

Write-Host "[*] Kiểm tra & khởi tạo CSDL SQLite..." -ForegroundColor Gray
& $pythonCmd database.py

Write-Host "====================================================================" -ForegroundColor Green
Write-Host " [+] Đang mở trình duyệt: http://127.0.0.1:5000" -ForegroundColor Green
Write-Host " - Admin: admin / admin123" -ForegroundColor Yellow
Write-Host " - Khách hàng: khachhang / 123456" -ForegroundColor Yellow
Write-Host "====================================================================" -ForegroundColor Green

Start-Process "http://127.0.0.1:5000"
& $pythonCmd app.py
