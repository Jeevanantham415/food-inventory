from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime, timedelta, date
import json

from .models import User, FoodItem, Transaction, Alert
from utils.alert_system import AlertSystem
from utils.data_processor import DataProcessor

alert_system = AlertSystem()
data_processor = DataProcessor()

# Custom Jinja/Django Template Helper Filters
def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def calculate_discount(days_to_expiry):
    if days_to_expiry <= 0:
        return 50  # Expired items
    elif days_to_expiry <= 3:
        return 30  # Very close to expiry
    elif days_to_expiry <= 7:
        return 20  # Close to expiry
    elif days_to_expiry <= 14:
        return 10  # Approaching expiry
    else:
        return 0   # Fresh items


# ============ PAGE VIEWS ============

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'index.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, 'Registration successful! Please login.')
            return redirect('login')
    
    return render(request, 'register.html')


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('index')


@login_required
def dashboard(request):
    today = date.today()
    
    total_items = FoodItem.objects.count()
    low_stock_items = FoodItem.objects.filter(quantity__lt=10).count()
    expired_items = FoodItem.objects.filter(expiry_date__lt=today, quantity__gt=0).count()
    expiring_soon = FoodItem.objects.filter(
        expiry_date__lte=today + timedelta(days=3),
        expiry_date__gte=today,
        quantity__gt=0
    ).count()
    
    recent_alerts = Alert.objects.filter(status='unread').exclude(alert_type='overstock').order_by('-created_at')[:6]
    
    # Category distribution for pie chart
    category_counts = FoodItem.objects.values('category').annotate(count=Count('id'))
    category_labels = [c['category'] for c in category_counts]
    category_values = [c['count'] for c in category_counts]
    
    context = {
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'expired_items': expired_items,
        'expiring_soon': expiring_soon,
        'recent_alerts': recent_alerts,
        'category_labels': category_labels,
        'category_values': category_values
    }
    return render(request, 'dashboard.html', context)


@login_required
def inventory_view(request):
    category = request.GET.get('category', 'all')
    search = request.GET.get('search', '')
    
    query = FoodItem.objects.all()
    
    if category != 'all':
        query = query.filter(category=category)
    
    if search:
        query = query.filter(name__icontains=search)
    
    items = query.order_by('name')
    categories = FoodItem.objects.values_list('category', flat=True).distinct()
    
    context = {
        'items': items,
        'categories': list(categories),
        'selected_category': category,
        'search_query': search
    }
    return render(request, 'inventory.html', context)


@login_required
def expiry_tracking(request):
    days = int(request.GET.get('days', 7))
    today = date.today()
    
    expiring_items = FoodItem.objects.filter(
        expiry_date__lte=today + timedelta(days=days),
        expiry_date__gte=today,
        quantity__gt=0
    ).order_by('expiry_date')

    expired_items = FoodItem.objects.filter(
        expiry_date__lt=today,
        quantity__gt=0
    ).order_by('expiry_date')
    
    low_stock_items = FoodItem.objects.filter(
        quantity__lt=10
    ).order_by('quantity')
    
    context = {
        'expiring_items': expiring_items,
        'expired_items': expired_items,
        'low_stock_items': low_stock_items,
        'days_filter': days
    }
    return render(request, 'expiry_tracking.html', context)


@login_required
def add_item_view(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            category = request.POST.get('category')
            quantity = int(request.POST.get('quantity'))
            price = float(request.POST.get('price'))
            expiry_date_str = request.POST.get('expiry_date')

            base_code = category[:3].upper() + name[:3].upper()
            item_code = base_code
            counter = 1
            while FoodItem.objects.filter(item_code=item_code).exists():
                item_code = f"{base_code}{counter}"
                counter += 1

            item = FoodItem.objects.create(
                item_code=item_code,
                name=name,
                category=category,
                quantity=quantity,
                price=price,
                expiry_date=datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            )
            alert_system.check_item_alerts(item)
            messages.success(request, f"Item '{name}' added successfully!")
            return redirect('inventory')
        except Exception as e:
            messages.error(request, f"Error adding item: {str(e)}")
            
    return render(request, 'add_item.html')


@login_required
def transactions_view(request):
    transactions = Transaction.objects.select_related('item', 'user').order_by('-transaction_date')
    items = FoodItem.objects.order_by('name')
    return render(request, 'transactions.html', {'transactions': transactions, 'items': items})


@login_required
def profile_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if email:
            request.user.email = email

        if new_password:
            if new_password == confirm_password:
                request.user.set_password(new_password)
                request.user.save()
                login(request, request.user)
                messages.success(request, "Profile and password updated successfully!")
                return redirect('profile')
            else:
                messages.error(request, "Passwords do not match!")
        else:
            request.user.save()
            messages.success(request, "Profile details updated successfully!")
            return redirect('profile')

    return render(request, 'profile.html')


# ============ API ENDPOINTS ============

@csrf_exempt
@login_required
def api_items(request):
    if request.method == 'GET':
        items = FoodItem.objects.all()
        data = [{
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'quantity': item.quantity,
            'price': item.price,
            'expiry_date': item.expiry_date.strftime('%Y-%m-%d'),
            'days_to_expiry': item.days_to_expiry,
            'is_low_stock': item.is_low_stock,
            'is_expired': item.is_expired
        } for item in items]
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            payload = json.loads(request.body)
            price = float(payload['price'])
            base_code = payload['category'][:3].upper() + payload['name'][:3].upper()
            item_code = base_code
            counter = 1
            while FoodItem.objects.filter(item_code=item_code).exists():
                item_code = f"{base_code}{counter}"
                counter += 1
            
            item = FoodItem.objects.create(
                item_code=item_code,
                name=payload['name'],
                category=payload['category'],
                quantity=int(payload['quantity']),
                price=price,
                expiry_date=datetime.strptime(payload['expiry_date'], '%Y-%m-%d').date()
            )
            
            alert_system.check_item_alerts(item)
            return JsonResponse({'success': True, 'message': 'Item added successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@login_required
def api_item_detail(request, item_id):
    item = get_object_or_404(FoodItem, id=item_id)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'quantity': item.quantity,
            'price': item.price,
            'expiry_date': item.expiry_date.strftime('%Y-%m-%d')
        })
        
    elif request.method == 'PUT':
        try:
            payload = json.loads(request.body)
            item.name = payload.get('name', item.name)
            item.category = payload.get('category', item.category)
            item.quantity = int(payload.get('quantity', item.quantity))
            item.price = float(payload.get('price', item.price))
            if 'expiry_date' in payload:
                item.expiry_date = datetime.strptime(payload['expiry_date'], '%Y-%m-%d').date()
            item.save()
            
            alert_system.check_item_alerts(item)
            return JsonResponse({'success': True, 'message': 'Item updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
            
    elif request.method == 'DELETE':
        try:
            item.delete()
            return JsonResponse({'success': True, 'message': 'Item deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@login_required
def api_transactions(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            item = FoodItem.objects.filter(id=payload['item_id']).first()
            if not item:
                return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)
                
            quantity = int(payload['quantity'])
            price_per_unit = float(payload['price_per_unit'])
            total_amount = quantity * price_per_unit
            trans_type = payload['transaction_type']
            
            if trans_type in ['sale', 'waste', 'discount']:
                if item.quantity < quantity:
                    return JsonResponse({'success': False, 'error': 'Insufficient stock for this transaction'}, status=400)
                item.quantity -= quantity
            elif trans_type == 'restock':
                item.quantity += quantity
            item.save()
                
            transaction = Transaction.objects.create(
                item=item,
                transaction_type=trans_type,
                quantity=quantity,
                price_per_unit=price_per_unit,
                total_amount=total_amount,
                notes=payload.get('notes', ''),
                user=request.user
            )
            
            alert_system.check_item_alerts(item)
            return JsonResponse({'success': True, 'message': 'Transaction recorded successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def get_alerts(request):
    alerts = Alert.objects.filter(status='unread').exclude(alert_type='overstock').order_by('-created_at')
    return JsonResponse([{
        'id': alert.id,
        'type': alert.alert_type,
        'message': alert.message,
        'priority': alert.priority,
        'created_at': alert.created_at.strftime('%Y-%m-%d %H:%M'),
        'item_name': alert.item.name if alert.item else 'Unknown Item'
    } for alert in alerts], safe=False)


@csrf_exempt
@login_required
def api_resolve_alert(request, alert_id):
    try:
        alert = get_object_or_404(Alert, id=alert_id)
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.save()
        return JsonResponse({'success': True, 'message': 'Alert removed successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def dashboard_stats(request):
    today = date.today()
    total_items = FoodItem.objects.count()
    low_stock_items = FoodItem.objects.filter(quantity__lt=10).count()
    expired_items = FoodItem.objects.filter(expiry_date__lt=today).count()
    expiring_soon = FoodItem.objects.filter(
        expiry_date__lte=today + timedelta(days=3),
        expiry_date__gte=today
    ).count()
    
    return JsonResponse({
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'expired_items': expired_items,
        'expiring_soon': expiring_soon
    })


@login_required
def delete_item(request, item_id):
    item = get_object_or_404(FoodItem, id=item_id)
    item.delete()
    messages.success(request, "Item deleted successfully!")
    return redirect('inventory')
