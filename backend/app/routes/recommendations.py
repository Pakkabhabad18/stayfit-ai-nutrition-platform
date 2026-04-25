from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Meal
from app.repositories.user_repository import UserRepository
from app.repositories.meal_repository import MealRepository
from app.services.gemini_service import get_meal_recommendations
from app.services.cache_service import cache_get, cache_set, build_recommendation_cache_key
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

recommendations_bp = Blueprint('recommendations', __name__)


@recommendations_bp.route('/', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Get AI-based meal recommendations based on remaining calorie budget.

    Cache-Aside Strategy:
    - Cache key includes user_id, remaining_calories (bucketed to nearest 50),
      goal, meal_type and dietary_preferences.
    - On a cache hit: return stored recommendations instantly (no AI call).
    - On a cache miss: call the AI, store the result, then return it.
    - TTL: 1 hour (3600 s).  Redis unavailability is handled gracefully —
      the route still works, just without caching.
    """
    user_id = get_jwt_identity()
    user = UserRepository.get_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # ── Calculate today's remaining calorie budget ──────────────────────────
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    end   = datetime.combine(today, datetime.max.time(), tzinfo=timezone.utc)

    meals = MealRepository.get_by_user_and_date_range(user_id, start, end)

    total_consumed = sum(m.total_calories for m in meals)
    remaining = max(user.daily_calorie_budget - total_consumed, 0)

    meal_type = request.args.get('meal_type', 'any')
    dietary_preferences = request.args.get('preferences', 'none')

    # ── Cache-Aside lookup ──────────────────────────────────────────────────
    cache_key = build_recommendation_cache_key(
        remaining_calories=remaining,
        goal=user.goal,
        meal_type=meal_type,
        dietary_preferences=dietary_preferences,
    )

    cached = cache_get(cache_key)
    if cached is not None:
        logger.info("Cache HIT for recommendations (key=%s)", cache_key)
        return jsonify({
            'remaining_calories': remaining,
            'budget': user.daily_calorie_budget,
            'consumed': total_consumed,
            'goal': user.goal,
            'cache_hit': True,
            **cached,
        }), 200

    # ── Cache MISS — fetch from AI ──────────────────────────────────────────
    logger.info("Cache MISS for recommendations (key=%s) — calling AI", cache_key)
    recommendations = get_meal_recommendations(
        remaining_calories=remaining,
        goal=user.goal,
        meal_type=meal_type,
        dietary_preferences=dietary_preferences,
    )

    # Store in cache for 1 hour
    cache_set(cache_key, recommendations, ttl=3600)

    return jsonify({
        'remaining_calories': remaining,
        'budget': user.daily_calorie_budget,
        'consumed': total_consumed,
        'goal': user.goal,
        'cache_hit': False,
        **recommendations,
    }), 200
