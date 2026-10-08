# ==========================================
# PHÂN HỆ QUẢN LÝ GÓI TẬP (PACKAGE VIEW)
# ==========================================
"""
Quản lý các gói tập gym (thời hạn, đơn giá, quyền lợi).
Hỗ trợ chế độ readonly đối với vai trò 'Nhân viên'.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Tuple
import database
from utils.validators import validate_goi_tap_form
from views.base_crud import BaseCrudView
from views.styles import (
    COLOR_CARD_BG, COLOR_TEXT_MAIN, FONT_BODY, FONT_BODY_BOLD
)


class GoiTapView(BaseCrudView):
    def __init__(self, parent: tk.Widget, readonly: bool = False):
        super().__init__(
            parent=parent,
            title="Quản Lý Gói Tập",
            subtitle="Cấu hình các gói dịch vụ tập luyện và bảng giá",
            readonly=readonly
        )
        self._setup_columns()
        self._build_custom_form()
        self.load_data()

    def _setup_columns(self):
        columns = ("ma_goi", "ten_goi", "thoi_han", "gia", "mo_ta")
        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        col_configs = [
            ("ma_goi", "Mã Gói", 80, "center"),
            ("ten_goi", "Tên gói tập", 180, "w"),
            ("thoi_han", "Thời hạn", 100, "center"),
            ("gia", "Giá niêm yết (VNĐ)", 150, "e"),
            ("mo_ta", "Mô tả / Quyền lợi", 280, "w"),
        ]

        for col, heading, width, anchor in col_configs:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=anchor)

    def _build_custom_form(self):
        f = self.form_fields_frame

        # Tên gói
        tk.Label(f, text="Tên gói tập (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.txt_ten_goi = ttk.Entry(f, font=FONT_BODY, style="Custom.TEntry")
        self.txt_ten_goi.pack(fill="x", pady=(0, 8))

        # Thời hạn (tháng)
        tk.Label(f, text="Thời hạn tính theo tháng (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.cbo_thoi_han = ttk.Combobox(f, values=["1", "2", "3", "6", "12", "24", "36"], font=FONT_BODY, style="Custom.TCombobox")
        self.cbo_thoi_han.set("1")
        self.cbo_thoi_han.pack(fill="x", pady=(0, 8))

        # Đơn giá
        tk.Label(f, text="Đơn giá (VNĐ) (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.txt_gia = ttk.Entry(f, font=FONT_BODY, style="Custom.TEntry")
        self.txt_gia.pack(fill="x", pady=(0, 8))

        # Mô tả
        tk.Label(f, text="Mô tả quyền lợi:", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.txt_mo_ta = tk.Text(f, height=5, font=FONT_BODY, relief="solid", bd=1)
        self.txt_mo_ta.pack(fill="x", pady=(0, 8))

    def _get_form_raw(self):
        return {
            "ten_goi": self.txt_ten_goi.get(),
            "thoi_han": self.cbo_thoi_han.get(),
            "gia": self.txt_gia.get(),
            "mo_ta": self.txt_mo_ta.get("1.0", tk.END).strip()
        }

    def populate_form_from_selection(self, values: Tuple[Any, ...]):
        # ("ma_goi", "ten_goi", "thoi_han", "gia", "mo_ta")
        self.txt_ten_goi.delete(0, tk.END)
        self.txt_ten_goi.insert(0, values[1])

        # Thời hạn tách số ra
        thoi_han_raw = str(values[2]).replace(" tháng", "").strip()
        self.cbo_thoi_han.set(thoi_han_raw)

        # Đơn giá loại bỏ ký tự định dạng
        gia_raw = str(values[3]).replace(",", "").replace(".", "").replace(" đ", "").replace(" VNĐ", "").strip()
        self.txt_gia.delete(0, tk.END)
        self.txt_gia.insert(0, gia_raw)

        self.txt_mo_ta.delete("1.0", tk.END)
        if values[4] and values[4] != "None":
            self.txt_mo_ta.insert(tk.END, values[4])

    def clear_form(self):
        super().clear_form()
        self.txt_ten_goi.delete(0, tk.END)
        self.cbo_thoi_han.set("1")
        self.txt_gia.delete(0, tk.END)
        self.txt_mo_ta.delete("1.0", tk.END)

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        ok, rows = database.get_all_goi_tap()
        if not ok:
            self.show_error(f"Không thể tải danh sách gói tập: {rows}")
            return

        for r in rows:
            gia_formatted = f"{float(r['gia']):,.0f} đ"
            self.tree.insert(
                "",
                "end",
                values=(
                    r["ma_goi"],
                    r["ten_goi"],
                    f"{r['thoi_han']} tháng",
                    gia_formatted,
                    r["mo_ta"] or ""
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

        ok, rows = database.search_goi_tap(kw)
        if not ok:
            self.show_error(f"Lỗi tìm kiếm: {rows}")
            return

        for r in rows:
            gia_formatted = f"{float(r['gia']):,.0f} đ"
            self.tree.insert(
                "",
                "end",
                values=(
                    r["ma_goi"],
                    r["ten_goi"],
                    f"{r['thoi_han']} tháng",
                    gia_formatted,
                    r["mo_ta"] or ""
                )
            )
        self.update_record_count(len(rows), f"Kết quả cho: '{kw}'")

    def on_add(self):
        raw = self._get_form_raw()
        ok, clean, err = validate_goi_tap_form(raw)
        if not ok:
            self.show_error(err)
            return

        db_ok, res = database.insert_goi_tap(clean)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Thêm mới gói tập thành công!")
        self.clear_form()
        self.load_data()

    def on_update(self):
        if not self.selected_item_id:
            self.show_error("Vui lòng chọn một gói tập trong danh sách để cập nhật.")
            return

        raw = self._get_form_raw()
        ok, clean, err = validate_goi_tap_form(raw)
        if not ok:
            self.show_error(err)
            return

        db_ok, res = database.update_goi_tap(int(self.selected_item_id), clean)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Cập nhật thông tin gói tập thành công!")
        self.clear_form()
        self.load_data()

    def on_delete(self):
        if not self.selected_item_id:
            self.show_error("Vui lòng chọn một gói tập trong danh sách để xóa.")
            return

        ten_goi = self.txt_ten_goi.get().strip() or f"Mã #{self.selected_item_id}"
        if not self.ask_confirm(f"Bạn có chắc chắn muốn xóa gói tập '{ten_goi}' không?"):
            return

        db_ok, res = database.delete_goi_tap(int(self.selected_item_id))
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Đã xóa gói tập thành công!")
        self.clear_form()
        self.load_data()
