# Architecture Analysis: Microservices vs Monolithic

## Purpose

This analysis compares the implemented StayFit architecture against an alternative monolithic Flask architecture. The goal is to evaluate trade-offs for non-functional requirements such as response time, availability, scalability, maintainability, and deployment complexity.

## Architectures Compared

### Implemented Architecture: Microservices with API Gateway

StayFit currently runs as a set of Flask-based services behind an API Gateway:

| Component | Runner | Port | Responsibility |
| --- | --- | ---: | --- |
| API Gateway | `backend/api_gateway.py` | 5000 | Single frontend entry point; forwards `/api/...` requests to internal services |
| Auth Service | `backend/run_auth.py` | 5001 | Registration, login, Google OAuth, profile management |
| Meals and Recommendations Service | `backend/run_meals.py` | 5002 | Meal upload, AI analysis task dispatch, meal history, recommendations |
| Analytics Service | `backend/run_analytics.py` | 5003 | Daily summary, weekly trends, progress analytics |
| Notifications Service | `backend/run_notifications.py` | 5004 | Server-Sent Events stream for real-time alerts |
| Celery Worker | `backend/run_celery.py` | N/A | Background AI meal analysis |

The frontend always calls `http://localhost:5000/api/...`, so the external API contract stays the same while the gateway routes requests to domain-specific services.

### Alternative Architecture: Monolithic Flask Application

The comparison baseline is the existing single-process Flask application:

| Component | Runner | Port | Responsibility |
| --- | --- | ---: | --- |
| Monolithic Backend | `backend/run.py` | 5000 | Auth, meals, analytics, recommendations, notifications routes in one process |

This alternative is simpler to start and debug, but all backend domains share the same runtime process.

## Non-Functional Requirements Evaluated

| Requirement | Why it matters for StayFit | Measurement |
| --- | --- | --- |
| Response time | The UI should feel responsive when users view dashboards, meal logs, and progress charts. | Average, p50, and p95 latency for selected authenticated API endpoints |
| Availability / fault isolation | AI meal analysis can be heavier and more failure-prone than auth or analytics. One failure should not break the entire app. | Number of unaffected API domains when the Meals service is unavailable |
| Scalability | AI processing and notification streaming have different resource needs from auth and analytics. | Qualitative comparison of independent scaling ability |
| Maintainability | The app has separate concerns: users, meals, analytics, notifications, and AI integration. | Qualitative comparison of module boundaries and change impact |
| Deployment complexity | The prototype should be easy to run and evaluate. | Number of processes and operational steps |

## Response Time Measurement Plan

Use the same database and same API contract for both tests.

### Monolith Mode

```bash
cd backend
python run.py
```

Base URL:

```text
http://localhost:5000
```

### Microservices Mode

```bash
cd backend
python start_microservices.py
```

In a second terminal, start Celery if testing meal analysis completion:

```bash
cd backend
celery -A run_celery.celery worker --loglevel=info --pool=solo
```

Base URL:

```text
http://localhost:5000
```

### Benchmark Command

After logging into the frontend, copy the JWT from browser local storage and run:

```bash
python scripts/benchmark_architecture.py --token "PASTE_JWT_TOKEN_HERE"
```

Run it once with the monolith backend running and once with the microservices cluster running. Label and paste the results into the table below.

### Endpoints Benchmarked

| Endpoint | Reason |
| --- | --- |
| `GET /api/analytics/daily` | Lightweight analytics query used by Dashboard |
| `GET /api/analytics/weekly` | Larger analytics query used by Analytics page |
| `GET /api/meals/today` | Meal log source-of-truth query |
| `GET /api/auth/profile` | Auth/profile domain query |

Real Gemini image upload is intentionally excluded from the primary latency comparison because external AI latency varies based on network and provider behavior. Instead, AI upload is discussed as a reason for asynchronous processing and service separation.

## Response Time Findings



The following results were collected with `scripts/benchmark_architecture.py` using a valid JWT. All endpoints returned HTTP `200`, reflecting successful authenticated endpoint execution.

## Monolithic Results

| Endpoint | Requests | Status counts | Throughput req/s | Avg ms | p50 ms | p95 ms | Min ms | Max ms |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| /api/analytics/daily | 100 | `{"200": 100}` | 205.99 | 4.83 | 4.19 | 5.78 | 3.45 | 33.12 |
| /api/analytics/weekly | 100 | `{"200": 100}` | 113.84 | 8.76 | 8.74 | 9.3 | 7.88 | 10.4 |
| /api/meals/today | 100 | `{"200": 100}` | 186.93 | 5.33 | 5.36 | 5.84 | 4.62 | 6.33 |
| /api/auth/profile | 100 | `{"200": 100}` | 291.54 | 3.41 | 2.88 | 3.85 | 2.39 | 31.4 |

**Total throughput:** 798.3 req/s 
**Average latency:** 5.58 ms

## Microservices Results

| Endpoint | Requests | Status counts | Throughput req/s | Avg ms | p50 ms | p95 ms | Min ms | Max ms |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| /api/analytics/daily | 100 | `{"200": 100}` | 137.48 | 7.25 | 6.95 | 8.48 | 5.9 | 28.72 |
| /api/analytics/weekly | 100 | `{"200": 100}` | 89.03 | 11.21 | 10.83 | 11.82 | 9.52 | 50.32 |
| /api/meals/today | 100 | `{"200": 100}` | 131.71 | 7.57 | 7.17 | 7.74 | 6.62 | 42.07 |
| /api/auth/profile | 100 | `{"200": 100}` | 184.87 | 5.39 | 4.89 | 5.56 | 4.42 | 45.19 |

**Total throughput:** 543.09 req/s
**Average latency:** 7.86 ms

Interpretation: The monolithic architecture shows lower average response times and higher throughput for these endpoints, but the microservices architecture still provides acceptable performance with the added benefits of fault isolation and scalability.

Interpretation: The monolithic architecture shows lower average response times and higher throughput for these endpoints, but the microservices architecture still provides acceptable performance with the added benefits of fault isolation and scalability.

## Fault Isolation / Availability Test
### Microservices Scenario

1. Start the microservices cluster.
2. Stop only the Meals service (`run_meals.py`, port 5002).
3. Test the following requests through the gateway:

| Request | Expected Result | Availability Impact |
| --- | --- | --- |
| `GET /api/meals/today` | `503` from API Gateway | Meals unavailable |
| `GET /api/recommendations/?meal_type=lunch` | `503` from API Gateway | Recommendations unavailable because they share Meals service |
| `GET /api/analytics/daily` | `200` | Analytics still available |
| `GET /api/auth/profile` | `200` | Auth/profile still available |

Result: two domains fail, while auth/profile and analytics remain available. The failure is isolated to the unavailable service.

### Measured Microservices Fault-Isolation Result


The following benchmark was collected with the Meals service on port `5002` stopped. The `503` result confirms the gateway detected the Meals service outage. The `200` results for Analytics and Auth/Profile show that those services were still reachable and fully functional through the gateway.

| Endpoint | Requests | Status counts | Throughput req/s | Avg ms | p50 ms | p95 ms | Min ms | Max ms |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| /api/analytics/daily | 5 | `{"200": 5}` | 74.6 | 13.31 | 8.14 | 29.39 | 7.55 | 34.57 |
| /api/analytics/weekly | 5 | `{"200": 5}` | 39.89 | 25.02 | 15.07 | 56.47 | 10.93 | 65.02 |
| /api/meals/today | 5 | `{"503": 5}` | 363.8 | 2.72 | 2.87 | 3.23 | 2.19 | 3.29 |
| /api/auth/profile | 5 | `{"200": 5}` | 100.54 | 9.91 | 6.63 | 19.83 | 6.36 | 23.04 |

**Total throughput:** 578.83 req/s**  
**Average latency:** 12.74 ms**

**Analysis:**
When the Meals service is down, `/api/meals/today` returns 503 for all requests, while analytics and auth endpoints remain available and return 200. This demonstrates effective fault isolation: the failure of the Meals service does not impact the availability of analytics or auth endpoints. The system maintains partial functionality, confirming the resilience benefits of the microservices architecture.

### Monolith Scenario

1. Start the monolith with `python run.py`.
2. Stop the backend process.
3. Test the same requests.

| Request | Expected Result | Availability Impact |
| --- | --- | --- |
| `GET /api/meals/today` | Connection failure | Meals unavailable |
| `GET /api/recommendations/?meal_type=lunch` | Connection failure | Recommendations unavailable |
| `GET /api/analytics/daily` | Connection failure | Analytics unavailable |
| `GET /api/auth/profile` | Connection failure | Auth/profile unavailable |

Result: all API domains fail because they share one process.

## Quantified Availability Comparison

| Failure Scenario | Architecture | Unavailable Domains | Still Available Domains | Availability Result |
| --- | --- | ---: | ---: | --- |
| Meals process unavailable | Microservices | 2 of 4 | 2 of 4 | Partial service remains available |
| Backend process unavailable | Monolith | 4 of 4 | 0 of 4 | Full backend outage |

Domains counted: Auth/Profile, Meals, Recommendations, Analytics. Notifications are excluded from this count because SSE behavior requires a long-lived stream rather than a simple request-response health check.

## Trade-Off Analysis

| Quality Attribute | Microservices with Gateway | Monolith |
| --- | --- | --- |
| Performance | Slight proxy overhead from gateway routing, but async Celery prevents AI analysis from blocking normal UI requests. | Fewer network hops for normal routes, but one process hosts every backend concern. |
| Availability | Better fault isolation. A Meals service failure does not automatically break Auth or Analytics. | Lower fault isolation. A backend crash removes all API functionality. |
| Scalability | Meals/AI service and Celery workers can be scaled independently from lightweight auth and analytics. | Scaling requires replicating the whole backend even if only AI or analytics needs more resources. |
| Maintainability | Clearer domain boundaries: auth, meals, analytics, notifications. More moving parts to understand. | Easier project structure for small teams, but domains become more coupled as the app grows. |
| Deployment Complexity | Requires gateway, multiple Flask services, Celery, Redis, and database. More operational overhead. | One backend process plus database and worker if async tasks are retained. Easier local startup. |

## Conclusion

For an early prototype, a monolithic Flask application is easier to run, debug, and deploy. However, StayFit has workloads with different failure and scaling characteristics: AI meal analysis is slow and provider-dependent, analytics is query-heavy but predictable, auth is security-sensitive, and notifications require long-lived SSE streams.

The implemented microservices architecture is therefore justified for demonstrating scalability and resilience. The gateway adds some latency, but it preserves a single frontend API contract while allowing independent service failure and future independent scaling. The best practical conclusion is that the monolith is simpler for initial development, while the microservices design better supports StayFit's AI-heavy, real-time, and growth-oriented requirements.
