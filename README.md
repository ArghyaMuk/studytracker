# StudyPilot — AI-Powered Study & Exam Readiness Platform

A secure, event-driven microservices platform for college students that transforms passive study logging into active, personalized learning guidance for semester exams, lab vivas, and placement/competitive-exam prep.

## Features

### For Students
- **Take Quizzes** — Attempt MCQ and Viva quizzes set by admin, get instant scores and feedback
- **Study Materials** — Access YouTube videos (embedded), PDF links, notes shared by admin
- **Spaced Repetition** — Smart revision scheduling with interval ladder (1→3→7→14→30→60→90 days)
- **Exam Readiness Scoring** — Track quiz performance per subject with progress bars
- **Dashboard** — Overview of sessions, due revisions, and readiness stats
- **Password Reset** — Forgot password flow to reset credentials without needing admin help

### For Admin
- **Course Management** — Add/delete programs, subjects, and units for any degree
- **AI Quiz Generation** — Generate quizzes using Gemini AI (with OpenRouter/Llama 3.1 fallback)
- **Manual Quiz Creation** — Write questions manually with MCQ options and correct answers
- **Study Materials Upload** — Add YouTube video URLs, PDF links, notes for students
- **Student Management** — View all registered students, signup stats
- **Role Management** — Promote/demote users between admin and student roles from the students page
- **Platform Health** — Monitor all microservices status, quiz count, program count

## Security

| Feature | Implementation |
|---------|---------------|
| Authentication | JWT (access 15min + refresh 7d) with role claim |
| Authorization | X-User-Id + X-User-Role headers enforced on every service |
| IDOR Protection | Services verify authenticated user owns the resource |
| Admin Enforcement | Server-side role check on all admin endpoints (not just frontend) |
| Rate Limiting | Redis-backed sliding window (100 req/min per user) |
| Password Security | bcrypt hashing, strong password policy |
| Admin Bootstrap | Auto-seeded from ADMIN_EMAIL/ADMIN_PASSWORD env vars on first startup |
| Admin Email | Configurable via .env (removed from source code) |
| CORS | Restricted to frontend origin |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Flask Frontend (:3000)                      │
│       Jinja2 Templates │ Server-side rendering │ CSS         │
└──────────────────────────┬──────────────────────────────────┘
                           │ (Authorization: Bearer JWT)
┌──────────────────────────▼──────────────────────────────────┐
│                    API Gateway (:8000)                        │
│     JWT Verify → X-User-Id/X-User-Role │ CORS │ Redis Rate  │
└──┬────────┬────────┬────────┬────────┬────────┬────────┬────┘
   │        │        │        │        │        │        │
┌──▼──┐ ┌──▼───┐ ┌──▼──┐ ┌──▼──┐ ┌──▼───┐ ┌──▼────┐ ┌─▼─────┐
│User │ │Curri-│ │Sess-│ │Quiz │ │Repe- │ │Ready- │ │Notif- │
│Svc  │ │culum │ │ions │ │Svc  │ │tition│ │ness   │ │ication│
│:8001│ │:8002 │ │:8003│ │:8005│ │:8004 │ │:8006  │ │:8007  │
└──┬──┘ └──┬───┘ └──┬──┘ └──┬──┘ └──┬───┘ └──┬────┘ └──┬────┘
   │        │        │       │        │        │         │
   │        │        │       │   ┌────┴────────┴─────────┘
   │        │        │       │   │  RabbitMQ Event Bus
   │        │        │       │   │  (async consumers on startup)
   │        │        └───────┼───┼──► session.logged
   │        │                └───┼──► quiz.completed
   │        │                    └──► readiness.updated
   │        │
┌──▼────────▼────────────────────────────────────────────────┐
│                  MySQL 8 (per-service schema)                │
│ users│curriculum│sessions│quizzes│repetition│readiness│notifs│
└────────────────────────────────────────────────────────────┘
┌───────────────────────┐
│     Redis (:6379)     │
│ Rate Limiting (sorted │
│ set sliding window)   │
└───────────────────────┘
```

## Event-Driven Flow

```
Student logs session ──► Session Service publishes session.logged
                              │
                              ├──► Repetition Service (updates review interval)
                              └──► Readiness Service (recomputes score)
                                        │
                                        └──► publishes readiness.updated
                                                  │
                                                  └──► Notification Service (alerts on drop)

Student submits quiz ──► Quiz Service publishes quiz.completed
                              │
                              ├──► Repetition Service (adjusts schedule by score)
                              └──► Readiness Service (recomputes score)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Flask 3.1, Jinja2, Vanilla HTML/CSS/JS |
| Backend | Python 3.12, FastAPI (async) |
| Database | MySQL 8 (database-per-service, 7 schemas) |
| Cache / Rate Limit | Redis 7 (sorted-set sliding window) |
| Message Broker | RabbitMQ 3 (topic exchange, durable queues) |
| AI/LLM | Google Gemini 2.0 Flash → OpenRouter/Llama 3.1 8B (fallback) |
| ORM | SQLAlchemy 2.0 (async) |
| Auth | JWT (python-jose) with role claims |
| Containers | Docker + docker-compose |

## Quick Start

### Prerequisites
- Docker Desktop (running)
- Python 3.10+ (for Flask frontend)

### One-Click Start
```bash
start.bat
```
Auto-starts Docker Desktop (if not running), pulls images, performs health check loop, then starts Flask frontend. Admin account auto-created from `ADMIN_EMAIL`/`ADMIN_PASSWORD` env vars.

### One-Click Stop
```bash
stop.bat
```
Interactive cleanup: stops containers, optionally removes volumes/images.

### Manual Start
```bash
# 1. Copy environment
cp .env.example .env
# Edit: add GEMINI_API_KEY and/or OPENROUTER_API_KEY

# 2. Backend
docker-compose up -d --build

# 3. Frontend
cd frontend
pip install -r requirements.txt
python app.py
```

## Default Accounts

| Role | Email | Password | Auto-created |
|------|-------|----------|-------------|
| Admin | Configured via `ADMIN_EMAIL` env var | Configured via `ADMIN_PASSWORD` env var | Yes (on first startup) |
| Student | Register via `/register` | Any strong password | No |

## Access Control

| Feature | Admin | Student |
|---------|-------|---------|
| Create/delete programs & subjects | ✅ | ❌ (403) |
| Generate AI quizzes | ✅ | ❌ (403) |
| Create manual quizzes | ✅ | ❌ (403) |
| Delete quizzes | ✅ | ❌ (403) |
| Take quizzes | ✅ | ✅ |
| Add study materials (YouTube, PDF) | ✅ | ❌ (403) |
| View study materials | ✅ | ✅ |
| View all students | ✅ | ❌ (403) |
| Promote/demote user roles | ✅ | ❌ (403) |
| Reset password (forgot password) | ✅ (public) | ✅ (public) |
| Log study sessions | ✅ | ✅ (own only) |
| View revision schedule | ❌ | ✅ (own only) |
| View readiness scores | ❌ | ✅ (own only) |
| Access other user's data | ❌ (403) | ❌ (403) |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | For AI quizzes | Google Gemini API key (primary) |
| `OPENROUTER_API_KEY` | Fallback | OpenRouter key (used when Gemini quota exceeded) |
| `JWT_SECRET_KEY` | Yes | Secret for JWT signing |
| `DATABASE_URL` | Yes | MySQL connection string |
| `REDIS_URL` | Yes | Redis connection (rate limiting) |
| `RABBITMQ_URL` | Yes | RabbitMQ connection (events) |
| `ADMIN_EMAIL` | Yes | Bootstrap admin account email |
| `ADMIN_PASSWORD` | Yes | Bootstrap admin account password |

## Services

| Service | Port | Responsibilities | Events |
|---------|------|-----------------|--------|
| Flask Frontend | 3000 | All pages, SSR | — |
| API Gateway | 8000 | JWT verify, route, rate limit, CORS | — |
| User Service | 8001 | Auth, profiles, admin bootstrap, password reset, role management | — |
| Curriculum Service | 8002 | Programs, subjects, units, materials | — |
| Session Service | 8003 | Study session CRUD | Publishes: `session.logged` |
| Repetition Service | 8004 | Spaced repetition scheduling | Consumes: `session.logged`, `quiz.completed` |
| Quiz Service | 8005 | AI/manual quiz gen, submissions | Publishes: `quiz.completed` |
| Readiness Service | 8006 | Readiness scoring | Consumes: `session.logged`, `quiz.completed` / Publishes: `readiness.updated` |
| Notification Service | 8007 | Alerts, digests | Consumes: `readiness.updated` |

## Pages

| URL | Access | Description |
|-----|--------|-------------|
| `/login` | Public | Login |
| `/register` | Public | Registration |
| `/forgot-password` | Public | Password reset (no JWT needed) |
| `/dashboard` | All | Stats overview |
| `/sessions` | All | Study Materials (YouTube, PDFs, links) |
| `/quizzes` | Student: take / Admin: create+take | Quiz list |
| `/quizzes/<id>/take` | Authenticated | Take a quiz |
| `/revision` | Student | Spaced repetition grading |
| `/readiness` | Student | Quiz scores + readiness |
| `/settings` | All | Profile settings |
| `/admin` | Admin | Dashboard + student stats + programs |
| `/admin/students` | Admin | Full student list + role promote/demote |
| `/admin/quizzes` | Admin | AI generate + manual create |
| `/admin/programs/<id>/subjects` | Admin | Manage subjects per semester |

## AI Quiz Generation

```
Admin selects subject (MCA201) + unit (1) + count (5)
        │
        ▼
Quiz Service → Curriculum Service:
  → Name: "Python Programming"
  → Unit: "Basics and Data Types"
  → Topics: ["variables", "loops", "functions"]
        │
        ▼
LLM Prompt: "Generate 5 MCQ on Python Programming - Basics and Data Types"
        │
        ├── Try Gemini 2.0 Flash (primary)
        │   └── 429 quota exceeded? ──┐
        │                             ▼
        └── Try OpenRouter (Llama 3.1 8B via DeepInfra)
                │
                ▼
Quiz saved → Students see it on /quizzes → Take → Score
```

## Spaced Repetition

```
Interval Ladder:  1 → 3 → 7 → 14 → 30 → 60 → 90 days

┌──────────────────────────────────────────┐
│ Forgot (0-1)  → Reset to day 1           │
│ Barely (2)    → Same interval again       │
│ Good (3-4)    → Next level               │
│ Too Easy (5)  → Skip a level             │
└──────────────────────────────────────────┘

Near exams: intervals capped to (days_remaining / units_left)
```

## Readiness Score

Based on quiz attempt history per subject:
- Average score across all attempts
- Per-subject progress bars
- Per-unit breakdown
- Best score tracking

## Database

```bash
# View all databases
docker-compose exec mysql mysql -uroot -ppassword -e "SHOW DATABASES;"

# View users
docker-compose exec mysql mysql -uroot -ppassword studypilot_users \
  -e "SELECT id, name, email, college FROM users;"

# View quizzes
docker-compose exec mysql mysql -uroot -ppassword studypilot_quizzes \
  -e "SELECT id, subject_code, unit_number, mode FROM quizzes;"

# View study materials
docker-compose exec mysql mysql -uroot -ppassword studypilot_curriculum \
  -e "SELECT id, subject_code, title, material_type FROM study_materials;"
```

## Project Structure

```
StudyPilot/
├── frontend/                    # Flask frontend
│   ├── app.py                  # All routes + auth + API helpers
│   ├── templates/              # 20 Jinja2 HTML templates
│   ├── static/css/style.css    # All styles
│   ├── static/js/clock.js      # Real-time clock
│   └── requirements.txt        # flask, requests, python-dotenv
├── services/
│   ├── api-gateway/            # JWT verify, CORS, Redis rate limit, routing
│   ├── user-service/           # Auth, profiles, admin bootstrap, user list
│   ├── curriculum-service/     # Programs, subjects, units, study materials
│   ├── session-service/        # Session CRUD + event publish
│   ├── quiz-service/           # AI gen (Gemini/OpenRouter) + manual + submit
│   ├── repetition-service/     # Interval ladder + event consume
│   ├── readiness-service/      # Score compute + event consume/publish
│   └── notification-service/   # Event consume + alert delivery
├── shared/                     # Shared Python libs
│   ├── auth/                   # JWT, passwords, dependencies (X-User-Id)
│   ├── config/                 # BaseServiceSettings (pydantic-settings)
│   ├── events/                 # EventPublisher, EventConsumer, schemas
│   └── messaging/              # Redis client
├── scripts/
│   ├── init-databases.sql      # Creates 7 MySQL schemas
│   ├── seed_curriculum.py      # Example B.Tech CSE seed
│   └── test_all.py             # Comprehensive test suite (46 tests)
├── docker-compose.yml          # Full orchestration (11 containers)
├── start.bat                   # One-click start
├── stop.bat                    # One-click stop
├── .env                        # Local config (gitignored)
└── .env.example                # Template
```

## API Endpoints (Key)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | Public | Student registration |
| POST | `/api/v1/auth/login` | Public | Login, returns JWT |
| POST | `/api/v1/auth/refresh` | Public | Refresh access token |
| POST | `/api/v1/auth/forgot-password` | Public | Reset password (email + new password, no JWT) |
| GET | `/api/v1/users` | Admin | List all users |
| PUT | `/api/v1/users/{id}/role` | Admin | Promote/demote user role (admin/student) |
| GET | `/api/v1/programs` | Admin | List programs |
| POST | `/api/v1/quizzes/generate` | Admin | AI quiz generation |
| POST | `/api/v1/quizzes/{id}/submit` | Auth | Submit quiz attempt |
| GET | `/api/v1/readiness/scores` | Auth | User's readiness scores |

## Testing

### Comprehensive Test Suite

Run the full test suite (46 tests covering functional, security, performance, and load):

```bash
cd scripts
python test_all.py
```

### Test Categories

| Category | Tests | Coverage |
|----------|-------|----------|
| Functional | 20 | Auth, CRUD, quiz flow, enrollment, materials |
| Security | 10 | IDOR, role enforcement, token validation, injection |
| Performance | 8 | Response times, throughput, database queries |
| Load | 8 | Concurrent users, sustained traffic, rate limiting |

### Expected Results

```
Total: 46 tests | Passed: 46 | Failed: 0 | Pass Rate: 100%
```

### Performance Benchmarks

| Metric | Result |
|--------|--------|
| Average response time | < 55ms |
| P95 response time | < 105ms |
| 50 concurrent users | 94% success rate |
| Rate limiting | Correctly throttles at 100 req/min |

## Known Limitations

| Item | Status | Notes |
|------|--------|-------|
| Viva quiz grading | Exact match only | Semantic similarity (NLP) planned |
| PYQ upload/parsing | Stub | OCR + LLM extraction not yet wired |
| Weak-topic quiz gen | Stub | Needs readiness → quiz service call |
| Login lockout | Not implemented | Spec requires 5-attempt lock |
| Materials cleanup on subject delete | Partial | Quizzes cleaned, materials may orphan |
| Kubernetes manifests | Not included | Docker-compose only for now |

## License

MIT
