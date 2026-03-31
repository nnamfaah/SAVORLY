import sqlite3
from datetime import datetime
import hashlib
import os
import json

DB_NAME = "savorly.db"

# ───────────────────────────────
# CONNECTION
# ───────────────────────────────
def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# ───────────────────────────────
# INITIALIZE DATABASE
# ───────────────────────────────
def init_database():
    conn = connect()
    cur = conn.cursor()

    # USERS table
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

    # FOODS table
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

    # MEALS table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        meal_data TEXT NOT NULL,
        meal_type TEXT NOT NULL DEFAULT 'general',
        food TEXT NOT NULL DEFAULT '',
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(user_id, date)
    );
    """)

    # FOOD HISTORY
    cur.execute("""
    CREATE TABLE IF NOT EXISTS food_history(
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

    # AI RECOMMENDATIONS (if not exists)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        meal_data TEXT NOT NULL,
        meal_type TEXT NOT NULL DEFAULT 'general',
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(user_id, date)
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
        # Example: add a new column safely
        cur.execute("ALTER TABLE users ADD COLUMN salt TEXT;")
    except sqlite3.OperationalError:
        pass  # column already exists

    conn.commit()
    conn.close()

def fix_db_on_startup():
    conn = connect()
    cur = conn.cursor()

    for col, definition in [
        ("meal_data", "TEXT DEFAULT '{}'"),
        ("meal_type", "TEXT DEFAULT 'general'"),
        ("food",      "TEXT DEFAULT ''"),
    ]:
        try:
            cur.execute(f"ALTER TABLE meals ADD COLUMN {col} {definition}")
        except sqlite3.OperationalError:
            pass

    cur.execute("UPDATE meals SET meal_data = '{}' WHERE meal_data IS NULL")
    cur.execute("DELETE FROM meals WHERE date = 'week_update'")
    cur.execute("""
        DELETE FROM meals WHERE id NOT IN (
            SELECT MIN(id) FROM meals GROUP BY user_id, date
        )
    """)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_date ON meals(user_id, date)")

    conn.commit()
    conn.close()
# ───────────────────────────────
# ENSURE UNIQUE CONSTRAINTS
# ───────────────────────────────
def ensure_meals_unique():
    conn = connect()
    cur = conn.cursor()
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_date ON meals(user_id, date);")
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
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return hashed.hex(), salt.hex()

def verify_password(input_password, stored_hash, salt):
    hashed, _ = hash_password(input_password, salt)
    return hashed == stored_hash

def update_password(username, new_password):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    user = cur.fetchone()
    if not user:
        conn.close()
        return False, "not found"
    hashed, salt = hash_password(new_password)
    cur.execute("UPDATE users SET password_hash=?, salt=? WHERE username=?",
                (hashed, salt, username))
    conn.commit()
    conn.close()
    return True, "Password changed successfully"

# ───────────────────────────────
# AUTH SYSTEM
# ───────────────────────────────
def register_user(username, password):
    conn = connect()
    cur = conn.cursor()
    hashed, salt = hash_password(password)
    try:
        cur.execute("INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)", (username, hashed, salt))
        conn.commit()
        return True, "User registered successfully"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    finally:
        conn.close()

def login_user(username, password):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash, salt FROM users WHERE username=?", (username,))
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
def save_user_profile(user_id, age=None, gender=None, height=None, weight=None, bmi=None, bmr=None, tdee=None):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM user_profiles WHERE user_id=?", (user_id,))
    exists = cur.fetchone()
    if exists:
        cur.execute("""
            UPDATE user_profiles
            SET age=?, gender=?, height=?, weight=?, bmi=?, bmr=?, tdee=?, updated_at=CURRENT_TIMESTAMP
            WHERE user_id=?
        """, (age, gender, height, weight, bmi, bmr, tdee, user_id))
    else:
        cur.execute("""
            INSERT INTO user_profiles (user_id, age, gender, height, weight, bmi, bmr, tdee)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, age, gender, height, weight, bmi, bmr, tdee))
    conn.commit()
    conn.close()

def get_user_profile(user_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT age, gender, height, weight, bmi, bmr, tdee FROM user_profiles WHERE user_id=?", (user_id,))
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
        return {"id": row[0], "username": row[1], "bmi": row[2], "tdee": row[3]}
    return None

# ───────────────────────────────
# FOOD HISTORY
# ───────────────────────────────
def save_food(food_text, portion, meal_type, time, bmi=None, bmr=None, tdee=None):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO food_history(food_text, portion, meal_type, time, bmi, bmr, tdee)
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

# ───────────────────────────────
# MEAL DATA
# ───────────────────────────────
def save_meal_data(user_id, date, meals_for_day, meal_type="general", food=""):
    meals_json = json.dumps(meals_for_day or {})
    ensure_meals_unique()

    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO meals (user_id, date, meal_data, meal_type, food)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
                meal_data=excluded.meal_data,
                meal_type=excluded.meal_type,
                food=excluded.food
        """, (user_id, date, meals_json, meal_type, food))
    conn.commit()

def load_meal_data(user_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT date, meal_data FROM meals WHERE user_id=?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    meal_data = {}
    for date, meal_json in rows:
        try:
            meal_data[date] = json.loads(meal_json or "{}")
        except json.JSONDecodeError:
            meal_data[date] = {}
    return meal_data

def remove_duplicate_meals():
    conn = connect()
    cur = conn.cursor()
    
    # Keep the first occurrence of each (user_id, date)
    cur.execute("""
        DELETE FROM meals
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM meals
            GROUP BY user_id, date
        )
    """)
    
    conn.commit()
    conn.close()

def ensure_meals_unique():
    """Removes duplicates and ensures meals table has UNIQUE(user_id, date)"""
    conn = connect()
    cur = conn.cursor()

    # Remove duplicates, keeping the earliest id
    cur.execute("""
        DELETE FROM meals
        WHERE id NOT IN (
            SELECT MIN(id) FROM meals
            GROUP BY user_id, date
        )
    """)

    # Add UNIQUE index safely
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_date ON meals(user_id, date);")

    conn.commit()
    conn.close()

def migrate_meals_table():
    conn = connect()
    cur = conn.cursor()

    # Add missing columns safely with defaults
    try:
        cur.execute("ALTER TABLE meals ADD COLUMN meal_type TEXT NOT NULL DEFAULT 'general';")
    except sqlite3.OperationalError:
        pass  # already exists

    try:
        cur.execute("ALTER TABLE meals ADD COLUMN food TEXT NOT NULL DEFAULT '';")
    except sqlite3.OperationalError:
        pass  # already exists

    # Remove duplicates and ensure UNIQUE constraint
    cur.execute("""
        DELETE FROM meals
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM meals
            GROUP BY user_id, date
        )
    """)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_date ON meals(user_id, date);")

    conn.commit()
    conn.close()

def remove_duplicate_meals():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM meals
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM meals
            GROUP BY user_id, date
        )
    """)
    conn.commit()
    conn.close()

# ───────────────────────────────
# CHECK IF USER HAS HEALTH DATA
# ───────────────────────────────
def user_has_health_data(user_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT bmi, tdee FROM user_profiles WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None and row[0] is not None and row[1] is not None

# ───────────────────────────────
# AI RECOMMENDATION
# ───────────────────────────────
def save_recommendation(user_id, text):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO ai_recommendations(user_id, recommendation) VALUES (?, ?)", (user_id, text))
    conn.commit()
    conn.close()