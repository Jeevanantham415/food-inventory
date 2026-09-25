import sqlite3
import os

db_path = r'data\inventory.db'

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Rename current table
cur.execute('ALTER TABLE food_item RENAME TO food_item_old')
conn.commit()
conn.close()

print("Table renamed to food_item_old. Recreating schema...")

# Run Flask app db.create_all() to recreate schema
from app import app, db
with app.app_context():
    db.create_all()

print("Schema recreated. Migrating data...")

# Reconnect to copy data
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute('''
    INSERT INTO food_item (id, item_code, name, category, quantity, price, expiry_date, status, created_at, updated_at)
    SELECT id, item_code, name, category, quantity, price, expiry_date, status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    FROM food_item_old
''')

cur.execute('DROP TABLE food_item_old')
conn.commit()
conn.close()

print("Migration successful! Extra columns removed.")
