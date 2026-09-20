"""بيانات تجريبية للتجربة السريعة: python manage.py seed_demo"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from delivery.models import ChatMessage, Customer, Delivery, Driver

User = get_user_model()


def get_or_create_user(username, role, password='demo12345'):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'role': role, 'is_staff': role in ('admin', 'dispatcher')},
    )
    if created:
        user.set_password(password)
        user.save()
    return user


class Command(BaseCommand):
    help = 'ينشئ بيانات تجريبية: مستخدمين بكل الأدوار، عملاء، سائقين، شحنات بحالات مختلفة'

    def handle(self, *args, **options):
        now = timezone.now()

        # --- مستخدمين ---
        dispatcher = get_or_create_user('dispatch1', 'dispatcher')
        driver_user_1 = get_or_create_user('khaled', 'driver')
        driver_user_2 = get_or_create_user('omar', 'driver')
        customer_user_1 = get_or_create_user('mona', 'customer')
        customer_user_2 = get_or_create_user('hazem', 'customer')

        # --- عملاء ---
        customer_1, _ = Customer.objects.get_or_create(
            phone='01000000001',
            defaults={'name': 'منى عبد الرحمن', 'address': 'المعادي، القاهرة', 'user': customer_user_1},
        )
        customer_2, _ = Customer.objects.get_or_create(
            phone='01000000002',
            defaults={'name': 'حازم فؤاد', 'address': 'سموحة، الإسكندرية', 'user': customer_user_2},
        )
        customer_3, _ = Customer.objects.get_or_create(
            phone='01000000003',
            defaults={'name': 'عميل نقدي (بدون حساب)', 'address': 'المنصورة، الدقهلية'},
        )

        # --- سائقين ---
        driver_1, _ = Driver.objects.get_or_create(
            phone='01100000001',
            defaults={'name': 'خالد السيد', 'vehicle_type': 'مركبة', 'user': driver_user_1, 'is_available': False},
        )
        driver_2, _ = Driver.objects.get_or_create(
            phone='01100000002',
            defaults={'name': 'عمر ماهر', 'vehicle_type': 'موتوسيكل', 'user': driver_user_2},
        )

        def make_delivery(pickup, dropoff, customer, driver, hours_from_now, status_path):
            delivery = Delivery.objects.filter(
                customer=customer, pickup_address=pickup, dropoff_address=dropoff
            ).first()
            if delivery:
                return delivery
            delivery = Delivery.objects.create(
                customer=customer,
                driver=driver,
                pickup_address=pickup,
                dropoff_address=dropoff,
                scheduled_date=now + timedelta(hours=hours_from_now),
            )
            for status in status_path:
                delivery.status = status
                delivery.save()  # كل حفظ بيسجل في StatusHistory تلقائيًا من الـ signals
            return delivery

        # --- شحنات بحالات مختلفة ---
        make_delivery(
            'مول سيتي ستارز، مدينة نصر', 'فيلا 12، التجمع الخامس',
            customer_1, driver_1, 48,
            ['ASSIGNED', 'IN_TRANSIT', 'DELIVERED'],
        )
        make_delivery(
            'مخزن العبور', 'شارع الجمهورية، المنصورة',
            customer_3, driver_2, 24,
            ['ASSIGNED'],
        )
        make_delivery(
            'مطار القاهرة الدولي', 'كمبوند بادية، أكتوبر',
            customer_2, driver_1, 72,
            ['ASSIGNED', 'IN_TRANSIT', 'DELAYED'],
        )
        make_delivery(
            'محطة رمل، الإسكندرية', 'سيدي جابر، الإسكندرية',
            customer_2, None, 12,
            [],
        )
        make_delivery(
            'طنطا، الغربية', 'المهندسين، الجيزة',
            customer_3, None, 36,
            ['CANCELLED'],
        )

        # --- رسائل شات بوت تجريبية ---
        if not ChatMessage.objects.exists():
            ChatMessage.objects.create(user=customer_user_1, role='user', content='فين شحنتي؟')
            ChatMessage.objects.create(
                user=customer_user_1, role='assistant',
                content='شحنتك رقم ... في الطريق ومتوقعة توصل خلال ساعتين.',
            )

        self.stdout.write(self.style.SUCCESS(
            f'تم: {User.objects.count()} مستخدم، '
            f'{Customer.objects.count()} عميل، '
            f'{Driver.objects.count()} سائق، '
            f'{Delivery.objects.count()} شحنة، '
            f'{ChatMessage.objects.count()} رسالة شات'
        ))
        self.stdout.write('كلمة سر كل الحسابات التجريبية: demo12345')
