from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import login  as asauth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Delivery, Customer, Driver,StatusHistory, ChatMessage
from .forms import DeliveryForm, RegisterForm
from django.contrib.auth import logout

def index(request):
    return render(request,'delivery/home.html')
def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            asauth_login(request, user)
            if user.role == 'driver':
                return redirect('driver_home')
            if user.role == 'dispatcher':
                return redirect('dispatch_home')
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'delivery/login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            if form.cleaned_data['role'] == 'driver':
                user.role = 'driver'
                user.save()
                Driver.objects.create(
                    user=user,
                    name=form.cleaned_data['name'],
                    phone=form.cleaned_data['phone'],
                    vehicle_type=form.cleaned_data['vehicle_type'] or 'van',
                )
            else:
                Customer.objects.create(
                    user=user,
                    name=form.cleaned_data['name'],
                    phone=form.cleaned_data['phone'],
                    address='')
            asauth_login(request, user)
            if user.role == 'driver':
                return redirect('driver_home')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'delivery/register.html', {'form': form})
@login_required
def add(request):
    if request.user.role != 'customer':
        return redirect('home')
    if request.method == 'POST':
        form = DeliveryForm(request.POST)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.customer = request.user.customer
            delivery.save()
            StatusHistory.objects.create(
                delivery=delivery,
                old_status=None,
                new_status='PENDING',
                changed_by=request.user,
            )
            return redirect('/track/?number=' + str(delivery.tracking_number))
    else:
        form = DeliveryForm()
    return render(request, 'delivery/request_shipment.html', {'form': form})
def track(request):
    delivery=None
    number=request.GET.get('number')
    if number:
        delivery=get_object_or_404(Delivery,tracking_number=number)
    return render(request, 'delivery/track.html', {'delivery': delivery})

@login_required
def driver_home(request):
    if request.user.role != 'driver':
        return redirect('home')

    if request.method == 'POST':
        delivery = get_object_or_404(Delivery, id=request.POST.get('delivery_id'), driver=request.user.driver)
        new_status = request.POST.get('new_status')
        if new_status in ['IN_TRANSIT', 'DELIVERED', 'DELAYED'] and new_status != delivery.status:
            StatusHistory.objects.create(
                delivery=delivery,
                old_status=delivery.status,
                new_status=new_status,
                changed_by=request.user,
            )
            delivery.status = new_status
            delivery.save()
        return redirect('driver_home')

    driver = request.user.driver
    deliveries = Delivery.objects.filter(driver=driver).exclude(status='DELIVERED').order_by('scheduled_date')
    return render(request, 'delivery/driver_home.html', {'deliveries': deliveries})


def make_reply(message, user):
    message = message.strip()
    # لو فيه رقم شحنة كامل في الرسالة → نرد بحالتها الحقيقية من الداتابيز
    for word in message.split():
        if len(word) == 36 and word.count('-') == 4:
            delivery = Delivery.objects.filter(tracking_number=word).first()
            if delivery and delivery.customer.user == user:
                return f'شحنتك ({word[:8]}) حالتها الآن: {delivery.get_status_display()} — الميعاد: {delivery.scheduled_date:%Y-%m-%d %H:%M}'
            return 'الرقم ده مش موجود أو مش تابع لحسابك.'
    if 'شحن' in message or 'طلب' in message:
        return 'تقدر تطلب شحنة جديدة من صفحة "اطلب شحنة" في القايمة فوق 🚚'
    if 'سعر' in message or 'تكلفة' in message:
        return 'التسعير حسب نوع المركبة: موتوسيكل للخفيف، مركبة للمتوسط، ومركبة كبيرة للحجم الكبير.'
    if 'سلام' in message or 'أهلا' in message or 'اهلا' in message:
        return 'أهلاً بيك! أنا المساعد الذكي لتوصيل ذكي 🤖 ابعت رقم شحنة كامل (زي 29ea6f72-...) وأنا أقولك حالتها.'
    return 'لسه بتعلم 😅 — ابعت رقم شحنة كامل وأنا أقولك حالتها فوراً.'


@login_required
def chat_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    user_message = request.POST.get('message', '').strip()
    if not user_message:
        return JsonResponse({'reply': 'اكتب حاجة الأول 😄'})
    reply = make_reply(user_message, request.user)
    ChatMessage.objects.create(user=request.user, role='user', content=user_message)
    ChatMessage.objects.create(user=request.user, role='assistant', content=reply)
    return JsonResponse({'reply': reply})
@login_required
def chat_page(request):
    history = ChatMessage.objects.filter(user=request.user).order_by('created_at')
    return render(request, 'delivery/chat_page.html', {'history': history})


@login_required
def dispatch_home(request):
    if request.user.role != 'dispatcher':
        return redirect('home')

    if request.method == 'POST':
        delivery = get_object_or_404(Delivery, id=request.POST.get('delivery_id'), status='PENDING')
        driver = get_object_or_404(Driver, id=request.POST.get('driver_id'))
        StatusHistory.objects.create(
            delivery=delivery,
            old_status=delivery.status,
            new_status='ASSIGNED',
            changed_by=request.user,
        )
        delivery.driver = driver
        delivery.status = 'ASSIGNED'
        delivery.save()
        return redirect('dispatch_home')

    pending = Delivery.objects.filter(status='PENDING').order_by('created_at')
    drivers = Driver.objects.all()
    return render(request, 'delivery/dispatch_home.html', {'pending': pending, 'drivers': drivers})


@login_required
def customer_dashboard(request):
    if request.user.role != 'customer':
        return redirect('home')
    status_filter = request.GET.get('status')
    deliveries = Delivery.objects.filter(customer=request.user.customer)
    if status_filter:
        deliveries = deliveries.filter(status=status_filter)
    deliveries = deliveries.order_by('-scheduled_date')

    all_mine = Delivery.objects.filter(customer=request.user.customer)
    return render(request, 'delivery/customer_dashboard.html', {
        'deliveries': deliveries,
        'total_count': all_mine.count(),
        'active_count': all_mine.exclude(status__in=['DELIVERED', 'CANCELLED']).count(),
        'delivered_count': all_mine.filter(status='DELIVERED').count(),
        'status_filter': status_filter,
    })



def logout_view(request):
    logout(request)
    return render(request, 'delivery/logout.html')




# Create your views here.
