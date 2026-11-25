from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from booking.models import Location, Hotel, Room, ExtraService, Booking, BookingService, Payment


class HotelBookingTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testowner', password='password123', is_staff=True)
        self.location = Location.objects.create(name='Đà Lạt', slug='da-lat')
        self.hotel = Hotel.objects.create(
            name='Test Homestay',
            owner=self.user,
            location=self.location,
            address='123 Đường Test, Đà Lạt',
            phone='0911223344',
            star_rating=4
        )
        self.room = Room.objects.create(
            hotel=self.hotel,
            name='Phòng 101 Test',
            room_type='DOUBLE',
            capacity=2,
            price_per_night=Decimal('500000'),
            is_active=True
        )
        self.service = ExtraService.objects.create(
            name='Bữa sáng',
            price=Decimal('50000'),
            unit='người',
            is_active=True
        )

    def test_realtime_availability_no_conflict(self):
        """Kiểm tra phòng trống khi chưa có đơn nào"""
        today = timezone.localdate()
        is_free = self.room.is_available(today, today + timedelta(days=2))
        self.assertTrue(is_free)

    def test_realtime_availability_with_conflict(self):
        """Kiểm tra phát hiện trùng phòng khi đã có đơn đặt trước"""
        today = timezone.localdate()
        # Tạo đơn đã đặt từ ngày 1 đến ngày 3
        Booking.objects.create(
            room=self.room,
            customer_name='Khách A',
            customer_phone='0900000001',
            customer_email='a@test.com',
            check_in=today + timedelta(days=1),
            check_out=today + timedelta(days=3),
            status='CONFIRMED'
        )

        # Kiểm tra trùng lịch: nhận phòng ngày 2, trả phòng ngày 4 -> Trùng!
        conflict = self.room.is_available(today + timedelta(days=2), today + timedelta(days=4))
        self.assertFalse(conflict)

        # Kiểm tra không trùng lịch: nhận phòng ngày 3, trả phòng ngày 5 -> Trống!
        no_conflict = self.room.is_available(today + timedelta(days=3), today + timedelta(days=5))
        self.assertTrue(no_conflict)

    def test_check_availability_api(self):
        """Kiểm tra API AJAX kiểm tra phòng trống"""
        today = timezone.localdate()
        url = reverse('booking:api_check_availability')
        response = self.client.get(url, {
            'room_id': self.room.id,
            'check_in': today.strftime('%Y-%m-%d'),
            'check_out': (today + timedelta(days=2)).strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['valid'])
        self.assertTrue(data['available'])
        self.assertEqual(data['nights'], 2)
        self.assertEqual(data['room_total'], 1000000)

    def test_booking_creation_with_extra_services(self):
        """Kiểm tra quy trình đặt phòng kèm dịch vụ đi kèm và tính tiền"""
        today = timezone.localdate()
        url = reverse('booking:book_room', kwargs={'pk': self.room.id})
        post_data = {
            'customer_name': 'Nguyễn Văn Test',
            'customer_phone': '0912345678',
            'customer_email': 'test@gmail.com',
            'check_in': today.strftime('%Y-%m-%d'),
            'check_out': (today + timedelta(days=3)).strftime('%Y-%m-%d'),
            'num_guests': 2,
            'customer_note': 'Ghi chú đặt phòng',
            'selected_services': [self.service.id],
            f'service_qty_{self.service.id}': 2,
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        booking = Booking.objects.get(customer_phone='0912345678')
        # 3 đêm * 500,000 = 1,500,000
        self.assertEqual(booking.room_price_total, Decimal('1500000'))
        # 2 bữa sáng * 50,000 = 100,000
        self.assertEqual(booking.services_price_total, Decimal('100000'))
        # Tổng = 1,600,000
        self.assertEqual(booking.total_price, Decimal('1600000'))
        self.assertTrue(booking.booking_code.startswith('BK'))

        # Kiểm tra tự động tạo Payment
        self.assertTrue(hasattr(booking, 'payment'))
        self.assertEqual(booking.payment.status, 'UNPAID')

    def test_owner_dashboard_authenticated(self):
        """Kiểm tra trang quản trị cho chủ khách sạn khi đăng nhập"""
        self.client.login(username='testowner', password='password123')
        url = reverse('booking:owner_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bảng Điều Khiển Chủ Khách Sạn')
