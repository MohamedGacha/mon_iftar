from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.RegisterUserAPIView.as_view(), name='register_user'),
    path('first-login/', views.FirstLoginAPIView.as_view(), name='first_login'),
    path('regular-login/', views.RegularLoginAPIView.as_view(), name='regular_login'),
]
