from database import db, Alert, FoodItem
from datetime import datetime
from config import Config

class AlertSystem:
    def __init__(self):
        self.config = Config()
    
    def check_item_alerts(self, item):
        """Check and update alerts for an item based on its current state"""
        alerts_created = []
        
        # Fetch current active alerts for this item
        existing_alerts = Alert.query.filter_by(item_id=item.id, status='unread').all()
        # Dictionary of type -> alert object
        active_types = {a.alert_type: a for a in existing_alerts}
        
        # 1. Check for low stock
        if item.quantity < self.config.LOW_STOCK_THRESHOLD:
            if 'low_stock' not in active_types:
                alert = self.create_alert(
                    item_id=item.id,
                    alert_type='low_stock',
                    message=f'{item.name} is low on stock ({item.quantity} units left)',
                    priority='high'
                )
                alerts_created.append(alert)
        else:
            if 'low_stock' in active_types:
                self.resolve_alert(active_types['low_stock'].id)
        
        # 2. Check for overstock
        if item.quantity > 100 * 1.2:
            if 'overstock' not in active_types:
                alert = self.create_alert(
                    item_id=item.id,
                    alert_type='overstock',
                    message=f'{item.name} is overstocked ({item.quantity} units)',
                    priority='medium'
                )
                alerts_created.append(alert)
        else:
            if 'overstock' in active_types:
                self.resolve_alert(active_types['overstock'].id)
        
        # 3. Check for expiry logic
        days_to_expiry = item.days_to_expiry
        if item.quantity > 0:
            if 0 <= days_to_expiry <= self.config.EXPIRY_ALERT_DAYS:
                # Expiring soon
                if 'expiry' not in active_types:
                    alert = self.create_alert(
                        item_id=item.id,
                        alert_type='expiry',
                        message=f'{item.name} expires in {days_to_expiry} days ({item.expiry_date})',
                        priority='high' if days_to_expiry == 0 else 'medium'
                    )
                    alerts_created.append(alert)
                    
                if 'expired' in active_types:
                    self.resolve_alert(active_types['expired'].id)
                    
            elif days_to_expiry < 0:
                # Already expired
                if 'expired' not in active_types:
                    alert = self.create_alert(
                        item_id=item.id,
                        alert_type='expired',
                        message=f'{item.name} has expired on {item.expiry_date}',
                        priority='high'
                    )
                    alerts_created.append(alert)
                    
                if 'expiry' in active_types:
                    self.resolve_alert(active_types['expiry'].id)
                    
            else:
                # Safe distance from expiry
                if 'expiry' in active_types:
                    self.resolve_alert(active_types['expiry'].id)
                if 'expired' in active_types:
                    self.resolve_alert(active_types['expired'].id)
        else:
            # Item quantity is 0, resolve expiry alerts
            if 'expiry' in active_types:
                self.resolve_alert(active_types['expiry'].id)
            if 'expired' in active_types:
                self.resolve_alert(active_types['expired'].id)
        
        return alerts_created
    
    def create_alert(self, item_id, alert_type, message, priority='medium'):
        """Create a new alert"""
        alert = Alert(
            item_id=item_id,
            alert_type=alert_type,
            message=message,
            priority=priority,
            status='unread'
        )
        db.session.add(alert)
        db.session.commit()
        return alert
    
    def mark_as_read(self, alert_id):
        """Mark an alert as read"""
        alert = Alert.query.get(alert_id)
        if alert:
            alert.status = 'read'
            alert.resolved_at = datetime.now()
            db.session.commit()
            return True
        return False
        
    def resolve_alert(self, alert_id):
        """Automatically resolve an alert when the condition is no longer met"""
        alert = Alert.query.get(alert_id)
        if alert:
            alert.status = 'resolved'
            alert.resolved_at = datetime.now()
            db.session.commit()
            return True
        return False
    
    def get_active_alerts(self, limit=50):
        """Get all active alerts"""
        return Alert.query.filter_by(status='unread').order_by(
            Alert.priority.desc(), Alert.created_at.desc()
        ).limit(limit).all()