import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# ── Load Data ──────────────────────────────
df = pd.read_csv('data/sample_sales.csv')
df['date'] = pd.to_datetime(df['date'])

# ── Feature Engineering ────────────────────
df['day']       = df['date'].dt.day
df['month']     = df['date'].dt.month
df['year']      = df['date'].dt.year
df['dayofweek'] = df['date'].dt.dayofweek
df['quarter']   = df['date'].dt.quarter
df['day_index'] = (df['date'] - df['date'].min()).dt.days

# Encode category
le = LabelEncoder()
df['category_enc'] = le.fit_transform(df['category'])

# ── Features & Target ──────────────────────
features = ['day_index','month','quarter','dayofweek','category_enc','quantity']
X = df[features]
y = df['total_amount']

# ── Split ──────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ── Train Linear Regression ────────────────
lr = LinearRegression()
lr.fit(X_train, y_train)
lr_pred = lr.predict(X_test)
print(f"Linear Regression  → MAE: ₹{mean_absolute_error(y_test,lr_pred):,.0f} | R²: {r2_score(y_test,lr_pred):.3f}")

# ── Train Random Forest ────────────────────
rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
rf_pred = rf.predict(X_test)
print(f"Random Forest      → MAE: ₹{mean_absolute_error(y_test,rf_pred):,.0f} | R²: {r2_score(y_test,rf_pred):.3f}")

# ── Save Best Model ────────────────────────
os.makedirs('ml/saved_model', exist_ok=True)
joblib.dump(rf, 'ml/saved_model/sales_model.pkl')
joblib.dump(le, 'ml/saved_model/label_encoder.pkl')

print("\n✅ Model trained and saved to ml/saved_model/")
print(f"   Training samples : {len(X_train)}")
print(f"   Testing  samples : {len(X_test)}")