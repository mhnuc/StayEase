import uuid
from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Location(models.Model):
    """Khu vực / Địa điểm du lịch (Đà Lạt, Sa Pa, Đà Nẵng, Vũng Tàu, Phú Quốc...)"""
    name = models.CharField(max_length=120, verbose_name="Tên khu vực")
    slug = models.SlugField(max_length=150, unique=True, verbose_name="Slug")
    image_url = models.CharField(max_length=500, blank=True, verbose_name="Link ảnh hoặc tên file trong static/images")
    description = models.TextField(blank=True, verbose_name="Mô tả khu vực")

    class Meta:
        verbose_name = "Khu vực"
        verbose_name_plural = "Danh sách khu vực"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def get_image(self):
        """Hỗ trợ cả link ngoài (http/https), đường dẫn /static/ hoặc chỉ cần gõ tên file"""
        if not self.image_url:
            return 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80'
        if self.image_url.startswith(('http://', 'https://', '/static/', '/media/')):
            return self.image_url
        from django.templatetags.static import static
        return static(f'images/{self.image_url}')


class Hotel(models.Model):
    """Khách sạn / Homestay"""
    name = models.CharField(max_length=200, verbose_name="Tên khách sạn / Homestay")
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='hotels', verbose_name="Chủ khách sạn"
    )
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name='hotels', verbose_name="Khu vực"
    )
    address = models.CharField(max_length=255, verbose_name="Địa chỉ cụ thể")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại liên hệ")
    email = models.EmailField(blank=True, verbose_name="Email liên hệ")
    description = models.TextField(verbose_name="Mô tả giới thiệu")
    image_url = models.URLField(max_length=500, blank=True, verbose_name="Link ảnh đại diện")
    star_rating = models.IntegerField(default=3, verbose_name="Đánh giá sao (1-5)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        verbose_name = "Khách sạn / Homestay"
        verbose_name_plural = "Danh sách khách sạn / Homestay"

    def __str__(self):
        return f"{self.name} ({self.location.name})"


class Room(models.Model):
    """Phòng khách sạn / homestay"""
    ROOM_TYPES = [
        ('SINGLE', 'Phòng đơn (1 giường)'),
        ('DOUBLE', 'Phòng đôi (2 người)'),
        ('FAMILY', 'Phòng gia đình (3 - 4 người)'),
        ('VIP', 'Phòng VIP / Suite'),
        ('BUNGALOW', 'Bungalow / Villa nguyên căn'),
    ]

    hotel = models.ForeignKey(
        Hotel, on_delete=models.CASCADE, related_name='rooms', verbose_name="Thuộc khách sạn"
    )
    name = models.CharField(max_length=150, verbose_name="Tên phòng / Mã phòng")
    room_type = models.CharField(
        max_length=20, choices=ROOM_TYPES, default='DOUBLE', verbose_name="Loại phòng"
    )
    capacity = models.PositiveIntegerField(default=2, verbose_name="Sức chứa tối đa (người)")
    price_per_night = models.DecimalField(
        max_digits=12, decimal_places=0, verbose_name="Giá mỗi đêm (VNĐ)"
    )
    area = models.PositiveIntegerField(default=25, verbose_name="Diện tích (m²)")
    amenities = models.CharField(
        max_length=255, default="Wifi tốc độ cao, Điều hòa, TV, Bình nóng lạnh, Máy sấy",
        verbose_name="Tiện nghi"
    )
    description = models.TextField(blank=True, verbose_name="Mô tả phòng")
    image_url = models.CharField(max_length=500, blank=True, verbose_name="Link ảnh hoặc tên file trong static/images")
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")

    class Meta:
        verbose_name = "Phòng"
        verbose_name_plural = "Danh sách phòng"
        ordering = ['price_per_night']

    def __str__(self):
        return f"{self.name} - {self.hotel.name} ({self.get_room_type_display()})"

    @property
    def get_image(self):
        """Hỗ trợ link ngoài, /static/ hoặc chỉ tên file ảnh"""
        if not self.image_url:
            return 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80'
        if self.image_url.startswith(('http://', 'https://', '/static/', '/media/')):
            return self.image_url
        from django.templatetags.static import static
        return static(f'images/{self.image_url}')

    def is_available(self, check_in, check_out, exclude_booking_id=None):
        """
        Kiểm tra thời gian thực xem phòng có trống từ check_in đến check_out không.
        Điều kiện trùng lịch: (booking.check_in < check_out) AND (booking.check_out > check_in)
        Và trạng thái booking không bị hủy.
        """
        if not self.is_active:
            return False

        if check_in >= check_out:
            return False

        conflicts = Booking.objects.filter(
            room=self,
            status__in=['PENDING', 'CONFIRMED', 'CHECKED_IN'],
            check_in__lt=check_out,
            check_out__gt=check_in
        )

        if exclude_booking_id:
            conflicts = conflicts.exclude(id=exclude_booking_id)

        return not conflicts.exists()


class ExtraService(models.Model):
    """Dịch vụ đi kèm (Bữa sáng, thuê xe, đưa đón, tiệc nướng...)"""
    hotel = models.ForeignKey(
        Hotel, on_delete=models.CASCADE, related_name='services',
        null=True, blank=True,
        verbose_name="Thuộc khách sạn (để trống nếu áp dụng chung)"
    )
    name = models.CharField(max_length=150, verbose_name="Tên dịch vụ")
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Đơn giá (VNĐ)")
    unit = models.CharField(
        max_length=50, default="lần/ngày", verbose_name="Đơn vị tính (vd: người/ngày, xe/ngày, lần)"
    )
    icon = models.CharField(
        max_length=50, default="fa-concierge-bell",
        verbose_name="Icon FontAwesome (vd: fa-utensils, fa-motorcycle, fa-car)"
    )
    description = models.TextField(blank=True, verbose_name="Mô tả chi tiết")
    is_active = models.BooleanField(default=True, verbose_name="Đang cung cấp")

    class Meta:
        verbose_name = "Dịch vụ đi kèm"
        verbose_name_plural = "Quản lý dịch vụ đi kèm"

    def __str__(self):
        return f"{self.name} - {self.price:,.0f} đ/{self.unit}"


class Booking(models.Model):
    """Đơn đặt phòng"""
    STATUS_CHOICES = [
        ('PENDING', 'Chờ xác nhận / thanh toán'),
        ('CONFIRMED', 'Đã xác nhận'),
        ('CHECKED_IN', 'Đã nhận phòng'),
        ('COMPLETED', 'Đã trả phòng / hoàn thành'),
        ('CANCELLED', 'Đã hủy'),
    ]

    booking_code = models.CharField(
        max_length=20, unique=True, editable=False, verbose_name="Mã đơn đặt"
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='bookings', verbose_name="Tài khoản khách (nếu có)"
    )
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='bookings', verbose_name="Phòng đặt"
    )
    customer_name = models.CharField(max_length=120, verbose_name="Họ và tên khách hàng")
    customer_phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    customer_email = models.EmailField(verbose_name="Email")
    customer_note = models.TextField(blank=True, verbose_name="Ghi chú / Yêu cầu đặc biệt")

    check_in = models.DateField(verbose_name="Ngày nhận phòng")
    check_out = models.DateField(verbose_name="Ngày trả phòng")
    num_guests = models.PositiveIntegerField(default=1, verbose_name="Số lượng khách")

    room_price_total = models.DecimalField(
        max_digits=12, decimal_places=0, default=0, verbose_name="Tổng tiền phòng (VNĐ)"
    )
    services_price_total = models.DecimalField(
        max_digits=12, decimal_places=0, default=0, verbose_name="Tổng tiền dịch vụ (VNĐ)"
    )
    total_price = models.DecimalField(
        max_digits=12, decimal_places=0, default=0, verbose_name="Tổng thanh toán (VNĐ)"
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Trạng thái đơn"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời điểm đặt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Cập nhật lần cuối")

    class Meta:
        verbose_name = "Đơn đặt phòng"
        verbose_name_plural = "Danh sách đơn đặt phòng"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.booking_code:
            self.booking_code = "BK" + uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    @property
    def total_nights(self):
        """Tính số đêm ở"""
        if self.check_in and self.check_out and self.check_out > self.check_in:
            return (self.check_out - self.check_in).days
        return 1

    def __str__(self):
        return f"[{self.booking_code}] {self.customer_name} - {self.room.name}"


class BookingService(models.Model):
    """Chi tiết dịch vụ đã chọn theo từng đơn đặt phòng"""
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name='booked_services', verbose_name="Đơn đặt phòng"
    )
    service = models.ForeignKey(
        ExtraService, on_delete=models.PROTECT, verbose_name="Dịch vụ"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Số lượng")
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Giá tại thời điểm đặt")

    class Meta:
        verbose_name = "Dịch vụ đã đặt"
        verbose_name_plural = "Dịch vụ đã đặt"

    @property
    def total_cost(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.service.name} x {self.quantity} ({self.total_cost:,.0f} đ)"


class Payment(models.Model):
    """Thông tin thanh toán"""
    METHOD_CHOICES = [
        ('BANK_TRANSFER', 'Chuyển khoản ngân hàng (QR Code / VietQR)'),
        ('CASH', 'Thanh toán trực tiếp khi nhận phòng'),
        ('ONLINE', 'Thẻ ATM / Thẻ quốc tế Visa/Master (Mô phỏng)'),
    ]

    STATUS_CHOICES = [
        ('UNPAID', 'Chưa thanh toán'),
        ('PAID', 'Đã thanh toán'),
        ('REFUNDED', 'Đã hoàn tiền'),
    ]

    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name='payment', verbose_name="Đơn đặt phòng"
    )
    payment_method = models.CharField(
        max_length=20, choices=METHOD_CHOICES, default='BANK_TRANSFER', verbose_name="Phương thức thanh toán"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Số tiền thanh toán")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='UNPAID', verbose_name="Trạng thái thanh toán"
    )
    transaction_code = models.CharField(
        max_length=50, blank=True, verbose_name="Mã giao dịch ngân hàng / cổng TT"
    )
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian thanh toán")
    note = models.TextField(blank=True, verbose_name="Ghi chú thanh toán")

    class Meta:
        verbose_name = "Thanh toán"
        verbose_name_plural = "Quản lý thanh toán"

    def __str__(self):
        return f"TT {self.booking.booking_code} - {self.get_status_display()} ({self.amount:,.0f} đ)"
