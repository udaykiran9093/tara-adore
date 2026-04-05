from flask import Blueprint, render_template, redirect, url_for, session

forecast_bp = Blueprint('forecast', __name__)

@forecast_bp.route('/forecast')
def forecast():
    if 'admin' not in session:
        return redirect(url_for('admin.login'))
    return render_template('forecast.html')