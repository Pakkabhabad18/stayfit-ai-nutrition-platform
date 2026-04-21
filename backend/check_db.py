from app import create_app, db
from app.models import User, Meal, DailyLog
import json

app = create_app()

with app.app_context():
    print("="*50)
    print("DATABASE STATUS")
    print("="*50)
    
    # Check Users
    users = User.query.all()
    print(f"\nUSERS ({len(users)} total):")
    for user in users:
        print(f" - {user.name} ({user.email}) | Goal: {user.goal} | Profile Completed: {user.profile_completed}")

    # Check Meals
    meals = Meal.query.all()
    print(f"\nMEALS ({len(meals)} total):")
    for meal in meals:
        print(f" - [{meal.meal_type}] {meal.total_calories} cal | Logged by: {meal.user_id}")

    # Check Daily Logs
    logs = DailyLog.query.all()
    print(f"\nDAILY LOGS ({len(logs)} total):")
    for log in logs:
        print(f" - {log.log_date} | {log.total_calories}/{log.budget} | Logged by: {log.user_id}")
    
    print("\n" + "="*50)
