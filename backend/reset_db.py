from app import create_app, db

app = create_app()

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    print("Recreating all tables...")
    db.create_all()
    print("Database has been successfully reset and is now empty!")
