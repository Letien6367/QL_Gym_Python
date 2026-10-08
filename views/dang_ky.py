# ==========================================
# PHÂN HỆ QUẢN LÝ ĐĂNG KÝ GÓI TẬP (REGISTRATION VIEW)
# ==========================================
"""
Quản lý đăng ký gói tập cho hội viên.
- Tự động tính ngày kết thúc dựa trên ngày bắt đầu và thời hạn gói
- Tự động cập nhật trạng thái 'Đã hết hạn' theo thời gian thực
- Kiểm tra hợp lệ bằng Logic Agent
- Lưu trữ dữ liệu an toàn qua Database Agent
"""

import tkinter as tk
from tkinter import ttk
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

try:
    from tkcalendar import DateEntry
    HAS_TKCALENDAR = True
except ImportError:
    HAS_TKCALENDAR = False

import database
from utils.validators import (
    validate_dang_ky_form, parse_date, calc_end_date, compute_status,
    find_registration_overlap
)
from views.base_crud import BaseCrudView
from views.styles import (
    COLOR_CARD_BG, COLOR_CONTENT_BG, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL
)


class DangKyView(BaseCrudView):
    def __init__(self, parent: tk.Widget, readonly: bool = False):
        super().__init__(
            parent=parent,
            title="Đăng Ký Gói Tập",
            subtitle="Quản lý hợp đồng tập luyện của hội viên và huấn luyện viên",
            readonly=readonly
        )
        self.members_map: Dict[str, int] = {}
        self.coaches_map: Dict[str, Optional[int]] = {}
        self.packages_data: List[Dict[str, Any]] = []

        self._setup_columns()
        self._build_custom_form()
        self._load_combobox_data()

        # Tự động cập nhật các gói đã hết hạn hôm nay
        database.update_expired_status()
        self.load_data()

    def _setup_columns(self):
        columns = (
            "ma_dk", "ten_hv", "sdt_hv", "ten_goi", "gia_goi",
            "ten_hlv", "ngay_dang_ky", "ngay_bat_dau", "ngay_ket_thuc", "trang_thai"
        )
        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        col_configs = [
            ("ma_dk", "Mã ĐK", 70, "center"),
            ("ten_hv", "Hội viên", 150, "w"),
            ("sdt_hv", "Số điện thoại", 100, "center"),
            ("ten_goi", "Gói tập", 130, "w"),
            ("gia_goi", "Giá gói", 110, "e"),
            ("ten_hlv", "Huấn luyện viên", 150, "w"),
            ("ngay_dang_ky", "Ngày ĐK", 95, "center"),
            ("ngay_bat_dau", "Ngày bắt đầu", 95, "center"),
            ("ngay_ket_thuc", "Ngày kết thúc", 95, "center"),
            ("trang_thai", "Trạng thái", 120, "center"),
        ]

        for col, heading, width, anchor in col_configs:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=anchor)

        # Cấu hình màu cho trạng thái
        self.tree.tag_configure("active_tag", foreground="#276749")
        self.tree.tag_configure("expired_tag", foreground="#9B2C2C")

    def _build_custom_form(self):
        f = self.form_fields_frame

        # 1. Hội viên
        tk.Label(f, text="Hội viên (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.cbo_hoi_vien = ttk.Combobox(f, state="readonly", font=FONT_BODY, style="Custom.TCombobox")
        self.cbo_hoi_vien.pack(fill="x", pady=(0, 8))

        # 2. Gói tập
        tk.Label(f, text="Gói tập (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.cbo_goi_tap = ttk.Combobox(f, state="readonly", font=FONT_BODY, style="Custom.TCombobox")
        self.cbo_goi_tap.pack(fill="x", pady=(0, 8))
        self.cbo_goi_tap.bind("<<ComboboxSelected>>", lambda e: self._on_package_or_date_changed())

        # 3. Huấn luyện viên
        tk.Label(f, text="Huấn luyện viên đi kèm:", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.cbo_hlv = ttk.Combobox(f, state="readonly", font=FONT_BODY, style="Custom.TCombobox")
        self.cbo_hlv.pack(fill="x", pady=(0, 8))

        # 4. Ngày đăng ký & Ngày bắt đầu
        row_dates = tk.Frame(f, bg=COLOR_CARD_BG)
        row_dates.pack(fill="x", pady=(0, 8))

        f_reg = tk.Frame(row_dates, bg=COLOR_CARD_BG)
        f_reg.pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Label(f_reg, text="Ngày ĐK (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(0, 2))
        if HAS_TKCALENDAR:
            self.txt_ngay_dang_ky = DateEntry(f_reg, date_pattern="yyyy-mm-dd", font=FONT_BODY, background="#FF5722", foreground="white")
        else:
            self.txt_ngay_dang_ky = ttk.Entry(f_reg, font=FONT_BODY, style="Custom.TEntry")
            self.txt_ngay_dang_ky.insert(0, date.today().strftime("%Y-%m-%d"))
        self.txt_ngay_dang_ky.pack(fill="x")

        f_start = tk.Frame(row_dates, bg=COLOR_CARD_BG)
        f_start.pack(side="right", fill="x", expand=True, padx=(4, 0))
        tk.Label(f_start, text="Ngày bắt đầu (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(0, 2))
        if HAS_TKCALENDAR:
            self.txt_ngay_bat_dau = DateEntry(f_start, date_pattern="yyyy-mm-dd", font=FONT_BODY, background="#FF5722", foreground="white")
            self.txt_ngay_bat_dau.bind("<<DateEntrySelected>>", lambda e: self._on_package_or_date_changed())
        else:
            self.txt_ngay_bat_dau = ttk.Entry(f_start, font=FONT_BODY, style="Custom.TEntry")
            self.txt_ngay_bat_dau.insert(0, date.today().strftime("%Y-%m-%d"))
            self.txt_ngay_bat_dau.bind("<KeyRelease>", lambda e: self._on_package_or_date_changed())
        self.txt_ngay_bat_dau.pack(fill="x")

        # 5. Ngày kết thúc (Tự động tính)
        tk.Label(f, text="Ngày kết thúc (Tự tính theo gói):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.txt_ngay_ket_thuc = ttk.Entry(f, font=FONT_BODY, state="readonly", style="Custom.TEntry")
        self.txt_ngay_ket_thuc.pack(fill="x", pady=(0, 8))

        # 6. Trạng thái (Tự động tính theo thời gian thực)
        tk.Label(f, text="Trạng thái (Tự tính theo thời gian thực):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.txt_trang_thai = ttk.Entry(f, font=FONT_BODY, state="readonly", style="Custom.TEntry")
        self.txt_trang_thai.pack(fill="x", pady=(0, 8))

    def _load_combobox_data(self):
        """Tải danh sách Hội viên, Gói tập, HLV vào Combobox."""
        # 1. Hội viên
        ok, hv_opts = database.get_hoi_vien_options()
        if ok:
            self.members_map = {lbl: mid for mid, lbl in hv_opts}
            self.cbo_hoi_vien["values"] = list(self.members_map.keys())

        # 2. HLV
        ok, hlv_opts = database.get_hlv_options(include_none=True)
        if ok:
            self.coaches_map = {lbl: cid for cid, lbl in hlv_opts}
            self.cbo_hlv["values"] = list(self.coaches_map.keys())
            if list(self.coaches_map.keys()):
                self.cbo_hlv.set(list(self.coaches_map.keys())[0])

        # 3. Gói tập
        ok, p_opts = database.get_goi_tap_options()
        if ok:
            self.packages_data = p_opts
            pkg_labels = [f"#{p['ma_goi']} - {p['ten_goi']} ({p['thoi_han']} tháng - {float(p['gia']):,.0f}đ)" for p in p_opts]
            self.cbo_goi_tap["values"] = pkg_labels

    def _get_selected_package(self) -> Optional[Dict[str, Any]]:
        idx = self.cbo_goi_tap.current()
        if 0 <= idx < len(self.packages_data):
            return self.packages_data[idx]
        return None

    def _on_package_or_date_changed(self):
        """Tính toán tự động ngày kết thúc khi chọn gói hoặc ngày bắt đầu."""
        pkg = self._get_selected_package()
        if not pkg:
            return

        start_val = self.txt_ngay_bat_dau.get_date() if HAS_TKCALENDAR else self.txt_ngay_bat_dau.get()
        ok, start_d, _ = parse_date(start_val)
        if not ok or not start_d:
            return

        duration = pkg["thoi_han"]
        end_d = calc_end_date(start_d, duration)

        self.txt_ngay_ket_thuc.config(state="normal")
        self.txt_ngay_ket_thuc.delete(0, tk.END)
        self.txt_ngay_ket_thuc.insert(0, str(end_d))
        self.txt_ngay_ket_thuc.config(state="readonly")

        # Gợi ý trạng thái
        status = compute_status(end_d)
        self.txt_trang_thai.config(state="normal")
        self.txt_trang_thai.delete(0, tk.END)
        self.txt_trang_thai.insert(0, status)
        self.txt_trang_thai.config(state="readonly")

    def _get_form_raw(self):
        hv_label = self.cbo_hoi_vien.get()
        hlv_label = self.cbo_hlv.get()
        pkg = self._get_selected_package()

        ma_hv = self.members_map.get(hv_label)
        ma_hlv = self.coaches_map.get(hlv_label)
        ma_goi = pkg["ma_goi"] if pkg else None
        thoi_han = pkg["thoi_han"] if pkg else None

        reg_val = self.txt_ngay_dang_ky.get_date() if HAS_TKCALENDAR else self.txt_ngay_dang_ky.get()
        start_val = self.txt_ngay_bat_dau.get_date() if HAS_TKCALENDAR else self.txt_ngay_bat_dau.get()

        return {
            "ma_hv": ma_hv,
            "ma_goi": ma_goi,
            "ma_hlv": ma_hlv,
            "thoi_han": thoi_han,
            "ngay_dang_ky": reg_val,
            "ngay_bat_dau": start_val,
            "trang_thai": self.txt_trang_thai.get()
        }

    def populate_form_from_selection(self, values: Tuple[Any, ...]):
        # ("ma_dk", "ten_hv", "sdt_hv", "ten_goi", "gia_goi", "ten_hlv", "ngay_dang_ky", "ngay_bat_dau", "ngay_ket_thuc", "trang_thai")
        self._load_combobox_data()

        # Chọn lại hội viên
        ten_hv = values[1]
        for lbl in self.cbo_hoi_vien["values"]:
            if ten_hv in lbl:
                self.cbo_hoi_vien.set(lbl)
                break

        # Chọn lại gói tập
        ten_goi = values[3]
        for lbl in self.cbo_goi_tap["values"]:
            if ten_goi in lbl:
                self.cbo_goi_tap.set(lbl)
                break

        # Chọn lại HLV
        ten_hlv = values[5]
        for lbl in self.cbo_hlv["values"]:
            if ten_hlv in lbl or (ten_hlv == "Không có" and "Không thuê" in lbl):
                self.cbo_hlv.set(lbl)
                break

        # Ngày ĐK & Ngày bắt đầu
        _, reg_d, _ = parse_date(values[6])
        if reg_d:
            if HAS_TKCALENDAR:
                self.txt_ngay_dang_ky.set_date(reg_d)
            else:
                self.txt_ngay_dang_ky.delete(0, tk.END)
                self.txt_ngay_dang_ky.insert(0, str(reg_d))

        _, start_d, _ = parse_date(values[7])
        if start_d:
            if HAS_TKCALENDAR:
                self.txt_ngay_bat_dau.set_date(start_d)
            else:
                self.txt_ngay_bat_dau.delete(0, tk.END)
                self.txt_ngay_bat_dau.insert(0, str(start_d))

        # Ngày kết thúc
        self.txt_ngay_ket_thuc.config(state="normal")
        self.txt_ngay_ket_thuc.delete(0, tk.END)
        self.txt_ngay_ket_thuc.insert(0, values[8])
        self.txt_ngay_ket_thuc.config(state="readonly")

        self.txt_trang_thai.config(state="normal")
        self.txt_trang_thai.delete(0, tk.END)
        self.txt_trang_thai.insert(0, values[9])
        self.txt_trang_thai.config(state="readonly")

    def clear_form(self):
        super().clear_form()
        self._load_combobox_data()
        self.cbo_hoi_vien.set("")
        self.cbo_goi_tap.set("")
        if list(self.coaches_map.keys()):
            self.cbo_hlv.set(list(self.coaches_map.keys())[0])

        today = date.today()
        if HAS_TKCALENDAR:
            self.txt_ngay_dang_ky.set_date(today)
            self.txt_ngay_bat_dau.set_date(today)
        else:
            self.txt_ngay_dang_ky.delete(0, tk.END)
            self.txt_ngay_dang_ky.insert(0, today.strftime("%Y-%m-%d"))
            self.txt_ngay_bat_dau.delete(0, tk.END)
            self.txt_ngay_bat_dau.insert(0, today.strftime("%Y-%m-%d"))

        self.txt_ngay_ket_thuc.config(state="normal")
        self.txt_ngay_ket_thuc.delete(0, tk.END)
        self.txt_ngay_ket_thuc.config(state="readonly")

        self.txt_trang_thai.config(state="normal")
        self.txt_trang_thai.delete(0, tk.END)
        self.txt_trang_thai.insert(0, "Đang hoạt động")
        self.txt_trang_thai.config(state="readonly")

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        ok, rows = database.get_all_dang_ky()
        if not ok:
            self.show_error(f"Không thể tải danh sách đăng ký: {rows}")
            return

        for r in rows:
            tag = "active_tag" if r["trang_thai"] == "Đang hoạt động" else "expired_tag"
            self.tree.insert(
                "",
                "end",
                values=(
                    r["ma_dk"],
                    r["ten_hv"],
                    r["sdt_hv"],
                    r["ten_goi"],
                    f"{float(r['gia_goi']):,.0f} đ",
                    r["ten_hlv"],
                    str(r["ngay_dang_ky"]),
                    str(r["ngay_bat_dau"]),
                    str(r["ngay_ket_thuc"]),
                    r["trang_thai"]
                ),
                tags=(tag,)
            )
        self.update_record_count(len(rows))

    def on_search(self):
        kw = self.txt_search.get().strip()
        if not kw:
            self.load_data()
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        ok, rows = database.search_dang_ky(kw)
        if not ok:
            self.show_error(f"Lỗi tìm kiếm: {rows}")
            return

        for r in rows:
            tag = "active_tag" if r["trang_thai"] == "Đang hoạt động" else "expired_tag"
            self.tree.insert(
                "",
                "end",
                values=(
                    r["ma_dk"],
                    r["ten_hv"],
                    r["sdt_hv"],
                    r["ten_goi"],
                    f"{float(r['gia_goi']):,.0f} đ",
                    r["ten_hlv"],
                    str(r["ngay_dang_ky"]),
                    str(r["ngay_bat_dau"]),
                    str(r["ngay_ket_thuc"]),
                    r["trang_thai"]
                ),
                tags=(tag,)
            )
        self.update_record_count(len(rows), f"Kết quả cho: '{kw}'")

    def _check_overlap(self, clean: Dict[str, Any], current_ma_dk: Optional[int] = None):
        """Logic Agent: một hội viên không có 2 gói đang hoạt động chồng thời gian."""
        if clean["trang_thai"] != "Đang hoạt động":
            return True, None
        db_ok, regs = database.get_active_dang_ky_of_hv(clean["ma_hv"], exclude_ma_dk=current_ma_dk)
        if not db_ok:
            return False, f"Không thể kiểm tra gói hiện có: {regs}"
        has_overlap, msg = find_registration_overlap(
            clean["ngay_bat_dau"], clean["ngay_ket_thuc"], regs
        )
        return (not has_overlap), msg

    def on_add(self):
        raw = self._get_form_raw()
        ok, clean, err = validate_dang_ky_form(raw)
        if not ok:
            self.show_error(err)
            return

        biz_ok, biz_err = self._check_overlap(clean)
        if not biz_ok:
            self.show_error(biz_err, title="Trùng thời gian gói tập")
            return

        db_ok, res = database.insert_dang_ky(clean)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Đăng ký gói tập thành công!")
        self.clear_form()
        self.load_data()

    def on_update(self):
        if not self.selected_item_id:
            self.show_error("Vui lòng chọn một đăng ký trong danh sách để cập nhật.")
            return

        raw = self._get_form_raw()
        ok, clean, err = validate_dang_ky_form(raw)
        if not ok:
            self.show_error(err)
            return

        biz_ok, biz_err = self._check_overlap(clean, current_ma_dk=int(self.selected_item_id))
        if not biz_ok:
            self.show_error(biz_err, title="Trùng thời gian gói tập")
            return

        db_ok, res = database.update_dang_ky(int(self.selected_item_id), clean)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Cập nhật thông tin đăng ký thành công!")
        self.clear_form()
        self.load_data()

    def on_delete(self):
        if not self.selected_item_id:
            self.show_error("Vui lòng chọn một đăng ký trong danh sách để xóa.")
            return

        if not self.ask_confirm(f"Bạn có chắc chắn muốn xóa đăng ký mã #{self.selected_item_id} không?"):
            return

        db_ok, res = database.delete_dang_ky(int(self.selected_item_id))
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Đã xóa đăng ký thành công!")
        self.clear_form()
        self.load_data()
