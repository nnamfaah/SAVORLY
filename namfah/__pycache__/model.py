"""
model.py 
Data models and nutrition lookup table
"""
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime

def get_slot_from_time(dt: datetime = None) -> str:
    """Auto-detect meal slot from current time."""
    hour = (dt or datetime.now()).hour
    if 5 <= hour < 10:
        return "Breakfast"
    elif 10 <= hour < 14:
        return "Lunch"
    elif 14 <= hour < 18:
        return "Dinner"
    else:
        return "Snack"

# ── Nutrition DB (per typical serving) ───────────────────────────────────────
food_db: Dict[str, Dict[str, float]] = {
    "banana": {"protein": 1.3, "carbs": 27.0, "fats": 0.4, "mineral": 0.8, "fiber": 3.1, "kcal": 105},
    "oat milk": {"protein": 1.0, "carbs": 16.0, "fats": 1.5, "mineral": 0.3, "fiber": 1.9, "kcal": 80},
    "sourdough": {"protein": 8.0, "carbs": 49.0, "fats": 1.2, "mineral": 0.5, "fiber": 2.4, "kcal": 240},
    "chicken": {"protein": 31.0,"carbs": 0.0,  "fats": 3.6, "mineral": 1.1, "fiber": 0.0, "kcal": 165},
    "rice": {"protein": 2.7, "carbs": 28.0, "fats": 0.3, "mineral": 0.4, "fiber": 0.4, "kcal": 130},
    "broccoli": {"protein": 2.8, "carbs": 7.0,  "fats": 0.4, "mineral": 0.9, "fiber": 2.6, "kcal": 55},
    "egg": {"protein": 6.0, "carbs": 0.6,  "fats": 5.0, "mineral": 0.6, "fiber": 0.0, "kcal": 78},
    "salmon": {"protein": 25.0,"carbs": 0.0,  "fats": 13.0,"mineral": 1.2, "fiber": 0.0, "kcal": 208},
    "apple": {"protein": 0.3, "carbs": 19.0, "fats": 0.2, "mineral": 0.5, "fiber": 2.4, "kcal": 95},
    "yogurt": {"protein": 10.0,"carbs": 11.0, "fats": 0.7, "mineral": 0.9, "fiber": 0.0, "kcal": 100},
    "pasta": {"protein": 7.0, "carbs": 43.0, "fats": 1.1, "mineral": 0.3, "fiber": 2.5, "kcal": 220},
    "spinach": {"protein": 2.9, "carbs": 3.6,  "fats": 0.4, "mineral": 2.7, "fiber": 2.2, "kcal": 23},
    "almonds": {"protein": 6.0, "carbs": 6.0,  "fats": 14.0,"mineral": 0.8, "fiber": 3.5, "kcal": 164},
    "avocado": {"protein": 2.0, "carbs": 9.0,  "fats": 15.0,"mineral": 0.7, "fiber": 6.7, "kcal": 160},
    "milk": {"protein": 8.0, "carbs": 12.0, "fats": 5.0, "mineral": 1.2, "fiber": 0.0, "kcal": 122},
    "sweet potato": {"protein": 2.0, "carbs": 20.0, "fats": 0.1, "mineral": 0.6, "fiber": 3.0, "kcal": 90},
    "tuna": {"protein": 30.0,"carbs": 0.0,  "fats": 1.0, "mineral": 0.9, "fiber": 0.0, "kcal": 132},
    "oatmeal": {"protein": 5.0, "carbs": 27.0, "fats": 3.0, "mineral": 0.5, "fiber": 4.0, "kcal": 150},
    "cheese": {"protein": 7.0, "carbs": 1.3,  "fats": 9.0, "mineral": 0.7, "fiber": 0.0, "kcal": 110},
    "tomato": {"protein": 0.9, "carbs": 3.9,  "fats": 0.2, "mineral": 0.4, "fiber": 1.2, "kcal": 22},
}

nutrients = ["protein", "carbs", "fats", "mineral", "fiber"]
meal_slots = ["Breakfast", "Lunch", "Dinner", "Snack"]

# - Domain objects -
@dataclass
class NutritionInfo:
    protein: float = 0.0
    carbs: float   = 0.0
    fats: float    = 0.0
    mineral: float = 0.0
    fiber: float   = 0.0
    kcal: float    = 0.0

    def __add__(self, other: "NutritionInfo") -> "NutritionInfo":
        return NutritionInfo(
            protein = self.protein + other.protein,
            carbs   = self.carbs   + other.carbs,
            fats    = self.fats    + other.fats,
            mineral = self.mineral + other.mineral,
            fiber   = self.fiber   + other.fiber,
            kcal    = self.kcal    + other.kcal,)

    def total_macros(self) -> float:
        return self.protein + self.carbs + self.fats

@dataclass
class FoodItem:
    name: str
    meal_slot: str   # "Breakfast" | "Lunch" | "Dinner" | "Snack"

    @property
    def nutrition(self) -> NutritionInfo:
        key = self.name.lower().strip()
        match = next((k for k in food_db if key in k or k in key), None)
        if match:
            d = food_db[match]
            return NutritionInfo(**d)
        return NutritionInfo()

@dataclass
class DayRecord:
    date: str = ""
    foods: List[FoodItem] = field(default_factory=list)

    def foods_for_slot(self, slot: str) -> List[FoodItem]:
        return [f for f in self.foods if f.meal_slot == slot]

    def total_nutrition(self) -> NutritionInfo:
        result = NutritionInfo()
        for food in self.foods:
            result = result + food.nutrition
        return result

    def add_food(self, name: str, slot: str):
        parts = [p.strip() for p in name.split(",") if p.strip()]
        for p in parts:
            self.foods.append(FoodItem(name=p, meal_slot=slot))

    def remove_food(self, food: FoodItem):
        if food in self.foods:
            self.foods.remove(food)

    def move_food(self, food: FoodItem, new_slot: str):
        if food in self.foods:
            food.meal_slot = new_slot

@dataclass
class WeekRecord:
    days: List[DayRecord] = field(default_factory=list)
    mood_score: int = 4
    mood_label: str = "Excellent Mood Overall"

    def weekly_nutrition(self) -> NutritionInfo:
        result = NutritionInfo()
        for day in self.days:
            result = result + day.total_nutrition()
        return result