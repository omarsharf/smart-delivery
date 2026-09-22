from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required 
from .models import Delivery
from.forms import DeliveryForm

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
