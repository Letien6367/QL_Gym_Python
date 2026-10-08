# ==========================================
# GIAO DIỆN & STYLE TOKENS
# ==========================================
"""
Quản lý màu sắc, kiểu chữ và cấu hình ttk.Style cho toàn bộ ứng dụng.
"""

import tkinter as tk
from tkinter import ttk

# Bảng màu chủ đạo (Gym energetic & professional dark-accent)
COLOR_PRIMARY = "#FF5722"       # Màu cam thể thao chủ đạo
COLOR_PRIMARY_HOVER = "#E64A19"
COLOR_SECONDARY = "#4A5568"
COLOR_SIDEBAR_BG = "#1A1D24"    # Sidebar tối sang trọng
COLOR_SIDEBAR_ACTIVE = "#FF5722"
COLOR_SIDEBAR_HOVER = "#2D323F"
COLOR_SIDEBAR_TEXT = "#E2E8F0"
COLOR_CONTENT_BG = "#F4F6F9"    # Nền nội dung sáng dịu mắt
COLOR_CARD_BG = "#FFFFFF"       # Nền card/form
COLOR_BORDER = "#E2E8F0"        # Viền mỏng

COLOR_TEXT_MAIN = "#1A202C"     # Chữ chính
COLOR_TEXT_MUTED = "#718096"    # Chữ phụ
COLOR_SUCCESS = "#38A169"       # Xanh lá thành công
COLOR_DANGER = "#E53E3E"        # Đỏ cảnh báo / xóa
COLOR_WARNING = "#D69E2E"       # Vàng cảnh báo
COLOR_INFO = "#3182CE"          # Xanh dương thông tin

# Kiểu chữ
FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 16, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 12, "bold")
FONT_SECTION = (FONT_FAMILY, 11, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_KPI_VAL = (FONT_FAMILY, 20, "bold")
FONT_KPI_LBL = (FONT_FAMILY, 10)


def configure_app_styles():
    """Khởi tạo cấu hình ttk.Style áp dụng cho toàn bộ cửa sổ ứng dụng."""
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Treeview
    style.configure(
        "Custom.Treeview",
        background=COLOR_CARD_BG,
        foreground=COLOR_TEXT_MAIN,
        fieldbackground=COLOR_CARD_BG,
        font=FONT_BODY,
        rowheight=30,
        borderwidth=0
    )
    style.map(
        "Custom.Treeview",
        background=[("selected", "#FFE0DB")],
        foreground=[("selected", "#C53030")]
    )

    style.configure(
        "Custom.Treeview.Heading",
        background="#EDF2F7",
        foreground=COLOR_TEXT_MAIN,
        font=FONT_BODY_BOLD,
        padding=(6, 8),
        borderwidth=0
    )
    style.map(
        "Custom.Treeview.Heading",
        background=[("active", "#E2E8F0")]
    )

    # Nút bấm Primary
    style.configure(
        "Primary.TButton",
        background=COLOR_PRIMARY,
        foreground="#FFFFFF",
        font=FONT_BODY_BOLD,
        padding=(12, 6),
        borderwidth=0
    )
    style.map(
        "Primary.TButton",
        background=[("active", COLOR_PRIMARY_HOVER), ("disabled", "#CBD5E0")],
        foreground=[("disabled", "#A0AEC0")]
    )

    # Nút bấm Success
    style.configure(
        "Success.TButton",
        background=COLOR_SUCCESS,
        foreground="#FFFFFF",
        font=FONT_BODY_BOLD,
        padding=(12, 6),
        borderwidth=0
    )
    style.map(
        "Success.TButton",
        background=[("active", "#2F855A")]
    )

    # Nút bấm Danger
    style.configure(
        "Danger.TButton",
        background=COLOR_DANGER,
        foreground="#FFFFFF",
        font=FONT_BODY_BOLD,
        padding=(12, 6),
        borderwidth=0
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#C53030")]
    )

    # Nút bấm Neutral / Secondary
    style.configure(
        "Neutral.TButton",
        background="#EDF2F7",
        foreground=COLOR_TEXT_MAIN,
        font=FONT_BODY,
        padding=(10, 6),
        borderwidth=0
    )
    style.map(
        "Neutral.TButton",
        background=[("active", "#E2E8F0")]
    )

    # Entry & Combobox
    style.configure(
        "Custom.TEntry",
        padding=6,
        font=FONT_BODY
    )
    style.configure(
        "Custom.TCombobox",
        padding=5,
        font=FONT_BODY
    )
