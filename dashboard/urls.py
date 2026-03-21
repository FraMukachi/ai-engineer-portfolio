from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('businesses/', views.businesses, name='businesses'),
    path('businesses/create/', views.create_business, name='create_business'),
    path('business/<str:business_id>/', views.business_detail, name='business_detail'),
    path('analytics/', views.analytics, name='analytics'),
    path('chat/', views.chat, name='chat'),
]
