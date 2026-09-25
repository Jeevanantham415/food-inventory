from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, FoodItem, Transaction, Alert, DemandPrediction

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'created_at')
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_code', 'category', 'quantity', 'price', 'expiry_date', 'status')
    list_filter = ('category', 'status')
    search_fields = ('name', 'item_code', 'category')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('item', 'transaction_type', 'quantity', 'price_per_unit', 'total_amount', 'transaction_date', 'user')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('item__name', 'notes')

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('item', 'alert_type', 'priority', 'status', 'created_at', 'resolved_at')
    list_filter = ('alert_type', 'priority', 'status')
    search_fields = ('item__name', 'message')

@admin.register(DemandPrediction)
class DemandPredictionAdmin(admin.ModelAdmin):
    list_display = ('item', 'predicted_date', 'predicted_demand', 'confidence', 'created_at')
    list_filter = ('predicted_date',)
