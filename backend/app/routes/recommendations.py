from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Meal
from app.repositories.user_repository import UserRepository
from app.repositories.meal_repository import MealRepository
from app.services.gemini_service import get_meal_recommendations
from datetime import datetime, date, timezone

recommendations_bp = Blueprint('recommendations', __name__)


@recommendations_bp.route('/', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Get AI-based meal recommendations based on remaining calorie budget."""
    user_id = get_jwt_identity()
    user = UserRepository.get_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Calculate remaining calories for today
    today = datetime.utcnow().date()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())

    meals = MealRepository.get_by_user_and_date_range(user_id, start, end)

    total_consumed = sum(m.total_calories for m in meals)
    remaining = max(user.daily_calorie_budget - total_consumed, 0)

    meal_type = request.args.get('meal_type', 'any')
    dietary_preferences = request.args.get('preferences', 'none')

    recommendations = get_meal_recommendations(
        remaining_calories=remaining,
        goal=user.goal,
        meal_type=meal_type,
        dietary_preferences=dietary_preferences
    )

    return jsonify({
        'remaining_calories': remaining,
        'budget': user.daily_calorie_budget,
        'consumed': total_consumed,
        'goal': user.goal,
        **recommendations
    }), 200
