from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # 1. Khách hàng & Tìm kiếm
    path('', views.index, name='index'),
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/<int:pk>/', views.room_detail, name='room_detail'),
    path('rooms/<int:pk>/book/', views.book_room, name='book_room'),

    # 2. API kiểm tra phòng trống theo thời gian thực (AJAX)
    path('api/check-availability/', views.check_availability_api, name='api_check_availability'),

    # 3. Thanh toán & Xác nhận
    path('payment/<str:booking_code>/', views.payment_page, name='payment_page'),
    path('payment/<str:booking_code>/process/', views.payment_process, name='payment_process'),
    path('booking/success/<str:booking_code>/', views.booking_success, name='booking_success'),
    path('lookup/', views.booking_lookup, name='booking_lookup'),

    # 4. Quản trị dành cho chủ khách sạn (Owner Dashboard)
    path('owner/dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/bookings/', views.owner_bookings_list, name='owner_bookings_list'),
    path('owner/bookings/<int:pk>/status/', views.owner_booking_update_status, name='owner_booking_update_status'),
    path('owner/rooms/', views.owner_rooms_list, name='owner_rooms_list'),
    path('owner/rooms/add/', views.owner_room_create, name='owner_room_create'),
    path('owner/rooms/<int:pk>/edit/', views.owner_room_edit, name='owner_room_edit'),
    path('owner/services/', views.owner_services_list, name='owner_services_list'),
    path('owner/services/add/', views.owner_service_create, name='owner_service_create'),
    path('owner/services/<int:pk>/edit/', views.owner_service_edit, name='owner_service_edit'),

    # 5. Xác thực tài khoản
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
]
