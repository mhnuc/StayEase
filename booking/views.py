from datetime import datetime, date
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Sum, Count
from django.utils import timezone

from .models import Location, Hotel, Room, ExtraService, Booking, BookingService, Payment
from .forms import BookingForm, RoomForm, ExtraServiceForm, PaymentProcessForm


# ==========================================
# 1. KHÁCH HÀNG: TRANG CHỦ & TÌM KIẾM PHÒNG
# ==========================================

def index(request):
    """Trang chủ hiển thị tìm kiếm nhanh, điểm đến nổi bật, phòng nổi bật"""
    locations = Location.objects.all()[:6]
    featured_rooms = Room.objects.filter(is_active=True).select_related('hotel', 'hotel__location')[:6]
    today = timezone.localdate().strftime('%Y-%m-%d')
    tomorrow = (timezone.localdate() + timezone.timedelta(days=1)).strftime('%Y-%m-%d')

    context = {
        'locations': locations,
        'featured_rooms': featured_rooms,
        'today': today,
        'tomorrow': tomorrow,
    }
    return render(request, 'booking/index.html', context)


def room_list(request):
    """
    Tìm kiếm và lọc phòng:
    - Theo khu vực (location_id)
    - Theo ngày nhận phòng (check_in) & ngày trả phòng (check_out) -> Kiểm tra thời gian thực
    - Theo số người (guests)
    - Theo loại phòng (room_type)
    - Theo khoảng giá (min_price, max_price)
    """
    rooms = Room.objects.filter(is_active=True).select_related('hotel', 'hotel__location')
    locations = Location.objects.all()

    location_id = request.GET.get('location')
    check_in_str = request.GET.get('check_in')
    check_out_str = request.GET.get('check_out')
    guests = request.GET.get('guests')
    room_type = request.GET.get('room_type')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    keyword = request.GET.get('keyword')

    check_in_date = None
    check_out_date = None

    # Lọc từ khóa tìm kiếm (tên phòng hoặc tên khách sạn)
    if keyword:
        rooms = rooms.filter(
            Q(name__icontains=keyword) |
            Q(hotel__name__icontains=keyword) |
            Q(hotel__address__icontains=keyword)
        )

    # Lọc theo khu vực
    if location_id:
        rooms = rooms.filter(hotel__location_id=location_id)

    # Lọc theo sức chứa
    if guests:
        try:
            rooms = rooms.filter(capacity__gte=int(guests))
        except ValueError:
            pass

    # Lọc theo loại phòng
    if room_type:
        rooms = rooms.filter(room_type=room_type)

    # Lọc theo giá
    if min_price:
        try:
            rooms = rooms.filter(price_per_night__gte=Decimal(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            rooms = rooms.filter(price_per_night__lte=Decimal(max_price))
        except ValueError:
            pass

    # KIỂM TRA PHÒNG TRỐNG THEO THỜI GIAN THỰC (Real-time availability check)
    if check_in_str and check_out_str:
        try:
            check_in_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out_str, '%Y-%m-%d').date()

            if check_in_date < check_out_date:
                # Loại trừ các phòng có đơn đặt trùng lịch
                conflicting_room_ids = Booking.objects.filter(
                    status__in=['PENDING', 'CONFIRMED', 'CHECKED_IN'],
                    check_in__lt=check_out_date,
                    check_out__gt=check_in_date
                ).values_list('room_id', flat=True)

                rooms = rooms.exclude(id__in=conflicting_room_ids)
            else:
                messages.warning(request, "Ngày trả phòng phải sau ngày nhận phòng!")
        except ValueError:
            pass

    context = {
        'rooms': rooms,
        'locations': locations,
        'selected_location': location_id,
        'check_in': check_in_str or '',
        'check_out': check_out_str or '',
        'guests': guests or '',
        'room_type': room_type or '',
        'min_price': min_price or '',
        'max_price': max_price or '',
        'keyword': keyword or '',
        'room_types': Room.ROOM_TYPES,
        'total_found': rooms.count(),
    }
    return render(request, 'booking/room_list.html', context)


def room_detail(request, pk):
    """Chi tiết phòng & form đặt phòng kèm dịch vụ đi kèm"""
    room = get_object_or_404(Room.objects.select_related('hotel', 'hotel__location'), pk=pk)

    # Lấy các dịch vụ đi kèm của khách sạn này hoặc dịch vụ chung
    services = ExtraService.objects.filter(
        Q(hotel=room.hotel) | Q(hotel__isnull=True),
        is_active=True
    )

    check_in_param = request.GET.get('check_in', '')
    check_out_param = request.GET.get('check_out', '')
    guests_param = request.GET.get('guests', 1)

    today = timezone.localdate().strftime('%Y-%m-%d')
    tomorrow = (timezone.localdate() + timezone.timedelta(days=1)).strftime('%Y-%m-%d')

    initial_data = {
        'check_in': check_in_param or today,
        'check_out': check_out_param or tomorrow,
        'num_guests': guests_param,
    }

    # Nếu người dùng đã đăng nhập, tự điền thông tin
    if request.user.is_authenticated:
        initial_data.update({
            'customer_name': request.user.get_full_name() or request.user.username,
            'customer_email': request.user.email,
        })

    booking_form = BookingForm(initial=initial_data)

    context = {
        'room': room,
        'services': services,
        'booking_form': booking_form,
        'today': today,
        'tomorrow': tomorrow,
    }
    return render(request, 'booking/room_detail.html', context)


# ==========================================
# 2. API KIỂM TRA PHÒNG TRỐNG THEO THỜI GIAN THỰC
# ==========================================

def check_availability_api(request):
    """
    API JSON kiểm tra phòng trống theo thời gian thực (hỗ trợ AJAX từ trình duyệt).
    Params: room_id, check_in (YYYY-MM-DD), check_out (YYYY-MM-DD)
    """
    room_id = request.GET.get('room_id')
    check_in_str = request.GET.get('check_in')
    check_out_str = request.GET.get('check_out')

    if not all([room_id, check_in_str, check_out_str]):
        return JsonResponse({'valid': False, 'message': 'Thiếu tham số kiểm tra.'})

    try:
        room = Room.objects.get(pk=room_id)
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()

        today = timezone.localdate()
        if check_in < today:
            return JsonResponse({'valid': False, 'available': False, 'message': 'Ngày nhận phòng không thể ở quá khứ.'})

        if check_out <= check_in:
            return JsonResponse({'valid': False, 'available': False, 'message': 'Ngày trả phòng phải sau ngày nhận ít nhất 1 đêm.'})

        nights = (check_out - check_in).days
        is_free = room.is_available(check_in, check_out)
        room_total = int(room.price_per_night * nights)

        return JsonResponse({
            'valid': True,
            'available': is_free,
            'nights': nights,
            'price_per_night': int(room.price_per_night),
            'room_total': room_total,
            'message': 'Phòng còn trống, bạn có thể đặt ngay!' if is_free else 'Rất tiếc! Phòng đã có người đặt trong thời gian này.'
        })
    except (Room.DoesNotExist, ValueError) as e:
        return JsonResponse({'valid': False, 'message': f'Dữ liệu không hợp lệ: {str(e)}'})


# ==========================================
# 3. QUY TRÌNH ĐẶT PHÒNG & QUẢN LÝ DỊCH VỤ ĐI KÈM
# ==========================================

def book_room(request, pk):
    """Xử lý đặt phòng và các dịch vụ đi kèm đã chọn"""
    room = get_object_or_404(Room, pk=pk)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            check_in = form.cleaned_data['check_in']
            check_out = form.cleaned_data['check_out']

            # Kiểm tra thời gian thực một lần nữa trước khi lưu
            if not room.is_available(check_in, check_out):
                messages.error(request, "Rất tiếc! Phòng này vừa có khách khác đặt trong thời gian bạn chọn. Vui lòng chọn ngày khác hoặc phòng khác.")
                return redirect('booking:room_detail', pk=room.pk)

            booking = form.save(commit=False)
            booking.room = room
            if request.user.is_authenticated:
                booking.user = request.user

            nights = booking.total_nights
            booking.room_price_total = room.price_per_night * Decimal(nights)

            # Xử lý dịch vụ đi kèm
            selected_services = request.POST.getlist('selected_services')
            service_total = Decimal(0)
            service_items = []

            for s_id in selected_services:
                try:
                    service = ExtraService.objects.get(pk=s_id, is_active=True)
                    qty_key = f'service_qty_{s_id}'
                    qty = int(request.POST.get(qty_key, 1))
                    if qty < 1:
                        qty = 1

                    cost = service.price * Decimal(qty)
                    service_total += cost
                    service_items.append((service, qty, service.price))
                except (ExtraService.DoesNotExist, ValueError):
                    continue

            booking.services_price_total = service_total
            booking.total_price = booking.room_price_total + service_total
            booking.status = 'PENDING'
            booking.save()

            # Lưu danh sách dịch vụ đã đặt
            for service, qty, price in service_items:
                BookingService.objects.create(
                    booking=booking,
                    service=service,
                    quantity=qty,
                    price=price
                )

            # Khởi tạo bản ghi thanh toán
            Payment.objects.create(
                booking=booking,
                amount=booking.total_price,
                status='UNPAID'
            )

            messages.success(request, f"Đã tạo đơn đặt phòng thành công! Mã đơn: {booking.booking_code}")
            return redirect('booking:payment_page', booking_code=booking.booking_code)
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin trong biểu mẫu.")
            return redirect('booking:room_detail', pk=room.pk)

    return redirect('booking:room_detail', pk=room.pk)


# ==========================================
# 4. THANH TOÁN (PAYMENT) & XÁC NHẬN ĐƠN
# ==========================================

def payment_page(request, booking_code):
    """Trang thanh toán đơn đặt phòng (QR Ngân hàng, Tiền mặt, Thẻ)"""
    booking = get_object_or_404(
        Booking.objects.select_related('room', 'room__hotel', 'payment').prefetch_related('booked_services__service'),
        booking_code=booking_code
    )

    # Thông tin tài khoản ngân hàng từ mã VietQR MB Bank của chủ khách sạn
    bank_info = {
        'bank_name': 'Ngân hàng TMCP Quân đội (MB)',
        'account_number': '0000040973128',
        'account_holder': 'NGUYEN MINH QUOC',
        'transfer_content': f"TT {booking.booking_code}",
    }

    # Sinh link QR thanh toán nhanh VietQR chuẩn kèm số tiền và mã đơn
    vietqr_url = (
        f"https://img.vietqr.io/image/MB-{bank_info['account_number']}-compact2.png"
        f"?amount={int(booking.total_price)}&addInfo={bank_info['transfer_content']}&accountName={bank_info['account_holder']}"
    )

    context = {
        'booking': booking,
        'bank_info': bank_info,
        'vietqr_url': vietqr_url,
        'qr_image_url': '/static/images/qr_code.png',
    }
    return render(request, 'booking/payment.html', context)


def payment_process(request, booking_code):
    """Xử lý xác nhận phương thức thanh toán của khách"""
    booking = get_object_or_404(Booking, booking_code=booking_code)
    payment = booking.payment

    if request.method == 'POST':
        method = request.POST.get('payment_method', 'BANK_TRANSFER')
        transaction_code = request.POST.get('transaction_code', '')
        note = request.POST.get('note', '')

        payment.payment_method = method
        payment.transaction_code = transaction_code
        payment.note = note

        if method == 'BANK_TRANSFER':
            # Với chuyển khoản, đánh dấu chờ đối soát hoặc xác nhận đã chuyển
            payment.status = 'PAID'
            payment.payment_date = timezone.now()
            booking.status = 'CONFIRMED'
            messages.success(request, "Đã ghi nhận giao dịch chuyển khoản! Chúng tôi đã xác nhận đơn phòng của bạn.")
        elif method == 'ONLINE':
            # Mô phỏng cổng thanh toán trực tuyến thành công
            payment.status = 'PAID'
            payment.payment_date = timezone.now()
            booking.status = 'CONFIRMED'
            messages.success(request, "Thanh toán thẻ trực tuyến thành công! Đơn phòng đã được xác nhận.")
        else: # CASH
            payment.status = 'UNPAID'
            booking.status = 'CONFIRMED'
            messages.success(request, "Bạn đã chọn thanh toán tại khách sạn khi nhận phòng. Đơn phòng đã được xác nhận!")

        payment.save()
        booking.save()

        return redirect('booking:booking_success', booking_code=booking.booking_code)

    return redirect('booking:payment_page', booking_code=booking.booking_code)


def booking_success(request, booking_code):
    """Trang thông báo thành công và hóa đơn điện tử"""
    booking = get_object_or_404(
        Booking.objects.select_related('room', 'room__hotel', 'payment').prefetch_related('booked_services__service'),
        booking_code=booking_code
    )
    context = {'booking': booking}
    return render(request, 'booking/booking_success.html', context)


def booking_lookup(request):
    """Tra cứu đơn đặt phòng theo mã đơn và số điện thoại"""
    booking = None
    searched = False

    if request.method == 'GET' and 'code' in request.GET:
        searched = True
        code = request.GET.get('code', '').strip().upper()
        phone = request.GET.get('phone', '').strip()

        try:
            booking = Booking.objects.select_related('room', 'room__hotel', 'payment').prefetch_related('booked_services__service').get(
                booking_code=code,
                customer_phone=phone
            )
        except Booking.DoesNotExist:
            messages.error(request, "Không tìm thấy đơn đặt phòng với thông tin đã nhập.")

    context = {
        'booking': booking,
        'searched': searched,
    }
    return render(request, 'booking/booking_lookup.html', context)


# ==========================================
# 5. TRANG QUẢN TRỊ DÀNH CHO CHỦ KHÁCH SẠN (OWNER DASHBOARD)
# ==========================================

def is_staff_or_owner(user):
    """Kiểm tra người dùng có quyền quản trị hoặc là chủ khách sạn"""
    return user.is_authenticated and (user.is_staff or user.hotels.exists() or user.is_superuser)


@user_passes_test(is_staff_or_owner, login_url='/login/')
def owner_dashboard(request):
    """Bảng điều khiển quản trị cho chủ khách sạn / homestay"""
    # Nếu là superuser/staff thì quản lý tất cả, nếu là owner thông thường thì quản lý hotel của mình
    if request.user.is_superuser or request.user.is_staff:
        hotels = Hotel.objects.all()
        rooms = Room.objects.all()
        bookings = Booking.objects.all()
    else:
        hotels = request.user.hotels.all()
        rooms = Room.objects.filter(hotel__in=hotels)
        bookings = Booking.objects.filter(room__hotel__in=hotels)

    today = timezone.localdate()

    # Thống kê tổng quan
    total_revenue = bookings.filter(status__in=['CONFIRMED', 'CHECKED_IN', 'COMPLETED']).aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_bookings_count = bookings.count()
    pending_bookings_count = bookings.filter(status='PENDING').count()
    current_occupied_rooms = bookings.filter(
        status__in=['CONFIRMED', 'CHECKED_IN'],
        check_in__lte=today,
        check_out__gt=today
    ).count()

    recent_bookings = bookings.select_related('room', 'room__hotel', 'payment')[:10]

    context = {
        'hotels': hotels,
        'rooms_count': rooms.count(),
        'total_revenue': total_revenue,
        'total_bookings_count': total_bookings_count,
        'pending_bookings_count': pending_bookings_count,
        'current_occupied_rooms': current_occupied_rooms,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'owner/dashboard.html', context)


@user_passes_test(is_staff_or_owner, login_url='/login/')
def owner_bookings_list(request):
    """Danh sách và bộ lọc toàn bộ đơn đặt phòng"""
    status_filter = request.GET.get('status')
    bookings = Booking.objects.select_related('room', 'room__hotel', 'payment').all()

    if not (request.user.is_superuser or request.user.is_staff):
        bookings = bookings.filter(room__hotel__owner=request.user)

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'status_choices': Booking.STATUS_CHOICES,
    }
    return render(request, 'owner/bookings_list.html', context)


@user_passes_test(is_staff_or_owner, login_url='/login/')
def owner_booking_update_status(request, pk):
    """Cập nhật nhanh trạng thái đơn đặt phòng"""
    booking = get_object_or_404(Booking, pk=pk)
    if not (request.user.is_superuser or request.user.is_staff or booking.room.hotel.owner == request.user):
        messages.error(request, "Bạn không có quyền thao tác trên đơn này.")
        return redirect('booking:owner_dashboard')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        payment_status = request.POST.get('payment_status')

        if new_status in dict(Booking.STATUS_CHOICES):
            booking.status = new_status
            booking.save()

        if payment_status and hasattr(booking, 'payment'):
            booking.payment.status = payment_status
            if payment_status == 'PAID' and not booking.payment.payment_date:
                booking.payment.payment_date = timezone.now()
            booking.payment.save()

        messages.success(request, f"Đã cập nhật trạng thái đơn {booking.booking_code} thành công!")

    return redirect('booking:owner_bookings_list')


@user_passes_test(is_staff_or_owner, login_url='/login/')
def owner_rooms_list(request):
    """Quản lý danh sách phòng của chủ"""
    if request.user.is_superuser or request.user.is_staff:
        rooms = Room.objects.select_related('hotel').all()
    else:
        rooms = Room.objects.filter(hotel__owner=request.user).select_related('hotel')

    context = {'rooms': rooms}
    return render(request, 'owner/rooms_list.html', context)


@user_passes_test(is_staff_or_owner, login_url='/login/')
def owner_room_create(request):
    """Thêm phòng mới"""
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save()
            messages.success(request, f"Đã thêm phòng '{room.name}' thành công!")
            return redirect('booking:owner_rooms_list')
    else:
        form = RoomForm()
        if not (request.user.is_superuser or request.user.is_staff):
            form.fields['hotel'].queryset = request.user.hotels.all()

    context = {'form': form, 'title': 'Thêm phòng mới'}
    return render(request, 'owner/room_form.html', context)


@user_passes_test(is_staff_or_owner, login_url='/login/')
def owner_room_edit(request, pk):
    """Chỉnh sửa thông tin phòng"""
    room = get_object_or_404(Room, pk=pk)
    if not (request.user.is_superuser or request.user.is_staff or room.hotel.owner == request.user):
        messages.error(request, "Bạn không có quyền chỉnh sửa phòng này.")
        return redirect('booking:owner_rooms_list')

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, f"Đã cập nhật phòng '{room.name}'!")
            return redirect('booking:owner_rooms_list')
    else:
        form = RoomForm(instance=room)
        if not (request.user.is_superuser or request.user.is_staff):
            form.fields['hotel'].queryset = request.user.hotels.all()

    context = {'form': form, 'title': f'Chỉnh sửa phòng: {room.name}'}
    return render(request, 'owner/room_form.html', context)


@user_passes_test(is_staff_or_owner, login_url='/login/')
def owner_services_list(request):
    """Quản lý danh sách dịch vụ đi kèm"""
    if request.user.is_superuser or request.user.is_staff:
        services = ExtraService.objects.select_related('hotel').all()
    else:
        services = ExtraService.objects.filter(
            Q(hotel__owner=request.user) | Q(hotel__isnull=True)
        ).select_related('hotel')

    context = {'services': services}
    return render(request, 'owner/services_list.html', context)


@user_passes_test(is_staff_or_owner, login_url='/login/')
def owner_service_create(request):
    """Thêm dịch vụ đi kèm mới"""
    if request.method == 'POST':
        form = ExtraServiceForm(request.POST)
        if form.is_valid():
            service = form.save()
            messages.success(request, f"Đã tạo dịch vụ '{service.name}'!")
            return redirect('booking:owner_services_list')
    else:
        form = ExtraServiceForm()
        if not (request.user.is_superuser or request.user.is_staff):
            form.fields['hotel'].queryset = request.user.hotels.all()

    context = {'form': form, 'title': 'Thêm dịch vụ đi kèm'}
    return render(request, 'owner/service_form.html', context)


@user_passes_test(is_staff_or_owner, login_url='/login/')
def owner_service_edit(request, pk):
    """Chỉnh sửa dịch vụ đi kèm"""
    service = get_object_or_404(ExtraService, pk=pk)
    if request.method == 'POST':
        form = ExtraServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, f"Đã cập nhật dịch vụ '{service.name}'!")
            return redirect('booking:owner_services_list')
    else:
        form = ExtraServiceForm(instance=service)
        if not (request.user.is_superuser or request.user.is_staff):
            form.fields['hotel'].queryset = request.user.hotels.all()

    context = {'form': form, 'title': f'Chỉnh sửa dịch vụ: {service.name}'}
    return render(request, 'owner/service_form.html', context)


# ==========================================
# 6. ĐĂNG NHẬP / ĐĂNG KÝ / ĐĂNG XUẤT
# ==========================================

def user_register(request):
    """Đăng ký tài khoản"""
    if request.user.is_authenticated:
        return redirect('booking:index')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Chào mừng {user.username}! Bạn đã đăng ký tài khoản thành công.")
            return redirect('booking:index')
    else:
        form = UserCreationForm()

    context = {'form': form}
    return render(request, 'booking/register.html', context)


def user_login(request):
    """Đăng nhập tài khoản"""
    if request.user.is_authenticated:
        return redirect('booking:index')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Đăng nhập thành công! Chào bạn, {user.username}.")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if user.is_staff or user.hotels.exists() or user.is_superuser:
                return redirect('booking:owner_dashboard')
            return redirect('booking:index')
        else:
            messages.error(request, "Tên đăng nhập hoặc mật khẩu không chính xác.")
    else:
        form = AuthenticationForm()

    context = {'form': form}
    return render(request, 'booking/login.html', context)


def user_logout(request):
    """Đăng xuất tài khoản"""
    logout(request)
    messages.info(request, "Bạn đã đăng xuất thành công.")
    return redirect('booking:index')
