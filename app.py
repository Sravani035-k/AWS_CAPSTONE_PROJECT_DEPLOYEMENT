from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3, os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "secretkey"

DB_NAME = "bakery.db"
UPLOAD_FOLDER = "static/images"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ORDERS = []

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS items(
                id INTEGER PRIMARY KEY,
                name TEXT,
                price INTEGER,
                image TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                password TEXT)""")

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route('/')
def home():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    items = conn.execute("SELECT * FROM items").fetchall()
    conn.close()
    cart_count = sum(i.get("qty",1) for i in session.get("cart", []))
    return render_template('home.html', items=items, cart_count=cart_count)

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_NAME)
        user = conn.execute("SELECT * FROM users WHERE email=? AND password=?",
                            (email, password)).fetchone()
        conn.close()

        if user:
            session["user"] = email
            return redirect("/specials")
        else:
            return "Invalid credentials"

    return render_template("login.html")

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_NAME)
        conn.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",
                     (name,email,password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")

# ---------------- SPECIALS ----------------
@app.route("/specials")
def specials():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    items = conn.execute("SELECT * FROM items").fetchall()
    conn.close()

    cart = session.get("cart", [])

    return render_template("specials.html", items=items, cart=cart)

# ---------------- ADD TO CART ----------------
@app.route("/add_to_cart/<int:item_id>", methods=["POST"])
def add_to_cart(item_id):
    conn = sqlite3.connect(DB_NAME)
    item = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    conn.close()

    if "cart" not in session:
        session["cart"] = []

    cart = session["cart"]

    # check if item already in cart
    for i in cart:
        if i["id"] == item_id:
            i["qty"] += 1
            session.modified = True
            return redirect("/specials")

    # first time adding
    cart.append({
        "id": item[0],
        "name": item[1],
        "price": item[2],
        "image": item[3],
        "qty": 1
    })

    session["cart"] = cart
    session.modified = True
    return redirect("/specials")

# ---------------- INC / DEC ----------------
@app.route("/inc/<int:item_id>")
def inc(item_id):
    for i in session["cart"]:
        if i["id"] == item_id:
            i["qty"] += 1
    session.modified = True
    return redirect("/cart")

@app.route("/dec/<int:item_id>")
def dec(item_id):
    for i in session["cart"]:
        if i["id"] == item_id:
            i["qty"] -= 1
            if i["qty"] <= 0:
                session["cart"].remove(i)
            break
    session.modified = True
    return redirect("/cart")

# ---------------- CART ----------------
@app.route("/cart")
def cart():
    items = session.get("cart", [])
    item_total = sum(i["price"] * i["qty"] for i in items)
    delivery_fee = 50 if item_total > 0 else 0
    total = item_total + delivery_fee

    return render_template("cart.html",
                           items=items,
                           item_total=item_total,
                           delivery_fee=delivery_fee,
                           total=total)

# ---------------- CHECKOUT ----------------
@app.route("/checkout")
def checkout():
    items = session.get("cart", [])
    item_total = sum(i["price"] * i["qty"] for i in items)
    delivery_fee = 50 if item_total > 0 else 0
    total = item_total + delivery_fee

    return render_template("checkout.html",
                           item_total=item_total,
                           delivery_fee=delivery_fee,
                           total=total)

# ---------------- PAYMENT ----------------
@app.route("/payment", methods=["POST"])
def payment():
    delivery_info = request.form.to_dict()
    session["delivery_info"] = delivery_info

    items = session.get("cart", [])
    total = sum(i["price"] * i["qty"] for i in items) + 50

    return render_template("payment.html", total=total)

# ---------------- PLACE ORDER ----------------
@app.route("/place_order", methods=["POST"])
def place_order():
    cart_items = session.get("cart", [])
    if not cart_items:
        return redirect("/cart")

    total = sum(i["price"] * i["qty"] for i in cart_items) + 50
    expected_date = (datetime.now() + timedelta(days=3)).strftime("%d-%m-%Y")

    # Use keys consistent with templates
    order = {
        "items": cart_items,          # for orders.html
        "order_items": cart_items,    # for success.html
        "total": total,
        "expected_date": expected_date,
        "delivery": session.get("delivery_info", {})
    }

    ORDERS.append(order)

    session.pop("cart", None)
    session.pop("delivery_info", None)

    # Render success page
    return render_template("success.html", order=order)

# ---------------- USER ORDERS ----------------
@app.route("/orders")
def orders():
    return render_template("orders.html", orders=ORDERS)

# ---------------- ADMIN ORDERS ----------------
@app.route("/admin/orders")
def admin_orders():
    return render_template("admin_orders.html", orders=ORDERS)

# ---------------- DELETE ITEM ----------------
@app.route("/admin/delete_item/<int:item_id>")
def delete_item(item_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

# ---------------- EDIT ITEM ----------------
@app.route("/admin/edit_item/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    if request.method == "POST":
        name = request.form["name"]
        price = int(request.form["price"])
        image = request.files.get("image")

        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cur.execute("UPDATE items SET name=?, price=?, image=? WHERE id=?",
                        (name, price, filename, item_id))
        else:
            cur.execute("UPDATE items SET name=?, price=? WHERE id=?",
                        (name, price, item_id))

        conn.commit()
        conn.close()
        return redirect(url_for('admin'))

    cur.execute("SELECT * FROM items WHERE id=?", (item_id,))
    item = cur.fetchone()
    conn.close()
    return render_template("edit_item.html", item=item)

# ---------------- ADMIN ADD ITEMS ----------------
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        price = int(request.form['price'])
        image = request.files['image']

        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cur.execute("INSERT INTO items(name,price,image) VALUES(?,?,?)",
                        (name, price, filename))
            conn.commit()

        conn.close()
        return redirect(url_for('admin'))

    cur.execute("SELECT * FROM items")
    items = cur.fetchall()
    conn.close()

    return render_template('admin.html', items=items, orders=ORDERS)

if __name__ == "__main__":
    app.run(debug=True)
