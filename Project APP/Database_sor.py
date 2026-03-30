import sqlite3
from datetime import datetime
import hashlib
import os

DB_NAME = "savorly.db"

# ───────────────────────────────
# CONNECTION
# ───────────────────────────────
def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# ───────────────────────────────
# INITIALIZE DATABASE (MAIN)
# ───────────────────────────────
def init_database():
    conn = connect()
    cur = conn.cursor()

    # USERS (✅ FIXED schema)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT,
        salt TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # USER PROFILE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles(
        user_id INTEGER PRIMARY KEY,
        age INTEGER,
        gender TEXT,
        height REAL,
        weight REAL,
        bmi REAL,
        bmr REAL,
        tdee REAL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # FOOD TABLE (for analyzer)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS foods(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT,
        health_score REAL,
        carbs REAL,
        protein REAL,
        fat REAL,
        vitamins REAL,
        minerals REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # MEALS table (for meal planner)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        meal_type TEXT NOT NULL,
        food TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # FOOD HISTORY (simple log)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS food_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        food_text TEXT,
        portion TEXT,
        meal_type TEXT,
        time TEXT,
        bmi REAL,
        bmr REAL,
        tdee REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()

# ───────────────────────────────
# MIGRATIONS (SAFE UPDATE)
# ───────────────────────────────
def run_migrations():
    conn = connect()
    cur = conn.cursor()

    try:
        cur.execute("ALTER TABLE users ADD COLUMN salt TEXT;")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

# ───────────────────────────────
# PASSWORD HASHING
# ───────────────────────────────
def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)

    if isinstance(salt, str):
        salt = bytes.fromhex(salt)

    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt,
        100000
    )

    return hashed.hex(), salt.hex()

def verify_password(input_password, stored_hash, salt):
    hashed, _ = hash_password(input_password, salt)
    return hashed == stored_hash

# ───────────────────────────────
# AUTH SYSTEM
# ───────────────────────────────
def register_user(username, password):
    conn = connect()
    cur = conn.cursor()

    hashed, salt = hash_password(password)

    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
            (username, hashed, salt)
        )
        conn.commit()
        return True, "User registered successfully"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    finally:
        conn.close()

def login_user(username, password):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, username, password_hash, salt FROM users WHERE username=?",
        (username,)
    )

    user = cur.fetchone()
    conn.close()

    if not user:
        return False, "User NOT Found"

    user_id, uname, stored_hash, salt = user

    if verify_password(password, stored_hash, salt):
        return True, (user_id, uname)
    else:
        return False, "Invalid password"

# ───────────────────────────────
# USER PROFILE
# ───────────────────────────────
def save_user_profile(user_id, age, gender, height, weight, bmi, bmr, tdee):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM user_profiles WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()

    if exists:
        cursor.execute("""
            UPDATE user_profiles
            SET age = ?, gender = ?, height = ?, weight = ?, bmi = ?, bmr = ?, tdee = ?, updated_at=CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (age, gender, height, weight, bmi, bmr, tdee, user_id))
    else:
        cursor.execute("""
            INSERT INTO user_profiles (user_id, age, gender, height, weight, bmi, bmr, tdee)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, age, gender, height, weight, bmi, bmr, tdee))

    conn.commit()
    conn.close()

def get_user_profile(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT age, gender, height, weight, bmi, bmr, tdee
    FROM user_profiles
    WHERE user_id=?
    """, (user_id,))

    data = cur.fetchone()
    conn.close()
    return data

def get_user_by_id(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT u.id, u.username, p.bmi, p.tdee
        FROM users u
        LEFT JOIN user_profiles p ON u.id = p.user_id
        WHERE u.id=?
    """, (user_id,))

    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "username": row[1],
            "bmi": row[2],
            "tdee": row[3]
        }
    return None

def save_user_data(user_id, bmi, tdee):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO user_profiles (user_id, bmi, tdee)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            bmi=excluded.bmi,
            tdee=excluded.tdee,
            updated_at=CURRENT_TIMESTAMP
    """, (user_id, bmi, tdee))

    conn.commit()
    conn.close()

def user_has_health_data(user_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT bmi, tdee FROM user_profiles WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    if row and row[0] is not None and row[1] is not None:
        return True
    return False

# ───────────────────────────────
# FOOD HISTORY
# ───────────────────────────────
def save_food(food_text, portion, meal_type, time, bmi, bmr, tdee):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO food_history 
    (food_text, portion, meal_type, time, bmi, bmr, tdee)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (food_text, portion, meal_type, time, bmi, bmr, tdee))

    conn.commit()
    conn.close()

def get_food_history(limit=10):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT food_text, portion, meal_type, time, created_at
    FROM food_history
    ORDER BY created_at DESC
    LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows

def save_meal_data(user_id, date, meals_for_day):
    import sqlite3

    conn = sqlite3.connect("savorly.db")
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM meals
        WHERE user_id=? AND date=?
    """, (user_id, date))

    # insert new data
    for meal_type, foods in meals_for_day.items():
        for food in foods:
            cur.execute("""
                INSERT INTO meals (user_id, date, meal_type, food)
                VALUES (?, ?, ?, ?)
            """, (user_id, date, meal_type, food))

    conn.commit()
    conn.close()

def load_meal_data(user_id):
    conn = sqlite3.connect("savorly.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT date, meal_type, food
        FROM meals
        WHERE user_id=?
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    meal_data = {}

    for date, meal_type, food in rows:
        meal_data.setdefault(date, {})\
                 .setdefault(meal_type, [])\
                 .append(food)

    return meal_data

def load_meal_data(user_id):
    conn = sqlite3.connect("savorly.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT date, meal_type, food
        FROM meals
        WHERE user_id=? 
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    meal_data = {}

    for date, meal_type, food in rows:
        meal_data.setdefault(date, {})\
                 .setdefault(meal_type, [])\
                 .append(food)

    return meal_data

# ───────────────────────────────
# AI RECOMMENDATION STORAGE
# ───────────────────────────────
def save_recommendation(user_id, text):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO ai_recommendations (user_id, recommendation)
        VALUES (?, ?)
    """, (user_id, text))

    conn.commit()
    conn.close()