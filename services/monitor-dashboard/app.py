"""
StudyPilot Monitoring Dashboard
Runs independently on port 9000 — shows real-time API health,
MySQL stats, Redis stats, RabbitMQ status, and system metrics.
Protected by login (admin credentials from env vars).
"""

import os
import time
import json
import threading
import requests
import pymysql
import redis
from functools import wraps
from flask import Flask, render_template, jsonify, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.getenv("MONITOR_SECRET", "monitor-secret-key-change-me")

# Configuration
API_GATEWAY = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASS = os.getenv("MYSQL_PASSWORD", "password")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RABBITMQ_API = os.getenv("RABBITMQ_API", "http://localhost:15672/api")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "arghya")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "arghya")
MONITOR_USER = os.getenv("MONITOR_USER", "admin")
MONITOR_PASS = os.getenv("MONITOR_PASS", "admin123")

# In-memory metrics store (updated by background thread)
metrics = {
    "api_health": {},
    "mysql": {},
    "redis": {},
    "rabbitmq": {},
    "users": [],
    "history": [],  # Last 60 data points (1 per second)
    "last_update": None,
}


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def collect_api_health():
    """Check all microservices health."""
    try:
        r = requests.get(f"{API_GATEWAY}/health", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"status": "unreachable", "services": {}}


def collect_mysql_stats():
    """Get MySQL connection count, database sizes, query stats."""
    try:
        conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT,
                               user=MYSQL_USER, password=MYSQL_PASS)
        cursor = conn.cursor()

        # Connection count
        cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
        threads = int(cursor.fetchone()[1])

        # Total queries
        cursor.execute("SHOW STATUS LIKE 'Queries'")
        queries = int(cursor.fetchone()[1])

        # Uptime
        cursor.execute("SHOW STATUS LIKE 'Uptime'")
        uptime = int(cursor.fetchone()[1])

        # Database sizes
        cursor.execute("""
            SELECT table_schema, 
                   ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb,
                   SUM(table_rows) as row_count
            FROM information_schema.tables
            WHERE table_schema LIKE 'studypilot_%'
            GROUP BY table_schema
        """)
        databases = [{"name": row[0], "size_mb": float(row[1] or 0), "rows": int(row[2] or 0)}
                     for row in cursor.fetchall()]

        # Slow queries
        cursor.execute("SHOW STATUS LIKE 'Slow_queries'")
        slow = int(cursor.fetchone()[1])

        # Fetch users list
        try:
            cursor.execute("SELECT id, name, email, role, college, current_semester, created_at FROM studypilot_users.users ORDER BY id")
            users = [{"id": r[0], "name": r[1], "email": r[2], "role": r[3] or "student",
                      "college": r[4] or "—", "semester": r[5] or "—",
                      "created_at": str(r[6])[:19] if r[6] else "—"}
                     for r in cursor.fetchall()]
            metrics["users"] = users
        except Exception:
            pass

        conn.close()
        return {
            "status": "connected",
            "connections": threads,
            "total_queries": queries,
            "uptime_seconds": uptime,
            "slow_queries": slow,
            "databases": databases,
            "qps": round(queries / max(uptime, 1), 1),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def collect_redis_stats():
    """Get Redis memory usage, connected clients, key count."""
    try:
        r = redis.from_url(REDIS_URL)
        info = r.info()
        return {
            "status": "connected",
            "memory_used_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
            "memory_peak_mb": round(info.get("used_memory_peak", 0) / 1024 / 1024, 2),
            "connected_clients": info.get("connected_clients", 0),
            "total_keys": sum(info.get(f"db{i}", {}).get("keys", 0) for i in range(16)),
            "uptime_seconds": info.get("uptime_in_seconds", 0),
            "ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def collect_rabbitmq_stats():
    """Get RabbitMQ queue depths, message rates."""
    try:
        r = requests.get(f"{RABBITMQ_API}/overview",
                         auth=(RABBITMQ_USER, RABBITMQ_PASS), timeout=5)
        if r.status_code == 200:
            data = r.json()
            msg_stats = data.get("message_stats", {})
            queue_totals = data.get("queue_totals", {})
            return {
                "status": "connected",
                "messages_ready": queue_totals.get("messages_ready", 0),
                "messages_unacked": queue_totals.get("messages_unacknowledged", 0),
                "publish_rate": msg_stats.get("publish_details", {}).get("rate", 0),
                "deliver_rate": msg_stats.get("deliver_details", {}).get("rate", 0),
                "connections": data.get("object_totals", {}).get("connections", 0),
                "queues": data.get("object_totals", {}).get("queues", 0),
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    return {"status": "unreachable"}


def background_collector():
    """Background thread: collect all metrics every 2 seconds."""
    while True:
        try:
            api = collect_api_health()
            mysql = collect_mysql_stats()
            redis_stats = collect_redis_stats()
            rabbit = collect_rabbitmq_stats()

            metrics["api_health"] = api
            metrics["mysql"] = mysql
            metrics["redis"] = redis_stats
            metrics["rabbitmq"] = rabbit
            metrics["last_update"] = time.strftime("%H:%M:%S")

            # Keep last 60 data points for charts
            metrics["history"].append({
                "time": time.strftime("%H:%M:%S"),
                "mysql_connections": mysql.get("connections", 0),
                "mysql_qps": mysql.get("qps", 0),
                "redis_ops": redis_stats.get("ops_per_sec", 0),
                "redis_memory": redis_stats.get("memory_used_mb", 0),
                "rabbit_ready": rabbit.get("messages_ready", 0),
            })
            if len(metrics["history"]) > 60:
                metrics["history"] = metrics["history"][-60:]
        except Exception:
            pass
        time.sleep(2)


# Start background collector
collector_thread = threading.Thread(target=background_collector, daemon=True)
collector_thread.start()


@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == MONITOR_USER and password == MONITOR_PASS:
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html", error=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/metrics")
@login_required
def api_metrics():
    """JSON endpoint for real-time metrics (polled by frontend JS)."""
    return jsonify(metrics)


if __name__ == "__main__":
    print("StudyPilot Monitor Dashboard running at http://localhost:9000")
    app.run(host="0.0.0.0", port=9000, debug=False)
