# Database Setup

## Prerequisites
- PostgreSQL 14+ installed and running

## Setup Steps

1. **Create the database:**
```bash
psql -U postgres
CREATE DATABASE stayfit;
\q
```

2. **Run the schema:**
```bash
psql -U postgres -d stayfit -f init.sql
```

3. **Update the backend `.env` file** with your database credentials:
```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/stayfit
```

## Tables
- `users` - User accounts and profile data
- `meals` - Individual meal entries with AI-analyzed food data
- `daily_logs` - Aggregated daily calorie logs
