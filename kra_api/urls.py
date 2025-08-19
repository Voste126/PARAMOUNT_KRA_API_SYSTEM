from django.urls import path
from . import views

urlpatterns = [
    path('token/', views.GetTokenView.as_view(), name='get-token'),
    path('pin-by-id/', views.PinByIDView.as_view(), name='pin-by-id'),
    path('pin-by-pin/', views.PinByPinView.as_view(), name='pin-by-pin'),
]
