from django import forms
from django.utils import timezone
from .models import Booking, Room, ExtraService, Hotel, Payment


class BookingForm(forms.ModelForm):
    """Form đặt phòng dành cho khách hàng"""
    class Meta:
        model = Booking
        fields = [
            'customer_name', 'customer_phone', 'customer_email',
            'check_in', 'check_out', 'num_guests', 'customer_note'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nguyễn Văn A'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0901234567'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'check_in': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'check_out': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'num_guests': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 20}),
            'customer_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Yêu cầu thêm (vd: nhận phòng muộn, tầng cao...)'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')

        if check_in and check_out:
            today = timezone.localdate()
            if check_in < today:
                raise forms.ValidationError("Ngày nhận phòng không thể trong quá khứ.")
            if check_out <= check_in:
                raise forms.ValidationError("Ngày trả phòng phải sau ngày nhận phòng ít nhất 1 ngày.")

        return cleaned_data


class RoomForm(forms.ModelForm):
    """Form thêm / sửa phòng cho chủ khách sạn"""
    class Meta:
        model = Room
        fields = [
            'hotel', 'name', 'room_type', 'capacity', 'price_per_night',
            'area', 'amenities', 'description', 'image_url', 'is_active'
        ]
        widgets = {
            'hotel': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vd: Phòng Deluxe Sea View 201'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'price_per_night': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '650000'}),
            'area': forms.NumberInput(attrs={'class': 'form-control'}),
            'amenities': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ExtraServiceForm(forms.ModelForm):
    """Form thêm / sửa dịch vụ đi kèm"""
    class Meta:
        model = ExtraService
        fields = ['hotel', 'name', 'price', 'unit', 'icon', 'description', 'is_active']
        widgets = {
            'hotel': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vd: Thuê xe máy tay ga Honda Lead'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '150000'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'chiếc/ngày'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa-motorcycle'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PaymentProcessForm(forms.Form):
    """Form xử lý thanh toán"""
    payment_method = forms.ChoiceField(
        choices=Payment.METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    transaction_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mã giao dịch ngân hàng (nếu có)'})
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ghi chú thêm...'})
    )
