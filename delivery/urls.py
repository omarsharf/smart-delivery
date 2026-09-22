from django.urls import path,include
from . import views

urlpatterns = [
   
path('request/', views.add, name='request_shipment'),
]