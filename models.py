import uuid
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection

class UserModel:
    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        return user

    @staticmethod
    def get_by_username_or_email(identifier):
        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?", 
            (identifier, identifier)
        ).fetchone()
        conn.close()
        return user

    @staticmethod
    def create(username, email, password, fullname, phone="", address="", role="customer"):
        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO users (username, email, password_hash, fullname, phone, address, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, fullname, phone, address, role))
            conn.commit()
            user_id = cursor.lastrowid
            return user_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def update_profile(user_id, fullname, phone, address):
        conn = get_db_connection()
        conn.execute('''
        UPDATE users SET fullname = ?, phone = ?, address = ? WHERE id = ?
        ''', (fullname, phone, address, user_id))
        conn.commit()
        conn.close()

    @staticmethod
    def get_all():
        conn = get_db_connection()
        users = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        conn.close()
        return users


class CategoryModel:
    @staticmethod
    def get_all():
        conn = get_db_connection()
        categories = conn.execute("SELECT * FROM categories ORDER BY id ASC").fetchall()
        conn.close()
        return categories

    @staticmethod
    def get_by_id(cat_id):
        conn = get_db_connection()
        category = conn.execute("SELECT * FROM categories WHERE id = ?", (cat_id,)).fetchone()
        conn.close()
        return category

    @staticmethod
    def get_with_product_count():
        conn = get_db_connection()
        query = '''
        SELECT c.*, COUNT(p.id) as product_count 
        FROM categories c
        LEFT JOIN products p ON c.id = p.category_id
        GROUP BY c.id
        ORDER BY c.id ASC
        '''
        results = conn.execute(query).fetchall()
        conn.close()
        return results

    @staticmethod
    def create(name, slug, icon, description, image_url=""):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO categories (name, slug, icon, description, image_url)
        VALUES (?, ?, ?, ?, ?)
        ''', (name, slug, icon, description, image_url))
        conn.commit()
        cat_id = cursor.lastrowid
        conn.close()
        return cat_id

    @staticmethod
    def delete(cat_id):
        conn = get_db_connection()
        conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        conn.commit()
        conn.close()


class ProductModel:
    @staticmethod
    def get_all():
        conn = get_db_connection()
        query = '''
        SELECT p.*, c.name as category_name 
        FROM products p
        JOIN categories c ON p.category_id = c.id
        ORDER BY p.id DESC
        '''
        products = conn.execute(query).fetchall()
        conn.close()
        return products

    @staticmethod
    def get_by_id(product_id):
        conn = get_db_connection()
        query = '''
        SELECT p.*, c.name as category_name, c.slug as category_slug
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
        '''
        product = conn.execute(query, (product_id,)).fetchone()
        conn.close()
        return product

    @staticmethod
    def get_featured(limit=8):
        conn = get_db_connection()
        query = '''
        SELECT p.*, c.name as category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.is_featured = 1
        ORDER BY p.id DESC
        LIMIT ?
        '''
        products = conn.execute(query, (limit,)).fetchall()
        conn.close()
        return products

    @staticmethod
    def get_new_arrivals(limit=8):
        conn = get_db_connection()
        query = '''
        SELECT p.*, c.name as category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.is_new = 1
        ORDER BY p.id DESC
        LIMIT ?
        '''
        products = conn.execute(query, (limit,)).fetchall()
        conn.close()
        return products

    @staticmethod
    def get_related(category_id, current_product_id, limit=4):
        conn = get_db_connection()
        query = '''
        SELECT p.*, c.name as category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.category_id = ? AND p.id != ?
        ORDER BY RANDOM()
        LIMIT ?
        '''
        products = conn.execute(query, (category_id, current_product_id, limit)).fetchall()
        conn.close()
        return products

    @staticmethod
    def search_and_filter(category_id=None, keyword=None, min_price=None, max_price=None, sort_by=None, page=1, per_page=12):
        conn = get_db_connection()
        params = []
        where_clauses = ["1=1"]

        if category_id:
            where_clauses.append("p.category_id = ?")
            params.append(category_id)

        if keyword:
            where_clauses.append("(p.name LIKE ? OR p.description LIKE ?)")
            search_param = f"%{keyword}%"
            params.extend([search_param, search_param])

        if min_price is not None and min_price != "":
            where_clauses.append("p.price >= ?")
            params.append(float(min_price))

        if max_price is not None and max_price != "":
            where_clauses.append("p.price <= ?")
            params.append(float(max_price))

        where_sql = " AND ".join(where_clauses)

        count_query = f"SELECT COUNT(*) FROM products p WHERE {where_sql}"
        total_items = conn.execute(count_query, params).fetchone()[0]

        order_sql = "ORDER BY p.id DESC"
        if sort_by == 'price_asc':
            order_sql = "ORDER BY p.price ASC"
        elif sort_by == 'price_desc':
            order_sql = "ORDER BY p.price DESC"
        elif sort_by == 'name_asc':
            order_sql = "ORDER BY p.name ASC"
        elif sort_by == 'featured':
            order_sql = "ORDER BY p.is_featured DESC, p.id DESC"

        offset = (page - 1) * per_page
        query = f'''
        SELECT p.*, c.name as category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE {where_sql}
        {order_sql}
        LIMIT ? OFFSET ?
        '''
        paged_params = list(params) + [per_page, offset]
        products = conn.execute(query, paged_params).fetchall()
        conn.close()

        total_pages = (total_items + per_page - 1) // per_page
        return products, total_items, total_pages

    @staticmethod
    def create(category_id, name, slug, description, price, original_price, unit, stock, 
               manufacturing_date="", expiry_date="", shelf_life="", image_url="", is_featured=0, is_new=1):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO products (
            category_id, name, slug, description, price, original_price, unit, stock,
            manufacturing_date, expiry_date, shelf_life, image_url, is_featured, is_new
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (category_id, name, slug, description, price, original_price, unit, stock,
              manufacturing_date, expiry_date, shelf_life, image_url, is_featured, is_new))
        conn.commit()
        product_id = cursor.lastrowid
        conn.close()
        return product_id

    @staticmethod
    def update(product_id, category_id, name, slug, description, price, original_price, unit, stock,
               manufacturing_date, expiry_date, shelf_life, image_url, is_featured, is_new):
        conn = get_db_connection()
        conn.execute('''
        UPDATE products SET 
            category_id = ?, name = ?, slug = ?, description = ?, price = ?, 
            original_price = ?, unit = ?, stock = ?, manufacturing_date = ?, 
            expiry_date = ?, shelf_life = ?, image_url = ?, is_featured = ?, is_new = ?
        WHERE id = ?
        ''', (category_id, name, slug, description, price, original_price, unit, stock,
              manufacturing_date, expiry_date, shelf_life, image_url, is_featured, is_new, product_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(product_id):
        conn = get_db_connection()
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()


class OrderModel:
    @staticmethod
    def create(user_id, customer_name, customer_phone, customer_email, shipping_address, payment_method, cart_items, 
               delivery_type='standard', delivery_time_slot='Bất kỳ lúc nào', discount=0, note=""):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        random_suffix = str(uuid.uuid4().hex[:4]).upper()
        order_code = f"FM-{today_str}-{random_suffix}"

        subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
        
        # Tính phí vận chuyển chính xác theo phương thức giao hàng
        if delivery_type == 'express_2h':
            # Giao siêu tốc 2h: 35.000đ, nếu đơn >= 300.000đ ưu đãi chỉ còn 15.000đ
            shipping_fee = 15000 if subtotal >= 300000 else 35000
        else:
            # Giao tiêu chuẩn: 20.000đ, nếu đơn >= 300.000đ MIỄN PHÍ hoàn toàn
            shipping_fee = 0 if subtotal >= 300000 else 20000

        total_amount = max(0, subtotal + shipping_fee - discount)
        payment_status = 'unpaid'
        order_status = 'pending'
        delivery_status = 'preparing'

        cursor.execute('''
        INSERT INTO orders (
            order_code, user_id, customer_name, customer_phone, customer_email,
            shipping_address, delivery_type, delivery_time_slot, delivery_status,
            payment_method, payment_status, order_status,
            subtotal, shipping_fee, discount, total_amount, note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_code, user_id, customer_name, customer_phone, customer_email,
            shipping_address, delivery_type, delivery_time_slot, delivery_status,
            payment_method, payment_status, order_status,
            subtotal, shipping_fee, discount, total_amount, note
        ))
        order_id = cursor.lastrowid

        # Lưu chi tiết từng món hàng kèm HSD và trừ số lượng tồn kho
        for item in cart_items:
            item_subtotal = item['price'] * item['quantity']
            expiry_val = item.get('expiry_date', '')
            cursor.execute('''
            INSERT INTO order_items (order_id, product_id, product_name, product_image, expiry_date, price, quantity, subtotal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, item['id'], item['name'], item['image_url'], expiry_val, item['price'], item['quantity'], item_subtotal))

            # Trừ số lượng tồn kho
            cursor.execute('''
            UPDATE products SET stock = MAX(0, stock - ?) WHERE id = ?
            ''', (item['quantity'], item['id']))

        conn.commit()
        conn.close()
        return order_code

    @staticmethod
    def get_by_code(order_code):
        conn = get_db_connection()
        order = conn.execute("SELECT * FROM orders WHERE order_code = ?", (order_code,)).fetchone()
        conn.close()
        return order

    @staticmethod
    def get_by_id(order_id):
        conn = get_db_connection()
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        conn.close()
        return order

    @staticmethod
    def get_items(order_id):
        conn = get_db_connection()
        items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
        conn.close()
        return items

    @staticmethod
    def get_user_orders(user_id):
        conn = get_db_connection()
        orders = conn.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
        conn.close()
        return orders

    @staticmethod
    def get_all():
        conn = get_db_connection()
        orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        conn.close()
        return orders

    @staticmethod
    def update_status(order_id, order_status, payment_status=None, delivery_status=None, shipper_name=None):
        conn = get_db_connection()
        updates = ["order_status = ?"]
        params = [order_status]

        if payment_status:
            updates.append("payment_status = ?")
            params.append(payment_status)

        if delivery_status:
            updates.append("delivery_status = ?")
            params.append(delivery_status)

        if shipper_name is not None:
            updates.append("shipper_name = ?")
            params.append(shipper_name)

        params.append(order_id)
        sql = f"UPDATE orders SET {', '.join(updates)} WHERE id = ?"
        conn.execute(sql, params)
        conn.commit()
        conn.close()

    @staticmethod
    def get_stats():
        conn = get_db_connection()
        total_revenue = conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE order_status != 'cancelled'").fetchone()[0]
        total_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        pending_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'pending'").fetchone()[0]
        total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        total_customers = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'customer'").fetchone()[0]
        recent_orders = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 5").fetchall()
        low_stock_products = conn.execute("SELECT * FROM products WHERE stock <= 20 ORDER BY stock ASC LIMIT 6").fetchall()
        conn.close()
        return {
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'total_products': total_products,
            'total_customers': total_customers,
            'recent_orders': recent_orders,
            'low_stock_products': low_stock_products
        }


class CouponModel:
    @staticmethod
    def validate(code, subtotal):
        conn = get_db_connection()
        coupon = conn.execute("SELECT * FROM coupons WHERE code = ? AND is_active = 1", (code.upper().strip(),)).fetchone()
        conn.close()
        if not coupon:
            return None, "Mã giảm giá không hợp lệ hoặc đã hết hạn!"
        
        if subtotal < coupon['min_order_amount']:
            return None, f"Đơn hàng cần đạt tối thiểu {coupon['min_order_amount']:,.0f} đ để áp dụng mã này!"

        discount = 0
        if coupon['discount_percent'] > 0:
            discount = (subtotal * coupon['discount_percent']) / 100
        elif coupon['discount_amount'] > 0:
            discount = coupon['discount_amount']

        return discount, "Áp dụng mã giảm giá thành công!"
