# ==========================================
# DATABASE AGENT
# ==========================================
"""
Đại lý Cơ sở dữ liệu (Database Agent).
Tuân thủ AGENTS.md:
- Chịu trách nhiệm duy nhất về việc giao tiếp với MySQL
- Thực thi CRUD qua các hàm với Parameterized Queries (%s)
- Bắt và chuyển dịch lỗi MySQL sang tiếng Việt thân thiện
- Trả về tuple: (success: bool, result_or_error_message: Any)
"""

from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple
import mysql.connector
from mysql.connector import Error, errorcode
from config import DB_CONFIG


# -------------------------------------------------------------
# 1. KẾT NỐI VÀ XỬ LÝ LỖI DÙNG CHUNG
# -------------------------------------------------------------

def get_connection():
    """Khởi tạo kết nối tới MySQL theo config."""
    return mysql.connector.connect(**DB_CONFIG)


def _translate_error(err: Error) -> str:
    """Dịch mã lỗi MySQL sang thông báo tiếng Việt dễ hiểu."""
    code = err.errno
    msg = str(err.msg) if hasattr(err, "msg") else str(err)

    if code == errorcode.ER_DUP_ENTRY:
        if "so_dien_thoai" in msg:
            return "Lỗi: Số điện thoại này đã được đăng ký trong hệ thống."
        if "ten_goi" in msg:
            return "Lỗi: Tên gói tập này đã tồn tại."
        if "ten_dang_nhap" in msg:
            return "Lỗi: Tên đăng nhập này đã được sử dụng."
        return "Lỗi: Dữ liệu bị trùng lặp khóa duy nhất (đã tồn tại trong hệ thống)."

    if code == errorcode.ER_ROW_IS_REFERENCED_2:
        return "Lỗi: Không thể xóa bản ghi này vì đang được liên kết sử dụng ở bảng khác (ví dụ: đang có đăng ký hoặc lịch tập)."

    if code == errorcode.ER_NO_REFERENCED_ROW_2:
        return "Lỗi: Dữ liệu liên kết không tồn tại (Mã hội viên, HLV hoặc Gói tập không hợp lệ)."

    if code == errorcode.ER_CHECK_CONSTRAINT_VIOLATED:
        return "Lỗi: Dữ liệu vi phạm ràng buộc kiểm tra (ví dụ: giá > 0, thời hạn > 0 hoặc giờ kết thúc > giờ bắt đầu)."

    if code in (errorcode.CR_CONN_HOST_ERROR, errorcode.CR_CONNECTION_ERROR):
        return f"Lỗi: Không thể kết nối tới máy chủ MySQL tại {DB_CONFIG.get('host')}:{DB_CONFIG.get('port')}. Vui lòng bật MySQL!"

    if code == errorcode.ER_ACCESS_DENIED_ERROR:
        return "Lỗi: Sai tên đăng nhập hoặc mật khẩu kết nối cơ sở dữ liệu MySQL (kiểm tra config.py)."

    if code == errorcode.ER_BAD_DB_ERROR:
        return f"Lỗi: Cơ sở dữ liệu '{DB_CONFIG.get('database')}' không tồn tại. Vui lòng import file SQL trước."

    return f"Lỗi CSDL ({code}): {msg}"


def _timedelta_to_time(value: timedelta) -> time:
    """mysql-connector trả cột TIME dưới dạng timedelta; đổi về datetime.time."""
    total_seconds = int(value.total_seconds()) % 86400
    return time(total_seconds // 3600, (total_seconds % 3600) // 60, total_seconds % 60)


def _normalize_row(row: Any) -> Any:
    """Chuẩn hoá các giá trị timedelta trong 1 bản ghi (dict) thành time."""
    if isinstance(row, dict):
        return {
            k: (_timedelta_to_time(v) if isinstance(v, timedelta) else v)
            for k, v in row.items()
        }
    return row


def _execute_query(
    sql: str,
    params: tuple = (),
    fetch: Optional[str] = "all"
) -> Tuple[bool, Any]:
    """
    Thực thi truy vấn an toàn:
    - fetch='all': trả về toàn bộ danh sách bản ghi
    - fetch='one': trả về 1 bản ghi
    - fetch=None: cho lệnh INSERT, UPDATE, DELETE (trả về lastrowid hoặc rowcount)
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)

        if fetch == "all":
            result = [_normalize_row(r) for r in cursor.fetchall()]
            return True, result
        elif fetch == "one":
            result = _normalize_row(cursor.fetchone())
            return True, result
        else:
            conn.commit()
            last_id = cursor.lastrowid
            affected = cursor.rowcount
            return True, {"last_id": last_id, "rowcount": affected}
    except Error as e:
        if conn:
            conn.rollback()
        return False, _translate_error(e)
    except Exception as ex:
        if conn:
            conn.rollback()
        return False, f"Lỗi hệ thống: {str(ex)}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def test_connection() -> Tuple[bool, str]:
    """Kiểm tra trạng thái kết nối tới CSDL."""
    ok, res = _execute_query("SELECT 1 AS check_val", fetch="one")
    if ok:
        return True, "Kết nối cơ sở dữ liệu MySQL thành công!"
    return False, str(res)


# -------------------------------------------------------------
# 2. XÁC THỰC NGƯỜI DÙNG (AUTHENTICATION)
# -------------------------------------------------------------

def get_user_by_username(username: str) -> Tuple[bool, Any]:
    sql = "SELECT ma_nd, ten_dang_nhap, mat_khau, ho_ten, vai_tro, trang_thai FROM nguoi_dung WHERE ten_dang_nhap = %s"
    return _execute_query(sql, (username,), fetch="one")


# -------------------------------------------------------------
# 3. QUẢN LÝ HỘI VIÊN (MEMBER)
# -------------------------------------------------------------

def get_all_hoi_vien() -> Tuple[bool, Any]:
    sql = """
        SELECT ma_hv, ho_ten, ngay_sinh, gioi_tinh, so_dien_thoai, email, dia_chi, ngay_tham_gia
        FROM hoi_vien
        ORDER BY ma_hv DESC
    """
    return _execute_query(sql, fetch="all")


def search_hoi_vien(keyword: str) -> Tuple[bool, Any]:
    kw = f"%{keyword.strip()}%"
    sql = """
        SELECT ma_hv, ho_ten, ngay_sinh, gioi_tinh, so_dien_thoai, email, dia_chi, ngay_tham_gia
        FROM hoi_vien
        WHERE ho_ten LIKE %s OR so_dien_thoai LIKE %s OR email LIKE %s
        ORDER BY ma_hv DESC
    """
    return _execute_query(sql, (kw, kw, kw), fetch="all")


def insert_hoi_vien(data: Dict[str, Any]) -> Tuple[bool, Any]:
    sql = """
        INSERT INTO hoi_vien (ho_ten, ngay_sinh, gioi_tinh, so_dien_thoai, email, dia_chi, ngay_tham_gia)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        data["ho_ten"], data["ngay_sinh"], data["gioi_tinh"],
        data["so_dien_thoai"], data.get("email"), data.get("dia_chi"), data["ngay_tham_gia"]
    )
    return _execute_query(sql, params, fetch=None)


def update_hoi_vien(ma_hv: int, data: Dict[str, Any]) -> Tuple[bool, Any]:
    sql = """
        UPDATE hoi_vien
        SET ho_ten = %s, ngay_sinh = %s, gioi_tinh = %s, so_dien_thoai = %s,
            email = %s, dia_chi = %s, ngay_tham_gia = %s
        WHERE ma_hv = %s
    """
    params = (
        data["ho_ten"], data["ngay_sinh"], data["gioi_tinh"],
        data["so_dien_thoai"], data.get("email"), data.get("dia_chi"),
        data["ngay_tham_gia"], ma_hv
    )
    return _execute_query(sql, params, fetch=None)


def delete_hoi_vien(ma_hv: int) -> Tuple[bool, Any]:
    sql = "DELETE FROM hoi_vien WHERE ma_hv = %s"
    return _execute_query(sql, (ma_hv,), fetch=None)


def get_hoi_vien_options() -> Tuple[bool, List[Tuple[int, str]]]:
    """Trả về danh sách [(ma_hv, 'Mã - Họ tên (SĐT)')] cho Combobox."""
    ok, rows = get_all_hoi_vien()
    if not ok:
        return False, rows
    options = [(r["ma_hv"], f"#{r['ma_hv']} - {r['ho_ten']} ({r['so_dien_thoai']})") for r in rows]
    return True, options


# -------------------------------------------------------------
# 4. QUẢN LÝ HUẤN LUYỆN VIÊN (COACH)
# -------------------------------------------------------------

def get_all_hlv() -> Tuple[bool, Any]:
    sql = """
        SELECT ma_hlv, ho_ten, ngay_sinh, gioi_tinh, so_dien_thoai, chuyen_mon
        FROM huan_luyen_vien
        ORDER BY ma_hlv DESC
    """
    return _execute_query(sql, fetch="all")


def search_hlv(keyword: str) -> Tuple[bool, Any]:
    kw = f"%{keyword.strip()}%"
    sql = """
        SELECT ma_hlv, ho_ten, ngay_sinh, gioi_tinh, so_dien_thoai, chuyen_mon
        FROM huan_luyen_vien
        WHERE ho_ten LIKE %s OR so_dien_thoai LIKE %s OR chuyen_mon LIKE %s
        ORDER BY ma_hlv DESC
    """
    return _execute_query(sql, (kw, kw, kw), fetch="all")


def insert_hlv(data: Dict[str, Any]) -> Tuple[bool, Any]:
    sql = """
        INSERT INTO huan_luyen_vien (ho_ten, ngay_sinh, gioi_tinh, so_dien_thoai, chuyen_mon)
        VALUES (%s, %s, %s, %s, %s)
    """
    params = (
        data["ho_ten"], data["ngay_sinh"], data["gioi_tinh"],
        data["so_dien_thoai"], data["chuyen_mon"]
    )
    return _execute_query(sql, params, fetch=None)


def update_hlv(ma_hlv: int, data: Dict[str, Any]) -> Tuple[bool, Any]:
    sql = """
        UPDATE huan_luyen_vien
        SET ho_ten = %s, ngay_sinh = %s, gioi_tinh = %s, so_dien_thoai = %s, chuyen_mon = %s
        WHERE ma_hlv = %s
    """
    params = (
        data["ho_ten"], data["ngay_sinh"], data["gioi_tinh"],
        data["so_dien_thoai"], data["chuyen_mon"], ma_hlv
    )
    return _execute_query(sql, params, fetch=None)


def delete_hlv(ma_hlv: int) -> Tuple[bool, Any]:
    sql = "DELETE FROM huan_luyen_vien WHERE ma_hlv = %s"
    return _execute_query(sql, (ma_hlv,), fetch=None)


def get_hlv_options(include_none: bool = False) -> Tuple[bool, List[Tuple[Optional[int], str]]]:
    """Trả về danh sách [(ma_hlv, 'Mã - Họ tên (Chuyên môn)')] cho Combobox."""
    ok, rows = get_all_hlv()
    if not ok:
        return False, rows
    options = []
    if include_none:
        options.append((None, "— Không thuê Huấn luyện viên —"))
    options.extend([(r["ma_hlv"], f"#{r['ma_hlv']} - {r['ho_ten']} ({r['chuyen_mon']})") for r in rows])
    return True, options


# -------------------------------------------------------------
# 5. QUẢN LÝ GÓI TẬP (PACKAGE)
# -------------------------------------------------------------

def get_all_goi_tap() -> Tuple[bool, Any]:
    sql = "SELECT ma_goi, ten_goi, thoi_han, gia, mo_ta FROM goi_tap ORDER BY ma_goi ASC"
    return _execute_query(sql, fetch="all")


def search_goi_tap(keyword: str) -> Tuple[bool, Any]:
    kw = f"%{keyword.strip()}%"
    sql = """
        SELECT ma_goi, ten_goi, thoi_han, gia, mo_ta
        FROM goi_tap
        WHERE ten_goi LIKE %s OR mo_ta LIKE %s
        ORDER BY ma_goi ASC
    """
    return _execute_query(sql, (kw, kw), fetch="all")


def get_goi_tap_by_id(ma_goi: int) -> Tuple[bool, Any]:
    sql = "SELECT ma_goi, ten_goi, thoi_han, gia, mo_ta FROM goi_tap WHERE ma_goi = %s"
    return _execute_query(sql, (ma_goi,), fetch="one")


def insert_goi_tap(data: Dict[str, Any]) -> Tuple[bool, Any]:
    sql = "INSERT INTO goi_tap (ten_goi, thoi_han, gia, mo_ta) VALUES (%s, %s, %s, %s)"
    params = (data["ten_goi"], data["thoi_han"], data["gia"], data.get("mo_ta"))
    return _execute_query(sql, params, fetch=None)


def update_goi_tap(ma_goi: int, data: Dict[str, Any]) -> Tuple[bool, Any]:
    sql = "UPDATE goi_tap SET ten_goi = %s, thoi_han = %s, gia = %s, mo_ta = %s WHERE ma_goi = %s"
    params = (data["ten_goi"], data["thoi_han"], data["gia"], data.get("mo_ta"), ma_goi)
    return _execute_query(sql, params, fetch=None)


def delete_goi_tap(ma_goi: int) -> Tuple[bool, Any]:
    sql = "DELETE FROM goi_tap WHERE ma_goi = %s"
    return _execute_query(sql, (ma_goi,), fetch=None)


def get_goi_tap_options() -> Tuple[bool, List[Dict[str, Any]]]:
    """Trả về danh sách gói tập đầy đủ thông tin để bind vào Combobox."""
    ok, rows = get_all_goi_tap()
    if not ok:
        return False, rows
    return True, rows


# -------------------------------------------------------------
# 6. QUẢN LÝ ĐĂNG KÝ (REGISTRATION)
# -------------------------------------------------------------

def get_all_dang_ky() -> Tuple[bool, Any]:
    sql = """
        SELECT dk.ma_dk, dk.ma_hv, hv.ho_ten AS ten_hv, hv.so_dien_thoai AS sdt_hv,
               dk.ma_goi, gt.ten_goi, gt.gia AS gia_goi, gt.thoi_han,
               dk.ma_hlv, COALESCE(hlv.ho_ten, 'Không có') AS ten_hlv,
               dk.ngay_dang_ky, dk.ngay_bat_dau, dk.ngay_ket_thuc, dk.trang_thai
        FROM dang_ky dk
        JOIN hoi_vien hv ON dk.ma_hv = hv.ma_hv
        JOIN goi_tap gt ON dk.ma_goi = gt.ma_goi
        LEFT JOIN huan_luyen_vien hlv ON dk.ma_hlv = hlv.ma_hlv
        ORDER BY dk.ma_dk DESC
    """
    return _execute_query(sql, fetch="all")


def search_dang_ky(keyword: str, trang_thai: Optional[str] = None) -> Tuple[bool, Any]:
    kw = f"%{keyword.strip()}%"
    conditions = ["(hv.ho_ten LIKE %s OR hv.so_dien_thoai LIKE %s OR gt.ten_goi LIKE %s)"]
    params = [kw, kw, kw]

    if trang_thai and trang_thai != "Tất cả":
        conditions.append("dk.trang_thai = %s")
        params.append(trang_thai)

    where_clause = " WHERE " + " AND ".join(conditions)
    sql = f"""
        SELECT dk.ma_dk, dk.ma_hv, hv.ho_ten AS ten_hv, hv.so_dien_thoai AS sdt_hv,
               dk.ma_goi, gt.ten_goi, gt.gia AS gia_goi, gt.thoi_han,
               dk.ma_hlv, COALESCE(hlv.ho_ten, 'Không có') AS ten_hlv,
               dk.ngay_dang_ky, dk.ngay_bat_dau, dk.ngay_ket_thuc, dk.trang_thai
        FROM dang_ky dk
        JOIN hoi_vien hv ON dk.ma_hv = hv.ma_hv
        JOIN goi_tap gt ON dk.ma_goi = gt.ma_goi
        LEFT JOIN huan_luyen_vien hlv ON dk.ma_hlv = hlv.ma_hlv
        {where_clause}
        ORDER BY dk.ma_dk DESC
    """
    return _execute_query(sql, tuple(params), fetch="all")


def insert_dang_ky(data: Dict[str, Any]) -> Tuple[bool, Any]:
    sql = """
        INSERT INTO dang_ky (ma_hv, ma_goi, ma_hlv, ngay_dang_ky, ngay_bat_dau, ngay_ket_thuc, trang_thai)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        data["ma_hv"], data["ma_goi"], data.get("ma_hlv"),
        data["ngay_dang_ky"], data["ngay_bat_dau"], data["ngay_ket_thuc"],
        data.get("trang_thai", "Đang hoạt động")
    )
    return _execute_query(sql, params, fetch=None)


def update_dang_ky(ma_dk: int, data: Dict[str, Any]) -> Tuple[bool, Any]:
    sql = """
        UPDATE dang_ky
        SET ma_hv = %s, ma_goi = %s, ma_hlv = %s, ngay_dang_ky = %s,
            ngay_bat_dau = %s, ngay_ket_thuc = %s, trang_thai = %s
        WHERE ma_dk = %s
    """
    params = (
        data["ma_hv"], data["ma_goi"], data.get("ma_hlv"),
        data["ngay_dang_ky"], data["ngay_bat_dau"], data["ngay_ket_thuc"],
        data.get("trang_thai", "Đang hoạt động"), ma_dk
    )
    return _execute_query(sql, params, fetch=None)


def delete_dang_ky(ma_dk: int) -> Tuple[bool, Any]:
    sql = "DELETE FROM dang_ky WHERE ma_dk = %s"
    return _execute_query(sql, (ma_dk,), fetch=None)


def update_expired_status(current_date: Optional[date] = None) -> Tuple[bool, Any]:
    """Tự động cập nhật gói tập sang 'Đã hết hạn' nếu ngày kết thúc < ngày hiện tại."""
    if current_date is None:
        current_date = date.today()
    sql = """
        UPDATE dang_ky
        SET trang_thai = 'Đã hết hạn'
        WHERE ngay_ket_thuc < %s AND trang_thai = 'Đang hoạt động'
    """
    return _execute_query(sql, (current_date,), fetch=None)


def get_active_dang_ky_of_hv(ma_hv: int, exclude_ma_dk: Optional[int] = None) -> Tuple[bool, Any]:
    """Kiểm tra xem hội viên có đăng ký nào đang hoạt động không."""
    if exclude_ma_dk:
        sql = """
            SELECT ma_dk, ngay_bat_dau, ngay_ket_thuc
            FROM dang_ky
            WHERE ma_hv = %s AND trang_thai = 'Đang hoạt động' AND ma_dk != %s
        """
        params = (ma_hv, exclude_ma_dk)
    else:
        sql = """
            SELECT ma_dk, ngay_bat_dau, ngay_ket_thuc
            FROM dang_ky
            WHERE ma_hv = %s AND trang_thai = 'Đang hoạt động'
        """
        params = (ma_hv,)
    return _execute_query(sql, params, fetch="all")


def get_dang_ky_options() -> Tuple[bool, List[Dict[str, Any]]]:
    """Trả về danh sách đăng ký để dùng cho form Thanh toán."""
    sql = """
        SELECT dk.ma_dk, dk.ma_hv, hv.ho_ten AS ten_hv, gt.ten_goi, gt.gia AS gia_goi
        FROM dang_ky dk
        JOIN hoi_vien hv ON dk.ma_hv = hv.ma_hv
        JOIN goi_tap gt ON dk.ma_goi = gt.ma_goi
        ORDER BY dk.ma_dk DESC
    """
    return _execute_query(sql, fetch="all")


# -------------------------------------------------------------
# 7. QUẢN LÝ THANH TOÁN (PAYMENT)
# -------------------------------------------------------------

def get_all_thanh_toan() -> Tuple[bool, Any]:
    sql = """
        SELECT tt.ma_tt, tt.ma_dk, hv.ho_ten AS ten_hv, gt.ten_goi,
               tt.so_tien, tt.ngay_thanh_toan, tt.phuong_thuc
        FROM thanh_toan tt
        JOIN dang_ky dk ON tt.ma_dk = dk.ma_dk
        JOIN hoi_vien hv ON dk.ma_hv = hv.ma_hv
        JOIN goi_tap gt ON dk.ma_goi = gt.ma_goi
        ORDER BY tt.ma_tt DESC
    """
    return _execute_query(sql, fetch="all")


def search_thanh_toan(keyword: str, phuong_thuc: Optional[str] = None) -> Tuple[bool, Any]:
    kw = f"%{keyword.strip()}%"
    conditions = ["(hv.ho_ten LIKE %s OR gt.ten_goi LIKE %s OR CAST(tt.ma_dk AS CHAR) LIKE %s)"]
    params = [kw, kw, kw]

    if phuong_thuc and phuong_thuc != "Tất cả":
        conditions.append("tt.phuong_thuc = %s")
        params.append(phuong_thuc)

    where_clause = " WHERE " + " AND ".join(conditions)
    sql = f"""
        SELECT tt.ma_tt, tt.ma_dk, hv.ho_ten AS ten_hv, gt.ten_goi,
               tt.so_tien, tt.ngay_thanh_toan, tt.phuong_thuc
        FROM thanh_toan tt
        JOIN dang_ky dk ON tt.ma_dk = dk.ma_dk
        JOIN hoi_vien hv ON dk.ma_hv = hv.ma_hv
        JOIN goi_tap gt ON dk.ma_goi = gt.ma_goi
        {where_clause}
        ORDER BY tt.ma_tt DESC
    """
    return _execute_query(sql, tuple(params), fetch="all")


def insert_thanh_toan(data: Dict[str, Any]) -> Tuple[bool, Any]:
    sql = """
        INSERT INTO thanh_toan (ma_dk, so_tien, ngay_thanh_toan, phuong_thuc)
        VALUES (%s, %s, %s, %s)
    """
    params = (data["ma_dk"], data["so_tien"], data["ngay_thanh_toan"], data["phuong_thuc"])
    return _execute_query(sql, params, fetch=None)


def update_thanh_toan(ma_tt: int, data: Dict[str, Any]) -> Tuple[bool, Any]:
    sql = """
        UPDATE thanh_toan
        SET ma_dk = %s, so_tien = %s, ngay_thanh_toan = %s, phuong_thuc = %s
        WHERE ma_tt = %s
    """
    params = (data["ma_dk"], data["so_tien"], data["ngay_thanh_toan"], data["phuong_thuc"], ma_tt)
    return _execute_query(sql, params, fetch=None)


def delete_thanh_toan(ma_tt: int) -> Tuple[bool, Any]:
    sql = "DELETE FROM thanh_toan WHERE ma_tt = %s"
    return _execute_query(sql, (ma_tt,), fetch=None)


# -------------------------------------------------------------
# 8. QUẢN LÝ LỊCH TẬP (SCHEDULE)
# -------------------------------------------------------------

def get_all_lich_tap() -> Tuple[bool, Any]:
    sql = """
        SELECT lt.ma_lich, lt.ma_hv, hv.ho_ten AS ten_hv, hv.so_dien_thoai AS sdt_hv,
               lt.ma_hlv, hlv.ho_ten AS ten_hlv,
               lt.ngay_tap, lt.gio_bat_dau, lt.gio_ket_thuc, lt.noi_dung
        FROM lich_tap lt
        JOIN hoi_vien hv ON lt.ma_hv = hv.ma_hv
        JOIN huan_luyen_vien hlv ON lt.ma_hlv = hlv.ma_hlv
        ORDER BY lt.ngay_tap DESC, lt.gio_bat_dau ASC
    """
    return _execute_query(sql, fetch="all")


def search_lich_tap(keyword: str, ngay_loc: Optional[str] = None) -> Tuple[bool, Any]:
    kw = f"%{keyword.strip()}%"
    conditions = ["(hv.ho_ten LIKE %s OR hlv.ho_ten LIKE %s OR COALESCE(lt.noi_dung, '') LIKE %s)"]
    params = [kw, kw, kw]

    if ngay_loc:
        conditions.append("lt.ngay_tap = %s")
        params.append(ngay_loc)

    where_clause = " WHERE " + " AND ".join(conditions)
    sql = f"""
        SELECT lt.ma_lich, lt.ma_hv, hv.ho_ten AS ten_hv, hv.so_dien_thoai AS sdt_hv,
               lt.ma_hlv, hlv.ho_ten AS ten_hlv,
               lt.ngay_tap, lt.gio_bat_dau, lt.gio_ket_thuc, lt.noi_dung
        FROM lich_tap lt
        JOIN hoi_vien hv ON lt.ma_hv = hv.ma_hv
        JOIN huan_luyen_vien hlv ON lt.ma_hlv = hlv.ma_hlv
        {where_clause}
        ORDER BY lt.ngay_tap DESC, lt.gio_bat_dau ASC
    """
    return _execute_query(sql, tuple(params), fetch="all")


def get_lich_tap_by_date_and_targets(
    ngay_tap: date,
    ma_hv: int,
    ma_hlv: int,
    exclude_ma_lich: Optional[int] = None
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Lấy danh sách các lịch tập trong ngày để Logic Agent kiểm tra xung đột khung giờ.
    Trả về cả lịch của HLV đó VÀ lịch của Hội viên đó trong ngày.
    """
    sql = """
        SELECT lt.ma_lich, lt.ma_hv, hv.ho_ten AS ten_hv,
               lt.ma_hlv, hlv.ho_ten AS ten_hlv,
               lt.gio_bat_dau, lt.gio_ket_thuc
        FROM lich_tap lt
        JOIN hoi_vien hv ON lt.ma_hv = hv.ma_hv
        JOIN huan_luyen_vien hlv ON lt.ma_hlv = hlv.ma_hlv
        WHERE lt.ngay_tap = %s AND (lt.ma_hlv = %s OR lt.ma_hv = %s)
    """
    params = [ngay_tap, ma_hlv, ma_hv]
    if exclude_ma_lich:
        sql += " AND lt.ma_lich != %s"
        params.append(exclude_ma_lich)

    ok, rows = _execute_query(sql, tuple(params), fetch="all")
    if not ok:
        return False, rows

    schedules_for_check = []
    for r in rows:
        # Nếu trùng HLV
        if r["ma_hlv"] == ma_hlv:
            schedules_for_check.append({
                "ma_lich": r["ma_lich"],
                "gio_bat_dau": r["gio_bat_dau"],
                "gio_ket_thuc": r["gio_ket_thuc"],
                "name": r["ten_hlv"],
                "role_conflict": "HLV"
            })
        # Nếu trùng Hội viên
        if r["ma_hv"] == ma_hv:
            schedules_for_check.append({
                "ma_lich": r["ma_lich"],
                "gio_bat_dau": r["gio_bat_dau"],
                "gio_ket_thuc": r["gio_ket_thuc"],
                "name": r["ten_hv"],
                "role_conflict": "Hội viên"
            })

    return True, schedules_for_check


def insert_lich_tap(data: Dict[str, Any]) -> Tuple[bool, Any]:
    sql = """
        INSERT INTO lich_tap (ma_hv, ma_hlv, ngay_tap, gio_bat_dau, gio_ket_thuc, noi_dung)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        data["ma_hv"], data["ma_hlv"], data["ngay_tap"],
        data["gio_bat_dau"], data["gio_ket_thuc"], data.get("noi_dung")
    )
    return _execute_query(sql, params, fetch=None)


def update_lich_tap(ma_lich: int, data: Dict[str, Any]) -> Tuple[bool, Any]:
    sql = """
        UPDATE lich_tap
        SET ma_hv = %s, ma_hlv = %s, ngay_tap = %s, gio_bat_dau = %s,
            gio_ket_thuc = %s, noi_dung = %s
        WHERE ma_lich = %s
    """
    params = (
        data["ma_hv"], data["ma_hlv"], data["ngay_tap"],
        data["gio_bat_dau"], data["gio_ket_thuc"], data.get("noi_dung"),
        ma_lich
    )
    return _execute_query(sql, params, fetch=None)


def delete_lich_tap(ma_lich: int) -> Tuple[bool, Any]:
    sql = "DELETE FROM lich_tap WHERE ma_lich = %s"
    return _execute_query(sql, (ma_lich,), fetch=None)


# -------------------------------------------------------------
# 9. QUẢN LÝ NGƯỜI DÙNG (USER MANAGEMENT - ADMIN ONLY)
# -------------------------------------------------------------

def get_all_nguoi_dung() -> Tuple[bool, Any]:
    sql = "SELECT ma_nd, ten_dang_nhap, ho_ten, vai_tro, trang_thai FROM nguoi_dung ORDER BY ma_nd ASC"
    return _execute_query(sql, fetch="all")


def search_nguoi_dung(keyword: str) -> Tuple[bool, Any]:
    kw = f"%{keyword.strip()}%"
    sql = """
        SELECT ma_nd, ten_dang_nhap, ho_ten, vai_tro, trang_thai
        FROM nguoi_dung
        WHERE ten_dang_nhap LIKE %s OR ho_ten LIKE %s
        ORDER BY ma_nd ASC
    """
    return _execute_query(sql, (kw, kw), fetch="all")


def insert_nguoi_dung(data: Dict[str, Any]) -> Tuple[bool, Any]:
    sql = """
        INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau, ho_ten, vai_tro, trang_thai)
        VALUES (%s, %s, %s, %s, %s)
    """
    params = (
        data["ten_dang_nhap"], data["mat_khau"], data["ho_ten"],
        data["vai_tro"], data.get("trang_thai", "Đang hoạt động")
    )
    return _execute_query(sql, params, fetch=None)


def update_nguoi_dung(ma_nd: int, data: Dict[str, Any]) -> Tuple[bool, Any]:
    sql = """
        UPDATE nguoi_dung
        SET ho_ten = %s, vai_tro = %s, trang_thai = %s
        WHERE ma_nd = %s
    """
    params = (data["ho_ten"], data["vai_tro"], data["trang_thai"], ma_nd)
    return _execute_query(sql, params, fetch=None)


def reset_user_password(ma_nd: int, new_hashed_pwd: str) -> Tuple[bool, Any]:
    sql = "UPDATE nguoi_dung SET mat_khau = %s WHERE ma_nd = %s"
    return _execute_query(sql, (new_hashed_pwd, ma_nd), fetch=None)


def count_other_active_admins(ma_nd: int) -> Tuple[bool, Any]:
    """Đếm số Admin đang hoạt động khác tài khoản ma_nd (bảo vệ Admin cuối cùng)."""
    sql = (
        "SELECT COUNT(*) AS so_luong FROM nguoi_dung "
        "WHERE vai_tro = 'Admin' AND trang_thai = 'Đang hoạt động' AND ma_nd != %s"
    )
    ok, row = _execute_query(sql, (ma_nd,), fetch="one")
    if not ok:
        return False, row
    return True, int(row["so_luong"])


def delete_nguoi_dung(ma_nd: int) -> Tuple[bool, Any]:
    sql = "DELETE FROM nguoi_dung WHERE ma_nd = %s"
    return _execute_query(sql, (ma_nd,), fetch=None)


# -------------------------------------------------------------
# 10. THỐNG KÊ DASHBOARD (DASHBOARD STATS & CHARTS)
# -------------------------------------------------------------

def get_dashboard_summary(today: Optional[date] = None) -> Tuple[bool, Dict[str, Any]]:
    """Lấy số liệu tổng quan 4 KPI cards trên Dashboard."""
    if today is None:
        today = date.today()

    first_day_of_month = date(today.year, today.month, 1)

    sql = """
        SELECT
            (SELECT COUNT(*) FROM hoi_vien) AS tong_hoi_vien,
            (SELECT COUNT(*) FROM dang_ky WHERE trang_thai = 'Đang hoạt động') AS goi_hoat_dong,
            (SELECT COALESCE(SUM(so_tien), 0) FROM thanh_toan WHERE ngay_thanh_toan >= %s) AS doanh_thu_thang,
            (SELECT COUNT(*) FROM lich_tap WHERE ngay_tap = %s) AS lich_tap_hom_nay
    """
    ok, res = _execute_query(sql, (first_day_of_month, today), fetch="one")
    if not ok:
        return False, res
    return True, res


def get_monthly_revenue_stats(year: int) -> Tuple[bool, List[Dict[str, Any]]]:
    """Lấy doanh thu theo từng tháng trong năm để vẽ biểu đồ cột."""
    sql = """
        SELECT MONTH(ngay_thanh_toan) AS thang, COALESCE(SUM(so_tien), 0) AS doanh_thu
        FROM thanh_toan
        WHERE YEAR(ngay_thanh_toan) = %s
        GROUP BY MONTH(ngay_thanh_toan)
        ORDER BY thang ASC
    """
    ok, rows = _execute_query(sql, (year,), fetch="all")
    if not ok:
        return False, rows

    # Điền đủ 12 tháng (kể cả tháng doanh thu = 0)
    rev_map = {r["thang"]: float(r["doanh_thu"]) for r in rows}
    full_year_data = [
        {"thang": m, "doanh_thu": rev_map.get(m, 0.0)}
        for m in range(1, 13)
    ]
    return True, full_year_data


def get_package_popularity() -> Tuple[bool, List[Dict[str, Any]]]:
    """Lấy số lượng đăng ký theo từng gói tập để vẽ biểu đồ tròn."""
    sql = """
        SELECT gt.ten_goi, COUNT(dk.ma_dk) AS so_luong
        FROM goi_tap gt
        LEFT JOIN dang_ky dk ON gt.ma_goi = dk.ma_goi
        GROUP BY gt.ma_goi, gt.ten_goi
        ORDER BY so_luong DESC
    """
    return _execute_query(sql, fetch="all")


def get_expiring_soon_registrations(days: int = 7, today: Optional[date] = None) -> Tuple[bool, Any]:
    """Lấy danh sách các gói đăng ký sắp hết hạn trong N ngày tới."""
    if today is None:
        today = date.today()

    target_date = today + timedelta(days=days)
    sql = """
        SELECT dk.ma_dk, hv.ho_ten AS ten_hv, hv.so_dien_thoai,
               gt.ten_goi, dk.ngay_ket_thuc,
               DATEDIFF(dk.ngay_ket_thuc, %s) AS so_ngay_con_lai
        FROM dang_ky dk
        JOIN hoi_vien hv ON dk.ma_hv = hv.ma_hv
        JOIN goi_tap gt ON dk.ma_goi = gt.ma_goi
        WHERE dk.trang_thai = 'Đang hoạt động'
          AND dk.ngay_ket_thuc >= %s
          AND dk.ngay_ket_thuc <= %s
        ORDER BY dk.ngay_ket_thuc ASC
    """
    return _execute_query(sql, (today, today, target_date), fetch="all")
