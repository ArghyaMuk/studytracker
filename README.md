# StudyPilot — AI-Powered Study & Exam Readiness Platform

An AI-powered microservices platform for college students that transforms passive study logging into active, personalized learning guidance for semester exams, lab vivas, and placement/competitive-exam prep.

## Features

- **Study Session Tracking** — Log sessions against subjects and units with duration, focus rating, and notes
- **AI Quiz Generation** — Generate quizzes from Gemini AI (with OpenRouter fallback) based on your syllabus
- **Custom Quiz Creation** — Admin can manually create quizzes or generate from AI and edit before publishing
- **Spaced Repetition** — SM-2 algorithm schedules revisions intelligently, weighted by upcoming exam dates
- **Exam Readiness Scoring** — 0–100 score per subject/unit combining quiz accuracy, study consistency, and more
- **Smart Notifications** — Daily digests, readiness drop alerts, exam countdowns, inactivity nudges
- **Multi-Program Support** — Works for any degree (B.Tech CSE, BBA, MCA, etc.) — fully syllabus-aware

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Next.js Frontend (:3000)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    API Gateway (:8000)                        │
│            JWT Auth │ CORS │ Rate Limiting │ Routing          │
└──┬────────┬────────┬────────┬────────┬────────┬────────┬────┘
   │        │        │        │        │        │        │
┌──▼──┐ ┌──▼───┐ ┌──▼──┐ ┌──▼──┐ ┌──▼───┐ ┌──▼────┐ ┌─▼─────┐
│User │ │Curri-│ │Sess-│ │Quiz │ │Repe- │ │Ready- │ │Notif- │
│Svc  │ │culum │ │ions │ │Svc  │ │tition│ │ness   │ │ication│
│:8001│ │:8002 │ │:8003│ │:8005│ │:8004 │ │:8006  │ │:8007  │
└──┬──┘ └──┬───┘ └──┬──┘ └──┬──┘ └──┬───┘ └──┬────┘ └──┬────┘
   │        │        │       │        │        │         │
┌──▼────────▼────────▼───────▼────────▼────────▼─────────▼────┐
│                  MySQL 8 (per-service schema)                 │
│ users│curriculum│sessions│quizzes│repetition│readiness│notifs │
└─────────────────────────────────────────────────────────────┘
┌───────────────────────┐  ┌────────────────────────────────┐
│     Redis (:6379)     │  │       RabbitMQ (:5672)          │
│ Cache │ Rate Limiting │  │ session.logged │ quiz.completed │
└───────────────────────┘  └────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, Zustand |
| Backend | Python 3.12, FastAPI (async) |
| Database | MySQL 8 (database-per-service) |
| Cache | Redis |
| Message Broker | RabbitMQ |
| AI/LLM | Google Gemini → OpenRouter (fallback) |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Containers | Docker + docker-compose |
| Testing | pytest |

## Quick Start

### Prerequisites
- Docker Desktop (running)
- Node.js 18+ (for frontend)

### One-Click Start

```bash
# Double-click or run:
start.bat
```

This starts all backend services (Docker) + frontend (Next.js) automatically.

### One-Click Stop

```bash
stop.bat
```

### Manual Start

```bash
# 1. Copy environment file
cp .env.example .env
# Edit .env to add your GEMINI_API_KEY and/or OPENROUTER_API_KEY

# 2. Start backend
docker-compose up -d --build

# 3. Start frontend
cd frontend
npm install
npm run dev
```

## Default Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@studypilot.com` | `Admin@1234` |
| Test Student | `test@student.com` | `Test@1234` |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key (primary AI provider) |
| `OPENROUTER_API_KEY` | OpenRouter API key (fallback when Gemini quota exceeded) |
| `JWT_SECRET_KEY` | Secret for JWT token signing |
| `DATABASE_URL` | MySQL connection string |
| `REDIS_URL` | Redis connection string |
| `RABBITMQ_URL` | RabbitMQ connection string |

## Services

| Service | Port | Responsibilities |
|---------|------|-----------------|
| Frontend | 3000 | Next.js UI (dashboard, quizzes, sessions, readiness) |
| API Gateway | 8000 | Routing, JWT auth, CORS, rate limiting |
| User Service | 8001 | Registration, login, profiles, exam targets |
| Curriculum Service | 8002 | Programs, subjects, units (syllabus-aware) |
| Session Service | 8003 | Study session CRUD + event publishing |
| Repetition Service | 8004 | SM-2 spaced repetition scheduling |
| Quiz Service | 8005 | AI quiz generation (Gemini/OpenRouter), custom quizzes |
| Readiness Service | 8006 | Exam readiness scoring (weighted formula) |
| Notification Service | 8007 | Digest, alerts, countdowns, nudges |

## API Endpoints

### Auth
- `POST /api/v1/auth/register` — Register new user
- `POST /api/v1/auth/login` — Login (returns JWT)
- `POST /api/v1/auth/refresh` — Refresh access token

### Users
- `GET /api/v1/users/{id}` — Get user profile
- `PUT /api/v1/users/{id}` — Update profile
- `PUT /api/v1/users/{id}/exam-targets` — Set exam dates

### Curriculum (Admin)
- `GET /api/v1/programs` — List programs
- `POST /api/v1/admin/programs` — Create program
- `DELETE /api/v1/admin/programs/{id}` — Delete program
- `GET /api/v1/programs/{id}/semesters/{n}/subjects` — Subjects for semester
- `POST /api/v1/admin/programs/{id}/subjects` — Add subject with units
- `DELETE /api/v1/admin/subjects/{id}` — Delete subject
- `GET /api/v1/subjects/{code}/units` — Units for subject

### Study Sessions
- `POST /api/v1/sessions` — Log session
- `GET /api/v1/sessions?user_id=&subject_code=` — List sessions
- `PATCH /api/v1/sessions/{id}` — Update session
- `DELETE /api/v1/sessions/{id}` — Soft-delete session

### Quizzes
- `POST /api/v1/quizzes/generate` — Generate AI quiz
- `POST /api/v1/admin/quizzes/custom` — Create custom quiz (admin)
- `GET /api/v1/quizzes/{id}` — Get quiz with questions
- `POST /api/v1/quizzes/{id}/submit` — Submit answers, get score

### Revision (Spaced Repetition)
- `GET /api/v1/revision/today?user_id=` — Today's due reviews
- `GET /api/v1/revision/upcoming?user_id=&days=7` — Upcoming schedule
- `POST /api/v1/revision/{item_id}/grade` — Grade recall (0-5)

### Readiness
- `GET /api/v1/readiness/{user_id}` — All subject scores
- `GET /api/v1/readiness/{user_id}/{subject_code}` — Subject detail

### Notifications
- `GET /api/v1/notifications/preferences?user_id=` — Get preferences
- `PUT /api/v1/notifications/preferences?user_id=` — Update preferences

## AI Quiz Generation Flow

```
Student selects subject (CS301) + unit (1)
        │
        ▼
Quiz Service fetches from Curriculum Service:
  → Subject name: "Data Structures"
  → Unit title: "Arrays and Linked Lists"
  → Topics: ["arrays", "linked-lists", "stacks"]
        │
        ▼
Sends to LLM: "Generate 5 MCQ on Data Structures - Arrays and Linked Lists"
        │
        ├── Try Gemini (primary)
        │   └── If 429/quota exceeded ──┐
        │                               ▼
        └── Try OpenRouter (fallback: Llama 3.1)
                │
                ▼
        Returns real quiz questions
```

## Event System

| Event | Producer | Consumers |
|-------|----------|-----------|
| `session.logged` | Session Service | Repetition, Readiness |
| `session.deleted` | Session Service | Readiness |
| `quiz.completed` | Quiz Service | Repetition, Readiness |
| `readiness.updated` | Readiness Service | Notification |

## Admin Features

- **Course Management** — Add/delete programs, subjects, and units
- **Custom Quiz Creator** — Manually write questions or generate from AI and edit
- **Platform Health** — Monitor all 7 microservices status
- **Notification Defaults** — Configure global notification settings
- **Danger Zone** — Reset scores, purge queues, flush cache

## Project Structure

```
StudyPilot/
├── frontend/                   # Next.js 16 + TypeScript + Tailwind
│   └── src/
│       ├── app/               # Pages (login, dashboard, quizzes, etc.)
│       ├── components/        # Sidebar, shared components
│       └── lib/               # API client, auth store
├── services/
│   ├── api-gateway/           # FastAPI reverse proxy + auth
│   ├── user-service/          # Registration, JWT, profiles
│   ├── curriculum-service/    # Programs, subjects, units
│   ├── session-service/       # Study session tracking
│   ├── quiz-service/          # AI quiz generation + custom quizzes
│   ├── repetition-service/    # SM-2 spaced repetition
│   ├── readiness-service/     # Exam readiness scoring
│   └── notification-service/  # Alerts, digests, countdowns
├── shared/                    # Shared libs (auth, events, config, redis)
├── scripts/                   # DB init, curriculum seed data
├── docker-compose.yml         # Full stack orchestration
├── start.bat                  # One-click start all services
├── stop.bat                   # One-click stop all services
├── .env                       # Environment configuration
└── .env.example               # Template for env vars
```

## SM-2 Algorithm (Spaced Repetition)

```python
EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))  # EF floor = 1.3
if q < 3: repetitions = 0; interval = 1
else:
    if repetitions == 0: interval = 1
    elif repetitions == 1: interval = 6
    else: interval = round(interval * EF)
    repetitions += 1

# Exam-aware capping:
interval = min(interval, days_until_exam / units_remaining)
```

## Readiness Score Formula

```
score = 0.25 × quiz_accuracy
      + 0.20 × pyq_accuracy
      + 0.20 × review_currency
      + 0.15 × unit_coverage
      + 0.10 × study_consistency
      + 0.10 × days_remaining_factor
```

Weights adjust for placement/competitive prep (PYQ weight increases to 30%, days_remaining drops to 0%).

## License

MIT
