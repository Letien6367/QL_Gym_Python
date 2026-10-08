# ==========================================
# PHÂN HỆ QUẢN LÝ THANH TOÁN (PAYMENT VIEW)
# ==========================================
"""
Quản lý các hóa đơn / giao dịch thanh toán gói tập.
- Tự động điền số tiền theo giá gói khi chọn mã đăng ký
- Thống kê tổng số tiền các giao dịch đang hiển thị
- Kiểm tra tính hợp lệ qua Logic Agent
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
from utils.validators import validate_thanh_toan_form, parse_date
from views.base_crud import BaseCrudView
from views.styles import (
    COLOR_CARD_BG, COLOR_CONTENT_BG, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL
)


class ThanhToanView(BaseCrudView):
    def __init__(self, parent: tk.Widget, readonly: bool = False):
        super().__init__(
            parent=parent,
            title="Quản Lý Thanh Toán",
            subtitle="Hóa đơn thanh toán và dòng tiền phòng gym",
            readonly=readonly
        )
        self.dang_ky_data: List[Dict[str, Any]] = []
        self._setup_columns()
        self._build_custom_form()
        self._load_dang_ky_options()
        self.load_data()

    def _setup_columns(self):
        columns = ("ma_tt", "ma_dk", "ten_hv", "ten_goi", "so_tien", "ngay_thanh_toan", "phuong_thuc")
        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        col_configs = [
            ("ma_tt", "Mã HĐ", 70, "center"),
            ("ma_dk", "Mã ĐK", 70, "center"),
            ("ten_hv", "Hội viên thanh toán", 180, "w"),
            ("ten_goi", "Gói tập", 150, "w"),
            ("so_tien", "Số tiền (VNĐ)", 140, "e"),
            ("ngay_thanh_toan", "Ngày giao dịch", 120, "center"),
            ("phuong_thuc", "Phương thức", 140, "center"),
        ]

        for col, heading, width, anchor in col_configs:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=anchor)

    def _build_custom_form(self):
        f = self.form_fields_frame

        # Hợp đồng / Đăng ký
        tk.Label(f, text="Hợp đồng đăng ký (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.cbo_dang_ky = ttk.Combobox(f, state="readonly", font=FONT_BODY, style="Custom.TCombobox")
        self.cbo_dang_ky.pack(fill="x", pady=(0, 8))
        self.cbo_dang_ky.bind("<<ComboboxSelected>>", lambda e: self._on_dang_ky_selected())

        # Số tiền
        tk.Label(f, text="Số tiền thanh toán (VNĐ) (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.txt_so_tien = ttk.Entry(f, font=FONT_BODY, style="Custom.TEntry")
        self.txt_so_tien.pack(fill="x", pady=(0, 8))

        # Ngày thanh toán
        tk.Label(f, text="Ngày thanh toán (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        if HAS_TKCALENDAR:
            self.txt_ngay_tt = DateEntry(f, date_pattern="yyyy-mm-dd", font=FONT_BODY, background="#FF5722", foreground="white")
        else:
            self.txt_ngay_tt = ttk.Entry(f, font=FONT_BODY, style="Custom.TEntry")
            self.txt_ngay_tt.insert(0, date.today().strftime("%Y-%m-%d"))
        self.txt_ngay_tt.pack(fill="x", pady=(0, 8))

        # Phương thức thanh toán
        tk.Label(f, text="Phương thức (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.cbo_phuong_thuc = ttk.Combobox(
            f,
            values=["Tiền mặt", "Chuyển khoản", "Quẹt thẻ ngân hàng", "Ví điện tử"],
            state="readonly",
            font=FONT_BODY,
            style="Custom.TCombobox"
        )
        self.cbo_phuong_thuc.set("Tiền mặt")
        self.cbo_phuong_thuc.pack(fill="x", pady=(0, 8))

    def _load_dang_ky_options(self):
        ok, rows = database.get_dang_ky_options()
        if ok:
            self.dang_ky_data = rows
            opts = [f"ĐK #{r['ma_dk']} - {r['ten_hv']} - {r['ten_goi']} ({float(r['gia_goi']):,.0f}đ)" for r in rows]
            self.cbo_dang_ky["values"] = opts

    def _on_dang_ky_selected(self):
        idx = self.cbo_dang_ky.current()
        if 0 <= idx < len(self.dang_ky_data):
            item = self.dang_ky_data[idx]
            # Tự động điền số tiền theo giá gói
            self.txt_so_tien.delete(0, tk.END)
            self.txt_so_tien.insert(0, str(int(float(item["gia_goi"]))))

    def _get_form_raw(self):
        idx = self.cbo_dang_ky.current()
        ma_dk = self.dang_ky_data[idx]["ma_dk"] if 0 <= idx < len(self.dang_ky_data) else None

        pay_d = self.txt_ngay_tt.get_date() if HAS_TKCALENDAR else self.txt_ngay_tt.get()
        return {
            "ma_dk": ma_dk,
            "so_tien": self.txt_so_tien.get(),
            "ngay_thanh_toan": pay_d,
            "phuong_thuc": self.cbo_phuong_thuc.get()
        }

    def populate_form_from_selection(self, values: Tuple[Any, ...]):
        # ("ma_tt", "ma_dk", "ten_hv", "ten_goi", "so_tien", "ngay_thanh_toan", "phuong_thuc")
        self._load_dang_ky_options()
        ma_dk_target = int(values[1])

        for i, item in enumerate(self.dang_ky_data):
            if item["ma_dk"] == ma_dk_target:
                self.cbo_dang_ky.current(i)
                break

        so_tien_raw = str(values[4]).replace(",", "").replace(".", "").replace(" đ", "").replace(" VNĐ", "").strip()
        self.txt_so_tien.delete(0, tk.END)
        self.txt_so_tien.insert(0, so_tien_raw)

        _, pay_d, _ = parse_date(values[5])
        if pay_d:
            if HAS_TKCALENDAR:
                self.txt_ngay_tt.set_date(pay_d)
            else:
                self.txt_ngay_tt.delete(0, tk.END)
                self.txt_ngay_tt.insert(0, str(pay_d))

        self.cbo_phuong_thuc.set(values[6])

    def clear_form(self):
        super().clear_form()
        self._load_dang_ky_options()
        self.cbo_dang_ky.set("")
        self.txt_so_tien.delete(0, tk.END)
        self.cbo_phuong_thuc.set("Tiền mặt")

        today = date.today()
        if HAS_TKCALENDAR:
            self.txt_ngay_tt.set_date(today)
        else:
            self.txt_ngay_tt.delete(0, tk.END)
            self.txt_ngay_tt.insert(0, today.strftime("%Y-%m-%d"))

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        ok, rows = database.get_all_thanh_toan()
        if not ok:
            self.show_error(f"Không thể tải danh sách thanh toán: {rows}")
            return

        total_amount = 0.0
        for r in rows:
            amt = float(r["so_tien"])
            total_amount += amt
            self.tree.insert(
                "",
                "end",
                values=(
                    r["ma_tt"],
                    r["ma_dk"],
                    r["ten_hv"],
                    r["ten_goi"],
                    f"{amt:,.0f} đ",
                    str(r["ngay_thanh_toan"]),
                    r["phuong_thuc"]
                )
            )
        self.update_record_count(len(rows), f"Tổng doanh thu: {total_amount:,.0f} VNĐ")

    def on_search(self):
        kw = self.txt_search.get().strip()
        if not kw:
            self.load_data()
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        ok, rows = database.search_thanh_toan(kw)
        if not ok:
            self.show_error(f"Lỗi tìm kiếm: {rows}")
            return

        total_amount = 0.0
        for r in rows:
            amt = float(r["so_tien"])
            total_amount += amt
            self.tree.insert(
                "",
                "end",
                values=(
                    r["ma_tt"],
                    r["ma_dk"],
                    r["ten_hv"],
                    r["ten_goi"],
                    f"{amt:,.0f} đ",
                    str(r["ngay_thanh_toan"]),
                    r["phuong_thuc"]
                )
            )
        self.update_record_count(len(rows), f"Tổng tiền hiển thị: {total_amount:,.0f} VNĐ")

    def on_add(self):
        raw = self._get_form_raw()
        ok, clean, err = validate_thanh_toan_form(raw)
        if not ok:
            self.show_error(err)
            return

        db_ok, res = database.insert_thanh_toan(clean)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Lập phiếu thanh toán thành công!")
        self.clear_form()
        self.load_data()

    def on_update(self):
        if not self.selected_item_id:
            self.show_error("Vui lòng chọn một phiếu thanh toán để cập nhật.")
            return

        raw = self._get_form_raw()
        ok, clean, err = validate_thanh_toan_form(raw)
        if not ok:
            self.show_error(err)
            return

        db_ok, res = database.update_thanh_toan(int(self.selected_item_id), clean)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Cập nhật phiếu thanh toán thành công!")
        self.clear_form()
        self.load_data()

    def on_delete(self):
        if not self.selected_item_id:
            self.show_error("Vui lòng chọn một phiếu thanh toán để xóa.")
            return

        if not self.ask_confirm(f"Bạn có chắc chắn muốn xóa phiếu thanh toán #{self.selected_item_id} không?"):
            return

        db_ok, res = database.delete_thanh_toan(int(self.selected_item_id))
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Đã xóa phiếu thanh toán thành công!")
        self.clear_form()
        self.load_data()
