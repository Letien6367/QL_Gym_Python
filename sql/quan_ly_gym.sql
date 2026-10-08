-- ==========================================
-- SCRIPT TẠO DATABASE QUẢN LÝ PHÒNG GYM
-- ==========================================

DROP DATABASE IF EXISTS quan_ly_gym;
CREATE DATABASE quan_ly_gym CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE quan_ly_gym;

-- 1. BẢNG GÓI TẬP (Tạo trước vì Đăng ký cần tham chiếu)
CREATE TABLE goi_tap (
    ma_goi INT AUTO_INCREMENT PRIMARY KEY,
    ten_goi VARCHAR(100) NOT NULL UNIQUE,
    thoi_han INT NOT NULL CHECK (thoi_han > 0), -- Thời hạn tính bằng tháng
    gia DECIMAL(12,2) NOT NULL CHECK (gia > 0),
    mo_ta TEXT
);

CREATE TABLE nguoi_dung (
    ma_nd INT AUTO_INCREMENT PRIMARY KEY,
    ten_dang_nhap VARCHAR(50) NOT NULL UNIQUE,
    mat_khau VARCHAR(255) NOT NULL, -- (Thực tế sẽ mã hóa, đồ án có thể để text thường hoặc mã hóa MD5/SHA256 tùy bạn)
    ho_ten VARCHAR(100) NOT NULL,
    vai_tro VARCHAR(50) NOT NULL DEFAULT 'Nhân viên', -- Ví dụ: 'Admin' hoặc 'Nhân viên'
    trang_thai VARCHAR(50) DEFAULT 'Đang hoạt động' -- 'Đang hoạt động' hoặc 'Đã khóa'
);

-- 2. BẢNG HUẤN LUYỆN VIÊN
CREATE TABLE huan_luyen_vien (
    ma_hlv INT AUTO_INCREMENT PRIMARY KEY,
    ho_ten VARCHAR(100) NOT NULL,
    ngay_sinh DATE NOT NULL,
    gioi_tinh VARCHAR(10),
    so_dien_thoai VARCHAR(15) NOT NULL UNIQUE,
    chuyen_mon VARCHAR(100) NOT NULL
);

-- 3. BẢNG HỘI VIÊN
CREATE TABLE hoi_vien (
    ma_hv INT AUTO_INCREMENT PRIMARY KEY,
    ho_ten VARCHAR(100) NOT NULL,
    ngay_sinh DATE NOT NULL,
    gioi_tinh VARCHAR(10),
    so_dien_thoai VARCHAR(15) NOT NULL UNIQUE,
    email VARCHAR(100),
    dia_chi VARCHAR(255),
    ngay_tham_gia DATE NOT NULL
);

-- 4. BẢNG ĐĂNG KÝ
CREATE TABLE dang_ky (
    ma_dk INT AUTO_INCREMENT PRIMARY KEY,
    ma_hv INT NOT NULL,
    ma_goi INT NOT NULL,
    ma_hlv INT, -- Có thể không thuê HLV
    ngay_dang_ky DATE NOT NULL,
    ngay_bat_dau DATE NOT NULL,
    ngay_ket_thuc DATE NOT NULL,
    trang_thai VARCHAR(50) DEFAULT 'Đang hoạt động',
    FOREIGN KEY (ma_hv) REFERENCES hoi_vien(ma_hv) ON DELETE RESTRICT,
    FOREIGN KEY (ma_goi) REFERENCES goi_tap(ma_goi) ON DELETE RESTRICT,
    FOREIGN KEY (ma_hlv) REFERENCES huan_luyen_vien(ma_hlv) ON DELETE RESTRICT
);

-- 5. BẢNG THANH TOÁN
CREATE TABLE thanh_toan (
    ma_tt INT AUTO_INCREMENT PRIMARY KEY,
    ma_dk INT NOT NULL,
    so_tien DECIMAL(12,2) NOT NULL CHECK (so_tien > 0),
    ngay_thanh_toan DATE NOT NULL,
    phuong_thuc VARCHAR(50) NOT NULL,
    FOREIGN KEY (ma_dk) REFERENCES dang_ky(ma_dk) ON DELETE RESTRICT
);

-- 6. BẢNG LỊCH TẬP
CREATE TABLE lich_tap (
    ma_lich INT AUTO_INCREMENT PRIMARY KEY,
    ma_hv INT NOT NULL,
    ma_hlv INT NOT NULL,
    ngay_tap DATE NOT NULL,
    gio_bat_dau TIME NOT NULL,
    gio_ket_thuc TIME NOT NULL,
    noi_dung TEXT,
    FOREIGN KEY (ma_hv) REFERENCES hoi_vien(ma_hv) ON DELETE RESTRICT,
    FOREIGN KEY (ma_hlv) REFERENCES huan_luyen_vien(ma_hlv) ON DELETE RESTRICT,
    CHECK (gio_ket_thuc > gio_bat_dau)
);

-- ==========================================
-- CHÈN DỮ LIỆU MẪU (Mock Data)
-- ==========================================

-- 4 Gói tập
INSERT INTO goi_tap (ten_goi, thoi_han, gia, mo_ta) VALUES 
('Gói 1 tháng', 1, 300000, 'Tập luyện tự do 1 tháng'),
('Gói 3 tháng', 3, 800000, 'Tiết kiệm hơn cho 3 tháng'),
('Gói 6 tháng', 6, 1400000, 'Tặng kèm 1 buổi tư vấn dinh dưỡng'),
('Gói 12 tháng VIP', 12, 2500000, 'Sử dụng khăn tắm, tủ đồ miễn phí');

-- 5 Huấn luyện viên
INSERT INTO huan_luyen_vien (ho_ten, ngay_sinh, gioi_tinh, so_dien_thoai, chuyen_mon) VALUES 
('Trần Văn Mạnh', '1990-05-12', 'Nam', '0901111222', 'Thể hình (Bodybuilding)'),
('Nguyễn Thị Nga', '1995-08-22', 'Nữ', '0902222333', 'Yoga & Pilates'),
('Lê Hoàng Long', '1993-11-05', 'Nam', '0903333444', 'Giảm cân (Cardio)'),
('Phạm Quang Khải', '1988-02-15', 'Nam', '0904444555', 'Phục hồi chấn thương'),
('Đặng Thu Thảo', '1998-12-30', 'Nữ', '0905555666', 'Zumba');

-- 10 Hội viên
INSERT INTO hoi_vien (ho_ten, ngay_sinh, gioi_tinh, so_dien_thoai, email, dia_chi, ngay_tham_gia) VALUES 
('Nguyễn Văn A', '2000-01-01', 'Nam', '0911000111', 'nva@gmail.com', 'Quận 1, TP.HCM', '2026-09-01'),
('Trần Thị B', '1999-02-02', 'Nữ', '0911000222', 'ttb@gmail.com', 'Quận 2, TP.HCM', '2026-09-05'),
('Lê Văn C', '1995-03-03', 'Nam', '0911000333', 'lvc@gmail.com', 'Quận 3, TP.HCM', '2026-09-10'),
('Phạm Thị D', '2001-04-04', 'Nữ', '0911000444', 'ptd@gmail.com', 'Quận 4, TP.HCM', '2026-09-15'),
('Hoàng Văn E', '1992-05-05', 'Nam', '0911000555', 'hve@gmail.com', 'Quận 5, TP.HCM', '2026-09-20'),
('Vũ Thị F', '1996-06-06', 'Nữ', '0911000666', 'vtf@gmail.com', 'Quận 6, TP.HCM', '2026-09-25'),
('Đinh Văn G', '1994-07-07', 'Nam', '0911000777', 'dvg@gmail.com', 'Quận 7, TP.HCM', '2026-10-01'),
('Ngô Thị H', '2002-08-08', 'Nữ', '0911000888', 'nth@gmail.com', 'Quận 8, TP.HCM', '2026-10-02'),
('Bùi Văn I', '1998-09-09', 'Nam', '0911000999', 'bvi@gmail.com', 'Quận 9, TP.HCM', '2026-10-05'),
('Lý Thị K', '1997-10-10', 'Nữ', '0911000000', 'ltk@gmail.com', 'Quận 10, TP.HCM', '2026-10-07');

-- 10 Đăng ký
INSERT INTO dang_ky (ma_hv, ma_goi, ma_hlv, ngay_dang_ky, ngay_bat_dau, ngay_ket_thuc, trang_thai) VALUES 
(1, 2, 1, '2026-09-01', '2026-09-01', '2026-12-01', 'Đang hoạt động'),
(2, 1, 2, '2026-09-05', '2026-09-05', '2026-10-05', 'Đã hết hạn'), -- Gói 1 tháng, đã hết hạn
(3, 3, 3, '2026-09-10', '2026-09-10', '2027-03-10', 'Đang hoạt động'),
(4, 4, NULL, '2026-09-15', '2026-09-15', '2027-09-15', 'Đang hoạt động'),
(5, 1, 4, '2026-09-20', '2026-09-20', '2026-10-20', 'Đang hoạt động'),
(6, 2, 5, '2026-09-25', '2026-09-25', '2026-12-25', 'Đang hoạt động'),
(7, 3, 1, '2026-10-01', '2026-10-01', '2027-04-01', 'Đang hoạt động'),
(8, 1, 2, '2026-10-02', '2026-10-02', '2026-11-02', 'Đang hoạt động'),
(9, 2, NULL, '2026-10-05', '2026-10-05', '2027-01-05', 'Đang hoạt động'),
(10, 4, 3, '2026-10-07', '2026-10-07', '2027-10-07', 'Đang hoạt động');

INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau, ho_ten, vai_tro, trang_thai) VALUES 
('admin', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'Quản trị viên', 'Admin', 'Đang hoạt động'),
('nhanvien1', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'Nguyễn Thị Lễ Tân', 'Nhân viên', 'Đang hoạt động'),
('nhanvien2', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'Trần Văn Bảo Vệ', 'Nhân viên', 'Đã khóa');

-- 10 Thanh toán
INSERT INTO thanh_toan (ma_dk, so_tien, ngay_thanh_toan, phuong_thuc) VALUES 
(1, 800000, '2026-09-01', 'Tiền mặt'),
(2, 300000, '2026-09-05', 'Chuyển khoản'),
(3, 1400000, '2026-09-10', 'Chuyển khoản'),
(4, 2500000, '2026-09-15', 'Tiền mặt'),
(5, 300000, '2026-09-20', 'Chuyển khoản'),
(6, 800000, '2026-09-25', 'Tiền mặt'),
(7, 1400000, '2026-10-01', 'Chuyển khoản'),
(8, 300000, '2026-10-02', 'Tiền mặt'),
(9, 800000, '2026-10-05', 'Chuyển khoản'),
(10, 2500000, '2026-10-07', 'Tiền mặt');

-- 10 Lịch tập (Thời gian: 06:00 đến 22:00, không trùng nhau trên cùng 1 HLV)
INSERT INTO lich_tap (ma_hv, ma_hlv, ngay_tap, gio_bat_dau, gio_ket_thuc, noi_dung) VALUES 
(1, 1, '2026-10-08', '17:00:00', '18:00:00', 'Tập ngực và tay sau'),
(2, 2, '2026-10-04', '18:00:00', '19:00:00', 'Yoga cơ bản'),
(3, 3, '2026-10-09', '06:00:00', '07:30:00', 'Chạy bộ, đốt mỡ'),
(5, 4, '2026-10-09', '08:00:00', '09:00:00', 'Giãn cơ vai'),
(6, 5, '2026-10-10', '19:00:00', '20:00:00', 'Zumba nhịp điệu nhanh'),
(7, 1, '2026-10-10', '18:30:00', '19:30:00', 'Tập lưng xô'),
(8, 2, '2026-10-11', '07:00:00', '08:00:00', 'Pilates'),
(10, 3, '2026-10-11', '17:30:00', '18:30:00', 'Tập chân và mông'),
(1, 1, '2026-10-12', '17:00:00', '18:00:00', 'Tập vai'),
(3, 3, '2026-10-12', '06:00:00', '07:30:00', 'Cardio cường độ cao');