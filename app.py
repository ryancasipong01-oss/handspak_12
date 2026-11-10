from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash
)

import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = "handspeak-secret-key-change-this"


# =========================================================
# DATABASE
# =========================================================

DATABASE = "database.db"


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():

    db = get_db()

    # USERS
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # GESTURES
    db.execute("""
        CREATE TABLE IF NOT EXISTS gestures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            image TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # SEARCH HISTORY
    db.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            search_text TEXT NOT NULL,
            gesture_id INTEGER,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
            REFERENCES users(id),

            FOREIGN KEY(gesture_id)
            REFERENCES gestures(id)
        )
    """)

    # CREATE DEFAULT ADMIN
    admin = db.execute(
        "SELECT id FROM users WHERE username = ?",
        ("admin",)
    ).fetchone()

    if admin is None:

        db.execute("""
            INSERT INTO users
            (username, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (
            "admin",
            "admin@handspeak.com",
            generate_password_hash("admin123"),
            "admin"
        ))

    # DEFAULT GESTURES
    gesture_count = db.execute(
        "SELECT COUNT(*) AS count FROM gestures"
    ).fetchone()["count"]

    if gesture_count == 0:

        gestures = [

            # LETTERS
            ("A", "letter", "a.jpg", "American Sign Language letter A"),
            ("B", "letter", "b.jpg", "American Sign Language letter B"),
            ("C", "letter", "c.jpg", "American Sign Language letter C"),
            ("D", "letter", "d.jpg", "American Sign Language letter D"),
            ("E", "letter", "e.jpg", "American Sign Language letter E"),
            ("F", "letter", "f.jpg", "American Sign Language letter F"),
            ("G", "letter", "g.jpg", "American Sign Language letter G"),
            ("H", "letter", "h.jpg", "American Sign Language letter H"),
            ("I", "letter", "i.jpg", "American Sign Language letter I"),
            ("J", "letter", "j.jpg", "American Sign Language letter J"),
            ("K", "letter", "k.jpg", "American Sign Language letter K"),
            ("L", "letter", "l.jpg", "American Sign Language letter L"),
            ("M", "letter", "m.jpg", "American Sign Language letter M"),
            ("N", "letter", "n.jpg", "American Sign Language letter N"),
            ("O", "letter", "o.jpg", "American Sign Language letter O"),
            ("P", "letter", "p.jpg", "American Sign Language letter P"),
            ("Q", "letter", "q.jpg", "American Sign Language letter Q"),
            ("R", "letter", "r.jpg", "American Sign Language letter R"),
            ("S", "letter", "s.jpg", "American Sign Language letter S"),
            ("T", "letter", "t.jpg", "American Sign Language letter T"),
            ("U", "letter", "u.jpg", "American Sign Language letter U"),
            ("V", "letter", "v.jpg", "American Sign Language letter V"),
            ("W", "letter", "w.jpg", "American Sign Language letter W"),
            ("X", "letter", "x.jpg", "American Sign Language letter X"),
            ("Y", "letter", "y.jpg", "American Sign Language letter Y"),
            ("Z", "letter", "z.jpg", "American Sign Language letter Z"),

            # NUMBERS
            ("0", "number", "0.jpg", "Sign language number 0"),
            ("1", "number", "1.jpg", "Sign language number 1"),
            ("2", "number", "2.jpg", "Sign language number 2"),
            ("3", "number", "3.jpg", "Sign language number 3"),
            ("4", "number", "4.jpg", "Sign language number 4"),
            ("5", "number", "5.jpg", "Sign language number 5"),
            ("6", "number", "6.jpg", "Sign language number 6"),
            ("7", "number", "7.jpg", "Sign language number 7"),
            ("8", "number", "8.jpg", "Sign language number 8"),
            ("9", "number", "9.jpg", "Sign language number 9"),

            # WORDS
            ("HI", "word", "hi.jpg", "Sign language for HI"),
            ("HELLO", "word", "hello.jpg", "Sign language for HELLO"),
            ("THANK YOU", "word", "thank-you.jpg", "Sign language for THANK YOU")
        ]

        db.executemany("""
            INSERT INTO gestures
            (name, category, image, description)
            VALUES (?, ?, ?, ?)
        """, gestures)

    db.commit()
    db.close()


# =========================================================
# AUTHENTICATION HELPERS
# =========================================================

def login_required():

    return "user_id" in session


def admin_required():

    return (
        "user_id" in session
        and session.get("role") == "admin"
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if not username or not email or not password:

            flash("Please complete all fields.")
            return redirect(url_for("register"))

        db = get_db()

        existing = db.execute("""
            SELECT id
            FROM users
            WHERE username = ?
               OR email = ?
        """, (username, email)).fetchone()

        if existing:

            db.close()

            flash("Username or email already exists.")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        db.execute("""
            INSERT INTO users
            (username, email, password, role)
            VALUES (?, ?, ?, 'user')
        """, (
            username,
            email,
            hashed_password
        ))

        db.commit()
        db.close()

        flash("Registration successful. Please login.")

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        user = db.execute("""
            SELECT *
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

        db.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            if user["role"] == "admin":

                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("dashboard"))

        flash("Invalid username or password.")

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))


# =========================================================
# USER DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if not login_required():

        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        username=session["username"]
    )


# =========================================================
# TRANSLATOR
# =========================================================

@app.route("/translator")
def translator():

    if not login_required():

        return redirect(url_for("login"))

    return render_template("translator.html")


# =========================================================
# API - SEARCH GESTURE
# =========================================================

@app.route("/api/gesture/<text>")
def api_gesture(text):

    text = text.strip()

    db = get_db()

    gesture = db.execute("""
        SELECT *
        FROM gestures
        WHERE LOWER(name) = LOWER(?)
        LIMIT 1
    """, (text,)).fetchone()

    db.close()

    if gesture:

        # SAVE SEARCH HISTORY
        if "user_id" in session:

            db = get_db()

            db.execute("""
                INSERT INTO search_history
                (user_id, search_text, gesture_id)
                VALUES (?, ?, ?)
            """, (
                session["user_id"],
                text,
                gesture["id"]
            ))

            db.commit()
            db.close()

        return jsonify({
            "success": True,
            "id": gesture["id"],
            "text": gesture["name"],
            "category": gesture["category"],
            "image": url_for(
                "static",
                filename="images/" + gesture["image"]
            ),
            "description": gesture["description"]
        })

    return jsonify({
        "success": False,
        "message": "Gesture not found."
    })


# =========================================================
# API - SUGGESTIONS
# =========================================================

@app.route("/api/suggestions")
def suggestions():

    query = request.args.get("q", "").strip()

    if not query:

        return jsonify([])

    db = get_db()

    results = db.execute("""
        SELECT id, name, category
        FROM gestures
        WHERE name LIKE ?
        ORDER BY name
        LIMIT 10
    """, (query + "%",)).fetchall()

    db.close()

    return jsonify([
        {
            "id": row["id"],
            "name": row["name"],
            "category": row["category"]
        }
        for row in results
    ])


# =========================================================
# SEARCH HISTORY
# =========================================================

@app.route("/history")
def history():

    if not login_required():

        return redirect(url_for("login"))

    db = get_db()

    histories = db.execute("""
        SELECT
            search_history.id,
            search_history.search_text,
            search_history.searched_at,
            gestures.name AS gesture_name
        FROM search_history
        LEFT JOIN gestures
        ON search_history.gesture_id = gestures.id
        WHERE search_history.user_id = ?
        ORDER BY search_history.id DESC
    """, (session["user_id"],)).fetchall()

    db.close()

    return render_template(
        "history.html",
        histories=histories
    )


@app.route("/history/delete/<int:history_id>", methods=["POST"])
def delete_history(history_id):

    if not login_required():

        return redirect(url_for("login"))

    db = get_db()

    db.execute("""
        DELETE FROM search_history
        WHERE id = ?
        AND user_id = ?
    """, (
        history_id,
        session["user_id"]
    ))

    db.commit()
    db.close()

    return redirect(url_for("history"))

@app.route("/admin/history/delete-all", methods=["POST"])
def delete_all_history():

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM search_history"
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for("search_history")
    )
    
# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        user = db.execute("""
            SELECT *
            FROM users
            WHERE username = ?
            AND role = 'admin'
        """, (username,)).fetchone()

        db.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = "admin"

            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin account.")

    return render_template("admin/login.html")


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin_dashboard():

    if not admin_required():

        return redirect(url_for("admin_login"))

    db = get_db()

    users = db.execute(
        "SELECT COUNT(*) AS total FROM users"
    ).fetchone()["total"]

    gestures = db.execute(
        "SELECT COUNT(*) AS total FROM gestures"
    ).fetchone()["total"]

    searches = db.execute(
        "SELECT COUNT(*) AS total FROM search_history"
    ).fetchone()["total"]

    db.close()

    return render_template(
        "admin/dashboard.html",
        users=users,
        gestures=gestures,
        searches=searches
    )


# =========================================================
# ADMIN - MANAGE USERS
# =========================================================

@app.route("/admin/users")
def admin_users():

    if not admin_required():

        return redirect(url_for("admin_login"))

    db = get_db()

    users = db.execute("""
        SELECT *
        FROM users
        ORDER BY id DESC
    """).fetchall()

    db.close()

    return render_template(
        "admin/users.html",
        users=users
    )


@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):

    if not admin_required():

        return redirect(url_for("admin_login"))

    if user_id == session["user_id"]:

        flash("You cannot delete your own admin account.")

        return redirect(url_for("admin_users"))

    db = get_db()

    db.execute(
        "DELETE FROM users WHERE id = ?",
        (user_id,)
    )

    db.commit()
    db.close()

    return redirect(url_for("admin_users"))


# =========================================================
# ADMIN - MANAGE GESTURES
# =========================================================

@app.route("/admin/gestures")
def admin_gestures():

    if not admin_required():

        return redirect(url_for("admin_login"))

    db = get_db()

    gestures = db.execute("""
        SELECT *
        FROM gestures
        ORDER BY category, name
    """).fetchall()

    db.close()

    return render_template(
        "admin/gestures.html",
        gestures=gestures
    )


# =========================================================
# ADMIN - ADD GESTURE
# =========================================================

@app.route("/admin/gestures/add", methods=["POST"])
def add_gesture():

    if not admin_required():

        return redirect(url_for("admin_login"))

    name = request.form["name"].strip().upper()
    category = request.form["category"]
    image = request.form["image"].strip()
    description = request.form["description"].strip()

    db = get_db()

    db.execute("""
        INSERT INTO gestures
        (name, category, image, description)
        VALUES (?, ?, ?, ?)
    """, (
        name,
        category,
        image,
        description
    ))

    db.commit()
    db.close()

    return redirect(url_for("admin_gestures"))


@app.route("/admin/gestures/edit/<int:gesture_id>", methods=["GET", "POST"])
def edit_gesture(gesture_id):

    conn = get_db()

    # GET - display existing gesture
    if request.method == "GET":

        gesture = conn.execute(
            "SELECT * FROM gestures WHERE id = ?",
            (gesture_id,)
        ).fetchone()

        conn.close()

        if gesture is None:
            return "Gesture not found", 404

        return render_template(
            "edit_gesture.html",
            gesture=gesture
        )

    # POST - update gesture
    name = request.form["name"].strip().upper()
    category = request.form["category"]
    image = request.form["image"].strip()
    description = request.form["description"].strip()

    conn.execute(
        """
        UPDATE gestures
        SET name = ?,
            category = ?,
            image = ?,
            description = ?
        WHERE id = ?
        """,
        (
            name,
            category,
            image,
            description,
            gesture_id
        )
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_gestures"))


# =========================================================
# ADMIN - DELETE GESTURE
# =========================================================

@app.route("/admin/gestures/delete/<int:gesture_id>", methods=["POST"])
def delete_gesture(gesture_id):

    if not admin_required():

        return redirect(url_for("admin_login"))

    db = get_db()

    db.execute("""
        DELETE FROM gestures
        WHERE id = ?
    """, (gesture_id,))

    db.commit()
    db.close()

    return redirect(url_for("admin_gestures"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)