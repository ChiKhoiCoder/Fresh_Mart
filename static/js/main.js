// FreshMart Front-end Interactions, Quantity Management & Dynamic Invoice

document.addEventListener('DOMContentLoaded', function () {
    // 1. Bắt sự kiện form thêm vào giỏ hàng bằng AJAX
    const addToCartForms = document.querySelectorAll('.ajax-add-to-cart');
    
    addToCartForms.forEach(form => {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const actionUrl = this.getAttribute('action');
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalContent = submitBtn ? submitBtn.innerHTML : '';

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            }

            fetch(actionUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalContent;
                }

                if (data.success) {
                    // Cập nhật số lượng trên icon giỏ hàng ở Navbar
                    const cartBadges = document.querySelectorAll('.cart-badge');
                    cartBadges.forEach(badge => {
                        badge.textContent = data.cart_count;
                        badge.classList.remove('hidden');
                        badge.classList.add('animate-bounce');
                        setTimeout(() => badge.classList.remove('animate-bounce'), 1000);
                    });

                    // Hiển thị thông báo Toast
                    if (window.Swal) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Đã thêm vào giỏ!',
                            text: data.message,
                            toast: true,
                            position: 'top-end',
                            showConfirmButton: false,
                            timer: 2000,
                            timerProgressBar: true
                        });
                    } else {
                        alert(data.message);
                    }
                } else {
                    if (window.Swal) {
                        Swal.fire({
                            icon: 'warning',
                            title: 'Thông báo kho hàng',
                            text: data.message,
                            toast: true,
                            position: 'top-end',
                            showConfirmButton: false,
                            timer: 3500
                        });
                    } else {
                        alert(data.message);
                    }
                }
            })
            .catch(err => {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalContent;
                }
                console.error("Lỗi khi thêm giỏ hàng:", err);
            });
        });
    });

    // 2. Bộ tăng giảm số lượng sản phẩm trên trang chi tiết (Product Detail Quantity Picker)
    const detailQtyInputs = document.querySelectorAll('.detail-qty-input');
    detailQtyInputs.forEach(input => {
        const btnMinus = input.parentElement.querySelector('.btn-qty-minus');
        const btnPlus = input.parentElement.querySelector('.btn-qty-plus');
        const maxStock = parseInt(input.getAttribute('max')) || 999;

        if (btnMinus) {
            btnMinus.addEventListener('click', () => {
                let val = parseInt(input.value) || 1;
                if (val > 1) {
                    input.value = val - 1;
                }
            });
        }

        if (btnPlus) {
            btnPlus.addEventListener('click', () => {
                let val = parseInt(input.value) || 1;
                if (val < maxStock) {
                    input.value = val + 1;
                } else {
                    if (window.Swal) {
                        Swal.fire({
                            icon: 'info',
                            title: 'Tồn kho giới hạn',
                            text: `Sản phẩm hiện chỉ còn ${maxStock} sản phẩm trong kho!`,
                            toast: true,
                            position: 'top-end',
                            showConfirmButton: false,
                            timer: 2500
                        });
                    }
                }
            });
        }
    });

    // 3. Tương tác thay đổi hình thức giao hàng trong giỏ hàng (Giao Tiêu Chuẩn / Giao 2H)
    const deliveryRadios = document.querySelectorAll('input[name="cart_delivery_type"]');
    deliveryRadios.forEach(radio => {
        radio.addEventListener('change', function () {
            const deliveryType = this.value;
            const formData = new FormData();
            formData.append('delivery_type', deliveryType);

            fetch('/cart/set-delivery', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // Cập nhật phí vận chuyển và tổng hóa đơn trên màn hình
                    const feeEl = document.getElementById('summary-shipping-fee');
                    const totalEl = document.getElementById('summary-grand-total');

                    if (feeEl) {
                        if (data.shipping_fee === 0) {
                            feeEl.innerHTML = '<span class="text-emerald-600 font-bold">Miễn phí (0 đ)</span>';
                        } else {
                            feeEl.innerHTML = `<span class="font-bold text-slate-800">${formatCurrency(data.shipping_fee)}</span>`;
                        }
                    }

                    if (totalEl) {
                        totalEl.textContent = formatCurrency(data.total);
                    }
                }
            });
        });
    });
});

// Hàm hỗ trợ format tiền tệ VNĐ
function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount).replace('₫', 'đ');
}

// Hàm hỗ trợ tự điền tài khoản mẫu ở màn hình Đăng nhập (dễ chấm điểm đồ án)
function fillDemoAccount(username, password) {
    const userInput = document.querySelector('input[name="identifier"]');
    const passInput = document.querySelector('input[name="password"]');
    if (userInput && passInput) {
        userInput.value = username;
        passInput.value = password;
        if (window.Swal) {
            Swal.fire({
                icon: 'info',
                title: 'Đã điền tài khoản mẫu',
                text: `Tài khoản: ${username}`,
                timer: 1500,
                showConfirmButton: false
            });
        }
    }
}
