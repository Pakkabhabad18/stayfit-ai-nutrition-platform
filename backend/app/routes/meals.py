
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Meal, DailyLog, User
from app.services.gemini_service import analyze_food_image
from datetime import datetime, date
import os
import uuid
import base64
import json
from sqlalchemy import text
# Add Pillow for image resizing
from PIL import Image
import io

meals_bp = Blueprint('meals', __name__)


def update_daily_log(user_id, log_date=None):
    """Recalculate and update the daily log for a user."""
    if log_date is None:
        log_date = date.today()

    user = User.query.get(user_id)

    # Get all meals for this date
    start = datetime.combine(log_date, datetime.min.time())
    end = datetime.combine(log_date, datetime.max.time())

    meals = Meal.query.filter(
        Meal.user_id == user_id,
        Meal.logged_at >= start,
        Meal.logged_at <= end
    ).all()

    total_cal = sum(m.total_calories for m in meals)
    total_protein = sum(m.protein_g or 0 for m in meals)
    total_carbs = sum(m.carbs_g or 0 for m in meals)
    total_fat = sum(m.fat_g or 0 for m in meals)

    daily_log = DailyLog.query.filter_by(user_id=user_id, log_date=log_date).first()

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
        db.session.add(daily_log)

    db.session.commit()
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


@meals_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_meal():
    """Upload a meal photo for AI analysis."""
    user_id = get_jwt_identity()

    meal_type = request.form.get('meal_type', 'snack')
    if meal_type not in ['breakfast', 'lunch', 'dinner', 'snack']:
        return jsonify({'error': 'Invalid meal type'}), 400

    # Handle image upload
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Save image
    filename = f"{uuid.uuid4()}.jpg"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Read and resize image for Gemini analysis
    with open(filepath, 'rb') as f:
        img = Image.open(f)
        # Resize to max 512x512, keeping aspect ratio
        img.thumbnail((512, 512))
        # Save to bytes
        img_bytes = io.BytesIO()
        # Always save as JPEG for LLM
        img.save(img_bytes, format='JPEG', quality=85)
        img_bytes.seek(0)
        image_data = img_bytes.read()

    # Use JPEG for LLM
    mime_type = 'image/jpeg'

    try:
        # Analyze with Gemini
        analysis = analyze_food_image(image_data, mime_type)

        meal = Meal(
            user_id=user_id,
            meal_type=meal_type,
            image_url=f'/api/meals/images/{filename}',
            food_items=analysis.get('food_items', []),
            total_calories=analysis.get('total_calories', 0),
            protein_g=analysis.get('total_protein_g', 0),
            carbs_g=analysis.get('total_carbs_g', 0),
            fat_g=analysis.get('total_fat_g', 0),
            fiber_g=analysis.get('total_fiber_g', 0),
        )

        db.session.add(meal)
        db.session.commit()

        # Update daily log and capture new alerts
        daily_log, alerts = update_daily_log(user_id)

        return jsonify({
            'message': 'Meal logged successfully',
            'meal': meal.to_dict(),
            'analysis': analysis,
            'alerts': alerts
        }), 201

    except Exception as e:
        import traceback
        with open('error_log.txt', 'a') as f:
            f.write("UPLOAD MEAL CRASH:\n")
            f.write(traceback.format_exc())
            f.write("\n")
        return jsonify({'error': str(e)}), 500


@meals_bp.route('/images/<filename>', methods=['GET'])
def get_image(filename):
    """Serve uploaded meal images."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@meals_bp.route('/today', methods=['GET'])
@jwt_required()
def get_today_meals():
    """Get all meals logged today."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())

    meals = Meal.query.filter(
        Meal.user_id == user_id,
        Meal.logged_at >= start,
        Meal.logged_at <= end
    ).order_by(Meal.logged_at.desc()).all()

    daily_log = DailyLog.query.filter_by(user_id=user_id, log_date=today).first()

    total_calories = sum(m.total_calories for m in meals)
    budget = user.daily_calorie_budget if user else 2000
    remaining = budget - total_calories

    # Categorize meals
    categorized = {'breakfast': [], 'lunch': [], 'dinner': [], 'snack': []}
    for meal in meals:
        categorized[meal.meal_type].append(meal.to_dict())

    return jsonify({
        'meals': [m.to_dict() for m in meals],
        'categorized': categorized,
        'summary': {
            'total_calories': total_calories,
            'budget': budget,
            'remaining': remaining,
            'protein_g': round(sum(m.protein_g or 0 for m in meals), 1),
            'carbs_g': round(sum(m.carbs_g or 0 for m in meals), 1),
            'fat_g': round(sum(m.fat_g or 0 for m in meals), 1),
        }
    }), 200


@meals_bp.route('/<meal_id>', methods=['DELETE'])
@jwt_required()
def delete_meal(meal_id):
    """Delete a meal entry."""
    user_id = get_jwt_identity()

    meal = Meal.query.filter_by(id=meal_id, user_id=user_id).first()
    if not meal:
        return jsonify({'error': 'Meal not found'}), 404

    db.session.delete(meal)
    db.session.commit()

    update_daily_log(user_id)

    return jsonify({'message': 'Meal deleted successfully'}), 200
