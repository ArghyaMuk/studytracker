"""
StudyPilot Frontend – Flask web application serving the student/admin UI.

This module acts as a Backend-For-Frontend (BFF): it renders Jinja2 templates
and proxies all data operations to the API Gateway. Key sections:
- API helpers: authenticated HTTP wrappers with automatic token refresh.
- Auth decorators: login_required and admin_required access control.
- Route groups: auth, dashboard, quizzes, revision, readiness, settings, admin.
"""

import os
import json
import base64
import requests
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "studypilot-flask-secret-change-me")

# Register a Jinja2 filter so templates can parse JSON strings inline
import json as json_module
app.jinja_env.filters['from_json'] = lambda s: json_module.loads(s) if s else []

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@studypilot.com")


@app.context_processor
def inject_admin_email():
    """Make ADMIN_EMAIL available in all templates for conditional UI rendering."""
    return {"ADMIN_EMAIL": ADMIN_EMAIL}


def decode_jwt_payload(token: str) -> dict:
    """Decode the JWT payload without signature verification.

    Used client-side to extract user claims (sub, email, role) from the token
    immediately after login, avoiding an extra API call.
    """
    try:
        payload_b64 = token.split(".")[1]
        # JWT uses base64url encoding which may lack padding – restore it
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        decoded = base64.urlsafe_b64decode(payload_b64)
        return json.loads(decoded)
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# API Helpers – Thin wrappers around requests with automatic token refresh.
# If a 401 is returned, the helper transparently refreshes the access token
# and retries the request once before giving up.
# ══════════════════════════════════════════════════════════════════════════════

def api_headers():
    """Build request headers with the current JWT access token."""
    token = session.get("access_token")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def api_get(endpoint):
    """Authenticated GET request with auto-retry on 401."""
    try:
        r = requests.get(f"{API_BASE}{endpoint}", headers=api_headers(), timeout=30)
        if r.status_code == 401:
            if _refresh_token():
                r = requests.get(f"{API_BASE}{endpoint}", headers=api_headers(), timeout=30)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def api_post(endpoint, data):
    """Authenticated POST request with auto-retry on 401.

    Skips refresh attempt for auth endpoints to avoid infinite loops.
    """
    try:
        r = requests.post(f"{API_BASE}{endpoint}", json=data, headers=api_headers(), timeout=60)
        if r.status_code == 401 and "auth" not in endpoint:
            if _refresh_token():
                r = requests.post(f"{API_BASE}{endpoint}", json=data, headers=api_headers(), timeout=60)
        return r.status_code, r.json()
    except Exception as e:
        return 500, {"detail": str(e)}


def api_put(endpoint, data):
    """Authenticated PUT request with auto-retry on 401."""
    try:
        r = requests.put(f"{API_BASE}{endpoint}", json=data, headers=api_headers(), timeout=30)
        if r.status_code == 401:
            if _refresh_token():
                r = requests.put(f"{API_BASE}{endpoint}", json=data, headers=api_headers(), timeout=30)
        return r.status_code, r.json()
    except Exception as e:
        return 500, {"detail": str(e)}


def api_delete(endpoint):
    """Authenticated DELETE request with auto-retry on 401."""
    try:
        r = requests.delete(f"{API_BASE}{endpoint}", headers=api_headers(), timeout=30)
        if r.status_code == 401:
            if _refresh_token():
                r = requests.delete(f"{API_BASE}{endpoint}", headers=api_headers(), timeout=30)
        return r.status_code
    except Exception:
        return 500


def _refresh_token():
    """Attempt to obtain a new access token using the stored refresh token.

    On success, updates the session with fresh tokens and returns True.
    On failure (expired refresh token or network error), returns False –
    the caller should let the 401 propagate so the user is redirected to login.
    """
    refresh_token = session.get("refresh_token")
    if not refresh_token:
        return False
    try:
        r = requests.post(f"{API_BASE}/auth/refresh", json={"refresh_token": refresh_token}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            session["access_token"] = data["access_token"]
            session["refresh_token"] = data["refresh_token"]
            return True
    except Exception:
        pass
    return False


# ══════════════════════════════════════════════════════════════════════════════
# Auth Decorators – Restrict route access based on login state and role.
# ══════════════════════════════════════════════════════════════════════════════

def login_required(f):
    """Redirect to login page if no access token is present in the session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "access_token" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Restrict access to the configured admin email.

    Must be stacked after @login_required so session['email'] is populated.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("email") != ADMIN_EMAIL:
            flash("Admin access required", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════════════════════
# Auth Routes – Login, registration, and logout.
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    if "access_token" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        status, data = api_post("/auth/login", {"email": email, "password": password})
        if status == 200:
            session["access_token"] = data["access_token"]
            session["refresh_token"] = data["refresh_token"]
            # Extract user claims from the JWT payload (avoids extra API call)
            payload = decode_jwt_payload(data["access_token"])
            session["user_id"] = int(payload["sub"])
            session["email"] = payload["email"]
            # Fetch full profile for display name
            profile = api_get(f"/users/{session['user_id']}")
            if profile:
                session["user_name"] = profile.get("name", "")
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(data.get("detail", "Login failed"), "error")
    return render_template("login.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("forgot_password"))

        if len(new_password) < 8:
            flash("Password must be at least 8 characters", "error")
            return redirect(url_for("forgot_password"))

        # Call backend to reset password
        status_code, resp = api_post("/auth/reset-password", {
            "email": email,
            "new_password": new_password,
        })
        if status_code == 200:
            flash("Password reset successfully! Please login with your new password.", "success")
            return redirect(url_for("login"))
        else:
            flash(resp.get("detail", "Failed to reset password"), "error")

    return render_template("forgot_password.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = {
            "name": request.form["name"],
            "email": request.form["email"],
            "password": request.form["password"],
            "college": request.form.get("college", ""),
            "university": request.form.get("university", ""),
            "current_semester": int(request.form.get("current_semester", 1)),
        }
        status, resp = api_post("/auth/register", data)
        if status == 201:
            session["access_token"] = resp["access_token"]
            session["refresh_token"] = resp["refresh_token"]
            payload = decode_jwt_payload(resp["access_token"])
            session["user_id"] = int(payload["sub"])
            session["email"] = payload["email"]
            session["user_name"] = data["name"]
            flash("Account created!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(resp.get("detail", "Registration failed"), "error")
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ══════════════════════════════════════════════════════════════════════════════
# Dashboard
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    sessions_data = api_get(f"/sessions?user_id={user_id}") or []
    revision = api_get(f"/revision/today?user_id={user_id}") or []
    readiness = api_get(f"/readiness/{user_id}") or []
    return render_template("dashboard.html",
                           sessions=sessions_data,
                           revision=revision,
                           readiness=readiness)


# ══════════════════════════════════════════════════════════════════════════════
# Study Materials
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/sessions")
@login_required
def sessions_page():
    materials = api_get("/materials") or []
    return render_template("sessions.html", materials=materials)


@app.route("/materials/add", methods=["POST"])
@login_required
@admin_required
def add_material():
    data = {
        "subject_code": request.form["subject_code"],
        "unit_number": int(request.form["unit_number"]) if request.form.get("unit_number") else None,
        "title": request.form["title"],
        "material_type": request.form["material_type"],
        "url": request.form["url"],
        "description": request.form.get("description", ""),
    }
    status_code, resp = api_post("/admin/materials", data)
    if status_code == 201:
        flash(f'Material "{data["title"]}" added!', "success")
    else:
        flash(resp.get("detail", "Failed to add material"), "error")
    return redirect(url_for("sessions_page"))


@app.route("/materials/<int:material_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_material(material_id):
    status_code = api_delete(f"/admin/materials/{material_id}")
    if status_code == 204:
        flash("Material deleted", "success")
    else:
        flash("Failed to delete", "error")
    return redirect(url_for("sessions_page"))


# ══════════════════════════════════════════════════════════════════════════════
# Quizzes – View available quizzes, take them, submit answers
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/quizzes")
@login_required
def quizzes_page():
    quizzes = api_get("/quizzes/available") or []
    return render_template("quizzes.html", quizzes=quizzes)


@app.route("/quizzes/<int:quiz_id>/take")
@login_required
def take_quiz(quiz_id):
    quiz = api_get(f"/quizzes/{quiz_id}")
    if not quiz:
        flash("Quiz not found", "error")
        return redirect(url_for("quizzes_page"))
    return render_template("quiz_take.html", quiz=quiz)


@app.route("/quizzes/<int:quiz_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_quiz_action(quiz_id):
    status = api_delete(f"/admin/quizzes/{quiz_id}")
    if status == 204:
        flash("Quiz deleted", "success")
    else:
        flash("Failed to delete quiz", "error")
    return redirect(url_for("quizzes_page"))


@app.route("/quizzes/generate", methods=["POST"])
@login_required
@admin_required
def generate_quiz():
    """Trigger AI-based quiz generation via the quiz service."""
    user_id = session["user_id"]
    data = {
        "subject_code": request.form["subject_code"],
        "unit_number": int(request.form["unit_number"]),
        "difficulty": request.form.get("difficulty", "medium"),
        "count": int(request.form.get("count", 5)),
        "mode": request.form.get("mode", "mcq"),
    }
    status, resp = api_post(f"/quizzes/generate?user_id={user_id}", data)
    if status == 201:
        quiz_id = resp["id"]
        quiz = api_get(f"/quizzes/{quiz_id}")
        return render_template("quiz_take.html", quiz=quiz)
    else:
        flash(resp.get("detail", "Failed to generate quiz"), "error")
        return redirect(url_for("quizzes_page"))


@app.route("/quizzes/<int:quiz_id>/submit", methods=["POST"])
@login_required
def submit_quiz(quiz_id):
    """Collect answers from the form and submit for grading."""
    user_id = session["user_id"]
    # Form fields are named q_{question_id} with the selected answer as value
    answers = {}
    for key, value in request.form.items():
        if key.startswith("q_"):
            q_id = int(key.replace("q_", ""))
            answers[q_id] = value
    status, resp = api_post(f"/quizzes/{quiz_id}/submit?user_id={user_id}", {"answers": answers})
    if status == 200:
        return render_template("quiz_result.html", result=resp)
    else:
        flash("Failed to submit quiz", "error")
        return redirect(url_for("quizzes_page"))


# ══════════════════════════════════════════════════════════════════════════════
# Revision & Exams – Spaced repetition review scheduling
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/exams")
@login_required
def exams_page():
    exams = api_get("/exams") or []
    return render_template("exams.html", exams=exams)


@app.route("/revision")
@login_required
def revision_page():
    user_id = session["user_id"]
    today = api_get(f"/revision/today?user_id={user_id}") or []
    upcoming = api_get(f"/revision/upcoming?user_id={user_id}&days=7") or []
    return render_template("revision.html", today=today, upcoming=upcoming)


@app.route("/revision/<int:item_id>/grade", methods=["POST"])
@login_required
def grade_revision(item_id):
    """Submit a recall quality grade (0-5) for a revision item."""
    quality = int(request.form["quality"])
    api_post(f"/revision/{item_id}/grade", {"quality": quality})
    flash("Revision recorded!", "success")
    return redirect(url_for("revision_page"))


# ══════════════════════════════════════════════════════════════════════════════
# Readiness – Exam readiness scores and quiz history
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/readiness")
@login_required
def readiness_page():
    user_id = session["user_id"]
    scores = api_get(f"/readiness/{user_id}") or []
    quiz_history = api_get(f"/quizzes/history?user_id={user_id}") or []
    return render_template("readiness.html", scores=scores, quiz_history=quiz_history)


# ══════════════════════════════════════════════════════════════════════════════
# Settings – User profile management
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings_page():
    user_id = session["user_id"]
    if request.method == "POST":
        data = {
            "name": request.form.get("name"),
            "college": request.form.get("college"),
            "university": request.form.get("university"),
            "current_semester": int(request.form.get("current_semester", 1)),
            "daily_study_hours_target": float(request.form.get("daily_study_hours_target", 2)),
            "goal_type": request.form.get("goal_type", "semester_exam"),
        }
        status, resp = api_put(f"/users/{user_id}", data)
        if status == 200:
            session["user_name"] = data["name"]
            flash("Profile updated!", "success")
        else:
            flash("Failed to update", "error")
        return redirect(url_for("settings_page"))

    profile = api_get(f"/users/{user_id}") or {}
    return render_template("settings.html", profile=profile)


# ══════════════════════════════════════════════════════════════════════════════
# Admin Routes – Program, subject, enrollment, exam, and quiz management.
# All routes below require both @login_required and @admin_required.
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/admin")
@login_required
@admin_required
def admin_page():
    """Admin dashboard – shows programs overview and aggregate student stats."""
    programs = api_get("/programs") or []
    user_data = api_get("/users/admin/all") or {"total_users": 0, "users": []}
    # Count signups from the last 7 days for the "recent activity" widget
    from datetime import datetime, timedelta
    recent_cutoff = (datetime.now() - timedelta(days=7)).isoformat()
    recent_signups = sum(
        1 for u in user_data.get("users", [])
        if u.get("created_at") and u["created_at"] >= recent_cutoff
    )
    available_quizzes = api_get("/quizzes/available") or []
    quiz_count = len(available_quizzes)

    student_stats = {
        "total_users": user_data.get("total_users", 0),
        "users": user_data.get("users", []),
        "recent_signups": recent_signups,
        "total_quizzes": quiz_count,
    }
    return render_template("admin.html", programs=programs, student_stats=student_stats)


@app.route("/admin/students")
@login_required
@admin_required
def admin_students():
    """List all registered students with signup stats."""
    user_data = api_get("/users/admin/all") or {"total_users": 0, "users": []}
    from datetime import datetime, timedelta
    recent_cutoff = (datetime.now() - timedelta(days=7)).isoformat()
    recent_count = sum(
        1 for u in user_data.get("users", [])
        if u.get("created_at") and u["created_at"] >= recent_cutoff
    )
    return render_template("admin_students.html",
                           users=user_data.get("users", []),
                           total_users=user_data.get("total_users", 0),
                           recent_count=recent_count)


@app.route("/admin/students/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def change_user_role(user_id):
    """Promote or demote a user's role (student ↔ admin)."""
    new_role = request.form.get("role", "student")
    status_code, resp = api_put("/users/admin/role", {"user_id": user_id, "role": new_role})
    if status_code == 200:
        flash(f"User role changed to {new_role}!", "success")
    else:
        flash(resp.get("detail", "Failed to change role"), "error")
    return redirect(url_for("admin_students"))


@app.route("/admin/exams")
@login_required
@admin_required
def admin_exams():
    exams = api_get("/exams") or []
    quizzes = api_get("/quizzes/available") or []
    return render_template("admin_exams.html", exams=exams, quizzes=quizzes)


@app.route("/admin/enrollments")
@login_required
@admin_required
def admin_enrollments():
    """Manage student-subject enrollments. Collects subjects from all programs."""
    enrollments = api_get("/enrollments") or []
    students = (api_get("/users/admin/all") or {}).get("users", [])
    # Build a deduplicated list of all subjects across programs and semesters
    programs = api_get("/programs") or []
    all_subjects = []
    for prog in programs:
        for sem in range(1, prog.get("total_semesters", 8) + 1):
            subjects = api_get(f"/programs/{prog['id']}/semesters/{sem}/subjects") or []
            for s in subjects:
                if not any(x["code"] == s["code"] for x in all_subjects):
                    all_subjects.append({"code": s["code"], "name": s["name"]})
    return render_template("admin_enrollments.html",
                           enrollments=enrollments,
                           students=students,
                           subjects=all_subjects)


@app.route("/admin/results")
@login_required
@admin_required
def admin_results():
    """View all quiz attempts with per-student analytics."""
    all_attempts = api_get("/quizzes/history/all") or []
    user_data = api_get("/users/admin/all") or {"users": []}
    users_map = {u["id"]: u for u in user_data.get("users", [])}

    # Enrich each attempt with the student's name and email for display
    for a in all_attempts:
        user = users_map.get(a.get("user_id"))
        a["user_name"] = user["name"] if user else ""
        a["user_email"] = user["email"] if user else ""

    # Aggregate statistics
    avg_score = round(sum(a["score"] for a in all_attempts) / len(all_attempts)) if all_attempts else 0
    pass_count = sum(1 for a in all_attempts if a["score"] >= 50)
    pass_rate = round(pass_count / len(all_attempts) * 100) if all_attempts else 0

    # Group scores by student for per-student progress tracking
    student_scores = {}
    for a in all_attempts:
        uid = a.get("user_id")
        if uid not in student_scores:
            student_scores[uid] = {
                "name": a["user_name"],
                "email": a["user_email"],
                "scores": [],
            }
        student_scores[uid]["scores"].append(a["score"])

    students_with_attempts = [
        {
            "name": s["name"],
            "email": s["email"],
            "attempt_count": len(s["scores"]),
            "avg_score": round(sum(s["scores"]) / len(s["scores"])),
        }
        for s in student_scores.values()
        if s["name"]  # Skip admin entries without a name
    ]
    students_with_attempts.sort(key=lambda x: x["avg_score"], reverse=True)

    return render_template("admin_results.html",
                           all_attempts=all_attempts,
                           students_with_attempts=students_with_attempts,
                           avg_score=avg_score,
                           pass_rate=pass_rate)


@app.route("/admin/enrollments/add", methods=["POST"])
@login_required
@admin_required
def add_enrollment():
    data = {
        "user_id": int(request.form["user_id"]),
        "user_email": request.form.get("user_email", ""),
        "subject_code": request.form["subject_code"],
        "subject_name": request.form.get("subject_name", ""),
    }
    status_code, resp = api_post("/admin/enrollments", data)
    if status_code == 201:
        flash(f"Student enrolled in {data['subject_code']}!", "success")
    else:
        flash(resp.get("detail", "Failed to enroll"), "error")
    return redirect(url_for("admin_enrollments"))


@app.route("/admin/enrollments/<int:enrollment_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_enrollment(enrollment_id):
    status_code = api_delete(f"/admin/enrollments/{enrollment_id}")
    if status_code == 204:
        flash("Enrollment removed", "success")
    else:
        flash("Failed to remove", "error")
    return redirect(url_for("admin_enrollments"))


@app.route("/admin/exams/add", methods=["POST"])
@login_required
@admin_required
def add_exam():
    data = {
        "subject_code": request.form["subject_code"],
        "subject_name": request.form.get("subject_name", ""),
        "exam_type": request.form["exam_type"],
        "exam_date": request.form["exam_date"],
        "exam_time": request.form.get("exam_time", ""),
        "duration_minutes": int(request.form["duration_minutes"]) if request.form.get("duration_minutes") else None,
        "venue": request.form.get("venue", ""),
        "notes": request.form.get("notes", ""),
        "quiz_id": int(request.form["quiz_id"]) if request.form.get("quiz_id") else None,
    }
    status_code, resp = api_post("/admin/exams", data)
    if status_code == 201:
        flash(f"Exam scheduled for {data['subject_code']} on {data['exam_date']}!", "success")
    else:
        flash(resp.get("detail", "Failed to schedule exam"), "error")
    return redirect(url_for("admin_exams"))


@app.route("/admin/exams/<int:exam_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_exam(exam_id):
    status_code = api_delete(f"/admin/exams/{exam_id}")
    if status_code == 204:
        flash("Exam deleted", "success")
    else:
        flash("Failed to delete", "error")
    return redirect(url_for("admin_exams"))


@app.route("/admin/programs/add", methods=["POST"])
@login_required
@admin_required
def add_program():
    data = {
        "name": request.form["name"],
        "total_semesters": int(request.form["total_semesters"]),
    }
    status, resp = api_post("/admin/programs", data)
    if status == 201:
        flash(f'Program "{data["name"]}" created!', "success")
    else:
        flash(resp.get("detail", "Failed"), "error")
    return redirect(url_for("admin_page"))


@app.route("/admin/programs/<int:program_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_program(program_id):
    """Delete a program and cascade-delete all associated quizzes."""
    # Collect all subjects under this program so their quizzes can be removed
    programs = api_get("/programs") or []
    program = next((p for p in programs if p["id"] == program_id), None)
    if program:
        for sem in range(1, program.get("total_semesters", 8) + 1):
            subjects = api_get(f"/programs/{program_id}/semesters/{sem}/subjects") or []
            for subj in subjects:
                api_delete(f"/admin/quizzes/by-subject/{subj['code']}")

    status = api_delete(f"/admin/programs/{program_id}")
    if status == 204:
        flash("Program and all related quizzes deleted", "success")
    else:
        flash("Failed to delete", "error")
    return redirect(url_for("admin_page"))


@app.route("/admin/programs/<int:program_id>/subjects")
@login_required
@admin_required
def admin_subjects(program_id):
    semester = int(request.args.get("semester", 1))
    programs = api_get("/programs") or []
    program = next((p for p in programs if p["id"] == program_id), None)
    subjects = api_get(f"/programs/{program_id}/semesters/{semester}/subjects") or []
    return render_template("admin_subjects.html",
                           program=program, subjects=subjects,
                           semester=semester, programs=programs)


@app.route("/admin/programs/<int:program_id>/subjects/add", methods=["POST"])
@login_required
@admin_required
def add_subject(program_id):
    """Add a subject with its unit breakdown to a program semester."""
    semester = int(request.form.get("semester", 1))
    # Dynamically collect unit fields (unit_title_1, unit_topics_1, etc.)
    units = []
    i = 1
    while f"unit_title_{i}" in request.form:
        title = request.form[f"unit_title_{i}"]
        topics = request.form.get(f"unit_topics_{i}", "")
        if title.strip():
            units.append({"unit_number": i, "unit_title": title, "topics_json": topics})
        i += 1

    data = {
        "code": request.form["code"],
        "name": request.form["name"],
        "semester": semester,
        "type": request.form.get("type", "theory"),
        "credits": int(request.form.get("credits", 3)),
        "units": units,
    }
    status, resp = api_post(f"/admin/programs/{program_id}/subjects", data)
    if status == 201:
        flash(f'Subject "{data["name"]}" added!', "success")
    else:
        flash(resp.get("detail", "Failed"), "error")
    return redirect(url_for("admin_subjects", program_id=program_id, semester=semester))


@app.route("/admin/subjects/<int:subject_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_subject(subject_id):
    """Delete a subject and its associated quizzes."""
    program_id = request.form.get("program_id", 1)
    semester = request.form.get("semester", 1)
    subject_code = request.form.get("subject_code", "")

    # Clean up quizzes linked to this subject before removing it
    if subject_code:
        api_delete(f"/admin/quizzes/by-subject/{subject_code}")

    status = api_delete(f"/admin/subjects/{subject_id}")
    if status == 204:
        flash("Subject and related quizzes deleted", "success")
    else:
        flash("Failed to delete", "error")
    return redirect(url_for("admin_subjects", program_id=program_id, semester=semester))


@app.route("/admin/quizzes", methods=["GET", "POST"])
@login_required
@admin_required
def admin_quizzes():
    """Admin quiz management – supports AI generation and manual creation."""
    if request.method == "POST":
        action = request.form.get("action")

        if action == "generate":
            # ── AI-generated quiz: send params to the quiz service ──
            user_id = session["user_id"]
            data = {
                "subject_code": request.form["subject_code"],
                "unit_number": int(request.form["unit_number"]),
                "difficulty": request.form.get("difficulty", "medium"),
                "count": int(request.form.get("count", 5)),
                "mode": request.form.get("mode", "mcq"),
            }
            status, resp = api_post(f"/quizzes/generate?user_id={user_id}", data)
            if status == 201:
                quiz = api_get(f"/quizzes/{resp['id']}")
                flash(f"Quiz generated with {len(quiz.get('questions', []))} questions!", "success")
            else:
                flash(resp.get("detail", "Generation failed"), "error")

        elif action == "manual":
            # ── Manual quiz: collect questions from numbered form fields ──
            questions = []
            i = 1
            while f"question_{i}" in request.form:
                q = {
                    "question": request.form[f"question_{i}"],
                    "options_json": None,
                    "correct_answer": request.form.get(f"answer_{i}", "A"),
                    "difficulty": request.form.get(f"difficulty_{i}", "medium"),
                }
                if request.form.get("mode") == "mcq":
                    options = [
                        request.form.get(f"option_{i}_A", ""),
                        request.form.get(f"option_{i}_B", ""),
                        request.form.get(f"option_{i}_C", ""),
                        request.form.get(f"option_{i}_D", ""),
                    ]
                    import json
                    q["options_json"] = json.dumps(options)
                questions.append(q)
                i += 1

            if questions:
                data = {
                    "subject_code": request.form["subject_code"],
                    "unit_number": int(request.form["unit_number"]),
                    "mode": request.form.get("mode", "mcq"),
                    "questions": questions,
                }
                status, resp = api_post("/admin/quizzes/custom", data)
                if status == 201:
                    flash(f"Custom quiz created with {resp.get('question_count', 0)} questions!", "success")
                else:
                    flash(resp.get("detail", "Failed"), "error")

        return redirect(url_for("admin_quizzes"))
    return render_template("admin_quizzes.html")


if __name__ == "__main__":
    app.run(debug=True, port=3000)
