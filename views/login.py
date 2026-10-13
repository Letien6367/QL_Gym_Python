# ==========================================
# GIAO DIỆN ĐĂNG NHẬP (LOGIN VIEW)
# ==========================================
"""
Màn hình đăng nhập xác thực người dùng.
- Kiểm tra tính hợp lệ qua Logic Agent (validators)
- Truy vấn tài khoản từ Database Agent (database)
- Xác thực mật khẩu băm SHA-256
- Chặn tài khoản có trạng thái 'Đã khóa'
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Any, Optional
import database
from utils.validators import require_fields, verify_password
from views.styles import (
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_CARD_BG, COLOR_CONTENT_BG,
    COLOR_BORDER, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_DANGER,
    FONT_TITLE, FONT_SUBTITLE, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL
)


import time as std_time

class LoginView(tk.Frame):
    def __init__(self, parent: tk.Widget, on_login_success: Callable[[Dict[str, Any]], None]):
        super().__init__(parent, bg="#1A1D24")
        self.on_login_success = on_login_success
        self.show_password = False
        self.failed_attempts = 0
        self.lock_until: Optional[float] = None

        self._build_ui()

    def _build_ui(self):
        # Card đăng nhập căn giữa
        card = tk.Frame(
            self,
            bg=COLOR_CARD_BG,
            padx=36,
            pady=36,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1
        )
        card.place(relx=0.5, rely=0.5, anchor="center", width=420)

        # Logo / Tiêu đề thương hiệu
        lbl_logo = tk.Label(
            card,
            text="🏋️ GYMPRO",
            font=(FONT_TITLE[0], 22, "bold"),
            fg=COLOR_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_logo.pack(pady=(0, 4))

        lbl_sub = tk.Label(
            card,
            text="HỆ THỐNG QUẢN LÝ PHÒNG GYM CHUYÊN NGHIỆP",
            font=(FONT_BODY[0], 8, "bold"),
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CARD_BG
        )
        lbl_sub.pack(pady=(0, 24))

        # Ô nhập Tên đăng nhập
        tk.Label(
            card,
            text="Tên đăng nhập:",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_MAIN,
            bg=COLOR_CARD_BG
        ).pack(anchor="w", pady=(0, 4))

        self.txt_username = ttk.Entry(card, font=FONT_BODY, style="Custom.TEntry")
        self.txt_username.pack(fill="x", pady=(0, 14))
        self.txt_username.focus_set()
        self.txt_username.bind("<Return>", lambda e: self.txt_password.focus_set())

        # Ô nhập Mật khẩu
        tk.Label(
            card,
            text="Mật khẩu:",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_MAIN,
            bg=COLOR_CARD_BG
        ).pack(anchor="w", pady=(0, 4))

        pw_frame = tk.Frame(card, bg=COLOR_CARD_BG)
        pw_frame.pack(fill="x", pady=(0, 8))

        self.txt_password = ttk.Entry(pw_frame, font=FONT_BODY, show="*", style="Custom.TEntry")
        self.txt_password.pack(side="left", fill="x", expand=True)
        self.txt_password.bind("<Return>", lambda e: self.handle_login())

        self.btn_eye = tk.Button(
            pw_frame,
            text="👁️",
            font=FONT_BODY,
            bd=0,
            bg="#EDF2F7",
            activebackground="#E2E8F0",
            cursor="hand2",
            padx=8,
            command=self.toggle_password_visibility
        )
        self.btn_eye.pack(side="right", padx=(4, 0))

        # Nhãn hiển thị thông báo lỗi
        self.lbl_error = tk.Label(
            card,
            text="",
            font=FONT_SMALL,
            fg=COLOR_DANGER,
            bg=COLOR_CARD_BG,
            wraplength=340,
            justify="center"
        )
        self.lbl_error.pack(fill="x", pady=(4, 10))

        # Nút Đăng nhập
        btn_login = tk.Button(
            card,
            text="ĐĂNG NHẬP",
            font=FONT_BODY_BOLD,
            fg="#FFFFFF",
            bg=COLOR_PRIMARY,
            activebackground=COLOR_PRIMARY_HOVER,
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            pady=10,
            command=self.handle_login
        )
        btn_login.pack(fill="x", pady=(4, 12))


    def toggle_password_visibility(self):
        """Bật/tắt ẩn hiện mật khẩu."""
        self.show_password = not self.show_password
        self.txt_password.config(show="" if self.show_password else "*")
        self.btn_eye.config(text="🙈" if self.show_password else "👁️")

    def handle_login(self):
        """Xử lý sự kiện đăng nhập kèm giới hạn số lần nhập sai."""
        now = std_time.time()
        if self.lock_until and now < self.lock_until:
            remain = int(self.lock_until - now)
            self.lbl_error.config(text=f"Bạn đã nhập sai quá 5 lần. Vui lòng đợi {remain} giây nữa để thử lại.")
            return

        username = self.txt_username.get().strip()
        password = self.txt_password.get().strip()

        self.lbl_error.config(text="")

        # 1. Logic Agent: Kiểm tra dữ liệu đầu vào
        ok, err = require_fields(
            {"username": username, "password": password},
            {"username": "Tên đăng nhập", "password": "Mật khẩu"}
        )
        if not ok:
            self.lbl_error.config(text=err)
            return

        # 2. Database Agent: Tìm người dùng theo username
        db_ok, user = database.get_user_by_username(username)
        if not db_ok:
            self.lbl_error.config(text=f"Lỗi hệ thống: {user}")
            return

        # 3. Logic Agent: Xác thực mật khẩu
        if not user or not verify_password(password, user["mat_khau"]):
            self.failed_attempts += 1
            if self.failed_attempts >= 5:
                self.lock_until = std_time.time() + 30
                self.failed_attempts = 0
                self.lbl_error.config(text="Đã nhập sai 5 lần liên tiếp. Hệ thống tạm khóa 30 giây!")
            else:
                con_lai = 5 - self.failed_attempts
                self.lbl_error.config(text=f"Tên đăng nhập hoặc mật khẩu không chính xác (còn {con_lai} lần thử).")
            return

        # 4. Logic Agent: Kiểm tra trạng thái tài khoản
        if user.get("trang_thai") != "Đang hoạt động":
            self.lbl_error.config(text="Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên!")
            return

        # Reset bộ đếm khi đăng nhập thành công
        self.failed_attempts = 0
        self.lock_until = None

        # 5. Đăng nhập thành công -> Chuyển vào ứng dụng chính
        self.on_login_success(user)
