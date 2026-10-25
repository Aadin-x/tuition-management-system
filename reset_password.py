
from werkzeug.security import generate_password_hash
from database import get_connection

username = input("Admin username to reset: ").strip()
new_password = input("New password: ")

conn = get_connection()
admin = conn.execute("SELECT id FROM admins WHERE username=?", (username,)).fetchone()

if admin is None:
    print("No admin found with that username.")
else:
    conn.execute(
        "UPDATE admins SET password_hash=? WHERE username=?",
        (generate_password_hash(new_password), username),
    )
    conn.commit()
    print("Password updated! You can log in with the new password.")
conn.close()