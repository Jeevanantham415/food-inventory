from inventory.models import Alert, FoodItem
from datetime import datetime, date
from django.utils import timezone

class AlertSystem:
    def __init__(self):
        self.LOW_STOCK_THRESHOLD = 10
        self.EXPIRY_ALERT_DAYS = 3
    
    def check_item_alerts(self, item):
        """Check and update alerts for an item based on low stock and expiry"""
        alerts_created = []
        
        # Fetch current active alerts for this item
        existing_alerts = Alert.objects.filter(item=item, status='unread')
        active_types = {a.alert_type: a for a in existing_alerts}
        
        # Delete any legacy overstock alerts if they exist
        if 'overstock' in active_types:
            self.resolve_alert(active_types['overstock'].id)

        # 1. Check for low stock (< 10)
        if item.quantity < self.LOW_STOCK_THRESHOLD:
            if 'low_stock' not in active_types:
                alert = self.create_alert(
                    item=item,
                    alert_type='low_stock',
                    message=f'{item.name} is low on stock ({item.quantity} units left)',
                    priority='high'
                )
                alerts_created.append(alert)
        else:
            if 'low_stock' in active_types:
                self.resolve_alert(active_types['low_stock'].id)
        
        # 2. Check for expiry logic
        days_to_expiry = item.days_to_expiry
        if item.quantity > 0:
            if 0 <= days_to_expiry <= self.EXPIRY_ALERT_DAYS:
                if 'expiry' not in active_types:
                    alert = self.create_alert(
                        item=item,
                        alert_type='expiry',
                        message=f'{item.name} expires in {days_to_expiry} days ({item.expiry_date})',
                        priority='high' if days_to_expiry == 0 else 'medium'
                    )
                    alerts_created.append(alert)
                    
                if 'expired' in active_types:
                    self.resolve_alert(active_types['expired'].id)
                    
            elif days_to_expiry < 0:
                if 'expired' not in active_types:
                    alert = self.create_alert(
                        item=item,
                        alert_type='expired',
                        message=f'{item.name} has expired on {item.expiry_date}',
                        priority='high'
                    )
                    alerts_created.append(alert)
                    
                if 'expiry' in active_types:
                    self.resolve_alert(active_types['expiry'].id)
                    
            else:
                if 'expiry' in active_types:
                    self.resolve_alert(active_types['expiry'].id)
                if 'expired' in active_types:
                    self.resolve_alert(active_types['expired'].id)
        else:
            if 'expiry' in active_types:
                self.resolve_alert(active_types['expiry'].id)
            if 'expired' in active_types:
                self.resolve_alert(active_types['expired'].id)
        
        return alerts_created
    
    def create_alert(self, item, alert_type, message, priority='medium'):
        """Create a new alert"""
        alert = Alert.objects.create(
            item=item,
            alert_type=alert_type,
            message=message,
            priority=priority,
            status='unread'
        )
        return alert
    
    def resolve_alert(self, alert_id):
        """Resolve/Remove an existing alert"""
        try:
            alert = Alert.objects.get(id=alert_id)
            alert.status = 'resolved'
            alert.resolved_at = timezone.now()
            alert.save()
            return alert
        except Alert.DoesNotExist:
            return None
    
    def get_active_alerts(self, limit=10):
        """Get list of unread alerts ordered by priority and date"""
        return Alert.objects.filter(status='unread').exclude(alert_type='overstock').order_by('-created_at')[:limit]
    
    def run_full_system_check(self):
        """Check all items in database and generate/update alerts"""
        # Clean out any old overstock alerts first
        Alert.objects.filter(alert_type='overstock').delete()
        
        items = FoodItem.objects.all()
        created_count = 0
        for item in items:
            alerts = self.check_item_alerts(item)
            created_count += len(alerts)
        return created_count