from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from booking.models import Location, Hotel, Room, ExtraService, Booking, BookingService, Payment


class Command(BaseCommand):
    help = 'Khởi tạo dữ liệu mẫu cho hệ thống đặt phòng homestay/khách sạn'

    def handle(self, *args, **kwargs):
        self.stdout.write("Bắt đầu khởi tạo dữ liệu mẫu...")

        # 1. Tạo tài khoản Superuser & Chủ khách sạn
        admin_user, _ = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@stayease.vn',
            'is_staff': True,
            'is_superuser': True,
        })
        admin_user.set_password('admin123')
        admin_user.save()

        owner_user, _ = User.objects.get_or_create(username='hotel_owner', defaults={
            'email': 'owner@stayease.vn',
            'is_staff': True,
            'is_superuser': False,
        })
        owner_user.set_password('owner123')
        owner_user.save()

        self.stdout.write(self.style.SUCCESS("Đã tạo tài khoản: admin/admin123 và hotel_owner/owner123"))

        # 2. Tạo khu vực (Location)
        locations_data = [
            {
                'name': 'Đà Lạt',
                'slug': 'da-lat',
                'image_url': 'https://images.unsplash.com/photo-1511497584788-87676104235f?auto=format&fit=crop&w=800&q=80',
                'description': 'Thành phố ngàn hoa với khí hậu se lạnh quanh năm, đồi thông thơ mộng và sương mù lãng mạn.'
            },
            {
                'name': 'Sa Pa',
                'slug': 'sa-pa',
                'image_url': 'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=800&q=80',
                'description': 'Thị trấn trong mây với ruộng bậc thang kỳ vĩ, đỉnh Fansipan và bản sắc văn hóa vùng cao đặc sắc.'
            },
            {
                'name': 'Đà Nẵng',
                'slug': 'da-nang',
                'image_url': 'https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=800&q=80',
                'description': 'Thành phố biển đáng sống nhất Việt Nam với bãi biển Mỹ Khê, bán đảo Sơn Trà và Cầu Vàng nổi tiếng.'
            },
            {
                'name': 'Vũng Tàu',
                'slug': 'vung-tau',
                'image_url': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80',
                'description': 'Điểm đến biển tuyệt vời gần Sài Gòn, nơi ngắm hoàng hôn rực rỡ và thưởng thức hải sản tươi ngon.'
            },
            {
                'name': 'Phú Quốc',
                'slug': 'phu-quoc',
                'image_url':"/static/images/dalat.jpg",
                'description': 'Đảo ngọc thiên đường với biển xanh màu ngọc bích, bãi Sao, bãi Khem và các khu nghỉ dưỡng đẳng cấp.'
            },
        ]

        created_locations = {}
        for loc in locations_data:
            obj, _ = Location.objects.update_or_create(
                slug=loc['slug'],
                defaults=loc
            )
            created_locations[loc['slug']] = obj

        # 3. Tạo Khách sạn / Homestay
        hotels_data = [
            {
                'name': 'Mây Homestay & Coffee Đà Lạt',
                'owner': owner_user,
                'location': created_locations['da-lat'],
                'address': '28 Hoàng Hoa Thám, Phường 10, TP. Đà Lạt',
                'phone': '0912345678',
                'email': 'mayhomestay.dalat@gmail.com',
                'description': 'Homestay nằm lưng chừng đồi thông với view ngắm mây tuyệt đẹp, quán cà phê chill ngoài trời và không gian cực kỳ yên tĩnh.',
                'image_url': 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1000&q=80',
                'star_rating': 4,
            },
            {
                'name': 'Sapa Cloud Valley Ecolodge',
                'owner': owner_user,
                'location': created_locations['sa-pa'],
                'address': 'Thôn Bản Hồ, Xã Mường Hoa, Thị xã Sa Pa',
                'phone': '0987654321',
                'email': 'sapacloud.ecolodge@gmail.com',
                'description': 'Khu nghỉ dưỡng sinh thái nhìn thẳng ra thung lũng Mường Hoa, hòa mình vào thiên nhiên hoang sơ và văn hóa bản địa mộc mạc.',
                'image_url': 'https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=1000&q=80',
                'star_rating': 5,
            },
            {
                'name': 'Ocean Breeze Hotel & Suites Đà Nẵng',
                'owner': owner_user,
                'location': created_locations['da-nang'],
                'address': '120 Võ Nguyên Giáp, Phước Mỹ, Sơn Trà, Đà Nẵng',
                'phone': '0905123456',
                'email': 'oceanbreeze.danang@gmail.com',
                'description': 'Khách sạn cách bãi biển Mỹ Khê chỉ 2 phút đi bộ, có hồ bơi vô cực trên tầng thượng nhìn ngắm trọn vẹn biển Đông.',
                'image_url': 'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1000&q=80',
                'star_rating': 4,
            },
            {
                'name': 'Sunset Beach Villa Phú Quốc',
                'owner': owner_user,
                'location': created_locations['phu-quoc'],
                'address': 'Bãi Trường, Dương Tơ, TP. Phú Quốc',
                'phone': '0939888999',
                'email': 'sunsetvilla.phuquoc@gmail.com',
                'description': 'Villa sát bờ biển ngắm hoàng hôn lộng lẫy, bãi cát trắng mịn, hồ bơi riêng biệt lập cho gia đình và nhóm bạn.',
                'image_url': 'https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1000&q=80',
                'star_rating': 5,
            },
        ]

        created_hotels = []
        for h in hotels_data:
            obj, _ = Hotel.objects.update_or_create(
                name=h['name'],
                defaults=h
            )
            created_hotels.append(obj)

        # 4. Tạo Dịch vụ đi kèm (Extra Services)
        services_data = [
            {
                'name': 'Bữa sáng buffet đặc sản địa phương',
                'price': Decimal('75000'),
                'unit': 'người/ngày',
                'icon': 'fa-utensils',
                'description': 'Bữa sáng đầy đủ dinh dưỡng với các món đặc sản địa phương, cà phê và nước ép tươi.',
                'is_active': True,
            },
            {
                'name': 'Thuê xe máy tay ga Honda (kèm 2 nón BH)',
                'price': Decimal('150000'),
                'unit': 'xe/ngày',
                'icon': 'fa-motorcycle',
                'description': 'Xe tay ga đời mới, tiết kiệm xăng, giao nhận xe tận nơi kèm mũ bảo hiểm và áo mưa.',
                'is_active': True,
            },
            {
                'name': 'Xe đưa đón sân bay / bến xe',
                'price': Decimal('250000'),
                'unit': 'chuyến',
                'icon': 'fa-car',
                'description': 'Xe 4 - 7 chỗ máy lạnh đón đúng giờ, tài xế thân thiện, nhiệt tình hỗ trợ hành lý.',
                'is_active': True,
            },
            {
                'name': 'Set tiệc nướng BBQ sân vườn buổi tối',
                'price': Decimal('350000'),
                'unit': 'set (2-3 người)',
                'icon': 'fa-fire-burner',
                'description': 'Bao gồm thịt bò tảng ướp sốt, hải sản, rau củ quả, bếp than nướng và gia vị chấm đặc biệt.',
                'is_active': True,
            },
            {
                'name': 'Dịch vụ giặt ủi lấy liền trong ngày',
                'price': Decimal('50000'),
                'unit': 'kg',
                'icon': 'fa-shirt',
                'description': 'Giặt sấy thơm tho, ủi phẳng phiu và giao tận phòng trong vòng 6 giờ.',
                'is_active': True,
            },
            {
                'name': 'Gói trang trí phòng trăng mật / sinh nhật',
                'price': Decimal('300000'),
                'unit': 'lần',
                'icon': 'fa-heart',
                'description': 'Trang trí nến, hoa hồng tươi, bóng bay lãng mạn và tặng kèm 1 chai vang nhẹ.',
                'is_active': True,
            },
        ]

        for s in services_data:
            ExtraService.objects.update_or_create(
                name=s['name'],
                defaults=s
            )

        # 5. Tạo Danh sách phòng (Rooms)
        rooms_data = [
            # Đà Lạt
            {
                'hotel': created_hotels[0],
                'name': 'Phòng Romantic Đồi Thông 101',
                'room_type': 'DOUBLE',
                'capacity': 2,
                'price_per_night': Decimal('550000'),
                'area': 28,
                'amenities': 'Wifi cáp quang, Bình nóng lạnh, Máy sấy, Ban công ngắm đồi, Trà & Cafe miễn phí',
                'description': 'Phòng ngủ view ngắm trọn đồi thông xanh mát, thiết kế gỗ thông mộc mạc ấm áp, có bồn tắm kính nhìn ra sương mù.',
                'image_url': 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80',
                'is_active': True,
            },
            {
                'hotel': created_hotels[0],
                'name': 'Bungalow Gỗ Áp Mái Panorama 202',
                'room_type': 'VIP',
                'capacity': 3,
                'price_per_night': Decimal('850000'),
                'area': 40,
                'amenities': 'Cửa kính Panorama 360, Điều hòa 2 chiều, Sofa thư giãn, Smart TV 55 inch, Minibar',
                'description': 'Căn bungalow áp mái góc rộng, sáng sớm đón bình minh săn mây ngay trên giường ngủ cực chill.',
                'image_url': 'https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80',
                'is_active': True,
            },
            {
                'hotel': created_hotels[0],
                'name': 'Phòng Gia Đình Mây Ấm Áp 301',
                'room_type': 'FAMILY',
                'capacity': 4,
                'price_per_night': Decimal('1100000'),
                'area': 52,
                'amenities': '2 Giường King, Bàn trà, Tủ lạnh mini, Bếp nhỏ, Phòng tắm đứng cao cấp',
                'description': 'Không gian rộng rãi cho cả gia đình nghỉ dưỡng, có ban công uống trà ngắm hoàng hôn Đà Lạt.',
                'image_url': 'https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=800&q=80',
                'is_active': True,
            },

            # Sa Pa
            {
                'hotel': created_hotels[1],
                'name': 'Deluxe View Ruộng Bậc Thang 102',
                'room_type': 'DOUBLE',
                'capacity': 2,
                'price_per_night': Decimal('750000'),
                'area': 35,
                'amenities': 'Lò sưởi ấm, Ban công ngắm thung lũng, Bồn tắm gỗ Pơ-mu, Wifi, Trà shan tuyết',
                'description': 'Căn phòng nhìn thẳng xuống thung lũng Mường Hoa, bồn tắm gỗ thư giãn ngắm mây trôi lững lờ.',
                'image_url': 'https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=800&q=80',
                'is_active': True,
            },
            {
                'hotel': created_hotels[1],
                'name': 'Suite Mường Hoa Hoàng Gia 201',
                'room_type': 'VIP',
                'capacity': 3,
                'price_per_night': Decimal('1450000'),
                'area': 60,
                'amenities': 'Phòng khách riêng, Bồn tắm sục Jacuzzi, Ban công 2 mặt view, Đồ ăn nhẹ miễn phí',
                'description': 'Phòng Suite cao cấp nhất tại ecolodge với ban công riêng biệt ôm trọn toàn cảnh dãy Hoàng Liên Sơn.',
                'image_url': 'https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=800&q=80',
                'is_active': True,
            },

            # Đà Nẵng
            {
                'hotel': created_hotels[2],
                'name': 'Superior Ocean View 501',
                'room_type': 'DOUBLE',
                'capacity': 2,
                'price_per_night': Decimal('650000'),
                'area': 30,
                'amenities': 'Hướng biển trực diện, Smart TV, Két sắt an toàn, Bàn làm việc, Áo choàng tắm',
                'description': 'Phòng tầng cao đón gió biển Mỹ Khê tươi mát, nội thất trắng thanh lịch và hiện đại.',
                'image_url': 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80',
                'is_active': True,
            },
            {
                'hotel': created_hotels[2],
                'name': 'Studio Gia Đình Tiện Nghi 602',
                'room_type': 'FAMILY',
                'capacity': 4,
                'price_per_night': Decimal('1250000'),
                'area': 55,
                'amenities': 'Bếp nấu ăn, Máy giặt riêng, Bàn ăn gia đình, 2 Giường Queen, View biển',
                'description': 'Căn hộ khách sạn đầy đủ tiện nghi sinh hoạt như ở nhà, rất phù hợp cho kỳ nghỉ dài ngày cùng gia đình.',
                'image_url': 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=800&q=80',
                'is_active': True,
            },

            # Phú Quốc
            {
                'hotel': created_hotels[3],
                'name': 'Beachfront Villa Hoàng Hôn 01',
                'room_type': 'BUNGALOW',
                'capacity': 4,
                'price_per_night': Decimal('1800000'),
                'area': 75,
                'amenities': 'Lối đi thẳng ra bãi biển, Hồ bơi riêng, Bếp nướng BBQ, Ghế tắm nắng, Loa Marshall',
                'description': 'Villa biệt lập sát biển chỉ cách làn nước trong xanh 10 bước chân, riêng tư tuyệt đối cho kỳ nghỉ dưỡng cao cấp.',
                'image_url': 'https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=800&q=80',
                'is_active': True,
            },
            {
                'hotel': created_hotels[3],
                'name': 'Garden Bungalow Nhiệt Đới 02',
                'room_type': 'DOUBLE',
                'capacity': 2,
                'price_per_night': Decimal('950000'),
                'area': 45,
                'amenities': 'Bao quanh bởi vườn dừa nhiệt đới, Bồn tắm ngoài trời, Hiên ngắm hoa, Wifi tốc độ cao',
                'description': 'Bungalow giữa khu vườn dừa xanh mướt, phong cách tropical thư thái và yên bình.',
                'image_url': 'https://images.unsplash.com/photo-1540541338287-41700207dee6?auto=format&fit=crop&w=800&q=80',
                'is_active': True,
            },
        ]

        created_rooms = []
        for r in rooms_data:
            obj, _ = Room.objects.update_or_create(
                hotel=r['hotel'],
                name=r['name'],
                defaults=r
            )
            created_rooms.append(obj)

        # 6. Tạo đơn đặt phòng mẫu (Sample Bookings) để test thống kê & kiểm tra trùng lịch
        today = timezone.localdate()

        # Đơn 1: Đã xác nhận (CONFIRMED) - đặt phòng Đà Lạt 101 vào ngày hôm nay
        booking1, _ = Booking.objects.get_or_create(
            booking_code='BK8A9F32',
            defaults={
                'room': created_rooms[0],
                'customer_name': 'Trần Văn Hoàng',
                'customer_phone': '0901234567',
                'customer_email': 'hoang.tran@gmail.com',
                'check_in': today,
                'check_out': today + timedelta(days=2),
                'num_guests': 2,
                'room_price_total': Decimal('1100000'),
                'services_price_total': Decimal('225000'),
                'total_price': Decimal('1325000'),
                'status': 'CONFIRMED',
            }
        )
        Payment.objects.get_or_create(
            booking=booking1,
            defaults={
                'payment_method': 'BANK_TRANSFER',
                'amount': booking1.total_price,
                'status': 'PAID',
                'transaction_code': 'FT241198234',
                'payment_date': timezone.now(),
            }
        )

        # Đơn 2: Chờ xác nhận (PENDING) - khách đặt Sa Pa 102 tuần sau
        booking2, _ = Booking.objects.get_or_create(
            booking_code='BK7C1149',
            defaults={
                'room': created_rooms[3],
                'customer_name': 'Nguyễn Thị Mai',
                'customer_phone': '0988776655',
                'customer_email': 'mai.nguyen@yahoo.com',
                'check_in': today + timedelta(days=5),
                'check_out': today + timedelta(days=7),
                'num_guests': 2,
                'room_price_total': Decimal('1500000'),
                'services_price_total': Decimal('300000'),
                'total_price': Decimal('1800000'),
                'status': 'PENDING',
            }
        )
        Payment.objects.get_or_create(
            booking=booking2,
            defaults={
                'payment_method': 'CASH',
                'amount': booking2.total_price,
                'status': 'UNPAID',
            }
        )

        # Đơn 3: Đã hoàn thành (COMPLETED) tuần trước - Phú Quốc Villa
        booking3, _ = Booking.objects.get_or_create(
            booking_code='BK5X4421',
            defaults={
                'room': created_rooms[7],
                'customer_name': 'Lê Minh Tuấn',
                'customer_phone': '0918889999',
                'customer_email': 'tuan.le@outlook.com',
                'check_in': today - timedelta(days=5),
                'check_out': today - timedelta(days=2),
                'num_guests': 4,
                'room_price_total': Decimal('5400000'),
                'services_price_total': Decimal('600000'),
                'total_price': Decimal('6000000'),
                'status': 'COMPLETED',
            }
        )
        Payment.objects.get_or_create(
            booking=booking3,
            defaults={
                'payment_method': 'ONLINE',
                'amount': booking3.total_price,
                'status': 'PAID',
                'transaction_code': 'CARD_VISA_8849',
                'payment_date': timezone.now() - timedelta(days=5),
            }
        )

        self.stdout.write(self.style.SUCCESS("Đã khởi tạo thành công tất cả dữ liệu mẫu!"))
        self.stdout.write(f"- 5 Điểm đến (Locations)\n- 4 Khách sạn/Homestay\n- 9 Phòng nghỉ đa dạng\n- 6 Dịch vụ đi kèm\n- 3 Đơn đặt phòng mẫu")
