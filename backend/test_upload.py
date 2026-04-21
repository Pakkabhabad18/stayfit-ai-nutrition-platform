import os
import io
from app import create_app, db
from app.models import User, Meal
import requests

app = create_app('all')
with app.app_context():
    # Attempt to upload using a local test client
    client = app.test_client()
    user = User.query.first()
    if user:
        from flask_jwt_extended import create_access_token
        access_token = create_access_token(identity=user.id)
        
        # Open dummy image
        with open("../frontend/public/vite.svg", "rb") as f:
            data = f.read()

        print("Testing upload_meal directly using test_client...")
        response = client.post(
            '/api/meals/upload',
            headers={'Authorization': f'Bearer {access_token}'},
            data={
                'meal_type': 'snack',
                'image': (io.BytesIO(data), 'vite.svg')
            },
            content_type='multipart/form-data'
        )
        print("Status:", response.status_code)
        print("Data:", response.get_json())
    else:
        print("No users found")
