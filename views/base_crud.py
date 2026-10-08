# ==========================================
# BASE CRUD VIEW
# ==========================================
"""
Lớp giao diện CRUD chuẩn dùng chung cho tất cả các phân hệ quản lý.
Bao gồm:
- Thanh công cụ tìm kiếm và làm mới
- Form nhập liệu bên trái (hỗ trợ readonly cho phân quyền)
- Bảng hiển thị Treeview bên phải kèm thanh cuộn
- Xử lý sự kiện chọn dòng đổ ngược lên form
- Phân tách rõ ràng với CSDL (UI Agent chỉ gọi hàm nghiệp vụ / DB Agent)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable, Dict, List, Optional, Tuple
from views.styles import (
    COLOR_CARD_BG, COLOR_CONTENT_BG, COLOR_BORDER, COLOR_TEXT_MAIN,
    COLOR_TEXT_MUTED, FONT_TITLE, FONT_SECTION, FONT_BODY, FONT_BODY_BOLD,
    FONT_SMALL, COLOR_PRIMARY
)


class BaseCrudView(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        subtitle: str = "",
        readonly: bool = False,
        *args,
        **kwargs
    ):
        super().__init__(parent, bg=COLOR_CONTENT_BG, *args, **kwargs)
        self.title_text = title
        self.subtitle_text = subtitle
        self.readonly = readonly
        self.selected_item_id: Optional[Any] = None

        self._build_header()
        self._build_body()

    # ---------------------------------------------------------
    # 1. DỰNG GIAO DIỆN HEADER & TÌM KIẾM
    # ---------------------------------------------------------
    def _build_header(self):
        header_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        # Tiêu đề bên trái
        title_box = tk.Frame(header_frame, bg=COLOR_CONTENT_BG)
        title_box.pack(side="left")

        lbl_title = tk.Label(
            title_box,
            text=self.title_text,
            font=FONT_TITLE,
            fg=COLOR_TEXT_MAIN,
            bg=COLOR_CONTENT_BG
        )
        lbl_title.pack(anchor="w")

        if self.subtitle_text:
            lbl_sub = tk.Label(
                title_box,
                text=self.subtitle_text,
                font=FONT_SMALL,
                fg=COLOR_TEXT_MUTED,
                bg=COLOR_CONTENT_BG
            )
            lbl_sub.pack(anchor="w")

        # Khối tìm kiếm bên phải
        search_box = tk.Frame(header_frame, bg=COLOR_CONTENT_BG)
        search_box.pack(side="right")

        tk.Label(
            search_box,
            text="🔍 Tìm kiếm:",
            font=FONT_BODY,
            fg=COLOR_TEXT_MAIN,
            bg=COLOR_CONTENT_BG
        ).pack(side="left", padx=(0, 6))

        self.txt_search = ttk.Entry(search_box, width=28, style="Custom.TEntry")
        self.txt_search.pack(side="left", padx=(0, 6))
        self.txt_search.bind("<Return>", lambda e: self.on_search())

        btn_search = ttk.Button(
            search_box,
            text="Tìm",
            style="Neutral.TButton",
            command=self.on_search
        )
        btn_search.pack(side="left", padx=(0, 6))

        btn_refresh = ttk.Button(
            search_box,
            text="🔄 Làm mới",
            style="Neutral.TButton",
            command=self.on_refresh
        )
        btn_refresh.pack(side="left")

    # ---------------------------------------------------------
    # 2. DỰNG BODY 2 CỘT (FORM BÊN TRÁI - TREEVIEW BÊN PHẢI)
    # ---------------------------------------------------------
    def _build_body(self):
        body_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
        body_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Khung Form bên trái
        self.form_container = tk.Frame(
            body_frame,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            padx=16,
            pady=16,
            width=360
        )
        self.form_container.pack(side="left", fill="y", padx=(0, 12))
        self.form_container.pack_propagate(False)

        form_title = tk.Label(
            self.form_container,
            text="📝 THÔNG TIN CHI TIẾT",
            font=FONT_SECTION,
            fg=COLOR_PRIMARY,
            bg=COLOR_CARD_BG
        )
        form_title.pack(anchor="w", pady=(0, 12))

        # Canvas/Frame cho các trường nhập liệu
        self.form_fields_frame = tk.Frame(self.form_container, bg=COLOR_CARD_BG)
        self.form_fields_frame.pack(fill="both", expand=True)

        # Khung nút thao tác form
        self.btn_action_frame = tk.Frame(self.form_container, bg=COLOR_CARD_BG)
        self.btn_action_frame.pack(fill="x", pady=(10, 0))

        if not self.readonly:
            self.btn_add = ttk.Button(
                self.btn_action_frame,
                text="➕ Thêm mới",
                style="Primary.TButton",
                command=self.on_add
            )
            self.btn_add.pack(fill="x", pady=2)

            self.btn_update = ttk.Button(
                self.btn_action_frame,
                text="✏️ Cập nhật",
                style="Success.TButton",
                command=self.on_update
            )
            self.btn_update.pack(fill="x", pady=2)

            self.btn_delete = ttk.Button(
                self.btn_action_frame,
                text="🗑️ Xóa",
                style="Danger.TButton",
                command=self.on_delete
            )
            self.btn_delete.pack(fill="x", pady=2)
        else:
            lbl_ro = tk.Label(
                self.btn_action_frame,
                text="⚠️ Chế độ xem (Chỉ đọc)",
                font=FONT_BODY_BOLD,
                fg=COLOR_TEXT_MUTED,
                bg=COLOR_CARD_BG
            )
            lbl_ro.pack(pady=4)

        self.btn_clear = ttk.Button(
            self.btn_action_frame,
            text="🧹 Làm sạch form",
            style="Neutral.TButton",
            command=self.clear_form
        )
        self.btn_clear.pack(fill="x", pady=2)

        # Khung Table bên phải
        self.table_container = tk.Frame(
            body_frame,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1
        )
        self.table_container.pack(side="right", fill="both", expand=True)

        # Thanh trạng thái đếm số dòng ở chân bảng
        self.footer_frame = tk.Frame(self.table_container, bg="#FAFAFA", height=28)
        self.footer_frame.pack(side="bottom", fill="x")

        self.lbl_record_count = tk.Label(
            self.footer_frame,
            text="Tổng số: 0 bản ghi",
            font=FONT_SMALL,
            fg=COLOR_TEXT_MUTED,
            bg="#FAFAFA"
        )
        self.lbl_record_count.pack(side="left", padx=10, pady=4)

        self._build_treeview()

    def _build_treeview(self):
        """Khởi tạo Treeview kèm thanh cuộn đứng và ngang."""
        scroll_y = ttk.Scrollbar(self.table_container, orient="vertical")
        scroll_x = ttk.Scrollbar(self.table_container, orient="horizontal")

        self.tree = ttk.Treeview(
            self.table_container,
            style="Custom.Treeview",
            selectmode="browse",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select_internal)

    # ---------------------------------------------------------
    # 3. CÁC HÀM CƠ CHẾ NỘI BỘ VÀ ABSTRACT ĐỂ CLASS CON OVERRIDE
    # ---------------------------------------------------------
    def _on_tree_select_internal(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item_id = selected[0]
        values = self.tree.item(item_id, "values")
        if values:
            self.selected_item_id = values[0]
            self.populate_form_from_selection(values)

    def populate_form_from_selection(self, values: Tuple[Any, ...]):
        """Lớp con ghi đè để đổ dữ liệu từ dòng được chọn lên form."""
        pass

    def clear_form(self):
        """Lớp con ghi đè để xóa trắng form nhập liệu."""
        self.selected_item_id = None
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def on_search(self):
        """Lớp con ghi đè để xử lý tìm kiếm."""
        pass

    def on_refresh(self):
        """Làm mới dữ liệu và xóa trắng form."""
        self.txt_search.delete(0, tk.END)
        self.clear_form()
        self.load_data()

    def load_data(self):
        """Lớp con ghi đè để tải dữ liệu từ Database Agent."""
        pass

    def on_add(self):
        """Lớp con ghi đè để thêm bản ghi mới."""
        pass

    def on_update(self):
        """Lớp con ghi đè để cập nhật bản ghi đang chọn."""
        pass

    def on_delete(self):
        """Lớp con ghi đè để xóa bản ghi đang chọn."""
        pass

    def update_record_count(self, count: int, extra_info: str = ""):
        txt = f"Tổng số: {count} bản ghi"
        if extra_info:
            txt += f" | {extra_info}"
        self.lbl_record_count.config(text=txt)

    # Helper hiển thị thông báo
    def show_info(self, msg: str, title: str = "Thông báo"):
        messagebox.showinfo(title, msg, parent=self)

    def show_error(self, msg: str, title: str = "Lỗi"):
        messagebox.showerror(title, msg, parent=self)

    def ask_confirm(self, msg: str, title: str = "Xác nhận") -> bool:
        return messagebox.askyesno(title, msg, parent=self)
