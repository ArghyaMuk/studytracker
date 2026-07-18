# StudyPilot — Complete Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Setup & Installation](#setup--installation)
4. [User Accounts](#user-accounts)
5. [Admin Guide](#admin-guide)
6. [Student Guide](#student-guide)
7. [API Reference](#api-reference)
8. [Architecture](#architecture)
9. [Database Schema](#database-schema)
10. [Security](#security)
11. [Testing](#testing)

---

## Project Overview

**StudyPilot** is an AI-powered microservices platform for college exam preparation. It enables:
- Admin to create courses, quizzes (AI-generated or manual), schedule exams, upload study materials
- Students to take exams, view materials, track readiness, and follow spaced repetition schedules

### Key Features
| Feature | Admin | Student |
|---------|-------|---------|
| Create/manage courses & subjects | ✅ | ❌ |
| Generate AI quizzes (Gemini/OpenRouter) | ✅ | ❌ |
| Create manual quizzes | ✅ | ❌ |
| Schedule exams | ✅ | ❌ |
| Assign quizzes to exams | ✅ | ❌ |
| Upload study materials (YouTube, PDF) | ✅ | ❌ |
| Enroll students in courses | ✅ | ❌ |
| View all student results | ✅ | ❌ |
| Take exams | ❌ | ✅ |
| View study materials | ✅ | ✅ |
| View exam schedule | ✅ | ✅ |
| Spaced repetition | ❌ | ✅ |
| Readiness tracking | ❌ | ✅ |

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Frontend | Flask + Jinja2 + Vanilla CSS | 3.1 |
| Backend Services | FastAPI (Python async) | 0.115 |
| Database | MySQL | 8.0 |
| Cache & Rate Limit | Redis | 7 |
| Message Broker | RabbitMQ | 3 |
| AI Provider (Primary) | Google Gemini | 2.0 Flash |
| AI Provider (Fallback) | OpenRouter / Llama 3.1 | 8B |
| Containerization | Docker + docker-compose | Latest |
| Authentication | JWT (python-jose) | HS256 |
| ORM | SQLAlchemy | 2.0 |
| Python | CPython | 3.12 |

---

## Setup & Installation

### Prerequisites
- Docker Desktop installed
- Python 3.10+ installed
- Git installed

### Quick Start (Windows)
```bash
git clone https://github.com/ArghyaMuk/studytracker.git
cd studytracker
cp .env.example .env
# Edit .env: add GEMINI_API_KEY and/or OPENROUTER_API_KEY
start.bat
```

### Manual Start
```bash
# 1. Start backend (Docker)
docker-compose up -d --build

# 2. Start frontend
cd frontend
pip install -r requirements.txt
python app.py
```

### Stop Everything
```bash
stop.bat
```

### URLs After Start
| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Gateway | http://localhost:8000 |
| API Health | http://localhost:8000/health |
| RabbitMQ Dashboard | http://localhost:15672 (guest/guest) |

---

## User Accounts

### Default Admin (auto-created on first startup)
- **Email:** admin@studypilot.com
- **Password:** Admin@1234
- **Role:** admin (full access)

### Creating Student Accounts
Students register at http://localhost:3000/register with:
- Full name
- Email (must be unique)
- Password (min 8 chars, uppercase, lowercase, digit, special char)
- College & University
- Current semester

---

## Admin Guide

### 1. Course Management
**Path:** Admin → Programs section (or `/admin`)

1. Add a program (e.g. "B.Tech CSE", "MCA", "BBA")
2. Click on program name → manage subjects per semester
3. Add subjects with code, name, type (theory/lab), credits
4. Add units per subject with title and topic keywords

### 2. Creating Quizzes

**AI Generated (Gemini/OpenRouter):**
1. Go to Quizzes → "Generate Quiz with AI" section
2. Enter subject code + unit number + count + difficulty
3. Click "Generate Quiz"
4. System calls Gemini (or OpenRouter fallback) with actual subject name + unit topics
5. Quiz is created and available for students

**Manual:**
1. Go to Quizzes → "Add Questions Manually" section
2. Enter subject code + unit number
3. Type each question with 4 options and mark correct answer
4. Click "+ Add Question" for more
5. Click "Save Quiz"

### 3. Scheduling Exams
**Path:** Admin → Schedule Exams (or `/admin/exams`)

1. Fill in: Subject code, name, exam type, date, time, duration, venue
2. **Assign a Quiz** from dropdown (makes it an online exam)
3. Click "Schedule Exam"
4. Students see it on their Exam Schedule page with "Start Exam" button

### 4. Study Materials
**Path:** Study Materials (`/sessions`)

1. Scroll to "Add Study Material" form
2. Enter subject code, title, type (YouTube/PDF/Notes/Link), URL
3. YouTube videos embed directly for students
4. PDF/links open in new tab

### 5. Student Enrollment
**Path:** Admin → Course Enrollment (or `/admin/enrollments`)

1. Select student from dropdown
2. Select subject from dropdown
3. Click "Enroll Student"
4. View/remove enrollments in table

### 6. Viewing Results
**Path:** Admin → Student Results (or `/admin/results`)

Shows:
- Total quiz attempts across all students
- Average score, pass rate (≥50%)
- Per-student breakdown with progress bars
- Individual attempt details (student, subject, score, date)

---

## Student Guide

### 1. Taking Exams
**Path:** Exam Schedule (`/exams`)

1. View all scheduled exams
2. Click "✍️ Start Exam" on online exams
3. Answer all MCQ questions
4. Click "Submit Quiz"
5. See score and per-question feedback immediately

### 2. Viewing Study Materials
**Path:** Study Materials (`/sessions`)

- YouTube videos play embedded (no need to leave the page)
- PDF/link materials open in new tab
- Materials organized by subject

### 3. Spaced Repetition
**Path:** Revision (`/revision`)

- See what's due for review today
- Grade your recall: Forgot / Hard / Good / Easy
- Schedule adjusts automatically:
  - Forgot → review tomorrow
  - Good → next level (1→3→7→14→30→60→90 days)
  - Easy → skip a level

### 4. Readiness Scores
**Path:** Readiness (`/readiness`)

- Shows your quiz performance per subject
- Average score, best score, attempts count
- Progress bars color-coded (green ≥75%, yellow ≥50%, red <50%)

---

## API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Register new user |
| POST | /api/v1/auth/login | Login (returns JWT) |
| POST | /api/v1/auth/refresh | Refresh access token |

### Users (Admin)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/users/{id} | Get user profile |
| PUT | /api/v1/users/{id} | Update profile |
| GET | /api/v1/users/admin/all | List all users (admin) |

### Curriculum
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/programs | List programs |
| POST | /api/v1/admin/programs | Create program (admin) |
| DELETE | /api/v1/admin/programs/{id} | Delete program (admin) |
| GET | /api/v1/programs/{id}/semesters/{n}/subjects | Subjects for semester |
| POST | /api/v1/admin/programs/{id}/subjects | Create subject (admin) |
| DELETE | /api/v1/admin/subjects/{id} | Delete subject (admin) |
| GET | /api/v1/subjects/{code}/units | Get units for subject |

### Study Materials
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/materials | List all materials |
| POST | /api/v1/admin/materials | Add material (admin) |
| DELETE | /api/v1/admin/materials/{id} | Delete material (admin) |

### Quizzes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/quizzes/available | List available quizzes |
| POST | /api/v1/quizzes/generate | Generate AI quiz (admin) |
| GET | /api/v1/quizzes/{id} | Get quiz with questions |
| POST | /api/v1/quizzes/{id}/submit | Submit answers, get score |
| GET | /api/v1/quizzes/history?user_id= | User's attempt history |
| GET | /api/v1/quizzes/history/all | All attempts (admin) |
| POST | /api/v1/admin/quizzes/custom | Create manual quiz (admin) |
| DELETE | /api/v1/admin/quizzes/{id} | Delete quiz (admin) |
| DELETE | /api/v1/admin/quizzes/by-subject/{code} | Delete all quizzes for subject |

### Exams
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/exams | List all scheduled exams |
| POST | /api/v1/admin/exams | Schedule exam (admin) |
| DELETE | /api/v1/admin/exams/{id} | Delete exam (admin) |

### Enrollment
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/enrollments | List enrollments |
| POST | /api/v1/admin/enrollments | Enroll student (admin) |
| DELETE | /api/v1/admin/enrollments/{id} | Remove enrollment (admin) |

### Revision
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/revision/today?user_id= | Due today |
| GET | /api/v1/revision/upcoming?user_id=&days=7 | Upcoming week |
| POST | /api/v1/revision/{id}/grade | Grade recall (0-5) |

### Readiness
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/readiness/{user_id} | All scores |
| GET | /api/v1/readiness/{user_id}/{subject_code} | Subject detail |

---

## Architecture

### Microservices (11 containers)
```
┌─ Flask Frontend (:3000)
│
├─ API Gateway (:8000) ── JWT verify, CORS, Redis rate limit
│
├─ User Service (:8001) ── Auth, profiles, admin bootstrap
├─ Curriculum Service (:8002) ── Programs, subjects, materials, exams, enrollments
├─ Session Service (:8003) ── Study sessions + event publish
├─ Quiz Service (:8005) ── AI gen + manual + submit + history
├─ Repetition Service (:8004) ── Spaced repetition + event consume
├─ Readiness Service (:8006) ── Score compute + event consume/publish
├─ Notification Service (:8007) ── Alert delivery + event consume
│
├─ MySQL 8 ── 7 independent schemas
├─ Redis 7 ── Rate limiting (sorted set sliding window)
└─ RabbitMQ 3 ── Event bus (topic exchange)
```

### Event Flow
```
session.logged ──► Repetition Service + Readiness Service
quiz.completed ──► Repetition Service + Readiness Service
readiness.updated ──► Notification Service
```

---

## Database Schema

### 7 Independent Schemas
| Schema | Tables |
|--------|--------|
| studypilot_users | users, user_profiles, exam_targets |
| studypilot_curriculum | programs, subjects, subject_units, university_templates, study_materials, exam_schedules, student_enrollments |
| studypilot_sessions | sessions |
| studypilot_quizzes | quizzes, quiz_questions, quiz_attempts, pyq_uploads |
| studypilot_repetition | review_items |
| studypilot_readiness | readiness_scores |
| studypilot_notifications | notification_preferences, notification_log |

### Viewing Data
```bash
docker-compose exec mysql mysql -uroot -ppassword studypilot_users -e "SELECT * FROM users;"
docker-compose exec mysql mysql -uroot -ppassword studypilot_quizzes -e "SELECT * FROM quiz_attempts;"
docker-compose exec mysql mysql -uroot -ppassword studypilot_curriculum -e "SELECT * FROM exam_schedules;"
```

---

## Security

| Layer | Implementation |
|-------|---------------|
| Authentication | JWT with `role` claim (admin/student) |
| Token Expiry | Access: 15min, Refresh: 7 days |
| IDOR Protection | X-User-Id header enforced, ownership checks |
| Admin Enforcement | X-User-Role header checked on every admin endpoint |
| Rate Limiting | Redis sorted-set sliding window (100 req/min) |
| Password | bcrypt hash, strong policy validation |
| CORS | Restricted to frontend origin only |
| Auto-bootstrap | Admin seeded on first startup |

---

## Testing

### Running the Backend Health Check
```bash
curl http://localhost:8000/health
```

### Testing as Admin
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@studypilot.com","password":"Admin@1234"}'

# Use returned access_token in subsequent requests:
# -H "Authorization: Bearer <token>"
```

### Testing as Student
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","password":"Test@1234","college":"LPU","current_semester":3}'
```

### Viewing Logs
```bash
docker-compose logs -f quiz-service
docker-compose logs -f api-gateway
docker-compose logs user-service --tail 20
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| GEMINI_API_KEY | For AI | Google Gemini API key |
| OPENROUTER_API_KEY | Fallback | Used when Gemini quota exceeded |
| JWT_SECRET_KEY | Yes | JWT signing secret |
| DATABASE_URL | Yes | MySQL connection |
| REDIS_URL | Yes | Redis connection |
| RABBITMQ_URL | Yes | RabbitMQ connection |
| FLASK_SECRET_KEY | Yes | Flask session secret |

---

## File Structure

```
StudyPilot/
├── frontend/
│   ├── app.py                     # Flask app (all routes)
│   ├── templates/                 # 15 Jinja2 templates
│   ├── static/css/style.css       # All styles
│   ├── static/js/clock.js         # Real-time clock
│   └── requirements.txt
├── services/
│   ├── api-gateway/               # JWT, CORS, rate limit, routing
│   ├── user-service/              # Auth, profiles, admin bootstrap
│   ├── curriculum-service/        # Programs, subjects, materials, exams
│   ├── session-service/           # Study sessions + events
│   ├── quiz-service/              # AI/manual quizzes + scoring
│   ├── repetition-service/        # Spaced repetition
│   ├── readiness-service/         # Score computation
│   └── notification-service/      # Alert delivery
├── shared/                        # Shared Python libs
├── scripts/                       # DB init, seed data
├── docker-compose.yml             # Full orchestration
├── start.bat / stop.bat           # One-click scripts
├── .env / .env.example            # Configuration
├── README.md                      # Quick overview
└── DOCUMENTATION.md               # This file
```
