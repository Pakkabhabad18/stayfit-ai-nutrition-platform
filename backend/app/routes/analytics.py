from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Meal, DailyLog, User
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/daily', methods=['GET'])
@jwt_required()
def get_daily_summary():
    """Get daily calorie summary for today."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(today, datetime.max.time(), tzinfo=timezone.utc)

    meals = Meal.query.filter(
        Meal.user_id == user_id,
        Meal.logged_at >= start,
        Meal.logged_at <= end
    ).all()

    total_calories = sum(m.total_calories for m in meals)
    budget = user.daily_calorie_budget if user else 2000
    remaining = budget - total_calories

    # Meal type breakdown
    breakdown = {}
    for meal_type in ['breakfast', 'lunch', 'dinner', 'snack']:
        type_meals = [m for m in meals if m.meal_type == meal_type]
        breakdown[meal_type] = {
            'calories': sum(m.total_calories for m in type_meals),
            'count': len(type_meals)
        }

    return jsonify({
        'date': today.isoformat(),
        'total_calories': total_calories,
        'budget': budget,
        'remaining': remaining,
        'percentage': round((total_calories / budget * 100), 1) if budget > 0 else 0,
        'breakdown': breakdown,
        'macros': {
            'protein_g': round(sum(m.protein_g or 0 for m in meals), 1),
            'carbs_g': round(sum(m.carbs_g or 0 for m in meals), 1),
            'fat_g': round(sum(m.fat_g or 0 for m in meals), 1),
        },
        'alert': 'exceeded' if total_calories > budget else ('warning' if total_calories > budget * 0.9 else 'normal')
    }), 200


@analytics_bp.route('/weekly', methods=['GET'])
@jwt_required()
def get_weekly_trends():
    """Get weekly calorie trends for the past 7 days."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    budget = user.daily_calorie_budget if user else 2000

    trends = []
    days_with_meals = 0
    total_calories_logged = 0
    days_on_track = 0
    now_utc = datetime.now(timezone.utc)
    for i in range(6, -1, -1):
        day = now_utc.date() - timedelta(days=i)
        start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
        end = datetime.combine(day, datetime.max.time(), tzinfo=timezone.utc)

        meals = Meal.query.filter(
            Meal.user_id == user_id,
            Meal.logged_at >= start,
            Meal.logged_at <= end
        ).all()

        total_cal = sum(m.total_calories for m in meals)
        logged = len(meals) > 0
        if logged:
            days_with_meals += 1
            total_calories_logged += total_cal
            if total_cal <= budget:
                days_on_track += 1

        trends.append({
            'date': day.isoformat(),
            'day_name': day.strftime('%a'),
            'calories': total_cal,
            'budget': budget,
            'protein_g': round(sum(m.protein_g or 0 for m in meals), 1),
            'carbs_g': round(sum(m.carbs_g or 0 for m in meals), 1),
            'fat_g': round(sum(m.fat_g or 0 for m in meals), 1),
            'on_track': total_cal <= budget if logged else False,
            'logged': logged
        })

    avg_calories = (total_calories_logged / days_with_meals) if days_with_meals > 0 else 0

    return jsonify({
        'trends': trends,
        'average_calories': round(avg_calories),
        'budget': budget,
        'days_on_track': days_on_track,
        'days_logged': days_with_meals,
        'total_days': 7
    }), 200


@analytics_bp.route('/progress', methods=['GET'])
@jwt_required()
def get_progress():
    """Get overall progress toward dietary goals."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Get data for the last 30 days
    thirty_days_ago = datetime.now(timezone.utc).date() - timedelta(days=30)

    daily_logs = DailyLog.query.filter(
        DailyLog.user_id == user_id,
        DailyLog.log_date >= thirty_days_ago
    ).order_by(DailyLog.log_date).all()

    days_logged = len(daily_logs)
    if days_logged == 0:
        return jsonify({
            'days_logged': 0,
            'average_calories': 0,
            'days_on_track': 0,
            'consistency': 0,
            'goal': user.goal,
            'budget': user.daily_calorie_budget,
        }), 200

    avg_cal = sum(d.total_calories for d in daily_logs) / days_logged
    days_on_track = sum(1 for d in daily_logs if d.total_calories <= d.budget)

    return jsonify({
        'days_logged': days_logged,
        'average_calories': round(avg_cal),
        'days_on_track': days_on_track,
        'consistency': round(days_on_track / days_logged * 100, 1),
        'goal': user.goal,
        'budget': user.daily_calorie_budget,
        'trend_data': [d.to_dict() for d in daily_logs]
    }), 200
