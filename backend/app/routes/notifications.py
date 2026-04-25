import json
import os
import psycopg2
import select
from flask import Blueprint, Response, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/stream', methods=['GET'])
@jwt_required()
def stream_notifications():
    """SSE endpoint for real-time notifications via Postgres Pub/Sub"""
    user_id = get_jwt_identity()

    def generate_events():
        # Get DB URL from env
        db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/stayfit')
        
        # Connect to Postgres bypassing SQLAlchemy connection pool for LISTEN
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Subscribe to channels
        channels = ["calorie_alerts", "meal_analysis"]
        for channel in channels:
            cursor.execute(f"LISTEN {channel};")
        
        try:
            # Yield initial connection heartbeat to prevent timeouts
            yield "data: {\"type\": \"ping\"}\n\n"
            
            while True:
                # Wait for notifications
                if select.select([conn], [], [], 30) == ([], [], []):
                    # Timeout, send keepalive
                    yield "data: {\"type\": \"ping\"}\n\n"
                    continue
                
                conn.poll()
                while conn.notifies:
                    notify = conn.notifies.pop(0)
                    try:
                        payload = json.loads(notify.payload)
                        # Only forward if message is meant for this user
                        if str(payload.get("user_id")) == str(user_id):
                            # SSE string format: "data: <json>\n\n"
                            yield f"data: {json.dumps(payload)}\n\n"
                    except json.JSONDecodeError:
                        continue
        finally:
            cursor.close()
            conn.close()

    return Response(generate_events(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'})
