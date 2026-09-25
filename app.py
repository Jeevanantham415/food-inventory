from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from database import db, User, FoodItem, Transaction, Alert, DemandPrediction
from models.prediction_model import DemandPredictor
from utils.alert_system import AlertSystem
from utils.data_processor import DataProcessor
from datetime import datetime, timedelta
import os
import json
import joblib
import pandas as pd
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Custom Jinja2 filters
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

app.jinja_env.filters['clamp'] = clamp
app.jinja_env.globals['calculate_discount'] = calculate_discount

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize AI components
predictor = DemandPredictor()
alert_system = AlertSystem()
data_processor = DataProcessor()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@inventory.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

# ============ ROUTES ============

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get dashboard statistics
    total_items = FoodItem.query.count()
    low_stock_items = FoodItem.query.filter(FoodItem.quantity < 10).count()
    expired_items = FoodItem.query.filter(
        FoodItem.expiry_date < datetime.now().date(),
        FoodItem.quantity > 0
    ).count()
    expiring_soon = FoodItem.query.filter(
        FoodItem.expiry_date <= datetime.now().date() + timedelta(days=3),
        FoodItem.expiry_date >= datetime.now().date(),
        FoodItem.quantity > 0
    ).count()
    
    # Get recent alerts
    recent_alerts = Alert.query.filter_by(status='unread').order_by(Alert.created_at.desc()).limit(5).all()
    
    # Get top selling items
    top_items = db.session.query(
        FoodItem,
        db.func.sum(Transaction.quantity).label('total_sold')
    ).join(Transaction).filter(
        Transaction.transaction_type == 'sale'
    ).group_by(FoodItem.id).order_by(db.desc('total_sold')).limit(5).all()
    
    # Get category distribution for the pie chart
    category_counts = db.session.query(
        FoodItem.category, 
        db.func.count(FoodItem.id)
    ).group_by(FoodItem.category).all()
    
    category_labels = [c[0] for c in category_counts]
    category_values = [c[1] for c in category_counts]
    
    return render_template('dashboard.html',
                         total_items=total_items,
                         low_stock_items=low_stock_items,
                         expired_items=expired_items,
                         expiring_soon=expiring_soon,
                         recent_alerts=recent_alerts,
                         top_items=top_items,
                         category_labels=category_labels,
                         category_values=category_values)

@app.route('/inventory')
@login_required
def inventory():
    category = request.args.get('category', 'all')
    search = request.args.get('search', '')
    
    query = FoodItem.query
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(FoodItem.name.ilike(f'%{search}%'))
    
    items = query.order_by(FoodItem.name).all()
    categories = db.session.query(FoodItem.category).distinct().all()
    
    return render_template('inventory.html', 
                         items=items, 
                         categories=[c[0] for c in categories],
                         selected_category=category,
                         search_query=search)

@app.route('/expiry-tracking')
@login_required
def expiry_tracking():
    days = int(request.args.get('days', 7))
    
    expiring_items = FoodItem.query.filter(
        FoodItem.expiry_date <= datetime.now().date() + timedelta(days=days),
        FoodItem.expiry_date >= datetime.now().date(),
        FoodItem.quantity > 0
    ).order_by(FoodItem.expiry_date).all()
    
    expired_items = FoodItem.query.filter(
        FoodItem.expiry_date < datetime.now().date(),
        FoodItem.quantity > 0
    ).order_by(FoodItem.expiry_date).all()
    
    from config import Config
    low_stock_items = FoodItem.query.filter(
        FoodItem.quantity < Config.LOW_STOCK_THRESHOLD
    ).order_by(FoodItem.quantity).all()
    
    return render_template('expiry_tracking.html',
                         expiring_items=expiring_items,
                         expired_items=expired_items,
                         low_stock_items=low_stock_items,
                         days_filter=days)

@app.route('/demand-prediction')
@login_required
def demand_prediction():
    items = FoodItem.query.order_by(FoodItem.name).all()
    selected_item = None
    item_id = request.args.get('item_id')
    if item_id:
        selected_item = FoodItem.query.get(item_id)
        
    return render_template('demand_prediction.html',
                         items=items,
                         selected_item=selected_item)

@app.route('/item-scanner')
@login_required
def item_scanner():
    return render_template('item_scanner.html')

@app.route('/transactions')
@login_required
def transactions():
    transactions = Transaction.query.order_by(Transaction.transaction_date.desc()).all()
    items = FoodItem.query.order_by(FoodItem.name).all()
    return render_template('transactions.html', transactions=transactions, items=items)

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

# ============ API ENDPOINTS ============

@app.route('/api/items', methods=['GET', 'POST'])
@login_required
def api_items():
    if request.method == 'GET':
        items = FoodItem.query.all()
        return jsonify([{
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'quantity': item.quantity,
            'price': item.price,
            'expiry_date': item.expiry_date.strftime('%Y-%m-%d'),
            'days_to_expiry': item.days_to_expiry,
            'is_low_stock': item.is_low_stock,
            'is_expired': item.is_expired
        } for item in items])
    
    elif request.method == 'POST':
        data = request.json
        try:
            price = float(data['price'])
            # Generate unique item code
            base_code = data['category'][:3].upper() + data['name'][:3].upper()
            item_code = base_code
            counter = 1
            while FoodItem.query.filter_by(item_code=item_code).first():
                item_code = f"{base_code}{counter}"
                counter += 1
            
            item = FoodItem(
                item_code=item_code,
                name=data['name'],
                category=data['category'],
                quantity=int(data['quantity']),
                price=price,
                expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
            )
            db.session.add(item)
            db.session.commit()
            
            # Check for alerts
            alert_system.check_item_alerts(item)
            
            return jsonify({'success': True, 'message': 'Item added successfully'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/items/<int:item_id>', methods=['PUT', 'DELETE'])
@login_required
def api_item(item_id):
    item = FoodItem.query.get_or_404(item_id)
    
    if request.method == 'PUT':
        data = request.json
        try:
            item.name = data.get('name', item.name)
            item.category = data.get('category', item.category)
            item.quantity = int(data.get('quantity', item.quantity))
            item.price = float(data.get('price', item.price))
            if 'expiry_date' in data:
                item.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
            db.session.commit()
            
            # Check for alerts
            alert_system.check_item_alerts(item)
            
            return jsonify({'success': True, 'message': 'Item updated successfully'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    elif request.method == 'DELETE':
        try:
            # Delete child records manually to prevent IntegrityError constraints
            Transaction.query.filter_by(item_id=item_id).delete()
            Alert.query.filter_by(item_id=item_id).delete()
            DemandPrediction.query.filter_by(item_id=item_id).delete()
            
            db.session.delete(item)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Item deleted successfully'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/transactions', methods=['POST'])
@login_required
def api_transactions():
    data = request.json
    try:
        item = FoodItem.query.get(data['item_id'])
        if not item:
            return jsonify({'success': False, 'error': 'Item not found'}), 404
            
        quantity = int(data['quantity'])
        price_per_unit = float(data['price_per_unit'])
        total_amount = quantity * price_per_unit
        trans_type = data['transaction_type']
        
        # Update stock based on transaction type
        if trans_type in ['sale', 'waste', 'discount']:
            if item.quantity < quantity:
                return jsonify({'success': False, 'error': 'Insufficient stock for this transaction'}), 400
            item.quantity -= quantity
        elif trans_type == 'restock':
            item.quantity += quantity
            
        transaction = Transaction(
            item_id=item.id,
            transaction_type=trans_type,
            quantity=quantity,
            price_per_unit=price_per_unit,
            total_amount=total_amount,
            notes=data.get('notes', ''),
            user_id=current_user.id
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        # Check alerts
        alert_system.check_item_alerts(item)
        
        return jsonify({'success': True, 'message': 'Transaction recorded successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/scan-item', methods=['POST'])
@login_required
def scan_item():
    # Simulate item scanning (in real implementation, this would use CV)
    data = request.json
    item_code = data.get('barcode')
    
    if item_code:
        item = FoodItem.query.filter_by(item_code=item_code).first()
        if item:
            return jsonify({
                'success': True,
                'item': {
                    'id': item.id,
                    'name': item.name,
                    'category': item.category,
                    'quantity': item.quantity,
                    'price': item.price,
                    'expiry_date': item.expiry_date.strftime('%Y-%m-%d')
                }
            })
    
    return jsonify({'success': False, 'error': 'Item not found'}), 404

@app.route('/api/alerts')
@login_required
def get_alerts():
    alerts = Alert.query.filter_by(status='unread').order_by(Alert.created_at.desc()).all()
    return jsonify([{
        'id': alert.id,
        'type': alert.alert_type,
        'message': alert.message,
        'priority': alert.priority,
        'created_at': alert.created_at.strftime('%Y-%m-%d %H:%M'),
        'item_name': alert.item.name if alert.item else 'Unknown Item'
    } for alert in alerts])

@app.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    total_items = FoodItem.query.count()
    low_stock_items = FoodItem.query.filter(FoodItem.quantity < 10).count()
    expired_items = FoodItem.query.filter(FoodItem.expiry_date < datetime.now().date()).count()
    expiring_soon = FoodItem.query.filter(
        FoodItem.expiry_date <= datetime.now().date() + timedelta(days=3),
        FoodItem.expiry_date >= datetime.now().date()
    ).count()
    
    return jsonify({
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'expired_items': expired_items,
        'expiring_soon': expiring_soon
    })

@app.route('/api/predict-status', methods=['POST'])
def predict_status():
    try:
        data = request.json
        item_name = data.get('name')
        category = data.get('category')
        quantity = int(data.get('quantity', 0))
        price = float(data.get('price', 0.0))
        days = int(data.get('days_to_expiry', 0))

        # Absolute paths for the AI Models
        model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'model')
        model = joblib.load(os.path.join(model_dir, "inventory_status_model.pkl"))
        scaler = joblib.load(os.path.join(model_dir, "scaler.pkl"))
        le_item = joblib.load(os.path.join(model_dir, "item_encoder.pkl"))
        le_category = joblib.load(os.path.join(model_dir, "category_encoder.pkl"))
        le_status = joblib.load(os.path.join(model_dir, "status_encoder.pkl"))

        # Transform inputs (Handle unseen classes gracefully)
        try:
            item_encoded = le_item.transform([item_name])[0]
        except ValueError:
            item_encoded = 0  # Fallback
            
        try:
            category_encoded = le_category.transform([category])[0]
        except ValueError:
            category_encoded = 0

        # Prediction DataFrame
        new_data = pd.DataFrame({
            "Item Name": [item_encoded],
            "Category": [category_encoded],
            "Quantity": [quantity],
            "Price": [price],
            "Days_To_Expiry": [days]
        })
        
        # Hardcoded rule for already expired items
        if days < 0:
            return jsonify({
                'success': True,
                'status': 'Expired Risk',
                'confidence': 100.0
            })
            
        new_data_scaled = scaler.transform(new_data)
        prediction = model.predict(new_data_scaled)
        result = le_status.inverse_transform(prediction)[0]
        
        # Confidence score
        probs = model.predict_proba(new_data_scaled)[0]
        confidence = float(max(probs) * 100)

        return jsonify({
            'success': True,
            'status': str(result),
            'confidence': round(confidence, 1)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============================
# GET SINGLE ITEM (FOR EDIT)
# ============================

@app.route('/api/items/<int:item_id>', methods=['GET'])
@login_required
def get_single_item(item_id):
    item = FoodItem.query.get_or_404(item_id)

    return jsonify({
        'id': item.id,
        'name': item.name,
        'category': item.category,
        'quantity': item.quantity,
        'price': item.price,
        'expiry_date': item.expiry_date.strftime('%Y-%m-%d')
    })


@app.route('/delete-item/<int:item_id>')
@login_required
def delete_item(item_id):
    item = FoodItem.query.get_or_404(item_id)

    # Cascade delete all related child records to prevent SQLite Integrity Constraints
    Transaction.query.filter_by(item_id=item.id).delete()
    Alert.query.filter_by(item_id=item.id).delete()
    DemandPrediction.query.filter_by(item_id=item.id).delete()

    db.session.delete(item)
    db.session.commit()

    flash("Item deleted successfully!", "success")

    return redirect(url_for('inventory'))  # redirect back to inventory page


if __name__ == '__main__':
    app.run(debug=True, port=5000)