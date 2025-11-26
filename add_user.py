import sqlite3

db = sqlite3.connect("payments.db")
cur = db.cursor()

cur.execute("""
INSERT INTO users (user_id, name, balance)
VALUES (3, 'User3', 20000)
""")

db.commit()
db.close()

print("User added!")
