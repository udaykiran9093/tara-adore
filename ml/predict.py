import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta

def generate_forecast(days=90):
    """Generate sales forecast for next N days"""
    
    model = joblib.load('ml/saved_model/sales_model.pkl')
    le    = joblib.load('ml/saved_model/label_encoder.pkl')

    base_date  = datetime(2024, 1, 5)
    start_date = datetime.today()
    categories = ['Ring', 'Necklace', 'Earring', 'Bangle', 'Bracelet']
    forecasts  = []

    for i in range(days):
        date = start_date + timedelta(days=i)
        cat  = categories[i % len(categories)]

        try:
            cat_enc = le.transform([cat])[0]
        except:
            cat_enc = 0

        day_index = (date - base_date).days
        features  = [[
            day_index,
            date.month,
            (date.month - 1) // 3 + 1,
            date.weekday(),
            cat_enc,
            1
        ]]

        predicted = model.predict(features)[0]
        predicted = max(5000, predicted)

        forecasts.append({
            'date':             date.strftime('%Y-%m-%d'),
            'predicted_amount': round(predicted, 2),
            'category':         cat,
            'month':            date.strftime('%b %Y')
        })

    return forecasts

def get_monthly_forecast():
    """Aggregate daily forecasts into monthly totals"""
    forecasts = generate_forecast(90)
    df = pd.DataFrame(forecasts)
    monthly = df.groupby('month')['predicted_amount'].sum().reset_index()
    monthly.columns = ['month', 'predicted_total']
    return monthly.to_dict('records')

def get_category_forecast():
    """Aggregate forecasts by category"""
    forecasts = generate_forecast(90)
    df = pd.DataFrame(forecasts)
    cat = df.groupby('category')['predicted_amount'].sum().reset_index()
    cat.columns = ['category', 'predicted_total']
    return cat.to_dict('records')