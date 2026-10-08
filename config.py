# ==========================================
# CẤU HÌNH HỆ THỐNG QUẢN LÝ PHÒNG GYM
# ==========================================

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "quan_ly_gym",
    "charset": "utf8mb4",
    "connection_timeout": 5
}

APP_TITLE = "Hệ Thống Quản Lý Phòng Gym - GymPro"
WINDOW_SIZE = "1280x760"
MIN_WINDOW_SIZE = (1024, 680)

# Quy định giờ hoạt động của phòng tập
GIO_MO_CUA = "06:00"
GIO_DONG_CUA = "22:00"

# Phân quyền chức năng theo vai trò
# Admin: Toàn quyền
# Nhân viên: Xem/thực hiện hội viên, đăng ký, thanh toán, lịch tập, dashboard; không vào Quản lý người dùng; chỉ xem Gói tập, HLV
ROLE_PERMISSIONS = {
    "Admin": {
        "dashboard": "full",
        "hoi_vien": "full",
        "huan_luyen_vien": "full",
        "goi_tap": "full",
        "dang_ky": "full",
        "thanh_toan": "full",
        "lich_tap": "full",
        "nguoi_dung": "full"
    },
    "Nhân viên": {
        "dashboard": "full",
        "hoi_vien": "full",
        "huan_luyen_vien": "readonly",
        "goi_tap": "readonly",
        "dang_ky": "full",
        "thanh_toan": "full",
        "lich_tap": "full",
        "nguoi_dung": "hidden"
    }
}
