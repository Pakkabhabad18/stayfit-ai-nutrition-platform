import os
import io
import json
import uuid
from PIL import Image
from celery import shared_task
from flask import current_app
from app import db
from app.models import Meal, User
from app.repositories.meal_repository import MealRepository
from app.services.gemini_service import analyze_food_image, analyze_food_text
from app.services.log_service import update_daily_log
import logging

logger = logging.getLogger(__name__)

@shared_task(ignore_result=False)
def process_meal_analysis(user_id, meal_type, filename):
    """
    Background task to analyze food image, save to DB, and update daily log.
    """
    logger.info("Starting analysis", extra={'user_id': user_id, 'meal_filename': filename})
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    try:
        # 1. Read and resize image for Gemini analysis
        logger.debug("Reading image", extra={'filepath': filepath})
        with open(filepath, 'rb') as f:
            img = Image.open(f)
            img.thumbnail((512, 512))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG', quality=85)
            img_bytes.seek(0)
            image_data = img_bytes.read()

        mime_type = 'image/jpeg'

        # 2. Analyze with Gemini
        logger.info("Calling AI API")
        analysis = analyze_food_image(image_data, mime_type)
        provider = analysis.get('provider', 'AI')
        logger.info("AI analysis complete", extra={'provider': provider})

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

        MealRepository.create(meal)

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
        logger.error("TASK ERROR", exc_info=True, extra={'user_id': user_id, 'meal_filename': filename})
        return {
            'status': 'failed',
            'error': str(e)
        }

@shared_task(ignore_result=False)
def process_text_analysis(user_id, meal_type, text_description):
    """
    Background task to analyze food text description, save to DB, and update daily log.
    """
    logger.info("Starting text analysis", extra={'user_id': user_id})
    
    try:
        # 1. Analyze with Gemini
        logger.info("Calling AI API for text")
        analysis = analyze_food_text(text_description)
        provider = analysis.get('provider', 'AI')
        logger.info("AI text analysis complete", extra={'provider': provider})

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

        MealRepository.create(meal)

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
        logger.error("TASK ERROR (Text)", exc_info=True, extra={'user_id': user_id})
        return {
            'status': 'failed',
            'error': str(e)
        }
