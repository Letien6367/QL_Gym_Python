# ==========================================
# LOGIC & VALIDATION AGENT
# ==========================================
"""
Đại lý Nghiệp vụ & Kiểm duyệt (Logic & Validation Agent).
Tuân thủ AGENTS.md:
- Không phụ thuộc vào Tkinter hoặc Database
- Kiểm tra tính hợp lệ dữ liệu đầu vào (Validation)
- Xử lý nghiệp vụ thời gian thực (Cộng tháng, tính ngày hết hạn, kiểm tra trùng lịch)
- Băm và xác thực mật khẩu SHA-256
"""

from datetime import date, datetime, time, timedelta
import calendar
import hashlib
import hmac
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union


# -------------------------------------------------------------
# 1. HÀM KIỂM TRA ĐỊNH DẠNG CƠ BẢN
# -------------------------------------------------------------

def require_fields(data: Dict[str, Any], field_labels: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """
    Kiểm tra các trường bắt buộc không được để trống.
    field_labels: map key -> nhãn hiển thị cho người dùng, ví dụ: {"ho_ten": "Họ và tên"}
    """
    for key, label in field_labels.items():
        val = data.get(key)
        if val is None or (isinstance(val, str) and not val.strip()):
            return False, f"Vui lòng nhập: {label}."
    return True, None


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Kiểm tra số điện thoại: chỉ chứa số, bắt đầu bằng 0, độ dài 10 số (phổ biến tại VN).
    """
    if not phone:
        return False, "Số điện thoại không được để trống."
    cleaned = phone.strip()
    if not re.fullmatch(r"0\d{9}", cleaned):
        return False, "Số điện thoại không hợp lệ (phải bắt đầu bằng số 0 và gồm đúng 10 chữ số)."
    return True, None


def validate_email(email: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Email có thể để trống. Nếu có nhập, phải đúng định dạng chuẩn.
    """
    if not email or not email.strip():
        return True, None
    cleaned = email.strip()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.fullmatch(pattern, cleaned):
        return False, "Định dạng Email không hợp lệ (ví dụ: example@domain.com)."
    return True, None


def parse_date(date_input: Union[str, date, datetime]) -> Tuple[bool, Optional[date], Optional[str]]:
    """
    Chuyển đổi chuỗi ngày sang đối tượng date (hỗ trợ YYYY-MM-DD và DD/MM/YYYY).
    """
    if isinstance(date_input, date) and not isinstance(date_input, datetime):
        return True, date_input, None
    if isinstance(date_input, datetime):
        return True, date_input.date(), None
    if not date_input or not str(date_input).strip():
        return False, None, "Ngày không được để trống."

    s = str(date_input).strip()
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
    for fmt in formats:
        try:
            parsed = datetime.strptime(s, fmt).date()
            return True, parsed, None
        except ValueError:
            continue
    return False, None, f"Ngày '{s}' không đúng định dạng (hợp lệ: YYYY-MM-DD hoặc DD/MM/YYYY)."


def parse_time(time_input: Union[str, time]) -> Tuple[bool, Optional[time], Optional[str]]:
    """
    Chuyển đổi chuỗi giờ sang time (hỗ trợ HH:MM và HH:MM:SS).
    """
    if isinstance(time_input, time):
        return True, time_input, None
    if not time_input or not str(time_input).strip():
        return False, None, "Giờ không được để trống."

    s = str(time_input).strip()
    formats = ["%H:%M:%S", "%H:%M"]
    for fmt in formats:
        try:
            parsed = datetime.strptime(s, fmt).time()
            return True, parsed, None
        except ValueError:
            continue
    return False, None, f"Giờ '{s}' không đúng định dạng (hợp lệ: HH:MM hoặc HH:MM:SS)."


def validate_positive_number(val: Any, label: str) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Kiểm tra số thực dương (> 0).
    """
    try:
        num = float(str(val).replace(",", "").strip())
        if num <= 0:
            return False, None, f"{label} phải lớn hơn 0."
        return True, num, None
    except (ValueError, TypeError):
        return False, None, f"{label} phải là số hợp lệ."


def validate_positive_int(val: Any, label: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Kiểm tra số nguyên dương (> 0).
    """
    try:
        num = int(str(val).strip())
        if num <= 0:
            return False, None, f"{label} phải là số nguyên lớn hơn 0."
        return True, num, None
    except (ValueError, TypeError):
        return False, None, f"{label} phải là số nguyên hợp lệ."


def validate_birth_date(birth_date: date) -> Tuple[bool, Optional[str]]:
    """
    Kiểm tra ngày sinh: không ở tương lai, độ tuổi hợp lý (10 - 100 tuổi).
    """
    today = date.today()
    if birth_date > today:
        return False, "Ngày sinh không thể ở tương lai."
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    if age < 10:
        return False, "Hội viên / HLV phải từ 10 tuổi trở lên."
    if age > 100:
        return False, "Độ tuổi không hợp lý (lớn hơn 100 tuổi)."
    return True, None


# -------------------------------------------------------------
# 2. XỬ LÝ NGHIỆP VỤ THỜI GIAN THỰC & TÍNH TOÁN
# -------------------------------------------------------------

def add_months(source_date: date, months: int) -> date:
    """
    Cộng số tháng vào ngày đã cho, tự động xử lý ngày cuối tháng (ví dụ: 31/01 + 1 tháng -> 28 hoặc 29/02).
    """
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def calc_end_date(start_date: date, duration_months: int) -> date:
    """
    Tính ngày kết thúc gói tập: ngày bắt đầu + thời hạn (tháng).
    """
    return add_months(start_date, duration_months)


def compute_status(end_date: date, current_date: Optional[date] = None) -> str:
    """
    Tự động xác định trạng thái dựa trên thời gian thực:
    - Nếu end_date >= current_date: 'Đang hoạt động'
    - Ngược lại: 'Đã hết hạn'
    """
    if current_date is None:
        current_date = date.today()
    return "Đang hoạt động" if end_date >= current_date else "Đã hết hạn"


def validate_time_slot(
    start_t: time,
    end_t: time,
    open_t: time = time(6, 0),
    close_t: time = time(22, 0)
) -> Tuple[bool, Optional[str]]:
    """
    Kiểm tra khung giờ tập luyện:
    - Nằm trong giờ mở cửa (mặc định 06:00 - 22:00)
    - Giờ kết thúc > giờ bắt đầu
    - Thời lượng tối thiểu 15 phút, tối đa 4 tiếng
    """
    if end_t <= start_t:
        return False, "Giờ kết thúc phải sau giờ bắt đầu."

    if start_t < open_t or end_t > close_t:
        return False, f"Khung giờ tập phải nằm trong khoảng hoạt động của phòng ({open_t.strftime('%H:%M')} - {close_t.strftime('%H:%M')})."

    # Tính thời lượng tính bằng phút
    start_dt = datetime.combine(date.min, start_t)
    end_dt = datetime.combine(date.min, end_t)
    duration_min = (end_dt - start_dt).total_seconds() / 60

    if duration_min < 15:
        return False, "Thời lượng buổi tập tối thiểu là 15 phút."
    if duration_min > 240:
        return False, "Thời lượng 1 buổi tập không được vượt quá 4 tiếng."

    return True, None


def _coerce_time(value: Any) -> Optional[time]:
    """Chấp nhận time, timedelta (MySQL TIME) hoặc chuỗi 'HH:MM[:SS]' -> time."""
    if isinstance(value, time):
        return value
    if isinstance(value, timedelta):
        secs = int(value.total_seconds()) % 86400
        return time(secs // 3600, (secs % 3600) // 60, secs % 60)
    if isinstance(value, str):
        _, parsed, _ = parse_time(value)
        return parsed
    return None


def find_schedule_conflict(
    new_start: time,
    new_end: time,
    existing_schedules: List[Dict[str, Any]],
    current_ma_lich: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Kiểm tra trùng lịch tập.
    existing_schedules là danh sách các dict chứa:
    - ma_lich: int
    - gio_bat_dau: time
    - gio_ket_thuc: time
    - ten_hv: str
    - ten_hlv: str
    - role_conflict: 'HLV' hoặc 'Hội viên'

    Quy tắc overlap: hai khung giờ [A, B] và [C, D] giao nhau khi: A < D và B > C.
    (Chạm biên ví dụ A == D hoặc B == C KHÔNG bị coi là trùng).
    """
    for item in existing_schedules:
        if current_ma_lich is not None and item.get("ma_lich") == current_ma_lich:
            continue

        ex_start = _coerce_time(item["gio_bat_dau"])
        ex_end = _coerce_time(item["gio_ket_thuc"])

        if not ex_start or not ex_end:
            continue

        # Kiểm tra giao nhau
        if new_start < ex_end and new_end > ex_start:
            role = item.get("role_conflict", "Đối tượng")
            name = item.get("name", "")
            return True, (
                f"Trùng lịch! {role} '{name}' đã có lịch từ "
                f"{ex_start.strftime('%H:%M')} đến {ex_end.strftime('%H:%M')}."
            )

    return False, None


def find_registration_overlap(
    new_start: date,
    new_end: date,
    existing_registrations: List[Dict[str, Any]]
) -> Tuple[bool, Optional[str]]:
    """
    Một hội viên không được có 2 đăng ký 'Đang hoạt động' chồng thời gian.
    Hai khoảng [A, B] và [C, D] chồng nhau khi A <= D và B >= C.
    """
    for reg in existing_registrations:
        _, r_start, _ = parse_date(reg["ngay_bat_dau"])
        _, r_end, _ = parse_date(reg["ngay_ket_thuc"])
        if not r_start or not r_end:
            continue
        if new_start <= r_end and new_end >= r_start:
            return True, (
                f"Hội viên đã có gói đang hoạt động (mã ĐK #{reg.get('ma_dk', '')}) "
                f"từ {r_start.strftime('%d/%m/%Y')} đến "
                f"{r_end.strftime('%d/%m/%Y')}, trùng thời gian với đăng ký mới."
            )
    return False, None


def check_date_within_active_registration(
    practice_date: date,
    active_registrations: List[Dict[str, Any]]
) -> Tuple[bool, Optional[str]]:
    """Ngày tập phải nằm trong thời hạn của ít nhất một gói 'Đang hoạt động' của hội viên."""
    if not active_registrations:
        return False, "Hội viên này hiện không có gói tập nào 'Đang hoạt động'. Vui lòng đăng ký gói trước khi xếp lịch!"
    for reg in active_registrations:
        _, r_start, _ = parse_date(reg["ngay_bat_dau"])
        _, r_end, _ = parse_date(reg["ngay_ket_thuc"])
        if not r_start or not r_end:
            continue
        if r_start <= practice_date <= r_end:
            return True, None
    return False, (
        f"Ngày tập {practice_date.strftime('%d/%m/%Y')} nằm ngoài thời hạn gói tập đang hoạt động của hội viên."
    )


def check_admin_safeguard(
    target_is_active_admin: bool,
    new_role: str,
    new_status: str,
    other_active_admins: int,
    is_delete: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Bảo vệ Admin: không cho hạ quyền / khoá / xoá Admin hoạt động cuối cùng.
    """
    if not target_is_active_admin:
        return True, None
    still_active_admin = (not is_delete) and new_role == "Admin" and new_status == "Đang hoạt động"
    if not still_active_admin and other_active_admins <= 0:
        return False, "Đây là Admin đang hoạt động cuối cùng. Không thể hạ quyền, khoá hoặc xoá tài khoản này!"
    return True, None


# -------------------------------------------------------------
# 3. BẢO MẬT & MẬT KHẨU
# -------------------------------------------------------------

def hash_password(password: str, use_salt: bool = True) -> str:
    """
    Tạo chuỗi băm mật khẩu.
    - use_salt=True: Dùng PBKDF2-HMAC-SHA256 với salt ngẫu nhiên 16 bytes (chuẩn OWASP).
      Định dạng lưu trữ: pbkdf2$sha256$100000$<salt_hex>$<key_hex>
    - use_salt=False: Trả về chuỗi SHA-256 thuần (dùng khi cần tương thích trực tiếp).
    """
    if not use_salt:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"pbkdf2$sha256$100000${salt.hex()}${key.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Xác thực mật khẩu hỗ trợ cả PBKDF2 có salt và SHA-256 hex thường (tương thích ngược).
    Dùng hmac.compare_digest để chống tấn công Timing Attack.
    """
    if not stored_hash or not plain_password:
        return False

    # Trường hợp 1: Mật khẩu băm chuẩn PBKDF2
    if stored_hash.startswith("pbkdf2$"):
        try:
            parts = stored_hash.split("$")
            if len(parts) == 5:
                _, algo, iterations_str, salt_hex, key_hex = parts
                salt = bytes.fromhex(salt_hex)
                iterations = int(iterations_str)
                derived = hashlib.pbkdf2_hmac(algo, plain_password.encode("utf-8"), salt, iterations).hex()
                return hmac.compare_digest(derived, key_hex)
        except Exception:
            return False

    # Trường hợp 2: Mật khẩu băm SHA-256 thuần (dữ liệu ban đầu từ SQL)
    computed_sha256 = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(computed_sha256, stored_hash)


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """Kiểm tra độ mạnh mật khẩu: tối thiểu 6 ký tự."""
    if not password or len(password.strip()) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự."
    return True, None


# -------------------------------------------------------------
# 4. GÓI KIỂM DUYỆT THEO TỪNG FORM (UI GỌI TRỰC TIẾP)
# -------------------------------------------------------------

def validate_hoi_vien_form(form: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Kiểm duyệt dữ liệu form Hội viên."""
    ok, err = require_fields(form, {
        "ho_ten": "Họ và tên",
        "ngay_sinh": "Ngày sinh",
        "gioi_tinh": "Giới tính",
        "so_dien_thoai": "Số điện thoại",
        "ngay_tham_gia": "Ngày tham gia"
    })
    if not ok:
        return False, None, err

    ok, err = validate_phone(form["so_dien_thoai"])
    if not ok:
        return False, None, err

    ok, err = validate_email(form.get("email"))
    if not ok:
        return False, None, err

    ok, dob, err = parse_date(form["ngay_sinh"])
    if not ok:
        return False, None, err

    ok, err = validate_birth_date(dob)
    if not ok:
        return False, None, err

    ok, join_date, err = parse_date(form["ngay_tham_gia"])
    if not ok:
        return False, None, err

    clean = {
        "ho_ten": form["ho_ten"].strip(),
        "ngay_sinh": dob,
        "gioi_tinh": form["gioi_tinh"].strip(),
        "so_dien_thoai": form["so_dien_thoai"].strip(),
        "email": form.get("email", "").strip() or None,
        "dia_chi": form.get("dia_chi", "").strip() or None,
        "ngay_tham_gia": join_date
    }
    return True, clean, None


def validate_hlv_form(form: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Kiểm duyệt dữ liệu form Huấn luyện viên."""
    ok, err = require_fields(form, {
        "ho_ten": "Họ và tên",
        "ngay_sinh": "Ngày sinh",
        "gioi_tinh": "Giới tính",
        "so_dien_thoai": "Số điện thoại",
        "chuyen_mon": "Chuyên môn"
    })
    if not ok:
        return False, None, err

    ok, err = validate_phone(form["so_dien_thoai"])
    if not ok:
        return False, None, err

    ok, dob, err = parse_date(form["ngay_sinh"])
    if not ok:
        return False, None, err

    ok, err = validate_birth_date(dob)
    if not ok:
        return False, None, err

    clean = {
        "ho_ten": form["ho_ten"].strip(),
        "ngay_sinh": dob,
        "gioi_tinh": form["gioi_tinh"].strip(),
        "so_dien_thoai": form["so_dien_thoai"].strip(),
        "chuyen_mon": form["chuyen_mon"].strip()
    }
    return True, clean, None


def validate_goi_tap_form(form: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Kiểm duyệt dữ liệu form Gói tập."""
    ok, err = require_fields(form, {
        "ten_goi": "Tên gói tập",
        "thoi_han": "Thời hạn (tháng)",
        "gia": "Giá gói tập"
    })
    if not ok:
        return False, None, err

    ok, thoi_han, err = validate_positive_int(form["thoi_han"], "Thời hạn")
    if not ok:
        return False, None, err

    ok, gia, err = validate_positive_number(form["gia"], "Giá gói tập")
    if not ok:
        return False, None, err

    clean = {
        "ten_goi": form["ten_goi"].strip(),
        "thoi_han": thoi_han,
        "gia": gia,
        "mo_ta": form.get("mo_ta", "").strip() or None
    }
    return True, clean, None


def validate_dang_ky_form(form: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Kiểm duyệt dữ liệu form Đăng ký gói tập."""
    ok, err = require_fields(form, {
        "ma_hv": "Hội viên",
        "ma_goi": "Gói tập",
        "ngay_dang_ky": "Ngày đăng ký",
        "ngay_bat_dau": "Ngày bắt đầu",
        "thoi_han": "Thời hạn gói tập"
    })
    if not ok:
        return False, None, err

    try:
        ma_hv = int(form["ma_hv"])
        ma_goi = int(form["ma_goi"])
        ma_hlv = int(form["ma_hlv"]) if form.get("ma_hlv") not in (None, "", "None") else None
    except (ValueError, TypeError):
        return False, None, "Mã hội viên hoặc gói tập không hợp lệ."

    ok, reg_date, err = parse_date(form["ngay_dang_ky"])
    if not ok:
        return False, None, err

    ok, start_date, err = parse_date(form["ngay_bat_dau"])
    if not ok:
        return False, None, err

    ok, duration, err = validate_positive_int(form["thoi_han"], "Thời hạn")
    if not ok:
        return False, None, err

    end_date = calc_end_date(start_date, duration)
    status = compute_status(end_date)

    clean = {
        "ma_hv": ma_hv,
        "ma_goi": ma_goi,
        "ma_hlv": ma_hlv,
        "ngay_dang_ky": reg_date,
        "ngay_bat_dau": start_date,
        "ngay_ket_thuc": end_date,
        "trang_thai": form.get("trang_thai") or status
    }
    return True, clean, None


def validate_thanh_toan_form(form: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Kiểm duyệt dữ liệu form Thanh toán."""
    ok, err = require_fields(form, {
        "ma_dk": "Mã đăng ký",
        "so_tien": "Số tiền thanh toán",
        "ngay_thanh_toan": "Ngày thanh toán",
        "phuong_thuc": "Phương thức thanh toán"
    })
    if not ok:
        return False, None, err

    try:
        ma_dk = int(form["ma_dk"])
    except (ValueError, TypeError):
        return False, None, "Mã đăng ký không hợp lệ."

    ok, so_tien, err = validate_positive_number(form["so_tien"], "Số tiền")
    if not ok:
        return False, None, err

    ok, pay_date, err = parse_date(form["ngay_thanh_toan"])
    if not ok:
        return False, None, err

    clean = {
        "ma_dk": ma_dk,
        "so_tien": so_tien,
        "ngay_thanh_toan": pay_date,
        "phuong_thuc": form["phuong_thuc"].strip()
    }
    return True, clean, None


def validate_lich_tap_form(form: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Kiểm duyệt dữ liệu form Lịch tập."""
    ok, err = require_fields(form, {
        "ma_hv": "Hội viên",
        "ma_hlv": "Huấn luyện viên",
        "ngay_tap": "Ngày tập",
        "gio_bat_dau": "Giờ bắt đầu",
        "gio_ket_thuc": "Giờ kết thúc"
    })
    if not ok:
        return False, None, err

    try:
        ma_hv = int(form["ma_hv"])
        ma_hlv = int(form["ma_hlv"])
    except (ValueError, TypeError):
        return False, None, "Mã hội viên hoặc huấn luyện viên không hợp lệ."

    ok, practice_date, err = parse_date(form["ngay_tap"])
    if not ok:
        return False, None, err

    ok, start_t, err = parse_time(form["gio_bat_dau"])
    if not ok:
        return False, None, err

    ok, end_t, err = parse_time(form["gio_ket_thuc"])
    if not ok:
        return False, None, err

    ok, err = validate_time_slot(start_t, end_t)
    if not ok:
        return False, None, err

    clean = {
        "ma_hv": ma_hv,
        "ma_hlv": ma_hlv,
        "ngay_tap": practice_date,
        "gio_bat_dau": start_t,
        "gio_ket_thuc": end_t,
        "noi_dung": form.get("noi_dung", "").strip() or None
    }
    return True, clean, None


def validate_nguoi_dung_form(form: Dict[str, Any], is_create: bool = True) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Kiểm duyệt dữ liệu form Người dùng."""
    required = {
        "ten_dang_nhap": "Tên đăng nhập",
        "ho_ten": "Họ và tên",
        "vai_tro": "Vai trò"
    }
    if is_create:
        required["mat_khau"] = "Mật khẩu"

    ok, err = require_fields(form, required)
    if not ok:
        return False, None, err

    username = form["ten_dang_nhap"].strip()
    if not re.fullmatch(r"^[a-zA-Z0-9_]{3,30}$", username):
        return False, None, "Tên đăng nhập chỉ gồm chữ cái, số, gạch dưới và dài từ 3-30 ký tự."

    clean = {
        "ten_dang_nhap": username,
        "ho_ten": form["ho_ten"].strip(),
        "vai_tro": form["vai_tro"].strip(),
        "trang_thai": form.get("trang_thai", "Đang hoạt động").strip()
    }

    if is_create or form.get("mat_khau"):
        pwd = form["mat_khau"].strip()
        ok, err = validate_password_strength(pwd)
        if not ok:
            return False, None, err
        clean["mat_khau"] = hash_password(pwd)

    return True, clean, None
