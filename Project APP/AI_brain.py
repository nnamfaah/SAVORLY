from Analyzer import FoodAnalyzer
from Database_sor import (
    save_recommendation,
    get_user_profile,
    connect
)
from datetime import datetime


class AIBrain:
    def __init__(self):
        self.analyzer = FoodAnalyzer()

    # -------------------------------
    # MAIN ENTRY POINT
    # -------------------------------
    def process_user_input(self, user_id, text):
        """
        Full pipeline:
        1. Analyze food
        2. Save logs
        3. Update daily nutrition
        4. Generate recommendation
        """

        # 1. Analyze food
        analysis = self.analyzer.analyze(text)

        # 2. Detect meal type
        meal_type = self.analyzer.detect_meal_type(text)

        # 3. Save logs + nutrients
        self._save_food_logs(user_id, analysis, meal_type)

        # 4. Update daily totals
        self._update_daily_totals(user_id, analysis)

        # 5. Generate recommendation
        recommendation = self._generate_ai_recommendation(user_id)

        # 6. Save recommendation
        save_recommendation(user_id, recommendation)

        return {
            "analysis": analysis,
            "meal_type": meal_type,
            "recommendation": recommendation
        }

    # -------------------------------
    # SAVE FOOD LOGS
    # -------------------------------
    def _save_food_logs(self, user_id, analysis, meal_type):
        conn = connect()
        cur = conn.cursor()

        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M")

        for item in analysis:
            # insert food if not exists
            cur.execute("INSERT OR IGNORE INTO foods (name) VALUES (?)", (item["name"],))

            cur.execute("SELECT id FROM foods WHERE name=?", (item["name"],))
            food_id = cur.fetchone()[0]

            # insert log
            cur.execute("""
                INSERT INTO food_logs
                (user_id, food_id, meal_type, portion, eaten_date, eaten_time, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                food_id,
                meal_type,
                item["portion"],
                date,
                time,
                item["source"]
            ))

            log_id = cur.lastrowid

            # save nutrients snapshot
            profile = item["profile"]
            cur.execute("""
                INSERT INTO log_nutrients
                (log_id, carbohydrate, protein, fat, vitamin, mineral, calories)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id,
                profile["carbs"],
                profile["protein"],
                profile["fat"],
                profile["vitamins"],
                profile["minerals"],
                item["calories"]
            ))

        conn.commit()
        conn.close()

    # -------------------------------
    # UPDATE DAILY TOTALS
    # -------------------------------
    def _update_daily_totals(self, user_id, analysis):
        conn = connect()
        cur = conn.cursor()

        date = datetime.now().strftime("%Y-%m-%d")

        totals = {
            "carbs": 0,
            "protein": 0,
            "fat": 0,
            "vitamins": 0,
            "minerals": 0,
            "calories": 0
        }

        for item in analysis:
            profile = item["profile"]
            portion = item["portion"]

            totals["carbs"] += profile["carbs"] * portion
            totals["protein"] += profile["protein"] * portion
            totals["fat"] += profile["fat"] * portion
            totals["vitamins"] += profile["vitamins"] * portion
            totals["minerals"] += profile["minerals"] * portion
            totals["calories"] += item["calories"]

        cur.execute("""
            INSERT INTO nutrition_daily_totals
            (user_id, date, total_carbohydrate, total_protein, total_fat,
             total_vitamin, total_mineral, total_calories)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
                total_carbohydrate = total_carbohydrate + excluded.total_carbohydrate,
                total_protein = total_protein + excluded.total_protein,
                total_fat = total_fat + excluded.total_fat,
                total_vitamin = total_vitamin + excluded.total_vitamin,
                total_mineral = total_mineral + excluded.total_mineral,
                total_calories = total_calories + excluded.total_calories
        """, (
            user_id, date,
            totals["carbs"],
            totals["protein"],
            totals["fat"],
            totals["vitamins"],
            totals["minerals"],
            totals["calories"]
        ))

        conn.commit()
        conn.close()

    # -------------------------------
    # AI RECOMMENDATION ENGINE
    # -------------------------------
    def _generate_ai_recommendation(self, user_id):
        conn = connect()
        cur = conn.cursor()

        date = datetime.now().strftime("%Y-%m-%d")

        # get today's totals
        cur.execute("""
            SELECT total_carbohydrate, total_protein, total_fat,
                   total_vitamin, total_mineral, total_calories
            FROM nutrition_daily_totals
            WHERE user_id=? AND date=?
        """, (user_id, date))

        row = cur.fetchone()
        conn.close()

        if not row:
            return "Start logging your meals to get AI recommendations."

        daily_totals = {
            "carbs": row[0],
            "protein": row[1],
            "fat": row[2],
            "vitamins": row[3],
            "minerals": row[4],
            "calories": row[5]
        }

        # simple target (can upgrade later)
        target = {
            "protein": 50,
            "fat": 70,
            "vitamins": 10,
            "minerals": 10,
            "calories": 2000
        }

        recs = self.analyzer.generate_recommendation(daily_totals, target)

        return " | ".join(recs)