import pymysql
import pymysql.cursors

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Uday',  # ← Change this
    'database': 'tara_adore_db',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db():
    return pymysql.connect(**DB_CONFIG)

def init_db(app):
    pass  # No setup needed for PyMySQL

mysql = None