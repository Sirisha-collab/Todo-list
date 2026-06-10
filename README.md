**To-Do List App**

A application built with FastAPI and React. Includes task management, overdue task detection, and automatic email reminders.

**Backend Setup**

### Install dependencies

```bash
pip install -r requirements.txt
```

**Environment Variables**

### Create a .env file:

```bash
TODO_EMAIL=your_email@gmail.com
TODO_PASSWORD=your_app_password
````

**Run Backend**
uvicorn main:app --reload

**Email Reminder System**

The application automatically checks overdue tasks every minute. If a task is scheduled for today, is not completed, and no reminder was sent within the last 4 hours, an email reminder will be sent using Gmail SMTP.
