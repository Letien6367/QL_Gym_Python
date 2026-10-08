# ==========================================
# KHỞI CHẠY ỨNG DỤNG QUẢN LÝ PHÒNG GYM
# ==========================================
"""
UI/UX Agent chính của hệ thống.
Quản lý vòng đời ứng dụng Desktop:
- Khởi động cửa sổ chính Tkinter
- Hiển thị màn hình Đăng nhập (LoginView)
- Điều phối điều hướng Sidebar dựa trên phân quyền vai trò (Admin / Nhân viên)
- Hoán chuyển các phân hệ quản lý mượt mà
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Any, Dict, Optional

from config import APP_TITLE, WINDOW_SIZE, MIN_WINDOW_SIZE, ROLE_PERMISSIONS
import database
from views.styles import (
    configure_app_styles, COLOR_SIDEBAR_BG, COLOR_SIDEBAR_ACTIVE,
    COLOR_SIDEBAR_HOVER, COLOR_SIDEBAR_TEXT, COLOR_CONTENT_BG,
    COLOR_BORDER, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_PRIMARY,
    COLOR_SUCCESS, FONT_TITLE, FONT_SUBTITLE, FONT_SECTION, FONT_BODY,
    FONT_BODY_BOLD, FONT_SMALL
)

from views.login import LoginView
from views.dashboard import DashboardView
from views.hoi_vien import HoiVienView
from views.huan_luyen_vien import HuanLuyenVienView
from views.goi_tap import GoiTapView
from views.dang_ky import DangKyView
from views.thanh_toan import ThanhToanView
from views.lich_tap import LichTapView
from views.nguoi_dung import NguoiDungView


class GymApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(*MIN_WINDOW_SIZE)

        # Cấu hình màu nền gốc
        self.configure(bg=COLOR_CONTENT_BG)

        # Cấu hình style dùng chung
        configure_app_styles()

        self.current_user: Optional[Dict[str, Any]] = None
        self.active_nav_key: Optional[str] = None
        self.nav_buttons: Dict[str, tk.Label] = {}
        self.current_view_frame: Optional[tk.Widget] = None
        self._clock_after_id: Optional[str] = None
        self._db_after_id: Optional[str] = None

        # Khởi chạy màn hình Đăng nhập
        self._show_login_screen()

    # ---------------------------------------------------------
    # 1. QUẢN LÝ MÀN HÌNH ĐĂNG NHẬP
    # ---------------------------------------------------------
    def _show_login_screen(self):
        """Hiển thị màn hình Đăng nhập."""
        if hasattr(self, "main_container") and self.main_container:
            self._cancel_timers()
            self.main_container.destroy()
            self.main_container = None

        self.login_view = LoginView(self, on_login_success=self._on_login_success)
        self.login_view.pack(fill="both", expand=True)

    def _on_login_success(self, user_info: Dict[str, Any]):
        """Xử lý sau khi người dùng đăng nhập thành công."""
        self.current_user = user_info
        self.login_view.destroy()

        # Tự động cập nhật gói tập hết hạn
        database.update_expired_status()

        # Dựng layout chính
        self._build_main_layout()

        # Mở trang mặc định Dashboard
        self.navigate_to("dashboard")

    # ---------------------------------------------------------
    # 2. DỰNG LAYOUT CHÍNH (SIDEBAR + TOPBAR + CONTENT)
    # ---------------------------------------------------------
    def _build_main_layout(self):
        self.main_container = tk.Frame(self, bg=COLOR_CONTENT_BG)
        self.main_container.pack(fill="both", expand=True)

        # A. SIDEBAR BÊN TRÁI
        self.sidebar = tk.Frame(self.main_container, bg=COLOR_SIDEBAR_BG, width=240)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self._build_sidebar_content()

        # B. PHẦN BÊN PHẢI (TOPBAR + NỘI DUNG)
        self.right_container = tk.Frame(self.main_container, bg=COLOR_CONTENT_BG)
        self.right_container.pack(side="right", fill="both", expand=True)

        self._build_topbar()

        # Khung chứa view động
        self.content_area = tk.Frame(self.right_container, bg=COLOR_CONTENT_BG)
        self.content_area.pack(fill="both", expand=True)

    def _build_sidebar_content(self):
        # 1. Logo & Tên phần mềm
        logo_frame = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR_BG, padx=16, pady=20)
        logo_frame.pack(fill="x")

        tk.Label(
            logo_frame,
            text="🏋️ GYMPRO",
            font=(FONT_TITLE[0], 18, "bold"),
            fg=COLOR_PRIMARY,
            bg=COLOR_SIDEBAR_BG
        ).pack(anchor="w")

        tk.Label(
            logo_frame,
            text="FITNESS & YOGA MANAGEMENT",
            font=(FONT_BODY[0], 7, "bold"),
            fg="#718096",
            bg=COLOR_SIDEBAR_BG
        ).pack(anchor="w", pady=(2, 0))

        # Đường ngăn cách
        tk.Frame(self.sidebar, bg="#2D3748", height=1).pack(fill="x", padx=14, pady=(0, 10))

        # 2. Thẻ thông tin người dùng đang đăng nhập
        user_card = tk.Frame(self.sidebar, bg="#242833", padx=12, pady=10)
        user_card.pack(fill="x", padx=12, pady=(0, 14))

        tk.Label(
            user_card,
            text="👤 " + self.current_user.get("ho_ten", "Người dùng"),
            font=FONT_BODY_BOLD,
            fg="#FFFFFF",
            bg="#242833"
        ).pack(anchor="w")

        role_text = f"Quyền: {self.current_user.get('vai_tro', 'Nhân viên')}"
        tk.Label(
            user_card,
            text=role_text,
            font=FONT_SMALL,
            fg="#A0AEC0",
            bg="#242833"
        ).pack(anchor="w", pady=(2, 0))

        # 3. Danh mục Menu điều hướng
        menu_items = [
            ("dashboard", "📊 Tổng quan"),
            ("hoi_vien", "👥 Quản lý Hội viên"),
            ("huan_luyen_vien", "🏋️ Huấn luyện viên"),
            ("goi_tap", "📦 Quản lý Gói tập"),
            ("dang_ky", "📝 Đăng ký Gói tập"),
            ("thanh_toan", "💳 Quản lý Thanh toán"),
            ("lich_tap", "📅 Quản lý Lịch tập"),
            ("nguoi_dung", "⚙️ Quản lý Người dùng")
        ]

        user_role = self.current_user.get("vai_tro", "Nhân viên")
        role_rules = ROLE_PERMISSIONS.get(user_role, {})

        nav_box = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR_BG)
        nav_box.pack(fill="both", expand=True)

        self.nav_buttons.clear()

        for key, title in menu_items:
            perm = role_rules.get(key, "full")
            if perm == "hidden":
                continue  # Ẩn hoàn toàn nếu không có quyền

            btn = tk.Label(
                nav_box,
                text=f"  {title}",
                font=FONT_BODY,
                fg=COLOR_SIDEBAR_TEXT,
                bg=COLOR_SIDEBAR_BG,
                anchor="w",
                padx=16,
                pady=10,
                cursor="hand2"
            )
            btn.pack(fill="x", pady=1)

            # Bind sự kiện Click và Hover
            btn.bind("<Button-1>", lambda e, k=key: self.navigate_to(k))
            btn.bind("<Enter>", lambda e, b=btn, k=key: self._on_nav_hover(b, k, True))
            btn.bind("<Leave>", lambda e, b=btn, k=key: self._on_nav_hover(b, k, False))

            self.nav_buttons[key] = btn

        # 4. Nút Đăng xuất ở chân Sidebar
        logout_box = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR_BG, padx=12, pady=16)
        logout_box.pack(side="bottom", fill="x")

        btn_logout = tk.Button(
            logout_box,
            text="🚪 ĐĂNG XUẤT",
            font=FONT_BODY_BOLD,
            fg="#FFFFFF",
            bg="#742A2A",
            activebackground="#9B2C2C",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            pady=8,
            command=self._handle_logout
        )
        btn_logout.pack(fill="x")

    def _build_topbar(self):
        """Thanh tiêu đề phía trên."""
        topbar = tk.Frame(self.right_container, bg="#FFFFFF", height=50, highlightbackground=COLOR_BORDER, highlightthickness=1)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        self.lbl_top_title = tk.Label(
            topbar,
            text="HỆ THỐNG QUẢN LÝ PHÒNG GYM",
            font=FONT_SUBTITLE,
            fg=COLOR_TEXT_MAIN,
            bg="#FFFFFF"
        )
        self.lbl_top_title.pack(side="left", padx=20)

        # Trạng thái kết nối DB và Đồng hồ
        info_box = tk.Frame(topbar, bg="#FFFFFF")
        info_box.pack(side="right", padx=20)

        # Trạng thái CSDL (cập nhật định kỳ theo kết nối thật)
        self.lbl_db_status = tk.Label(
            info_box,
            text="⏳ CSDL: Đang kiểm tra...",
            font=FONT_SMALL,
            fg=COLOR_TEXT_MUTED,
            bg="#FFFFFF"
        )
        self.lbl_db_status.pack(side="left", padx=(0, 16))
        self._refresh_db_status()

        # Đồng hồ số realtime
        self.lbl_clock = tk.Label(
            info_box,
            text="",
            font=FONT_SMALL,
            fg=COLOR_TEXT_MUTED,
            bg="#FFFFFF"
        )
        self.lbl_clock.pack(side="right")
        self._update_clock()

    def _update_clock(self):
        now_str = datetime.now().strftime("%H:%M:%S • %d/%m/%Y")
        self.lbl_clock.config(text=now_str)
        self._clock_after_id = self.after(1000, self._update_clock)

    def _refresh_db_status(self):
        """Kiểm tra kết nối MySQL thật sự mỗi 15 giây để hiển thị đúng trạng thái."""
        ok, _ = database.test_connection()
        if ok:
            self.lbl_db_status.config(text="🟢 CSDL: Kết nối", fg=COLOR_SUCCESS)
        else:
            self.lbl_db_status.config(text="🔴 CSDL: Mất kết nối", fg="#E53E3E")
        self._db_after_id = self.after(15000, self._refresh_db_status)

    def _cancel_timers(self):
        """Huỷ các vòng lặp after() trước khi hủy giao diện để tránh TclError."""
        for attr in ("_clock_after_id", "_db_after_id"):
            after_id = getattr(self, attr, None)
            if after_id:
                try:
                    self.after_cancel(after_id)
                except Exception:
                    pass
                setattr(self, attr, None)

    # ---------------------------------------------------------
    # 3. HIỆU ỨNG VÀ ĐIỀU HƯỚNG TỪNG TRANG
    # ---------------------------------------------------------
    def _on_nav_hover(self, btn: tk.Label, key: str, is_hover: bool):
        if key == self.active_nav_key:
            return
        if is_hover:
            btn.config(bg=COLOR_SIDEBAR_HOVER)
        else:
            btn.config(bg=COLOR_SIDEBAR_BG)

    def navigate_to(self, key: str):
        """Chuyển sang giao diện tương ứng với mục được chọn."""
        self.active_nav_key = key

        # Cập nhật style nút trên sidebar
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.config(bg=COLOR_SIDEBAR_ACTIVE, fg="#FFFFFF", font=FONT_BODY_BOLD)
            else:
                btn.config(bg=COLOR_SIDEBAR_BG, fg=COLOR_SIDEBAR_TEXT, font=FONT_BODY)

        # Hủy view cũ nếu có
        if self.current_view_frame:
            self.current_view_frame.destroy()

        user_role = self.current_user.get("vai_tro", "Nhân viên")
        role_rules = ROLE_PERMISSIONS.get(user_role, {})
        is_readonly = (role_rules.get(key) == "readonly")

        # Cập nhật tiêu đề Topbar
        titles_map = {
            "dashboard": "BÁO CÁO THỐNG KÊ & TỔNG QUAN HỆ THỐNG",
            "hoi_vien": "QUẢN LÝ DANH SÁCH HỘI VIÊN",
            "huan_luyen_vien": "QUẢN LÝ ĐỘI NGŨ HUẤN LUYỆN VIÊN",
            "goi_tap": "QUẢN LÝ GÓI TẬP VÀ BẢNG GIÁ",
            "dang_ky": "QUẢN LÝ ĐĂNG KÝ GÓI TẬP",
            "thanh_toan": "QUẢN LÝ HÓA ĐƠN VÀ THANH TOÁN",
            "lich_tap": "QUẢN LÝ LỊCH TẬP LUYỆN",
            "nguoi_dung": "QUẢN TRỊ TÀI KHOẢN VÀ PHÂN QUYỀN"
        }
        self.lbl_top_title.config(text=titles_map.get(key, APP_TITLE))

        # Tự động cập nhật trạng thái hết hạn khi đổi trang
        database.update_expired_status()

        # Khởi tạo view mới
        if key == "dashboard":
            self.current_view_frame = DashboardView(self.content_area, current_user=self.current_user)
        elif key == "hoi_vien":
            self.current_view_frame = HoiVienView(self.content_area, readonly=is_readonly)
        elif key == "huan_luyen_vien":
            self.current_view_frame = HuanLuyenVienView(self.content_area, readonly=is_readonly)
        elif key == "goi_tap":
            self.current_view_frame = GoiTapView(self.content_area, readonly=is_readonly)
        elif key == "dang_ky":
            self.current_view_frame = DangKyView(self.content_area, readonly=is_readonly)
        elif key == "thanh_toan":
            self.current_view_frame = ThanhToanView(self.content_area, readonly=is_readonly)
        elif key == "lich_tap":
            self.current_view_frame = LichTapView(self.content_area, readonly=is_readonly)
        elif key == "nguoi_dung":
            self.current_view_frame = NguoiDungView(self.content_area, current_user=self.current_user)

        if self.current_view_frame:
            self.current_view_frame.pack(fill="both", expand=True)

    def _handle_logout(self):
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc chắn muốn đăng xuất khỏi hệ thống?", parent=self):
            self.current_user = None
            self.active_nav_key = None
            self._show_login_screen()


if __name__ == "__main__":
    app = GymApp()
    app.mainloop()
