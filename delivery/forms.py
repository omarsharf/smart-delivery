from django import forms
from .models import Delivery


class DeliveryForm(forms.ModelForm):
    
    class Meta:
        model = Delivery
        fields = ['pickup_address', 'dropoff_address','vehicle_type','notes', 'scheduled_date']
        labels = {
            'pickup_address': 'عنوان الاستلام (من)',
            'dropoff_address': 'عنوان التسليم (إلى)',
            'scheduled_date': 'الميعاد المخطط',
            'vehicle_type': 'نوع المركبة المطلوب' ,
            'notes': 'ملاحظات (اختياري)'
        }
        widgets = {
            'pickup_address': forms.TextInput(
                attrs={'placeholder': 'مثال: مول سيتي ستارز، مدينة نصر'}),
            'dropoff_address': forms.TextInput(
                attrs={'placeholder': 'مثال: فيلا 12، التجمع الخامس'}),
            'scheduled_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}),
        }