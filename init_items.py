import sqlite3

db = sqlite3.connect("payments.db")
cur = db.cursor()

# Delete table if exists
cur.execute("DROP TABLE IF EXISTS test_items")

# Create new clean table
cur.execute("""
CREATE TABLE test_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price INTEGER,
    image TEXT
)
""")

# Insert the single test item
cur.execute("""
INSERT INTO test_items (name, price, image)
VALUES (?, ?, ?)
""", (
    "apple_crumble",
    19000,
    "img/cakes/apple_crumble.jpg"
))

db.commit()
db.close()

print("✔ Test item added successfully!")
