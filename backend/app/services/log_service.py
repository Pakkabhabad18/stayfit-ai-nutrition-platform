import json
from datetime import datetime, date, timezone
from sqlalchemy import text
from app import db
from app.models import Meal, DailyLog, User
from app.repositories.user_repository import UserRepository
from app.repositories.meal_repository import MealRepository
from app.repositories.daily_log_repository import DailyLogRepository

def update_daily_log(user_id, log_date=None):
    """Recalculate and update the daily log for a user."""
    if log_date is None:
        log_date = datetime.now(timezone.utc).date()

    user = UserRepository.get_by_id(user_id)

    # Get all meals for this date
    start = datetime.combine(log_date, datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(log_date, datetime.max.time(), tzinfo=timezone.utc)

    meals = MealRepository.get_by_user_and_date_range(user_id, start, end)

    total_cal = sum(m.total_calories for m in meals)
    total_protein = sum(m.protein_g or 0 for m in meals)
    total_carbs = sum(m.carbs_g or 0 for m in meals)
    total_fat = sum(m.fat_g or 0 for m in meals)

    daily_log = DailyLogRepository.get_by_user_and_date(user_id, log_date)

    old_cal = 0
    budget = user.daily_calorie_budget if user else 2000
    
    if daily_log:
        old_cal = daily_log.total_calories
        daily_log.total_calories = total_cal
        daily_log.total_protein_g = total_protein
        daily_log.total_carbs_g = total_carbs
        daily_log.total_fat_g = total_fat
        daily_log.budget = budget
    else:
        daily_log = DailyLog(
            user_id=user_id,
            log_date=log_date,
            total_calories=total_cal,
            total_protein_g=total_protein,
            total_carbs_g=total_carbs,
            total_fat_g=total_fat,
            budget=budget
        )
        DailyLogRepository.create(daily_log)

    DailyLogRepository.commit()
    triggered_alerts = []

    # Pub/Sub Publisher: Fire events when crossing critical thresholds independently
    thresholds = [
        (0.5, "You have reached 50% of your daily calorie intake! 🏃‍♂️"),
        (0.8, "You have hit 80% of your daily calorie budget! ⚠️"),
        (1.0, "You have reached 100% of your calorie limit for today! 🛑")
    ]
    
    for pct, msg in thresholds:
        if old_cal < (budget * pct) and total_cal >= (budget * pct):
            triggered_alerts.append(msg)
            payload = json.dumps({
                "user_id": user_id,
                "message": msg
            })
            # Use Postgres NOTIFY for decoupled microservices real-time communication
            db.session.execute(text(f"NOTIFY calorie_alerts, '{payload}'"))
            db.session.commit()

    return daily_log, triggered_alerts
