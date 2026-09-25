from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import date

class User(AbstractUser):
    role = models.CharField(max_length=20, default='staff')  # admin, manager, staff
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password_hash(self, raw_password):
        self.set_password(raw_password)

    def check_password_hash(self, raw_password):
        return self.check_password(raw_password)

    def __str__(self):
        return f"{self.username} ({self.role})"


class FoodItem(models.Model):
    item_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    quantity = models.IntegerField(default=0)
    price = models.FloatField()
    expiry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, default='active')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.item_code})"

    @property
    def is_expired(self):
        return self.expiry_date < date.today()

    @property
    def days_to_expiry(self):
        return (self.expiry_date - date.today()).days

    @property
    def is_low_stock(self):
        return self.quantity < 10


class Transaction(models.Model):
    item = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20)  # sale, restock, waste, discount
    quantity = models.IntegerField()
    price_per_unit = models.FloatField(null=True, blank=True)
    total_amount = models.FloatField(null=True, blank=True)
    transaction_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, default='')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')

    class Meta:
        ordering = ['-transaction_date']

    def __str__(self):
        return f"{self.transaction_type.upper()} - {self.item.name} x {self.quantity}"


class Alert(models.Model):
    item = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=50)  # expiry, low_stock, overstock, expired
    message = models.CharField(max_length=500)
    priority = models.CharField(max_length=20, default='medium')  # high, medium, low
    status = models.CharField(max_length=20, default='unread')  # unread, read, resolved
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.priority.upper()}] {self.alert_type} - {self.message}"


class DemandPrediction(models.Model):
    item = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name='predictions')
    predicted_date = models.DateField()
    predicted_demand = models.IntegerField()
    confidence = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Prediction for {self.item.name} on {self.predicted_date}: {self.predicted_demand}"
