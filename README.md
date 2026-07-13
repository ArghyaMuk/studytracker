# StudyPilot — AI-Powered Study & Exam Readiness Platform

An AI-powered microservices platform for college students that transforms passive study logging into active, personalized learning guidance for semester exams, lab vivas, and placement/competitive-exam prep.

## Features

### For Students
- **Take Quizzes** — Attempt quizzes set by admin (MCQ and Viva modes)
- **Study Session Tracking** — Log sessions against subjects and units with duration, focus rating, and notes
- **Spaced Repetition** — Smart revision scheduling with interval ladder (1→3→7→14→30→60→90 days)
- **Exam Readiness Scoring** — 0–100 score per subject/unit combining quiz accuracy, study consistency, and more
- **Dashboard** — Overview of sessions, due revisions, and readiness stats

### For Admin
- **Course Management** — Add/delete programs, subjects, and units for any degree
- **AI Quiz Generation** — Generate quizzes using Gemini AI (with OpenRouter fallback)
- **Manual Quiz Creation** — Write questions manually with options and correct answers
- **Student Management** — View all registered students, signup stats
- **Platform Health** — Monitor all microservices status

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Flask Frontend (:3000)                      │
│         HTML/CSS │ Jinja2 Templates │ Server-side             │
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
| Frontend | Flask, Jinja2, Vanilla HTML/CSS, JavaScript |
| Backend | Python 3.12, FastAPI (async) |
| Database | MySQL 8 (database-per-service) |
| Cache | Redis |
| Message Broker | RabbitMQ |
| AI/LLM | Google Gemini (primary) → OpenRouter/Llama 3.1 (fallback) |
| ORM | SQLAlchemy 2.0 (async) |
| Containers | Docker + docker-compose |

## Quick Start

### Prerequisites
- Docker Desktop (running)
- Python 3.10+ (for frontend)

### One-Click Start

```bash
start.bat
```

Starts all backend services (Docker) + Flask frontend automatically.

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
pip install -r requirements.txt
python app.py
```

## Default Accounts

| Role | Email | Password | Sees |
|------|-------|----------|------|
| Admin | `admin@studypilot.com` | `Admin@1234` | Dashboard, Quizzes (create), Settings, Admin Panel |
| Student | `test@student.com` | `Test@1234` | Dashboard, Sessions, Quizzes (take), Revision, Readiness, Settings |

## Access Control

| Feature | Admin | Student |
|---------|-------|---------|
| Create quizzes (AI + Manual) | ✅ | ❌ |
| Take quizzes | ✅ | ✅ |
| View students | ✅ | ❌ |
| Manage courses | ✅ | ❌ |
| Log study sessions | ❌ | ✅ |
| Spaced repetition | ❌ | ✅ |
| Readiness scores | ❌ | ✅ |
| Settings | ✅ | ✅ |

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
| Frontend (Flask) | 3000 | All pages, server-side rendering |
| API Gateway | 8000 | Routing, JWT auth, CORS, rate limiting (60s timeout) |
| User Service | 8001 | Registration, login, profiles, admin user list |
| Curriculum Service | 8002 | Programs, subjects, units (syllabus-aware) |
| Session Service | 8003 | Study session CRUD + event publishing |
| Repetition Service | 8004 | Spaced repetition scheduling |
| Quiz Service | 8005 | AI quiz generation, custom quizzes, quiz submissions |
| Readiness Service | 8006 | Exam readiness scoring (weighted formula) |
| Notification Service | 8007 | Digest, alerts, countdowns, nudges |

## AI Quiz Generation Flow

```
Admin creates quiz for subject CS301, Unit 1
        │
        ▼
Quiz Service looks up Curriculum Service:
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
        └── Try OpenRouter (fallback: Llama 3.1 8B)
                │
                ▼
Quiz saved to database → Students can take it from /quizzes
```

## Pages

| URL | Who | Description |
|-----|-----|-------------|
| `/login` | All | Login page |
| `/register` | All | Registration page |
| `/dashboard` | All | Overview stats |
| `/sessions` | Student | Log and track study sessions |
| `/quizzes` | Student: take / Admin: create | Quiz list + creation |
| `/quizzes/<id>/take` | Student | Take a specific quiz |
| `/revision` | Student | Spaced repetition schedule + grading |
| `/readiness` | Student | Readiness scores per subject |
| `/settings` | All | Profile and preferences |
| `/admin` | Admin | Course management + student stats |
| `/admin/students` | Admin | Full student list |
| `/admin/quizzes` | Admin | AI generate + manual quiz creation |
| `/admin/programs/<id>/subjects` | Admin | Manage subjects per semester |

## Spaced Repetition System

Simple interval-based revision scheduling:

```
How well did you recall?
┌──────────────────────────────────────────┐
│ Forgot (0-1)  → Review tomorrow          │
│ Barely (2)    → Same interval again       │
│ Good (3-4)    → Next level               │
│ Too Easy (5)  → Skip a level             │
└──────────────────────────────────────────┘

Interval ladder:  1 → 3 → 7 → 14 → 30 → 60 → 90 days

Near exams: intervals are shortened automatically
so all units get reviewed before the exam date.
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

## Project Structure

```
StudyPilot/
├── frontend/                   # Flask + HTML/CSS
│   ├── app.py                 # Flask application (all routes)
│   ├── templates/             # Jinja2 HTML templates
│   │   ├── base.html          # Layout with sidebar + clock
│   │   ├── login.html         # Auth pages
│   │   ├── register.html
│   │   ├── dashboard.html     # Student/admin dashboard
│   │   ├── sessions.html      # Study session tracking
│   │   ├── quizzes.html       # Take quizzes (student) / Create (admin)
│   │   ├── quiz_take.html     # Quiz-taking interface
│   │   ├── quiz_result.html   # Score + feedback
│   │   ├── revision.html      # Spaced repetition
│   │   ├── readiness.html     # Readiness scores
│   │   ├── settings.html      # Profile settings
│   │   ├── admin.html         # Admin panel
│   │   ├── admin_students.html # Student management
│   │   ├── admin_subjects.html # Subject management
│   │   └── admin_quizzes.html  # Quiz creation
│   ├── static/css/style.css   # All styles
│   ├── static/js/clock.js     # Real-time clock
│   └── requirements.txt       # flask, requests, python-dotenv
├── services/
│   ├── api-gateway/           # FastAPI reverse proxy + auth + CORS
│   ├── user-service/          # Registration, JWT, profiles, admin user list
│   ├── curriculum-service/    # Programs, subjects, units (CRUD + delete)
│   ├── session-service/       # Study session tracking
│   ├── quiz-service/          # AI quiz gen + custom quizzes + submissions
│   ├── repetition-service/    # Spaced repetition (interval ladder)
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

## Database Schema

Check the database:
```bash
# List all databases
docker-compose exec mysql mysql -uroot -ppassword -e "SHOW DATABASES;"

# View users
docker-compose exec mysql mysql -uroot -ppassword studypilot_users -e "SELECT * FROM users;"

# View quizzes
docker-compose exec mysql mysql -uroot -ppassword studypilot_quizzes -e "SELECT * FROM quizzes;"

# View sessions
docker-compose exec mysql mysql -uroot -ppassword studypilot_sessions -e "SELECT * FROM sessions;"
```

## Event System

| Event | Producer | Consumers |
|-------|----------|-----------|
| `session.logged` | Session Service | Repetition, Readiness |
| `session.deleted` | Session Service | Readiness |
| `quiz.completed` | Quiz Service | Repetition, Readiness |
| `readiness.updated` | Readiness Service | Notification |

## License

MIT
