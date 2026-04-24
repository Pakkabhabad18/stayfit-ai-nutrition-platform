from app import db
from app.models import Meal

class MealRepository:
    @staticmethod
    def get_by_id_and_user(meal_id, user_id):
        return Meal.query.filter_by(id=meal_id, user_id=user_id).first()

    @staticmethod
    def get_by_user_and_date_range(user_id, start_date, end_date):
        return Meal.query.filter(
            Meal.user_id == user_id,
            Meal.logged_at >= start_date,
            Meal.logged_at <= end_date
        ).order_by(Meal.logged_at.desc()).all()

    @staticmethod
    def create(meal):
        db.session.add(meal)
        db.session.commit()
        return meal

    @staticmethod
    def delete(meal):
        db.session.delete(meal)
        db.session.commit()
