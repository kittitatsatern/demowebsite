from flask import Flask, render_template, request, redirect, g
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "cakeshop.db"

# -------------------------------
# Database Utilities
# -------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database with tables and default categories"""
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Create tables
        cursor.execute("""
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """)
        cursor.execute("""
        CREATE TABLE cakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            image TEXT,
            stock INTEGER DEFAULT 0,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
        """)

        # Insert default categories
        default_categories = ["Chocolate", "Fruit", "Birthday", "Wedding", "Custom"]
        cursor.executemany("INSERT INTO categories (name) VALUES (?)",
                           [(cat,) for cat in default_categories])

        conn.commit()
        conn.close()

# Initialize DB once at startup
init_db()

# -------------------------------
# Routes
# -------------------------------
@app.route("/")
def cakemenu():
    db = get_db()
    cakes = db.execute("""
        SELECT cakes.*, categories.name as category_name
        FROM cakes
        LEFT JOIN categories ON cakes.category_id = categories.id
    """).fetchall()
    return render_template("cakemenu.html", cakes=cakes)

@app.route("/append", methods=["GET", "POST"])
def append():
    db = get_db()
    categories = db.execute("SELECT * FROM categories").fetchall()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = float(request.form.get("price", 0))
        image = request.form.get("image", "").strip()
        stock = int(request.form.get("stock") or 0)
        category_id = request.form.get("category_id")
        category_id = int(category_id) if category_id else None

        db.execute(
            "INSERT INTO cakes (name, price, image, stock, category_id) VALUES (?, ?, ?, ?, ?)",
            (name, price, image, stock, category_id)
        )
        db.commit()
        return redirect("/")

    return render_template("append.html", categories=categories)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    db = get_db()
    categories = db.execute("SELECT * FROM categories").fetchall()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = float(request.form.get("price", 0))
        image = request.form.get("image", "").strip()
        stock = int(request.form.get("stock") or 0)
        category_id = request.form.get("category_id")
        category_id = int(category_id) if category_id else None

        db.execute(
            "UPDATE cakes SET name=?, price=?, image=?, stock=?, category_id=? WHERE id=?",
            (name, price, image, stock, category_id, id)
        )
        db.commit()
        return redirect("/")

    cake = db.execute("""
        SELECT cakes.*, categories.name as category_name
        FROM cakes
        LEFT JOIN categories ON cakes.category_id = categories.id
        WHERE cakes.id=?
    """, (id,)).fetchone()

    return render_template("edit.html", cake=cake, categories=categories)

@app.route("/delete/<int:id>")
def delete(id):
    db = get_db()
    db.execute("DELETE FROM cakes WHERE id=?", (id,))
    db.commit()
    return redirect("/")

# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)