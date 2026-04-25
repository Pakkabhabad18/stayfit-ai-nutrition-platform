# StayFit - AI-Powered Calorie Tracker

A full-stack application that uses AI (Gemini 2.5 Flash) to analyze food photos and track daily calorie intake.

## Project Structure

```
project3/
├── backend/          # Python Flask API
├── frontend/         # React + Vite Frontend
└── database/         # PostgreSQL Schema
```

## ⚡ Quick Setup

### 1. Database (PostgreSQL)
```bash
# Create database
psql -U postgres -c "CREATE DATABASE stayfit;"
psql -c "CREATE DATABASE stayfit;" #(for Mac users)

# Run schema
psql -U postgres -d stayfit -f database/init.sql
psql -d stayfit -f database/init.sql #(for Mac users)
```

### 2. Backend (Python)
```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run microservices cluster (API Gateway + 3 Services)
python start_microservices.py

# Install 
brew install redis #Mac Users
brew services start redis #Mac Users

# second terminal
cd backend 

source venv/bin/activate

celery -A run_celery.celery worker --loglevel=info --pool=solo

# third terminal (to start frontend)
cd frontend
npm run dev
```
The API Gateway runs on **http://localhost:5000**, routing to internal ports (5001-5003).

### 3. Frontend (React)
```bash
cd frontend

# Install dependencies (already done)
npm install

# Run dev server
npm run dev
```
The app runs on **http://localhost:5173**

## Environment Variables

Create `backend/.env` from `.env.example`:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `GEMINI_API_KEY` | Google Gemini API key ([Get one here](https://aistudio.google.com/apikey)) |
| `SECRET_KEY` | Flask secret key |
| `JWT_SECRET_KEY` | JWT signing key |
| `GOOGLE_CLIENT_ID`| Google OAuth2 Client ID (Backend) |
| `SENTRY_DSN` | Sentry DSN |

*Also create a `frontend/.env` file containing:*
| Variable | Description |
|----------|-------------|
| `VITE_GOOGLE_CLIENT_ID`| Google OAuth2 Client ID (Frontend) |
| `VITE_SENTRY_DSN` | Sentry DSN |

## 📐 Architectural Patterns Implemented

### 1. Federated Identity Pattern (Google Auth)
**How it's implemented:** We integrated **Google OAuth2** via `@react-oauth/google` on the frontend and `google-auth` on the backend. When a user logs in, Google provides an encrypted JWT `id_token` credential directly to the React app. The React app forwards this token to our backend (`/api/auth/google`), which cryptographically verifies it securely via Google's libraries without passwords.
**Why:**
- **Zero-Trust Security:** We offload password security, hashing logic, and credential management to an enterprise provider (Google).
- **Reduced Friction:** Users can jump straight into the health tracking funnel without filling out registration forms, maximizing sign-up conversion.

### 2. Microservices Architecture (via API Gateway)
**How it's implemented:** The monolithic Flask codebase was partitioned across disparate network boundaries. 
- **API Gateway (`api_gateway.py` -> Port 5000):** Acts as the single entry point. It receives frontend requests, strips/validates CORS headers globally, and reverse-proxies payloads downstream.
- **Service Domain 1 (Auth -> Port 5001):** Manages user states.
- **Service Domain 2 (Meals & AI -> Port 5002):** Connects to Gemini to analyze images heavily.
- **Service Domain 3 (Analytics -> Port 5003):** Does purely numeric reporting queries.
*We utilized the "Modular Monolith Deployment" strategy to achieve this without redundantly copying DB schema files everywhere.*
**Why:**
- **Fault-Isolation:** If the Gemini AI image parsing crashes the Meals service (Port 5002) due to a heavy load, users can still view their Analytics charts (Port 5003) uninterrupted natively.
- **Independent Scaling:** In the future, the heavy AI-computation Meal routing could be given more RAM/CPU resources autonomously without wasting resources on the lightweight Analytics service.

### 3. Pub/Sub (Publish-Subscribe) Pattern
**How it's implemented:** We utilize **Redis Pub/Sub** connected across our microservice cluster!
- **Publisher (`run_meals.py`, `tasks.py`):** When a calorie threshold is hit or an AI async task finishes parsing a meal, the worker services fire a raw `client.publish('channel', payload)` command.
- **Message Broker:** The internal Redis instance receives the JSON strings and broadcasts them instantly across internal memory channels dynamically.
- **Subscriber (`run_notifications.py` -> Port 5004):** A dedicated streaming microservice continuously polls a direct internal Redis subscription (`pubsub.get_message()`). Every time an alert hits the memory stack, it pushes it out through an open TCP connection to the React Frontend utilizing a real-time **Server-Sent Events (SSE)** stream.
**Why:**
- **Decoupling:** The Meals Service doesn't need to know anything about WebSockets, UI push notifications, or user sessions. It securely transmits the alert payload over the network and immediately completes the worker task natively.
- **Real-Time Push:** Users on the app get beautiful instant toaster popups globally without the UI incessantly polling the server databases every few seconds checking for new records.

### 4. Cache-Aside Pattern
**How it's implemented:** We embedded an in-memory **Redis Caching Layer**. 
- Using a bespoke `@cache_response` Flask decorator, heavy DB-aggregation API endpoints like `/api/analytics/weekly` are intercepted and frozen into Redis memory. 
- For expensive AI computations, we utilize *Semantic Caching* keys based globally on physical profile constraints (calorie buckets, goals) to prevent redundant identical Gemini calls natively.
- An automatic cache-invalidation buster systematically purges old data the instant a user completes logging a new meal.
**Why:**
- **Drastically Lowered Latency:** What previously took 3.5 seconds inside Gemini flash queries now pulls in under ~5ms.
- **Cost Reduction:** Protects the cloud budget from spamming unnecessary identical LLM prompting externally and vastly spares the PostgreSQL database from executing repetitive complex `SUM()` aggregate functions.

## ✨ Features

1. **User Authentication** - Email/password with JWT tokens
2. **Profile Setup** - Age, gender, weight, height, activity level, goal → auto-calculated daily calorie budget
3. **AI Food Logging** - Upload a meal photo → Gemini 2.5 Flash identifies food items and estimates calories
4. **Calorie Tracking** - Real-time daily tracking with remaining budget display
5. **Smart Notifications** - Alerts when approaching or exceeding calorie limits
6. **AI Meal Recommendations** - Personalized meal suggestions based on remaining budget
7. **Health Analytics Dashboard** - Weekly trends, macro breakdowns, 30-day progress charts

## 🛠️ Tech Stack

- **Frontend**: React 18, Vite, Chart.js, React Router, Lucide Icons
- **Backend**: Python Flask, Flask-JWT-Extended, SQLAlchemy
- **Database**: PostgreSQL
- **AI**: Google Gemini 2.5 Flash API
