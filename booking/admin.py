from django.contrib import admin
from .models import Location, Hotel, Room, ExtraService, Booking, BookingService, Payment


admin.site.site_header = "Hệ thống Quản lý Khách sạn & Homestay"
admin.site.site_title = "Quản trị Khách sạn"
admin.site.index_title = "Bảng điều khiển Quản trị viên"


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'owner', 'phone', 'star_rating', 'created_at')
    list_filter = ('location', 'star_rating')
    search_fields = ('name', 'address', 'phone')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'hotel', 'room_type', 'capacity', 'price_per_night', 'is_active')
    list_filter = ('hotel', 'room_type', 'is_active')
    search_fields = ('name', 'hotel__name')
    list_editable = ('price_per_night', 'is_active')


@admin.register(ExtraService)
class ExtraServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'hotel', 'price', 'unit', 'icon', 'is_active')
    list_filter = ('hotel', 'is_active')
    search_fields = ('name',)
    list_editable = ('price', 'is_active')


class BookingServiceInline(admin.TabularInline):
    model = BookingService
    extra = 0
    readonly_fields = ('service', 'quantity', 'price', 'total_cost')

    def total_cost(self, obj):
        return f"{obj.total_cost:,.0f} đ"
    total_cost.short_description = "Thành tiền"


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    can_delete = False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_code', 'customer_name', 'customer_phone', 'room',
        'check_in', 'check_out', 'total_price_display', 'status', 'created_at'
    )
    list_filter = ('status', 'check_in', 'check_out', 'room__hotel')
    search_fields = ('booking_code', 'customer_name', 'customer_phone', 'customer_email')
    list_editable = ('status',)
    inlines = [BookingServiceInline, PaymentInline]
    date_hierarchy = 'check_in'

    def total_price_display(self, obj):
        return f"{obj.total_price:,.0f} đ"
    total_price_display.short_description = "Tổng tiền"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'payment_method', 'amount_display', 'status', 'payment_date')
    list_filter = ('payment_method', 'status')
    search_fields = ('booking__booking_code', 'transaction_code')
    list_editable = ('status',)

    def amount_display(self, obj):
        return f"{obj.amount:,.0f} đ"
    amount_display.short_description = "Số tiền"
