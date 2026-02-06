# AWS_CAPSTONE_PROJECT_DEPLOYEMENT

Artisan Bakery Project
Project Overview

Artisan Bakery is a local bakery management web application that allows users to browse bakery items, add items to their cart, and place orders. The admin can manage the bakery items, including adding, updating, and deleting products.

This project is built using Flask (Python) for the backend and HTML, CSS, and JavaScript for the frontend.

Features

User signup and login system

Admin panel to manage bakery items

Browse and view bakery items

Add items to cart and update quantity

Place orders

Responsive design

Installation

Clone the repository:

git clone <repository-url>


Navigate to the project directory:

cd artisan-bakery


Install required Python packages:

pip install -r requirements.txt


Create the database:

python
>>> from app import init_db
>>> init_db()
>>> exit()


Run the Flask application:

python app.py


Open your browser and go to:

http://127.0.0.1:5000

Folder Structure
artisan-bakery/
│
├─ static/               # CSS, JS, images
├─ templates/            # HTML templates
├─ app.py                # Main Flask application
├─ bakery.db             # SQLite database
├─ requirements.txt      # Python dependencies
└─ README.md             # Project documentation

Dependencies

Flask

SQLite3

Werkzeug

Jinja2

(Install using pip install -r requirements.txt)

Usage

Signup as a new user or login if you already have an account.

Browse bakery items and add them to your cart.

Admin can login to manage items.

Place orders and view cart details.

License

This project is for learning purposes and personal use.
