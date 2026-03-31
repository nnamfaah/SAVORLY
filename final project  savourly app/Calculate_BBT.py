class BBTCalculator:

    @staticmethod
    def calculate_bmi(weight, height):
        """
        weight: kg
        height: cm
        """
        if height <= 0:
            raise ValueError("Height must be greater than 0")

        height_m = height / 100
        bmi = weight / (height_m ** 2)

        return round(bmi, 2)

    @staticmethod
    def calculate_bmr(weight, height, age, gender):
        """
        weight: kg
        height: cm
        age: years
        gender: male / female
        """

        if gender.lower() == "male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        return round(bmr, 2)

    @staticmethod
    def calculate_tdee(bmr, activity):
        """
        activity can be:
        - index: 1–5
        - string: 'sedentary', 'light', etc.
        """

        activity_map = {
            1: 1.2,
            2: 1.375,
            3: 1.55,
            4: 1.725,
            5: 1.9,
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }

        multiplier = activity_map.get(activity, 1.2)

        tdee = bmr * multiplier

        return round(tdee, 2)