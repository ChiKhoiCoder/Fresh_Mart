import os
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, 
    session, flash, jsonify
)
from werkzeug.security import check_password_hash
from config import Config
from database import init_db, migrate_db, get_db_connection
from models import UserModel, CategoryModel, ProductModel, OrderModel, CouponModel

app = Flask(__name__)
app.config.from_object(Config)

# Đảm bảo database được khởi tạo và nâng cấp khi ứng dụng chạy
try:
    if not os.path.exists(Config.DATABASE_PATH):
        init_db()
    else:
        migrate_db()
except Exception as e:
    print(f"[!] Khởi tạo database notice: {e}")

# ==========================================
# JINJA TEMPLATE FILTERS & HELPERS
# ==========================================
@app.template_filter('currency')
def format_currency(value):
    """Định dạng số tiền sang chuẩn tiền tệ Việt Nam (VD: 35.000 đ)"""
    try:
        val = float(value or 0)
        return f"{val:,.0f} đ".replace(',', '.')
    except (ValueError, TypeError):
        return "0 đ"

# Context processor: Cung cấp biến dùng chung cho tất cả giao diện
@app.context_processor
def inject_common_variables():
    try:
        categories = CategoryModel.get_all()
    except Exception:
        categories = []
    
    # Tính tổng số lượng hàng trong giỏ
    cart = session.get('cart', {})
    cart_count = sum(cart.values()) if isinstance(cart, dict) else 0

    # Lấy thông tin user hiện tại nếu đã đăng nhập
    current_user = None
    if 'user_id' in session:
        try:
            current_user = UserModel.get_by_id(session['user_id'])
        except Exception:
            current_user = None

    return {
        'all_categories': categories,
        'cart_count': cart_count,
        'current_user': current_user,
        'store_name': Config.STORE_NAME,
        'store_hotline': Config.STORE_HOTLINE,
        'store_address': Config.STORE_ADDRESS
    }

# ==========================================
# AUTHENTICATION DECORATORS
# ==========================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Vui lòng đăng nhập để tiếp tục!", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'admin':
            flash("Bạn không có quyền truy cập trang quản trị!", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# CART & SHIPPING FEE CALCULATION HELPER
# ==========================================
def get_cart_details(custom_delivery_type=None):
    """
    Tính toán chi tiết giỏ hàng, số lượng tồn kho, hạn sử dụng,
    phí vận chuyển và tổng hóa đơn. 100% an toàn không gây lỗi IndexError hay KeyError.
    """
    cart = session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
        session['cart'] = cart

    cart_items = []
    subtotal = 0.0

    for prod_id_str, qty in list(cart.items()):
        try:
            prod_id = int(prod_id_str)
            qty = max(1, int(qty))
        except (ValueError, TypeError):
            cart.pop(prod_id_str, None)
            continue

        try:
            product = ProductModel.get_by_id(prod_id)
        except Exception as e:
            print(f"[!] Lỗi truy vấn sản phẩm {prod_id}: {e}")
            product = None

        if product:
            p = dict(product)
            stock_val = int(p.get('stock') or 50)
            if qty > stock_val:
                qty = max(1, stock_val)
                cart[prod_id_str] = qty

            price_val = float(p.get('price') or 0)
            item_subtotal = price_val * qty
            subtotal += item_subtotal

            cart_items.append({
                'id': p.get('id', prod_id),
                'name': p.get('name', 'Sản phẩm tươi'),
                'price': price_val,
                'original_price': p.get('original_price'),
                'unit': p.get('unit', 'Kg'),
                'image_url': p.get('image_url', ''),
                'quantity': qty,
                'subtotal': item_subtotal,
                'stock': stock_val,
                'manufacturing_date': p.get('manufacturing_date') or 'Mới thu hoạch',
                'expiry_date': p.get('expiry_date') or 'Tươi trong ngày',
                'shelf_life': p.get('shelf_life') or 'Bảo quản nhiệt độ 4-8°C'
            })
        else:
            cart.pop(prod_id_str, None)

    session['cart'] = cart
    session.modified = True

    # Xác định hình thức giao hàng
    if custom_delivery_type:
        session['delivery_type'] = custom_delivery_type
    delivery_type = session.get('delivery_type', 'standard')

    # Tính phí vận chuyển (Shipping fee)
    if subtotal == 0:
        shipping_fee = 0
    elif session.get('coupon_code') == 'FREESHIP':
        shipping_fee = 0
    elif delivery_type == 'express_2h':
        shipping_fee = 15000 if subtotal >= Config.FREE_SHIPPING_THRESHOLD else 35000
    else:
        shipping_fee = 0 if subtotal >= Config.FREE_SHIPPING_THRESHOLD else Config.DEFAULT_SHIPPING_FEE

    discount = float(session.get('discount_amount') or 0)
    total = max(0, subtotal + shipping_fee - discount)
    free_shipping_needed = max(0, Config.FREE_SHIPPING_THRESHOLD - subtotal)

    # Tính phần trăm tiến độ Freeship trực tiếp tại Python (tránh lỗi Jinja2)
    if Config.FREE_SHIPPING_THRESHOLD > 0:
        progress_pct = min(100, int((subtotal / Config.FREE_SHIPPING_THRESHOLD) * 100))
    else:
        progress_pct = 100

    return {
        'items': cart_items,
        'item_list': cart_items,
        'items_list': cart_items,
        'total_items_count': len(cart_items),
        'subtotal': subtotal,
        'delivery_type': delivery_type,
        'shipping_fee': shipping_fee,
        'discount': discount,
        'total': total,
        'coupon_code': session.get('coupon_code'),
        'free_shipping_needed': free_shipping_needed,
        'progress_pct': progress_pct
    }

# ==========================================
# CLIENT ROUTES (GIAO DIỆN KHÁCH HÀNG)
# ==========================================

@app.route('/')
def index():
    """Trang chủ siêu thị FreshMart"""
    featured_products = ProductModel.get_featured(limit=8)
    new_products = ProductModel.get_new_arrivals(limit=8)
    categories = CategoryModel.get_with_product_count()
    return render_template('index.html', 
                           featured_products=featured_products, 
                           new_products=new_products,
                           categories=categories)

@app.route('/products')
def products():
    """Danh sách sản phẩm kèm bộ lọc, tìm kiếm và phân trang"""
    category_id = request.args.get('category', type=int)
    keyword = request.args.get('q', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', 'default')
    page = request.args.get('page', 1, type=int)

    selected_category = None
    if category_id:
        selected_category = CategoryModel.get_by_id(category_id)

    products_list, total_items, total_pages = ProductModel.search_and_filter(
        category_id=category_id,
        keyword=keyword,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        page=page,
        per_page=Config.ITEMS_PER_PAGE
    )

    return render_template('products.html',
                           products=products_list,
                           total_items=total_items,
                           total_pages=total_pages,
                           current_page=page,
                           selected_category=selected_category,
                           current_category_id=category_id,
                           keyword=keyword,
                           min_price=min_price,
                           max_price=max_price,
                           sort_by=sort_by)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Chi tiết sản phẩm và hạn sử dụng"""
    product = ProductModel.get_by_id(product_id)
    if not product:
        flash("Sản phẩm không tồn tại!", "warning")
        return redirect(url_for('products'))
    
    related_products = ProductModel.get_related(product['category_id'], product_id, limit=4)
    return render_template('product_detail.html', product=product, related_products=related_products)

# ==========================================
# CART ROUTES (GIỎ HÀNG, SỐ LƯỢNG & PHÍ SHIP)
# ==========================================

@app.route('/cart')
def cart():
    """Xem giỏ hàng và bảng tính phí vận chuyển"""
    try:
        cart_data = get_cart_details()
    except Exception as e:
        print(f"[!] Lỗi khi lấy thông tin giỏ hàng: {e}")
        cart_data = {
            'item_list': [],
            'subtotal': 0,
            'delivery_type': 'standard',
            'shipping_fee': 0,
            'discount': 0,
            'total': 0,
            'coupon_code': None,
            'free_shipping_needed': Config.FREE_SHIPPING_THRESHOLD,
            'progress_pct': 0
        }
    return render_template('cart.html', cart=cart_data)

@app.route('/cart/add/<int:product_id>', methods=['POST', 'GET'])
def cart_add(product_id):
    """Thêm sản phẩm vào giỏ hàng và kiểm tra tồn kho"""
    product = ProductModel.get_by_id(product_id)
    if not product:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Sản phẩm không tồn tại!'}), 404
        flash("Sản phẩm không tồn tại!", "error")
        return redirect(url_for('products'))

    p = dict(product)
    stock_val = int(p.get('stock') or 0)

    # Xử lý số lượng an toàn không bị lỗi ép kiểu
    raw_qty = request.form.get('quantity') or request.args.get('quantity') or 1
    try:
        quantity = int(raw_qty)
        if quantity < 1:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1

    cart = session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    
    prod_id_str = str(product_id)
    current_qty = cart.get(prod_id_str, 0)
    new_qty = current_qty + quantity

    # Kiểm tra số lượng tồn kho
    if stock_val <= 0:
        msg = f"Sản phẩm '{p['name']}' hiện đã hết hàng trong kho!"
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': msg}), 400
        flash(msg, "warning")
        return redirect(request.referrer or url_for('cart'))

    if new_qty > stock_val:
        cart[prod_id_str] = stock_val
        session['cart'] = cart
        session.modified = True
        msg = f"Kho chỉ còn lại {stock_val} {p['unit']}. Đã tự động điều chỉnh về tối đa!"
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': msg, 'cart_count': sum(cart.values())})
        flash(msg, "warning")
        return redirect(url_for('cart'))

    cart[prod_id_str] = new_qty
    session['cart'] = cart
    session.modified = True

    total_count = sum(cart.values())
    msg = f"Đã thêm {quantity} {p['unit']} '{p['name']}' vào giỏ hàng!"

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': msg, 'cart_count': total_count})

    redirect_dest = request.args.get('redirect')
    if redirect_dest == 'checkout':
        return redirect(url_for('checkout'))
    elif redirect_dest == 'cart':
        return redirect(url_for('cart'))

    flash(msg, "success")
    return redirect(request.referrer or url_for('cart'))

@app.route('/cart/change-qty/<int:product_id>/<action>')
def cart_change_qty(product_id, action):
    """Tăng hoặc giảm 1 đơn vị số lượng sản phẩm bằng liên kết an toàn"""
    cart = session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    
    prod_key = str(product_id)
    if prod_key in cart:
        product = ProductModel.get_by_id(product_id)
        current_qty = cart[prod_key]
        stock_val = product['stock'] if product else 999

        if action == 'increase':
            if current_qty >= stock_val:
                flash(f"Kho chỉ còn lại tối đa {stock_val} sản phẩm!", "warning")
            else:
                cart[prod_key] = current_qty + 1
        elif action == 'decrease':
            if current_qty > 1:
                cart[prod_key] = current_qty - 1
            else:
                cart.pop(prod_key, None)
                flash("Đã xóa sản phẩm khỏi giỏ!", "info")
        session['cart'] = cart
        session.modified = True

    return redirect(url_for('cart'))

@app.route('/cart/update', methods=['POST'])
def cart_update():
    """Cập nhật số lượng sản phẩm nhập trực tiếp từ ô input"""
    product_id = request.form.get('product_id')
    raw_qty = request.form.get('quantity', 1)

    try:
        quantity = int(raw_qty)
    except (ValueError, TypeError):
        quantity = 1

    cart = session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}

    if product_id and str(product_id) in cart:
        prod_key = str(product_id)
        product = ProductModel.get_by_id(int(product_id))

        if quantity <= 0:
            cart.pop(prod_key, None)
            flash("Đã xóa sản phẩm khỏi giỏ hàng!", "info")
        elif product and quantity > product['stock']:
            cart[prod_key] = product['stock']
            flash(f"Số lượng yêu cầu vượt quá tồn kho ({product['stock']} {product['unit']})!", "warning")
        else:
            cart[prod_key] = quantity

        session['cart'] = cart
        session.modified = True

    return redirect(url_for('cart'))

@app.route('/cart/set-delivery', methods=['POST', 'GET'])
def cart_set_delivery():
    """Chuyển đổi phương thức giao hàng và tự động cập nhật phí vận chuyển"""
    delivery_type = request.form.get('delivery_type') or request.args.get('delivery_type', 'standard')
    cart_data = get_cart_details(custom_delivery_type=delivery_type)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'delivery_type': cart_data['delivery_type'],
            'shipping_fee': cart_data['shipping_fee'],
            'total': cart_data['total']
        })

    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:product_id>')
def cart_remove(product_id):
    """Xóa sản phẩm khỏi giỏ hàng"""
    prod_id_str = str(product_id)
    cart = session.get('cart', {})
    if isinstance(cart, dict) and prod_id_str in cart:
        cart.pop(prod_id_str, None)
        session['cart'] = cart
        session.modified = True
        flash("Đã xóa sản phẩm khỏi giỏ hàng!", "info")
    return redirect(url_for('cart'))

@app.route('/cart/clear')
def cart_clear():
    """Xóa toàn bộ giỏ hàng"""
    session.pop('cart', None)
    session.pop('coupon_code', None)
    session.pop('discount_amount', None)
    session.pop('delivery_type', None)
    flash("Đã làm trống giỏ hàng!", "info")
    return redirect(url_for('cart'))

@app.route('/apply-coupon', methods=['POST'])
def apply_coupon():
    """Áp dụng mã giảm giá"""
    code = request.form.get('coupon_code', '').strip().upper()
    cart_data = get_cart_details()

    if not code:
        flash("Vui lòng nhập mã giảm giá!", "warning")
        return redirect(url_for('cart'))

    discount, message = CouponModel.validate(code, cart_data['subtotal'])
    if discount is not None:
        session['coupon_code'] = code
        session['discount_amount'] = discount
        flash(f"{message} (Tiết kiệm {discount:,.0f} đ)", "success")
    else:
        flash(message, "danger")

    return redirect(url_for('cart'))

@app.route('/remove-coupon')
def remove_coupon():
    """Hủy mã giảm giá"""
    session.pop('coupon_code', None)
    session.pop('discount_amount', None)
    flash("Đã hủy áp dụng mã giảm giá!", "info")
    return redirect(url_for('cart'))

# ==========================================
# CHECKOUT & INVOICE (ĐẶT HÀNG & HÓA ĐƠN)
# ==========================================

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Trang thanh toán đơn hàng & chọn lịch giao hàng"""
    delivery_type_param = request.args.get('delivery_type')
    cart_data = get_cart_details(custom_delivery_type=delivery_type_param)

    if not cart_data['items']:
        flash("Giỏ hàng của bạn đang trống!", "warning")
        return redirect(url_for('products'))

    user = None
    if 'user_id' in session:
        user = UserModel.get_by_id(session['user_id'])

    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        customer_phone = request.form.get('customer_phone', '').strip()
        customer_email = request.form.get('customer_email', '').strip()
        shipping_address = request.form.get('shipping_address', '').strip()
        delivery_type = request.form.get('delivery_type', 'standard')
        delivery_time_slot = request.form.get('delivery_time_slot', 'Bất kỳ lúc nào')
        payment_method = request.form.get('payment_method', 'cod')
        note = request.form.get('note', '').strip()

        if not customer_name or not customer_phone or not shipping_address:
            flash("Vui lòng điền đầy đủ họ tên, số điện thoại và địa chỉ giao hàng!", "danger")
            return render_template('checkout.html', cart=cart_data, user=user)

        # Kiểm tra lại số lượng tồn kho trước khi chốt đơn
        for item in cart_data['items']:
            prod_check = ProductModel.get_by_id(item['id'])
            if prod_check and prod_check['stock'] < item['quantity']:
                flash(f"Sản phẩm '{item['name']}' vừa hết hàng hoặc chỉ còn {prod_check['stock']} {item['unit']}!", "danger")
                return redirect(url_for('cart'))

        user_id = session.get('user_id')
        order_code = OrderModel.create(
            user_id=user_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            shipping_address=shipping_address,
            payment_method=payment_method,
            cart_items=cart_data['items'],
            delivery_type=delivery_type,
            delivery_time_slot=delivery_time_slot,
            discount=cart_data['discount'],
            note=note
        )

        # Xóa giỏ hàng sau khi đặt thành công
        session.pop('cart', None)
        session.pop('coupon_code', None)
        session.pop('discount_amount', None)

        flash("Đặt hàng thành công! FreshMart đang tiếp nhận và phân công đóng gói.", "success")
        return redirect(url_for('order_success', order_code=order_code))

    return render_template('checkout.html', cart=cart_data, user=user)

@app.route('/order-success/<order_code>')
def order_success(order_code):
    """Trang xác nhận đặt hàng thành công, hiển thị VietQR và hóa đơn chi tiết"""
    order = OrderModel.get_by_code(order_code)
    if not order:
        flash("Không tìm thấy đơn hàng!", "danger")
        return redirect(url_for('index'))

    items = OrderModel.get_items(order['id'])
    return render_template('order_success.html', order=order, items=items)

# ==========================================
# AUTHENTICATION & PROFILE
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')

        user = UserModel.get_by_username_or_email(identifier)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['fullname'] = user['fullname']
            session['user_role'] = user['role']

            flash(f"Chào mừng {user['fullname']} đã trở lại!", "success")
            
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash("Tên đăng nhập / Email hoặc mật khẩu không chính xác!", "danger")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        fullname = request.form.get('fullname', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        if not username or not email or not password or not fullname:
            flash("Vui lòng điền các trường bắt buộc!", "warning")
            return render_template('register.html')

        if password != confirm_password:
            flash("Mật khẩu xác nhận không khớp!", "danger")
            return render_template('register.html')

        if UserModel.get_by_username_or_email(username):
            flash("Tên đăng nhập đã được sử dụng!", "danger")
            return render_template('register.html')
        if UserModel.get_by_username_or_email(email):
            flash("Email đã được sử dụng!", "danger")
            return render_template('register.html')

        try:
            UserModel.create(username, email, password, fullname, phone, address, role='customer')
            flash("Đăng ký tài khoản thành công! Vui lòng đăng nhập.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Lỗi khi đăng ký: {str(e)}", "danger")

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Bạn đã đăng xuất thành công!", "info")
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Thông tin cá nhân & Lịch sử đơn hàng"""
    user_id = session['user_id']
    user = UserModel.get_by_id(user_id)

    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        
        UserModel.update_profile(user_id, fullname, phone, address)
        session['fullname'] = fullname
        flash("Cập nhật thông tin tài khoản thành công!", "success")
        return redirect(url_for('profile'))

    orders = OrderModel.get_user_orders(user_id)
    return render_template('profile.html', user=user, orders=orders)

@app.route('/order/<order_code>')
def view_order(order_code):
    """Khách hàng tra cứu chi tiết hóa đơn đơn hàng"""
    order = OrderModel.get_by_code(order_code)
    if not order:
        flash("Không tìm thấy thông tin đơn hàng!", "warning")
        return redirect(url_for('index'))
    items = OrderModel.get_items(order['id'])
    return render_template('order_detail.html', order=order, items=items)

# ==========================================
# ADMIN ROUTES (PHÂN HỆ QUẢN TRỊ)
# ==========================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Bảng điều khiển quản trị thống kê doanh thu, tồn kho và đơn hàng"""
    stats = OrderModel.get_stats()
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/products')
@admin_required
def admin_products():
    """Danh sách sản phẩm trong kho kèm số lượng và HSD"""
    products = ProductModel.get_all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_product_add():
    """Thêm mới sản phẩm có quản lý số lượng tồn kho & hạn sử dụng"""
    categories = CategoryModel.get_all()
    if request.method == 'POST':
        category_id = int(request.form.get('category_id'))
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip() or name.lower().replace(' ', '-')
        description = request.form.get('description', '').strip()
        price = float(request.form.get('price', 0))
        original_price = float(request.form.get('original_price', 0)) if request.form.get('original_price') else None
        unit = request.form.get('unit', 'Kg').strip()
        stock = int(request.form.get('stock', 0))
        manufacturing_date = request.form.get('manufacturing_date', '').strip()
        expiry_date = request.form.get('expiry_date', '').strip()
        shelf_life = request.form.get('shelf_life', '').strip()
        image_url = request.form.get('image_url', '').strip()
        is_featured = 1 if request.form.get('is_featured') else 0
        is_new = 1 if request.form.get('is_new') else 0

        ProductModel.create(category_id, name, slug, description, price, original_price, unit, stock,
                            manufacturing_date, expiry_date, shelf_life, image_url, is_featured, is_new)
        flash(f"Thêm sản phẩm '{name}' thành công!", "success")
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', categories=categories, product=None)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_product_edit(product_id):
    """Chỉnh sửa thông tin, số lượng và hạn sử dụng sản phẩm"""
    product = ProductModel.get_by_id(product_id)
    if not product:
        flash("Sản phẩm không tồn tại!", "danger")
        return redirect(url_for('admin_products'))

    categories = CategoryModel.get_all()
    if request.method == 'POST':
        category_id = int(request.form.get('category_id'))
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip() or product['slug']
        description = request.form.get('description', '').strip()
        price = float(request.form.get('price', 0))
        original_price = float(request.form.get('original_price', 0)) if request.form.get('original_price') else None
        unit = request.form.get('unit', 'Kg').strip()
        stock = int(request.form.get('stock', 0))
        manufacturing_date = request.form.get('manufacturing_date', '').strip()
        expiry_date = request.form.get('expiry_date', '').strip()
        shelf_life = request.form.get('shelf_life', '').strip()
        image_url = request.form.get('image_url', '').strip() or product['image_url']
        is_featured = 1 if request.form.get('is_featured') else 0
        is_new = 1 if request.form.get('is_new') else 0

        ProductModel.update(product_id, category_id, name, slug, description, price, original_price, unit, stock,
                            manufacturing_date, expiry_date, shelf_life, image_url, is_featured, is_new)
        flash(f"Cập nhật sản phẩm '{name}' thành công!", "success")
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', categories=categories, product=product)

@app.route('/admin/products/delete/<int:product_id>')
@admin_required
def admin_product_delete(product_id):
    """Xóa sản phẩm"""
    ProductModel.delete(product_id)
    flash("Đã xóa sản phẩm thành công!", "info")
    return redirect(url_for('admin_products'))

@app.route('/admin/categories', methods=['GET', 'POST'])
@admin_required
def admin_categories():
    """Quản lý danh mục sản phẩm"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip() or name.lower().replace(' ', '-')
        icon = request.form.get('icon', 'fa-solid fa-basket-shopping').strip()
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()

        CategoryModel.create(name, slug, icon, description, image_url)
        flash(f"Thêm danh mục '{name}' thành công!", "success")
        return redirect(url_for('admin_categories'))

    categories = CategoryModel.get_with_product_count()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/delete/<int:category_id>')
@admin_required
def admin_category_delete(category_id):
    """Xóa danh mục"""
    CategoryModel.delete(category_id)
    flash("Đã xóa danh mục thành công!", "info")
    return redirect(url_for('admin_categories'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    """Quản lý đơn hàng, thông tin giao hàng và shipper"""
    orders = OrderModel.get_all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def admin_order_update_status(order_id):
    """Cập nhật trạng thái đơn, thanh toán, giao hàng và shipper"""
    order_status = request.form.get('order_status')
    payment_status = request.form.get('payment_status')
    delivery_status = request.form.get('delivery_status')
    shipper_name = request.form.get('shipper_name', '').strip()
    
    OrderModel.update_status(order_id, order_status, payment_status, delivery_status, shipper_name)
    flash("Cập nhật trạng thái đơn hàng & giao nhận thành công!", "success")
    return redirect(url_for('admin_orders'))

@app.route('/admin/users')
@admin_required
def admin_users():
    """Quản lý danh sách người dùng"""
    users = UserModel.get_all()
    return render_template('admin/users.html', users=users)

if __name__ == '__main__':
    print("=====================================================")
    print(" FreshMart - Siêu thị trực tuyến đang khởi chạy...")
    print(" Quản lý Số lượng, Hạn sử dụng, Giao hàng & Hóa đơn")
    print(" Truy cập tại: http://127.0.0.1:5000")
    print("=====================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)
