from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='staff')  # admin, manager, staff
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # dairy, bakery, beverages, etc.
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    status = db.Column(db.String(20), default='active')  # active, expired, sold_out
    
    # Relationships
    transactions = db.relationship('Transaction', backref='food_item', lazy=True)
    
    @property
    def is_expired(self):
        return self.expiry_date < datetime.now().date()
    
    @property
    def days_to_expiry(self):
        return (self.expiry_date - datetime.now().date()).days
    
    @property
    def is_low_stock(self):
        return self.quantity <= 10

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    transaction_type = db.Column(db.String(20))  # sale, restock, waste, discount
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float)
    total_amount = db.Column(db.Float)
    transaction_date = db.Column(db.DateTime, default=datetime.now)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recorded_by = db.relationship('User', backref='transactions')

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    alert_type = db.Column(db.String(50))  # expiry, low_stock, high_waste
    message = db.Column(db.String(500), nullable=False)
    priority = db.Column(db.String(20), default='medium')  # high, medium, low
    status = db.Column(db.String(20), default='unread')  # unread, read, resolved
    created_at = db.Column(db.DateTime, default=datetime.now)
    resolved_at = db.Column(db.DateTime)
    
    item = db.relationship('FoodItem', backref='alerts')

class DemandPrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    predicted_date = db.Column(db.Date, nullable=False)
    predicted_demand = db.Column(db.Integer, nullable=False)
    confidence = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    item = db.relationship('FoodItem', backref='predictions')