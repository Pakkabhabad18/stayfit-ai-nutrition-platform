from app import create_app, db
from sqlalchemy import text

app = create_app('all')
with app.app_context():
    try:
        print("Testing notify command...")
        db.session.execute(text("NOTIFY calorie_alerts, '{\"user_id\": \"test\", \"message\": \"test\"}'"))
        db.session.commit()
        print("NOTIFY success.")
    except Exception as e:
        print("NOTIFY CRAASH:", str(e))
