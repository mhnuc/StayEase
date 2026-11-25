# Hệ Thống Đặt Phòng Khách Sạn & Homestay (StayEase) - Django Framework

Dự án website đặt phòng khách sạn, homestay trực tuyến được thiết kế theo phong cách hiện đại, tinh gọn, code đơn giản, cấu trúc mạch lạc và dễ hiểu cho người mới bắt đầu hoặc sinh viên học Django.

---

## 🌟 Chức Năng Chính

1. **Tìm kiếm phòng thông minh**:
   - Tìm theo khu vực/tỉnh thành (Đà Lạt, Sa Pa, Đà Nẵng, Vũng Tàu, Phú Quốc...).
   - Lọc theo ngày nhận/trả phòng, số lượng khách, loại phòng, mức giá tối đa.
2. **Kiểm tra phòng trống theo thời gian thực (Real-time Availability)**:
   - Thuật toán loại trừ trùng lịch tự động: `(check_in < requested_check_out) AND (check_out > requested_check_in)`.
   - Gọi API AJAX ngầm khi khách chọn ngày trên giao diện, thông báo ngay tình trạng phòng trống và tự động tính tổng tiền theo số đêm.
3. **Quy trình đặt phòng & Quản lý dịch vụ đi kèm (Extra Services)**:
   - Cho phép khách chọn thêm dịch vụ: Bữa sáng buffet đặc sản, Thuê xe máy tay ga, Đưa đón sân bay, Tiệc nướng BBQ sân vườn, Giặt ủi lấy liền, Trang trí phòng trăng mật...
   - Tự động cộng dồn tiền phòng + tiền dịch vụ vào hóa đơn tổng.
4. **Cổng thanh toán đa dạng (Payment Gateway Simulation)**:
   - **Chuyển khoản Ngân hàng (VietQR)**: Sinh mã QR Code động chuẩn VietQR kèm số tài khoản, tên ngân hàng và mã đơn nội dung chuyển tiền.
   - **Thanh toán trực tiếp khi nhận phòng (Tiền mặt / COD)**.
   - **Thẻ ngân hàng ATM / Thẻ quốc tế Visa/Master (Mô phỏng trực tuyến)**.
5. **Hóa đơn điện tử & Tra cứu đơn đặt phòng**:
   - In hóa đơn trực tiếp từ trình duyệt (`window.print()`).
   - Tra cứu lại đơn phòng bất cứ lúc nào qua mã booking (vd: `BK8A9F32`) và số điện thoại.
6. **Bảng điều khiển Quản trị dành cho Chủ khách sạn (Host/Owner Dashboard)**:
   - Thống kê doanh thu, tổng số đơn đặt, phòng đang có khách ở hôm nay, đơn chờ xác nhận.
   - Cập nhật nhanh trạng thái đơn phòng (`Chờ xác nhận` &rarr; `Đã xác nhận` &rarr; `Đã nhận phòng` &rarr; `Hoàn thành` / `Đã hủy`).
   - Thêm, sửa, ngưng hoạt động phòng khách sạn.
   - Thêm, sửa, định giá các dịch vụ đi kèm.
   - Tích hợp cả **Django Admin chuẩn** với giao diện tiếng Việt.

---

## 🗂️ Cấu Trúc Dự Án

```
Django/
├── booking/                      # Ứng dụng chính đặt phòng
│   ├── management/commands/      # Lệnh nạp dữ liệu mẫu (seed_data)
│   ├── migrations/               # Lịch sử di chuyển CSDL
│   ├── admin.py                  # Cấu hình Django Admin tiếng Việt
│   ├── apps.py                   # Cấu hình app Booking
│   ├── forms.py                  # Biểu mẫu đặt phòng, phòng & dịch vụ
│   ├── models.py                 # CSDL (Location, Hotel, Room, Service, Booking, Payment)
│   ├── tests.py                  # Unit tests kiểm tra logic
│   ├── urls.py                   # Định tuyến URL cho booking
│   └── views.py                  # Xử lý logic nghiệp vụ và API
├── hotel_booking/                # Cấu hình dự án Django
│   ├── settings.py               # Cài đặt (Templates, Database, Static, Timezone)
│   ├── urls.py                   # URL gốc
│   └── wsgi.py                   # WSGI server
├── templates/                    # Giao diện HTML (Bootstrap 5 + FontAwesome 6)
│   ├── base.html                 # Giao diện khung dùng chung
│   ├── booking/                  # Giao diện khách hàng (Trang chủ, Tìm phòng, Chi tiết, Thanh toán...)
│   └── owner/                    # Giao diện Bảng điều khiển cho chủ khách sạn
├── db.sqlite3                    # Cơ sở dữ liệu SQLite
├── manage.py                     # Script quản trị Django
└── README.md                     # Tài liệu hướng dẫn
```

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy

### 1. Di chuyển vào thư mục dự án
```bash
cd "c:\Users\MINH QUOC\24CT1 - NguyenMinhQuoc\Django"
```

### 2. Chạy migrate tạo cấu trúc Database (nếu chưa chạy)
```bash
python manage.py migrate
```

### 3. Nạp dữ liệu mẫu khởi tạo (Sample Data)
Lệnh này sẽ tự động tạo 5 khu vực du lịch, 4 khách sạn/homestay, 9 phòng nghỉ, 6 dịch vụ đi kèm và 3 đơn đặt phòng mẫu:
```bash
python manage.py seed_data
```

### 4. Khởi chạy máy chủ phát triển
```bash
python manage.py runserver
```
Sau đó mở trình duyệt và truy cập: **http://127.0.0.1:8000/**

---

## 🔑 Tài Khoản Mẫu Để Đăng Nhập

| Loại tài khoản | Tên đăng nhập | Mật khẩu | Quyền hạn |
| :--- | :--- | :--- | :--- |
| **Quản trị viên (Admin)** | `admin` | `admin123` | Toàn quyền hệ thống & truy cập `/admin/` |
| **Chủ Homestay (Owner)** | `hotel_owner` | `owner123` | Quản trị phòng, xem doanh thu & cập nhật đơn đặt phòng tại `/owner/dashboard/` |

---

## 🧪 Chạy Kiểm Thử Tự Động (Unit Tests)

Dự án đã tích hợp đầy đủ test cases kiểm tra:
- Logic kiểm tra phòng trống theo thời gian thực (không trùng và trùng lịch).
- API AJAX `/api/check-availability/`.
- Quy trình đặt phòng, cộng dồn tiền dịch vụ đi kèm.
- Quyền truy cập trang quản trị chủ khách sạn.

Chạy lệnh test:
```bash
python manage.py test
```
Kết quả mong đợi: `Ran 5 tests ... OK`.
