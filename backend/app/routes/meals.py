
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Meal, DailyLog, User
from app.services.gemini_service import analyze_food_image, analyze_food_text
from app.tasks import process_meal_analysis, process_text_analysis
from celery.result import AsyncResult
from datetime import datetime, date
import os
import uuid
import base64
import json
from sqlalchemy import text
# Add Pillow for image resizing
from PIL import Image
import io
from app.services.log_service import update_daily_log

meals_bp = Blueprint('meals', __name__)




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
        # Trigger background analysis
        task = process_meal_analysis.delay(user_id, meal_type, filename)

        return jsonify({
            'message': 'Analysis started in background',
            'task_id': task.id,
            'image_url': f'/api/meals/images/{filename}'
        }), 202

    except Exception as e:
        import traceback
        with open('error_log.txt', 'a') as f:
            f.write("UPLOAD MEAL CRASH:\n")
            f.write(traceback.format_exc())
            f.write("\n")
        return jsonify({'error': str(e)}), 500


@meals_bp.route('/task-status/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    """Check the status of a background analysis task."""
    result = AsyncResult(task_id)
    
    response = {
        'status': result.status,
        'task_id': task_id
    }

    if result.ready():
        if result.successful():
            response.update({
                'result': result.result
            })
        else:
            response.update({
                'error': str(result.result)
            })

    return jsonify(response), 200

@meals_bp.route('/log_text', methods=['POST'])
@jwt_required()
def log_meal_text():
    """Log a meal using a text description."""
    user_id = get_jwt_identity()

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    meal_type = data.get('meal_type', 'snack')
    text_description = data.get('text', '')

    if meal_type not in ['breakfast', 'lunch', 'dinner', 'snack']:
        return jsonify({'error': 'Invalid meal type'}), 400

    if not text_description.strip():
        return jsonify({'error': 'Text description cannot be empty'}), 400

    try:
        # Trigger background text analysis
        task = process_text_analysis.delay(user_id, meal_type, text_description)

        return jsonify({
            'message': 'Text analysis started in background',
            'task_id': task.id
        }), 202

    except Exception as e:
        import traceback
        with open('error_log.txt', 'a') as f:
            f.write("LOG MEAL TEXT CRASH:\n")
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
