"""
Cache Service — Redis-backed Cache-Aside helper.

Key design decisions:
- Uses a single global Redis client (lazy-init) to avoid repeated connections.
- All errors are caught and logged so a Redis outage never breaks the app.
- TTL defaults to 1 hour but callers can override per use-case.
"""

import json
import logging
import redis
from app.config import Config
from functools import wraps
from flask import request, jsonify, make_response
from flask_jwt_extended import get_jwt_identity

logger = logging.getLogger(__name__)

_redis_client = None


def _get_client():
    """Return a shared Redis client, initialising it on first call."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis.from_url(
                Config.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            _redis_client.ping()
            logger.info("Redis cache connected successfully.")
        except Exception as exc:
            logger.warning("Redis unavailable — caching disabled. (%s)", exc)
            _redis_client = None
    return _redis_client


def cache_get(key: str):
    """
    Return the cached Python object for *key*, or None on miss / error.
    """
    client = _get_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("cache_get error for key '%s': %s", key, exc)
        return None


def cache_set(key: str, value, ttl: int = 3600):
    """
    Store *value* (JSON-serialisable) under *key* with a TTL in seconds.
    Default TTL = 1 hour.
    """
    client = _get_client()
    if client is None:
        return
    try:
        client.setex(key, ttl, json.dumps(value))
    except Exception as exc:
        logger.warning("cache_set error for key '%s': %s", key, exc)


def cache_delete(key: str):
    """Delete a single cache key."""
    client = _get_client()
    if client is None:
        return
    try:
        client.delete(key)
    except Exception as exc:
        logger.warning("cache_delete error for key '%s': %s", key, exc)


def build_recommendation_cache_key(remaining_calories, goal, meal_type, dietary_preferences):
    """
    Build a deterministic, globally-shared cache key for meal recommendations.

    user_id is intentionally excluded — recommendations depend only on the
    calorie budget, goal, meal type, and dietary preferences, so two different
    users with the same values can safely share the same cached result.

    Cache is keyed by:
      - remaining_calories — bucketed to nearest 50 cal to absorb tiny daily drift
      - goal           — weight-loss / maintenance / muscle-gain
      - meal_type      — breakfast / lunch / dinner / any
      - dietary_preferences — vegan / none / etc.
    """
    # Round remaining calories to the nearest 50 to avoid unnecessary misses
    # caused by tiny differences (e.g. 1497 vs 1503) while still keeping
    # results sensible.  Change the bucket size below if you prefer exact matching.
    BUCKET = 50
    bucketed = round(remaining_calories / BUCKET) * BUCKET

    return (
        f"rec:"
        f"cal{bucketed}:"
        f"goal{goal}:"
        f"type{meal_type}:"
        f"pref{dietary_preferences}"
    ).replace(" ", "_").lower()


def cache_response(timeout=300):
    """
    Decorator to cache a Flask JSON response for a specific user.
    Uses the request path and user ID to formulate the key.
    Only caches on HTTP 200 OK.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_id = get_jwt_identity()
            except Exception:
                user_id = "anonymous"

            if not user_id:
                return f(*args, **kwargs)

            # Generate unique cache key for this user and this route
            cache_key = f"routecache:{user_id}:{request.path}"
            
            cached_data = cache_get(cache_key)
            if cached_data is not None:
                logger.info("Route cache HIT for key: %s", cache_key)
                if isinstance(cached_data, dict):
                    cached_data['cache_hit'] = True
                return jsonify(cached_data), 200

            logger.info("Route cache MISS for key: %s — computing...", cache_key)
            response = f(*args, **kwargs)
            
            # Using make_response to standardise whatever was returned (e.g. tuple)
            resp_obj = make_response(response)
            
            if resp_obj.status_code == 200 and resp_obj.is_json:
                data = resp_obj.get_json()
                cache_set(cache_key, data, ttl=timeout)

            return response
        return decorated_function
    return decorator


def redis_publish(channel: str, message: str):
    """Publish a message to a Redis channel."""
    client = _get_client()
    if client:
        try:
            client.publish(channel, message)
        except Exception as exc:
            logger.warning("redis_publish error on channel '%s': %s", channel, exc)


def get_redis_pubsub():
    """Return a Redis pubsub object."""
    client = _get_client()
    if client:
        try:
            return client.pubsub(ignore_subscribe_messages=True)
        except Exception as exc:
            logger.warning("get_redis_pubsub error: %s", exc)
    return None

def invalidate_user_analytics_cache(user_id):
    """Clear precisely the cached route payloads for a specific user after they log a meal."""
    # Since blueprint is registered with '/api/analytics', request.path looks like this:
    cache_delete(f"routecache:{user_id}:/api/analytics/weekly")
    cache_delete(f"routecache:{user_id}:/api/analytics/progress")
