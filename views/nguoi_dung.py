# ==========================================
# PHÂN HỆ QUẢN LÝ NGƯỜI DÙNG (USER VIEW - ADMIN)
# ==========================================
"""
Quản lý tài khoản cán bộ nhân viên và quản trị viên hệ thống.
Chỉ tài khoản quyền Admin mới có thể truy cập phân hệ này.
Bao gồm:
- Thêm tài khoản mới (tự động băm SHA-256)
- Sửa thông tin nhân viên, phân quyền Admin / Nhân viên
- Khóa / Mở khóa tài khoản
- Đổi mật khẩu / Reset mật khẩu
- Chặn tự xóa hoặc tự khóa tài khoản đang đăng nhập
"""

import tkinter as tk
from tkinter import ttk, simpledialog
from typing import Any, Dict, Optional, Tuple
import database
from utils.validators import (
    validate_nguoi_dung_form, hash_password, validate_password_strength,
    check_admin_safeguard
)
from views.base_crud import BaseCrudView
from views.styles import (
    COLOR_CARD_BG, COLOR_CONTENT_BG, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL
)


class NguoiDungView(BaseCrudView):
    def __init__(self, parent: tk.Widget, current_user: Dict[str, Any]):
        self.current_user = current_user
        super().__init__(
            parent=parent,
            title="Quản Lý Người Dùng & Phân Quyền",
            subtitle="Quản lý tài khoản đăng nhập của nhân viên và quản trị viên (Admin Only)",
            readonly=False
        )
        self._setup_columns()
        self._build_custom_form()
        self.load_data()

    def _setup_columns(self):
        columns = ("ma_nd", "ten_dang_nhap", "ho_ten", "vai_tro", "trang_thai")
        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        col_configs = [
            ("ma_nd", "Mã ND", 80, "center"),
            ("ten_dang_nhap", "Tên đăng nhập", 160, "w"),
            ("ho_ten", "Họ và tên", 200, "w"),
            ("vai_tro", "Vai trò / Quyền", 140, "center"),
            ("trang_thai", "Trạng thái", 150, "center"),
        ]

        for col, heading, width, anchor in col_configs:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=anchor)

        self.tree.tag_configure("active_tag", foreground="#276749")
        self.tree.tag_configure("locked_tag", foreground="#9B2C2C")

    def _build_custom_form(self):
        f = self.form_fields_frame

        # Tên đăng nhập
        tk.Label(f, text="Tên đăng nhập (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.txt_username = ttk.Entry(f, font=FONT_BODY, style="Custom.TEntry")
        self.txt_username.pack(fill="x", pady=(0, 8))

        # Họ và tên
        tk.Label(f, text="Họ và tên nhân viên (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.txt_ho_ten = ttk.Entry(f, font=FONT_BODY, style="Custom.TEntry")
        self.txt_ho_ten.pack(fill="x", pady=(0, 8))

        # Mật khẩu (chỉ bắt buộc khi thêm mới)
        self.lbl_pwd = tk.Label(f, text="Mật khẩu khởi tạo (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG)
        self.lbl_pwd.pack(anchor="w", pady=(2, 2))
        self.txt_password = ttk.Entry(f, font=FONT_BODY, show="*", style="Custom.TEntry")
        self.txt_password.pack(fill="x", pady=(0, 8))

        # Vai trò
        tk.Label(f, text="Vai trò phân quyền (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.cbo_vai_tro = ttk.Combobox(f, values=["Nhân viên", "Admin"], state="readonly", font=FONT_BODY, style="Custom.TCombobox")
        self.cbo_vai_tro.set("Nhân viên")
        self.cbo_vai_tro.pack(fill="x", pady=(0, 8))

        # Trạng thái
        tk.Label(f, text="Trạng thái tài khoản:", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.cbo_trang_thai = ttk.Combobox(f, values=["Đang hoạt động", "Đã khóa"], state="readonly", font=FONT_BODY, style="Custom.TCombobox")
        self.cbo_trang_thai.set("Đang hoạt động")
        self.cbo_trang_thai.pack(fill="x", pady=(0, 8))

        # Nút Đặt lại mật khẩu bổ sung
        btn_reset = ttk.Button(
            self.btn_action_frame,
            text="🔑 Đặt lại mật khẩu",
            style="Neutral.TButton",
            command=self.on_reset_password
        )
        btn_reset.pack(fill="x", pady=2)

    def _get_form_raw(self, is_create: bool = True):
        return {
            "ten_dang_nhap": self.txt_username.get(),
            "ho_ten": self.txt_ho_ten.get(),
            "mat_khau": self.txt_password.get() if is_create else None,
            "vai_tro": self.cbo_vai_tro.get(),
            "trang_thai": self.cbo_trang_thai.get()
        }

    def populate_form_from_selection(self, values: Tuple[Any, ...]):
        # ("ma_nd", "ten_dang_nhap", "ho_ten", "vai_tro", "trang_thai")
        self.txt_username.delete(0, tk.END)
        self.txt_username.insert(0, values[1])
        # Không cho sửa tên đăng nhập của tài khoản đã tạo
        self.txt_username.config(state="disabled")

        self.txt_ho_ten.delete(0, tk.END)
        self.txt_ho_ten.insert(0, values[2])

        self.txt_password.delete(0, tk.END)
        self.txt_password.config(state="disabled")
        self.lbl_pwd.config(text="Mật khẩu (Dùng nút 'Đặt lại mật khẩu'):")

        self.cbo_vai_tro.set(values[3])
        self.cbo_trang_thai.set(values[4])

    def clear_form(self):
        super().clear_form()
        self.txt_username.config(state="normal")
        self.txt_username.delete(0, tk.END)

        self.txt_ho_ten.delete(0, tk.END)

        self.txt_password.config(state="normal")
        self.txt_password.delete(0, tk.END)
        self.lbl_pwd.config(text="Mật khẩu khởi tạo (*):")

        self.cbo_vai_tro.set("Nhân viên")
        self.cbo_trang_thai.set("Đang hoạt động")

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        ok, rows = database.get_all_nguoi_dung()
        if not ok:
            self.show_error(f"Không thể tải danh sách người dùng: {rows}")
            return

        for r in rows:
            tag = "active_tag" if r["trang_thai"] == "Đang hoạt động" else "locked_tag"
            self.tree.insert(
                "",
                "end",
                values=(
                    r["ma_nd"],
                    r["ten_dang_nhap"],
                    r["ho_ten"],
                    r["vai_tro"],
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

        ok, rows = database.search_nguoi_dung(kw)
        if not ok:
            self.show_error(f"Lỗi tìm kiếm: {rows}")
            return

        for r in rows:
            tag = "active_tag" if r["trang_thai"] == "Đang hoạt động" else "locked_tag"
            self.tree.insert(
                "",
                "end",
                values=(
                    r["ma_nd"],
                    r["ten_dang_nhap"],
                    r["ho_ten"],
                    r["vai_tro"],
                    r["trang_thai"]
                ),
                tags=(tag,)
            )
        self.update_record_count(len(rows), f"Kết quả cho: '{kw}'")

    def on_add(self):
        raw = self._get_form_raw(is_create=True)
        ok, clean, err = validate_nguoi_dung_form(raw, is_create=True)
        if not ok:
            self.show_error(err)
            return

        db_ok, res = database.insert_nguoi_dung(clean)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Thêm người dùng mới thành công!")
        self.clear_form()
        self.load_data()

    def _selected_row_values(self) -> Tuple[Any, ...]:
        sel = self.tree.selection()
        return self.tree.item(sel[0], "values") if sel else ()

    def _admin_safeguard(self, cur_id: int, new_role: str, new_status: str, is_delete: bool = False):
        """Logic Agent: không để hệ thống mất Admin hoạt động cuối cùng."""
        values = self._selected_row_values()
        if not values:
            return True, None
        target_is_active_admin = (values[3] == "Admin" and values[4] == "Đang hoạt động")
        db_ok, others = database.count_other_active_admins(cur_id)
        if not db_ok:
            return False, f"Không thể kiểm tra số lượng Admin: {others}"
        return check_admin_safeguard(target_is_active_admin, new_role, new_status, others, is_delete)

    def on_update(self):
        if not self.selected_item_id:
            self.show_error("Vui lòng chọn một người dùng trong bảng để cập nhật.")
            return

        cur_id = int(self.selected_item_id)
        if cur_id == self.current_user["ma_nd"]:
            # Không cho tự khoá hoặc tự đổi vai trò của chính mình
            if self.cbo_trang_thai.get() != "Đang hoạt động":
                self.show_error("Bạn không thể tự khóa tài khoản đang đăng nhập của chính mình!")
                return
            if self.cbo_vai_tro.get() != self.current_user.get("vai_tro"):
                self.show_error("Bạn không thể tự thay đổi vai trò của chính mình!")
                return

        safe_ok, safe_err = self._admin_safeguard(cur_id, self.cbo_vai_tro.get(), self.cbo_trang_thai.get())
        if not safe_ok:
            self.show_error(safe_err)
            return

        raw = self._get_form_raw(is_create=False)
        ok, clean, err = validate_nguoi_dung_form(raw, is_create=False)
        if not ok:
            self.show_error(err)
            return

        db_ok, res = database.update_nguoi_dung(cur_id, clean)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Cập nhật thông tin người dùng thành công!")
        self.clear_form()
        self.load_data()

    def on_delete(self):
        if not self.selected_item_id:
            self.show_error("Vui lòng chọn một người dùng để xóa.")
            return

        cur_id = int(self.selected_item_id)
        if cur_id == self.current_user["ma_nd"]:
            self.show_error("Bạn không thể tự xóa tài khoản đang đăng nhập của chính mình!")
            return

        username = self.txt_username.get().strip() or f"Mã #{cur_id}"
        safe_ok, safe_err = self._admin_safeguard(cur_id, "", "", is_delete=True)
        if not safe_ok:
            self.show_error(safe_err)
            return

        if not self.ask_confirm(f"Bạn có chắc chắn muốn xóa tài khoản '{username}' không?"):
            return

        db_ok, res = database.delete_nguoi_dung(cur_id)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Đã xóa tài khoản thành công!")
        self.clear_form()
        self.load_data()

    def on_reset_password(self):
        if not self.selected_item_id:
            self.show_error("Vui lòng chọn một người dùng trong bảng để đặt lại mật khẩu.")
            return

        cur_id = int(self.selected_item_id)
        username = self.txt_username.get().strip()

        new_pwd = simpledialog.askstring(
            "Đặt lại mật khẩu",
            f"Nhập mật khẩu mới cho tài khoản '{username}':",
            show="*",
            parent=self
        )
        if new_pwd is None:
            return

        ok, err = validate_password_strength(new_pwd)
        if not ok:
            self.show_error(err)
            return

        hashed = hash_password(new_pwd)
        db_ok, res = database.reset_user_password(cur_id, hashed)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info(f"Đã cập nhật mật khẩu mới cho tài khoản '{username}' thành công!")
