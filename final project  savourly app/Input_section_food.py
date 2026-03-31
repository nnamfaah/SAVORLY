import re
from Models import FoodInput


class InputProcessor:
    def __init__(self):
        self.portions = ["small", "medium", "large", "extra large"]

        self.meals = ["breakfast", "lunch", "dinner", "snack"]

        self.time_words = {
            "morning": "morning",
            "afternoon": "afternoon",
            "evening": "evening",
            "night": "night"
        }

    def clean_text(self, text):
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        return text

    def detect_portion(self, text):

        for p in self.portions:
            if p in text:
                return p

        return "medium"

    def detect_meal(self, text):

        for m in self.meals:
            if m in text:
                return m

        return "unknown"

    def detect_time(self, text):

        for word in self.time_words:
            if word in text:
                return self.time_words[word]

        return "unknown"
    
    def detect_quantity(self, text):

        quantity_words = {
            "one":1,
            "two":2,
            "three":3,
            "four":4,
            "five":5
        }

        for word in text.split():
            if word.isdigit():
                return int(word)

            if word in quantity_words:
                return quantity_words[word]

        return 1
    
    def process(self, text):

        cleaned = self.clean_text(text)

        return FoodInput(
            food_text=cleaned,
            portion=self.detect_portion(cleaned),
            meal_type=self.detect_meal(cleaned),
            time_of_day=self.detect_time(cleaned),
            quantity = self.detect_quantity(cleaned)
        )