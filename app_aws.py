from flask import Flask, render_template, request, redirect, url_for, session
import boto3
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "bakery_secret_key"

# ---------- AWS CLIENTS ----------
region = "ap-south-1"   # Mumbai region

dynamodb = boto3.resource("dynamodb", region_name=region)
sns = boto3.client("sns", region_name=region)

PRODUCTS_TABLE = dynamodb.Table("BakeryProducts")
ORDERS_TABLE = dynamodb.Table("BakeryOrders")

SNS_TOPIC_ARN = "arn:aws:sns:ap-south-1:123456789012:BakeryOrders"

# ---------- HOME ----------
@app.route("/")
def home():
    response = PRODUCTS_TABLE.scan()
    items = response.get("Items", [])
    return render_template("index.html", items=items)

# ---------- ADD TO CART ----------
@app.route("/add_to_cart/<product_id>")
def add_to_cart(product_id):
    if "cart" not in session:
        session["cart"] = []

    session["cart"].append(product_id)
    session.modified = True
    return redirect(url_for("cart"))

# ---------- VIEW CART ----------
@app.route("/cart")
def cart():
    cart_items = []
    total = 0

    if "cart" in session:
        for pid in session["cart"]:
            response = PRODUCTS_TABLE.get_item(Key={"product_id": pid})
            item = response.get("Item")
            if item:
                cart_items.append(item)
                total += int(item["price"])

    return render_template("cart.html", items=cart_items, total=total)

# ---------- PLACE ORDER ----------
@app.route("/place_order", methods=["POST"])
def place_order():
    if "cart" not in session or len(session["cart"]) == 0:
        return redirect(url_for("home"))

    order_id = str(uuid.uuid4())
    order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ORDERS_TABLE.put_item(
        Item={
            "order_id": order_id,
            "items": session["cart"],
            "order_date": order_date,
            "status": "Order Placed"
        }
    )

    # SNS Notification
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject="New Bakery Order 🍞",
        Message=f"New order placed!\nOrder ID: {order_id}\nTime: {order_date}"
    )

    session.pop("cart")

    return render_template("success.html", order_id=order_id)

# ---------- ADMIN: VIEW ORDERS ----------
@app.route("/admin/orders")
def admin_orders():
    response = ORDERS_TABLE.scan()
    orders = response.get("Items", [])
    return render_template("orders.html", orders=orders)

# ---------- RUN APP ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

