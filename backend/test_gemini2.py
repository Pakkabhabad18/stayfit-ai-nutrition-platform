from app import create_app, db
from app.routes.meals import upload_meal
from flask import current_app
from app.models import User
import json

app = create_app('all')
with app.app_context():
    # Mocking the request context
    with app.test_request_context(
        '/api/meals/upload',
        method='POST',
        data={'meal_type': 'snack'},
    ):
        user = User.query.first()
        from flask_jwt_extended import create_access_token
        # Wait, easier to just call the gemini service directly to see if gemini is failing!
        from app.services.gemini_service import analyze_food_image
        try:
            print("Pinging Gemini...")
            with open("frontend/public/vite.svg", "rb") as f:
                 data = f.read()
            res = analyze_food_image(data, 'image/svg+xml')
            print("Gemini result:", res)
        except Exception as e:
            print("Gemini CRAASH:", str(e))
