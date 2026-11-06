import sqlite3
import os
from werkzeug.security import generate_password_hash
from config import Config

def get_db_connection():
    """Tạo kết nối tới cơ sở dữ liệu SQLite và trả về đối tượng Connection."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Cho phép truy cập dữ liệu theo tên cột như dictionary
    conn.execute("PRAGMA foreign_keys = ON")  # Bật kiểm tra khóa ngoại
    return conn

def migrate_db():
    """Tự động nâng cấp cấu trúc bảng nếu database đã tồn tại từ trước."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # 1. Cập nhật bảng products: Hạn sử dụng, Ngày sản xuất, Thời hạn bảo quản
        cursor.execute("PRAGMA table_info(products)")
        prod_cols = [row[1] for row in cursor.fetchall()]
        if 'manufacturing_date' not in prod_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN manufacturing_date TEXT DEFAULT ''")
        if 'expiry_date' not in prod_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN expiry_date TEXT DEFAULT ''")
        if 'shelf_life' not in prod_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN shelf_life TEXT DEFAULT ''")

        # 2. Cập nhật bảng orders: Loại giao hàng, Khung giờ giao, Shipper phụ trách, Tiến độ giao
        cursor.execute("PRAGMA table_info(orders)")
        order_cols = [row[1] for row in cursor.fetchall()]
        if 'delivery_type' not in order_cols:
            cursor.execute("ALTER TABLE orders ADD COLUMN delivery_type TEXT DEFAULT 'standard'")
        if 'delivery_time_slot' not in order_cols:
            cursor.execute("ALTER TABLE orders ADD COLUMN delivery_time_slot TEXT DEFAULT 'Bất kỳ lúc nào'")
        if 'shipper_name' not in order_cols:
            cursor.execute("ALTER TABLE orders ADD COLUMN shipper_name TEXT DEFAULT ''")
        if 'delivery_status' not in order_cols:
            cursor.execute("ALTER TABLE orders ADD COLUMN delivery_status TEXT DEFAULT 'preparing'")

        # 3. Cập nhật bảng order_items: Hạn sử dụng của từng món khi mua
        cursor.execute("PRAGMA table_info(order_items)")
        item_cols = [row[1] for row in cursor.fetchall()]
        if 'expiry_date' not in item_cols:
            cursor.execute("ALTER TABLE order_items ADD COLUMN expiry_date TEXT DEFAULT ''")

        conn.commit()
    except Exception as e:
        print(f"[!] Migration status: {e}")
    finally:
        conn.close()

def init_db(force_recreate=False):
    """
    Khởi tạo cấu trúc các bảng trong cơ sở dữ liệu và nạp dữ liệu mẫu ban đầu.
    Nếu force_recreate=True, xóa database cũ và tạo mới hoàn toàn.
    """
    if force_recreate and os.path.exists(Config.DATABASE_PATH):
        try:
            os.remove(Config.DATABASE_PATH)
            print("[-] Đã xóa cơ sở dữ liệu cũ.")
        except Exception:
            pass

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Bảng USERS
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        fullname TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        role TEXT DEFAULT 'customer' CHECK(role IN ('admin', 'customer')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. Bảng CATEGORIES
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        icon TEXT DEFAULT 'fa-solid fa-basket-shopping',
        description TEXT,
        image_url TEXT
    )
    ''')

    # 3. Bảng PRODUCTS (Có quản lý Số lượng tồn kho & Hạn sử dụng)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        original_price REAL,
        unit TEXT NOT NULL,
        stock INTEGER NOT NULL DEFAULT 50,
        manufacturing_date TEXT DEFAULT '',
        expiry_date TEXT DEFAULT '',
        shelf_life TEXT DEFAULT '',
        image_url TEXT NOT NULL,
        is_featured INTEGER DEFAULT 0,
        is_new INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE RESTRICT
    )
    ''')

    # 4. Bảng ORDERS (Có quản lý Phương thức giao hàng, Khung giờ, Shipper, Phí ship, Tổng hóa đơn)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_code TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        customer_email TEXT,
        shipping_address TEXT NOT NULL,
        delivery_type TEXT DEFAULT 'standard',
        delivery_time_slot TEXT DEFAULT 'Bất kỳ lúc nào',
        shipper_name TEXT DEFAULT '',
        delivery_status TEXT DEFAULT 'preparing',
        payment_method TEXT NOT NULL CHECK(payment_method IN ('cod', 'banking')),
        payment_status TEXT DEFAULT 'unpaid' CHECK(payment_status IN ('unpaid', 'paid')),
        order_status TEXT DEFAULT 'pending' CHECK(order_status IN ('pending', 'confirmed', 'shipping', 'completed', 'cancelled')),
        subtotal REAL NOT NULL,
        shipping_fee REAL DEFAULT 20000,
        discount REAL DEFAULT 0,
        total_amount REAL NOT NULL,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
    )
    ''')

    # 5. Bảng ORDER_ITEMS (Lưu chi tiết từng sản phẩm và HSD)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER,
        product_name TEXT NOT NULL,
        product_image TEXT,
        expiry_date TEXT DEFAULT '',
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE SET NULL
    )
    ''')

    # 6. Bảng COUPONS
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS coupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        discount_percent REAL DEFAULT 0,
        discount_amount REAL DEFAULT 0,
        min_order_amount REAL DEFAULT 0,
        is_active INTEGER DEFAULT 1
    )
    ''')

    conn.commit()

    # Kiểm tra nếu chưa có dữ liệu thì nạp dữ liệu mẫu
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        seed_data(conn)
    else:
        ensure_product_expiry_dates(conn)

    conn.close()

    # Chạy nâng cấp cột nếu cần thiết sau khi đóng kết nối trước
    migrate_db()
    print("[+] Khởi tạo & Cập nhật CSDL thành công!")

def ensure_product_expiry_dates(conn):
    """Cập nhật bổ sung HSD cho các sản phẩm nếu đang để trống."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, category_id, expiry_date FROM products WHERE expiry_date IS NULL OR expiry_date = ''")
    empty_prods = cursor.fetchall()
    for p in empty_prods:
        p_id = p['id']
        cat_id = p['category_id']
        if cat_id in [1, 2]: # Rau củ quả
            nsx = "09/10/2026"
            hsd = "16/10/2026"
            shelf = "7 ngày (bảo quản 4-8°C)"
        elif cat_id == 3: # Thịt cá tươi
            nsx = "10/10/2026"
            hsd = "13/10/2026"
            shelf = "3 ngày (bảo quản 0-4°C)"
        elif cat_id == 4: # Sữa trứng
            nsx = "08/10/2026"
            hsd = "25/10/2026"
            shelf = "17 ngày"
        elif cat_id == 5: # Đồ khô
            nsx = "15/09/2026"
            hsd = "15/03/2027"
            shelf = "6 tháng"
        else: # Nước ép
            nsx = "10/10/2026"
            hsd = "12/10/2026"
            shelf = "48 giờ"
        cursor.execute("UPDATE products SET manufacturing_date = ?, expiry_date = ?, shelf_life = ? WHERE id = ?", (nsx, hsd, shelf, p_id))
    conn.commit()

def seed_data(conn):
    """Nạp dữ liệu mẫu ban đầu cho siêu thị FreshMart."""
    cursor = conn.cursor()
    print("[*] Đang nạp dữ liệu mẫu chi tiết (Seed Data)...")

    # 1. Tài khoản mẫu
    users_data = [
        ('admin', 'admin@freshmart.vn', generate_password_hash('admin123'), 'Quản Trị Viên FreshMart', '0988889999', 'Trụ sở FreshMart, Cầu Giấy, Hà Nội', 'admin'),
        ('khachhang', 'nguyenan@gmail.com', generate_password_hash('123456'), 'Nguyễn Văn An', '0912345678', 'Số 45 Ngõ 120 Hoàng Quốc Việt, Cầu Giấy, Hà Nội', 'customer')
    ]
    cursor.executemany('''
    INSERT INTO users (username, email, password_hash, fullname, phone, address, role)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', users_data)

    # 2. Danh mục sản phẩm
    categories_data = [
        ('Rau Củ Hữu Cơ', 'rau-cu-huu-co', 'fa-solid fa-carrot', 'Rau xanh, củ quả tươi sạch canh tác theo tiêu chuẩn hữu cơ VietGAP', 'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80'),
        ('Trái Cây Tươi Ngon', 'trai-cay-tuoi-ngon', 'fa-solid fa-apple-whole', 'Trái cây đặc sản nhiệt đới và hoa quả nhập khẩu tươi ngon ngọt mát', 'https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=600&auto=format&fit=crop&q=80'),
        ('Thịt & Hải Sản Tươi', 'thit-hai-san', 'fa-solid fa-fish-fins', 'Thịt bò, thịt heo sạch kiểm định, hải sản tươi sống đánh bắt trong ngày', 'https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?w=600&auto=format&fit=crop&q=80'),
        ('Sữa, Trứng & Bơ', 'sua-trung-bo', 'fa-solid fa-egg', 'Trứng gà ta thả vườn, sữa tươi thanh trùng và các chế phẩm bơ sữa nguyên chất', 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=600&auto=format&fit=crop&q=80'),
        ('Đồ Khô & Gia Vị', 'do-kho-gia-vi', 'fa-solid fa-jar', 'Gạo lứt, ngũ cốc dinh dưỡng, dầu ăn hạt và gia vị tự nhiên không phụ gia', 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=600&auto=format&fit=crop&q=80'),
        ('Nước Ép & Đồ Uống', 'nuoc-ep-do-uong', 'fa-solid fa-bottle-droplet', 'Nước ép trái cây ép chậm nguyên chất 100%, sinh tố và trà thảo mộc giải nhiệt', 'https://images.unsplash.com/photo-1622484216850-863a16900f89?w=600&auto=format&fit=crop&q=80')
    ]
    cursor.executemany('''
    INSERT INTO categories (name, slug, icon, description, image_url)
    VALUES (?, ?, ?, ?, ?)
    ''', categories_data)

    # 3. Sản phẩm có đầy đủ Số lượng tồn kho, NSX, HSD, Thời hạn bảo quản
    products_data = [
        # Rau củ hữu cơ
        (1, 'Cà chua Beef Đà Lạt hữu cơ', 'ca-chua-beef-da-lat', 'Cà chua Beef trồng theo chuẩn VietGAP tại Đà Lạt, quả to, mọng nước, giàu vitamin C.', 35000, 45000, 'Hộp 500g', 85, '09/10/2026', '19/10/2026', '10 ngày (0-4°C)', 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=600&auto=format&fit=crop&q=80', 1, 0),
        (1, 'Xà lách Lolo xanh thủy canh', 'xa-lach-lolo-xanh', 'Rau xà lách thủy canh tươi giòn, lá xoăn đẹp, rửa sạch ăn ngay, thích hợp làm salad.', 28000, 35000, 'Túi 300g', 60, '10/10/2026', '15/10/2026', '5 ngày (mát)', 'https://images.unsplash.com/photo-1622206151226-18ca2c9ab4a1?w=600&auto=format&fit=crop&q=80', 1, 1),
        (1, 'Súp lơ xanh Baby organic', 'sup-lo-xanh-baby', 'Bông cải xanh baby ngọn mềm, vị ngọt đậm, chứa nhiều chất chống oxy hóa và chất xơ.', 42000, 50000, 'Khay 400g', 45, '09/10/2026', '16/10/2026', '7 ngày', 'https://images.unsplash.com/photo-1584270354949-c26b0d5b4a0c?w=600&auto=format&fit=crop&q=80', 0, 1),
        (1, 'Cà rốt hữu cơ Đà Lạt', 'ca-rot-huu-co-da-lat', 'Cà rốt củ nhỏ đều, ruột đỏ cam đậm đà vị ngọt thanh tự nhiên, dùng ép nước hoặc nấu canh.', 26000, 32000, 'Túi 1kg', 110, '08/10/2026', '28/10/2026', '20 ngày', 'https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=600&auto=format&fit=crop&q=80', 0, 0),

        # Trái cây tươi ngon
        (2, 'Dâu tây giống Nhật Mộc Châu', 'dau-tay-giong-nhat', 'Dâu tây chín mọng hái tại vườn Mộc Châu, quả đỏ tươi, vị ngọt thanh xen chua nhẹ quyến rũ.', 135000, 160000, 'Hộp 500g', 35, '09/10/2026', '14/10/2026', '5 ngày (0-4°C)', 'https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=600&auto=format&fit=crop&q=80', 1, 1),
        (2, 'Xoài Cát Chu Cao Lãnh chín cây', 'xoai-cat-chu-cao-lanh', 'Xoài Cát Chu Đồng Tháp thơm lừng, thịt quả vàng ươm, mịn không xơ, vị ngọt đậm đà.', 55000, 68000, '1 kg', 70, '07/10/2026', '17/10/2026', '10 ngày', 'https://images.unsplash.com/photo-1553279768-865429fa0078?w=600&auto=format&fit=crop&q=80', 1, 0),
        (2, 'Bơ sáp 034 Đắk Lắk dẻo béo', 'bo-sap-034-dak-lak', 'Bơ giống 034 trái dài, hạt lép, cơm bơ dày vàng ươm béo ngậy, giàu dưỡng chất.', 60000, 75000, '1 kg', 80, '08/10/2026', '18/10/2026', '10 ngày', 'https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=600&auto=format&fit=crop&q=80', 0, 0),
        (2, 'Nho đen không hạt Mỹ', 'nho-den-khong-hat-my', 'Nho đen nhập khẩu vỏ mỏng, không hạt, quả giòn ngọt đậm đà, bổ sung năng lượng dồi dào.', 145000, 175000, 'Hộp 500g', 40, '05/10/2026', '25/10/2026', '20 ngày', 'https://images.unsplash.com/photo-1537640538966-79f369143f8f?w=600&auto=format&fit=crop&q=80', 1, 1),

        # Thịt & Hải sản tươi
        (3, 'Thịt ba chỉ heo sạch MEATDeli', 'thit-ba-chi-heo-meatdeli', 'Thịt heo mát công nghệ châu Âu, thớ thịt săn chắc, tỷ lệ nạc mỡ cân đối chuẩn vị.', 125000, 140000, 'Khay 500g', 50, '10/10/2026', '13/10/2026', '3 ngày (0-2°C)', 'https://images.unsplash.com/photo-1602470520998-f4a52199a3d6?w=600&auto=format&fit=crop&q=80', 1, 0),
        (3, 'Bắp bò Úc thái lát mềm mọng', 'bap-bo-uc-thai-lat', 'Bắp hoa bò Úc vân hoa đẹp mắt, thái lát mỏng tiện lợi nhúng lẩu hoặc xào cần tỏi.', 145000, 165000, 'Khay 400g', 40, '09/10/2026', '14/10/2026', '5 ngày (0-2°C)', 'https://images.unsplash.com/photo-1588168333986-5078d3ae3976?w=600&auto=format&fit=crop&q=80', 1, 1),
        (3, 'Cá hồi Na Uy tươi phi lê', 'ca-hoi-na-uy-phi-le', 'Phi lê cá hồi tươi Đại Tây Dương chuẩn sashimi, giàu Omega-3, thịt béo mềm tự nhiên.', 220000, 255000, 'Khay 300g', 30, '10/10/2026', '12/10/2026', '48 giờ ăn sống / 5 ngày nấu', 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=600&auto=format&fit=crop&q=80', 1, 0),
        (3, 'Tôm sú sinh thái Cà Mau', 'tom-su-sinh-thai-ca-mau', 'Tôm sú tự nhiên nuôi vùng rừng ngập mặn Cà Mau, vỏ mỏng thịt chắc ngọt đậm đà.', 185000, 210000, 'Hộp 500g', 45, '10/10/2026', '13/10/2026', '3 ngày (ướp đá)', 'https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?w=600&auto=format&fit=crop&q=80', 0, 1),

        # Sữa, Trứng & Bơ
        (4, 'Trứng gà ta thả vườn thảo mộc', 'trung-ga-ta-tha-vuon', 'Trứng gà từ đàn gà nuôi tự nhiên ăn thảo mộc, lòng đỏ to đậm cam, thơm bùi ngậy không tanh.', 45000, 52000, 'Vỉ 10 quả', 120, '08/10/2026', '28/10/2026', '20 ngày', 'https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=600&auto=format&fit=crop&q=80', 1, 0),
        (4, 'Sữa tươi thanh trùng Ba Vì không đường', 'sua-tuoi-thanh-trung-ba-vi', 'Sữa tươi 100% nguyên chất xử lý thanh trùng giữ trọn vị béo thơm và hệ vi sinh có lợi.', 38000, 42000, 'Chai 900ml', 75, '09/10/2026', '19/10/2026', '10 ngày (2-4°C)', 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=600&auto=format&fit=crop&q=80', 0, 1),
        (4, 'Phô mai tươi Mozzarella mềm', 'pho-mai-tuoi-mozzarella', 'Phô mai mềm mọng nước dùng kèm salad cà chua hoặc làm pizza kéo sợi thơm ngậy.', 85000, 98000, 'Khay 250g', 35, '01/10/2026', '01/11/2026', '30 ngày', 'https://images.unsplash.com/photo-1589881133595-a3c085cb731d?w=600&auto=format&fit=crop&q=80', 0, 0),

        # Đồ khô & Gia vị
        (5, 'Gạo lứt huyết rồng hữu cơ', 'gao-lut-huyet-rong', 'Gạo lứt đỏ nguyên cám giàu dinh dưỡng, hỗ trợ ăn kiêng eat clean, cơm dẻo thơm dễ nấu.', 65000, 75000, 'Túi 2kg', 90, '01/09/2026', '01/09/2027', '12 tháng', 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=600&auto=format&fit=crop&q=80', 1, 0),
        (5, 'Hạt Granola nướng mật ong hoa nhãn', 'granola-nuong-mat-ong', 'Hạnh nhân, óc chó, hạt điều và yến mạch nguyên cám nướng mật ong giòn rụm bổ dưỡng.', 115000, 135000, 'Hũ 500g', 65, '15/09/2026', '15/03/2027', '6 tháng', 'https://images.unsplash.com/photo-1517093157656-b9ec81643c15?w=600&auto=format&fit=crop&q=80', 1, 1),

        # Nước ép & Đồ uống
        (6, 'Nước cam sành ép tươi 100%', 'nuoc-cam-sanh-ep-tuoi', 'Nước cam sành nguyên chất vắt trong ngày, không thêm đường, giữ trọn tép cam tươi thơm mát.', 35000, 40000, 'Chai 350ml', 80, '10/10/2026', '12/10/2026', '48 giờ (0-4°C)', 'https://images.unsplash.com/photo-1613478223719-2ab802602423?w=600&auto=format&fit=crop&q=80', 1, 1),
        (6, 'Nước ép cần tây táo xanh detox', 'nuoc-ep-can-tay-tao-xanh', 'Hỗn hợp cần tây Đà Lạt kết hợp táo xanh và dưa leo mát lành, thanh lọc cơ thể tức thì.', 40000, 48000, 'Chai 350ml', 70, '10/10/2026', '11/10/2026', '24 giờ (lạnh)', 'https://images.unsplash.com/photo-1556881286-fc6915169721?w=600&auto=format&fit=crop&q=80', 0, 1)
    ]
    cursor.executemany('''
    INSERT INTO products (
        category_id, name, slug, description, price, original_price, unit, stock,
        manufacturing_date, expiry_date, shelf_life, image_url, is_featured, is_new
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', products_data)

    # 4. Mã giảm giá
    coupons_data = [
        ('FRESHMART10', 10, 0, 100000, 1),
        ('GIAM20K', 0, 20000, 150000, 1),
        ('FREESHIP', 0, 20000, 0, 1)
    ]
    cursor.executemany('''
    INSERT INTO coupons (code, discount_percent, discount_amount, min_order_amount, is_active)
    VALUES (?, ?, ?, ?, ?)
    ''', coupons_data)

    # 5. Đơn hàng mẫu có phương thức giao hàng và shipper
    orders_data = [
        (
            'FM-20261008-0001', 2, 'Nguyễn Văn An', '0912345678', 'nguyenan@gmail.com',
            'Số 45 Ngõ 120 Hoàng Quốc Việt, Cầu Giấy, Hà Nội',
            'express_2h', '14:00 - 17:00 (Chiều)', 'Nguyễn Văn Tuấn (0911.222.333)', 'delivered',
            'cod', 'paid', 'completed',
            260000, 35000, 26000, 269000, 'Giao giờ hành chính giúp mình nhé', '2026-10-08 09:30:00'
        ),
        (
            'FM-20261009-0002', 2, 'Nguyễn Văn An', '0912345678', 'nguyenan@gmail.com',
            'Số 45 Ngõ 120 Hoàng Quốc Việt, Cầu Giấy, Hà Nội',
            'standard', '08:00 - 11:00 (Sáng)', 'Trần Văn Hoàng (0922.333.444)', 'delivering',
            'banking', 'paid', 'shipping',
            355000, 0, 0, 355000, 'Để trước cửa phòng bảo vệ nếu không gọi được', '2026-10-09 14:15:00'
        ),
        (
            'FM-20261010-0003', None, 'Trần Thị Mai', '0987654321', 'maitran@gmail.com',
            'Tòa Landmark 81, P. 22, Bình Thạnh, TP.HCM',
            'express_2h', 'Bất kỳ lúc nào', '', 'preparing',
            'cod', 'unpaid', 'pending',
            170000, 35000, 20000, 185000, 'Giao trước 17h chiều nay', '2026-10-10 10:05:00'
        )
    ]
    cursor.executemany('''
    INSERT INTO orders (
        order_code, user_id, customer_name, customer_phone, customer_email,
        shipping_address, delivery_type, delivery_time_slot, shipper_name, delivery_status,
        payment_method, payment_status, order_status,
        subtotal, shipping_fee, discount, total_amount, note, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', orders_data)

    order_items_data = [
        (1, 1, 'Cà chua Beef Đà Lạt hữu cơ', 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=600&auto=format&fit=crop&q=80', '19/10/2026', 35000, 2, 70000),
        (1, 9, 'Thịt ba chỉ heo sạch MEATDeli', 'https://images.unsplash.com/photo-1602470520998-f4a52199a3d6?w=600&auto=format&fit=crop&q=80', '13/10/2026', 125000, 1, 125000),
        (1, 13, 'Trứng gà ta thả vườn thảo mộc', 'https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=600&auto=format&fit=crop&q=80', '28/10/2026', 45000, 1, 45000),
        (2, 5, 'Dâu tây giống Nhật Mộc Châu', 'https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=600&auto=format&fit=crop&q=80', '14/10/2026', 135000, 1, 135000),
        (2, 11, 'Cá hồi Na Uy tươi phi lê', 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=600&auto=format&fit=crop&q=80', '12/10/2026', 220000, 1, 220000),
        (3, 6, 'Xoài Cát Chu Cao Lãnh chín cây', 'https://images.unsplash.com/photo-1553279768-865429fa0078?w=600&auto=format&fit=crop&q=80', '17/10/2026', 55000, 2, 110000),
        (3, 8, 'Bơ sáp 034 Đắk Lắk dẻo béo', 'https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=600&auto=format&fit=crop&q=80', '18/10/2026', 60000, 1, 60000)
    ]
    cursor.executemany('''
    INSERT INTO order_items (
        order_id, product_id, product_name, product_image, expiry_date, price, quantity, subtotal
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', order_items_data)

    conn.commit()
    print("[+] Nạp dữ liệu mẫu hoàn tất!")

if __name__ == '__main__':
    init_db()
