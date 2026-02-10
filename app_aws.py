from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
import uuid
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError

app = Flask(__name___)
app.secret_key = "artisan_secret_key"

# ---------------- AWS CONFIGURATION ----------------
REGION = "ap-south-1"
BUCKET_NAME = "artisan-bakery-images"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

# ---------------- DYNAMODB TABLES ----------------
users_table = dynamodb.Table("Users")
items_table = dynamodb.Table("BakeryItems")
orders_table = dynamodb.Table("Orders")

# ---------------- SNS TOPIC ARN ----------------
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:490004646397:aws_capstone"


# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect(url_for("login"))


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users_table.put_item(Item={
            "user_id": str(uuid.uuid4()),
            "username": username,
            "password": password
        })

        flash("Registered Successfully!")
        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        response = users_table.scan()
        users = response.get("Items", [])

        for user in users:
            if user["username"] == username and user["password"] == password:
                session["user"] = username
                return redirect(url_for("specials"))

        flash("Invalid Credentials")

    return render_template("login.html")


# ---------------- SHOW ITEMS ----------------
@app.route("/specials")
def specials():
    response = items_table.scan()
    items = response.get("Items", [])
    return render_template("specials.html", items=items, cart=session.get("cart", []))


# ---------------- ADMIN ADD ITEM ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        name = request.form["name"]
        price = int(request.form["price"])
        image = request.files["image"]

        filename = secure_filename(image.filename)
        s3.upload_fileobj(
            image,
            BUCKET_NAME,
            filename,
            ExtraArgs={"ContentType": image.content_type}
        )

        image_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"

        items_table.put_item(Item={
            "item_id": str(uuid.uuid4()),
            "name": name,
            "price": price,
            "image": image_url
        })

        flash("Item Added Successfully!")
        return redirect(url_for("admin"))

    response = items_table.scan()
    items = response.get("Items", [])
    return render_template("admin.html", items=items)


# ---------------- ADD TO CART ----------------
@app.route("/add_to_cart/<item_id>", methods=["POST"])
def add_to_cart(item_id):
    cart = session.get("cart", [])

    found = False
    for c in cart:
        if c["id"] == item_id:
            c["qty"] += 1
            found = True

    if not found:
        cart.append({"id": item_id, "qty": 1})

    session["cart"] = cart
    return redirect(url_for("specials"))


# ---------------- PLACE ORDER ----------------
@app.route("/place_order")
def place_order():
    cart = session.get("cart", [])
    if not cart:
        flash("Cart is empty!")
        return redirect(url_for("specials"))

    order_id = str(uuid.uuid4())

    orders_table.put_item(Item={
        "order_id": order_id,
        "user": session.get("user"),
        "items": cart
    })

    # SNS Notification
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=f"New Order Placed!\nOrder ID: {order_id}\nUser: {session.get('user')}\nItems: {cart}",
        Subject="New Bakery Order"
    )

    session["cart"] = []
    flash("Order placed successfully!")
    return redirect(url_for("specials"))


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- RUN ----------------
if _name_ == "_main_":
    app.run(debug=True)
    



