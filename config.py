import os

class Config:
    # Flask
    SECRET_KEY = 'tara_adore_secret_key_2025'

    # MySQL Database
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'your_mysql_password'   # ← Change this
    MYSQL_DB = 'tara_adore_db'

    # Razorpay
    RAZORPAY_KEY_ID = 'your_razorpay_key_id'         # ← Add later
    RAZORPAY_KEY_SECRET = 'your_razorpay_key_secret'  # ← Add later

    # DTDC
    DTDC_API_KEY = 'your_dtdc_api_key'   # ← Add later