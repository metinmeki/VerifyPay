from flask import Flask, request, jsonify, render_template
import sqlite3
from zk import ZK
import time
import os
from werkzeug.utils import secure_filename

app = Flask(__name__, static_url_path="/static")

# ==========================
# IMAGE UPLOAD CONFIG
# ==========================
UPLOAD_FOLDER = "static/img/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==========================
# CONNECT TO DEVICE
# ==========================
DEVICE_IP = "192.168.1.20"   # Your correct IP
zk = ZK(DEVICE_IP, port=4370)

print("Connecting to ZKTeco device...")
conn = zk.connect()
print("Connected to ZKTeco!")


# ==========================
# DATABASE
# ==========================
def get_db():
    return sqlite3.connect("payments.db")


# ==========================
# LAST ATTENDANCE LOG
# ==========================
def get_last_log():
    try:
        logs = conn.get_attendance()
        if not logs:
            return None
        last = logs[-1]
        return (last.user_id, last.timestamp)
    except Exception as e:
        print("Error reading logs:", e)
        return None


# ==========================
# HOME PAGE
# ==========================
@app.route("/")
def home():
    return render_template("index.html")


# ==========================
# ADMIN PAGE
# ==========================
@app.route("/admin")
def admin_page():
    return render_template("admin.html")


# ==========================
# ADMIN – ADD ITEMS (UI)
# ==========================
@app.route("/admin/items", methods=["GET", "POST"])
def admin_items():
    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        category = request.form["category"]

        # ---- Handle Image Upload ----
        file = request.files["image"]
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            image_path = f"img/uploads/{filename}"
        else:
            image_path = "img/default.jpg"

        # ---- Insert into Database ----
        cur.execute("""
            INSERT INTO test_items (name, price, image, category)
            VALUES (?, ?, ?, ?)
        """, (name, price, image_path, category))
        db.commit()

    # Load all items
    cur.execute("SELECT id, name, price, image, category FROM test_items")
    items = cur.fetchall()

    db.close()
    return render_template("admin_items.html", items=items)


# ==========================
# API: LIST USERS
# ==========================
@app.route("/list_users")
def list_users():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT user_id, name, balance FROM users")
    rows = cur.fetchall()
    db.close()

    users = []
    for r in rows:
        users.append({
            "user_id": r[0],
            "name": r[1],
            "balance": r[2]
        })

    return jsonify(users)


# ==========================
# API: ADD USER
# ==========================
@app.route("/add_user", methods=["POST"])
def add_user():
    data = request.get_json()

    user_id = int(data["user_id"])
    name = data["name"]
    balance = int(data["balance"])

    db = get_db()
    cur = db.cursor()

    try:
        cur.execute(
            "INSERT INTO users (user_id, name, balance) VALUES (?, ?, ?)",
            (user_id, name, balance)
        )
        db.commit()
        msg = "User added successfully!"
    except:
        msg = "User already exists."

    db.close()
    return jsonify({"message": msg})


# ==========================
# GET ITEMS FOR POS
# ==========================
@app.route("/items", methods=["GET"])
def get_items():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT id, name, price, image, category FROM test_items")
    rows = cur.fetchall()
    db.close()

    items = []
    for r in rows:
        items.append({
            "id": r[0],
            "name": r[1],
            "price": r[2],
            "image": r[3],
            "category": r[4]
        })

    return jsonify(items)


# ==========================
# PAYMENT — WORKING VERSION
# ==========================
@app.route("/pay", methods=["POST"])
def pay():
    data = request.get_json()
    total = data.get("total")

    print(f"\nWaiting for fingerprint to pay: {total} IQD...")

    # Read last log before any new scan
    last_before = get_last_log()
    print("Last log before scan:", last_before)

    timeout = time.time() + 10
    new_log = None

    # Wait for new attendance
    while time.time() < timeout:
        current = get_last_log()

        if current and last_before:
            if current != last_before:
                new_log = current
                print("New fingerprint detected! User:", new_log[0])
                break

        elif current and not last_before:
            new_log = current
            print("New fingerprint detected! User:", new_log[0])
            break

        time.sleep(0.3)

    if not new_log:
        print("No fingerprint detected (timeout)")
        return jsonify({"success": False, "message": "No fingerprint detected"}), 400

    user_id = new_log[0]

    # ==========================
    # PAYMENT LOGIC
    # ==========================
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
    cur.execute("INSERT INTO transactions (user_id, amount) VALUES (?, ?)",
                (user_id, total))
    db.commit()
    db.close()

    print(f"Payment SUCCESS! User {user_id}, New Balance = {new_balance}")

    return jsonify({
        "success": True,
        "message": "Payment success",
        "user_id": user_id,
        "new_balance": new_balance
    })


# ==========================
# START SERVER
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
