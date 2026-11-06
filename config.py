import os

class Config:
    # Khóa bí mật cho session Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'freshmart-super-secret-key-2026')
    
    # Đường dẫn thư mục gốc dự án
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Đường dẫn cơ sở dữ liệu SQLite
    DATABASE_PATH = os.path.join(BASE_DIR, 'freshmart.db')
    
    # Thư mục lưu trữ hình ảnh tải lên (nếu có)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    
    # Phân trang sản phẩm
    ITEMS_PER_PAGE = 12
    
    # Thông tin cửa hàng
    STORE_NAME = "FreshMart — Siêu Thị Thực Phẩm Tươi Sạch"
    STORE_HOTLINE = "1900 6868"
    STORE_EMAIL = "support@freshmart.vn"
    STORE_ADDRESS = "Số 128 Đường Xuân Thủy, Cầu Giấy, Hà Nội"
    
    # Phí vận chuyển mặc định (VNĐ)
    DEFAULT_SHIPPING_FEE = 20000
    FREE_SHIPPING_THRESHOLD = 300000 # Đơn trên 300.000đ được miễn phí vận chuyển
