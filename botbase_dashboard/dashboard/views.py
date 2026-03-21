import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
import json

def home(request):
    """Dashboard home page"""
    return render(request, 'dashboard/home.html')

def businesses(request):
    """List all businesses"""
    try:
        response = requests.get(f'{settings.BOTBASE_API_URL}/api/businesses')
        data = response.json()
        return render(request, 'dashboard/businesses.html', {'businesses': data.get('businesses', [])})
    except:
        return render(request, 'dashboard/businesses.html', {'businesses': [], 'error': 'Cannot connect to BotBase API'})

def business_detail(request, business_id):
    """View business details"""
    try:
        biz_response = requests.get(f'{settings.BOTBASE_API_URL}/api/business/{business_id}')
        bookings_response = requests.get(f'{settings.BOTBASE_API_URL}/api/business/{business_id}/bookings')
        orders_response = requests.get(f'{settings.BOTBASE_API_URL}/api/business/{business_id}/orders')
        docs_response = requests.get(f'{settings.BOTBASE_API_URL}/api/business/{business_id}/documents')
        
        context = {
            'business': biz_response.json() if biz_response.status_code == 200 else {},
            'bookings': bookings_response.json().get('bookings', []) if bookings_response.status_code == 200 else [],
            'orders': orders_response.json().get('orders', []) if orders_response.status_code == 200 else [],
            'documents': docs_response.json().get('documents', []) if docs_response.status_code == 200 else []
        }
        return render(request, 'dashboard/business_detail.html', context)
    except Exception as e:
        return render(request, 'dashboard/business_detail.html', {'error': str(e)})

def create_business(request):
    """Create a new business"""
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name'),
            'email': request.POST.get('email'),
            'type': request.POST.get('type', 'general'),
            'phone': request.POST.get('phone', '')
        }
        try:
            response = requests.post(f'{settings.BOTBASE_API_URL}/api/business/register', json=data)
            if response.status_code == 200:
                messages.success(request, 'Business created successfully!')
                return redirect('businesses')
            else:
                messages.error(request, 'Failed to create business')
        except:
            messages.error(request, 'Cannot connect to BotBase API')
    return render(request, 'dashboard/create_business.html')

def analytics(request):
    """View analytics dashboard"""
    try:
        response = requests.get(f'{settings.BOTBASE_API_URL}/api/analytics')
        bots_response = requests.get(f'{settings.BOTBASE_API_URL}/api/bots/status')
        ai_response = requests.get(f'{settings.BOTBASE_API_URL}/api/ai/status')
        
        context = {
            'analytics': response.json() if response.status_code == 200 else {},
            'bots': bots_response.json() if bots_response.status_code == 200 else {},
            'ai': ai_response.json() if ai_response.status_code == 200 else {}
        }
        return render(request, 'dashboard/analytics.html', context)
    except:
        return render(request, 'dashboard/analytics.html', {'error': 'Cannot connect to BotBase API'})

def chat(request):
    """AI chat interface"""
    return render(request, 'dashboard/chat.html')
