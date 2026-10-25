import sqlite3
from werkzeug.security import generate_password_hash
from database import get_connection, create_table

create_table()

username = input("Choose admin username: ").strip()
password = input("Choose admin password: ")

conn = get_connection()
try:
    conn.execute(
        "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
        (username, generate_password_hash(password)),
    )
    conn.commit()
    print("Admin created! You can now log in.")
except sqlite3.IntegrityError:
    print("That username already exists.")
conn.close()