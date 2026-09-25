import os
# pyrefly: ignore [missing-import]
import django
import random
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_project.settings')
django.setup()

from inventory.models import User, FoodItem, Transaction, Alert
from utils.alert_system import AlertSystem

CATEGORIES = [
    "Dairy", "Bakery", "Beverages", "Vegetables", 
    "Fruits", "Meat", "Frozen", "Snacks", "Grains", "Groceries"
]

ITEM_NAME_TEMPLATES = {
    "Dairy": ["Whole Milk 1L", "Skimmed Milk", "Greek Yogurt 200g", "Amul Butter 500g", "Cheddar Cheese", "Paneer 200g", "Condensed Milk", "Whipped Cream", "Mozzarella Cheese", "Flavored Milk"],
    "Bakery": ["Whole Wheat Bread", "White Bread", "Croissant", "Chocolate Muffin", "Garlic Bread", "Burger Buns", "Hot Dog Buns", "Fruit Cake", "Bagel", "Donut"],
    "Beverages": ["Fresh Orange Juice", "Apple Juice 1L", "Green Tea Box", "Ground Coffee 250g", "Sparkling Water", "Mango Smoothie", "Lemonade 1L", "Energy Drink", "Cold Coffee", "Iced Tea"],
    "Vegetables": ["Fresh Tomatoes 1kg", "Potatoes 1kg", "Onions 1kg", "Carrots 500g", "Broccoli", "Spinach Pack", "Bell Peppers 300g", "Cucumber 500g", "Garlic 250g", "Ginger 200g"],
    "Fruits": ["Red Apples 1kg", "Bananas 1 Dozen", "Fresh Oranges 1kg", "Green Grapes 500g", "Watermelon", "Papaya", "Pineapple", "Strawberries 250g", "Pomegranate 1kg", "Kiwi 4 Pack"],
    "Meat": ["Chicken Breast 500g", "Mutton Curry Cut 500g", "Fish Fillet 400g", "Pork Chops 500g", "Chicken Wings 1kg", "Minced Meat 500g", "Egg Pack of 12", "Turkey Slices", "Prawns 300g", "Bacon Strips"],
    "Frozen": ["Frozen Peas 1kg", "French Fries 750g", "Vanilla Ice Cream 1L", "Frozen Corn 500g", "Veg Nuggets Pack", "Frozen Pizza", "Chicken Nuggets", "Frozen Berries", "Ice Cream Bars", "Frozen Paratha"],
    "Snacks": ["Potato Chips 150g", "Salted Cashews 200g", "Roasted Almonds 200g", "Dark Chocolate Bar", "Popcorn Bag", "Digestive Biscuits", "Nachos Pack", "Pretzels", "Mixed Nuts", "Granola Bar"],
    "Grains": ["Basmati Rice 5kg", "Sona Masoori Rice 5kg", "Wheat Atta 5kg", "Rolled Oats 1kg", "Quinoa 500g", "Pasta Penne 500g", "Macaroni 500g", "Brown Rice 2kg", "Poha 1kg", "Vermicelli 400g"],
    "Groceries": ["Refined Oil 1L", "Olive Oil 500ml", "Iodized Salt 1kg", "Sugar 1kg", "Turmeric Powder 200g", "Red Chili Powder 200g", "Garam Masala 100g", "Soy Sauce 200ml", "Tomato Ketchup 500g", "Honey 500g"]
}

def seed():
    print("Clearing old inventory records...")
    Alert.objects.all().delete()
    Transaction.objects.all().delete()
    FoodItem.objects.all().delete()

    # 1. Create Superuser / Admin
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@inventory.com',
            password='admin123',
            role='admin'
        )
        print("Created admin user: admin / admin123")

    today = date.today()
    alert_sys = AlertSystem()

    print("Generating exactly 502 food inventory items...")

    items_to_create = []
    
    random.seed(42)

    for i in range(1, 503):
        cat = CATEGORIES[(i - 1) % len(CATEGORIES)]
        base_name = ITEM_NAME_TEMPLATES[cat][(i - 1) % len(ITEM_NAME_TEMPLATES[cat])]
        item_name = f"{base_name} #{i}" if i > 100 else base_name
        
        item_code = f"{cat[:3].upper()}{i:04d}"

        if i <= 40:
            quantity = random.randint(1, 9)
        else:
            quantity = random.randint(15, 200)

        if i <= 45:
            expiry_offset = random.randint(0, 3)
        elif i <= 95:
            expiry_offset = random.randint(4, 7)
        elif i <= 110:
            expiry_offset = random.randint(-5, -1)
        else:
            expiry_offset = random.randint(8, 180)

        expiry_date = today + timedelta(days=expiry_offset)
        price = round(random.uniform(20.0, 500.0), 2)

        items_to_create.append(FoodItem(
            item_code=item_code,
            name=item_name,
            category=cat,
            quantity=quantity,
            price=price,
            expiry_date=expiry_date
        ))

    FoodItem.objects.bulk_create(items_to_create)
    print(f"Successfully created {FoodItem.objects.count()} items in inventory!")

    created_alerts = alert_sys.run_full_system_check()
    print(f"Ran system alert check: Generated {created_alerts} active alerts.")

if __name__ == '__main__':
    seed()
