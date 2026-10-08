# ==========================================
# PHÂN HỆ QUẢN LÝ LỊCH TẬP (SCHEDULE VIEW)
# ==========================================
"""
Quản lý lịch tập luyện giữa hội viên và huấn luyện viên.
Đặc tả nghiệp vụ thời gian thực theo AGENTS.md:
- Giờ tập phải nằm trong khoảng 06:00 - 22:00
- Giờ kết thúc phải lớn hơn giờ bắt đầu
- Bắt buộc kiểm tra trùng lịch (cùng hội viên hoặc cùng HLV không được có 2 lịch trùng giờ trong ngày)
- Thông báo lỗi chi tiết khi xảy ra xung đột
"""

import tkinter as tk
from tkinter import ttk
from datetime import date, time
from typing import Any, Dict, List, Optional, Tuple

try:
    from tkcalendar import DateEntry
    HAS_TKCALENDAR = True
except ImportError:
    HAS_TKCALENDAR = False

import database
from utils.validators import (
    validate_lich_tap_form, parse_date, parse_time, find_schedule_conflict,
    check_date_within_active_registration
)
from views.base_crud import BaseCrudView
from views.styles import (
    COLOR_CARD_BG, COLOR_CONTENT_BG, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL
)


class LichTapView(BaseCrudView):
    def __init__(self, parent: tk.Widget, readonly: bool = False):
        super().__init__(
            parent=parent,
            title="Quản Lý Lịch Tập Luyện",
            subtitle="Đặt lịch và kiểm tra xung đột thời gian giữa Hội viên và Huấn luyện viên",
            readonly=readonly
        )
        self.members_map: Dict[str, int] = {}
        self.coaches_map: Dict[str, int] = {}

        self._setup_columns()
        self._build_custom_form()
        self._load_combobox_data()
        self.load_data()

    def _setup_columns(self):
        columns = (
            "ma_lich", "ten_hv", "sdt_hv", "ten_hlv",
            "ngay_tap", "khung_gio", "gio_bat_dau", "gio_ket_thuc", "noi_dung"
        )
        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        col_configs = [
            ("ma_lich", "Mã Lịch", 70, "center"),
            ("ten_hv", "Hội viên", 160, "w"),
            ("sdt_hv", "SĐT", 100, "center"),
            ("ten_hlv", "Huấn luyện viên", 160, "w"),
            ("ngay_tap", "Ngày tập", 100, "center"),
            ("khung_gio", "Khung giờ", 130, "center"),
            ("gio_bat_dau", "Bắt đầu", 80, "center"),
            ("gio_ket_thuc", "Kết thúc", 80, "center"),
            ("noi_dung", "Nội dung bài tập", 220, "w"),
        ]

        for col, heading, width, anchor in col_configs:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=anchor)

    def _build_custom_form(self):
        f = self.form_fields_frame

        # 1. Hội viên
        tk.Label(f, text="Hội viên (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.cbo_hoi_vien = ttk.Combobox(f, state="readonly", font=FONT_BODY, style="Custom.TCombobox")
        self.cbo_hoi_vien.pack(fill="x", pady=(0, 8))

        # 2. HLV
        tk.Label(f, text="Huấn luyện viên phụ trách (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.cbo_hlv = ttk.Combobox(f, state="readonly", font=FONT_BODY, style="Custom.TCombobox")
        self.cbo_hlv.pack(fill="x", pady=(0, 8))

        # 3. Ngày tập
        tk.Label(f, text="Ngày tập (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        if HAS_TKCALENDAR:
            self.txt_ngay_tap = DateEntry(f, date_pattern="yyyy-mm-dd", font=FONT_BODY, background="#FF5722", foreground="white")
        else:
            self.txt_ngay_tap = ttk.Entry(f, font=FONT_BODY, style="Custom.TEntry")
            self.txt_ngay_tap.insert(0, date.today().strftime("%Y-%m-%d"))
        self.txt_ngay_tap.pack(fill="x", pady=(0, 8))

        # 4. Giờ bắt đầu & Giờ kết thúc
        row_time = tk.Frame(f, bg=COLOR_CARD_BG)
        row_time.pack(fill="x", pady=(0, 8))

        # Danh sách các mốc thời gian 30 phút từ 06:00 đến 22:00
        time_options = []
        for h in range(6, 23):
            time_options.append(f"{h:02d}:00")
            if h < 22:
                time_options.append(f"{h:02d}:30")

        f_start = tk.Frame(row_time, bg=COLOR_CARD_BG)
        f_start.pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Label(f_start, text="Giờ bắt đầu (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(0, 2))
        self.cbo_start_time = ttk.Combobox(f_start, values=time_options, font=FONT_BODY, style="Custom.TCombobox")
        self.cbo_start_time.set("08:00")
        self.cbo_start_time.pack(fill="x")

        f_end = tk.Frame(row_time, bg=COLOR_CARD_BG)
        f_end.pack(side="right", fill="x", expand=True, padx=(4, 0))
        tk.Label(f_end, text="Giờ kết thúc (*):", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(0, 2))
        self.cbo_end_time = ttk.Combobox(f_end, values=time_options, font=FONT_BODY, style="Custom.TCombobox")
        self.cbo_end_time.set("09:00")
        self.cbo_end_time.pack(fill="x")

        # 5. Nội dung buổi tập
        tk.Label(f, text="Nội dung / Giáo án buổi tập:", font=FONT_BODY_BOLD, fg=COLOR_TEXT_MAIN, bg=COLOR_CARD_BG).pack(anchor="w", pady=(2, 2))
        self.txt_noi_dung = tk.Text(f, height=4, font=FONT_BODY, relief="solid", bd=1)
        self.txt_noi_dung.pack(fill="x", pady=(0, 8))

    def _load_combobox_data(self):
        ok, hv_opts = database.get_hoi_vien_options()
        if ok:
            self.members_map = {lbl: mid for mid, lbl in hv_opts}
            self.cbo_hoi_vien["values"] = list(self.members_map.keys())

        ok, hlv_opts = database.get_hlv_options(include_none=False)
        if ok:
            self.coaches_map = {lbl: cid for cid, lbl in hlv_opts}
            self.cbo_hlv["values"] = list(self.coaches_map.keys())

    def _get_form_raw(self):
        hv_lbl = self.cbo_hoi_vien.get()
        hlv_lbl = self.cbo_hlv.get()

        ma_hv = self.members_map.get(hv_lbl)
        ma_hlv = self.coaches_map.get(hlv_lbl)
        practice_d = self.txt_ngay_tap.get_date() if HAS_TKCALENDAR else self.txt_ngay_tap.get()

        return {
            "ma_hv": ma_hv,
            "ma_hlv": ma_hlv,
            "ngay_tap": practice_d,
            "gio_bat_dau": self.cbo_start_time.get(),
            "gio_ket_thuc": self.cbo_end_time.get(),
            "noi_dung": self.txt_noi_dung.get("1.0", tk.END).strip()
        }

    def populate_form_from_selection(self, values: Tuple[Any, ...]):
        # ("ma_lich", "ten_hv", "sdt_hv", "ten_hlv", "ngay_tap", "khung_gio", "gio_bat_dau", "gio_ket_thuc", "noi_dung")
        self._load_combobox_data()

        ten_hv = values[1]
        for lbl in self.cbo_hoi_vien["values"]:
            if ten_hv in lbl:
                self.cbo_hoi_vien.set(lbl)
                break

        ten_hlv = values[3]
        for lbl in self.cbo_hlv["values"]:
            if ten_hlv in lbl:
                self.cbo_hlv.set(lbl)
                break

        _, p_date, _ = parse_date(values[4])
        if p_date:
            if HAS_TKCALENDAR:
                self.txt_ngay_tap.set_date(p_date)
            else:
                self.txt_ngay_tap.delete(0, tk.END)
                self.txt_ngay_tap.insert(0, str(p_date))

        self.cbo_start_time.set(str(values[6])[:5])
        self.cbo_end_time.set(str(values[7])[:5])

        self.txt_noi_dung.delete("1.0", tk.END)
        if values[8] and values[8] != "None":
            self.txt_noi_dung.insert(tk.END, values[8])

    def clear_form(self):
        super().clear_form()
        self._load_combobox_data()
        self.cbo_hoi_vien.set("")
        self.cbo_hlv.set("")
        self.cbo_start_time.set("08:00")
        self.cbo_end_time.set("09:00")
        self.txt_noi_dung.delete("1.0", tk.END)

        today = date.today()
        if HAS_TKCALENDAR:
            self.txt_ngay_tap.set_date(today)
        else:
            self.txt_ngay_tap.delete(0, tk.END)
            self.txt_ngay_tap.insert(0, today.strftime("%Y-%m-%d"))

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        ok, rows = database.get_all_lich_tap()
        if not ok:
            self.show_error(f"Không thể tải danh sách lịch tập: {rows}")
            return

        for r in rows:
            start_str = str(r["gio_bat_dau"])[:5]
            end_str = str(r["gio_ket_thuc"])[:5]
            self.tree.insert(
                "",
                "end",
                values=(
                    r["ma_lich"],
                    r["ten_hv"],
                    r["sdt_hv"],
                    r["ten_hlv"],
                    str(r["ngay_tap"]),
                    f"{start_str} - {end_str}",
                    start_str,
                    end_str,
                    r["noi_dung"] or ""
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

        ok, rows = database.search_lich_tap(kw)
        if not ok:
            self.show_error(f"Lỗi tìm kiếm: {rows}")
            return

        for r in rows:
            start_str = str(r["gio_bat_dau"])[:5]
            end_str = str(r["gio_ket_thuc"])[:5]
            self.tree.insert(
                "",
                "end",
                values=(
                    r["ma_lich"],
                    r["ten_hv"],
                    r["sdt_hv"],
                    r["ten_hlv"],
                    str(r["ngay_tap"]),
                    f"{start_str} - {end_str}",
                    start_str,
                    end_str,
                    r["noi_dung"] or ""
                )
            )
        self.update_record_count(len(rows), f"Kết quả cho: '{kw}'")

    def _check_business_rules(self, clean: Dict[str, Any], current_ma_lich: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Logic Agent kiểm duyệt nghiệp vụ thời gian thực:
        1. Kiểm tra xem hội viên có đăng ký đang hoạt động không
        2. Lấy danh sách lịch trong ngày của HLV và Hội viên
        3. Kiểm tra trùng/xung đột khung giờ
        """
        # 1. Ngày tập phải nằm trong thời hạn một gói 'Đang hoạt động' của hội viên
        db_ok, active_subs = database.get_active_dang_ky_of_hv(clean["ma_hv"])
        if not db_ok:
            return False, f"Không thể kiểm tra gói tập của hội viên: {active_subs}"
        cover_ok, cover_err = check_date_within_active_registration(clean["ngay_tap"], active_subs)
        if not cover_ok:
            return False, cover_err

        # 2. Lấy các lịch cùng ngày để đối chiếu
        db_ok, existing_schedules = database.get_lich_tap_by_date_and_targets(
            clean["ngay_tap"],
            clean["ma_hv"],
            clean["ma_hlv"],
            exclude_ma_lich=current_ma_lich
        )
        if not db_ok:
            return False, f"Không thể kiểm tra xung đột lịch: {existing_schedules}"

        # 3. Logic Agent phát hiện xung đột
        has_conflict, err_msg = find_schedule_conflict(
            new_start=clean["gio_bat_dau"],
            new_end=clean["gio_ket_thuc"],
            existing_schedules=existing_schedules,
            current_ma_lich=current_ma_lich
        )
        if has_conflict:
            return False, err_msg

        return True, None

    def on_add(self):
        raw = self._get_form_raw()
        # 1. Validate định dạng cơ bản
        ok, clean, err = validate_lich_tap_form(raw)
        if not ok:
            self.show_error(err)
            return

        # 2. Logic Agent kiểm tra nghiệp vụ trùng lịch
        biz_ok, biz_err = self._check_business_rules(clean)
        if not biz_ok:
            self.show_error(biz_err, title="Cảnh báo trùng lịch / Nghiệp vụ")
            return

        # 3. Database Agent ghi dữ liệu
        db_ok, res = database.insert_lich_tap(clean)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Đặt lịch tập thành công!")
        self.clear_form()
        self.load_data()

    def on_update(self):
        if not self.selected_item_id:
            self.show_error("Vui lòng chọn một lịch tập trong danh sách để cập nhật.")
            return

        raw = self._get_form_raw()
        ok, clean, err = validate_lich_tap_form(raw)
        if not ok:
            self.show_error(err)
            return

        cur_id = int(self.selected_item_id)
        biz_ok, biz_err = self._check_business_rules(clean, current_ma_lich=cur_id)
        if not biz_ok:
            self.show_error(biz_err, title="Cảnh báo trùng lịch / Nghiệp vụ")
            return

        db_ok, res = database.update_lich_tap(cur_id, clean)
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Cập nhật lịch tập thành công!")
        self.clear_form()
        self.load_data()

    def on_delete(self):
        if not self.selected_item_id:
            self.show_error("Vui lòng chọn một lịch tập để xóa.")
            return

        if not self.ask_confirm(f"Bạn có chắc chắn muốn hủy lịch tập mã #{self.selected_item_id} không?"):
            return

        db_ok, res = database.delete_lich_tap(int(self.selected_item_id))
        if not db_ok:
            self.show_error(res)
            return

        self.show_info("Đã xóa lịch tập thành công!")
        self.clear_form()
        self.load_data()
