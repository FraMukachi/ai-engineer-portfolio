import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages

def home(request):
    return render(request, 'dashboard/home.html')

def businesses(request):
    try:
        response = requests.get(f'{settings.BOTBASE_API_URL}/api/businesses', timeout=10)
        data = response.json()
        return render(request, 'dashboard/businesses.html', {'businesses': data.get('businesses', [])})
    except Exception as e:
        return render(request, 'dashboard/businesses.html', {'businesses': [], 'error': str(e)})

def business_detail(request, business_id):
    try:
        biz = requests.get(f'{settings.BOTBASE_API_URL}/api/business/{business_id}', timeout=10)
        bookings = requests.get(f'{settings.BOTBASE_API_URL}/api/business/{business_id}/bookings', timeout=10)
        orders = requests.get(f'{settings.BOTBASE_API_URL}/api/business/{business_id}/orders', timeout=10)
        
        context = {
            'business': biz.json() if biz.status_code == 200 else {},
            'bookings': bookings.json().get('bookings', []) if bookings.status_code == 200 else [],
            'orders': orders.json().get('orders', []) if orders.status_code == 200 else []
        }
        return render(request, 'dashboard/business_detail.html', context)
    except Exception as e:
        return render(request, 'dashboard/business_detail.html', {'error': str(e)})

def create_business(request):
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name'),
            'email': request.POST.get('email'),
            'type': request.POST.get('type', 'general'),
            'phone': request.POST.get('phone', '')
        }
        try:
            response = requests.post(f'{settings.BOTBASE_API_URL}/api/business/register', json=data, timeout=10)
            if response.status_code == 200:
                messages.success(request, 'Business created!')
                return redirect('businesses')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'dashboard/create_business.html')

def analytics(request):
    try:
        analytics_data = requests.get(f'{settings.BOTBASE_API_URL}/api/analytics', timeout=10)
        bots_status = requests.get(f'{settings.BOTBASE_API_URL}/api/bots/status', timeout=10)
        
        context = {
            'analytics': analytics_data.json() if analytics_data.status_code == 200 else {},
            'bots': bots_status.json() if bots_status.status_code == 200 else {}
        }
        return render(request, 'dashboard/analytics.html', context)
    except Exception as e:
        return render(request, 'dashboard/analytics.html', {'error': str(e)})

def chat(request):
    return render(request, 'dashboard/chat.html')

def api_businesses(request):
    try:
        response = requests.get(f'{settings.BOTBASE_API_URL}/api/businesses', timeout=10)
        return JsonResponse(response.json())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def api_analytics(request):
    try:
        response = requests.get(f'{settings.BOTBASE_API_URL}/api/analytics', timeout=10)
        return JsonResponse(response.json())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
