import sqlite3

db = sqlite3.connect("payments.db")
cur = db.cursor()

# إدراج مستخدم جديد
cur.execute("""
INSERT INTO users (user_id, name, balance)
VALUES (1, 'Metin', 20000)
""")

db.commit()
db.close()

print("User added!")
