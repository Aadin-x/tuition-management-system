import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash
from database import get_connection, create_table

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-key-change-me")
create_table()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        conn = get_connection()
        admin = conn.execute(
            "SELECT * FROM admins WHERE username=?", (username,)
        ).fetchone()
        conn.close()
        if admin and check_password_hash(admin["password_hash"], password):
            session["admin"] = admin["username"]
            return redirect(url_for("dashboard"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    paid = conn.execute("SELECT COUNT(*) FROM students WHERE fee_paid=1").fetchone()[0]
    unpaid = total - paid
    unpaid_students = conn.execute(
        "SELECT * FROM students WHERE fee_paid=0 ORDER BY name"
    ).fetchall()
    conn.close()
    return render_template(
        "dashboard.html",
        total=total,
        paid=paid,
        unpaid=unpaid,
        unpaid_students=unpaid_students,
    )

@app.route("/students")
@login_required
def students():
    q = request.args.get("q", "").strip()
    conn = get_connection()
    if q:
        rows = conn.execute(
            "SELECT * FROM students WHERE name LIKE ? OR roll_no LIKE ? ORDER BY id DESC",
            (f"%{q}%", f"%{q}%"),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("students.html", students=rows, q=q)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        name = request.form["name"]
        roll_no = request.form["roll_no"]
        course = request.form["course"]
        phone = request.form["phone"]
        email = request.form["email"]
        fee_paid = 1 if request.form.get("fee_paid") else 0

        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO students (name, roll_no, course, phone, email, fee_paid) VALUES (?, ?, ?, ?, ?, ?)",
                (name, roll_no, course, phone, email, fee_paid),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("add_student.html", error="This roll number already exists.")
        conn.close()
        return redirect(url_for("students"))

    return render_template("add_student.html")


@app.route("/edit/<int:student_id>", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    conn = get_connection()
    if request.method == "POST":
        name = request.form["name"]
        roll_no = request.form["roll_no"]
        course = request.form["course"]
        phone = request.form["phone"]
        email = request.form["email"]
        fee_paid = 1 if request.form.get("fee_paid") else 0
        try:
            conn.execute(
                "UPDATE students SET name=?, roll_no=?, course=?, phone=?, email=?, fee_paid=? WHERE id=?",
                (name, roll_no, course, phone, email, fee_paid, student_id),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            student = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
            conn.close()
            return render_template("edit_student.html", student=student, error="This roll number already exists.")
        conn.close()
        return redirect(url_for("students"))

    student = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    conn.close()
    if student is None:
        return redirect(url_for("students"))
    return render_template("edit_student.html", student=student)


@app.route("/delete/<int:student_id>", methods=["POST"])
@login_required
def delete_student(student_id):
    conn = get_connection()
    conn.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("students"))


if __name__ == "__main__":
    app.run(debug=True)