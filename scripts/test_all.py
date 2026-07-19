"""
StudyPilot - Comprehensive Test Suite
Tests: Functional, Security, Performance, Load

Run: python scripts/test_all.py
"""

import time
import json
import requests
import concurrent.futures
from datetime import datetime

API = "http://localhost:8000/api/v1"
RESULTS = []
PASS = 0
FAIL = 0


def log(test_name, passed, detail="", duration_ms=0):
    global PASS, FAIL
    status = "✅ PASS" if passed else "❌ FAIL"
    if passed:
        PASS += 1
    else:
        FAIL += 1
    RESULTS.append({
        "test": test_name,
        "status": "PASS" if passed else "FAIL",
        "detail": detail,
        "duration_ms": duration_ms,
    })
    print(f"  {status} | {test_name} ({duration_ms}ms) {detail}")


def timed_request(method, url, **kwargs):
    start = time.time()
    r = method(url, **kwargs)
    duration = int((time.time() - start) * 1000)
    return r, duration


# ═══════════════════════════════════════════════════
# SECTION 1: HEALTH & INFRASTRUCTURE
# ═══════════════════════════════════════════════════
def test_health():
    print("\n══ 1. HEALTH & INFRASTRUCTURE ══")
    r, ms = timed_request(requests.get, "http://localhost:8000/health")
    log("API Gateway health", r.status_code == 200, f"status={r.json().get('status')}", ms)

    health = r.json()
    for svc, status in health.get("services", {}).items():
        log(f"Service: {svc}", status == "healthy", "", 0)


# ═══════════════════════════════════════════════════
# SECTION 2: AUTHENTICATION
# ═══════════════════════════════════════════════════
def test_auth():
    print("\n══ 2. AUTHENTICATION ══")

    # Login as admin
    r, ms = timed_request(requests.post, f"{API}/auth/login",
                          json={"email": "admin@studypilot.com", "password": "Admin@1234"})
    log("Admin login", r.status_code == 200, "", ms)
    admin_token = r.json().get("access_token", "") if r.status_code == 200 else ""

    # Invalid login
    r, ms = timed_request(requests.post, f"{API}/auth/login",
                          json={"email": "admin@studypilot.com", "password": "wrong"})
    log("Invalid login rejected", r.status_code == 401, "", ms)

    # Register new student
    email = f"test_{int(time.time())}@test.com"
    r, ms = timed_request(requests.post, f"{API}/auth/register",
                          json={"name": "Load Test", "email": email, "password": "Test@1234",
                                "college": "LPU", "current_semester": 3})
    log("Student registration", r.status_code == 201, f"email={email}", ms)
    student_token = r.json().get("access_token", "") if r.status_code == 201 else ""

    # Duplicate registration
    r, ms = timed_request(requests.post, f"{API}/auth/register",
                          json={"name": "Dup", "email": email, "password": "Test@1234",
                                "college": "X", "current_semester": 1})
    log("Duplicate email rejected", r.status_code == 409, "", ms)

    # Token refresh
    if student_token:
        refresh = requests.post(f"{API}/auth/login",
                                json={"email": email, "password": "Test@1234"}).json().get("refresh_token")
        r, ms = timed_request(requests.post, f"{API}/auth/refresh",
                              json={"refresh_token": refresh})
        log("Token refresh", r.status_code == 200, "", ms)

    return admin_token, student_token


# ═══════════════════════════════════════════════════
# SECTION 3: AUTHORIZATION & SECURITY
# ═══════════════════════════════════════════════════
def test_security(admin_token, student_token):
    print("\n══ 3. AUTHORIZATION & SECURITY ══")
    admin_h = {"Authorization": f"Bearer {admin_token}"}
    student_h = {"Authorization": f"Bearer {student_token}"}

    # Student cannot access admin endpoints
    r, ms = timed_request(requests.post, f"{API}/admin/programs",
                          json={"name": "Hack", "total_semesters": 2}, headers=student_h)
    log("Student blocked from admin/programs", r.status_code == 403, "", ms)

    r, ms = timed_request(requests.get, f"{API}/users/admin/all", headers=student_h)
    log("Student blocked from user list", r.status_code == 403, "", ms)

    r, ms = timed_request(requests.post, f"{API}/admin/quizzes/custom",
                          json={"subject_code": "X", "unit_number": 1, "mode": "mcq",
                                "questions": [{"question": "q", "correct_answer": "A", "difficulty": "easy"}]},
                          headers=student_h)
    log("Student blocked from quiz creation", r.status_code == 403, "", ms)

    # No auth = 401
    r, ms = timed_request(requests.get, f"{API}/users/admin/all")
    log("No auth returns 401", r.status_code == 401, "", ms)

    # Admin can access
    r, ms = timed_request(requests.get, f"{API}/users/admin/all", headers=admin_h)
    log("Admin can list users", r.status_code == 200, f"users={r.json().get('total_users')}", ms)


# ═══════════════════════════════════════════════════
# SECTION 4: CURRICULUM (CRUD)
# ═══════════════════════════════════════════════════
def test_curriculum(admin_token):
    print("\n══ 4. CURRICULUM CRUD ══")
    h = {"Authorization": f"Bearer {admin_token}"}

    # Create program
    r, ms = timed_request(requests.post, f"{API}/admin/programs",
                          json={"name": "Test Program", "total_semesters": 4}, headers=h)
    log("Create program", r.status_code == 201, "", ms)
    prog_id = r.json().get("id") if r.status_code == 201 else None

    if prog_id:
        # Create subject
        r, ms = timed_request(requests.post, f"{API}/admin/programs/{prog_id}/subjects",
                              json={"code": f"TST{int(time.time()) % 1000}", "name": "Test Subject",
                                    "semester": 1, "type": "theory", "credits": 3,
                                    "units": [{"unit_number": 1, "unit_title": "Unit One", "topics_json": '["topic1"]'}]},
                              headers=h)
        log("Create subject", r.status_code == 201, "", ms)

        # List subjects
        r, ms = timed_request(requests.get, f"{API}/programs/{prog_id}/semesters/1/subjects", headers=h)
        log("List subjects", r.status_code == 200, f"count={len(r.json())}", ms)

        # Delete program (cascade)
        r, ms = timed_request(requests.delete, f"{API}/admin/programs/{prog_id}", headers=h)
        log("Delete program cascade", r.status_code == 204, "", ms)

    return prog_id


# ═══════════════════════════════════════════════════
# SECTION 5: QUIZ LIFECYCLE
# ═══════════════════════════════════════════════════
def test_quiz(admin_token, student_token):
    print("\n══ 5. QUIZ LIFECYCLE ══")
    admin_h = {"Authorization": f"Bearer {admin_token}"}
    student_h = {"Authorization": f"Bearer {student_token}"}

    # Admin creates manual quiz
    r, ms = timed_request(requests.post, f"{API}/admin/quizzes/custom",
                          json={"subject_code": "TEST101", "unit_number": 1, "mode": "mcq",
                                "questions": [
                                    {"question": "What is 2+2?", "options_json": '["3","4","5","6"]',
                                     "correct_answer": "B", "difficulty": "easy"},
                                    {"question": "What is 3+3?", "options_json": '["5","6","7","8"]',
                                     "correct_answer": "B", "difficulty": "easy"},
                                ]}, headers=admin_h)
    log("Admin creates manual quiz", r.status_code == 201, f"id={r.json().get('id')}", ms)
    quiz_id = r.json().get("id") if r.status_code == 201 else None

    if quiz_id:
        # List available quizzes
        r, ms = timed_request(requests.get, f"{API}/quizzes/available", headers=student_h)
        log("List available quizzes", r.status_code == 200, f"count={len(r.json())}", ms)
        has_quiz = any(q["id"] == quiz_id for q in r.json())
        log("New quiz appears in list", has_quiz, "", 0)

        # Get quiz
        r, ms = timed_request(requests.get, f"{API}/quizzes/{quiz_id}", headers=student_h)
        log("Get quiz with questions", r.status_code == 200, f"questions={len(r.json().get('questions', []))}", ms)

        # Submit quiz
        questions = r.json().get("questions", [])
        answers = {str(q["id"]): "B" for q in questions}
        r, ms = timed_request(requests.post, f"{API}/quizzes/{quiz_id}/submit",
                              json={"answers": answers}, headers=student_h)
        log("Submit quiz", r.status_code == 200, f"score={r.json().get('score')}%", ms)
        log("Score is 100%", r.json().get("score") == 100.0, "", 0)

        # Quiz history
        r, ms = timed_request(requests.get, f"{API}/quizzes/history?user_id=99", headers=student_h)
        log("Quiz history endpoint", r.status_code == 200, "", ms)

        # Delete quiz
        r, ms = timed_request(requests.delete, f"{API}/admin/quizzes/{quiz_id}", headers=admin_h)
        log("Admin deletes quiz", r.status_code == 204, "", ms)

    return quiz_id


# ═══════════════════════════════════════════════════
# SECTION 6: EXAM SCHEDULING
# ═══════════════════════════════════════════════════
def test_exams(admin_token):
    print("\n══ 6. EXAM SCHEDULING ══")
    h = {"Authorization": f"Bearer {admin_token}"}

    r, ms = timed_request(requests.post, f"{API}/admin/exams",
                          json={"subject_code": "TEST101", "subject_name": "Test Exam",
                                "exam_type": "internal", "exam_date": "2026-08-01",
                                "exam_time": "10:00", "duration_minutes": 60}, headers=h)
    log("Schedule exam", r.status_code == 201, "", ms)
    exam_id = r.json().get("id") if r.status_code == 201 else None

    r, ms = timed_request(requests.get, f"{API}/exams", headers=h)
    log("List exams", r.status_code == 200, f"count={len(r.json())}", ms)

    if exam_id:
        r, ms = timed_request(requests.delete, f"{API}/admin/exams/{exam_id}", headers=h)
        log("Delete exam", r.status_code == 204, "", ms)


# ═══════════════════════════════════════════════════
# SECTION 7: STUDY MATERIALS
# ═══════════════════════════════════════════════════
def test_materials(admin_token):
    print("\n══ 7. STUDY MATERIALS ══")
    h = {"Authorization": f"Bearer {admin_token}"}

    r, ms = timed_request(requests.post, f"{API}/admin/materials",
                          json={"subject_code": "TEST101", "title": "Test Video",
                                "material_type": "video",
                                "url": "https://youtube.com/watch?v=test123"}, headers=h)
    log("Add study material", r.status_code == 201, "", ms)
    mat_id = r.json().get("id") if r.status_code == 201 else None

    r, ms = timed_request(requests.get, f"{API}/materials", headers=h)
    log("List materials", r.status_code == 200, f"count={len(r.json())}", ms)

    if mat_id:
        r, ms = timed_request(requests.delete, f"{API}/admin/materials/{mat_id}", headers=h)
        log("Delete material", r.status_code == 204, "", ms)


# ═══════════════════════════════════════════════════
# SECTION 8: PERFORMANCE TESTING
# ═══════════════════════════════════════════════════
def test_performance(admin_token):
    print("\n══ 8. PERFORMANCE TESTING ══")
    h = {"Authorization": f"Bearer {admin_token}"}

    # Measure response times for key endpoints
    endpoints = [
        ("GET", "/programs"),
        ("GET", "/quizzes/available"),
        ("GET", "/exams"),
        ("GET", "/materials"),
    ]

    for method, ep in endpoints:
        times = []
        for _ in range(10):
            start = time.time()
            requests.get(f"{API}{ep}", headers=h, timeout=10)
            times.append((time.time() - start) * 1000)
        avg = int(sum(times) / len(times))
        p95 = int(sorted(times)[int(len(times) * 0.95)])
        log(f"Perf: {ep} (10 reqs)", avg < 500, f"avg={avg}ms p95={p95}ms", avg)


# ═══════════════════════════════════════════════════
# SECTION 9: LOAD TESTING
# ═══════════════════════════════════════════════════
def test_load(admin_token):
    print("\n══ 9. LOAD TESTING ══")
    h = {"Authorization": f"Bearer {admin_token}"}

    def make_request(_):
        try:
            r = requests.get(f"{API}/quizzes/available", headers=h, timeout=10)
            return r.status_code, r.elapsed.total_seconds()
        except:
            return 0, 10.0

    # 50 concurrent requests
    print("  Running 50 concurrent requests...")
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_request, i) for i in range(50)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    total_time = time.time() - start

    success = sum(1 for code, _ in results if code == 200)
    avg_time = sum(t for _, t in results) / len(results) * 1000
    log(f"Load: 50 concurrent (20 threads)", success >= 45,
        f"success={success}/50, avg={int(avg_time)}ms, total={int(total_time*1000)}ms", int(total_time * 1000))

    # 100 sequential requests (throughput)
    print("  Running 100 sequential requests...")
    start = time.time()
    successes = 0
    for _ in range(100):
        try:
            r = requests.get(f"{API}/quizzes/available", headers=h, timeout=5)
            if r.status_code == 200:
                successes += 1
        except:
            pass
    total_time = time.time() - start
    rps = int(100 / total_time)
    log(f"Throughput: 100 sequential requests", successes >= 50,
        f"success={successes}/100, {rps} req/s, total={int(total_time)}s", int(total_time * 1000))

    # Rate limiting test (should hit 429 after 100/min)
    print("  Testing rate limiting...")
    rate_limited = False
    for i in range(110):
        r = requests.get(f"{API}/quizzes/available", headers=h, timeout=5)
        if r.status_code == 429:
            rate_limited = True
            log("Rate limiting triggers", True, f"triggered at request #{i+1}", 0)
            break
    if not rate_limited:
        log("Rate limiting triggers", False, "did not trigger within 110 requests", 0)


# ═══════════════════════════════════════════════════
# SECTION 10: SPACED REPETITION
# ═══════════════════════════════════════════════════
def test_revision(admin_token):
    print("\n══ 10. REVISION & READINESS ══")
    h = {"Authorization": f"Bearer {admin_token}"}

    r, ms = timed_request(requests.get, f"{API}/revision/today?user_id=1", headers=h)
    log("Get today's revision", r.status_code == 200, f"items={len(r.json())}", ms)

    r, ms = timed_request(requests.get, f"{API}/revision/upcoming?user_id=1&days=7", headers=h)
    log("Get upcoming revision", r.status_code == 200, f"items={len(r.json())}", ms)

    r, ms = timed_request(requests.get, f"{API}/readiness/1", headers=h)
    log("Get readiness scores", r.status_code == 200 or r.status_code == 404, f"status={r.status_code}", ms)


# ═══════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  StudyPilot - Comprehensive Test Suite")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    test_health()
    admin_token, student_token = test_auth()
    test_security(admin_token, student_token)
    test_curriculum(admin_token)
    test_quiz(admin_token, student_token)
    test_exams(admin_token)
    test_materials(admin_token)
    test_performance(admin_token)
    test_load(admin_token)
    test_revision(admin_token)

    print("\n" + "=" * 60)
    print(f"  RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
    print(f"  Pass Rate: {int(PASS / (PASS + FAIL) * 100)}%")
    print("=" * 60)

    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "passed": PASS,
            "failed": FAIL,
            "total": PASS + FAIL,
            "pass_rate": f"{int(PASS / (PASS + FAIL) * 100)}%",
            "tests": RESULTS,
        }, f, indent=2)
    print(f"\n  Results saved to test_results.json")
