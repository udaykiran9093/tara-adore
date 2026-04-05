import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='Uday',
    database='tara_adore_db',
    connect_timeout=10
)
cur = conn.cursor()

print("Connected!")

# Step 1: Get existing admin data
cur.execute("SELECT id, username, password FROM admin")
admins = cur.fetchall()
print(f"Found {len(admins)} admin(s): {admins}")

# Step 2: Drop old table
cur.execute("DROP TABLE IF EXISTS admin")
conn.commit()
print("Old table dropped.")

# Step 3: Create new table with all columns
cur.execute("""
    CREATE TABLE admin (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        email VARCHAR(255) DEFAULT NULL,
        reset_token VARCHAR(255) DEFAULT NULL,
        reset_expiry DATETIME DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()
print("New table created.")

# Step 4: Re-insert existing admins
for a in admins:
    cur.execute(
        "INSERT INTO admin (id, username, password) VALUES (%s, %s, %s)",
        (a[0], a[1], a[2])
    )
conn.commit()
print("Existing admins restored.")

# Step 5: Verify
cur.execute("DESCRIBE admin")
cols = cur.fetchall()
print("\nAdmin table columns:")
for c in cols:
    print(f"  {c[0]} — {c[1]}")

cur.execute("SELECT id, username, email FROM admin")
rows = cur.fetchall()
print("\nAdmin rows:")
for r in rows:
    print(f"  {r}")

conn.close()
print("\nDone! Now update your admin email in the database or via /register.")