from flask import Blueprint, render_template, request, redirect, url_for, session
from models.db import get_db

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/sales')
def sales():
    if 'admin' not in session:
        return redirect(url_for('admin.login'))

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