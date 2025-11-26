from flask import Flask, request, jsonify
import sqlite3
from zk import ZK
import time

app = Flask(__name__)

device_ip = "192.168.1.20"
zk = ZK(device_ip, port=4370)
print("Connecting to device...")
conn = zk.connect()
print("Connected to ZKTeco!")


def get_db():
    return sqlite3.connect("payments.db")


def wait_for_fingerprint(timeout=20):
    start = time.time()
    for attendance in conn.live_capture():
        if time.time() - start > timeout:
            return None
        if attendance is None:
            continue
        return attendance.user_id


# ==============================
# TEST ITEMS ENDPOINT (1 item)
# ==============================
@app.route("/test_items", methods=["GET"])
def get_test_items():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT id, name, price, image FROM test_items")
    rows = cur.fetchall()
    db.close()

    items = []
    for r in rows:
        items.append({
            "id": r[0],
            "name": r[1],
            "price": r[2],
            "image": r[3]  # example: img/cakes/apple_crumble.jpg
        })
    return jsonify(items)


# =================================
# PAYMENT ENDPOINT (unchanged)
# =================================
@app.route("/pay", methods=["POST"])
def pay():
    data = request.get_json()
    total = data.get("total")

    print(f"\n💰 Waiting for fingerprint to pay: {total} IQD...")

    user_id = wait_for_fingerprint()

    if user_id is None:
        return jsonify({"success": False, "message": "No fingerprint detected"}), 400

    print(f"Fingerprint detected! User = {user_id}")

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    result = cur.fetchone()

    if not result:
        db.close()
        return jsonify({"success": False, "message": "User not found"}), 404

    balance = result[0]

    if balance < total:
        db.close()
        return jsonify({
            "success": False,
            "message": "Not enough balance",
            "user_id": user_id,
            "balance": balance
        })

    new_balance = balance - total

    cur.execute("UPDATE users SET balance=? WHERE user_id=?", (new_balance, user_id))
    cur.execute("INSERT INTO transactions (user_id, amount) VALUES (?,?)",
                (user_id, total))
    db.commit()
    db.close()

    print(f"Payment Success! User {user_id}, New Balance = {new_balance}")

    return jsonify({
        "success": True,
        "message": "Payment success",
        "user_id": user_id,
        "new_balance": new_balance
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
