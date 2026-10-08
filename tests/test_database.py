import unittest
from datetime import date, time, timedelta
from unittest.mock import MagicMock, patch

import database
from utils.validators import (
    find_schedule_conflict,
    find_registration_overlap,
    check_date_within_active_registration,
    check_admin_safeguard,
)


def _fake_connection(rows):
    """Tạo kết nối MySQL giả trả về `rows` cho fetchall/fetchone."""
    cursor = MagicMock()
    cursor.fetchall.return_value = rows
    cursor.fetchone.return_value = rows[0] if rows else None
    cursor.lastrowid = 7
    cursor.rowcount = 1
    conn = MagicMock()
    conn.cursor.return_value = cursor
    conn.is_connected.return_value = True
    return conn, cursor


class TestDatabaseAgent(unittest.TestCase):

    def test_time_columns_are_normalized(self):
        """TIME của MySQL (timedelta) phải được đổi thành datetime.time."""
        rows = [{"ma_lich": 1, "gio_bat_dau": timedelta(hours=6), "gio_ket_thuc": timedelta(hours=7, minutes=30)}]
        conn, _ = _fake_connection(rows)
        with patch("database.get_connection", return_value=conn):
            ok, result = database._execute_query("SELECT 1", fetch="all")
        self.assertTrue(ok)
        self.assertEqual(result[0]["gio_bat_dau"], time(6, 0))
        self.assertEqual(result[0]["gio_ket_thuc"], time(7, 30))
        # Định dạng hiển thị không còn bị cắt thành "6:00:"
        self.assertEqual(str(result[0]["gio_bat_dau"])[:5], "06:00")

    def test_parameterized_queries_pass_params_separately(self):
        conn, cursor = _fake_connection([])
        with patch("database.get_connection", return_value=conn):
            database.get_user_by_username("admin' OR '1'='1")
        sql, params = cursor.execute.call_args[0]
        self.assertIn("%s", sql)
        self.assertNotIn("OR '1'='1", sql)
        self.assertEqual(params, ("admin' OR '1'='1",))

    def test_expiring_soon_query_runs(self):
        """Trước đây thiếu import timedelta nên hàm này ném NameError."""
        with patch("database._execute_query", return_value=(True, [])) as mock_q:
            ok, rows = database.get_expiring_soon_registrations(days=7, today=date(2026, 10, 7))
        self.assertTrue(ok)
        params = mock_q.call_args[0][1]
        self.assertEqual(params, (date(2026, 10, 7), date(2026, 10, 7), date(2026, 10, 14)))

    def test_mysql_errors_are_translated(self):
        from mysql.connector import Error
        err = Error(msg="Duplicate entry '0911000111' for key 'hoi_vien.so_dien_thoai'", errno=1062)
        self.assertIn("Số điện thoại", database._translate_error(err))
        err = Error(msg="Cannot delete or update a parent row", errno=1451)
        self.assertIn("Không thể xóa", database._translate_error(err))

    def test_count_other_active_admins(self):
        with patch("database._execute_query", return_value=(True, {"so_luong": 2})):
            ok, n = database.count_other_active_admins(1)
        self.assertTrue(ok)
        self.assertEqual(n, 2)


class TestBusinessRules(unittest.TestCase):

    def test_schedule_conflict_accepts_timedelta_rows(self):
        existing = [{
            "ma_lich": 1, "gio_bat_dau": timedelta(hours=17), "gio_ket_thuc": timedelta(hours=18),
            "name": "Trần Văn Mạnh", "role_conflict": "HLV",
        }]
        conflict, _ = find_schedule_conflict(time(17, 30), time(18, 30), existing)
        self.assertTrue(conflict)
        conflict, _ = find_schedule_conflict(time(18, 0), time(19, 0), existing)
        self.assertFalse(conflict)

    def test_registration_overlap(self):
        regs = [{"ma_dk": 3, "ngay_bat_dau": date(2026, 9, 1), "ngay_ket_thuc": date(2026, 12, 1)}]
        self.assertTrue(find_registration_overlap(date(2026, 11, 1), date(2027, 2, 1), regs)[0])
        self.assertTrue(find_registration_overlap(date(2026, 12, 1), date(2027, 1, 1), regs)[0])  # chạm ngày cuối
        self.assertFalse(find_registration_overlap(date(2026, 12, 2), date(2027, 1, 2), regs)[0])
        self.assertFalse(find_registration_overlap(date(2026, 1, 1), date(2026, 8, 31), regs)[0])

    def test_practice_date_within_registration(self):
        regs = [{"ma_dk": 1, "ngay_bat_dau": date(2026, 9, 1), "ngay_ket_thuc": date(2026, 12, 1)}]
        self.assertTrue(check_date_within_active_registration(date(2026, 10, 8), regs)[0])
        self.assertFalse(check_date_within_active_registration(date(2026, 12, 2), regs)[0])
        self.assertFalse(check_date_within_active_registration(date(2026, 10, 8), [])[0])

    def test_admin_safeguard(self):
        # Admin cuối cùng: không được hạ quyền / khoá / xoá
        self.assertFalse(check_admin_safeguard(True, "Nhân viên", "Đang hoạt động", 0)[0])
        self.assertFalse(check_admin_safeguard(True, "Admin", "Đã khóa", 0)[0])
        self.assertFalse(check_admin_safeguard(True, "", "", 0, is_delete=True)[0])
        # Còn Admin khác: được phép
        self.assertTrue(check_admin_safeguard(True, "Nhân viên", "Đang hoạt động", 1)[0])
        # Giữ nguyên Admin hoạt động: được phép
        self.assertTrue(check_admin_safeguard(True, "Admin", "Đang hoạt động", 0)[0])
        # Không phải Admin hoạt động: luôn được phép
        self.assertTrue(check_admin_safeguard(False, "Nhân viên", "Đã khóa", 0)[0])


if __name__ == "__main__":
    unittest.main()
