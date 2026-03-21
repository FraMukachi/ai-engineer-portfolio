from django.contrib import admin
from django.urls import path, include
from dashboard import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('businesses/', views.businesses, name='businesses'),
    path('businesses/create/', views.create_business, name='create_business'),
    path('business/<str:business_id>/', views.business_detail, name='business_detail'),
    path('analytics/', views.analytics, name='analytics'),
    path('chat/', views.chat, name='chat'),
    path('api/businesses/', views.api_businesses, name='api_businesses'),
    path('api/analytics/', views.api_analytics, name='api_analytics'),
]
