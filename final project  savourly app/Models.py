from dataclasses import dataclass

@dataclass
class FoodInput:

    food_text: str
    portion: str
    meal_type: str
    time_of_day: str
    quantity: int