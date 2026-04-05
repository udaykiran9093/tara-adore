from flask import Blueprint, render_template, redirect, url_for, session
from models.db import get_db

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/customers')
def customers():
    if 'admin' not in session:
        return redirect(url_for('admin.login'))

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT c.id, c.name, c.email, c.phone, c.city,
               COUNT(s.id) as total_orders,
               SUM(s.total_amount) as total_spent
        FROM customers c
        LEFT JOIN sales s ON c.id = s.customer_id
        GROUP BY c.id
        ORDER BY total_spent DESC
    """)
    all_customers = cur.fetchall()
    db.close()

    return render_template('customers.html', customers=all_customers)