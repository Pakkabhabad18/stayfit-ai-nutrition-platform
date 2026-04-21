from app import db
from datetime import datetime, date
import uuid


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    weight_kg = db.Column(db.Float)
    height_cm = db.Column(db.Float)
    activity_level = db.Column(db.String(30), default='moderate')
    goal = db.Column(db.String(20), default='maintain')
    daily_calorie_budget = db.Column(db.Integer, default=2000)
    profile_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meals = db.relationship('Meal', backref='user', lazy=True, cascade='all, delete-orphan')
    daily_logs = db.relationship('DailyLog', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'weight_kg': self.weight_kg,
            'height_cm': self.height_cm,
            'activity_level': self.activity_level,
            'goal': self.goal,
            'daily_calorie_budget': self.daily_calorie_budget,
            'profile_completed': self.profile_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Meal(db.Model):
    __tablename__ = 'meals'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)
    image_url = db.Column(db.String(500))
    food_items = db.Column(db.JSON, default=list)
    total_calories = db.Column(db.Integer, default=0)
    protein_g = db.Column(db.Float, default=0)
    carbs_g = db.Column(db.Float, default=0)
    fat_g = db.Column(db.Float, default=0)
    fiber_g = db.Column(db.Float, default=0)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'meal_type': self.meal_type,
            'image_url': self.image_url,
            'food_items': self.food_items,
            'total_calories': self.total_calories,
            'protein_g': self.protein_g,
            'carbs_g': self.carbs_g,
            'fat_g': self.fat_g,
            'fiber_g': self.fiber_g,
            'logged_at': self.logged_at.isoformat() if self.logged_at else None,
        }


class DailyLog(db.Model):
    __tablename__ = 'daily_logs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    log_date = db.Column(db.Date, nullable=False, default=date.today)
    total_calories = db.Column(db.Integer, default=0)
    total_protein_g = db.Column(db.Float, default=0)
    total_carbs_g = db.Column(db.Float, default=0)
    total_fat_g = db.Column(db.Float, default=0)
    budget = db.Column(db.Integer, default=2000)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'log_date', name='uq_user_date'),)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'log_date': self.log_date.isoformat() if self.log_date else None,
            'total_calories': self.total_calories,
            'total_protein_g': self.total_protein_g,
            'total_carbs_g': self.total_carbs_g,
            'total_fat_g': self.total_fat_g,
            'budget': self.budget,
        }
