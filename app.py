from flask import Flask, render_template, request, redirect, session, make_response, jsonify
import pymysql
import pymysql.cursors
import sys
import os
import csv
import io
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'tara_adore_secret_key_2025'

DB_CONFIG = {
    'host':     os.environ.get('MYSQLHOST', 'localhost'),
    'user':     os.environ.get('MYSQLUSER', 'root'),
    'password': os.environ.get('MYSQLPASSWORD', 'Uday'),
    'database': os.environ.get('MYSQLDATABASE', 'tara_adore_db'),
    'port':     int(os.environ.get('MYSQLPORT', 3306)),
    'cursorclass': pymysql.cursors.DictCursor
}

MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'udaykirandokku007@gmail.com')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'vzabovucblmvliji')

def get_db():
    return pymysql.connect(**DB_CONFIG)

def send_reset_email(to_email, reset_link):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Tara Adore — Password Reset Request'
        msg['From']    = f'Tara Adore <{MAIL_USERNAME}>'
        msg['To']      = to_email
        html_body = f"""
        <!DOCTYPE html><html>
        <body style="margin:0;padding:0;background:#050505;font-family:sans-serif">
        <div style="max-width:480px;margin:40px auto;background:#111;border:1px solid rgba(201,168,76,0.15);border-radius:20px;overflow:hidden">
            <div style="padding:28px;text-align:center;border-bottom:1px solid rgba(201,168,76,0.1)">
                <div style="font-size:1.6rem;font-weight:700;color:#E8C97A">Tara Adore</div>
                <div style="font-size:.6rem;letter-spacing:.25em;color:#6e6a63;margin-top:4px;text-transform:uppercase">Jewellery Analytics Platform</div>
            </div>
            <div style="padding:36px">
                <p style="color:#f0ece4;font-size:1rem;font-weight:500;margin:0 0 12px">Password Reset Request</p>
                <p style="color:#9e9a93;font-size:.85rem;line-height:1.7;margin:0 0 28px">
                    We received a request to reset your admin password. This link expires in <strong style="color:#C9A84C">30 minutes</strong>.
                </p>
                <div style="text-align:center;margin-bottom:28px">
                    <a href="{reset_link}" style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#E8C97A,#C9A84C);color:#000;font-weight:600;border-radius:10px;text-decoration:none;font-size:.85rem">
                        Reset My Password →
                    </a>
                </div>
                <p style="color:#6e6a63;font-size:.72rem;line-height:1.6;margin:0">
                    If you didn't request this, ignore this email.
                </p>
            </div>
            <div style="padding:16px;border-top:1px solid rgba(255,255,255,0.04);text-align:center">
                <div style="font-size:.6rem;color:#4e4a43;text-transform:uppercase">Tara Adore © 2025 · taraadore.in</div>
            </div>
        </div>
        </body></html>
        """
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_USERNAME, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ── LOGIN / LOGOUT ───────────────────────────────────────────────────────────
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM admin WHERE LOWER(username)=LOWER(%s) AND password=%s", (username, password))
        admin = cur.fetchone()
        db.close()
        if admin:
            session['admin'] = admin['username']
            return redirect('/dashboard')
        else:
            error = 'Invalid username or password!'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/login')

# ── REGISTER ─────────────────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm  = request.form['confirm_password']
        email    = request.form['email'].strip()
        if password != confirm:
            error = 'Passwords do not match!'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT id FROM admin WHERE LOWER(username)=LOWER(%s)", (username,))
            if cur.fetchone():
                error = 'Username already exists!'
            else:
                cur.execute(
                    "INSERT INTO admin (username, password, email) VALUES (%s, %s, %s)",
                    (username, password, email)
                )
                db.commit()
                success = 'Account created successfully! You can now log in.'
            db.close()
    return render_template('register.html', error=error, success=success)

# ── FORGOT PASSWORD ──────────────────────────────────────────────────────────
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    error = None
    success = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        email    = request.form['email'].strip()
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM admin WHERE LOWER(username)=LOWER(%s) AND LOWER(email)=LOWER(%s)", (username, email))
        admin = cur.fetchone()
        if admin:
            token  = secrets.token_urlsafe(32)
            expiry = datetime.now() + timedelta(minutes=30)
            cur.execute(
                "UPDATE admin SET reset_token=%s, reset_expiry=%s WHERE id=%s",
                (token, expiry, admin['id'])
            )
            db.commit()
            reset_link = f"http://127.0.0.1:5000/reset-password/{token}"
            sent = send_reset_email(email, reset_link)
            if sent:
                success = f'Reset link sent to <strong>{email}</strong>. Check your inbox!'
            else:
                success = f'Dev mode — <a href="{reset_link}" style="color:#C9A84C">click here to reset your password</a>'
        else:
            error = 'No account found with that username and email combination.'
        db.close()
    return render_template('forgot_password.html', error=error, success=success)

# ── RESET PASSWORD ───────────────────────────────────────────────────────────
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    error = None
    success = None
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM admin WHERE reset_token=%s", (token,))
    admin = cur.fetchone()
    if not admin:
        db.close()
        return render_template('reset_password.html', error='Invalid or expired reset link.', token=None)
    if admin['reset_expiry'] and datetime.now() > admin['reset_expiry']:
        db.close()
        return render_template('reset_password.html', error='Reset link expired. Please request a new one.', token=None)
    if request.method == 'POST':
        new_pass = request.form['new_password']
        confirm  = request.form['confirm_password']
        if new_pass != confirm:
            error = 'Passwords do not match!'
        elif len(new_pass) < 6:
            error = 'Password must be at least 6 characters.'
        else:
            cur.execute(
                "UPDATE admin SET password=%s, reset_token=NULL, reset_expiry=NULL WHERE id=%s",
                (new_pass, admin['id'])
            )
            db.commit()
            db.close()
            return render_template('reset_password.html', success='Password reset successfully! You can now log in.', token=None)
    db.close()
    return render_template('reset_password.html', error=error, success=success, token=token)

# ── DASHBOARD ────────────────────────────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/login')
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COALESCE(SUM(total_amount),0) as total FROM sales WHERE payment_status='Paid'")
    total_revenue = cur.fetchone()['total'] or 0
    cur.execute("SELECT COUNT(*) as cnt FROM sales")
    total_orders = cur.fetchone()['cnt'] or 0
    cur.execute("SELECT COUNT(*) as cnt FROM customers")
    total_customers = cur.fetchone()['cnt'] or 0
    cur.execute("SELECT COUNT(*) as cnt FROM products")
    total_products = cur.fetchone()['cnt'] or 0
    cur.execute("""
        SELECT s.id, c.name, p.name as product, s.total_amount,
               s.sale_date, s.payment_status
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        JOIN products p ON s.product_id = p.id
        ORDER BY s.sale_date DESC LIMIT 5
    """)
    recent_sales = cur.fetchall()
    db.close()
    return render_template('dashboard.html',
                           total_revenue=total_revenue,
                           total_orders=total_orders,
                           total_customers=total_customers,
                           total_products=total_products,
                           recent_sales=recent_sales)

# ── SALES ────────────────────────────────────────────────────────────────────
@app.route('/sales')
def sales():
    if 'admin' not in session:
        return redirect('/login')
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT s.id, c.name, p.name as product, s.quantity,
               s.total_amount, s.sale_date, s.payment_status, s.delivery_status
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        JOIN products p ON s.product_id = p.id
        ORDER BY s.sale_date DESC
    """)
    all_sales = cur.fetchall()
    db.close()
    return render_template('sales.html', sales=all_sales)

@app.route('/add_sale', methods=['POST'])
def add_sale():
    if 'admin' not in session:
        return redirect('/login')
    customer_id = request.form['customer_id']
    product_id  = request.form['product_id']
    quantity    = int(request.form['quantity'])
    sale_date   = request.form['sale_date']
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT price FROM products WHERE id=%s", (product_id,))
    price = cur.fetchone()['price']
    total = price * quantity
    cur.execute("""
        INSERT INTO sales (customer_id, product_id, quantity,
                           unit_price, total_amount, sale_date, payment_status, delivery_status)
        VALUES (%s, %s, %s, %s, %s, %s, 'Paid', 'Delivered')
    """, (customer_id, product_id, quantity, price, total, sale_date))
    db.commit()
    db.close()
    return redirect('/sales')

# ── CUSTOMERS ────────────────────────────────────────────────────────────────
@app.route('/customers')
def customers():
    if 'admin' not in session:
        return redirect('/login')
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT c.id, c.name, c.email, c.phone, c.city,
               COUNT(s.id) as total_orders,
               COALESCE(SUM(s.total_amount), 0) as total_spent
        FROM customers c
        LEFT JOIN sales s ON c.id = s.customer_id
        GROUP BY c.id, c.name, c.email, c.phone, c.city
        ORDER BY total_spent DESC
    """)
    all_customers = cur.fetchall()
    db.close()
    return render_template('customers.html', customers=all_customers)

@app.route('/add_customer', methods=['POST'])
def add_customer():
    if 'admin' not in session:
        return redirect('/login')
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO customers (name, email, phone, city, state, pincode)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (request.form['name'], request.form['email'], request.form['phone'],
          request.form['city'], request.form['state'], request.form['pincode']))
    db.commit()
    db.close()
    return redirect('/customers')

# ── PRODUCTS ─────────────────────────────────────────────────────────────────
@app.route('/products')
def products():
    if 'admin' not in session:
        return redirect('/login')
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT p.id, p.name, p.category, p.material,
               p.weight_grams, p.price, p.stock_quantity,
               COUNT(s.id) as total_sold,
               COALESCE(SUM(s.total_amount), 0) as total_revenue
        FROM products p
        LEFT JOIN sales s ON p.id = s.product_id
        GROUP BY p.id, p.name, p.category, p.material, p.weight_grams, p.price, p.stock_quantity
        ORDER BY total_revenue DESC
    """)
    all_products = cur.fetchall()
    cur.execute("""
        SELECT category, COUNT(*) as product_count,
               SUM(stock_quantity) as total_stock, AVG(price) as avg_price
        FROM products GROUP BY category
    """)
    categories = cur.fetchall()
    db.close()
    return render_template('products.html', products=all_products, categories=categories)

@app.route('/add_product', methods=['POST'])
def add_product():
    if 'admin' not in session:
        return redirect('/login')
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO products (name, category, material, weight_grams, price, stock_quantity, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (request.form['name'], request.form['category'], request.form['material'],
          request.form['weight_grams'], request.form['price'], request.form['stock_quantity'],
          request.form.get('description', '')))
    db.commit()
    db.close()
    return redirect('/products')

@app.route('/delete_product/<int:id>')
def delete_product(id):
    if 'admin' not in session:
        return redirect('/login')
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (id,))
    db.commit()
    db.close()
    return redirect('/products')

# ── REPORTS ──────────────────────────────────────────────────────────────────
@app.route('/reports')
def reports():
    if 'admin' not in session:
        return redirect('/login')
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT DATE_FORMAT(sale_date, '%b %Y') as month,
               DATE_FORMAT(sale_date, '%Y-%m') as month_sort,
               COUNT(*) as orders, SUM(total_amount) as revenue
        FROM sales WHERE payment_status='Paid'
        GROUP BY DATE_FORMAT(sale_date, '%Y-%m'), DATE_FORMAT(sale_date, '%b %Y')
        ORDER BY month_sort
    """)
    monthly = cur.fetchall()
    cur.execute("""
        SELECT p.id, p.name, p.category, COUNT(s.id) as sold,
               COALESCE(SUM(s.total_amount), 0) as revenue
        FROM products p LEFT JOIN sales s ON p.id = s.product_id
        GROUP BY p.id, p.name, p.category ORDER BY revenue DESC LIMIT 5
    """)
    top_products = cur.fetchall()
    cur.execute("""
        SELECT c.id, c.name, c.city, COUNT(s.id) as orders,
               COALESCE(SUM(s.total_amount), 0) as spent
        FROM customers c LEFT JOIN sales s ON c.id = s.customer_id
        GROUP BY c.id, c.name, c.city ORDER BY spent DESC LIMIT 5
    """)
    top_customers = cur.fetchall()
    db.close()
    return render_template('reports.html', monthly=monthly,
                           top_products=top_products, top_customers=top_customers)

@app.route('/export/sales')
def export_sales():
    if 'admin' not in session:
        return redirect('/login')
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT s.id, c.name, p.name as product, s.quantity,
               s.total_amount, s.sale_date, s.payment_status, s.delivery_status
        FROM sales s JOIN customers c ON s.customer_id = c.id
        JOIN products p ON s.product_id = p.id ORDER BY s.sale_date DESC
    """)
    rows = cur.fetchall()
    db.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID','Customer','Product','Qty','Amount','Date','Payment','Delivery'])
    for r in rows:
        writer.writerow([r['id'], r['name'], r['product'], r['quantity'],
                         r['total_amount'], r['sale_date'], r['payment_status'], r['delivery_status']])
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=tara_adore_sales.csv'
    response.headers['Content-type'] = 'text/csv'
    return response

# ── PROFILE ──────────────────────────────────────────────────────────────────
@app.route('/profile')
def profile():
    if 'admin' not in session:
        return redirect('/login')
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COALESCE(SUM(total_amount),0) as total FROM sales WHERE payment_status='Paid'")
    total_revenue = cur.fetchone()['total'] or 0
    cur.execute("SELECT COUNT(*) as cnt FROM sales")
    total_orders = cur.fetchone()['cnt'] or 0
    cur.execute("SELECT COUNT(*) as cnt FROM customers")
    total_customers = cur.fetchone()['cnt'] or 0
    cur.execute("SELECT * FROM admin WHERE username=%s", (session['admin'],))
    admin_data = cur.fetchone()
    db.close()
    return render_template('profile.html',
                           admin_data=admin_data,
                           total_revenue=total_revenue,
                           total_orders=total_orders,
                           total_customers=total_customers)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'admin' not in session:
        return redirect('/login')
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("ALTER TABLE admin ADD COLUMN phone VARCHAR(20) DEFAULT NULL")
        db.commit()
    except: pass
    cur.execute("UPDATE admin SET email=%s, phone=%s WHERE username=%s",
                (email, phone, session['admin']))
    db.commit()
    db.close()
    return redirect('/profile')

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'admin' not in session:
        return redirect('/login')
    current  = request.form['current_password']
    new_pass = request.form['new_password']
    confirm  = request.form['confirm_password']
    if new_pass != confirm or len(new_pass) < 6:
        return redirect('/profile')
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (session['admin'], current))
    if cur.fetchone():
        cur.execute("UPDATE admin SET password=%s WHERE username=%s", (new_pass, session['admin']))
        db.commit()
    db.close()
    return redirect('/profile')

# ── ANALYTICS ────────────────────────────────────────────────────────────────
@app.route('/analytics')
def analytics():
    if 'admin' not in session:
        return redirect('/login')
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT DAYNAME(sale_date) as day_name,
               DAYOFWEEK(sale_date) as day_num,
               COUNT(*) as orders,
               SUM(total_amount) as revenue
        FROM sales
        GROUP BY DAYNAME(sale_date), DAYOFWEEK(sale_date)
        ORDER BY DAYOFWEEK(sale_date)
    """)
    weekly_data = cur.fetchall()

    cur.execute("""
        SELECT p.id, p.name, p.category, p.stock_quantity, p.price,
               MAX(s.sale_date) as last_sold
        FROM products p
        LEFT JOIN sales s ON p.id = s.product_id
        GROUP BY p.id, p.name, p.category, p.stock_quantity, p.price
        HAVING last_sold IS NULL OR last_sold < DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        ORDER BY last_sold ASC
    """)
    dead_stock = cur.fetchall()

    cur.execute("""
        SELECT MONTH(sale_date) as month_num,
               MONTHNAME(sale_date) as month_name,
               p.category,
               SUM(s.total_amount) as revenue
        FROM sales s
        JOIN products p ON s.product_id = p.id
        GROUP BY MONTH(sale_date), MONTHNAME(sale_date), p.category
        ORDER BY month_num
    """)
    seasonal = cur.fetchall()

    cur.execute("""
        SELECT c.id, c.name, c.city,
               DATEDIFF(CURDATE(), MAX(s.sale_date)) as recency,
               COUNT(s.id) as frequency,
               COALESCE(SUM(s.total_amount), 0) as monetary
        FROM customers c
        LEFT JOIN sales s ON c.id = s.customer_id
        GROUP BY c.id, c.name, c.city
        ORDER BY monetary DESC
    """)
    rfm_data = cur.fetchall()

    cur.execute("SELECT name, stock_quantity, category FROM products WHERE stock_quantity <= 5 ORDER BY stock_quantity ASC")
    low_stock = cur.fetchall()

    cur.execute("SELECT COALESCE(SUM(total_amount),0) as total FROM sales WHERE payment_status='Paid'")
    total_rev = cur.fetchone()['total'] or 0

    db.close()

    rfm_scored = []
    for r in rfm_data:
        score = 0
        if r['recency'] is not None and r['recency'] <= 30: score += 3
        elif r['recency'] is not None and r['recency'] <= 90: score += 2
        else: score += 1
        if r['frequency'] >= 3: score += 3
        elif r['frequency'] >= 2: score += 2
        else: score += 1
        if r['monetary'] >= 80000: score += 3
        elif r['monetary'] >= 30000: score += 2
        else: score += 1
        if score >= 8: segment = 'Champion'
        elif score >= 6: segment = 'Loyal'
        elif score >= 4: segment = 'At Risk'
        else: segment = 'New'
        rfm_scored.append({**r, 'score': score, 'segment': segment})

    notifications = []
    for p in low_stock:
        notifications.append({
            'type': 'warning',
            'message': f"Low stock alert: {p['name']} — only {p['stock_quantity']} left!",
            'icon': 'fa-exclamation-triangle'
        })
    if float(total_rev) >= 200000:
        notifications.append({
            'type': 'success',
            'message': f"🏆 Revenue milestone reached! Total: ₹{total_rev:,.0f}",
            'icon': 'fa-trophy'
        })
    if not notifications:
        notifications.append({
            'type': 'success',
            'message': '✅ All systems normal. Stock levels are healthy!',
            'icon': 'fa-check-circle'
        })

    return render_template('analytics.html',
                           weekly_data=weekly_data,
                           dead_stock=dead_stock,
                           seasonal=seasonal,
                           rfm_scored=rfm_scored,
                           notifications=notifications,
                           total_rev=total_rev)

# ── AI ADVISOR ───────────────────────────────────────────────────────────────
@app.route('/ai_advisor', methods=['POST'])
def ai_advisor():
    if 'admin' not in session:
        return jsonify({'response': 'Unauthorized'}), 401
    try:
        data = request.get_json()
        if not data:
            return jsonify({'response': 'No data received'}), 400
        question = data.get('question', '').lower().strip()
        if not question:
            return jsonify({'response': 'Please ask a question!'})
    except Exception as e:
        return jsonify({'response': f'Request error: {str(e)}'}), 400

    try:
        db = get_db()
        cur = db.cursor()

        cur.execute("SELECT COALESCE(SUM(total_amount),0) as total FROM sales WHERE payment_status='Paid'")
        total_rev = float(cur.fetchone()['total'] or 0)

        cur.execute("""
            SELECT p.name, p.category, COUNT(s.id) as sold,
                   COALESCE(SUM(s.total_amount),0) as revenue
            FROM products p LEFT JOIN sales s ON p.id=s.product_id
            GROUP BY p.id, p.name, p.category ORDER BY revenue DESC LIMIT 1
        """)
        top_product = cur.fetchone()

        cur.execute("""
            SELECT p.name, p.category, COUNT(s.id) as sold
            FROM products p LEFT JOIN sales s ON p.id=s.product_id
            GROUP BY p.id, p.name, p.category ORDER BY sold ASC LIMIT 1
        """)
        low_product = cur.fetchone()

        cur.execute("""
            SELECT c.name, COALESCE(SUM(s.total_amount),0) as spent
            FROM customers c JOIN sales s ON c.id=s.customer_id
            GROUP BY c.id, c.name ORDER BY spent DESC LIMIT 1
        """)
        top_customer = cur.fetchone()

        cur.execute("SELECT COUNT(*) as cnt FROM customers")
        total_customers = cur.fetchone()['cnt'] or 0

        cur.execute("SELECT COUNT(*) as cnt FROM sales")
        total_orders = cur.fetchone()['cnt'] or 0

        cur.execute("SELECT name, stock_quantity FROM products WHERE stock_quantity <= 5")
        low_stock = cur.fetchall()

        cur.execute("""
            SELECT DATE_FORMAT(sale_date,'%b %Y') as month, SUM(total_amount) as rev
            FROM sales GROUP BY DATE_FORMAT(sale_date,'%Y-%m'), DATE_FORMAT(sale_date,'%b %Y')
            ORDER BY MIN(sale_date) DESC LIMIT 1
        """)
        latest_month = cur.fetchone()

        cur.execute("""
            SELECT p.category, COALESCE(SUM(s.total_amount),0) as revenue
            FROM sales s JOIN products p ON s.product_id=p.id
            GROUP BY p.category ORDER BY revenue DESC LIMIT 1
        """)
        top_category = cur.fetchone()

        cur.execute("SELECT COUNT(*) as cnt FROM products")
        total_products = cur.fetchone()['cnt'] or 0

        db.close()

    except Exception as e:
        return jsonify({'response': f'Database error: {str(e)}'}), 500

    response = ""

    if any(w in question for w in ['hello','hi','hey','namaste','good morning','good evening']):
        response = f"👋 Hello! I'm your AI Business Advisor for Tara Adore.\n\nYou have ₹{total_rev:,.0f} in total revenue, {total_customers} customers and {total_orders} orders. Ask me anything!"

    elif any(w in question for w in ['revenue','earning','money','total','income','how much']):
        response = f"💰 Total Revenue: ₹{total_rev:,.0f}\n📦 Total Orders: {total_orders}\n👥 Customers: {total_customers}"
        if latest_month:
            response += f"\n📅 Latest month ({latest_month['month']}): ₹{float(latest_month['rev']):,.0f}"
        if total_rev >= 200000:
            response += "\n\n🎉 Excellent! You've crossed the ₹2 lakh milestone!"
        else:
            response += f"\n\n🎯 ₹{200000 - total_rev:,.0f} more to reach the ₹2 lakh milestone!"

    elif any(w in question for w in ['best','top','popular','selling','highest','most']):
        if top_product:
            response = f"💎 Best Product: {top_product['name']} ({top_product['category']})\n💵 Revenue: ₹{float(top_product['revenue']):,.0f}\n📦 Units Sold: {top_product['sold']}"
        if top_category:
            response += f"\n\n🏆 Top Category: {top_category['category']} — ₹{float(top_category['revenue']):,.0f}"
        if top_customer:
            response += f"\n\n👑 Top Customer: {top_customer['name']} — ₹{float(top_customer['spent']):,.0f}"

    elif any(w in question for w in ['worst','slow','poor','least','bad']):
        if low_product:
            response = f"📉 Slowest Product: {low_product['name']} ({low_product['category']}) with only {low_product['sold'] or 0} units sold.\n\n💡 Try a discount or bundle deal to move this stock."

    elif any(w in question for w in ['stock','inventory','restock','supply','lock','available']):
        if low_stock:
            response = "⚠️ Low Stock Alert!\n"
            for p in low_stock:
                response += f"• {p['name']} — only {p['stock_quantity']} left\n"
            response += "\n🚨 Restock immediately to avoid lost sales!"
        else:
            response = "✅ All products have healthy stock levels. No restocking needed right now."

    elif any(w in question for w in ['customer','buyer','client','who','loyal']):
        response = f"👥 Total Customers: {total_customers}\n🛍️ Total Orders: {total_orders}"
        if top_customer:
            response += f"\n\n👑 Most Valuable Customer: {top_customer['name']}\n💰 Total Spent: ₹{float(top_customer['spent']):,.0f}\n\n💡 Consider a loyalty reward for them!"

    elif any(w in question for w in ['product','item','catalog','jewel','ring','necklace','earring','bangle','bracelet']):
        response = f"💍 Total Products in Catalog: {total_products}"
        if top_product:
            response += f"\n🏆 Best Seller: {top_product['name']} (₹{float(top_product['revenue']):,.0f})"
        if low_stock:
            response += f"\n⚠️ {len(low_stock)} product(s) need restocking"

    elif any(w in question for w in ['order','transaction','purchase','how many']):
        response = f"🛍️ Total Sales: {total_orders}\n💰 Total Revenue: ₹{total_rev:,.0f}"
        if latest_month:
            response += f"\n📅 Latest: {latest_month['month']} — ₹{float(latest_month['rev']):,.0f}"

    elif any(w in question for w in ['category','type','kind']):
        if top_category:
            response = f"💍 Top Category: {top_category['category']}\n💵 Revenue: ₹{float(top_category['revenue']):,.0f}\n\n💡 Focus marketing here for maximum ROI!"

    elif any(w in question for w in ['advice','suggest','recommend','should','improve','grow','help','tips']):
        tips = []
        if top_product:
            tips.append(f"📈 Stock more '{top_product['name']}' — it's your best seller")
        if low_stock:
            tips.append(f"⚠️ Restock {', '.join([p['name'] for p in low_stock[:2]])} immediately")
        if total_customers < 10:
            tips.append("👥 Focus on customer acquisition — run social media promotions")
        if top_category:
            tips.append(f"💎 Expand your {top_category['category']} collection")
        tips.append("🎯 Consider festive season discounts to boost sales")
        tips.append("📱 Ask loyal customers for reviews and referrals")
        response = "🤖 Top Business Tips for Tara Adore:\n\n" + "\n".join(tips)

    elif any(w in question for w in ['forecast','predict','future','next month']):
        response = "🔮 Check the AI Forecast page for ML-powered sales predictions based on your historical data!"

    elif any(w in question for w in ['profit','margin','cost']):
        response = f"💰 Recorded Revenue: ₹{total_rev:,.0f} from {total_orders} orders.\n\n💡 Add purchase cost data to products to track profit margins."

    else:
        response = "🤖 I can help with:\n• Revenue & earnings\n• Best/worst products\n• Stock alerts\n• Customer insights\n• Business advice\n• Category performance\n\nTry: 'What is my best selling product?' or 'Give me business advice!'"

    return jsonify({'response': response})

# ── FORECAST ─────────────────────────────────────────────────────────────────
@app.route('/forecast')
def forecast():
    if 'admin' not in session:
        return redirect('/login')
    monthly_forecast  = []
    category_forecast = []
    total_predicted   = 0
    model_trained     = False
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from ml.predict import get_monthly_forecast, get_category_forecast
        monthly_forecast  = get_monthly_forecast()
        category_forecast = get_category_forecast()
        total_predicted   = sum(m['predicted_total'] for m in monthly_forecast)
        model_trained     = True
    except Exception as e:
        print(f"Forecast error: {e}")
    return render_template('forecast.html',
                           monthly_forecast=monthly_forecast,
                           category_forecast=category_forecast,
                           total_predicted=total_predicted,
                           model_trained=model_trained)

# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)