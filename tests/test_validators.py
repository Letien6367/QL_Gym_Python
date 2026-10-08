import unittest
from datetime import date, time
from utils.validators import (
    validate_phone,
    validate_email,
    add_months,
    calc_end_date,
    compute_status,
    validate_time_slot,
    find_schedule_conflict,
    hash_password,
    verify_password,
    validate_hoi_vien_form,
    validate_goi_tap_form,
    validate_dang_ky_form,
    validate_lich_tap_form
)


class TestValidators(unittest.TestCase):

    def test_phone_validation(self):
        self.assertTrue(validate_phone("0911000111")[0])
        self.assertTrue(validate_phone("0388123456")[0])
        # Sai định dạng
        self.assertFalse(validate_phone("0911000")[0])  # quá ngắn
        self.assertFalse(validate_phone("1911000111")[0])  # không bắt đầu bằng 0
        self.assertFalse(validate_phone("0911000111a")[0])  # chứa chữ
        self.assertFalse(validate_phone("")[0])  # rỗng

    def test_email_validation(self):
        # Email rỗng được chấp nhận (tùy chọn)
        self.assertTrue(validate_email("")[0])
        self.assertTrue(validate_email(None)[0])
        # Email hợp lệ
        self.assertTrue(validate_email("test@gmail.com")[0])
        self.assertTrue(validate_email("user.name+tag@domain.co")[0])
        # Email không hợp lệ
        self.assertFalse(validate_email("plainaddress")[0])
        self.assertFalse(validate_email("@missingusername.com")[0])
        self.assertFalse(validate_email("username@.com")[0])

    def test_add_months_and_end_date(self):
        # 31/01/2026 + 1 tháng -> 28/02/2026 (2026 không nhuận)
        d1 = date(2026, 1, 31)
        res1 = add_months(d1, 1)
        self.assertEqual(res1, date(2026, 2, 28))

        # Năm nhuận 2028: 31/01/2028 + 1 tháng -> 29/02/2028
        d2 = date(2028, 1, 31)
        res2 = add_months(d2, 1)
        self.assertEqual(res2, date(2028, 2, 29))

        # 31/03/2026 + 1 tháng -> 30/04/2026
        d3 = date(2026, 3, 31)
        self.assertEqual(add_months(d3, 1), date(2026, 4, 30))

        # Cộng 12 tháng qua năm
        self.assertEqual(calc_end_date(date(2026, 5, 10), 12), date(2027, 5, 10))

    def test_compute_status(self):
        today = date(2026, 10, 7)
        self.assertEqual(compute_status(date(2026, 10, 8), today), "Đang hoạt động")
        self.assertEqual(compute_status(date(2026, 10, 7), today), "Đang hoạt động")
        self.assertEqual(compute_status(date(2026, 10, 6), today), "Đã hết hạn")

    def test_validate_time_slot(self):
        # Hợp lệ
        self.assertTrue(validate_time_slot(time(7, 0), time(8, 30))[0])
        # Giờ kết thúc <= bắt đầu
        self.assertFalse(validate_time_slot(time(8, 0), time(7, 0))[0])
        self.assertFalse(validate_time_slot(time(8, 0), time(8, 0))[0])
        # Ngoài giờ mở cửa (< 06:00 hoặc > 22:00)
        self.assertFalse(validate_time_slot(time(5, 30), time(6, 30))[0])
        self.assertFalse(validate_time_slot(time(21, 30), time(22, 30))[0])
        # Quá ngắn (< 15p)
        self.assertFalse(validate_time_slot(time(7, 0), time(7, 10))[0])

    def test_find_schedule_conflict(self):
        existing = [
            {
                "ma_lich": 1,
                "gio_bat_dau": time(17, 0),
                "gio_ket_thuc": time(18, 0),
                "name": "Trần Văn Mạnh",
                "role_conflict": "HLV"
            }
        ]
        # Trùng: 17:30 - 18:30
        conflict, msg = find_schedule_conflict(time(17, 30), time(18, 30), existing)
        self.assertTrue(conflict)
        self.assertIn("Trần Văn Mạnh", msg)

        # Trùng: 16:30 - 17:30
        conflict, _ = find_schedule_conflict(time(16, 30), time(17, 30), existing)
        self.assertTrue(conflict)

        # Trùng: bao phủ 16:00 - 19:00
        conflict, _ = find_schedule_conflict(time(16, 0), time(19, 0), existing)
        self.assertTrue(conflict)

        # KHÔNG TRÙNG: Chạm biên 18:00 - 19:00
        conflict, _ = find_schedule_conflict(time(18, 0), time(19, 0), existing)
        self.assertFalse(conflict)

        # KHÔNG TRÙNG: Chạm biên 16:00 - 17:00
        conflict, _ = find_schedule_conflict(time(16, 0), time(17, 0), existing)
        self.assertFalse(conflict)

        # Bỏ qua chính nó khi sửa (cùng ma_lich)
        conflict, _ = find_schedule_conflict(time(17, 0), time(18, 0), existing, current_ma_lich=1)
        self.assertFalse(conflict)

    def test_password_hash(self):
        # 1. SHA-256 thuần (dữ liệu mẫu SQL ban đầu)
        h_legacy = hash_password("123456", use_salt=False)
        self.assertEqual(h_legacy, "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92")
        self.assertTrue(verify_password("123456", h_legacy))
        self.assertFalse(verify_password("wrong", h_legacy))

        # 2. PBKDF2 có salt (chuẩn bảo mật mới)
        h_salted = hash_password("123456", use_salt=True)
        self.assertTrue(h_salted.startswith("pbkdf2$sha256$100000$"))
        self.assertTrue(verify_password("123456", h_salted))
        self.assertFalse(verify_password("wrong", h_salted))

        # Hai lần hash cùng password có salt khác nhau phải cho kết quả khác nhau
        h_salted_2 = hash_password("123456", use_salt=True)
        self.assertNotEqual(h_salted, h_salted_2)

    def test_validate_hoi_vien_form(self):
        raw = {
            "ho_ten": "Nguyễn Văn Test",
            "ngay_sinh": "2000-01-01",
            "gioi_tinh": "Nam",
            "so_dien_thoai": "0988777666",
            "email": "test@gym.vn",
            "dia_chi": "Hà Nội",
            "ngay_tham_gia": "01/10/2026"
        }
        ok, clean, err = validate_hoi_vien_form(raw)
        self.assertTrue(ok)
        self.assertEqual(clean["so_dien_thoai"], "0988777666")
        self.assertEqual(clean["ngay_sinh"], date(2000, 1, 1))
        self.assertEqual(clean["ngay_tham_gia"], date(2026, 10, 1))

    def test_validate_goi_tap_form(self):
        raw = {"ten_goi": "Gói 1 tháng", "thoi_han": "1", "gia": "300000", "mo_ta": "Mô tả"}
        ok, clean, err = validate_goi_tap_form(raw)
        self.assertTrue(ok)
        self.assertEqual(clean["thoi_han"], 1)
        self.assertEqual(clean["gia"], 300000.0)


if __name__ == "__main__":
    unittest.main()
