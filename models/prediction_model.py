import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import joblib
import os

class DemandPredictor:
    def __init__(self, model_path='models/trained_models/'):
        self.model_path = model_path
        os.makedirs(model_path, exist_ok=True)
        self.models = {}
        self.scalers = {}
        self.load_models()
    
    def load_models(self):
        """Load pre-trained models if they exist"""
        model_files = os.listdir(self.model_path)
        for file in model_files:
            if file.endswith('.pkl'):
                item_id = int(file.split('_')[0])
                self.models[item_id] = joblib.load(os.path.join(self.model_path, file))
    
    def train_model(self, item_id, historical_data):
        """Train a demand prediction model for an item"""
        if len(historical_data) < 30:
            return None
        
        # Prepare features
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['day_of_month'] = df['date'].dt.day
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Lag features
        for lag in [1, 7, 14, 30]:
            df[f'sales_lag_{lag}'] = df['sales'].shift(lag)
        
        df = df.dropna()
        
        if len(df) < 20:
            return None
        
        # Prepare training data
        X = df[['day_of_week', 'month', 'day_of_month', 'is_weekend', 
                'sales_lag_1', 'sales_lag_7', 'sales_lag_14', 'sales_lag_30']]
        y = df['sales']
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Save model
        joblib.dump(model, os.path.join(self.model_path, f'{item_id}_model.pkl'))
        self.models[item_id] = model
        
        return model
    
    def predict_demand(self, item_id, days=30):
        """Predict demand for next n days"""
        # Generate sample predictions (in real app, use actual historical data)
        predictions = []
        base_date = datetime.now()
        
        # Simulate predictions based on day of week and seasonality
        for i in range(days):
            date = base_date + timedelta(days=i)
            day_of_week = date.weekday()
            month = date.month
            
            # Simulate prediction logic
            base_demand = 50  # Base demand
            weekday_factor = 1.2 if day_of_week < 5 else 0.8  # Lower on weekends
            season_factor = 1.1 if month in [11, 12] else 0.9 if month in [6, 7] else 1.0
            
            predicted = int(base_demand * weekday_factor * season_factor + np.random.normal(0, 5))
            predicted = max(10, min(predicted, 200))  # Keep within bounds
            
            predictions.append({
                'date': date.strftime('%Y-%m-%d'),
                'predicted_demand': predicted,
                'confidence': np.random.uniform(0.7, 0.95)
            })
        
        return predictions
    
    def get_recommended_order(self, item_id, current_stock, lead_time=2):
        """Calculate recommended order quantity"""
        predictions = self.predict_demand(item_id, days=lead_time + 7)
        total_predicted_demand = sum(p['predicted_demand'] for p in predictions[:lead_time + 7])
        safety_stock = total_predicted_demand * 0.2  # 20% safety stock
        
        recommended = total_predicted_demand + safety_stock - current_stock
        return max(0, int(recommended))