from django.urls import path
from . import views

urlpatterns = [
    # Main Pages
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('expiry-tracking/', views.expiry_tracking, name='expiry_tracking'),
    path('add-item/', views.add_item_view, name='add_item'),
    path('transactions/', views.transactions_view, name='transactions'),
    path('profile/', views.profile_view, name='profile'),
    path('delete-item/<int:item_id>/', views.delete_item, name='delete_item'),

    # APIs
    path('api/items/', views.api_items, name='api_items'),
    path('api/items/<int:item_id>/', views.api_item_detail, name='api_item_detail'),
    path('api/transactions/', views.api_transactions, name='api_transactions'),
    path('api/alerts/', views.get_alerts, name='api_alerts'),
    path('api/alerts/<int:alert_id>/resolve/', views.api_resolve_alert, name='api_resolve_alert'),
    path('api/dashboard-stats/', views.dashboard_stats, name='api_dashboard_stats'),
]
