# ADR 0003: Use Pub/Sub Notification System via Redis

## Status
Accepted

## Context
When a user logs a meal that pushes their daily intake over 80% of their calorie budget, or when an AI analysis completes asynchronously, the system needs to immediately alert the user in real-time. Traditional approaches involve having the frontend incessantly poll the backend database for new records, which wastes network bandwidth and database connections. We need a performant push-notification mechanism. 

To consolidate our messaging infrastructure efficiently alongside our asynchronous task queue and in-memory caching layer, we chose to utilize Redis.

## Decision
We decided to implement a **Publish-Subscribe (Pub/Sub) Pattern** utilizing **Redis** as a centralized, high-performance message broker.

- **Publisher (`run_meals.py`, `tasks.py`):** When actions occur (e.g., a logged meal pushes a user over an 80% daily calorie threshold or an AI analysis completes), the backend services execute a lightweight standard call to `redis_publish(<channel>, <json_payload>)` wrapping `client.publish()`.
- **Message Broker:** The centralized Redis server (`localhost:6379`) receives the payload and broadcasts it instantly across its internal Pub/Sub system.
- **Subscriber (`run_notifications.py` -> Port 5004):** A dedicated streaming microservice mounts an endpoint (`/api/notifications/stream`). It bypasses database connections entirely by calling `get_redis_pubsub().subscribe("calorie_alerts", "meal_analysis")`. It drops into an infinite loop polling `pubsub.get_message(timeout=30.0)`, dispatching heartbeat pings to prevent timeout closures, and yielding formatted Server-Sent Events (`data: <json>\n\n`) directly to the frontend the exact microsecond a payload arrives.

## Consequences
### Positive
- **Database Relief:** Postgres is entirely alleviated from maintaining long-lived idle connections for thousands of listening clients.
- **Microsecond Latency:** Redis Pub/Sub operates exclusively in-memory, handling throughput magnitudes faster than disk-based event triggers.
- **Decoupling:** The backend publishers fire real-time JSON packets securely and forget about them instantly without tying up SQLAlchemy transaction commits.

### Negative
- **Message Durability:** Redis Pub/Sub is inherently "fire-and-forget". If the Notification subscriber or the user's browser SSE stream disconnects exactly as a payload is published, that notification is permanently lost. (For our UI "toaster" alerts, this is an acceptable tradeoff).
