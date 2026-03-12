import re
from models import FoodInput


class InputProcessor:

    def clean_text(self, text):
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        return text

    def detect_portion(self, text):

        portions = ["small", "medium", "large", "extra large"]

        for p in portions:
            if p in text:
                return p

        return "medium"

    def detect_meal(self, text):

        meals = ["breakfast", "lunch", "dinner", "snack"]

        for m in meals:
            if m in text:
                return m

        return "unknown"

    def detect_time(self, text):

        if "morning" in text:
            return "morning"

        if "afternoon" in text:
            return "afternoon"

        if "night" in text:
            return "night"

        return "unknown"

    def process(self, text):

        cleaned = self.clean_text(text)

        return FoodInput(
            food_text=cleaned,
            portion=self.detect_portion(cleaned),
            meal_type=self.detect_meal(cleaned),
            time_of_day=self.detect_time(cleaned)
        )