# FreshMart — Nền Tảng Siêu Thị Thực Phẩm Trực Tuyến

> **Đồ án Lập trình Web / Cơ sở dữ liệu Python — Kì 1**
> Dự án xây dựng một hệ thống siêu thị thực phẩm tươi sạch trực tuyến hoàn chỉnh với kết nối Cơ sở dữ liệu SQLite, giao diện tương thích đa thiết bị và đầy đủ nghiệp vụ thương mại điện tử: **Quản lý số lượng tồn kho, Hạn sử dụng, Giao hàng, Tính phí vận chuyển và Tổng hóa đơn**.

---

## 1. Giới Thiệu Dự Án & Các Tính Năng Cốt Lõi

**FreshMart** là nền tảng thương mại điện tử chuyên cung cấp rau củ quả hữu cơ, trái cây đặc sản, thịt cá tươi sống, trứng sữa và đồ khô dinh dưỡng đạt chuẩn VietGAP. Dự án được thiết kế theo mô hình MVC hiện đại, phân chia rõ ràng giữa tầng dữ liệu (Models), logic điều hướng (Controllers) và giao diện hiển thị (Templates).

### Các phân hệ nâng cấp mới:

1. **Quản lý Số lượng (Stock & Quantity Management)**:
   - Kiểm tra tồn kho thời gian thực khi thêm vào giỏ hàng và cập nhật số lượng.
   - Giới hạn số lượng mua tối đa bằng số lượng tồn kho thực tế, tự động cảnh báo khi vượt quá tồn kho.
   - Trừ kho tự động khi đơn hàng được đặt thành công.
   - Quản trị viên theo dõi tồn kho và nhận cảnh báo hàng sắp hết kho (`stock <= 20`).
2. **Quản lý Hạn sử dụng (Expiry Date & Shelf Life)**:
   - Lưu trữ rõ ràng **Ngày thu hoạch / Ngày sản xuất (NSX)**, **Hạn sử dụng (HSD)** và **Thời hạn bảo quản**.
   - Hiển thị badge HSD trực quan trên trang chủ, danh sách sản phẩm, chi tiết sản phẩm và trong giỏ hàng.
   - Quản trị viên có thể nhập và điều chỉnh HSD cho từng lô hàng trong Admin.
3. **Quản lý Giao hàng (Delivery Management)**:
   - **Giao tiêu chuẩn trong ngày**: Bảo quản mát, giao hàng trong ngày.
   - **Giao hỏa tốc 2 giờ (Express 2H)**: Đóng gói túi giữ nhiệt, shipper giao tận nơi trong 120 phút.
   - Khách hàng được chọn **Khung giờ nhận hàng thuận tiện** (Sáng 8-11h, Chiều 14-17h, Tối 18-20h hoặc Bất kỳ lúc nào).
   - Quản trị viên cập nhật tiến độ vận chuyển (*Đang đóng gói -> Đang giao -> Đã giao*) và gán Shipper phụ trách kèm số điện thoại.
4. **Tính Phí Vận Chuyển & Tổng Hóa Đơn (Shipping Fee & Detailed Invoice)**:
   - Thanh tiến độ Freeship trực quan: *"Mua thêm X đ để được MIỄN PHÍ VẬN CHUYỂN!"*.
   - Đơn hàng từ 300.000đ trở lên được **Miễn phí vận chuyển tiêu chuẩn (0đ)** hoặc ưu đãi cước hỏa tốc 2h chỉ còn 15.000đ.
   - Bảng kê chi tiết hóa đơn: Tiền hàng + Phí giao hàng - Giảm giá voucher = **Tổng hóa đơn thanh toán**.
   - Tích hợp tính năng **In Hóa Đơn Bán Lẻ** chuẩn siêu thị tiện lợi khi giao hàng.

---

## 2. Kiến Trúc & Cấu Trúc Thư Mục

```text
FreshMart/
├── app.py                      # Flask Controller: Định tuyến & điều khiển nghiệp vụ chính
├── config.py                   # Cấu hình hệ thống, SECRET_KEY, CSDL, hotline, địa chỉ
├── database.py                 # Kết nối SQLite, tự động khởi tạo bảng, migration & seed data
├── models.py                   # Tầng truy xuất dữ liệu: UserModel, ProductModel, OrderModel...
├── requirements.txt            # Thư viện phụ thuộc (Flask, Werkzeug)
├── run.bat                     # File chạy tự động 1-click cho Windows
├── run.ps1                     # Script khởi chạy cho PowerShell
├── README.md                   # Tài liệu hướng dẫn sử dụng và báo cáo đồ án
├── static/
│   ├── css/style.css           # CSS tùy biến & hiệu ứng giao diện
│   └── js/main.js              # Giỏ hàng AJAX, cập nhật phí ship động, điền tài khoản mẫu
└── templates/
    ├── base.html               # Khung layout dùng chung (Navbar, Footer, Flash alerts)
    ├── index.html              # Trang chủ: Banner, danh mục, sản phẩm bán chạy có HSD
    ├── products.html           # Danh sách sản phẩm: Bộ lọc giá, danh mục, tìm kiếm, phân trang
    ├── product_detail.html     # Chi tiết sản phẩm: NSX, HSD, bảo quản, số lượng tồn kho
    ├── cart.html               # Giỏ hàng: Bộ tăng giảm số lượng, chọn giao hàng, tính phí ship
    ├── checkout.html           # Đặt hàng & thanh toán: Khung giờ giao hàng, COD hoặc VietQR
    ├── order_success.html      # Xác nhận đơn hàng, bảng kê hóa đơn bán lẻ, in hóa đơn & VietQR
    ├── login.html              # Đăng nhập (kèm nút 1-click điền nhanh tài khoản Admin/Khách)
    ├── register.html           # Đăng ký tài khoản khách hàng mới
    ├── profile.html            # Hồ sơ cá nhân & tra cứu lịch sử đơn hàng
    ├── order_detail.html       # Chi tiết hóa đơn và tiến độ vận chuyển của đơn hàng
    └── admin/
        ├── admin_base.html     # Layout riêng cho phân hệ Quản trị viên
        ├── dashboard.html      # Thống kê doanh thu, tổng đơn, cảnh báo tồn kho thấp
        ├── products.html       # Quản lý sản phẩm: Tồn kho, Hạn sử dụng, CRUD
        ├── product_form.html   # Form thêm/sửa sản phẩm kèm HSD, NSX và số lượng kho
        ├── categories.html     # Quản lý danh mục ngành hàng
        ├── orders.html         # Quản lý đơn hàng, điều phối shipper và tiến độ giao hàng
        └── users.html          # Quản lý danh sách thành viên
```

---

## 3. Lược Đồ Cơ Sở Dữ Liệu (Database Schema)

CSDL bao gồm các bảng quan hệ chuẩn hóa:

1. `users`: Tài khoản khách hàng và quản trị viên (`username`, `password_hash`, `role`...).
2. `categories`: Danh mục thực phẩm (`name`, `slug`, `icon`, `description`...).
3. `products`: Sản phẩm với thông tin số lượng tồn kho (`stock`), ngày sản xuất (`manufacturing_date`), hạn sử dụng (`expiry_date`), thời hạn bảo quản (`shelf_life`).
4. `orders`: Đơn hàng lưu trữ phương thức giao hàng (`delivery_type`), khung giờ hẹn (`delivery_time_slot`), shipper phụ trách (`shipper_name`), tiến độ (`delivery_status`), tiền hàng (`subtotal`), phí vận chuyển (`shipping_fee`), giảm giá (`discount`), tổng hóa đơn (`total_amount`).
5. `order_items`: Chi tiết từng món trong đơn hàng kèm hạn sử dụng của lô hàng (`expiry_date`), đơn giá và số lượng.
6. `coupons`: Mã ưu đãi giảm giá (`code`, `discount_percent`, `discount_amount`...).

---

## 4. Hướng Dẫn Cài Đặt & Khởi Chạy

### Cách 1: Khởi chạy 1-Click (Khuyến nghị trên Windows)

Nhấp đúp chuột vào file:

```
run.bat
```

*(File sẽ tự động kiểm tra Python, cài đặt thư viện cần thiết, tự động cập nhật CSDL và mở trình duyệt web tại `http://127.0.0.1:5000`)*.

### Cách 2: Khởi chạy thủ công qua Terminal / CMD / PowerShell

```bash
cd "d:\Project Kì 1\FreshMart"
py -m pip install -r requirements.txt
py database.py
py app.py
```

Sau đó truy cập trình duyệt tại: **`http://127.0.0.1:5000`**

---

## 5. Tài Khoản Mẫu Trải Nghiệm & Chấm Điểm

| Vai trò                           | Tên đăng nhập | Mật khẩu   | Chức năng kiểm thử                                                                         |
| ---------------------------------- | ----------------- | ------------ | ---------------------------------------------------------------------------------------------- |
| **Quản trị viên (Admin)** | `admin`         | `admin123` | Quản lý kho hàng, cập nhật HSD & số lượng tồn kho, duyệt đơn, điều phối shipper |
| **Khách hàng**             | `khachhang`     | `123456`   | Mua sắm, kiểm tra HSD, tăng giảm số lượng, chọn giờ giao hàng, in hóa đơn         |

> [!TIP]
> Tại trang **Đăng nhập**, có sẵn 2 nút bấm **"Admin"** và **"Khách hàng"** để tự động điền tài khoản chỉ với 1 cú click chuột!
> **Mã voucher thử nghiệm**: `FRESHMART10` (Giảm 10%), `GIAM20K` (Giảm 20.000đ).
