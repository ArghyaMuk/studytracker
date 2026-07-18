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

# Custom Jinja2 filter
import json as json_module
app.jinja_env.filters['from_json'] = lambda s: json_module.loads(s) if s else []

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


def decode_jwt_payload(token: str) -> dict:
    """Safely decode JWT payload (no verification, just parse)."""
    try:
        payload_b64 = token.split(".")[1]
        # Fix base64url padding
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        decoded = base64.urlsafe_b64decode(payload_b64)
        return json.loads(decoded)
    except Exception:
        return {}


# ── Helpers ──

def api_headers():
    """Get headers with JWT token for API calls."""
    token = session.get("access_token")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def api_get(endpoint):
    """Make authenticated GET request to backend."""
    try:
        r = requests.get(f"{API_BASE}{endpoint}", headers=api_headers(), timeout=30)
        if r.status_code == 401:
            if _refresh_token():
                r = requests.get(f"{API_BASE}{endpoint}", headers=api_headers(), timeout=30)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def api_post(endpoint, data):
    """Make authenticated POST request to backend."""
    try:
        r = requests.post(f"{API_BASE}{endpoint}", json=data, headers=api_headers(), timeout=60)
        if r.status_code == 401 and "auth" not in endpoint:
            if _refresh_token():
                r = requests.post(f"{API_BASE}{endpoint}", json=data, headers=api_headers(), timeout=60)
        return r.status_code, r.json()
    except Exception as e:
        return 500, {"detail": str(e)}


def api_put(endpoint, data):
    """Make authenticated PUT request to backend."""
    try:
        r = requests.put(f"{API_BASE}{endpoint}", json=data, headers=api_headers(), timeout=30)
        if r.status_code == 401:
            if _refresh_token():
                r = requests.put(f"{API_BASE}{endpoint}", json=data, headers=api_headers(), timeout=30)
        return r.status_code, r.json()
    except Exception as e:
        return 500, {"detail": str(e)}


def api_delete(endpoint):
    """Make authenticated DELETE request to backend."""
    try:
        r = requests.delete(f"{API_BASE}{endpoint}", headers=api_headers(), timeout=30)
        if r.status_code == 401:
            if _refresh_token():
                r = requests.delete(f"{API_BASE}{endpoint}", headers=api_headers(), timeout=30)
        return r.status_code
    except Exception:
        return 500


def _refresh_token():
    """Attempt to refresh the access token using the refresh token."""
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


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "access_token" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator to require admin login."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("email") != "admin@studypilot.com":
            flash("Admin access required", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


# ── Auth Routes ──

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
            # Decode user ID from token
            payload = decode_jwt_payload(data["access_token"])
            session["user_id"] = int(payload["sub"])
            session["email"] = payload["email"]
            # Fetch profile
            profile = api_get(f"/users/{session['user_id']}")
            if profile:
                session["user_name"] = profile.get("name", "")
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(data.get("detail", "Login failed"), "error")
    return render_template("login.html")


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


# ── Dashboard ──

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


# ── Study Materials (was Study Sessions) ──

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


# ── Quizzes ──

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
    user_id = session["user_id"]
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


# ── Revision ──

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
    quality = int(request.form["quality"])
    api_post(f"/revision/{item_id}/grade", {"quality": quality})
    flash("Revision recorded!", "success")
    return redirect(url_for("revision_page"))


# ── Readiness ──

@app.route("/readiness")
@login_required
def readiness_page():
    user_id = session["user_id"]
    scores = api_get(f"/readiness/{user_id}") or []
    # Also get quiz history for score display
    quiz_history = api_get(f"/quizzes/history?user_id={user_id}") or []
    return render_template("readiness.html", scores=scores, quiz_history=quiz_history)


# ── Settings ──

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


# ── Admin ──

@app.route("/admin")
@login_required
@admin_required
def admin_page():
    programs = api_get("/programs") or []
    # Fetch student stats
    user_data = api_get("/users/admin/all") or {"total_users": 0, "users": []}
    # Count recent signups (last 7 days)
    from datetime import datetime, timedelta
    recent_cutoff = (datetime.now() - timedelta(days=7)).isoformat()
    recent_signups = sum(
        1 for u in user_data.get("users", [])
        if u.get("created_at") and u["created_at"] >= recent_cutoff
    )
    # Get quiz count
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


@app.route("/admin/exams")
@login_required
@admin_required
def admin_exams():
    exams = api_get("/exams") or []
    quizzes = api_get("/quizzes/available") or []
    return render_template("admin_exams.html", exams=exams, quizzes=quizzes)


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
    # First, get all subjects for this program to delete their quizzes
    programs = api_get("/programs") or []
    program = next((p for p in programs if p["id"] == program_id), None)
    if program:
        for sem in range(1, program.get("total_semesters", 8) + 1):
            subjects = api_get(f"/programs/{program_id}/semesters/{sem}/subjects") or []
            for subj in subjects:
                # Delete all quizzes for this subject code
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
    semester = int(request.form.get("semester", 1))
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
    program_id = request.form.get("program_id", 1)
    semester = request.form.get("semester", 1)
    subject_code = request.form.get("subject_code", "")

    # Delete all quizzes for this subject code
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
    if request.method == "POST":
        action = request.form.get("action")

        if action == "generate":
            # Generate from AI
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
            # Manual quiz creation
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
