from fastapi import FastAPI
import pyodbc
import os
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta

from fastapi.middleware.cors import CORSMiddleware

import smtplib
from email.mime.text import MIMEText

import schedule
import time
import threading

from pydantic import BaseModel

# ---------------- Database connection ---------------- #
def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost\\SQLEXPRESS;"
        "DATABASE=DotNetProjects;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_EMAIL = "shirishagangarapu@gmail.com"

# ---------------- MODEL ---------------- #
class Task(BaseModel):
    name: str
    date: str
    priority: str

# ---------------- GET TASKS ---------------- #
@app.get("/tasks")
def get_tasks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, task_name, task_date, status, priority
        FROM Todo_app
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "name": r[1],
            "date": str(r[2]),
            "status": r[3],
            "priority": r[4]
        }
        for r in rows
    ]

# ---------------- ADD TASK ---------------- #
@app.post("/tasks")
def add_task(task: Task):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Todo_app
        (task_name, task_date, priority, user_email, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        task.name,
        task.date,
        task.priority,
        DEFAULT_EMAIL,
        "Pending"
    ))

    conn.commit()
    conn.close()

    return {"message": "Task added"}

# ---------------- UPDATE STATUS ---------------- #
@app.put("/tasks/{task_id}")
def update_task(task_id: int, data: dict):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Todo_app
        SET status = ?
        WHERE id = ?
    """, (data["status"], task_id))

    conn.commit()
    conn.close()

    return {"message": "Updated"}

# ---------------- DELETE ---------------- #
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM Todo_app WHERE id=?",
        (task_id,)
    )

    conn.commit()
    conn.close()

    return {"message": "Deleted"}

# ---------------- EMAIL ---------------- #
EMAIL_ADDRESS = os.getenv("TODO_EMAIL")
EMAIL_PASSWORD = os.getenv("TODO_PASSWORD")

def send_email(to_email, task_name):
    subject = "Missed Task Alert"

    body = f"""
You missed this task:

{task_name}

Please check your To-Do List app.
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"Email sent to {to_email}")
        return True

    except Exception as e:
        print("Email error:", e)
        return False

# ---------------- DATE NORMALIZER ---------------- #
def normalize_to_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value.split(" ")[0])
    return None

# ---------------- OVERDUE CHECK ---------------- #
def check_overdue_tasks():
    print("Checking tasks...")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, task_name, task_date,
               status, user_email, last_alert_sent
        FROM Todo_app
    """)

    rows = cursor.fetchall()

    now = datetime.now()
    four_hrs_ago = now - timedelta(hours=4)

    for row in rows:
        task_id, task_name, task_date, status, email, last_alert_sent = row

        task_date = normalize_to_date(task_date)

        if task_date != date.today():
            continue

        if (status or "").lower() == "completed":
            continue

        # normalize last alert
        if last_alert_sent and isinstance(last_alert_sent, str):
            last_alert_sent = datetime.fromisoformat(last_alert_sent)

        if last_alert_sent and last_alert_sent > four_hrs_ago:
            continue

        # SEND EMAIL
        if send_email(DEFAULT_EMAIL, task_name):
            cursor.execute("""
                UPDATE Todo_app
                SET last_alert_sent = ?
                WHERE id = ?
            """, (now, task_id))

    conn.commit()
    conn.close()

# ---------------- SCHEDULER ---------------- #
schedule.every(1).minutes.do(check_overdue_tasks)

def run_scheduler():
    print("Scheduler thread started")

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"Scheduler error: {e}")

        time.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()

    print("Scheduler started")

    yield