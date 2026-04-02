
from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "portfolio_secret"

# ---------- DB ----------
def db():
    return sqlite3.connect("db.sqlite3")

def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS food(id INTEGER PRIMARY KEY, name TEXT, price INT, category TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS cart(id INTEGER PRIMARY KEY, username TEXT, item TEXT, price INT)")
    c.execute("CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, username TEXT, total INT, status TEXT)")

    # Default items
    c.execute("INSERT OR IGNORE INTO food VALUES (1,'Burger',50,'Fast Food')")
    c.execute("INSERT OR IGNORE INTO food VALUES (2,'Pizza',120,'Fast Food')")
    c.execute("INSERT OR IGNORE INTO food VALUES (3,'Thali',150,'Meal')")

    conn.commit()
    conn.close()

init_db()

# ---------- Routes ----------
@app.route("/")
def home():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM food")
    foods = c.fetchall()
    conn.close()
    return render_template("home.html", foods=foods)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        conn = db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?",
                  (request.form["username"], request.form["password"]))
        user = c.fetchone()
        conn.close()
        if user:
            session["user"] = user[1]
            return redirect("/")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        conn = db()
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES(NULL,?,?)",
                  (request.form["username"], request.form["password"]))
        conn.commit()
        conn.close()
        return redirect("/login")
    return render_template("register.html")

@app.route("/add/<int:id>")
def add(id):
    if "user" not in session:
        return redirect("/login")

    conn = db()
    c = conn.cursor()
    c.execute("SELECT name, price FROM food WHERE id=?", (id,))
    item = c.fetchone()

    c.execute("INSERT INTO cart VALUES(NULL,?,?,?)",
              (session["user"], item[0], item[1]))

    conn.commit()
    conn.close()
    return redirect("/cart")

@app.route("/cart")
def cart():
    if "user" not in session:
        return redirect("/login")

    conn = db()
    c = conn.cursor()
    c.execute("SELECT item, price FROM cart WHERE username=?", (session["user"],))
    items = c.fetchall()
    total = sum([i[1] for i in items]) if items else 0
    conn.close()

    return render_template("cart.html", items=items, total=total)

@app.route("/place_order")
def place_order():
    conn = db()
    c = conn.cursor()

    c.execute("SELECT SUM(price) FROM cart WHERE username=?", (session["user"],))
    total = c.fetchone()[0]

    c.execute("INSERT INTO orders VALUES(NULL, ?, ?, 'Preparing')",
              (session["user"], total))

    c.execute("DELETE FROM cart WHERE username=?", (session["user"],))
    conn.commit()
    conn.close()

    return render_template("success.html")

@app.route("/orders")
def orders():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE username=?", (session.get("user"),))
    data = c.fetchall()
    conn.close()
    return render_template("orders.html", orders=data)

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        conn = db()
        c = conn.cursor()
        c.execute("INSERT INTO food VALUES(NULL,?,?,?)",
                  (request.form["name"], request.form["price"], request.form["category"]))
        conn.commit()
        conn.close()
        return redirect("/")
    return render_template("admin.html")

@app.route("/api/foods")
def api_foods():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM food")
    return jsonify(c.fetchall())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
