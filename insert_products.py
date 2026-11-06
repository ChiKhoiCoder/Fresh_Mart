"""
Script chèn 20 sản phẩm mới vào các danh mục:
- Danh mục 3: Thịt & Hải Sản Tươi (SP 11-15)
- Danh mục 4: Sữa, Trứng & Bơ (SP 16-20)
- Danh mục 5: Đồ Khô & Gia Vị (SP 21-25)
- Danh mục 6: Nước Ép & Đồ Uống (SP 26-30, không tính SP thay thế)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import get_db_connection

products_data = [
    # ── Danh mục 3: Thịt & Hải Sản Tươi (category_id = 3) ──────────────────
    # (category_id, name, slug, description, price, original_price, unit, stock,
    #  manufacturing_date, expiry_date, shelf_life, image_url, is_featured, is_new)
    (3, 'Thịt ba chỉ heo', 'thit-ba-chi-heo',
     'Thịt ba chỉ tươi, tỷ lệ nạc mỡ hài hòa, phù hợp kho và nướng.',
     165000, 185000, 'Kg', 30,
     '05/11/2026', '08/11/2026', '2–3 ngày (0–4°C)',
     'https://placehold.co/600x600?text=Thit+Ba+Chi',
     1, 1),

    (3, 'Ức gà tươi', 'uc-ga-tuoi',
     'Ức gà tươi, ít mỡ, phù hợp chế độ ăn lành mạnh.',
     95000, 110000, 'Kg', 40,
     '05/11/2026', '08/11/2026', '2–3 ngày (0–4°C)',
     'https://placehold.co/600x600?text=Uc+Ga',
     1, 1),

    (3, 'Cá hồi phi lê tươi', 'ca-hoi-phi-le-tuoi',
     'Cá hồi phi lê tươi, thịt mềm, thích hợp áp chảo và chế biến món ăn.',
     350000, 390000, 'Kg', 20,
     '05/11/2026', '07/11/2026', '1–2 ngày (0–2°C)',
     'https://placehold.co/600x600?text=Ca+Hoi',
     1, 1),

    (3, 'Mực ống tươi', 'muc-ong-tuoi',
     'Mực ống tươi, thân chắc, phù hợp hấp, xào và nướng.',
     190000, 220000, 'Kg', 25,
     '05/11/2026', '07/11/2026', '1–2 ngày (0–2°C)',
     'https://placehold.co/600x600?text=Muc+Ong',
     0, 1),

    (3, 'Cá rô phi tươi', 'ca-ro-phi-tuoi',
     'Cá rô phi tươi, thịt trắng, phù hợp chiên, hấp và nấu canh.',
     65000, 75000, 'Kg', 35,
     '05/11/2026', '07/11/2026', '1–2 ngày (0–2°C)',
     'https://placehold.co/600x600?text=Ca+Ro+Phi',
     0, 1),

    # ── Danh mục 4: Sữa, Trứng & Bơ (category_id = 4) ──────────────────────
    (4, 'Sữa chua không đường', 'sua-chua-khong-duong',
     'Sữa chua không đường, vị thanh nhẹ, phù hợp sử dụng hằng ngày.',
     28000, 32000, 'Lốc 4 hộp', 80,
     '02/11/2026', '02/12/2026', 'Theo HSD (2–6°C)',
     'https://placehold.co/600x600?text=Sua+Chua',
     1, 1),

    (4, 'Bơ lạt cao cấp', 'bo-lat-cao-cap',
     'Bơ lạt thơm béo, thích hợp làm bánh và chế biến món ăn.',
     65000, 75000, 'Hộp 200g', 35,
     '01/11/2026', '01/02/2027', 'Theo HSD (2–6°C)',
     'https://placehold.co/600x600?text=Bo+Lat',
     1, 0),

    (4, 'Phô mai lát', 'pho-mai-lat',
     'Phô mai lát có vị béo thơm, phù hợp làm sandwich và hamburger.',
     55000, 62000, 'Gói 200g', 45,
     '01/11/2026', '01/02/2027', 'Theo HSD (2–6°C)',
     'https://placehold.co/600x600?text=Pho+Mai',
     0, 1),

    (4, 'Trứng vịt tươi', 'trung-vit-tuoi',
     'Trứng vịt tươi được chọn lọc, thích hợp luộc và chế biến món ăn.',
     38000, 43000, 'Hộp 10 quả', 50,
     '04/11/2026', '25/11/2026', 'Theo NSX (4–8°C)',
     'https://placehold.co/600x600?text=Trung+Vit',
     0, 1),

    (4, 'Sữa tươi nguyên kem', 'sua-tuoi-nguyen-kem',
     'Sữa tươi nguyên kem có hương vị béo ngậy, cung cấp canxi và protein.',
     42000, 48000, 'Hộp 1 lít', 75,
     '01/11/2026', '01/12/2026', 'Theo HSD (2–6°C)',
     'https://placehold.co/600x600?text=Sua+Nguyen+Kem',
     1, 1),

    # ── Danh mục 5: Đồ Khô & Gia Vị (category_id = 5) ──────────────────────
    (5, 'Nấm hương khô', 'nam-huong-kho',
     'Nấm hương khô thơm tự nhiên, phù hợp nấu canh và chế biến món ăn.',
     85000, 95000, 'Túi 200g', 40,
     '01/10/2026', '01/10/2027', '12 tháng (dưới 30°C)',
     'https://placehold.co/600x600?text=Nam+Huong',
     1, 1),

    (5, 'Ớt khô nguyên quả', 'ot-kho-nguyen-qua',
     'Ớt khô có vị cay đặc trưng, dùng làm gia vị cho nhiều món ăn.',
     35000, 40000, 'Túi 100g', 55,
     '01/10/2026', '01/10/2027', '12 tháng (kín khí)',
     'https://placehold.co/600x600?text=Ot+Kho',
     0, 1),

    (5, 'Miến dong khô', 'mien-dong-kho',
     'Miến dong dai ngon, thích hợp nấu miến gà, miến xào và lẩu.',
     55000, 65000, 'Túi 500g', 60,
     '01/10/2026', '01/10/2027', '12 tháng (thoáng mát)',
     'https://placehold.co/600x600?text=Mien+Dong',
     1, 0),

    (5, 'Hạt điều rang', 'hat-dieu-rang',
     'Hạt điều rang giòn, bùi béo, phù hợp ăn nhẹ và làm quà tặng.',
     145000, 165000, 'Hộp 500g', 35,
     '01/11/2026', '01/05/2027', '6 tháng (kín khí)',
     'https://placehold.co/600x600?text=Hat+Dieu',
     1, 1),

    (5, 'Quế thanh tự nhiên', 'que-thanh-tu-nhien',
     'Quế thanh có mùi thơm đặc trưng, dùng làm gia vị và pha chế.',
     65000, 75000, 'Túi 200g', 45,
     '01/10/2026', '01/10/2027', '12 tháng (kín khí)',
     'https://placehold.co/600x600?text=Que+Thanh',
     0, 1),

    # ── Danh mục 6: Nước Ép & Đồ Uống (category_id = 6) ────────────────────
    (6, 'Nước ép dưa hấu', 'nuoc-ep-dua-hau',
     'Nước ép dưa hấu tươi mát, vị ngọt dịu, thích hợp giải khát.',
     22000, 27000, 'Chai 500ml', 50,
     '05/11/2026', '07/11/2026', '2 ngày (2–5°C)',
     'https://placehold.co/600x600?text=Nuoc+Ep+Dua+Hau',
     1, 1),

    (6, 'Nước ép táo', 'nuoc-ep-tao',
     'Nước ép táo có vị ngọt thanh, thơm tự nhiên, dùng ngon nhất khi uống lạnh.',
     30000, 35000, 'Chai 500ml', 45,
     '05/11/2026', '07/11/2026', '2 ngày (2–5°C)',
     'https://placehold.co/600x600?text=Nuoc+Ep+Tao',
     1, 1),

    (6, 'Nước ép chanh dây', 'nuoc-ep-chanh-day',
     'Nước ép chanh dây thơm đặc trưng, vị chua ngọt hài hòa.',
     28000, 33000, 'Chai 500ml', 40,
     '05/11/2026', '07/11/2026', '2 ngày (2–5°C)',
     'https://placehold.co/600x600?text=Nuoc+Ep+Chanh+Day',
     0, 1),

    (6, 'Nước dừa đóng chai', 'nuoc-dua-dong-chai',
     'Nước dừa có vị thanh mát, thích hợp giải khát hằng ngày.',
     20000, 25000, 'Chai 500ml', 65,
     '05/11/2026', '07/11/2026', '2 ngày (2–5°C)',
     'https://placehold.co/600x600?text=Nuoc+Dua',
     1, 1),

    (6, 'Nước mía tươi', 'nuoc-mia-tuoi',
     'Nước mía ép tươi, vị ngọt tự nhiên, thích hợp dùng ngay sau khi mở nắp.',
     15000, 18000, 'Chai 500ml', 70,
     '05/11/2026', '06/11/2026', '1 ngày (2–5°C)',
     'https://placehold.co/600x600?text=Nuoc+Mia',
     0, 1),
]

def insert_products():
    conn = get_db_connection()
    cursor = conn.cursor()

    inserted = 0
    skipped = 0
    for p in products_data:
        slug = p[2]
        exists = cursor.execute("SELECT id FROM products WHERE slug = ?", (slug,)).fetchone()
        if exists:
            print(f"  [~] Bỏ qua (đã tồn tại): {p[1]} (slug={slug})")
            skipped += 1
            continue
        cursor.execute('''
        INSERT INTO products (
            category_id, name, slug, description, price, original_price, unit, stock,
            manufacturing_date, expiry_date, shelf_life, image_url, is_featured, is_new
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', p)
        print(f"  [+] Đã thêm: {p[1]}")
        inserted += 1

    conn.commit()
    conn.close()
    print(f"\n✅ Hoàn tất! Đã thêm {inserted} sản phẩm, bỏ qua {skipped} sản phẩm đã tồn tại.")

if __name__ == '__main__':
    insert_products()

