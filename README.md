# Cartify — Full-Stack E-Commerce Platform

Cartify is a modern, high-performance, full-stack grocery and essentials e-commerce platform architected for extreme concurrency and horizontal scalability.

---

## 1. Project Overview

Cartify combines a rich, responsive Next.js frontend with an asynchronous Python FastAPI backend, backed by PostgreSQL for transactional ACID persistence, Redis for in-memory caching, rate-limiting, and stampede protection, and PgBouncer for transaction-level connection multiplexing.

The architecture is strictly decoupled: the Next.js website acts solely as an API client, allowing future Android and iOS mobile applications to consume the identical REST API without modifications.

---

## 2. Architecture

```
                    CARTIFY
                       │
             ┌─────────┴─────────┐
             │                   │
        Next.js Website     Future Mobile Apps
        (React 19 / App)      (Android + iOS)
             │                   │
             └─────────┬─────────┘
                       │
                  REST API (/api/v1)
                       │
                 Python FastAPI
                       │
             ┌─────────┴─────────┐
             │                   │
         SQLAlchemy 2.x        Redis 7
         (Async Engine)    (Cache-Aside & Mutex)
             │
         PgBouncer (Transaction Pooling)
             │
     ┌───────┴───────┐
     │               │
 PostgreSQL      PostgreSQL
  (Primary)    (Read Replica)
```

---

## 3. Frontend Setup

### Prerequisites
- **Node.js**: v18.17.0+ or v20+
- **Package Manager**: `npm` (v10+)

### Installation
From the repository root:
```bash
npm install
```

### Environment Configuration
Copy the example environment file:
```powershell
# Windows PowerShell
Copy-Item .env.example .env.local

# Windows Command Prompt (CMD)
copy .env.example .env.local
```

Ensure `.env.local` contains:
```ini
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_USE_MOCK=true
NEXT_PUBLIC_APP_NAME=Cartify
NEXT_PUBLIC_APP_TAGLINE=Fresh Groceries & Essentials in Minutes
```

---

## 4. Backend Setup

### Prerequisites
- **Python**: v3.11, v3.12, or v3.14+
- **Pip**: Latest version

### Virtual Environment Creation & Dependency Installation
Navigate to `backend/`:

#### Windows PowerShell:
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Windows Command Prompt (CMD):
```cmd
cd backend
python -m venv .venv
.\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5. PostgreSQL Setup

Cartify uses PostgreSQL 16 as its relational database.

### Local Docker Option (Recommended)
From `backend/`:
```bash
docker-compose up -d postgres
```
This spins up PostgreSQL on port `5432` with credentials:
- **User**: `cartify`
- **Password**: `cartify_secure_pass`
- **Database**: `cartify_db`
- **URL**: `postgresql+asyncpg://cartify:cartify_secure_pass@localhost:5432/cartify_db`

### Native PostgreSQL Option
If running PostgreSQL natively on Windows:
```sql
CREATE DATABASE cartify_db;
CREATE USER cartify WITH PASSWORD 'cartify_secure_pass';
GRANT ALL PRIVILEGES ON DATABASE cartify_db TO cartify;
```

---

## 6. Redis Setup

Redis 7 powers cache-aside caching, stampede mutex locks, and sliding-window rate limiters.

### Local Docker Option (Recommended)
From `backend/`:
```bash
docker-compose up -d redis
```
This starts Redis on port `6379`.

### Docker Compose (All Services)
To start both PostgreSQL and Redis together:
```bash
docker-compose up -d
```

---

## 7. Environment Variables

### Frontend (`.env.local` in project root)
| Variable | Description | Default |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_BASE_URL` | Base endpoint for the FastAPI REST API | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_USE_MOCK` | Fallback to client-side mock service when live backend is offline | `true` |
| `NEXT_PUBLIC_APP_NAME` | Display name of the application | `Cartify` |

### Backend (`backend/.env`)
| Variable | Description | Default |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Runtime environment (`development`, `production`) | `development` |
| `DEBUG` | Enable debug logging | `true` |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://cartify:cartify_secure_pass@localhost:5432/cartify_db` |
| `DB_POOL_SIZE` | SQLAlchemy connection pool size | `20` |
| `DB_MAX_OVERFLOW` | Max overflow connections | `10` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:3000,http://127.0.0.1:3000` |
| `SECRET_KEY` | JWT signing secret | Change in production |
| `REQUEST_TIMEOUT_SECONDS` | Server-side request timeout | `10.0` |

---

## 8. Alembic Migration Commands

All database schema modifications are managed version-by-version using Alembic.

From `backend/`:

#### Windows PowerShell:
```powershell
# Run pending migrations up to head
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head

# Rollback the last migration
.\.venv\Scripts\python.exe -m alembic -c alembic.ini downgrade -1

# View migration history
.\.venv\Scripts\python.exe -m alembic -c alembic.ini history
```

#### Windows Command Prompt (CMD):
```cmd
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
.\.venv\Scripts\python.exe -m alembic -c alembic.ini downgrade -1
.\.venv\Scripts\python.exe -m alembic -c alembic.ini history
```

---

## 9. Running Frontend

From the repository root:
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser to view the Cartify homepage.

To create an optimized production build:
```bash
npm run build
npm run start
```

---

## 10. Running Backend

From the repository root or `backend/`:

#### Windows PowerShell:
```powershell
# From root directory:
& "backend/.venv/Scripts/python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --app-dir backend

# Or from backend directory:
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### Windows Command Prompt (CMD):
```cmd
cd backend
.\.venv\Scripts\activate.bat
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## 11. API Documentation

Interactive API documentation is generated automatically by FastAPI:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

Core Foundation Endpoints:
- `GET /`: Service metadata and discovery links
- `GET /api/v1/health`: Liveness probe (200 OK)
- `GET /api/v1/ready`: Infrastructure readiness probe (verifies PostgreSQL and Redis)

---

## 12. Testing

### Running Backend Tests
From the repository root:

#### Windows PowerShell:
```powershell
& "backend/.venv/Scripts/python.exe" -m pytest backend/tests -v
```

#### Windows Command Prompt (CMD):
```cmd
backend\.venv\Scripts\python.exe -m pytest backend/tests -v
```

### Running Frontend-to-Backend Connection Test
With the backend running, execute:
```bash
node scripts/test-api-connection.mjs
```
This tests live network communication from the frontend client to `GET /api/v1/health`.

### Running Frontend Type & Build Verification
```bash
npm run typecheck
npm run build
```

---

## 13. Git Workflow & Safety

The repository is protected against committing environment variables, build artifacts, or credentials.

- **Protected files**: `.env`, `.env.local`, `.venv/`, `node_modules/`, `.next/`, `__pycache__/`
- Always verify git status before committing:
  ```bash
  git status
  ```
- To test changes cleanly before pushing:
  ```bash
  npm run build
  & "backend/.venv/Scripts/python.exe" -m pytest backend/tests -v
  ```
