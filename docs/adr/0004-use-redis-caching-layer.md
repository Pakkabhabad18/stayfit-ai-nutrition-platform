# ADR 0004: Use Redis Caching Layer (Cache-Aside Pattern)

## Status
Accepted

## Context
As the application scales, expensive read-heavy operations emerged as system bottlenecks:
1. **AI Recommendations:** Generating personalized meal suggestions dynamically via the Gemini API introduces high latency (3-10 seconds per request) and consumes billable external API tokens, even when multiple users share practically identical dietary constraints.
2. **Aggregated Analytics:** Routes such as `/weekly` and `/progress` perform heavy iterative database queries summing multiple days of logs containing various macro and calorie data. Under load, constantly recalculating these aggregations on every single page navigation needlessly strains the PostgreSQL database and slows down the frontend rendering.

## Decision
We elected to introduce an in-memory **Redis Caching Layer** adopting the **Cache-Aside** architectural pattern. 

We deployed two distinct caching strategies:
1. **Global Semantic Caching (Recommendations):**
   Instead of caching by purely isolated `user_id`, we cache generation keys based on semantically aligned profile attributes (`remaining_calories` bucketed to nearest 50, `goal`, `meal_type`, and `dietary_preferences`). This allows identical constraints from totally different users to safely share the same cached AI response, heavily mitigating external token usage.
2. **User-Scoped Route Caching (Analytics):**
   We implemented a reusable custom `@cache_response(timeout=300)` Flask decorator structurally attached to expensive reporting routes. This parses unique permutations of `routecache:{user_id}:{request.path}`, dynamically intercepting view payloads, freezing the tuples into Redis via `make_response`, and yielding lightning-fast (1-3ms) JSON structures natively back to the endpoints on subsequent page reloads.

Furthermore, the `cache_service.py` is written to defensively fail open: if the Redis server goes offline unexpectedly, the application seamlessly logs a warning and falls back directly to the AI/Database computations without throwing 500 internal errors.

## Consequences
### Positive
- **Drastically Reduced Latency:** Complex aggregations and AI responses now load in near real-time (usually < 5ms).
- **Reduced Compute Cost/Load:** Spares the PostgreSQL DB from repetitive sequential scans and protects our external AI API billing thresholds.
- **High Resiliency:** The graceful degradation fallback pattern ensures that a Redis disconnection does not halt system transactions.

### Negative
- **Stale Data Risks:** Users accessing analytics might view slightly older progression stats within the short lifespan (5-minute TTL) window before the cache expires after logging a quick meal.
- **Operational Infrastructure:** Adds a dependency (Redis) that must be strictly monitored inside WSL environments or production deployments alongside the main database.
