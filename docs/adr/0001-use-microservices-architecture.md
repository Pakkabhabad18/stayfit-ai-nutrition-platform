# ADR 0001: Use Microservices Architecture via API Gateway

## Status
Accepted

## Context
As the project grows, especially with the integration of heavy AI processing for meal analysis alongside standard CRUD operations and real-time analytics, running everything in a single process introduces risks. For example, a heavy load on the Gemini AI image parsing could crash or stall the entire application, preventing users from accessing their analytics or authenticating.

## Decision
We elected to partition the application across disparate network boundaries using a Microservices Architecture, fronted by an API Gateway.

We separated the application into the following domains, operating as independent Flask processes communicating via HTTP and acting as a modular monolith sharing a common source folder for database models:
- **API Gateway (Port 5000):** Acts as the single entry point. It receives frontend requests, strips/validates CORS headers globally, and reverse-proxies payloads downstream, handling special cases like Server-Sent Events dynamically.
- **Auth Service (Port 5001):** Manages user session states and authentication (`/api/auth`).
- **Meals & AI Service (Port 5002):** Connects to Gemini to analyze images (`/api/meals`), handling the heavy computational load. It also uses Redis for cache-aside meal recommendations.
- **Analytics Service (Port 5003):** Handles purely numeric reporting queries (`/api/analytics`).
- **Notifications Service (Port 5004):** A long-lived Server-Sent Events (SSE) streaming service (`/api/notifications`).
- **Async Workers (Celery & Redis):** Background processing workers executing out-of-band tasks without blocking the HTTP microservices.

We utilized the "Modular Monolith Deployment" strategy to achieve this without redundantly copying DB schema files everywhere. All microservices share the same foundational `app` package but are executed as independent processes (`run_X.py`) focusing on specific routing domains.

## Consequences
### Positive
- **Fault-Isolation:** If the Meals service crashes due to heavy AI image processing loads, users can still view their Analytics charts natively without interruption.
- **Independent Scaling:** The heavy Meals routing can be assigned more RAM/CPU resources autonomously without wasting resources on the lightweight Analytics service.
- **Separation of Concerns:** Clear boundaries between different operational domains.

### Negative
- **Operational Complexity:** Running and managing multiple processes (orchestrated via `start_microservices.py` and Celery) is more complex than a single monolithic app.
- **Port Management:** We must actively manage multiple internal ports and reverse-proxy mapping.
