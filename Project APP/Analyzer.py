import re
import random
from Database_sor import connect
from food_database import FOOD_DATABASE


class FoodAnalyzer:
    def __init__(self):

        self.stop_words = {
            "ate","with","today","have","and","for","the","this",
            "morning","breakfast","lunch","dinner","evening"
        }

        self.portion_words = {
            "one":1,"two":2,"three":3,"four":4,"five":5,
            "six":6,"seven":7,"eight":8,"nine":9,"ten":10
        }

        self.food_synonyms = {
            "krapow": "pad kra pao",
            "kra pao": "pad kra pao",
            "pad krapow": "pad kra pao",
            "fried rice": "khao pad",
            "papaya salad": "som tam",
            "tom yum soup": "tom yum",
            "thai fried noodles": "pad thai"
        }

        self.food_database = FOOD_DATABASE

    # -------------------------
    # TEXT CLEANING
    # -------------------------
    def clean_text(self, text):
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        return text

    def normalize_word(self, word):
        if word.endswith("s"):
            return word[:-1]
        return word

    def normalize_food_name(self, text):
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)

        # Apply synonyms
        if text in self.food_synonyms:
            return self.food_synonyms[text]

        return text

    # -------------------------
    # FOOD DETECTION
    # -------------------------
    def detect_foods(self, text):

        text = self.clean_text(text)

        detected = []
        unknown = []

        # Check multi-word foods FIRST (important)
        for food in sorted(self.food_database.keys(), key=len, reverse=True):
            if food in text:
                detected.append(food)

        words = text.split()

        for word in words:
            normalized = self.normalize_word(word)
            normalized = self.normalize_food_name(normalized)

            if normalized in self.food_database and normalized not in detected:
                detected.append(normalized)

            elif normalized not in self.stop_words and len(normalized) > 3:
                if normalized not in self.food_database:
                    unknown.append(normalized)

        return detected, unknown

    # -------------------------
    # PORTION DETECTION
    # -------------------------
    def detect_portions(self, text):

        text = self.clean_text(text)
        words = text.split()

        portions = {}

        for i, word in enumerate(words):

            # numeric portion (2 eggs)
            if word.isdigit():
                qty = int(word)
                if i + 1 < len(words):
                    food = self.normalize_food_name(self.normalize_word(words[i+1]))
                    portions[food] = qty

            # word portion (two eggs)
            elif word in self.portion_words:
                qty = self.portion_words[word]
                if i + 1 < len(words):
                    food = self.normalize_food_name(self.normalize_word(words[i+1]))
                    portions[food] = qty

        return portions

    # -------------------------
    # UNKNOWN FOOD ESTIMATION
    # -------------------------
    def estimate_unknown(self, food_name):

        if "juice" in food_name:
            return {"category":"Estimated","carbs":8,"protein":1,"fat":0,"vitamins":7,"minerals":5}

        if "pizza" in food_name:
            return {"category":"Estimated","carbs":8,"protein":6,"fat":8,"vitamins":2,"minerals":3}

        return {
            "category":"Estimated",
            "carbs": random.randint(3,7),
            "protein": random.randint(2,6),
            "fat": random.randint(2,6),
            "vitamins": random.randint(2,6),
            "minerals": random.randint(2,6)
        }

    # -------------------------
    # CALCULATIONS
    # -------------------------
    def estimate_calories(self, profile, portion):

        carbs = profile["carbs"] * portion
        protein = profile["protein"] * portion
        fat = profile["fat"] * portion

        return (carbs * 4) + (protein * 4) + (fat * 9)

    def calculate_health_score(self, profile):

        score = (
            profile["vitamins"] * 0.3 +
            profile["minerals"] * 0.3 +
            profile["protein"] * 0.2 +
            profile["carbs"] * 0.1 -
            profile["fat"] * 0.2
        )

        return round(max(1, min(10, score)), 2)

    # -------------------------
    # DATABASE SAVE
    # -------------------------
    def save_food(self, name, profile, health_score):

        try:
            conn = connect()
            cur = conn.cursor()

            cur.execute("""
                INSERT OR IGNORE INTO foods
                (name, category, health_score, carbs, protein, fat, vitamins, minerals)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name.title(),
                profile["category"],
                health_score,
                profile["carbs"],
                profile["protein"],
                profile["fat"],
                profile["vitamins"],
                profile["minerals"]
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            print("DB Error:", e)

    # -------------------------
    # MAIN ANALYSIS
    # -------------------------
    def analyze(self, text):

        portions = self.detect_portions(text)
        recognized, unknown = self.detect_foods(text)

        results = []

    
        recognized = list(dict.fromkeys(recognized))
        unknown = list(dict.fromkeys(unknown))

    # -------------------------
    # KNOWN FOODS
    # -------------------------
        for food in recognized:

            profile = self.food_database[food]
            portion = portions.get(food, 1)

            calories = self.estimate_calories(profile, portion)
            score = self.calculate_health_score(profile)

            results.append({
            "name": food.title(),
            "macros": {
                "protein": profile.get("protein", 0),
                "carbs": profile.get("carbs", 0),
                "fat": profile.get("fat", 0),
                "vitamins": profile.get("vitamins", 0),
                "minerals": profile.get("minerals", 0)
            },
            "portion": portion,
            "calories": calories,
            "health_score": score,
            "source": "database"
            })

    # -------------------------
    # UNKNOWN FOODS
    # -------------------------
        for food in unknown:

            profile = self.estimate_unknown(food)
            portion = portions.get(food, 1)

            calories = self.estimate_calories(profile, portion)
            score = self.calculate_health_score(profile)

            self.save_food(food, profile, score)

            results.append({
            "name": food.title(),
            "macros": {
                "protein": profile.get("protein", 0),
                "carbs": profile.get("carbs", 0),
                "fat": profile.get("fat", 0),
                "vitamins": profile.get("vitamins", 0),
                "minerals": profile.get("minerals", 0)
            },
            "portion": portion,
            "calories": calories,
            "health_score": score,
            "source": "estimated"
            })

        return results


    def detect_foods(self, text):

        text = self.clean_text(text)

        detected = []
        unknown = []

        # Match full phrases safely
        for food in sorted(self.food_database.keys(), key=len, reverse=True):
            if f" {food} " in f" {text} ":
                detected.append(food)

        words = text.split()

        for word in words:
            normalized = self.normalize_word(word)
            normalized = self.normalize_food_name(normalized)

            if normalized in self.food_database and normalized not in detected:
                detected.append(normalized)

            elif normalized not in self.stop_words and len(normalized) > 3:
                if normalized not in self.food_database:
                    unknown.append(normalized)

        return detected, unknown

    # -------------------------
    # RECOMMENDATION ENGINE
    # -------------------------
    def generate_recommendation(self, results):

        total_protein = sum(r["profile"]["protein"] for r in results)
        total_fat = sum(r["profile"]["fat"] for r in results)

        tips = []

        if total_protein < 15:
            tips.append("Add more protein like chicken, eggs, or tofu")

        if total_fat > 20:
            tips.append("Reduce fried or fatty foods")

        if not tips:
            tips.append("Balanced meal — good job!")

        return tips