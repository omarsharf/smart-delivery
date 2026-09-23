from django.shortcuts import render,redirect
from django.contrib.auth import login  as asauth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required 
from .models import Delivery, Customer
from .forms import DeliveryForm, RegisterForm
def index(request):
    return render(request,'delivery/home.html')
def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            asauth_login(request, user)
            return redirect('home')   
    else:
        form = AuthenticationForm()
    return render(request,'delivery/login.html',{'form':form})
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Customer.objects.create(
                user=user,
                name=form.cleaned_data['name'],
                phone=form.cleaned_data['phone'],
                address='')
            asauth_login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'delivery/register.html', {'form': form})
@login_required
def add(request):
    if request.method == 'POST':
        form = DeliveryForm(request.POST)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.customer = request.user.customer
            delivery.save()
            return redirect('/admin/')
    else:
        form = DeliveryForm()
    return render(request, 'delivery/request_shipment.html', {'form': form})
# Create your views here.
