from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Meal
from app.services.gemini_service import get_meal_recommendations
from datetime import datetime, date

recommendations_bp = Blueprint('recommendations', __name__)


@recommendations_bp.route('/', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Get AI-based meal recommendations based on remaining calorie budget."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Calculate remaining calories for today
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())

    meals = Meal.query.filter(
        Meal.user_id == user_id,
        Meal.logged_at >= start,
        Meal.logged_at <= end
    ).all()

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
