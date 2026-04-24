import os
import io
import json
import uuid
from PIL import Image
from celery import shared_task
from flask import current_app
from app import db
from app.models import Meal, User
from app.services.gemini_service import analyze_food_image, analyze_food_text
from app.services.log_service import update_daily_log

@shared_task(ignore_result=False)
def process_meal_analysis(user_id, meal_type, filename):
    """
    Background task to analyze food image, save to DB, and update daily log.
    """
    print(f"[CELERY] Starting analysis for user {user_id}, file: {filename}")
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    try:
        # 1. Read and resize image for Gemini analysis
        print(f"[CELERY] Reading image from {filepath}...")
        with open(filepath, 'rb') as f:
            img = Image.open(f)
            img.thumbnail((512, 512))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG', quality=85)
            img_bytes.seek(0)
            image_data = img_bytes.read()

        mime_type = 'image/jpeg'

        # 2. Analyze with Gemini
        print("[CELERY] Calling AI API... (this may take 10-15 seconds)")
        analysis = analyze_food_image(image_data, mime_type)
        provider = analysis.get('provider', 'AI')
        print(f"[CELERY] {provider} analysis complete: {json.dumps(analysis)[:100]}...")

        # 3. Create and save Meal record
        print("[CELERY] Saving meal to database...")
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

        # 4. Update daily log and capture new alerts
        print("[CELERY] Updating daily log...")
        _, alerts = update_daily_log(user_id)
        print("[CELERY] Task finished successfully!")

        return {
            'status': 'completed',
            'meal_id': meal.id,
            'analysis': analysis,
            'alerts': alerts
        }

    except Exception as e:
        import traceback
        error_msg = f"TASK ERROR: {str(e)}\n{traceback.format_exc()}"
        with open('error_log.txt', 'a') as f:
            f.write(error_msg + "\n")
        return {
            'status': 'failed',
            'error': str(e)
        }

@shared_task(ignore_result=False)
def process_text_analysis(user_id, meal_type, text_description):
    """
    Background task to analyze food text description, save to DB, and update daily log.
    """
    print(f"[CELERY] Starting text analysis for user {user_id}")
    
    try:
        # 1. Analyze with Gemini
        print("[CELERY] Calling AI API for text... (this may take 5-10 seconds)")
        analysis = analyze_food_text(text_description)
        provider = analysis.get('provider', 'AI')
        print(f"[CELERY] {provider} text analysis complete: {json.dumps(analysis)[:100]}...")

        # 2. Create and save Meal record
        print("[CELERY] Saving meal to database...")
        meal = Meal(
            user_id=user_id,
            meal_type=meal_type,
            image_url=None,
            food_items=analysis.get('food_items', []),
            total_calories=analysis.get('total_calories', 0),
            protein_g=analysis.get('total_protein_g', 0),
            carbs_g=analysis.get('total_carbs_g', 0),
            fat_g=analysis.get('total_fat_g', 0),
            fiber_g=analysis.get('total_fiber_g', 0),
        )

        db.session.add(meal)
        db.session.commit()

        # 3. Update daily log and capture new alerts
        print("[CELERY] Updating daily log...")
        _, alerts = update_daily_log(user_id)
        print("[CELERY] Task finished successfully!")

        return {
            'status': 'completed',
            'meal_id': meal.id,
            'analysis': analysis,
            'alerts': alerts
        }

    except Exception as e:
        import traceback
        error_msg = f"TASK ERROR (Text): {str(e)}\n{traceback.format_exc()}"
        with open('error_log.txt', 'a') as f:
            f.write(error_msg + "\n")
        return {
            'status': 'failed',
            'error': str(e)
        }
