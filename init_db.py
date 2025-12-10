import sqlite3

db = sqlite3.connect("payments.db")
cur = db.cursor()

users = [
    (2, "User2", 50000),
    (3, "User3", 5000),
    (1, "Metin", 20000),
]

for u in users:
    try:
        cur.execute("INSERT INTO users (user_id, name, balance) VALUES (?, ?, ?)", u)
        print(f"Added user {u[0]}")
    except:
        print(f"User {u[0]} already exists")

db.commit()
db.close()
print("DONE!")
