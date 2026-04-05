from flask import Blueprint, render_template, request, redirect, session, url_for
from models.db import get_db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
def home():
    return redirect(url_for('admin.login'))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM admin WHERE username=%s AND password=%s",
                    (username, password))
        admin = cur.fetchone()
        db.close()

        if admin:
            session['admin'] = username
            return redirect(url_for('admin.dashboard'))
        else:
            error = 'Invalid username or password!'

    return render_template('login.html', error=error)

@admin_bp.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin.login'))

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT SUM(total_amount) as total FROM sales WHERE payment_status='Paid'")
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

@admin_bp.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin.login'))