import sqlite3
from datetime import datetime

DB_NAME = "savorly.db"


# DATABASE CONNECTION
def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# INITIALIZE DATABASE
def init_database():

    conn = connect()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT,
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
        goal TEXT,
        activity_level TEXT,
        lifestyle TEXT,
        bmi REAL,
        bmr REAL,
        tdee REAL,
        daily_calorie_target INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # FOOD CATEGORIES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS food_categories(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    );
    """)

    # FOODS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS foods(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES food_categories(id)
    );
    """)

    # FOOD NUTRIENTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS food_nutrients(
        food_id INTEGER PRIMARY KEY,
        carbohydrate REAL DEFAULT 0,
        protein REAL DEFAULT 0,
        fat REAL DEFAULT 0,
        fiber REAL DEFAULT 0,
        sugar REAL DEFAULT 0,
        sodium REAL DEFAULT 0,
        vitamin REAL DEFAULT 0,
        mineral REAL DEFAULT 0,
        calories REAL DEFAULT 0,
        FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE
    );
    """)

    # FOOD TAGS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS food_tags(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        food_id INTEGER,
        tag TEXT,
        FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE
    );
    """)

    # FOOD LOGS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS food_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        food_id INTEGER,
        meal_type TEXT,
        portion REAL,
        portion_unit TEXT,
        mood TEXT,
        eaten_date TEXT,
        eaten_time TEXT,
        source TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (food_id) REFERENCES foods(id)
    );
    """)

    # SNAPSHOT NUTRIENTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS log_nutrients(
        log_id INTEGER PRIMARY KEY,
        carbohydrate REAL,
        protein REAL,
        fat REAL,
        fiber REAL,
        sugar REAL,
        sodium REAL,
        vitamin REAL,
        mineral REAL,
        calories REAL,
        FOREIGN KEY (log_id) REFERENCES food_logs(id) ON DELETE CASCADE
    );
    """)

    # DAILY TOTALS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS nutrition_daily_totals(
        user_id INTEGER,
        date TEXT,
        total_carbohydrate REAL DEFAULT 0,
        total_protein REAL DEFAULT 0,
        total_fat REAL DEFAULT 0,
        total_fiber REAL DEFAULT 0,
        total_sugar REAL DEFAULT 0,
        total_sodium REAL DEFAULT 0,
        total_vitamin REAL DEFAULT 0,
        total_mineral REAL DEFAULT 0,
        total_calories REAL DEFAULT 0,
        PRIMARY KEY (user_id, date),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # WEEKLY TOTALS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS nutrition_weekly_totals(
        user_id INTEGER,
        week_start TEXT,
        total_carbohydrate REAL DEFAULT 0,
        total_protein REAL DEFAULT 0,
        total_fat REAL DEFAULT 0,
        total_fiber REAL DEFAULT 0,
        total_sugar REAL DEFAULT 0,
        total_sodium REAL DEFAULT 0,
        total_vitamin REAL DEFAULT 0,
        total_mineral REAL DEFAULT 0,
        total_calories REAL DEFAULT 0,
        PRIMARY KEY (user_id, week_start),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # AI RECOMMENDATIONS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ai_recommendations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        recommendation TEXT,
        health_focus TEXT,
        reason TEXT,
        accepted INTEGER DEFAULT 0,
        swapped INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # MEAL SWAPS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meal_swaps(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recommendation_id INTEGER,
        original_food TEXT,
        swapped_food TEXT,
        swap_reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (recommendation_id) REFERENCES ai_recommendations(id) ON DELETE CASCADE
    );
    """)

    # REWARDS / GAMIFICATION
    cur.execute("""
    CREATE TABLE IF NOT EXISTS rewards(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        points INTEGER,
        badge TEXT,
        emoji TEXT,
        earned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # EATING PATTERNS (AI habit detection)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS eating_patterns(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        frequent_food TEXT,
        frequency INTEGER,
        unhealthy_flag INTEGER DEFAULT 0,
        detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # COMMUNITY RECIPES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recipes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        description TEXT,
        instructions TEXT,
        visibility TEXT DEFAULT 'public',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # RECIPE LIKES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recipe_likes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER,
        user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # INDEXES FOR PERFORMANCE
    cur.execute("CREATE INDEX IF NOT EXISTS idx_food_logs_user ON food_logs(user_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_food_logs_date ON food_logs(eaten_date);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_daily_totals ON nutrition_daily_totals(user_id, date);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_weekly_totals ON nutrition_weekly_totals(user_id, week_start);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_user ON ai_recommendations(user_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_patterns_user ON eating_patterns(user_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_recipes_user ON recipes(user_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_food_name ON foods(name);")

    conn.commit()
    conn.close()