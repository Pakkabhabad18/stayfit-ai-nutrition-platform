import json
import time
from flask import Blueprint, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.cache_service import get_redis_pubsub

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/stream', methods=['GET'])
@jwt_required()
def stream_notifications():
    """SSE endpoint for real-time notifications via Redis Pub/Sub"""
    user_id = get_jwt_identity()

    def generate_events():
        pubsub = get_redis_pubsub()
        if not pubsub:
            # If Redis is unavailable, stream a heartbeat and return
            yield "data: {\"type\": \"ping\"}\n\n"
            return
            
        try:
            pubsub.subscribe("calorie_alerts", "meal_analysis")
            # Yield initial connection heartbeat to prevent timeouts
            yield "data: {\"type\": \"ping\"}\n\n"
            
            while True:
                # Poll Redis pubsub messages with a timeout simulating Select
                message = pubsub.get_message(timeout=30.0)
                
                if message is None:
                    # Timeout, send keepalive
                    yield "data: {\"type\": \"ping\"}\n\n"
                    continue
                
                # We only want standard published messages
                if message['type'] == 'message':
                    try:
                        payload = json.loads(message['data'])
                        # Only forward if message is meant for this user
                        if str(payload.get("user_id")) == str(user_id):
                            # SSE string format: "data: <json>\n\n"
                            yield f"data: {json.dumps(payload)}\n\n"
                    except json.JSONDecodeError:
                        continue
        finally:
            if pubsub:
                pubsub.close()

    return Response(generate_events(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'})
