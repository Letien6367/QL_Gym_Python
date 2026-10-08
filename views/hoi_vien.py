# ==========================================
# PHÂN HỆ QUẢN LÝ HỘI VIÊN (MEMBER VIEW)
# ==========================================
"""
Quản lý danh sách hội viên phòng gym.
Tuân thủ kiến trúc đa đại lý:
- Thu thập dữ liệu giao diện
- Chuyển qua Logic Agent (validators) để kiểm tra hợp lệ
- Chuyển dữ liệu sạch xuống Database Agent (database)
- Hiển thị kết quả lên Treeview
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
from utils.validators import validate_hoi_vien_form, parse_date
from views.base_crud import BaseCrudView
from views.styles import (
    COLOR_CARD_BG, COLOR_TEXT_MAIN, FONT_BODY, FONT_BODY_BOLD
)


class HoiVienView(BaseCrudView):
    def __init__(self, parent: tk.Widget, readonly: bool = False):
        super().__init__(
            parent=parent,
            title="Quản Lý Hội Viên",
            subtitle="Danh sách và thông tin hồ sơ khách hàng phòng gym",
            readonly=readonly
        )
        self._setup_columns()
        self._build_custom_form()
        self.load_data()

    def _setup_columns(self):
        columns = ("ma_hv", "ho_ten", "ngay_sinh", "gioi_tinh", "so_dien_thoai", "email", "dia_chi", "ngay_tham_gia")
        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        col_configs = [
            ("ma_hv", "Mã HV", 70, "center"),
            ("ho_ten", "Họ và tên", 160, "w"),
            ("ngay_sinh", "Ngày sinh", 100, "center"),
            ("gioi_tinh", "Giới tính", 80, "center"),
            ("so_dien_thoai", "Số điện thoại", 110, "center"),
            ("email", "Email", 160, "w"),
            ("dia_chi", "Địa chỉ", 180, "w"),
            ("ngay_tham_gia", "Ngày tham gia", 110, "center"),
        ]

        for col, heading, width, anchor in col_configs:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=anchor)

    def _build_custom_form(self):
        f = self.form_fields_frame

        # Họ và tên
        tk.Label(f, text="Họ và tên (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
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

        # Email
        tk.Label(f, text="Email:", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.txt_email = ttk.Entry(f, font=FONT_BODY, style="Custom.TEntry")
        self.txt_email.pack(fill="x", pady=(0, 8))

        # Địa chỉ
        tk.Label(f, text="Địa chỉ:", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.txt_dia_chi = ttk.Entry(f, font=FONT_BODY, style="Custom.TEntry")
        self.txt_dia_chi.pack(fill="x", pady=(0, 8))

        # Ngày tham gia
        tk.Label(f, text="Ngày tham gia (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        if HAS_TKCALENDAR:
            self.txt_ngay_tham_gia = DateEntry(f, date_pattern="yyyy-mm-dd", font=FONT_BODY, background="#FF5722", foreground="white")
        else:
            self.txt_ngay_tham_gia = ttk.Entry(f, font=FONT_BODY, style="Custom.TEntry")
            self.txt_ngay_tham_gia.insert(0, date.today().strftime("%Y-%m-%d"))
        self.txt_ngay_tham_gia.pack(fill="x", pady=(0, 8))

    def _get_form_raw(self):
        dob_val = self.txt_ngay_sinh.get_date() if HAS_TKCALENDAR else self.txt_ngay_sinh.get()
        join_val = self.txt_ngay_tham_gia.get_date() if HAS_TKCALENDAR else self.txt_ngay_tham_gia.get()

        return {
            "ho_ten": self.txt_ho_ten.get(),
            "ngay_sinh": dob_val,
            "gioi_tinh": self.cbo_gioi_tinh.get(),
            "so_dien_thoai": self.txt_sdt.get(),
            "email": self.txt_email.get(),
            "dia_chi": self.txt_dia_chi.get(),
            "ngay_tham_gia": join_val
        }

    def populate_form_from_selection(self, values: Tuple[Any, ...]):
        # ("ma_hv", "ho_ten", "ngay_sinh", "gioi_tinh", "so_dien_thoai", "email", "dia_chi", "ngay_tham_gia")
        self.txt_ho_ten.delete(0, tk.END)
        self.txt_ho_ten.insert(0, values[1])

        # Ngày sinh
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

        self.txt_email.delete(0, tk.END)
        self.txt_email.insert(0, values[5] if values[5] and values[5] != "None" else "")

        self.txt_dia_chi.delete(0, tk.END)
        self.txt_dia_chi.insert(0, values[6] if values[6] and values[6] != "None" else "")

        # Ngày tham gia
        _, join_d, _ = parse_date(values[7])
        if join_d:
            if HAS_TKCALENDAR:
                self.txt_ngay_tham_gia.set_date(join_d)
            else:
                self.txt_ngay_tham_gia.delete(0, tk.END)
                self.txt_ngay_tham_gia.insert(0, str(join_d))

    def clear_form(self):
        super().clear_form()
        self.txt_ho_ten.delete(0, tk.END)
        self.txt_sdt.delete(0, tk.END)
        self.txt_email.delete(0, tk.END)
        self.txt_dia_chi.delete(0, tk.END)
        self.cbo_gioi_tinh.set("Nam")

        today = date.today()
        if HAS_TKCALENDAR:
            self.txt_ngay_tham_gia.set_date(today)
        else:
            self.txt_ngay_tham_gia.delete(0, tk.END)
            self.txt_ngay_tham_gia.insert(0, today.strftime("%Y-%m-%d"))

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        ok, rows = database.get_all_hoi_vien()
        if not ok:
            self.show_error(f"Không thể tải danh sách hội viên: {rows}")
            return

        for r in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    r["ma_hv"],
                    r["ho_ten"],
                    str(r["ngay_sinh"]),
                    r["gioi_tinh"],
                    r["so_dien_thoai"],
                    r["email"] or "",
                    r["dia_chi"] or "",
                    str(r["ngay_tham_gia"])
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

        ok, rows = database.search_hoi_vien(kw)
        if not ok:
            self.show_error(f"Lỗi tìm kiếm: {rows}")
            return

        for r in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    r["ma_hv"],
                    r["ho_ten"],
                    str(r["ngay_sinh"]),
                    r["gioi_tinh"],
                    r["so_dien_thoai"],
                    r["email"] or "",
                    r["dia_chi"] or "",
                    str(r["ngay_tham_gia"])
                )
            )
        self.update_record_count(len(rows), f"Kết quả cho: '{kw}'")

    def on_add(self):
        raw = self._get_form_raw()
        # 1. Logic Agent kiểm duyệt
        ok, clean, err = validate_hoi_vien_form(raw)
        if not ok:
            self.show_error(err)
            return

        # 2. Database Agent thực thi
        db_ok, res = database.insert_hoi_vien(clean)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Thêm mới hội viên thành công!")
        self.clear_form()
        self.load_data()

    def on_update(self):
        if not self.selected_item_id:
            self.show_error("Vui lòng chọn một hội viên trong danh sách để cập nhật.")
            return

        raw = self._get_form_raw()
        # 1. Logic Agent kiểm duyệt
        ok, clean, err = validate_hoi_vien_form(raw)
        if not ok:
            self.show_error(err)
            return

        # 2. Database Agent thực thi
        db_ok, res = database.update_hoi_vien(int(self.selected_item_id), clean)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Cập nhật thông tin hội viên thành công!")
        self.clear_form()
        self.load_data()

    def on_delete(self):
        if not self.selected_item_id:
            self.show_error("Vui lòng chọn một hội viên trong danh sách để xóa.")
            return

        ho_ten = self.txt_ho_ten.get().strip() or f"Mã #{self.selected_item_id}"
        if not self.ask_confirm(f"Bạn có chắc chắn muốn xóa hội viên '{ho_ten}' không?"):
            return

        db_ok, res = database.delete_hoi_vien(int(self.selected_item_id))
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Đã xóa hội viên thành công!")
        self.clear_form()
        self.load_data()
