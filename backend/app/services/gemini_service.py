import google.generativeai as genai
from groq import Groq
from app.config import Config
import json
import base64
import re
from tenacity import retry, stop_after_attempt, wait_exponential
from pycircuitbreaker import circuit
from abc import ABC, abstractmethod

def configure_gemini():
    """Configure the Gemini API client."""
    genai.configure(api_key=Config.GEMINI_API_KEY)

def get_groq_client():
    """Get the Groq API client."""
    return Groq(api_key=Config.GROQ_API_KEY)

def _clean_json_response(response_text):
    """Remove markdown formatting from JSON response."""
    if response_text.startswith('```'):
        response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
        response_text = re.sub(r'\n?```$', '', response_text)
    return response_text

@circuit
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
def _call_gemini_vision(prompt, image_part):
    configure_gemini()
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content([prompt, image_part])
    return response.text.strip()

@circuit
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
def _call_gemini_text(prompt):
    configure_gemini()
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    return response.text.strip()

def _call_groq_vision(prompt, image_data, mime_type):
    client = get_groq_client()
    base64_image = base64.b64encode(image_data).decode('utf-8')
    data_url = f"data:{mime_type};base64,{base64_image}"
    
    response = client.chat.completions.create(
        # model="llama-3.2-11b-vision-preview",
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }
        ],
        temperature=0.1,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()

def _call_groq_text(prompt):
    client = get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()
class AIProviderStrategy(ABC):
    @property
    @abstractmethod
    def name(self):
        pass

    def analyze_vision(self, prompt, image_data, mime_type):
        raise NotImplementedError

    def analyze_text(self, prompt):
        raise NotImplementedError

class GeminiStrategy(AIProviderStrategy):
    @property
    def name(self):
        return 'Gemini 2.5 Flash'

    def analyze_vision(self, prompt, image_data, mime_type):
        image_part = {'mime_type': mime_type, 'data': image_data}
        return _call_gemini_vision(prompt, image_part)

    def analyze_text(self, prompt):
        return _call_gemini_text(prompt)

class GroqStrategy(AIProviderStrategy):
    @property
    def name(self):
        return 'Groq (Llama)'

    def analyze_vision(self, prompt, image_data, mime_type):
        return _call_groq_vision(prompt, image_data, mime_type)

    def analyze_text(self, prompt):
        return _call_groq_text(prompt)

class ProviderChain:
    def __init__(self, strategies):
        self.strategies = strategies

    def execute_vision(self, prompt, image_data, mime_type, default_fallback):
        for strategy in self.strategies:
            try:
                response_text = strategy.analyze_vision(prompt, image_data, mime_type)
                result = json.loads(_clean_json_response(response_text))
                result['provider'] = strategy.name
                return result
            except Exception as e:
                print(f"{strategy.name} vision analysis failed: {e}. Moving to next provider...")
                continue
        
        print("All providers failed. Using default fallback.")
        result = default_fallback()
        result['provider'] = 'Default Fallback'
        return result

    def execute_text(self, prompt, default_fallback):
        for strategy in self.strategies:
            try:
                response_text = strategy.analyze_text(prompt)
                result = json.loads(_clean_json_response(response_text))
                result['provider'] = strategy.name
                return result
            except Exception as e:
                print(f"{strategy.name} text analysis failed: {e}. Moving to next provider...")
                continue
        
        print("All providers failed. Using default fallback.")
        result = default_fallback()
        result['provider'] = 'Default Fallback'
        return result

def get_default_food_analysis():
    return {
        'food_items': [{'name': 'Unidentified food', 'portion': 'Unknown', 'calories': 300, 'protein_g': 10, 'carbs_g': 30, 'fat_g': 10}],
        'total_calories': 300,
        'total_protein_g': 10.0,
        'total_carbs_g': 30.0,
        'total_fat_g': 10.0,
        'total_fiber_g': 2.0
    }

def analyze_food_image(image_data, mime_type='image/jpeg'):
    """
    Send a food image to Gemini and get food identification + calorie estimation.
    Falls back to Groq on failure.
    """
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

    chain = ProviderChain([GeminiStrategy(), GroqStrategy()])
    return chain.execute_vision(prompt, image_data, mime_type, get_default_food_analysis)

def analyze_food_text(text_description):
    """
    Send a text description of a meal to Gemini and get food identification + calorie estimation.
    Falls back to Groq on failure.
    """
    prompt = f"""Analyze the following text description of a meal and identify all food items.
Text description: "{text_description}"

For each food item, estimate:
- Name of the food
- Approximate portion size
- Estimated calories
- Protein (grams)
- Carbs (grams)
- Fat (grams)

Return the response as a valid JSON object with this exact structure:
{{
    "food_items": [
        {{
            "name": "food name",
            "portion": "portion description",
            "calories": 250,
            "protein_g": 10.0,
            "carbs_g": 30.0,
            "fat_g": 8.0
        }}
    ],
    "total_calories": 500,
    "total_protein_g": 20.0,
    "total_carbs_g": 60.0,
    "total_fat_g": 15.0,
    "total_fiber_g": 5.0
}}

Be as accurate as possible with calorie estimations based on typical serving sizes for the described food.
Return ONLY the JSON object, no additional text or markdown formatting."""

    chain = ProviderChain([GeminiStrategy(), GroqStrategy()])
    return chain.execute_text(prompt, get_default_food_analysis)

def get_meal_recommendations(remaining_calories, goal, meal_type='any', dietary_preferences='none'):
    """
    Get meal recommendations from Gemini based on remaining calorie allowance.
    Falls back to Groq on failure.
    """
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

    def default_recommendations():
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

    chain = ProviderChain([GeminiStrategy(), GroqStrategy()])
    return chain.execute_text(prompt, default_recommendations)
