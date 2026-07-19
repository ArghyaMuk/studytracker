# Screenshot Capture Guide for Project Report

## Setup
1. Run `start.bat` (or docker-compose up + python app.py)
2. Open Chrome at http://localhost:3000
3. Use **Windows + Shift + S** or **Snipping Tool** to capture screenshots
4. Save each screenshot in a folder called `screenshots/`

---

## Screenshots to Capture

### 1. Login Page
- **URL:** http://localhost:3000/login
- **What to show:** Purple gradient background, StudyPilot title, email/password fields, Sign In button, Register link
- **Save as:** `01_login.png`

### 2. Registration Page
- **URL:** http://localhost:3000/register
- **What to show:** Full registration form (name, email, password, college, university, semester dropdown)
- **Save as:** `02_register.png`

---

### 3. Admin Dashboard
- **Login:** admin@studypilot.com / Admin@1234
- **URL:** http://localhost:3000/admin
- **What to show:** Stats cards (Total Students, Programs, Recent Signups, Total Quizzes), Recent Students table, Programs list with Add/Delete
- **Save as:** `03_admin_dashboard.png`

### 4. Admin Quiz Creation (AI)
- **URL:** http://localhost:3000/quizzes (logged in as admin)
- **What to show:** "Generate Quiz with AI" form + "Add Questions Manually" form below
- **Save as:** `04_admin_quiz_creation.png`

### 5. Admin Custom Quiz Page
- **URL:** http://localhost:3000/admin/quizzes
- **What to show:** AI generate section + Manual add with question builder (options A/B/C/D)
- **Save as:** `05_admin_custom_quiz.png`

### 6. Admin Exam Scheduling
- **URL:** http://localhost:3000/admin/exams
- **What to show:** Schedule form (subject, type, date, time, duration, venue, quiz dropdown) + scheduled exams table
- **Save as:** `06_admin_exam_scheduling.png`

### 7. Admin Student Results
- **URL:** http://localhost:3000/admin/results
- **What to show:** Stats (Total Attempts, Avg Score, Pass Rate), results table, per-student progress bars
- **Save as:** `07_admin_results.png`

### 8. Admin Student Management
- **URL:** http://localhost:3000/admin/students
- **What to show:** Total accounts stat, full student table (name, email, college, semester, joined)
- **Save as:** `08_admin_students.png`

### 9. Admin Course Enrollment
- **URL:** http://localhost:3000/admin/enrollments
- **What to show:** Enroll form (student dropdown + subject dropdown), current enrollments table
- **Save as:** `09_admin_enrollment.png`

### 10. Admin Subjects Page
- **URL:** http://localhost:3000/admin/programs/{id}/subjects (click on a program first)
- **What to show:** Semester tabs, Add Subject form with units, existing subjects list
- **Save as:** `10_admin_subjects.png`

---

### 11. Student Dashboard
- **Login:** test@student.com / Test@1234 (or register a new account)
- **URL:** http://localhost:3000/dashboard
- **What to show:** Stat cards (Sessions, Due Revisions, Avg Readiness), Today's Revision Plan
- **Save as:** `11_student_dashboard.png`

### 12. Student Exam Schedule
- **URL:** http://localhost:3000/exams
- **What to show:** Exam cards with subject, type badge, date/time, green "Start Exam" button
- **Save as:** `12_student_exam_schedule.png`

### 13. Student Taking Quiz
- **URL:** Click "Start Exam" on the exams page (or /quizzes/{id}/take)
- **What to show:** Question text, 4 MCQ radio button options, Submit Quiz button
- **Save as:** `13_student_taking_quiz.png`

### 14. Quiz Result
- **After submitting quiz**
- **What to show:** Score percentage (large), correct/wrong count, per-question green/red feedback
- **Save as:** `14_quiz_result.png`

### 15. Study Materials
- **URL:** http://localhost:3000/sessions
- **What to show:** YouTube video embedded (playing), PDF links, subject badges, stats cards
- **Save as:** `15_study_materials.png`

### 16. Spaced Repetition
- **URL:** http://localhost:3000/revision
- **What to show:** "Due Today" section with Forgot/Hard/Good/Easy buttons, Upcoming table
- **Save as:** `16_spaced_repetition.png`

### 17. Readiness Scores
- **URL:** http://localhost:3000/readiness
- **What to show:** Stats (Quiz Avg Score, Quizzes Taken, Best Score), per-subject progress bars, attempt table
- **Save as:** `17_readiness.png`

### 18. Settings Page
- **URL:** http://localhost:3000/settings
- **What to show:** Profile form (name, college, university, semester, study target, goal type)
- **Save as:** `18_settings.png`

### 19. Study Materials (Admin View)
- **URL:** http://localhost:3000/sessions (as admin)
- **What to show:** Same materials + "Add Study Material" form at bottom (subject, title, type dropdown, URL)
- **Save as:** `19_admin_materials.png`

---

## Tips for Clean Screenshots
- Use Chrome full-screen (F11) for consistent size
- Set browser width to ~1280px
- Make sure there's actual data (create a program, add subjects, generate a quiz, take it)
- For student screenshots, first take an exam so scores appear on readiness page
- Use the sidebar to show navigation context

## Quick Data Setup for Screenshots
1. Login as admin
2. Go to Admin → Add program "MCA" (2 semesters)
3. Click MCA → Add subject "MCA201 - Python Programming" with 2 units
4. Go to Quizzes → Generate AI quiz for MCA201 Unit 1
5. Go to Admin → Schedule Exams → Schedule with quiz assigned
6. Go to Study Materials → Add a YouTube video URL
7. Logout → Login as student → Take the exam → See results
