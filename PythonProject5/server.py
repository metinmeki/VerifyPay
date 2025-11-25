import sqlite3
import time
from zk import ZK

AMOUNT = 1000

db = sqlite3.connect("payments.db")
cur = db.cursor()

device_ip = "192.168.1.20"
zk = ZK(device_ip, port=4370)

print("Connecting to device...")
conn = zk.connect()
print("Connected!\n")

# ====== Get initial last log (ignore old logs) ======
logs = conn.get_attendance()
last_log_time = logs[-1].timestamp if logs else None

print("🔥 System started — ignoring all logs before:", last_log_time)

print("System Ready — Waiting for real fingerprint...\n")

while True:
    try:
        logs = conn.get_attendance()

        if not logs:
            time.sleep(0.5)
            continue

        last_log = logs[-1]

        # 1. Ignore any log older than startup
        if last_log_time and last_log.timestamp <= last_log_time:
            time.sleep(0.5)
            continue

        # 2. Real new log detected — update last_log_time
        last_log_time = last_log.timestamp

        user_id = last_log.user_id

        # 3. Ignore system user_id like 0 or 1 if they don't come from device finger scan
        if user_id == 0:
            print("⚠️ Ignoring system log (user_id = 0)")
            continue

        # 4. Print detected
        print(f"Detected User: {user_id} at {last_log.timestamp}")

        # === Payment Processing ===
        cur.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        result = cur.fetchone()

        if not result:
            print("User not found — skipping...\n")
            continue

        balance = result[0]

        if balance >= AMOUNT:
            new_balance = balance - AMOUNT

            cur.execute("UPDATE users SET balance=? WHERE user_id=?", (new_balance, user_id))
            cur.execute("INSERT INTO transactions (user_id, amount) VALUES (?,?)",
                        (user_id, AMOUNT))
            db.commit()

            print(f"Payment Success for User {user_id}")
            print(f"New Balance: {new_balance}\n")
        else:
            print("Not enough balance!\n")

    except Exception as e:
        print("Error:", e)
        time.sleep(1)
