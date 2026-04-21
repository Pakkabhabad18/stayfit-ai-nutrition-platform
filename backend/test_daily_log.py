from app import create_app, db
from app.routes.meals import update_daily_log
from app.models import User, Meal

app = create_app('all')
with app.app_context():
    user = User.query.first()
    if user:
        try:
            print("testing daily log...")
            daily_log, alerts = update_daily_log(user.id)
            print("SUCCESS! Alerts:", alerts)
        except Exception as e:
            print("CRASH IN DAILY LOG:", str(e))
    else:
        print("No users found.")
