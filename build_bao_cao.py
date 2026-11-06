# -*- coding: utf-8 -*-
"""Báo cáo Mini project FreshMart — 3 chương, chuẩn TNR 13 / dòng 1.3 / lề 2.5-2.5-3-2.

Chạy:  "<đường dẫn python>" "D:/Học Tập 1/Project Kì 1/FreshMart/build_bao_cao.py"
Mở Word: Ctrl+A rồi F9 để cập nhật Mục lục và Danh mục hình.
"""
from __future__ import annotations

import os, re, sys
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = "Bao_Cao_Mini_Project_FreshMart.docx"
DARK = RGBColor(0x15, 0x50, 0x2D)


def new_doc() -> Document:
    doc = Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)          # A4
    sec.top_margin, sec.bottom_margin = Cm(2.5), Cm(2.5)
    sec.left_margin, sec.right_margin = Cm(3.0), Cm(2.0)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(13)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    pf = normal.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.line_spacing = 1.3          # Multiple 1.3 lines
    pf.space_before = Pt(6)
    pf.space_after = Pt(6)

    for name, size in {"Heading 1": Pt(14), "Heading 2": Pt(13.5), "Heading 3": Pt(13)}.items():
        st = doc.styles[name]
        st.font.name = "Times New Roman"
        st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        st.font.size, st.font.bold = size, True
        st.font.color.rgb = DARK
        st.paragraph_format.space_before = Pt(12 if name == "Heading 1" else 6)
        st.paragraph_format.space_after = Pt(6)
        st.paragraph_format.line_spacing = 1.3
        st.paragraph_format.keep_with_next = True

    cap = doc.styles["Caption"]
    cap.font.name = "Times New Roman"
    cap.font.size, cap.font.bold, cap.font.italic = Pt(12), True, False
    cap.font.color.rgb = RGBColor(0, 0, 0)
    cap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(2)
    cap.paragraph_format.space_after = Pt(5)
    cap.paragraph_format.line_spacing = 1.3

    for lname in ("List Bullet", "List Bullet 2"):
        lst = doc.styles[lname]
        lst.font.name = "Times New Roman"
        lst.font.size = Pt(13)
        lst.paragraph_format.line_spacing = 1.3
        lst.paragraph_format.space_before = Pt(0)
        lst.paragraph_format.space_after = Pt(3)
    return doc


def add_field(par, instr: str, display: str) -> None:
    run = par.add_run()
    b = OxmlElement("w:fldChar"); b.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = instr
    s = OxmlElement("w:fldChar"); s.set(qn("w:fldCharType"), "separate")
    t = OxmlElement("w:t"); t.text = display
    e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), "end")
    for x in (b, it, s, t, e):
        run._r.append(x)


TOKEN_RX = re.compile(r"\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`")

# Cho phép Word xuống dòng ngay sau các ký tự nối, tránh kéo giãn khoảng trắng
# khi câu có định dạng justify chứa token dài (đường dẫn, URL, lệnh).
ZW = chr(0x200B)
ZW_CODE_RX = re.compile(r"([/?=&:])(?=\S)")
ZW_TEXT_RX = re.compile(r"(/)(?=\S)")


def _wrapable(text: str, rx=ZW_TEXT_RX) -> str:
    return rx.sub(r"\1" + ZW, text)


def rich(par, text: str) -> None:
    pos = 0
    for m in TOKEN_RX.finditer(text):
        if m.start() > pos:
            par.add_run(_wrapable(text[pos:m.start()]))
        if m.group(1) is not None:
            r = par.add_run(_wrapable(m.group(1), ZW_CODE_RX)); r.bold = True
        elif m.group(2) is not None:
            r = par.add_run(m.group(2)); r.italic = True
        else:
            r = par.add_run(_wrapable(m.group(3), ZW_CODE_RX))
            r.font.name = "Consolas"; r.font.size = Pt(11.5)
        pos = m.end()
    if pos < len(text):
        par.add_run(_wrapable(text[pos:]))


def body(doc, text):
    par = doc.add_paragraph()
    rich(par, text)
    return par


def bullet(doc, text, level=0):
    par = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    rich(par, text)
    return par


def heading(doc, level, text, center=False, page_break=False):
    if page_break:
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    par = doc.add_heading(level=level)
    par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.JUSTIFY
    par.add_run(text)
    return par


def set_cell_bg(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def make_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2); p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(h); r.bold = True; r.font.size = Pt(11); r.font.name = "Times New Roman"
        set_cell_bg(cell, "D9EAD3")
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(2); p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            rich(p, str(val))
            for r in p.runs:
                r.font.size = Pt(11)
    if widths:
        for i, w in enumerate(widths):
            for row in table.rows:
                row.cells[i].width = Cm(w)
    return table


def set_borders(table, color="A6A6A6", sz="8"):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single"); el.set(qn("w:sz"), sz)
        el.set(qn("w:space"), "0"); el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)


def fig(doc, description, caption):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_borders(table)
    cell = table.rows[0].cells[0]
    cell.width = Cm(16.0)
    trPr = table.rows[0]._tr.get_or_add_trPr()
    trH = OxmlElement("w:trHeight")
    trH.set(qn("w:val"), "240"); trH.set(qn("w:hRule"), "atLeast")
    trPr.append(trH)
    p1 = cell.paragraphs[0]
    p1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.space_before = Pt(2)
    r0 = p1.add_run("[ DÁN ẢNH VÀO KHUNG NÀY ] ")
    r0.bold = True; r0.font.size = Pt(10.5); r0.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    r2 = p1.add_run(description)
    r2.italic = True; r2.font.size = Pt(10.5); r2.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
    par = doc.add_paragraph(style="Caption")
    par.add_run("Hình ")
    add_field(par, 'SEQ Hình \\* ARABIC', "1")
    par.add_run(f": {caption}")


def note(doc, text, prefix="Ghi chú: "):
    par = doc.add_paragraph()
    r = par.add_run(prefix); r.bold = True
    rich(par, text)
    for run in par.runs:
        run.italic = True
    return par


def add_footer_page_number(doc):
    par = doc.sections[0].footer.paragraphs[0]
    par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_field(par, "PAGE", "1")
    for r in par.runs:
        r.font.name = "Times New Roman"; r.font.size = Pt(12)


doc = new_doc()


def center(text, size, bold=False, before=0, after=0, italic=False, color=None):
    par = doc.add_paragraph()
    par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_before = Pt(before)
    par.paragraph_format.space_after = Pt(after)
    r = par.add_run(text)
    r.bold, r.italic, r.font.size = bold, italic, Pt(size)
    if color:
        r.font.color.rgb = RGBColor(*color)
    return par


# ============================================================== TRANG BÌA ====
center("TRƯỜNG ĐẠI HỌC ………………………………………", 13, True, after=2)
center("KHOA ……………………………………………………", 13, True)
center("[LOGO TRƯỜNG]", 10.5, before=24, after=24, color=(0x80, 0x80, 0x80))
center("BÁO CÁO MINI PROJECT", 18, True, after=6)
center("SIÊU THỊ THỰC PHẨM TRỰC TUYẾN FRESHMART\nXÂY DỰNG BẰNG FLASK, SQLITE VÀ TRIỂN KHAI TRÊN MICROSOFT AZURE",
       14.5, True, color=DARK, after=6)
center("Dịch vụ Cloud: Microsoft Azure – App Service (Web App Linux)\n"
       "Mã nguồn: ứng dụng Flask + SQLite, 29 tuyến URL, 18 mẫu giao diện", 12.5, italic=True, after=24)
center("Giảng viên hướng dẫn: …………………………………", 13, before=12)
center("Nhóm thực hiện:", 13, True, before=10, after=4)
for i in range(1, 5):
    center(f"Thành viên {i}: …………………………… — MSSV: …………………", 12.5, after=1)
center("Học kỳ 1 – Năm học 2026 – 2027\nTháng 11 / 2026", 13, before=30)

# ================================================================ MỤC LỤC ====
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
center("MỤC LỤC", 14, True, after=12, color=DARK)
par = doc.add_paragraph()
add_field(par, r'TOC \o "1-2" \h \z \u',
          "(Mục lục tự động: mở Word, nhấn Ctrl+A rồi F9 để cập nhật số trang.)")

par = doc.add_paragraph()
par.paragraph_format.space_before = Pt(12)
r = par.add_run("DANH MỤC HÌNH ẢNH"); r.bold = True; r.font.size = Pt(13)
par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
par = doc.add_paragraph()
add_field(par, r'TOC \h \z \c "Hình"',
          "(Danh mục hình tự động: nhấn Ctrl+A rồi F9 sau khi dán xong ảnh vào 15 khung.)")

add_footer_page_number(doc)

# ============================================================ LỜI MỞ ĐẦU =====
heading(doc, 1, "LỜI MỞ ĐẦU", center=True)
body(doc, "**Lý do chọn đề tài.** Mua thực phẩm tươi trực tuyến khác hẳn mua hàng công nghiệp: người bán phải "
          "chứng minh hàng còn tươi, truy xuất được ngày sản xuất – hạn sử dụng và giao trong vài giờ chứ không "
          "phải vài ngày. Nhiều cửa hàng vẫn chốt đơn bằng tin nhắn thủ công nên mắc ba lỗi quen thuộc: bán quá "
          "tồn kho, giao hàng gần hết hạn và tính tiền sai. Xây dựng hệ thống làm sẵn ba việc đó — kiểm kho tức "
          "thời, hiển thị hạn sử dụng, tính hóa đơn minh bạch — rồi đưa lên một dịch vụ cloud để khách truy cập "
          "từ bất kỳ máy nào là hướng đi phù hợp với một đồ án học phần.")
body(doc, "**Mục đích nghiên cứu.** Nhóm xây dựng FreshMart, siêu thị thực phẩm trực tuyến cho khách hàng và "
          "quản trị viên, chạy trên nền Python – Flask – SQLite theo mô hình MVC giản lược (29 tuyến URL, 18 mẫu "
          "giao diện, 6 bảng dữ liệu), bảo đảm trọn vòng đời một đơn hàng từ tìm và lọc sản phẩm, thêm vào giỏ, "
          "chọn kiểu giao, áp voucher đến chốt đơn, tra mã đơn và in hóa đơn. Trên cơ sở đó, nhóm trình bày quy "
          "trình đưa ứng dụng lên dịch vụ cloud và đánh giá các giới hạn phải xử lý khi rời khỏi máy cá nhân.")
body(doc, "**Đối tượng và phạm vi nghiên cứu.** Đối tượng là quy trình nghiệp vụ bán lẻ thực phẩm và kiến trúc "
          "kỹ thuật của mã nguồn FreshMart: điều phối trong `app.py` (796 dòng), lớp truy cập dữ liệu `models.py` "
          "(434 dòng, năm lớp mô hình), khởi tạo và di cư lược đồ trong `database.py` (352 dòng), tham số trong "
          "`config.py` (27 dòng). Phạm vi là bản dùng thử với dữ liệu mẫu, thanh toán theo hình thức thu hộ hoặc "
          "chuyển khoản kèm mã VietQR; báo cáo không triển khai cổng thanh toán thật, không tích hợp hệ thống vận "
          "chuyển bên ngoài và không cam kết vận hành dưới tải lớn.")
body(doc, "**Ý nghĩa khoa học và thực tiễn.** Về học thuật, đồ án thể hiện cách tổ chức ứng dụng web động theo "
          "ba lớp, cách dùng phiên làm việc giữ giỏ hàng, cách ràng buộc nghiệp vụ ngay trong tầng mô hình (ép số "
          "lượng theo tồn kho, tái kiểm tra trước khi ghi đơn, trừ kho trong cùng giao dịch) và cách chuyển một dự "
          "án chạy cục bộ sang dịch vụ cloud. Về thực tiễn, sản phẩm đủ cho một cửa hàng nhỏ giai đoạn thử nghiệm: "
          "chủ cửa hàng thấy doanh thu, số đơn chờ và danh sách sắp hết hàng trên một màn hình; khách thấy rõ "
          "thành tiền, phí vận chuyển và tổng phải trả trước khi xác nhận.")
body(doc, "**Cấu trúc báo cáo.** Ngoài Lời mở đầu, Tài liệu tham khảo, Phụ lục và Phần B hướng dẫn demo, báo cáo "
          "gồm ba chương theo khung đề cương: Chương 1 phát biểu bài toán và biện hộ cho lựa chọn dịch vụ cloud; "
          "Chương 2 trình bày phân công, kế hoạch và các bước triển khai; Chương 3 tổng hợp kết quả, hướng dẫn sử "
          "dụng cùng kết luận và hướng phát triển.")

# =========================================================== CHƯƠNG 1 =======
heading(doc, 1, "CHƯƠNG 1. TỔNG QUAN ĐỀ TÀI", center=True, page_break=True)

heading(doc, 2, "1. MÔ TẢ BÀI TOÁN VÀ VẤN ĐỀ CẦN GIẢI QUYẾT")
heading(doc, 3, "1.1. Bối cảnh và phát biểu bài toán")
body(doc, "Nhu cầu mua rau, củ, quả và thực phẩm tươi bằng điện thoại đã thành thói quen, nhưng trải "
          "nghiệm mua hàng phụ thuộc vào ba câu hỏi mà người bán ít khi trả lời được trên tin nhắn: hàng "
          "còn hay hết, hạn sử dụng đến ngày nào, và tổng tiền cuối cùng là bao gồm những khoản gì. Bài "
          "toán của FreshMart là xây dựng một website tự động trả lời ba câu hỏi đó, đồng thời cho phép "
          "người bán quản lý danh mục, giá, tồn kho và tiến độ giao hàng, rồi đưa lên Microsoft Azure App "
          "Service để khách truy cập bằng một đường link công khai thay vì chỉ chạy trên máy của nhóm.")
body(doc, "**Đầu vào** của hệ thống là: tài khoản và vai trò người dùng; danh mục và sản phẩm (giá bán, giá "
          "gạch, đơn vị tính, số tồn, hình ảnh, cờ nổi bật và hàng mới, ngày sản xuất, hạn sử dụng, cách bảo "
          "quản); điều kiện xem hàng của khách (từ khóa, danh mục, khoảng giá, kiểu sắp xếp, số trang); giỏ "
          "hàng lưu trong phiên làm việc; phiếu đặt hàng (họ tên, điện thoại, email, địa chỉ, kiểu giao, khung "
          "giờ, phương thức thanh toán, ghi chú); mã giảm giá do khách nhập; và lệnh cập nhật trạng thái của "
          "quản trị viên.")
body(doc, "**Đầu ra** gồm: trang chủ với sản phẩm nổi bật và hàng mới về; danh mục phân trang 12 sản phẩm mỗi "
          "trang; trang chi tiết kèm sản phẩm liên quan; giỏ hàng hiển thị phí vận chuyển theo kiểu giao, thanh "
          "tiến độ miễn phí, số tiền giảm và tổng hóa đơn; trang xác nhận kèm mã đơn `FM-YYYYMMDD-XXXX`, mã "
          "VietQR và phiếu in; lịch sử mua hàng; bảng quản trị có thống kê doanh thu và cảnh báo sắp hết hàng.")
body(doc, "**Nội hàm** của bài toán là năm ràng buộc nghiệp vụ mà hệ thống phải tự thực hiện, không dựa "
          "vào thao tác tay của người dùng: (1) giới hạn số lượng theo tồn kho – mỗi lần thêm hoặc sửa "
          "mỗi lần thêm hoặc sửa số lượng, ứng dụng đối chiếu số tồn thực tế và ép về giá trị tối đa được phép kèm thông báo; "
          "(2) trừ kho ngay khi ghi đơn và chỉ trừ trong phạm vi an toàn, không cho tồn âm; (3) tái kiểm "
          "tra tồn kho của từng mặt hàng trước khi chốt đơn, vì giỏ hàng có thể đã nằm chờ từ phiên trước; "
          "(4) tính phí vận chuyển theo công thức tập trung: tiêu chuẩn 20.000 đồng và miễn phí từ đơn "
          "300.000 đồng, siêu tốc 2 giờ 35.000 đồng và giảm còn 15.000 đồng khi đạt ngưỡng, tổng thanh "
          "toán không bao giờ nhỏ hơn không; (5) kiểm tra điều kiện của mã giảm giá theo số tiền tối thiểu "
          "trước khi áp.")
body(doc, "**Phạm vi và giả định.** Dữ liệu là dữ liệu mẫu do `seed_data` nạp khi khởi tạo: 2 tài khoản "
          "demo, 6 danh mục, 19 sản phẩm, 3 mã giảm giá và 3 đơn hàng minh họa; trong quá trình kiểm thử, "
          "lược đồ hiện còn 9 sản phẩm và 5 đơn hàng (11 dòng chi tiết) vì có đơn đặt thật và có sản phẩm "
          "bị xóa từ trang quản trị. Giá và tồn kho chỉ có tính minh họa. **Giới hạn** cần nêu trung thực: "
          "hạn sử dụng được lưu dưới dạng chuỗi ngày (`dd/mm/yyyy`, có cả mô tả kiểu “7 ngày (bảo quản "
          "4-8°C)”) nên không thể so sánh ngày thực sự; mã giảm giá chỉ giảm tiền, chưa có giới hạn số lần "
          "dùng hay thời hạn; thanh toán chuyển khoản mới ở mức hiển thị mã VietQR, chưa có xác nhận tự "
          "động từ ngân hàng.")

heading(doc, 3, "1.2. Kiến trúc và mã nguồn của ứng dụng")
body(doc, "FreshMart là ứng dụng web nhiều trang theo mô hình MVC giản lược: trình duyệt gửi yêu cầu tới các "
          "tuyến URL do Flask điều phối, hàm xử lý đọc và ghi trạng thái qua lớp mô hình trong `models.py`, lớp "
          "này dùng kết nối SQLite do `database.py` cung cấp, kết quả hiển thị qua mẫu Jinja2 trong `templates/`. "
          "Giao diện dùng Tailwind CSS và Font Awesome nạp từ CDN, SweetAlert2 cho thông báo, cùng 184 dòng "
          "JavaScript tự viết trong `static/js/main.js` để thêm giỏ hàng và đổi kiểu giao bằng AJAX mà không tải "
          "lại trang. Cách tổ chức này cho phép đọc một luồng nghiệp vụ hoàn chỉnh mà không phải nhảy khắp nơi: "
          "hành vi giỏ hàng nằm ở `get_cart_details`, hành vi đặt hàng nằm ở `OrderModel.create`, còn mỗi tuyến "
          "quản trị đều được bảo vệ bằng decorator `admin_required` (kiểm tra cả `user_id` lẫn `user_role` trong phiên).")
make_table(doc,
           ["Thành phần", "Độ lớn", "Vai trò trong hệ thống"],
           [["`app.py`", "796 dòng", "29 tuyến URL, bộ lọc định dạng tiền, xử lý ngữ cảnh cung cấp biến dùng chung, hai decorator bảo vệ `login_required` và `admin_required`, hàm `get_cart_details` tính giỏ hàng và phí ship"],
            ["`models.py`", "434 dòng", "Năm lớp `UserModel`, `CategoryModel`, `ProductModel`, `OrderModel`, `CouponModel`, đóng gói toàn bộ truy vấn và ràng buộc nghiệp vụ"],
            ["`database.py`", "352 dòng", "Kết nối SQLite, `init_db` tạo bảng, `migrate_db` bổ sung cột an toàn, `ensure_product_expiry_dates` và `seed_data` nạp dữ liệu mẫu"],
            ["`config.py`", "27 dòng", "Khóa bí mật, đường dẫn CSDL và thư mục upload, 12 sản phẩm mỗi trang, phí ship 20.000 đồng, ngưỡng miễn phí 300.000 đồng, thông tin cửa hàng"],
            ["`templates/` và `static/`", "18 + 2 tệp", "11 mẫu phía khách (gồm `base.html`) và 7 mẫu quản trị (gồm `admin_base.html`); `css/style.css` 62 dòng và `js/main.js` 184 dòng xử lý tương tác"],
            ["`requirements.txt`", "2 dòng", "`Flask>=3.0.0`, `Werkzeug>=3.0.0` — chưa khai báo máy chủ ứng dụng, là điểm phải bổ sung trước khi lên cloud"]],
           widths=[3.2, 1.9, 10.9])
body(doc, "Cách tổ chức này cho phép đọc một luồng nghiệp vụ hoàn chỉnh mà không nhảy khắp nơi: hành vi "
          "giỏ hàng nằm ở `get_cart_details`, hành vi đặt hàng nằm ở `OrderModel.create`, và mỗi tuyến "
          "quản trị đều được bảo vệ bằng decorator `admin_required`, vốn kiểm tra cả `user_id` lẫn "
          "`user_role` trong phiên làm việc.")
fig(doc, "Ảnh chụp hoặc sơ đồ: Trình duyệt → tuyến URL Flask → lớp mô hình → SQLite → mẫu Jinja2 → HTML.",
    "Kiến trúc ba lớp và lược đồ cơ sở dữ liệu của FreshMart")

heading(doc, 3, "1.3. Dữ liệu và các quy tắc nghiệp vụ đã cài đặt")
make_table(doc,
           ["Bảng", "Số cột", "Nội dung lưu trữ"],
           [["`users`", "9", "Tên đăng nhập, email, mật khẩu băm, họ tên, điện thoại, địa chỉ, vai trò `admin` hoặc `customer`"],
            ["`categories`", "6", "Tên, slug, lớp icon Font Awesome, mô tả, ảnh danh mục"],
            ["`products`", "16", "Danh mục, tên, slug, mô tả, giá bán, giá gạch, đơn vị tính, tồn kho, ảnh, cờ nổi bật, cờ mới, ngày sản xuất, hạn sử dụng, cách bảo quản"],
            ["`orders`", "20", "Mã đơn, người mua, thông tin nhận hàng, phương thức thanh toán, ba trạng thái (đơn / thanh toán / giao), kiểu giao, khung giờ, shipper, tạm tính, phí ship, giảm, tổng, ghi chú"],
            ["`order_items`", "9", "Snapshot tên, ảnh, giá, số lượng, thành tiền và hạn sử dụng của từng mặt hàng tại thời điểm đặt"],
            ["`coupons`", "6", "Mã, tỷ lệ phần trăm, số tiền giảm cố định, đơn tối thiểu, cờ đang hoạt động"]],
           widths=[2.6, 1.4, 12.0])
body(doc, "Lược đồ được phát triển theo hướng an toàn: `migrate_db` dùng `ALTER TABLE` để bổ sung các cột "
          "`manufacturing_date`, `expiry_date`, `shelf_life` cho sản phẩm; `delivery_type`, "
          "`delivery_time_slot`, `shipper_name`, `delivery_status` cho đơn hàng; `expiry_date` cho chi tiết "
          "đơn, nhờ đó tệp CSDL cũ vẫn nâng cấp được mà không mất dữ liệu. `OrderModel.create` sinh mã đơn "
          "`FM-YYYYMMDD-` cộng 4 ký tự hexadecimal viết hoa, ghi đơn, ghi từng dòng `order_items` (kèm hạn "
          "sử dụng snapshot), rồi trừ kho bằng lệnh cập nhật có `MAX(0, stock - số lượng)` trước khi cam "
          "kết giao dịch. Trạng thái khởi tạo của một đơn mới là chưa duyệt, chưa thanh toán và đang đóng "
          "gói.")
body(doc, "Ba mã giảm giá mẫu được `CouponModel.validate` kiểm tra theo số tiền tối thiểu: "
          "`FRESHMART10` giảm 10 phần trăm cho đơn từ 100.000 đồng, `GIAM20K` giảm 20.000 đồng cho đơn từ "
          "150.000 đồng, `FREESHIP` được xử lý riêng trong công thức phí vận chuyển: nếu phiên đang mang "
          "mã này thì phí ship bằng không.")

heading(doc, 2, "2. DỊCH VỤ ĐƯỢC LỰA CHỌN VÀ TÍNH PHÙ HỢP")
heading(doc, 3, "2.1. Thông tin cơ bản về Microsoft Azure App Service")
body(doc, "Nhóm chọn **Azure App Service** — dịch vụ PaaS (Platform as a Service) chạy ứng dụng web của "
          "Microsoft — cụ thể là loại **Web App chạy trên nền Linux, stack Python**. Người dùng chỉ nộp mã "
          "nguồn và khai báo lệnh khởi động; nền tảng lo máy chủ ứng dụng, HTTPS, cân bằng tải, khởi động "
          "lại tiến trình và vá hệ điều hành. Các thông số nhóm dùng cho FreshMart:")
make_table(doc,
           ["Thông tin", "Giá trị nhóm chọn", "Ý nghĩa với FreshMart"],
           [["Loại tài nguyên", "Web App (chu kỳ vòng đời: Continuous Deployment)", "Nhận mã Flask trực tiếp, không phải dựng container"],
            ["Ngăn xếp công nghệ", "Python 3.12 trên hình nền Linux của App Service", "Khớp với mã nguồn Flask 3.x; hình nền đã có Gunicorn"],
            ["App Service Plan", "F1 (Free) trên plan Shared, region Southeast Asia", "Không chi phí, độ trễ thấp cho người xem ở Việt Nam"],
            ["Tên miền", "`https://<tên-app>.azurewebsites.net`, HTTPS mặc định", "Giảng viên mở link là thấy sản phẩm chạy"],
            ["Lưu trữ", "Mục `/home` là Azure Files được gắn bền vững; mã nằm ở `/home/site/wwwroot`", "Tệp `freshmart.db` đặt trong `/home` nên không mất khi khởi động lại"],
            ["Cổng và tiến trình", "App Service cấp biến `PORT`; ứng dụng chạy sau `gunicorn --bind=0.0.0.0:$PORT app:app`", "Thay cho `app.run(port=5000, debug=True)` khi chạy cục bộ"],
            ["Cấu hình", "Application Settings (biến môi trường), Startup Command, Deployment Center", "Khai báo `SECRET_KEY`, `DATABASE_PATH` mà không sửa mã"]],
           widths=[2.9, 6.7, 6.4])
body(doc, "Về hạn mức, mức Free dùng tài nguyên chia sẻ, có trần thời gian CPU mỗi ngày và không bật Always "
          "On, nên vừa cho một buổi bảo vệ đồ án chứ không cho cửa hàng thật; khi cần, chỉ đổi sang B1 bằng "
          "thao tác Scale up mà giữ nguyên URL và dữ liệu.")
heading(doc, 3, "2.2. Giao diện và tính năng của dịch vụ sau khi đăng nhập tài khoản")
body(doc, "Sau khi đăng nhập vào `portal.azure.com` bằng tài khoản của nhóm, giao diện Azure Portal hiển thị "
          "thanh tìm kiếm, mục Favorites, danh sách Resource Group và bảng Blade của Web App vừa tạo. Mỗi "
          "blade cung cấp một nhóm tính năng mà đồ án sử dụng thật trong quá trình triển khai:")
make_table(doc,
           [" Blade / tính năng trên Azure Portal", "Nội dung hiển thị hoặc thao tác", "Việc đồ án đã dùng"],
           [["Overview", "URL công khai, trạng thái Running, giờ khởi động gần nhất, biểu đồ yêu cầu, App Service Plan", "Kiểm tra site đã sống và mở FreshMart để trình diễn"],
            ["Configuration", "Tab General (phiên bản Python, Startup Command), Tab Application settings, Path mappings", "Khai báo `SECRET_KEY`, `DATABASE_PATH=/home/data/freshmart.db`"],
            ["Deployment Center", "Nguồn triển khai (GitHub Actions, Zip, FTP, Local Git), log các lần deploy", "Gắn repository FreshMart và theo dõi lần phát hành"],
            ["Log stream và Console (Kudu)", "Nhật ký ứng dụng thời gian thực; bán dòng trong đúng môi trường chạy", "Thấy lỗi thiếu phụ thuộc; kiểm tra `/home`, quyền ghi và phiên bản Python"],
            ["App Service plan và slots", "Scale up kích cỡ CPU/RAM, Scale out số instance, deployment slot", "Nâng F1 lên B1 khi demo cần ổn định; đưa bản thử vào slot rồi swap"],
            ["Monitoring, Networking, Certificates", "Metrics, Alert, quy tắc vào/ra, tên miền và chứng chỉ tùy biến", "Theo dõi thời gian đáp ứng và ràng buộc nguồn truy cập nếu thu hẹp phạm vi demo"]],
           widths=[3.8, 6.0, 6.2])
fig(doc, "Ảnh chụp blade Overview của Web App sau khi đăng nhập Azure Portal, thấy URL azurewebsites.net và trạng thái Running.",
    "Bảng điều khiển Azure App Service sau khi đăng nhập")
fig(doc, "Ảnh chụp tab Application settings và Startup Command trong blade Configuration của Web App FreshMart.",
    "Cấu hình biến môi trường và lệnh khởi động của ứng dụng")
heading(doc, 3, "2.3. Tính hợp lý của dịch vụ được lựa chọn với bài toán")
body(doc, "Tính hợp lý thể hiện ở bốn điểm gắn với chính bài toán đã phát biểu. **Khớp công nghệ:** FreshMart "
          "chỉ cần Python, Flask và SQLite, mà App Service đã có hình nền Python hỗ trợ Gunicorn nên không phải "
          "dựng container. **Khớp mô hình dữ liệu:** ràng buộc lớn nhất là tồn kho và đơn hàng phải ghi được "
          "xuống đĩa, trong khi mục `/home` của App Service là vùng lưu trữ bền vững (Azure Files), nên chỉ cần "
          "trỏ `DATABASE_PATH` vào đó là giữ được dữ liệu qua các lần khởi động lại và deploy. **Khớp nghiệp "
          "vụ:** mọi quy tắc tính tiền, giới hạn tồn kho và trừ kho đều chạy phía máy chủ trong `models.py` và "
          "`get_cart_details`, nên khi chuyển sang Azure, kết quả hiển thị không đổi. **Khớp chi phí và tiến "
          "độ:** mức Free đủ cho buổi bảo vệ, kèm GitHub Actions để mỗi lần nhóm sửa nghiệp vụ là site tự cập nhật.")
body(doc, "Các điểm phải chấp nhận, nhóm nêu trung thực: mức Free dùng tài nguyên chia sẻ và có trần CPU mỗi "
          "ngày nên site có thể chậm; SQLite ghi qua vùng lưu trữ chia sẻ chỉ an toàn ở một instance, nếu Scale "
          "out thì phải chuyển sang Azure Database for PostgreSQL; `debug` phải tắt và `SECRET_KEY` phải nằm "
          "trong Application settings vì mã hiện dùng giá trị dự phòng hard-code; ảnh sản phẩm đang tham chiếu "
          "URL ngoài nên khi mất mạng sẽ lỗi hiển thị. Toàn bộ các điểm này được xử lý trong mục 5.")

# =========================================================== CHƯƠNG 2 =======
heading(doc, 1, "CHƯƠNG 2. GIẢI PHÁP VÀ TRIỂN KHAI", center=True, page_break=True)

heading(doc, 2, "3. PHÂN CÔNG CÔNG VIỆC TRONG NHÓM")
heading(doc, 3, "3.1. Nguyên tắc phân công")
body(doc, "Mã nguồn tách thành các khu vực tương đối rõ nên việc chia vai trò dựa trên khu vực phụ trách, "
          "kèm một người làm tích hợp. Điều phối viên giữ luồng nghiệp vụ chính (`app.py` và các trang "
          "giỏ hàng, thanh toán); thành viên dữ liệu giữ `models.py` và `database.py`; thành viên giao diện "
          "giữ `templates/` và `static/`; thành viên triển khai giữ kho mã nguồn, cấu hình dịch vụ cloud và "
          "tài liệu. Mỗi khu vực được mô tả bằng URL, phương thức và dữ liệu đầu vào để người khác không "
          "phải đoán.")
make_table(doc,
           ["Vai trò", "Họ tên / MSSV", "Khu vực phụ trách", "Sản phẩm bàn giao"],
           [["TV1 – Điều phối, nghiệp vụ giỏ hàng và đặt hàng", "……………………", "`app.py`: `get_cart_details`, các tuyến `/cart`, `/checkout`, `/order-success`", "Luồng đặt hàng hoàn chỉnh, công thức phí vận chuyển"],
            ["TV2 – Dữ liệu và lớp mô hình", "……………………", "`models.py`, `database.py`, `config.py`", "Lược đồ 6 bảng, `migrate_db`, `seed_data`, ràng buộc tồn kho"],
            ["TV3 – Giao diện khách và quản trị", "……………………", "`templates/`, `static/css`, `static/js`", "18 mẫu Jinja2, AJAX thêm giỏ, badge số lượng, phiếu in"],
            ["TV4 – Triển khai cloud, kiểm thử và tài liệu", "……………………", "Repository, Azure App Service, kịch bản kiểm thử, báo cáo", "Hướng dẫn triển khai, bảng kết quả kiểm thử, báo cáo và slide"]],
           widths=[4.3, 3.0, 4.7, 4.0])
note(doc, "Nhóm cập nhật họ tên và MSSV sau khi thống nhất nội bộ; tỷ lệ đóng góp nên phản ánh cả phân "
          "tích, lập trình, tích hợp, tài liệu và trình bày theo quy định của học phần. Nếu nhóm ít thành "
          "viên hơn, có thể gộp TV1 với TV4.")
heading(doc, 3, "3.2. Quy tắc phối hợp")
bullet(doc, "Thống nhất tên cột và kiểu dữ liệu trước khi cùng sửa mô hình, tuyến URL và mẫu giao diện; mỗi thay đổi nghiệp vụ phải nêu URL, phương thức HTTP, dữ liệu đầu vào và kết quả mong đợi.")
bullet(doc, "Dùng nhánh riêng cho phần việc độc lập, gộp qua pull request hoặc rà soát trực tiếp; cuối mỗi giai đoạn, điều phối viên chạy lại luồng từ xem sản phẩm đến tạo đơn và kiểm tra khu vực quản trị.")
bullet(doc, "Không đưa mật khẩu thật, khóa bí mật, dữ liệu khách hàng thật hay bản sao CSDL cá nhân lên repository công khai.")

heading(doc, 2, "4. KẾ HOẠCH THỰC HIỆN MINI-PROJECT")
heading(doc, 3, "4.1. Các giai đoạn và kết quả dự kiến")
body(doc, "Kế hoạch dưới đây là khung tham khảo cho một nhóm sinh viên trong 6 tuần (02/11 đến 13/12/2026). "
          "Nhóm cần thay bằng số liệu thực tế của mình trước khi nộp, vì phần đánh giá quá trình yêu cầu "
          "khoảng thời gian và người thực hiện đúng với lịch học.")
make_table(doc,
           ["Giai đoạn", "Thời lượng", "Nội dung chính", "Kết quả kiểm chứng"],
           [["1. Khảo sát", "Tuần 1", "Đọc nghiệp vụ bán lẻ thực phẩm, liệt kê yêu cầu, dựng kịch bản user journey", "Bảng yêu cầu và phạm vi đề tài"],
            ["2. Thiết kế", "Tuần 1", "Vẽ kiến trúc ba lớp, thiết kế 6 bảng và công thức hóa đơn", "Lược đồ dữ liệu và công thức phí ship"],
            ["3. Nền tảng", "Tuần 2", "Khởi tạo Flask, `config.py`, `database.py`, `base.html`, dữ liệu mẫu", "Trang chủ hiển thị 19 sản phẩm, 6 danh mục"],
            ["4. Mua hàng", "Tuần 3", "Giỏ hàng theo phiên, giới hạn tồn kho, đổi kiểu giao, voucher", "Đơn hàng tính đúng và không vượt kho"],
            ["5. Thanh toán", "Tuần 4", "Trang checkout, khung giờ giao, mã đơn, VietQR, phiếu in, lịch sử đơn", "Tra được đơn theo mã `FM-...`"],
            ["6. Quản trị", "Tuần 4–5", "Bảng điều khiển thống kê, CRUD sản phẩm và danh mục, cập nhật tiến độ và shipper", "Cảnh báo sản phẩm tồn từ 20 trở xuống"],
            ["7. Cloud và hoàn thiện", "Tuần 5–6", "Sửa cấu hình để chạy ngoài localhost, bổ sung `gunicorn`, tạo Web App trên Azure, deploy, chụp ảnh, viết báo cáo", "URL azurewebsites.net hoạt động, báo cáo và slide"]],
           widths=[2.7, 1.9, 7.4, 4.0])
heading(doc, 3, "4.2. Tiêu chí hoàn thành")
bullet(doc, "Ứng dụng khởi chạy theo hướng dẫn, trang chủ không lỗi; tìm kiếm, lọc danh mục và khoảng giá, sắp xếp theo giá, phân trang 12 sản phẩm hoạt động với dữ liệu mẫu.")
bullet(doc, "Giỏ hàng không cho vượt tồn kho; tiền hàng, phí ship, số tiền giảm và tổng hiển thị đúng công thức.")
bullet(doc, "Đơn hàng được lưu kèm thông tin người nhận, snapshot từng mặt hàng, kiểu giao, khung giờ và ba nhóm trạng thái.")
bullet(doc, "Khách hàng không vào được khu vực quản trị; truy cập trực tiếp tuyến `/admin` bị chuyển về trang đăng nhập kèm cảnh báo; quản trị viên quản lý sản phẩm, danh mục, trạng thái đơn và shipper.")
bullet(doc, "Bản triển khai trên Azure mở được từ URL công khai; các lỗi thường gặp có mô tả và hướng xử lý.")
heading(doc, 3, "4.3. Quản lý rủi ro và chất lượng")
make_table(doc,
           ["Rủi ro", "Mức độ", "Biện pháp phòng ngừa và xử lý"],
           [["Bán vượt tồn kho khi hai khách đặt cùng lúc", "Trung bình", "Ép số lượng theo tồn kho trong `get_cart_details`, tái kiểm tra từng mặt hàng trong `checkout` trước khi ghi, trừ kho bằng `MAX(0, ...)`"],
            ["Người dùng sửa dữ liệu trong phiên (giỏ hàng, voucher) gây lỗi tính tiền", "Trung bình", "Hàm tính giỏ hàng bọc an toàn, bỏ mục không hợp lệ thay vì ném lỗi; tổng thanh toán không âm và được tính lại ở máy chủ trước khi ghi đơn"],
            ["Hạn sử dụng lưu dạng chuỗi nên không so sánh được ngày", "Thấp", "Dùng cho trình diễn; hướng chuẩn hóa kiểu ngày được đưa vào mục phát triển"],
            ["Dữ liệu mất khi triển khai cloud nếu để CSDL trong thư mục mã nguồn", "Cao", "Trỏ `DATABASE_PATH` vào `/home/data` (vùng Azure Files bền vững), sao lưu `freshmart.db`; nếu Scale out thì chuyển sang PostgreSQL"],
            ["Khóa bí mật hard-code trong `config.py`", "Cao", "Chấp nhận biến môi trường `SECRET_KEY`, giá trị dự phòng chỉ dùng khi chạy cục bộ"],
            ["Trang demo chậm vì free tier ngủ đông", "Thấp", "Mở site trước buổi trình diễn vài phút và nêu trước với người xem"]],
           widths=[4.6, 1.6, 9.8])

heading(doc, 2, "5. CÁC BƯỚC TRIỂN KHAI LÊN DỊCH VỤ CLOUD")
heading(doc, 3, "5.1. Tạo tài khoản Azure và tài khoản GitHub")
body(doc, "Toàn bộ quy trình dưới đây dùng tài khoản miễn phí, không phát sinh chi phí cho một buổi bảo vệ. "
          "Nhóm chọn đường dẫn dành cho sinh viên vì không cần thẻ ngân hàng; nếu không còn xác nhận được tư "
          "cách sinh viên thì dùng tài khoản Free và chấp nhận bước xác minh bằng thẻ.")
make_table(doc,
           ["Bước", "Thao tác", "Kết quả cần thấy"],
           [["1", "Mở `azure.microsoft.com/free/students` nếu còn là sinh viên (dùng email trường); nếu không thì mở `azure.com/free` và bấm Start free", "Form đăng ký hiện ra, yêu cầu xác thực bằng email trường hoặc bằng thẻ tùy đường dẫn"],
            ["2", "Đăng nhập bằng tài khoản Microsoft ( tạo mới nếu chưa có)", "Portal ghi nhận danh tính và chuyển sang màn hình About you"],
            ["3", "Khai báo họ tên, quốc gia, số điện thoại; nhận mã OTP qua SMS và nhập", "Dòng xác minh số điện thoại chuyển xanh hợp lệ"],
            ["4", "Chỉ đường dẫn Free: thêm thẻ ngân hàng hoặc Visa/Master để xác minh danh tính, không bị trừ tiền", "Xác minh danh tính thành công; phần Credit hiện 200 USD trong 30 ngày"],
            ["5", "Bấm Sign up, chờ khoảng hai phút để hệ thống cấp subscription", "Portal mở tại Home, subscription là Azure for Students hoặc Azure Free Trial"],
            ["6", "Kiểm tra Cost Management + Billing, bảo đảm Spending limit đang Bật", "Trạng thái Spending limit: On, nghĩa là dịch vụ bị khóa khi hết credit thay vì thu tiền"],
            ["7", "Home → Create a resource → Resource group → tên `freshmart-rg`, region Southeast Asia", "Resource group mới xuất hiện trong danh sách và trong dashboard"]],
           widths=[1.0, 7.4, 7.6])
fig(doc, "Ảnh chụp trang Azure Free Student Account và nút Activate/Sign up trước khi điền thông tin.",
    "Bắt đầu tạo tài khoản Azure miễn phí cho sinh viên")
body(doc, "Vì FreshMart hiện chưa phải một repository Git trong máy, nhóm tạo kho mã nguồn ở bước này để "
          "Deployment Center của App Service đọc được và để mỗi lần sửa nghiệp vụ là site tự cập nhật:")
make_table(doc,
           ["Bước", "Thao tác", "Kết quả cần thấy"],
           [["1", "Đăng ký hoặc đăng nhập `github.com`, tạo repository `freshmart`, chọn Private hoặc Public", "Repository trống hiện tab Quick setup"],
            ["2", "Trong thư mục FreshMart tạo `.gitignore` loại `.venv/`, `__pycache__/`, `freshmart.db`, `static/uploads/`, `*.docx` và `~$*`", "Lệnh `git status` không còn liệt kê tệp CSDL và môi trường ảo"],
            ["3", "`git init`, `git add .`, `git commit -m 'FreshMart Flask'`, `git branch -M main`", "Báo đã ghi một commit đầu tiên trên nhánh main"],
            ["4", "`git remote add origin https://github.com/<user>/freshmart.git` rồi `git push -u origin main`", "Repository trên GitHub hiển thị `app.py`, `models.py`, `database.py`, `templates/`, `static/`"],
            ["5", "Kiểm tra lại không có tệp `freshmart.db` và không có mật khẩu thật trong mã nguồn vừa push", "Tìm kiếm trong repository không ra tên đăng nhập hay dữ liệu khách hàng"]],
           widths=[1.0, 7.4, 7.6])
fig(doc, "Ảnh chụp repository `freshmart` trên GitHub sau lần push đầu, thấy các tệp `app.py`, `models.py`, `database.py` và thư mục `templates/`.",
    "Kho mã nguồn FreshMart trên GitHub trước khi gắn vào App Service")
note(doc, "Học phần này chỉ cần một tài khoản Azure dùng chung cho nhóm; mỗi thành viên tự đăng ký sẽ làm phân "
          "tán credit và dễ vượt hạn mức. Chủ tài khoản nên giữ subscription ở chế độ Spending limit On trong "
          "suốt thời gian làm đồ án.")
heading(doc, 3, "5.2. Danh mục ảnh minh họa và vị trí cần dán")
body(doc, "Báo cáo có 15 khung ảnh để trống, mỗi khung in dòng chữ đỏ [ DÁN ẢNH VÀO KHUNG NÀY ] và có chú thích "
          "tự đánh số bên dưới. Bảng sau chỉ định khung đó nằm ở mục nào, cần chụp cảnh gì và lấy cảnh đó bằng "
          "thao tác nào; mỗi ảnh nên đặt chiều cao 6 đến 8 cm để bản in gọn trong khổ A4.")
make_table(doc,
           ["Hình", "Thuộc mục", "Cảnh cần chụp", "Cách lấy cảnh"],
           [["1", "1.2", "Sơ đồ ba lớp: trình duyệt, tuyến URL Flask, lớp mô hình, SQLite, mẫu Jinja2", "Vẽ bằng diagrams.net hoặc PowerPoint rồi xuất ảnh, chụp lại màn hình sơ đồ"],
            ["2", "2.2", "Blade Overview của Web App, thấy URL và trạng thái Running", "Đăng nhập `portal.azure.com`, mở resource group rồi bấm vào Web App FreshMart"],
            ["3", "2.2", "Tab Environment variables và Startup Command trong blade Configuration", "Overview → Configuration → lần lượt hai tab General và Environment variables"],
            ["4", "5.1", "Trang Azure Free Student Account với nút Activate Now", "Mở `azure.microsoft.com/free/students` bằng email trường, chụp trước khi điền form"],
            ["5", "5.1", "Repository `freshmart` trên GitHub sau lần push đầu", "Mở `github.com/<user>/freshmart`, chụp danh sách tệp `app.py`, `models.py`, `templates/`"],
            ["6", "5.4", "Form Create Web App với Publish = Code, Runtime Python 3.12, region Southeast Asia, plan F1", "Home → Create a resource → Web App, dừng ở bước Basics trước khi bấm Review"],
            ["7", "5.4", "Deployment Center hiển thị nguồn GitHub Actions và log lần deploy", "blade Web App → Deployment Center → chọn GitHub, bấm Authorize rồi xem mục Logs"],
            ["8", "5.5", "Console (Kudu) liệt kê `/home/data/freshmart.db` và phiên bản Python", "Development Tools → Console, chạy `ls /home/data` và `python -V`"],
            ["9", "5.6", "Trang chủ FreshMart mở từ URL azurewebsites.net", "Dán URL công khai vào trình duyệt, ẩn thanh bookmark, chụp toàn trang"],
            ["10", "6.2", "Trang danh mục với bộ lọc danh mục, khoảng giá và kiểu sắp xếp", "Mở `/products`, chọn một danh mục và khoảng giá rồi bấm Sắp xếp"],
            ["11", "6.2", "Trang chi tiết sản phẩm: giá, giá gạch, tồn kho, ngày sản xuất, hạn sử dụng", "Bấm vào một sản phẩm từ trang danh mục"],
            ["12", "6.2", "Giỏ hàng: phí vận chuyển, thanh tiến độ miễn phí và ô nhập mã giảm giá", "Thêm hai sản phẩm rồi mở `/cart`, chọn Giao siêu tốc 2 giờ"],
            ["13", "6.2", "Trang xác nhận đơn: mã đơn, mã VietQR và phiếu in", "Đặt đơn bằng tài khoản `khachhang`, dừng ở trang cảm ơn và bấm In hóa đơn"],
            ["14", "6.3", "Bảng điều khiển `/admin` với các thẻ thống kê và cảnh báo tồn kho", "Đăng nhập `admin`, chụp phần đầu trang quản trị"],
            ["15", "6.3", "`/admin/orders` với ô chọn trạng thái và ô nhập tên shipper", "Mở mục Đơn hàng, chọn một đơn ở trạng thái đang giao"]],
           widths=[1.1, 1.8, 6.5, 6.6])
note(doc, "Ảnh 1 là sơ đồ tự vẽ nên chèn được ngay; ảnh 4 và 5 chụp ở bước tạo tài khoản và tạo kho mã nguồn; "
          "các ảnh 2, 3, 6, 7, 8 chỉ tồn tại sau khi nhóm làm thật mục 5.4 và 5.5; riêng ảnh 9 đến 15 phải chụp "
          "từ bản chạy trên cloud, không chụp ở `http://127.0.0.1:5000`.")
heading(doc, 3, "5.3. Chuẩn bị mã nguồn trước khi deploy")
body(doc, "Ứng dụng hiện chạy hoàn toàn cục bộ: `python database.py` để nạp dữ liệu mẫu rồi `python app.py`, "
          "truy cập tại `http://127.0.0.1:5000`; hai tệp `run.bat` và `run.ps1` chỉ tự động hóa việc này. "
          "Năm việc sau là bắt buộc trước khi nộp mã cho App Service:")
bullet(doc, "Tạo repository Git cho FreshMart, push lên GitHub; thêm `.gitignore` loại `__pycache__/`, `.venv/`, `freshmart.db` và `static/uploads` để không đưa CSDL có dữ liệu cá nhân lên kho.")
bullet(doc, "Bổ sung `gunicorn` vào `requirements.txt` (hiện mới có `Flask>=3.0.0` và `Werkzeug>=3.0.0`) để có máy chủ ứng dụng độc lập với `app.run`.")
bullet(doc, "Bỏ `debug=True`: App Service chạy lệnh khởi động riêng, nên khối `if __name__ == '__main__'` chỉ còn ý nghĩa khi lập trình tại máy; đồng thời đọc cổng từ biến môi trường `PORT` do nền tảng cấp thay vì hard-code 5000.")
bullet(doc, "Chuyển `SECRET_KEY` vào Application settings; `config.py` đã ưu tiên `os.environ.get('SECRET_KEY', ...)`, chỉ cần bỏ giá trị dự phòng khỏi kho hoặc đổi thành chuỗi ngẫu nhiên.")
bullet(doc, "Cho phép ghi đè đường dẫn CSDL: ghép `DATABASE_PATH` từ biến môi trường để trỏ vào `/home/data/freshmart.db`, vùng lưu trữ bền vững của App Service.")
body(doc, "Ba sửa đổi cụ thể trong mã nguồn, ghi nguyên văn để nhóm đối chiếu khi làm:")
make_table(doc,
           ["Tệp", "Dòng hiện tại", "Thay bằng"],
           [["`config.py`", "`DATABASE_PATH = os.path.join(BASE_DIR, 'freshmart.db')`", "`DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'freshmart.db'))`"],
            ["`app.py` (cuối tệp)", "`app.run(host='0.0.0.0', port=5000, debug=True)`", "`app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)`"],
            ["`requirements.txt`", "`Flask>=3.0.0` và `Werkzeug>=3.0.0`", "thêm một dòng `gunicorn>=22,<24`"]],
           widths=[2.6, 6.0, 7.4])
note(doc, "Vì `app.py` gọi `init_db` hoặc `migrate_db` ngay khi nạp mô-đun, chỉ cần đường dẫn dữ liệu hợp lệ "
          "và có quyền ghi là ứng dụng tự tạo bảng và tự nạp dữ liệu mẫu ở lần chạy đầu trên cloud.")
heading(doc, 3, "5.4. Tạo Web App và cấu hình chạy trên Azure")
body(doc, "Bảy bước sau được viết theo đúng thứ tự màn hình Azure Portal; cột Kết quả cho biết điều phải thấy "
          "trước khi chuyển sang bước kế tiếp, cột Ảnh ghi số khung tương ứng trong báo cáo.")
make_table(doc,
           ["Bước", "Thao tác trong Azure Portal", "Kết quả cần thấy", "Ảnh"],
           [["1", "Đăng nhập `portal.azure.com` → Create a resource → tìm Web App → Create", "Blade Web App mở ra với bốn tab Basics, Networking, Monitoring, Tags", ""],
            ["2", "Tab Basics: đặt Resource group `freshmart-rg`, nhập Name, Publish = Code, Runtime stack = Python 3.12, Region = Southeast Asia", "Tên app hợp lệ và duy nhất; portal báo URL tương lai dạng `<tên>.azurewebsites.net`", "Hình 6"],
            ["3", "Vẫn tab Basics: Operating System = Linux, Create new App Service plan, size F1 (Free)", "Dòng Structure hiện Free tier với trần CPU hàng ngày", "Hình 6"],
            ["4", "Review + Create → Create, chờ 2 đến 4 phút", "Deployment complete, blade Overview hiện Trạng thái Running", "Hình 2"],
            ["5", "Overview → Configuration → tab General → ô Startup Command", "Lệnh `gunicorn --bind=0.0.0.0:$PORT --workers 1 --threads 8 --timeout 120 app:app` được chấp nhận", "Hình 3"],
            ["6", "Configuration → tab Environment variables → New setting, thêm `SECRET_KEY`, `DATABASE_PATH=/home/data/freshmart.db`, `FLASK_ENV=production`", "Ba biến hiện trong danh sách, cột Value được mask; bấm Save để lưu", "Hình 3"],
            ["7", "Bấm Save, chờ Web App khởi động lại rồi mở URL công khai", "Trang chủ FreshMart hiển thị kèm sản phẩm nổi bật do `seed_data` nạp", "Hình 9"]],
           widths=[1.0, 6.6, 6.8, 1.6])
fig(doc, "Ảnh chụp form Create Web App với Publish = Code, Runtime stack = Python 3.12, region Southeast Asia và plan F1.",
    "Tạo Web App cho FreshMart trên Azure")
fig(doc, "Ảnh chụp Deployment Center của Web App, hiển thị nguồn GitHub Actions và trạng thái lần deploy.",
    "Gắn repository FreshMart và theo dõi lần triển khai")
heading(doc, 3, "5.5. Đưa mã nguồn lên dịch vụ")
body(doc, "Nhóm dùng một trong ba cách sau, đều được App Service hỗ trợ trực tiếp; cách (b) nên chọn vì tái "
          "lập được và minh họa đúng quy trình CI/CD của học phần:")
bullet(doc, "**(a) ZIP deploy:** nén mã nguồn (không kèm `.venv` và `__pycache__`) rồi chạy `az webapp deploy --resource-group freshmart-rg --name <tên-app> --src-path freshmart.zip`, hoặc kéo thả tệp vào thẻ Deployment Center.")
bullet(doc, "**(b) GitHub Actions (OIDC):** trong Deployment Center chọn GitHub, App Service sinh sẵn tệp workflow; nhóm chỉ cần cấp quyền cho service principal một lần. Mỗi lần push lên nhánh chính là site tự dựng và khởi động lại.")
bullet(doc, "**(c) Local Git hoặc Visual Studio Code:** thêm remote deploy của App Service rồi `git push azure main`, hoặc dùng extension Azure App Service để Deploy và xem Log stream ngay trong trình soạn thảo.")
body(doc, "Sau khi deploy, mở Console (Kudu) để kiểm chứng nhanh: thư mục `/home/data` có tệp `freshmart.db`, "
          "`python -V` đúng 3.12, và tiến trình Gunicorn nhận cổng từ biến `PORT`. Log stream phải hiện dòng "
          "`[+] Khởi tạo database` của `database.py` ở lần chạy đầu.")
fig(doc, "Ảnh chụp Console (Kudu) liệt kê `/home/data/freshmart.db` và phiên bản Python trong môi trường chạy.",
    "Kiểm tra vùng dữ liệu bền vững sau khi triển khai")
heading(doc, 3, "5.6. Kiểm tra sau triển khai và lỗi thường gặp")
make_table(doc,
           ["Hiện tượng sau deploy", "Nguyên nhân thường gặp", "Hướng xử lý"],
           [["Build báo lỗi thiếu module", "Thiếu phụ thuộc trong `requirements.txt`", "Bổ sung `gunicorn` và các gói cần thiết, deploy lại"],
            ["URL trả lỗi 502 hoặc 404 sau khi Running", "Startup Command sai, bind nhầm cổng, hoặc module Flask không phải tên `app`", "Dùng `--bind=0.0.0.0:$PORT`, kiểm tra `app:app` và xem Log stream"],
            ["Trang chủ mở được nhưng thêm giỏ hàng bị mất", "`SECRET_KEY` thay đổi mỗi lần khởi động làm mất hiệu lực phiên", "Khai báo `SECRET_KEY` cố định trong Application settings"],
            ["Đơn hàng và sản phẩm biến mất sau khi deploy", "Để CSDL trong thư mục mã nguồn (`BASE_DIR`), bị ghi đè khi dựng lại", "Trỏ `DATABASE_PATH` vào `/home/data` là vùng Azure Files bền vững"],
            ["Lỗi ghi CSDL khi bật nhiều instance; site chậm hoặc bị từ chối theo giờ", "SQLite ghi qua vùng lưu trữ chia sẻ nên khóa không an toàn khi Scale out; mức F1 dùng tài nguyên chia sẻ và có trần CPU mỗi ngày", "Giữ một instance và mở site trước buổi demo; khi cần tải thật thì Scale up lên B1 và chuyển sang Azure Database for PostgreSQL"]],
           widths=[4.3, 5.3, 6.4])
fig(doc, "Ảnh chụp website FreshMart mở từ URL azurewebsites.net trên trình duyệt (trang chủ đã có dữ liệu mẫu).",
    "Giao diện FreshMart sau khi triển khai trên Azure")

# =========================================================== CHƯƠNG 3 =======
heading(doc, 1, "CHƯƠNG 3. KẾT QUẢ VÀ ĐÁNH GIÁ", center=True, page_break=True)

heading(doc, 2, "6. KẾT QUẢ, GIAO DIỆN VÀ HƯỚNG DẪN SỬ DỤNG")
heading(doc, 3, "6.1. Kết quả chức năng")
make_table(doc,
           ["Nhóm chức năng", "Cài đặt trong mã nguồn", "Trạng thái"],
           [["Xem, lọc và chi tiết sản phẩm", "`search_and_filter` theo danh mục, từ khóa, khoảng giá, bốn kiểu sắp xếp; phân trang `ITEMS_PER_PAGE = 12`; `get_featured` (8 sản phẩm), `get_new_arrivals`, `get_related`", "Hoàn chỉnh"],
            ["Thông tin tươi sống", "Cột ngày sản xuất, hạn sử dụng, cách bảo quản; mặc định thân thiện khi trống do `ensure_product_expiry_dates`", "Hoàn chỉnh"],
            ["Giỏ hàng và tồn kho", "Bảy tuyến `/cart` (thêm, tăng giảm, sửa hàng loạt, xóa, làm trống, đổi kiểu giao, cập nhật); ép số lượng theo `stock` cả ở AJAX lẫn form", "Hoàn chỉnh"],
            ["Phí vận chuyển và voucher", "Tiêu chuẩn 20.000 đồng, miễn từ 300.000 đồng; siêu tốc 2 giờ 35.000 đồng còn 15.000 đồng khi đạt ngưỡng; `CouponModel.validate` kiểm tra đơn tối thiểu, mã `FREESHIP` miễn phí", "Hoàn chỉnh"],
            ["Đặt hàng và hóa đơn", "`OrderModel.create` sinh mã đơn, ghi snapshot mặt hàng, trừ kho; trang xác nhận hiển thị VietQR và phiếu in", "Hoàn chỉnh"],
            ["Tài khoản, phân quyền và quản trị", "Đăng nhập bằng tên hoặc email với mật khẩu băm, đăng ký chống trùng, trang cá nhân và lịch sử đơn; `login_required` và `admin_required`; thống kê, CRUD, cập nhật trạng thái và shipper", "Hoàn chỉnh"]],
           widths=[3.4, 10.6, 2.0])
heading(doc, 3, "6.2. Hướng dẫn khách hàng")
body(doc, "Khách có thể mua mà không cần đăng nhập; ứng dụng chỉ yêu cầu đăng nhập với các tuyến cá nhân "
          "hóa. Luồng chuẩn gồm sáu bước: (1) mở trang chủ hoặc `/products`, tìm bằng ô tìm kiếm hoặc lọc "
          "theo danh mục và khoảng giá; (2) mở trang chi tiết để đọc mô tả, đơn vị tính, tồn kho, ngày sản "
          "xuất và cách bảo quản; (3) chọn số lượng bằng bộ tăng giảm — nút cộng dừng ở đúng số tồn và bật "
          "thông báo nếu kho ít hơn; (4) bấm thêm vào giỏ, badge trên thanh điều hướng cập nhật ngay nhờ "
          "AJAX; (5) vào `/cart`, chọn Giao tiêu chuẩn hoặc Giao siêu tốc 2 giờ để phí và tổng tiền đổi trực "
          "tiếp, quan sát thanh tiến độ miễn phí vận chuyển và nhập mã giảm nếu đủ điều kiện; (6) sang "
          "`/checkout`, điền họ tên, điện thoại, địa chỉ, chọn khung giờ giao, phương thức thanh toán, ghi chú rồi xác nhận.")
fig(doc, "Ảnh chụp trang danh sách sản phẩm với bộ lọc danh mục, khoảng giá và kiểu sắp xếp.",
    "Trang sản phẩm: tìm kiếm, lọc và phân trang")
fig(doc, "Ảnh chụp trang chi tiết sản phẩm: giá, giá gạch, đơn vị tính, tồn kho, ngày sản xuất và hạn sử dụng.",
    "Trang chi tiết thể hiện thông tin tươi sống của sản phẩm")
fig(doc, "Ảnh chụp trang giỏ hàng: bảng mặt hàng, hai lựa chọn kiểu giao, thanh tiến độ miễn phí vận chuyển và ô nhập mã giảm giá.",
    "Giỏ hàng với phí vận chuyển và voucher tính theo thời gian thực")
fig(doc, "Ảnh chụp trang xác nhận đơn: mã đơn, mã VietQR và phiếu in.",
    "Xác nhận đặt hàng, mã chuyển khoản và hóa đơn bán lẻ")
heading(doc, 3, "6.3. Hướng dẫn quản trị viên")
body(doc, "Trang đăng nhập có sẵn nút điền nhanh tài khoản mẫu để phục vụ trình diễn: `admin` / `admin123` "
          "cho vai trò quản trị và `khachhang` / `123456` cho vai trò khách hàng. Đăng nhập bằng quản trị, "
          "hệ thống chuyển thẳng tới `/admin`; nếu một khách hàng thử mở trực tiếp tuyến này, decorator "
          "`admin_required` sẽ chặn và chuyển về trang đăng nhập kèm cảnh báo không có quyền.")
bullet(doc, "**Bảng điều khiển:** doanh thu đã loại đơn bị hủy, tổng số đơn, số đơn chờ, số sản phẩm, số khách hàng, năm đơn gần nhất và cảnh báo sản phẩm tồn kho từ 20 trở xuống.")
bullet(doc, "**Sản phẩm:** thêm, sửa, xóa; form gồm danh mục, tên, slug, mô tả, giá bán, giá gạch, đơn vị tính, tồn kho, ảnh, ngày sản xuất, hạn sử dụng và cách bảo quản.")
bullet(doc, "**Danh mục:** thêm danh mục mới (tên, slug tự sinh nếu trống, icon, mô tả, ảnh), xem số sản phẩm thuộc mỗi danh mục và xóa danh mục.")
bullet(doc, "**Đơn hàng:** cập nhật đồng thời trạng thái đơn (chờ duyệt, đã duyệt, đang giao, hoàn thành, đã hủy), trạng thái thanh toán (chưa, đã) và tiến độ giao (đóng gói, đang giao, đã giao), kèm tên và số điện thoại shipper.")
bullet(doc, "**Người dùng:** xem danh sách tài khoản, vai trò và thông tin liên hệ.")
fig(doc, "Ảnh chụp `/admin` hiển thị các thẻ thống kê và bảng sản phẩm sắp hết hàng.",
    "Bảng điều khiển quản trị với số liệu tổng hợp")
fig(doc, "Ảnh chụp `/admin/orders` với các ô chọn trạng thái và ô nhập tên shipper.",
    "Cập nhật tiến độ giao hàng và người giao cho từng đơn")
heading(doc, 3, "6.4. Đánh giá kết quả và giới hạn")
body(doc, "So với yêu cầu ban đầu, ứng dụng đã phủ đủ năm ràng buộc nghiệp vụ và cả hai vai trò, với một điểm "
          "mạnh đáng nhấn mạnh: mọi con số người dùng nhìn thấy đều do máy chủ tính, không phụ thuộc JavaScript, "
          "nên hành vi không đổi khi chạy trên cloud. Giới hạn còn lại thuộc về quy mô và độ chuyên sâu: hạn sử "
          "dụng chưa chuẩn hóa kiểu ngày, thanh toán mới dừng ở hiển thị mã VietQR, chưa có đánh giá sản phẩm, "
          "wishlist và API, SQLite chỉ chịu tải thấp, khu vực quản trị mới phân biệt hai vai trò, và bản cloud "
          "phụ thuộc cấu hình lưu trữ bền vững nếu muốn giữ đơn hàng lâu dài.")

heading(doc, 2, "7. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN")
heading(doc, 3, "7.1. Kết luận")
body(doc, "Nhóm đã xây dựng được một siêu thị thực phẩm trực tuyến hoạt động đầy đủ vòng đời đơn hàng trên nền "
          "Flask và SQLite, với 29 tuyến URL, 18 mẫu giao diện và 6 bảng dữ liệu, đồng thời cài đặt được ba bài "
          "toán đặc thù của ngành thực phẩm tươi: ràng buộc tồn kho ngay trong lớp mô hình, minh bạch hạn sử "
          "dụng và cách bảo quản, cùng công thức tính hóa đơn tập trung gồm phí vận chuyển theo ngưỡng và mã giảm "
          "giá. Báo cáo cũng trình bày có cơ sở phương án đưa ứng dụng lên Azure App Service, chỉ ra đúng những "
          "việc phải sửa trong mã nguồn (máy chủ ứng dụng, cổng khởi động, khóa bí mật, đường dẫn dữ liệu) và một "
          "rủi ro phải thiết kế quanh (SQLite trên vùng lưu trữ chia sẻ). Ba giá trị nhóm rút ra được: kiểm chứng "
          "nghiệp vụ phải đặt ở phía máy chủ vì dữ liệu phiên và biểu mẫu đều có thể bị sửa; tách truy vấn vào "
          "lớp mô hình giúp đổi nền tảng lưu trữ mà không viết lại giao diện; triển khai cloud không phải bước "
          "trang trí cuối kỳ mà ảnh hưởng ngược lại tới mã nguồn.")
heading(doc, 3, "7.2. Hướng phát triển")
bullet(doc, "Chuẩn hóa kiểu dữ liệu ngày cho ngày sản xuất và hạn sử dụng, thêm bộ lọc tự động đẩy sản phẩm sắp hết hạn xuống cuối danh sách và cảnh báo trên bảng quản trị.")
bullet(doc, "Chuyển tầng lưu trữ từ SQLite sang Azure Database for PostgreSQL khi cần nhiều instance, kèm di trú dữ liệu để bảo toàn đơn hàng giữa các lần triển khai.")
bullet(doc, "Kết nối cổng thanh toán thật và đối soát tự động, thay cho việc hiển thị mã VietQR thủ công; tích hợp định vị và phí giao theo khoảng cách, đồng bộ trạng thái đơn với hệ thống vận chuyển.")
bullet(doc, "Tăng cường an toàn: đặt lại mật khẩu qua email, giới hạn số lần áp dụng voucher, quyền chi tiết cho từng nhóm quản trị, thẻ chống giả mạo form và kiểm tra mã chuyển hướng hợp lệ trước khi đổi trang sau đăng nhập.")
bullet(doc, "Bổ sung đánh giá sản phẩm, danh sách yêu thích, gợi ý mua kèm, pipeline triển khai tự động có giám sát và API để mở rộng sang ứng dụng di động.")

# ==================================================== PHẦN B – DEMO =========
heading(doc, 1, "PHẦN B. HƯỚNG DẪN TRÌNH BÀY VÀ DEMO", center=True, page_break=True)
body(doc, "Yêu cầu của học phần nêu bốn nội dung mỗi nhóm bắt buộc phải làm rõ khi trình bày. Bảng dưới đây "
          "chỉ ra nội dung đó nằm ở đâu trong báo cáo và sẽ được chứng minh thế nào trong buổi demo, để hội "
          "đồng đối chiếu nhanh.")
make_table(doc,
           ["Nội dung bắt buộc", "Vị trí trong báo cáo", "Cách chứng minh khi demo"],
           [["Nêu được bài toán/vấn đề nghiên cứu (input, output, nội hàm và hướng giải quyết)", "Mục 1.1 và 1.3", "Chiếu slide phát biểu bài toán; nói ba ràng buộc: giới hạn tồn kho, minh bạch hạn sử dụng, hóa đơn có phí vận chuyển và voucher"],
            ["Các bước triển khai chi tiết lên dịch vụ cloud đã chọn", "Mục 2.2 và 5.1 đến 5.6, Ảnh 2 đến 9", "Review lại 7 bước tạo Web App trên Azure Portal, startup command, Application settings và lần deploy"],
            ["Các giao diện, tính năng, chức năng của sản phẩm sau khi triển khai trên cloud", "Mục 6.1 đến 6.3, Ảnh 10 đến 15", "Thao tác trực tiếp trên URL azurewebsites.net, không dùng localhost"],
            ["Kết luận và hướng phát triển", "Mục 7.1 và 7.2", "Tóm tắt những gì đã được, giới hạn còn lại và lộ trình ba bước tiếp theo"]],
           widths=[4.6, 3.4, 8.0])
heading(doc, 2, "B.1. Kịch bản trình bày 12 phút")
make_table(doc,
           ["Thời lượng", "Nội dung nói", "Màn hình chiếu"],
           [["0:00 – 2:00", "Vấn đề của cửa hàng thực phẩm tươi; input, output và năm ràng buộc của bài toán; vì sao chọn Azure App Service", "Slide bài toán, kiến trúc ba lớp (Ảnh 1)"],
            ["2:00 – 6:00", "Bảy bước tạo Web App, những gì phải sửa trong mã nguồn, cách deploy và cách dữ liệu được giữ trên `/home`", "Azure Portal: Overview, Configuration, Deployment Center, Log stream (Ảnh 2 – 9)"],
            ["6:00 – 10:00", "Demo mua hàng từ đầu đến hóa đơn, rồi đổi sang vai trò quản trị để duyệt đơn và xem cảnh báo hết hàng", "Website trên URL azurewebsites.net (Ảnh 10 – 15)"],
            ["10:00 – 12:00", "Kết luận, giới hạn thật của bản dùng thử và hướng phát triển; dành 30 giây nêu trước giới hạn", "Slide kết luận"]],
           widths=[2.3, 9.0, 4.7])
heading(doc, 2, "B.2. Các bước triển khai sẽ trình bày")
body(doc, "Sáu bước sau đúng thứ tự nhóm thực hiện và khớp với bảng 7 bước ở mục 5.4: (1) chuẩn bị mã nguồn — "
          "repository Git, `.gitignore`, thêm `gunicorn`, tắt `debug`, đọc cổng từ `PORT`; (2) tạo Resource "
          "Group và Web App với Runtime Python 3.12, plan F1, region Southeast Asia; (3) đặt Startup Command "
          "`gunicorn --bind=0.0.0.0:$PORT app:app`; (4) khai báo `SECRET_KEY` và "
          "`DATABASE_PATH=/home/data/freshmart.db` rồi Save; (5) deploy qua ZIP hoặc GitHub Actions, theo dõi "
          "Log stream; (6) mở URL công khai, chạy thử luồng đặt hàng và kiểm tra `/home/data` trong Console.")
heading(doc, 2, "B.3. Giao diện và tính năng sẽ trình diễn sau khi deploy")
body(doc, "Màn hình chiếu là bản chạy trên Azure, theo bảy cảnh khớp với mục 6.2 và 6.3: trang chủ có sản phẩm "
          "nổi bật và hàng mới về; trang danh mục có tìm kiếm, lọc khoảng giá, bốn kiểu sắp xếp, phân trang 12; "
          "trang chi tiết có giá, giá gạch, đơn vị tính, tồn kho, ngày sản xuất, hạn sử dụng; giỏ hàng có nút "
          "tăng giảm bị chặn ở mức tồn kho, thanh tiến độ miễn phí và ô voucher; trang xác nhận có mã đơn "
          "`FM-...`, mã VietQR và phiếu in; trang cá nhân liệt sử đơn cũ; khu vực quản trị có thống kê doanh "
          "thu, cảnh báo tồn từ 20 trở xuống và form cập nhật trạng thái đơn kèm shipper.")
heading(doc, 2, "B.4. Lưu ý chuẩn bị trước buổi demo")
bullet(doc, "Mở website trên Azure trước 10 phút để tiến trình đã nóng; mức F1 dùng tài nguyên chia sẻ nên lần mở đầu có thể chậm.")
bullet(doc, "Đăng nhập sẵn hai cửa sổ trình duyệt: một bằng `khachhang` để demo luồng khách, một bằng `admin` để chiếu khu vực quản trị, tránh mất thời gian gõ mật khẩu.")
bullet(doc, "Giữ sẵn một giỏ hàng và một mã đơn đã tạo để nếu thao tác trực tiếp gặp sự cố thì vẫn có nội dung để phân tích; chụp sẵn toàn bộ ảnh mục 5 và 6 để phòng lỗi mạng.")
bullet(doc, "Tắt `debug=True` trước khi trình diễn và giải thích được vì sao để debug trên cloud là không an toàn; khi hỏi về dữ liệu thật, trả lời theo mục 2.3: đơn hàng lưu ở vùng `/home` bền vững, còn nếu mở nhiều instance thì phải đổi sang PostgreSQL.")

# ==================================================== TÀI LIỆU THAM KHẢO ====
heading(doc, 1, "TÀI LIỆU THAM KHẢO", center=True, page_break=True)
refs = [
    "Mã nguồn dự án FreshMart trong workspace: `app.py` (796 dòng), `models.py` (434 dòng), `database.py` (352 dòng), `config.py`, `requirements.txt`, `templates/` (18 tệp) và `static/`.",
    "Tài liệu Flask chính thức — Quickstart, Views, Sessions, URL Dispatch. https://flask.palletsprojects.com/",
    "SQLite — Datatypes, ALTER TABLE, Transactions. https://www.sqlite.org/docs.html",
    "Microsoft Learn – Azure App Service: Overview, Create a Linux Python app, Configure a startup command and environment variables, Deploy from GitHub Actions, vùng lưu trữ `/home` bền vững. https://learn.microsoft.com/azure/app-service/",
    "Gunicorn — Design and Deployment; MDN Web Docs — HTML Forms và Fetch API; Tailwind CSS, Font Awesome, SweetAlert2 cho giao diện; VietQR cho mã chuyển khoản.",
]
for i, t in enumerate(refs, 1):
    body(doc, f"{i}. {t}")

# ================================================================= PHỤ LỤC ==
heading(doc, 1, "PHỤ LỤC", center=True)
heading(doc, 3, "Phụ lục A. Câu hỏi dự kiến của hội đồng")
body(doc, "Sáu câu hỏi sau xuất phát trực tiếp từ các ràng buộc trong mã nguồn; đáp án ngắn gọn để nhóm giữ "
          "tay khi trình bày.")
make_table(doc,
           ["Câu hỏi của hội đồng", "Trả lời dựa trên mã nguồn"],
           [["Vì sao giới hạn số lượng làm ở máy chủ chứ không chỉ ở trang?", "Giỏ hàng lưu trong phiên làm việc và người dùng có thể gửi số lượng tùy ý; `get_cart_details` đối chiếu `stock` thật và ép về mức tối đa, `checkout` kiểm tra lại trước khi ghi đơn, lệnh trừ kho dùng `MAX(0, stock - ?)` nên tồn kho không thể âm."],
            ["Nếu hai khách đặt cùng một sản phẩm thì sao?", "Kiểm tra lại tồn kho ngay trước khi ghi đơn nên trường hợp hết hàng giữa hai lượt sẽ bị chặn và báo cho khách về số còn lại; xử lý khóa dòng và giao dịch đồng thời là hướng phát triển khi chuyển sang hệ quản trị client/server."],
            ["Phí vận chuyển thay đổi thế nào?", "Hằng số nằm trong `config.py`: phí tiêu chuẩn 20.000 đồng, ngưỡng miễn phí 300.000 đồng; giao siêu tốc 2 giờ 35.000 đồng và giảm còn 15.000 đồng khi đạt ngưỡng; mã `FREESHIP` được ưu tiên miễn phí. Muốn điều chỉnh chỉ sửa cấu hình."],
            ["Vì sao cần sửa mã nguồn trước khi lên cloud?", "`app.run` đang bật `debug=True` và bind cổng 5000, còn `requirements.txt` chưa có máy chủ ứng dụng. Cloud cần bind theo biến `PORT`, chế độ debug tắt và một lệnh khởi động độc lập."],
            ["Dữ liệu của khách đặt trên cloud có giữ được không?", "Có, nếu đặt tệp `freshmart.db` trong `/home/data` vì App Service gắn vùng này bằng Azure Files và giữ qua các lần deploy. Nếu để trong thư mục mã nguồn thì sẽ bị ghi đè; còn khi Scale out nhiều instance thì phải chuyển sang Azure Database for PostgreSQL."],
            ["Vì sao mật khẩu an toàn?", "Mật khẩu được băm bằng `werkzeug.security`, khi đăng nhập dùng `check_password_hash`; giá trị mẫu chỉ có trong dữ liệu seed."]],
           widths=[4.7, 11.3])

heading(doc, 3, "Phụ lục B. Chạy dự án trên máy cá nhân")
body(doc, "Yêu cầu Python 3.10 trở lên. Từ thư mục dự án, tạo môi trường ảo rồi cài phụ thuộc bằng "
          "`pip install -r requirements.txt`; chạy `python database.py` để tạo `freshmart.db` và nạp dữ liệu "
          "mẫu; chạy `python app.py` (hoặc `run.bat`) rồi mở `http://127.0.0.1:5000`. Có thể xóa tệp CSDL để "
          "ứng dụng tự khởi tạo và nạp lại dữ liệu mẫu. Tài khoản trình diễn: `admin` / `admin123` và "
          "`khachhang` / `123456`; mã giảm giá thử nghiệm: `FRESHMART10`, `GIAM20K`, `FREESHIP`.")
note(doc, "Báo cáo được sinh tự động từ tệp `build_bao_cao.py` đặt cạnh mã nguồn FreshMart; khi nội dung "
          "thay đổi, chạy lại tệp này để tạo bản Word mới thay vì sửa trực tiếp trong Word.")

# ---------------------------------------------------------------- SAVE ------
_offending = [p.text for p in doc.paragraphs if "*" in p.text]
for _t in doc.tables:
    for _r in _t.rows:
        for _c in _r.cells:
            if "*" in _c.text:
                _offending.append(_c.text)
if _offending:
    raise SystemExit("Còn dấu * trong văn bản: " + _offending[0][:160])

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT)
try:
    doc.save(out_path)
except PermissionError:  # file đang mở trong Word -> lưu bản mới tên khác
    base, ext = os.path.splitext(OUT)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), base + "_v2" + ext)
    doc.save(out_path)
print("Saved:", out_path)
