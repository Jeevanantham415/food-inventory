import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from django.utils import timezone
from inventory.models import FoodItem, Transaction
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.processed_data = {}
    
    def process_inventory_data(self):
        """Process all inventory data for analysis"""
        try:
            items = FoodItem.objects.all()
            cutoff_date = timezone.now() - timedelta(days=90)
            transactions = Transaction.objects.filter(transaction_date__gte=cutoff_date)
            
            # Create DataFrames
            items_df = pd.DataFrame([{
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'quantity': item.quantity,
                'price': item.price,
                'expiry_date': item.expiry_date,
                'days_to_expiry': item.days_to_expiry,
                'is_low_stock': item.is_low_stock,
                'is_expired': item.is_expired
            } for item in items])
            
            transactions_df = pd.DataFrame([{
                'id': t.id,
                'item_id': t.item_id,
                'type': t.transaction_type,
                'quantity': t.quantity,
                'price': t.price_per_unit,
                'total': t.total_amount,
                'date': t.transaction_date,
                'notes': t.notes
            } for t in transactions])
            
            # Process data
            self.processed_data = {
                'inventory_summary': self.get_inventory_summary(items_df),
                'category_analysis': self.get_category_analysis(items_df),
                'expiry_analysis': self.get_expiry_analysis(items_df),
                'sales_analysis': self.get_sales_analysis(transactions_df),
                'waste_analysis': self.get_waste_analysis(items_df, transactions_df)
            }
            
            return self.processed_data
            
        except Exception as e:
            logger.error(f"Error processing inventory data: {e}")
            return {}
    
    def get_inventory_summary(self, items_df):
        """Generate inventory summary statistics"""
        if items_df.empty:
            return {}
        
        return {
            'total_items': len(items_df),
            'total_quantity': int(items_df['quantity'].sum()),
            'total_value': float((items_df['quantity'] * items_df['price']).sum()),
            'low_stock_items': int(items_df['is_low_stock'].sum()),
            'expired_items': int(items_df['is_expired'].sum()),
            'expiring_soon': int(((items_df['days_to_expiry'] <= 3) & (items_df['days_to_expiry'] >= 0)).sum()),
            'avg_price': float(items_df['price'].mean())
        }
    
    def get_category_analysis(self, items_df):
        """Analyze inventory by category"""
        if items_df.empty:
            return {}
        
        category_stats = items_df.groupby('category').agg({
            'quantity': 'sum',
            'price': 'mean',
            'id': 'count'
        }).rename(columns={'id': 'item_count'})
        
        category_stats['value'] = category_stats['quantity'] * category_stats['price']
        
        return category_stats.to_dict('index')
    
    def get_expiry_analysis(self, items_df):
        """Analyze expiry-related data"""
        if items_df.empty:
            return {}
        
        expiry_stats = {
            'expiry_distribution': {
                'expired': int(items_df['is_expired'].sum()),
                'expiring_0_3': int(((items_df['days_to_expiry'] <= 3) & 
                                   (items_df['days_to_expiry'] >= 0)).sum()),
                'expiring_4_7': int(((items_df['days_to_expiry'] > 3) & 
                                   (items_df['days_to_expiry'] <= 7)).sum()),
                'expiring_8_14': int(((items_df['days_to_expiry'] > 7) & 
                                    (items_df['days_to_expiry'] <= 14)).sum()),
                'expiring_15_30': int(((items_df['days_to_expiry'] > 14) & 
                                     (items_df['days_to_expiry'] <= 30)).sum()),
                'safe': int(items_df['days_to_expiry'] > 30)
            },
            'expiry_value_at_risk': float(
                items_df[items_df['days_to_expiry'] <= 7]['quantity'] * 
                items_df[items_df['days_to_expiry'] <= 7]['price']
            ).sum()
        }
        
        return expiry_stats
    
    def get_sales_analysis(self, transactions_df):
        """Analyze sales data"""
        if transactions_df.empty:
            return {}
        
        sales_df = transactions_df[transactions_df['type'] == 'sale'].copy()
        if sales_df.empty:
            return {}
        
        sales_df['date'] = pd.to_datetime(sales_df['date']).dt.date
        daily_sales = sales_df.groupby('date').agg({
            'quantity': 'sum',
            'total': 'sum'
        }).sort_index()
        
        return {
            'total_sales': float(sales_df['total'].sum()),
            'total_units_sold': int(sales_df['quantity'].sum()),
            'avg_daily_sales': float(daily_sales['total'].mean()),
            'avg_daily_units': float(daily_sales['quantity'].mean()),
            'best_selling_day': daily_sales['total'].idxmax().strftime('%Y-%m-%d') 
                               if not daily_sales.empty else None,
            'sales_trend': self.calculate_sales_trend(daily_sales)
        }
    
    def get_waste_analysis(self, items_df, transactions_df):
        """Analyze waste patterns"""
        if transactions_df.empty:
            return {}
        
        waste_df = transactions_df[transactions_df['type'] == 'waste'].copy()
        if waste_df.empty:
            return {}
        
        waste_by_category = waste_df.merge(
            items_df[['id', 'category']],
            left_on='item_id',
            right_on='id',
            how='left'
        ).groupby('category').agg({
            'quantity': 'sum',
            'total': 'sum'
        })
        
        total_waste_value = float(waste_df['total'].sum())
        total_inventory_value = float((items_df['quantity'] * items_df['price']).sum())
        
        return {
            'total_waste_units': int(waste_df['quantity'].sum()),
            'total_waste_value': total_waste_value,
            'waste_rate': float(total_waste_value / total_inventory_value * 100) 
                         if total_inventory_value > 0 else 0,
            'waste_by_category': waste_by_category.to_dict('index'),
            'avg_daily_waste': float(waste_df.groupby(
                pd.to_datetime(waste_df['date']).dt.date
            )['total'].mean().mean())
        }
    
    def calculate_sales_trend(self, daily_sales, window=7):
        """Calculate sales trend over time"""
        if len(daily_sales) < window * 2:
            return 0
        
        recent_sales = daily_sales['total'].tail(window).mean()
        previous_sales = daily_sales['total'].head(window).mean()
        
        if previous_sales == 0:
            return 0
        
        return float(((recent_sales - previous_sales) / previous_sales) * 100)
    
    def get_item_health_score(self, item):
        """Calculate health score for an item (0-100)"""
        score = 100
        
        # Stock level penalty
        stock_ratio = item.quantity / 100
        if stock_ratio < 0.2:
            score -= 30
        elif stock_ratio > 1.2:
            score -= 20
        
        # Expiry penalty
        if item.days_to_expiry <= 0:
            score -= 50
        elif item.days_to_expiry <= 3:
            score -= 30
        elif item.days_to_expiry <= 7:
            score -= 15
        
        return max(0, min(100, score))
    
    def predict_stockout_date(self, item, daily_sales_rate):
        """Predict when stock will run out"""
        if daily_sales_rate <= 0:
            return None
        
        days_of_supply = item.quantity / daily_sales_rate
        stockout_date = datetime.now() + timedelta(days=days_of_supply)
        
        return stockout_date.date()
    
    def generate_reorder_recommendation(self, item, lead_time_days=2, safety_factor=1.2):
        """Generate reorder recommendation"""
        avg_daily_sales = 10
        lead_time_demand = avg_daily_sales * lead_time_days
        safety_stock = lead_time_demand * (safety_factor - 1)
        reorder_point = lead_time_demand + safety_stock
        order_quantity = max(0, 100 - item.quantity)
        
        return {
            'reorder_point': round(reorder_point),
            'safety_stock': round(safety_stock),
            'recommended_order': round(order_quantity),
            'current_stock': item.quantity,
            'stockout_risk': 'High' if item.quantity < reorder_point else 'Low'
        }