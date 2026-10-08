# ==========================================
# PHÂN HỆ TỔNG QUAN (DASHBOARD VIEW)
# ==========================================
"""
Màn hình Dashboard thống kê và phân tích số liệu phòng gym.
Bao gồm:
- 4 Thẻ KPI: Tổng hội viên, Gói đang hoạt động, Doanh thu tháng, Lịch tập hôm nay
- Biểu đồ Matplotlib: Cột doanh thu 12 tháng & Tròn thị phần gói tập
- Bảng cảnh báo: Hội viên có gói tập sắp hết hạn trong 7 ngày tới
"""

import tkinter as tk
from tkinter import ttk
from datetime import date
from typing import Any, Dict

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import database
from views.styles import (
    COLOR_CARD_BG, COLOR_CONTENT_BG, COLOR_BORDER, COLOR_TEXT_MAIN,
    COLOR_TEXT_MUTED, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_INFO, COLOR_WARNING,
    COLOR_DANGER, FONT_TITLE, FONT_SUBTITLE, FONT_SECTION, FONT_BODY,
    FONT_BODY_BOLD, FONT_SMALL, FONT_KPI_VAL, FONT_KPI_LBL
)


class DashboardView(tk.Frame):
    def __init__(self, parent: tk.Widget, current_user: Dict[str, Any]):
        super().__init__(parent, bg=COLOR_CONTENT_BG)
        self.current_user = current_user

        self._build_ui()
        self.refresh_dashboard()

    def _build_ui(self):
        # Thanh cuộn chính cho toàn bộ trang Dashboard
        canvas = tk.Canvas(self, bg=COLOR_CONTENT_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=COLOR_CONTENT_BG)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Cuộn trang bằng con lăn chuột (MouseWheel)
        def _on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_scroll_up(event):
            canvas.yview_scroll(-1, "units")

        def _on_scroll_down(event):
            canvas.yview_scroll(1, "units")

        def _bind_wheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_scroll_up)
            canvas.bind_all("<Button-5>", _on_scroll_down)

        def _unbind_wheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # 1. Header chào mừng
        self._build_welcome_header()

        # 2. Hàng 4 thẻ KPI
        self._build_kpi_cards()

        # 3. Hàng biểu đồ (Doanh thu & Cơ cấu gói tập)
        self._build_charts_section()

        # 4. Bảng danh sách sắp hết hạn trong 7 ngày
        self._build_expiring_soon_section()

    def _build_welcome_header(self):
        header = tk.Frame(self.scrollable_frame, bg=COLOR_CONTENT_BG)
        header.pack(fill="x", padx=24, pady=(20, 15))

        title_box = tk.Frame(header, bg=COLOR_CONTENT_BG)
        title_box.pack(side="left")

        user_name = self.current_user.get("ho_ten", "Quản trị viên")
        role_name = self.current_user.get("vai_tro", "Nhân viên")

        tk.Label(
            title_box,
            text=f"👋 Xin chào, {user_name} ({role_name})",
            font=FONT_TITLE,
            fg=COLOR_TEXT_MAIN,
            bg=COLOR_CONTENT_BG
        ).pack(anchor="w")

        today_str = date.today().strftime("Hôm nay: %d/%m/%Y")
        tk.Label(
            title_box,
            text=f"Báo cáo tổng quan tình hình kinh doanh & hoạt động phòng gym • {today_str}",
            font=FONT_SMALL,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CONTENT_BG
        ).pack(anchor="w")

        btn_refresh = ttk.Button(
            header,
            text="🔄 Làm mới số liệu",
            style="Neutral.TButton",
            command=self.refresh_dashboard
        )
        btn_refresh.pack(side="right")

    def _build_kpi_cards(self):
        cards_row = tk.Frame(self.scrollable_frame, bg=COLOR_CONTENT_BG)
        cards_row.pack(fill="x", padx=24, pady=(0, 15))

        # Cấu hình 4 cột đều nhau
        cards_row.columnconfigure(0, weight=1)
        cards_row.columnconfigure(1, weight=1)
        cards_row.columnconfigure(2, weight=1)
        cards_row.columnconfigure(3, weight=1)

        # Card 1: Tổng hội viên
        self.card_members = self._create_kpi_card(
            parent=cards_row,
            col=0,
            title="TỔNG HỘI VIÊN",
            icon="👥",
            accent_color=COLOR_INFO
        )

        # Card 2: Gói đang hoạt động
        self.card_active_subs = self._create_kpi_card(
            parent=cards_row,
            col=1,
            title="GÓI ĐANG HOẠT ĐỘNG",
            icon="📋",
            accent_color=COLOR_SUCCESS
        )

        # Card 3: Doanh thu tháng này
        self.card_revenue = self._create_kpi_card(
            parent=cards_row,
            col=2,
            title="DOANH THU THÁNG",
            icon="💰",
            accent_color=COLOR_PRIMARY
        )

        # Card 4: Lịch tập hôm nay
        self.card_schedules = self._create_kpi_card(
            parent=cards_row,
            col=3,
            title="LỊCH TẬP HÔM NAY",
            icon="📅",
            accent_color=COLOR_WARNING
        )

    def _create_kpi_card(self, parent: tk.Widget, col: int, title: str, icon: str, accent_color: str) -> Dict[str, Any]:
        frame = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            padx=16,
            pady=14
        )
        frame.grid(row=0, column=col, sticky="nsew", padx=6)

        # Thanh vạch màu bên trên
        stripe = tk.Frame(frame, bg=accent_color, height=3)
        stripe.pack(fill="x", pady=(0, 10))

        top_box = tk.Frame(frame, bg=COLOR_CARD_BG)
        top_box.pack(fill="x")

        tk.Label(
            top_box,
            text=title,
            font=FONT_KPI_LBL,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CARD_BG
        ).pack(side="left")

        tk.Label(
            top_box,
            text=icon,
            font=(FONT_TITLE[0], 16),
            bg=COLOR_CARD_BG
        ).pack(side="right")

        lbl_val = tk.Label(
            frame,
            text="0",
            font=FONT_KPI_VAL,
            fg=COLOR_TEXT_MAIN,
            bg=COLOR_CARD_BG
        )
        lbl_val.pack(anchor="w", pady=(8, 0))

        return {"val_label": lbl_val}

    def _build_charts_section(self):
        charts_row = tk.Frame(self.scrollable_frame, bg=COLOR_CONTENT_BG)
        charts_row.pack(fill="x", padx=24, pady=(0, 15))

        charts_row.columnconfigure(0, weight=3)
        charts_row.columnconfigure(1, weight=2)

        # Khung Biểu đồ cột Doanh thu (bên trái)
        chart_left = tk.Frame(
            charts_row,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            padx=16,
            pady=16
        )
        chart_left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(
            chart_left,
            text="📊 DOANH THU 12 THÁNG",
            font=FONT_SECTION,
            fg=COLOR_TEXT_MAIN,
            bg=COLOR_CARD_BG
        ).pack(anchor="w", pady=(0, 10))

        self.fig_bar = Figure(figsize=(6, 3.2), dpi=100)
        self.fig_bar.patch.set_facecolor(COLOR_CARD_BG)
        self.canvas_bar = FigureCanvasTkAgg(self.fig_bar, master=chart_left)
        self.canvas_bar.get_tk_widget().pack(fill="both", expand=True)

        # Khung Biểu đồ tròn Gói tập (bên phải)
        chart_right = tk.Frame(
            charts_row,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            padx=16,
            pady=16
        )
        chart_right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(
            chart_right,
            text="🥧 CƠ CẤU GÓI TẬP",
            font=FONT_SECTION,
            fg=COLOR_TEXT_MAIN,
            bg=COLOR_CARD_BG
        ).pack(anchor="w", pady=(0, 10))

        self.fig_pie = Figure(figsize=(4.2, 3.2), dpi=100)
        self.fig_pie.patch.set_facecolor(COLOR_CARD_BG)
        self.canvas_pie = FigureCanvasTkAgg(self.fig_pie, master=chart_right)
        self.canvas_pie.get_tk_widget().pack(fill="both", expand=True)

    def _build_expiring_soon_section(self):
        table_card = tk.Frame(
            self.scrollable_frame,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            padx=16,
            pady=16
        )
        table_card.pack(fill="x", padx=24, pady=(0, 24))

        tk.Label(
            table_card,
            text="⚠️ GÓI TẬP SẮP HẾT HẠN (TRONG VÒNG 7 NGÀY TỚI)",
            font=FONT_SECTION,
            fg=COLOR_DANGER,
            bg=COLOR_CARD_BG
        ).pack(anchor="w", pady=(0, 10))

        cols = ("ma_dk", "ten_hv", "sdt", "ten_goi", "ngay_ket_thuc", "con_lai")
        self.tree_exp = ttk.Treeview(
            table_card,
            columns=cols,
            show="headings",
            height=6,
            style="Custom.Treeview"
        )

        configs = [
            ("ma_dk", "Mã ĐK", 70, "center"),
            ("ten_hv", "Họ và tên hội viên", 180, "w"),
            ("sdt", "Số điện thoại", 120, "center"),
            ("ten_goi", "Gói tập", 160, "w"),
            ("ngay_ket_thuc", "Ngày hết hạn", 120, "center"),
            ("con_lai", "Thời gian còn lại", 140, "center")
        ]

        for col, head, w, anc in configs:
            self.tree_exp.heading(col, text=head)
            self.tree_exp.column(col, width=w, anchor=anc)

        self.tree_exp.pack(fill="x")

    def refresh_dashboard(self):
        """Làm mới dữ liệu từ Database Agent và vẽ lại biểu đồ."""
        today = date.today()

        # 1. Tải KPI
        ok, stats = database.get_dashboard_summary(today)
        if ok and stats:
            self.card_members["val_label"].config(text=str(stats.get("tong_hoi_vien", 0)))
            self.card_active_subs["val_label"].config(text=str(stats.get("goi_hoat_dong", 0)))
            rev = float(stats.get("doanh_thu_thang", 0))
            self.card_revenue["val_label"].config(text=f"{rev:,.0f} đ")
            self.card_schedules["val_label"].config(text=str(stats.get("lich_tap_hom_nay", 0)))

        # 2. Vẽ biểu đồ Doanh thu 12 tháng
        ok, rev_data = database.get_monthly_revenue_stats(today.year)
        self.fig_bar.clear()
        ax_bar = self.fig_bar.add_subplot(111)

        if ok and rev_data:
            months = [f"T{d['thang']}" for d in rev_data]
            values = [d["doanh_thu"] / 1_000_000 for d in rev_data]  # Triệu VNĐ

            bars = ax_bar.bar(months, values, color=COLOR_PRIMARY, width=0.6, edgecolor="none", zorder=3)
            ax_bar.set_ylabel("Triệu VNĐ", fontsize=8, color=COLOR_TEXT_MUTED)
            ax_bar.set_title(f"Năm {today.year}", fontsize=9, color=COLOR_TEXT_MUTED, loc="right")
            ax_bar.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)

            # Gắn nhãn giá trị trên cột nếu > 0
            for bar in bars:
                h = bar.get_height()
                if h > 0:
                    ax_bar.annotate(
                        f"{h:.1f}",
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 2),
                        textcoords="offset points",
                        ha="center", va="bottom",
                        fontsize=7,
                        color=COLOR_TEXT_MAIN
                    )
        ax_bar.tick_params(colors=COLOR_TEXT_MUTED, labelsize=8)
        for spine in ax_bar.spines.values():
            spine.set_color(COLOR_BORDER)
        self.fig_bar.tight_layout()
        self.canvas_bar.draw()

        # 3. Vẽ biểu đồ tròn Cơ cấu gói tập
        ok, pkg_data = database.get_package_popularity()
        self.fig_pie.clear()
        ax_pie = self.fig_pie.add_subplot(111)

        if ok and pkg_data:
            labels = [p["ten_goi"] for p in pkg_data]
            counts = [p["so_luong"] for p in pkg_data]
            colors = ["#FF5722", "#38A169", "#3182CE", "#D69E2E", "#805AD5", "#DD6B20"]

            if sum(counts) > 0:
                ax_pie.pie(
                    counts,
                    labels=labels,
                    autopct="%1.0f%%",
                    colors=colors[:len(labels)],
                    startangle=140,
                    textprops={"fontsize": 8, "color": COLOR_TEXT_MAIN},
                    wedgeprops={"edgecolor": "white", "linewidth": 1.5}
                )
            else:
                ax_pie.text(0.5, 0.5, "Chưa có đăng ký", ha="center", va="center", color=COLOR_TEXT_MUTED)
        self.fig_pie.tight_layout()
        self.canvas_pie.draw()

        # 4. Tải danh sách sắp hết hạn
        for item in self.tree_exp.get_children():
            self.tree_exp.delete(item)

        ok, exp_rows = database.get_expiring_soon_registrations(days=7, today=today)
        if ok and exp_rows:
            for r in exp_rows:
                days_left = r["so_ngay_con_lai"]
                txt_left = "Hôm nay hết hạn" if days_left == 0 else f"Còn {days_left} ngày"
                self.tree_exp.insert(
                    "",
                    "end",
                    values=(
                        r["ma_dk"],
                        r["ten_hv"],
                        r["so_dien_thoai"],
                        r["ten_goi"],
                        str(r["ngay_ket_thuc"]),
                        txt_left
                    )
                )
