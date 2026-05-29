from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import re

# load_dotenv()
from pathlib import Path
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.getenv("SECRET_KEY")
# DATABASE CONFIG

# DB_HOST = os.getenv("MYSQLHOST")
# DB_USER = os.getenv("MYSQLUSER")
# DB_PASSWORD = os.getenv("MYSQLPASSWORD")
# DB_NAME = os.getenv("MYSQLDATABASE")
# DB_PORT = os.getenv("MYSQLPORT", "3306")

# app.config['SQLALCHEMY_DATABASE_URI'] = (
#     f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
#     f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# )

DATABASE_URL = os.getenv("DATABASE_URL")

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
# ---------------- MODELS ---------------- #

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    role = db.Column(
        db.String(20),
        default='user'
    )
    profile_image = db.Column(db.Text)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100))

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    supplier_id = db.Column(db.Integer)
    product_name = db.Column(db.String(255))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)
    rating = db.Column(db.Float)
    image_url = db.Column(db.Text)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    total_price = db.Column(db.Float)
    order_date = db.Column(db.DateTime)

# ---------------- ROUTES ---------------- #
@app.route('/')
def home():

    if 'user' not in session:
        return redirect('/login')

    query = request.args.get('query')
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)

    products_query = Product.query

    # SEARCH LOGIC
    if query:

        query_lower = query.lower()

        products_query = products_query.filter(
            Product.product_name.ilike(f"%{query}%") |
            Product.description.ilike(f"%{query}%")
        )

        # CHEAP PRODUCTS
        if "cheap" in query_lower:
            products_query = products_query.filter(
                Product.price < 5000
            )

        # EXPENSIVE PRODUCTS
        if "expensive" in query_lower:
            products_query = products_query.filter(
                Product.price > 50000
            )

        # TOP RATED
        if "top rated" in query_lower:
            products_query = products_query.order_by(
                Product.rating.desc()
            )

        # LOW STOCK
        if "low stock" in query_lower:
            products_query = products_query.filter(
                Product.stock < 20
            )

        # HIGH STOCK
        if "high stock" in query_lower:
            products_query = products_query.filter(
                Product.stock > 100
            )

        # UNDER PRICE FILTER
        under_match = re.search(r'under (\d+)', query_lower)

        if under_match:

            max_price = int(under_match.group(1))

            products_query = products_query.filter(
                Product.price <= max_price
            )

        # ABOVE PRICE FILTER
        above_match = re.search(r'above (\d+)', query_lower)

        if above_match:

            min_price = int(above_match.group(1))

            products_query = products_query.filter(
                Product.price >= min_price
            )

    # CATEGORY FILTER
    if category:

        selected_category = Category.query.filter_by(
            category_name=category
        ).first()

        if selected_category:

            products_query = products_query.filter(
                Product.category_id == selected_category.id
            )

    products = products_query.paginate(
        page=page,
        per_page=9
    )

    total_products = Product.query.count()

    total_categories = Category.query.count()

    total_suppliers = db.session.query(
        Product.supplier_id
    ).distinct().count()

    avg_rating = db.session.query(
        db.func.avg(Product.rating)
    ).scalar()

    if avg_rating is None:
        avg_rating = 0
    else:
        avg_rating = round(avg_rating, 1)

    categories = Category.query.all()
    print(session)
    return render_template(
        'dashboard/home.html',
        products=products,
        categories=categories,
        total_products=total_products,
        total_categories=total_categories,
        total_suppliers=total_suppliers,
        avg_rating=avg_rating
    )

@app.route('/products')
def products_page():

    if 'user' not in session:
        return redirect('/login')

    products = Product.query.order_by(
        Product.id.desc()
    ).all()

    return render_template(
        'dashboard/products.html',
        products=products
    )

@app.route('/categories')
def categories_page():

    if 'user' not in session:
        return redirect('/login')

    categories = Category.query.all()

    return render_template(
        'dashboard/categories.html',
        categories=categories
    )

@app.route('/orders')
def orders_page():

    if 'user' not in session:
        return redirect('/login')

    orders = Order.query.order_by(
        Order.id.desc()
    ).all()

    return render_template(
        'dashboard/orders.html',
        orders=orders
    )

@app.route('/admin-dashboard')
def admin_dashboard():

    if 'user' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/')

    total_users = User.query.count()

    total_products = Product.query.count()

    total_admins = User.query.filter_by(
        role='admin'
    ).count()

    total_orders = Order.query.count()

    return render_template(
        'dashboard/admin_dashboard.html',
        total_users=total_users,
        total_products=total_products,
        total_admins=total_admins,
        total_orders=total_orders
    )

@app.route('/product/<int:id>')
def product_detail(id):

    if 'user' not in session:
        return redirect('/login')

    product = Product.query.get_or_404(id)

    return render_template(
        'dashboard/product_detail.html',
        product=product
    )

@app.route('/place-order/<int:id>', methods=['POST'])
def place_order(id):

    if 'user' not in session:
        return redirect('/login')

    product = Product.query.get_or_404(id)

    user = User.query.filter_by(
        email=session['user']
    ).first()

    quantity = int(
        request.form['quantity']
    )

    # CHECK STOCK
    if quantity > product.stock:

        flash(
            'Not enough stock available.',
            'danger'
        )

        return redirect(f'/product/{id}')

    total_price = quantity * product.price

    # CREATE ORDER
    order = Order(

        user_id=user.id,

        product_id=product.id,

        quantity=quantity,

        total_price=total_price,

        order_date=datetime.utcnow()
    )

    # REDUCE STOCK
    product.stock -= quantity

    db.session.add(order)

    db.session.commit()

    flash(
        'Order placed successfully!',
        'success'
    )

    return redirect('/orders')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(
            request.form['password']
        ).decode('utf-8')

        user = User(
            username=username,
            email=email,
            password=password
        )

        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect('/login')

    return render_template('auth/signup.html')

@app.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if 'user' not in session:
        return redirect('/login')
    if session.get('role') != 'admin':
        return redirect('/')
    if request.method == 'POST':
        image = request.files['image']
        filename = secure_filename(image.filename)
        image_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            filename
        )
        image.save(image_path)
        new_product = Product(
            category_id=1,
            supplier_id=1,
            product_name=request.form['product_name'],
            description=request.form['description'],
            price=float(request.form['price']),
            stock=int(request.form['stock']),
            rating=float(request.form['rating']),
            image_url='/' + image_path
        )
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect('/products')

    return render_template(
        'dashboard/add_product.html'
    )
@app.route('/edit-product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if 'user' not in session:
        return redirect('/login')
    if session.get('role') != 'admin':
        return redirect('/')
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.product_name = request.form['product_name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.stock = int(request.form['stock'])
        product.rating = float(request.form['rating'])
        product.image_url = request.form['image_url']
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(f'/product/{product.id}')
    return render_template(
        'dashboard/edit_product.html',
        product=product
    )
@app.route('/delete-product/<int:id>')
def delete_product(id):
    if session.get('role') != 'admin':
        return redirect('/')
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect('/')

@app.route('/analytics')
def analytics():

    if 'user' not in session:
        return redirect('/login')

    total_products = Product.query.count()

    total_categories = Category.query.count()

    avg_rating = db.session.query(
        db.func.avg(Product.rating)
    ).scalar()

    avg_rating = round(avg_rating or 0, 1)

    return render_template(
        'dashboard/analytics.html',
        total_products=total_products,
        total_categories=total_categories,
        avg_rating=avg_rating
    )

@app.route('/category-analytics')
def category_analytics():

    if 'user' not in session:
        return redirect('/login')

    categories = Category.query.all()

    category_names = []

    product_counts = []

    for category in categories:

        count = Product.query.filter_by(
            category_id=category.id
        ).count()

        category_names.append(
            category.category_name
        )

        product_counts.append(count)

    return render_template(
        'dashboard/category_analytics.html',
        category_names=category_names,
        product_counts=product_counts
    )

@app.route('/update-profile', methods=['POST'])
def update_profile():

    if 'user' not in session:
        return redirect('/login')

    user = User.query.filter_by(
        email=session['user']
    ).first()
    user.username = request.form['username']
    image = request.files.get('profile_image')
    if image and image.filename != '':
        filename = secure_filename(image.filename)
        image_path = os.path.join(
            'static/profile_pics',
            filename
        )
        image.save(image_path)
        user.profile_image = '/' + image_path
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect('/settings')

@app.route('/change-password', methods=['POST'])
def change_password():

    if 'user' not in session:
        return redirect('/login')

    user = User.query.filter_by(
        email=session['user']
    ).first()

    old_password = request.form['old_password']

    new_password = request.form['new_password']

    confirm_password = request.form['confirm_password']

    # VERIFY OLD PASSWORD
    if not bcrypt.check_password_hash(
        user.password,
        old_password
    ):

        flash(
            'Old password is incorrect.',
            'danger'
        )

        return redirect('/settings')

    # VERIFY NEW PASSWORD MATCH
    if new_password != confirm_password:

        flash(
            'New passwords do not match.',
            'warning'
        )

        return redirect('/settings')

    # PASSWORD LENGTH CHECK
    if len(new_password) < 6:

        flash(
            'Password must be at least 6 characters.',
            'warning'
        )

        return redirect('/settings')

    # HASH NEW PASSWORD
    hashed_password = bcrypt.generate_password_hash(
        new_password
    ).decode('utf-8')

    user.password = hashed_password

    db.session.commit()

    flash(
        'Password updated successfully!',
        'success'
    )

    return redirect('/settings')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user'] = user.email
            session['role'] = user.role
            flash('Logged in successfully!', 'success')
            return redirect('/')
        else:
            flash('Invalid email or password', 'danger')

    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/login')

@app.route('/settings')
def settings():

    if 'user' not in session:
        return redirect('/login')

    user = User.query.filter_by(
        email=session['user']
    ).first()

    return render_template(
        'dashboard/settings.html',
        user=user
    )

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)


