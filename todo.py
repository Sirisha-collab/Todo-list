import customtkinter as ctk
from tkinter import messagebox
from customtkinter import CTkTabview, CTkProgressBar
from datetime import date
import pyodbc
import os
from dotenv import load_dotenv

# ---------------- STYLE ---------------- #
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------------- ENV ---------------- #
load_dotenv()

server = os.getenv("DB_SERVER")
database = os.getenv("DB_DATABASE")

# ---------------- DB CONNECTION ---------------- #
connection_string = f"""
DRIVER={{ODBC Driver 18 for SQL Server}};
SERVER={server};
DATABASE={database};
Trusted_Connection=yes;
TrustServerCertificate=yes;
"""

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

print("Connected Successfully!")

# ---------------- TABLE ---------------- #
cursor.execute("""
IF NOT EXISTS (
    SELECT * FROM sysobjects
    WHERE name='Todo_app' AND xtype='U'
)
CREATE TABLE Todo_app (
    id INT PRIMARY KEY IDENTITY(1,1),
    task_name VARCHAR(255),
    task_date DATE,
    status VARCHAR(20) DEFAULT 'Pending',
    priority VARCHAR(10) DEFAULT 'Medium'
)
""")
conn.commit()

# ---------------- GLOBALS ---------------- #
today = str(date.today())
task_vars = {}

# ---------------- FUNCTIONS ---------------- #

def clear_frame(frame):
    for w in frame.winfo_children():
        w.destroy()


def toggle_task(task_id):
    var = task_vars.get(task_id)
    if not var:
        return

    status = "Completed" if var.get() else "Pending"

    cursor.execute("""
        UPDATE Todo_app
        SET status = ?
        WHERE id = ?
    """, (status, task_id))

    conn.commit()


def priority_color(priority):
    if priority == "High":
        return "#ff4d4d"
    elif priority == "Medium":
        return "#ffcc00"
    else:
        return "#33cc66"


def create_task_box(frame, task_id, name, status, priority):
    var = ctk.BooleanVar(value=(status == "Completed"))
    task_vars[task_id] = var

    color = priority_color(priority)

    # "shadow-like" card
    outer = ctk.CTkFrame(frame, fg_color="#2b2b2b", corner_radius=12)
    outer.pack(fill="x", pady=6, padx=10)

    inner = ctk.CTkFrame(outer, fg_color="#1f1f1f", corner_radius=10)
    inner.pack(fill="x", padx=2, pady=2)

    def on_enter(e):
        inner.configure(fg_color="#2a2a2a")

    def on_leave(e):
        inner.configure(fg_color="#1f1f1f")

    inner.bind("<Enter>", on_enter)
    inner.bind("<Leave>", on_leave)

    cb = ctk.CTkCheckBox(
        inner,
        text=f"{task_id} | {name}",
        variable=var,
        command=lambda: toggle_task(task_id),
        text_color=color
    )
    cb.pack(side="left", padx=10, pady=8)

    tag = ctk.CTkLabel(
        inner,
        text=priority,
        text_color=color,
        font=("Arial", 12, "bold")
    )
    tag.pack(side="right", padx=10)


def create_progress(frame, percent):
    bar = CTkProgressBar(frame, width=420)
    bar.set(percent / 100)
    bar.pack(pady=5)

    ctk.CTkLabel(frame, text=f"Completed: {percent:.0f}%").pack()


def load_tasks():
    clear_frame(today_frame)
    clear_frame(tomorrow_frame)
    clear_frame(month_frame)
    clear_frame(overdue_frame)

    task_vars.clear()

    # ---------------- TODAY ---------------- #
    cursor.execute("""
        SELECT id, task_name, status, priority
        FROM Todo_app
        WHERE task_date = ?
    """, (today,))
    today_rows = cursor.fetchall()

    for r in today_rows:
        create_task_box(today_frame, r[0], r[1], r[2], r[3])

    done = len([r for r in today_rows if r[2] == "Completed"])
    create_progress(today_frame, (done / len(today_rows) * 100) if today_rows else 0)

    # ---------------- TOMORROW ---------------- #
    cursor.execute("""
        SELECT id, task_name, status, priority
        FROM Todo_app
        WHERE task_date = DATEADD(day, 1, ?)
    """, (today,))
    tom_rows = cursor.fetchall()

    for r in tom_rows:
        create_task_box(tomorrow_frame, r[0], r[1], r[2], r[3])

    done = len([r for r in tom_rows if r[2] == "Completed"])
    create_progress(tomorrow_frame, (done / len(tom_rows) * 100) if tom_rows else 0)

    # ---------------- MONTH ---------------- #
    cursor.execute("""
        SELECT id, task_name, status, priority
        FROM Todo_app
        WHERE MONTH(task_date) = MONTH(GETDATE())
    """)
    month_rows = cursor.fetchall()

    for r in month_rows:
        create_task_box(month_frame, r[0], r[1], r[2], r[3])

    done = len([r for r in month_rows if r[2] == "Completed"])
    create_progress(month_frame, (done / len(month_rows) * 100) if month_rows else 0)

    # ---------------- OVERDUE ---------------- #
    cursor.execute("""
        SELECT id, task_name, status, priority
        FROM Todo_app
        WHERE task_date < ?
        AND status != 'Completed'
    """, (today,))
    over_rows = cursor.fetchall()

    for r in over_rows:
        create_task_box(overdue_frame, r[0], r[1], r[2], r[3])

    done = len([r for r in over_rows if r[2] == "Completed"])
    create_progress(overdue_frame, (done / len(over_rows) * 100) if over_rows else 0)


def add_task():
    task = task_entry.get()
    priority = priority_menu.get()

    if task.strip() == "":
        messagebox.showwarning("Warning", "Task cannot be empty!")
        return

    cursor.execute("""
        INSERT INTO Todo_app (task_name, task_date, priority)
        VALUES (?, ?, ?)
    """, (task, today, priority))

    conn.commit()
    task_entry.delete(0, "end")
    load_tasks()


def delete_completed():
    ids = [tid for tid, var in task_vars.items() if var.get()]

    for tid in ids:
        cursor.execute("DELETE FROM Todo_app WHERE id=?", (tid,))

    conn.commit()
    load_tasks()

# ---------------- UI ---------------- #

app = ctk.CTk()
app.title("Advanced To-Do Manager")
app.geometry("900x700")

ctk.CTkLabel(app, text="Task Manager", font=("Arial", 28, "bold")).pack(pady=10)

# ---------------- INPUT ---------------- #
task_entry = ctk.CTkEntry(app, width=450, placeholder_text="Enter task...")
task_entry.pack(pady=8)

priority_menu = ctk.CTkOptionMenu(app, values=["High", "Medium", "Low"])
priority_menu.set("Medium")
priority_menu.pack(pady=5)

ctk.CTkButton(app, text="Add Task", command=add_task).pack(pady=5)
ctk.CTkButton(app, text="Delete Completed", command=delete_completed).pack(pady=5)

# ---------------- TABS ---------------- #
tabs = CTkTabview(app, width=850, height=500)
tabs.pack(pady=10)

tabs.add("Today")
tabs.add("Tomorrow")
tabs.add("This Month")
tabs.add("Overdue")

today_frame = ctk.CTkScrollableFrame(tabs.tab("Today"))
today_frame.pack(fill="both", expand=True)

tomorrow_frame = ctk.CTkScrollableFrame(tabs.tab("Tomorrow"))
tomorrow_frame.pack(fill="both", expand=True)

month_frame = ctk.CTkScrollableFrame(tabs.tab("This Month"))
month_frame.pack(fill="both", expand=True)

overdue_frame = ctk.CTkScrollableFrame(tabs.tab("Overdue"))
overdue_frame.pack(fill="both", expand=True)

# ---------------- LOAD ---------------- #
load_tasks()

app.mainloop()