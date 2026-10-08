# ==========================================
# PHÂN HỆ QUẢN LÝ HUẤN LUYỆN VIÊN (COACH VIEW)
# ==========================================
"""
Quản lý danh sách huấn luyện viên (HLV).
Hỗ trợ chế độ readonly đối với vai trò 'Nhân viên'.
"""

import tkinter as tk
from tkinter import ttk
from datetime import date
from typing import Any, Tuple

try:
    from tkcalendar import DateEntry
    HAS_TKCALENDAR = True
except ImportError:
    HAS_TKCALENDAR = False

import database
from utils.validators import validate_hlv_form, parse_date
from views.base_crud import BaseCrudView
from views.styles import (
    COLOR_CARD_BG, COLOR_TEXT_MAIN, FONT_BODY, FONT_BODY_BOLD
)


class HuanLuyenVienView(BaseCrudView):
    def __init__(self, parent: tk.Widget, readonly: bool = False):
        super().__init__(
            parent=parent,
            title="Quản Lý Huấn Luyện Viên",
            subtitle="Đội ngũ huấn luyện viên và chuyên môn đào tạo",
            readonly=readonly
        )
        self._setup_columns()
        self._build_custom_form()
        self.load_data()

    def _setup_columns(self):
        columns = ("ma_hlv", "ho_ten", "ngay_sinh", "gioi_tinh", "so_dien_thoai", "chuyen_mon")
        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        col_configs = [
            ("ma_hlv", "Mã HLV", 80, "center"),
            ("ho_ten", "Họ và tên", 180, "w"),
            ("ngay_sinh", "Ngày sinh", 110, "center"),
            ("gioi_tinh", "Giới tính", 90, "center"),
            ("so_dien_thoai", "Số điện thoại", 130, "center"),
            ("chuyen_mon", "Chuyên môn đào tạo", 220, "w"),
        ]

        for col, heading, width, anchor in col_configs:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=anchor)

    def _build_custom_form(self):
        f = self.form_fields_frame

        # Họ và tên
        tk.Label(f, text="Họ và tên HLV (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.txt_ho_ten = ttk.Entry(f, font=FONT_BODY, style="Custom.TEntry")
        self.txt_ho_ten.pack(fill="x", pady=(0, 8))

        # Ngày sinh & Giới tính
        row_dob_sex = tk.Frame(f, bg=COLOR_CARD_BG)
        row_dob_sex.pack(fill="x", pady=(0, 8))

        f_dob = tk.Frame(row_dob_sex, bg=COLOR_CARD_BG)
        f_dob.pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Label(f_dob, text="Ngày sinh (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(0, 2))
        if HAS_TKCALENDAR:
            self.txt_ngay_sinh = DateEntry(f_dob, date_pattern="yyyy-mm-dd", font=FONT_BODY, background="#FF5722", foreground="white")
        else:
            self.txt_ngay_sinh = ttk.Entry(f_dob, font=FONT_BODY, style="Custom.TEntry")
        self.txt_ngay_sinh.pack(fill="x")

        f_sex = tk.Frame(row_dob_sex, bg=COLOR_CARD_BG)
        f_sex.pack(side="right", fill="x", expand=True, padx=(4, 0))
        tk.Label(f_sex, text="Giới tính (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(0, 2))
        self.cbo_gioi_tinh = ttk.Combobox(f_sex, values=["Nam", "Nữ", "Khác"], state="readonly", style="Custom.TCombobox")
        self.cbo_gioi_tinh.set("Nam")
        self.cbo_gioi_tinh.pack(fill="x")

        # Số điện thoại
        tk.Label(f, text="Số điện thoại (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.txt_sdt = ttk.Entry(f, font=FONT_BODY, style="Custom.TEntry")
        self.txt_sdt.pack(fill="x", pady=(0, 8))

        # Chuyên môn
        tk.Label(f, text="Chuyên môn đào tạo (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        specialties = [
            "Thể hình (Bodybuilding)",
            "Yoga & Pilates",
            "Giảm cân (Cardio)",
            "Phục hồi chấn thương",
            "Zumba & Nhảy",
            "Boxing / Kickboxing",
            "Tập luyện cơ bản"
        ]
        self.cbo_chuyen_mon = ttk.Combobox(f, values=specialties, font=FONT_BODY, style="Custom.TCombobox")
        self.cbo_chuyen_mon.set(specialties[0])
        self.cbo_chuyen_mon.pack(fill="x", pady=(0, 8))

    def _get_form_raw(self):
        dob_val = self.txt_ngay_sinh.get_date() if HAS_TKCALENDAR else self.txt_ngay_sinh.get()
        return {
            "ho_ten": self.txt_ho_ten.get(),
            "ngay_sinh": dob_val,
            "gioi_tinh": self.cbo_gioi_tinh.get(),
            "so_dien_thoai": self.txt_sdt.get(),
            "chuyen_mon": self.cbo_chuyen_mon.get()
        }

    def populate_form_from_selection(self, values: Tuple[Any, ...]):
        # ("ma_hlv", "ho_ten", "ngay_sinh", "gioi_tinh", "so_dien_thoai", "chuyen_mon")
        self.txt_ho_ten.delete(0, tk.END)
        self.txt_ho_ten.insert(0, values[1])

        _, dob, _ = parse_date(values[2])
        if dob:
            if HAS_TKCALENDAR:
                self.txt_ngay_sinh.set_date(dob)
            else:
                self.txt_ngay_sinh.delete(0, tk.END)
                self.txt_ngay_sinh.insert(0, str(dob))

        self.cbo_gioi_tinh.set(values[3])

        self.txt_sdt.delete(0, tk.END)
        self.txt_sdt.insert(0, values[4])

        self.cbo_chuyen_mon.set(values[5])

    def clear_form(self):
        super().clear_form()
        self.txt_ho_ten.delete(0, tk.END)
        self.txt_sdt.delete(0, tk.END)
        self.cbo_gioi_tinh.set("Nam")
        self.cbo_chuyen_mon.set("Thể hình (Bodybuilding)")

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        ok, rows = database.get_all_hlv()
        if not ok:
            self.show_error(f"Không thể tải danh sách HLV: {rows}")
            return

        for r in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    r["ma_hlv"],
                    r["ho_ten"],
                    str(r["ngay_sinh"]),
                    r["gioi_tinh"],
                    r["so_dien_thoai"],
                    r["chuyen_mon"]
                )
            )
        self.update_record_count(len(rows))

    def on_search(self):
        kw = self.txt_search.get().strip()
        if not kw:
            self.load_data()
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        ok, rows = database.search_hlv(kw)
        if not ok:
            self.show_error(f"Lỗi tìm kiếm: {rows}")
            return

        for r in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    r["ma_hlv"],
                    r["ho_ten"],
                    str(r["ngay_sinh"]),
                    r["gioi_tinh"],
                    r["so_dien_thoai"],
                    r["chuyen_mon"]
                )
            )
        self.update_record_count(len(rows), f"Kết quả cho: '{kw}'")

    def on_add(self):
        raw = self._get_form_raw()
        ok, clean, err = validate_hlv_form(raw)
        if not ok:
            self.show_error(err)
            return

        db_ok, res = database.insert_hlv(clean)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Thêm mới huấn luyện viên thành công!")
        self.clear_form()
        self.load_data()

    def on_update(self):
        if not self.selected_item_id:
            self.show_error("Vui lòng chọn một HLV trong danh sách để cập nhật.")
            return

        raw = self._get_form_raw()
        ok, clean, err = validate_hlv_form(raw)
        if not ok:
            self.show_error(err)
            return

        db_ok, res = database.update_hlv(int(self.selected_item_id), clean)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Cập nhật thông tin HLV thành công!")
        self.clear_form()
        self.load_data()

    def on_delete(self):
        if not self.selected_item_id:
            self.show_error("Vui lòng chọn một HLV trong danh sách để xóa.")
            return

        ho_ten = self.txt_ho_ten.get().strip() or f"Mã #{self.selected_item_id}"
        if not self.ask_confirm(f"Bạn có chắc chắn muốn xóa HLV '{ho_ten}' không?"):
            return

        db_ok, res = database.delete_hlv(int(self.selected_item_id))
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Đã xóa huấn luyện viên thành công!")
        self.clear_form()
        self.load_data()
