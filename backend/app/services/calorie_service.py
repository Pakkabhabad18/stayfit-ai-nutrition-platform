def calculate_bmr(weight_kg, height_cm, age, gender):
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation."""
    if gender == 'male':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return bmr


def calculate_tdee(bmr, activity_level):
    """Calculate Total Daily Energy Expenditure."""
    multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.9,
    }
    return bmr * multipliers.get(activity_level, 1.55)


def calculate_daily_budget(weight_kg, height_cm, age, gender, activity_level, goal):
    """Calculate recommended daily calorie budget based on user profile."""
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = calculate_tdee(bmr, activity_level)

    adjustments = {
        'lose': -500,       # ~0.5 kg per week loss
        'maintain': 0,
        'gain': 500,        # ~0.5 kg per week gain
    }

    budget = int(tdee + adjustments.get(goal, 0))
    # Ensure minimum safe intake
    return max(budget, 1200)
