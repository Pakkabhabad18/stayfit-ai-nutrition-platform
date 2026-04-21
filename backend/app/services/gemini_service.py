import google.generativeai as genai
from app.config import Config
import json
import base64
import re


def configure_gemini():
    """Configure the Gemini API client."""
    genai.configure(api_key=Config.GEMINI_API_KEY)


def analyze_food_image(image_data, mime_type='image/jpeg'):
    """
    Send a food image to Gemini 2.5 Flash and get food identification + calorie estimation.
    Returns a dict with food_items, total_calories, protein_g, carbs_g, fat_g, fiber_g.
    """
    configure_gemini()
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = """Analyze this food image and identify all food items visible. 
For each food item, estimate:
- Name of the food
- Approximate portion size
- Estimated calories
- Protein (grams)
- Carbs (grams)
- Fat (grams)

Return the response as a valid JSON object with this exact structure:
{
    "food_items": [
        {
            "name": "food name",
            "portion": "portion description",
            "calories": 250,
            "protein_g": 10.0,
            "carbs_g": 30.0,
            "fat_g": 8.0
        }
    ],
    "total_calories": 500,
    "total_protein_g": 20.0,
    "total_carbs_g": 60.0,
    "total_fat_g": 15.0,
    "total_fiber_g": 5.0
}

Be as accurate as possible with calorie estimations based on typical serving sizes visible in the image.
Return ONLY the JSON object, no additional text or markdown formatting."""

    image_part = {
        'mime_type': mime_type,
        'data': image_data
    }

    try:
        response = model.generate_content([prompt, image_part])
        response_text = response.text.strip()

        # Clean up response - remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)

        result = json.loads(response_text)
        return result
    except json.JSONDecodeError:
        return {
            'food_items': [{'name': 'Unidentified food', 'portion': 'Unknown', 'calories': 300, 'protein_g': 10, 'carbs_g': 30, 'fat_g': 10}],
            'total_calories': 300,
            'total_protein_g': 10.0,
            'total_carbs_g': 30.0,
            'total_fat_g': 10.0,
            'total_fiber_g': 2.0
        }
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")


def get_meal_recommendations(remaining_calories, goal, meal_type='any', dietary_preferences='none'):
    """
    Get meal recommendations from Gemini based on remaining calorie allowance.
    """
    configure_gemini()
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""Based on the following constraints, suggest 3 meal options:

- Remaining calorie budget for today: {remaining_calories} calories
- User's dietary goal: {goal}
- Meal type: {meal_type}
- Dietary preferences/restrictions: {dietary_preferences}

For each meal suggestion, provide:
- Meal name
- Brief description
- Estimated calories
- Key nutritional highlights
- Simple preparation instructions (2-3 steps)

Return the response as a valid JSON object:
{{
    "recommendations": [
        {{
            "name": "Meal Name",
            "description": "Brief description",
            "calories": 400,
            "protein_g": 25.0,
            "carbs_g": 45.0,
            "fat_g": 12.0,
            "highlights": ["High protein", "Low fat"],
            "preparation": ["Step 1", "Step 2", "Step 3"]
        }}
    ]
}}

Ensure all suggested meals fit within the remaining calorie budget.
Return ONLY the JSON object, no additional text or markdown formatting."""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        if response_text.startswith('```'):
            response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)

        return json.loads(response_text)
    except Exception as e:
        return {
            'recommendations': [
                {
                    'name': 'Grilled Chicken Salad',
                    'description': 'Light and healthy grilled chicken with mixed greens',
                    'calories': min(400, remaining_calories),
                    'protein_g': 30.0,
                    'carbs_g': 15.0,
                    'fat_g': 12.0,
                    'highlights': ['High protein', 'Low carb'],
                    'preparation': ['Grill chicken breast', 'Toss with mixed greens', 'Add light dressing']
                }
            ]
        }
