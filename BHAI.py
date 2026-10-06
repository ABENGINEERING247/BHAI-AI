import os
import re
import io
import json
import uuid
import sqlite3
import smtplib
import threading
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st

# ============================================================
# OPTIONAL PACKAGES
# ============================================================

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import dateparser
except ImportError:
    dateparser = None

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.triggers.cron import CronTrigger
except ImportError:
    BackgroundScheduler = None
    DateTrigger = None
    CronTrigger = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
except ImportError:
    SimpleDocTemplate = None


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="BHAI - 20 Agent AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 18px;
        color: #666;
        margin-bottom: 20px;
    }

    .agent-card {
        border: 1px solid #ddd;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 10px;
        background: rgba(128,128,128,0.05);
    }

    .success-box {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #35a853;
        background: rgba(53,168,83,0.08);
    }

    .schedule-box {
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #4285f4;
        background: rgba(66,133,244,0.08);
    }

    .footer {
        text-align: center;
        margin-top: 40px;
        padding: 20px;
        color: #777;
        border-top: 1px solid #ddd;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# AGENTS
# ============================================================

AGENTS = {
    1: {
        "name": "Planner Agent",
        "icon": "🗓️",
        "description": "Plans daily and long-term activities."
    },
    2: {
        "name": "Reminder Agent",
        "icon": "⏰",
        "description": "Creates reminders and alerts."
    },
    3: {
        "name": "Calendar Agent",
        "icon": "📅",
        "description": "Manages calendar events."
    },
    4: {
        "name": "Task Agent",
        "icon": "✅",
        "description": "Creates and manages tasks."
    },
    5: {
        "name": "Productivity Agent",
        "icon": "🚀",
        "description": "Improves productivity and workflows."
    },
    6: {
        "name": "Learning Agent",
        "icon": "📚",
        "description": "Creates learning plans and study schedules."
    },
    7: {
        "name": "Research Agent",
        "icon": "🔬",
        "description": "Performs research and analysis."
    },
    8: {
        "name": "Communication Agent",
        "icon": "💬",
        "description": "Prepares communication and messages."
    },
    9: {
        "name": "Email Agent",
        "icon": "📧",
        "description": "Creates and manages emails."
    },
    10: {
        "name": "Meeting Agent",
        "icon": "🤝",
        "description": "Plans meetings and agendas."
    },
    11: {
        "name": "Health Agent",
        "icon": "❤️",
        "description": "Provides general wellness planning."
    },
    12: {
        "name": "Fitness Agent",
        "icon": "🏃",
        "description": "Creates fitness routines."
    },
    13: {
        "name": "Finance Agent",
        "icon": "💰",
        "description": "Helps organize finance-related tasks."
    },
    14: {
        "name": "Shopping Agent",
        "icon": "🛒",
        "description": "Manages shopping lists."
    },
    15: {
        "name": "Travel Agent",
        "icon": "✈️",
        "description": "Plans travel activities."
    },
    16: {
        "name": "News Agent",
        "icon": "📰",
        "description": "Handles news-related requests."
    },
    17: {
        "name": "Notes Agent",
        "icon": "📝",
        "description": "Creates and organizes notes."
    },
    18: {
        "name": "File Agent",
        "icon": "📁",
        "description": "Creates and manages documents."
    },
    19: {
        "name": "Home Agent",
        "icon": "🏠",
        "description": "Manages home-related routines."
    },
    20: {
        "name": "Entertainment Agent",
        "icon": "🎮",
        "description": "Handles entertainment and games."
    },
    21: {
        "name": "Email Notification Agent",
        "icon": "🔔",
        "description": "Schedules reminders and automatic email notifications."
    }
}


# ============================================================
# KEYWORD ROUTING
# ============================================================

KEYWORD_ROUTING = {

    1: [
        "plan",
        "planning",
        "schedule my day",
        "daily plan",
        "weekly plan"
    ],

    2: [
        "remind",
        "reminder",
        "alert",
        "yaad",
        "yaad dilao"
    ],

    3: [
        "calendar",
        "event",
        "appointment",
        "date"
    ],

    4: [
        "task",
        "todo",
        "to do",
        "kaam"
    ],

    5: [
        "productive",
        "productivity",
        "workflow"
    ],

    6: [
        "learn",
        "learning",
        "study",
        "course",
        "class"
    ],

    7: [
        "research",
        "research paper",
        "literature",
        "analysis"
    ],

    8: [
        "message",
        "communication",
        "whatsapp",
        "sms"
    ],

    9: [
        "email",
        "mail",
        "send email",
        "email kar"
    ],

    10: [
        "meeting",
        "agenda",
        "minutes"
    ],

    11: [
        "health",
        "wellness",
        "medicine"
    ],

    12: [
        "fitness",
        "exercise",
        "workout",
        "gym"
    ],

    13: [
        "finance",
        "money",
        "budget",
        "expense"
    ],

    14: [
        "shopping",
        "buy",
        "purchase",
        "shopping list"
    ],

    15: [
        "travel",
        "trip",
        "flight",
        "hotel"
    ],

    16: [
        "news",
        "latest news"
    ],

    17: [
        "note",
        "notes",
        "remember"
    ],

    18: [
        "file",
        "document",
        "word",
        "pdf"
    ],

    19: [
        "home",
        "house"
    ],

    20: [
        "game",
        "games",
        "entertainment",
        "movie"
    ],

    21: [
        "alarm",
        "notification",
        "notify",
        "automatic email",
        "scheduled email",
        "schedule email",
        "system alarm"
    ]
}


# ============================================================
# DATABASE
# ============================================================

DB_FILE = "bhai_ai.db"

db_lock = threading.Lock()


def get_db():

    conn = sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


def initialize_database():

    with db_lock:

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schedules (
                id TEXT PRIMARY KEY,
                action_type TEXT NOT NULL,
                title TEXT,
                message TEXT,
                recipient TEXT,
                subject TEXT,
                run_at TEXT NOT NULL,
                recurrence TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_run TEXT
            )
            """
        )

        conn.commit()
        conn.close()


initialize_database()


# ============================================================
# DATABASE HELPERS
# ============================================================

def add_contact_db(name, email):

    contact_id = uuid.uuid4().hex[:10]

    with db_lock:

        conn = get_db()

        conn.execute(
            """
            INSERT INTO contacts
            VALUES (?, ?, ?, ?)
            """,
            (
                contact_id,
                name,
                email,
                datetime.now().isoformat()
            )
        )

        conn.commit()
        conn.close()


def get_contacts():

    conn = get_db()

    rows = conn.execute(
        """
        SELECT *
        FROM contacts
        ORDER BY name
        """
    ).fetchall()

    conn.close()

    return rows


def delete_contact(contact_id):

    with db_lock:

        conn = get_db()

        conn.execute(
            "DELETE FROM contacts WHERE id = ?",
            (contact_id,)
        )

        conn.commit()
        conn.close()


def resolve_contact(name_or_email):

    value = name_or_email.lower().strip()

    contacts = get_contacts()

    for contact in contacts:

        if contact["email"].lower() == value:
            return contact["email"]

        if contact["name"].lower() == value:
            return contact["email"]

    for contact in contacts:

        if value in contact["name"].lower():
            return contact["email"]

    return None


# ============================================================
# SCHEDULE DATABASE
# ============================================================

def add_schedule_db(
    action_type,
    title,
    message,
    recipient,
    subject,
    run_at,
    recurrence=None
):

    schedule_id = uuid.uuid4().hex[:10]

    with db_lock:

        conn = get_db()

        conn.execute(
            """
            INSERT INTO schedules
            (
                id,
                action_type,
                title,
                message,
                recipient,
                subject,
                run_at,
                recurrence,
                status,
                created_at,
                last_run
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                schedule_id,
                action_type,
                title,
                message,
                recipient,
                subject,
                run_at.isoformat(),
                recurrence,
                "Scheduled",
                datetime.now().isoformat(),
                None
            )
        )

        conn.commit()
        conn.close()

    return schedule_id


def get_schedules():

    conn = get_db()

    rows = conn.execute(
        """
        SELECT *
        FROM schedules
        ORDER BY run_at
        """
    ).fetchall()

    conn.close()

    return rows


def delete_schedule(schedule_id):

    with db_lock:

        conn = get_db()

        conn.execute(
            """
            UPDATE schedules
            SET status = 'Cancelled'
            WHERE id = ?
            """,
            (schedule_id,)
        )

        conn.commit()
        conn.close()


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "chat_messages": [],
    "last_agents": [],
    "last_results": [],
    "generated_emails": [],
    "generated_document_content": "",
    "document_title": "BHAI AI Document",
    "document_author": "Engr. Bilal Mehmood",
    "manual_api_key": "",
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# OPENAI API
# ============================================================

def get_api_key():

    key = ""

    try:
        key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        pass

    if not key:

        key = os.getenv(
            "OPENAI_API_KEY",
            ""
        )

    if not key:

        key = st.session_state.get(
            "manual_api_key",
            ""
        )

    return key.strip()


def call_openai(
    prompt,
    model="gpt-5",
    system_instruction=None
):

    if OpenAI is None:

        return (
            "OpenAI package is not installed. "
            "Run: pip install openai"
        )

    api_key = get_api_key()

    if not api_key:

        return (
            "OpenAI API key is not configured. "
            "Please use Demo Mode or enter your API key."
        )

    try:

        client = OpenAI(
            api_key=api_key
        )

        response = client.responses.create(

            model=model,

            instructions=system_instruction
            or
            """
            You are BHAI, a master AI assistant.
            You coordinate specialist agents.
            Be practical, concise and helpful.
            """,

            input=prompt
        )

        return response.output_text

    except Exception as e:

        return f"OpenAI API Error: {e}"


# ============================================================
# ROMAN URDU NORMALIZATION
# ============================================================

def normalize_roman_urdu(text):

    result = text

    replacements = {

        r"\baaj\b": "today",

        r"\baj\b": "today",

        r"\bkal\b": "tomorrow",

        r"\bparson\b": "in 2 days",

        r"\bsubah\b": "AM",

        r"\bsawere\b": "AM",

        r"\bsavera\b": "AM",

        r"\bdopahar\b": "PM",

        r"\bdupehar\b": "PM",

        r"\bshaam\b": "PM",

        r"\bsham\b": "PM",

        r"\braat\b": "PM",

        r"\bbaje\b": "",

        r"\bbajay\b": "",

    }

    for pattern, replacement in replacements.items():

        result = re.sub(
            pattern,
            replacement,
            result,
            flags=re.IGNORECASE
        )

    return result


# ============================================================
# TIME / DATE PARSER
# ============================================================

def parse_schedule_from_text(text):

    original = text

    normalized = normalize_roman_urdu(text)

    now = datetime.now()

    run_at = None

    recurrence = None

    # --------------------------------------------------------
    # RECURRENCE
    # --------------------------------------------------------

    lower = normalized.lower()

    if re.search(
        r"\b(every day|daily|har roz|roz)\b",
        lower
    ):
        recurrence = "daily"

    weekdays = {
        "monday": "mon",
        "tuesday": "tue",
        "wednesday": "wed",
        "thursday": "thu",
        "friday": "fri",
        "saturday": "sat",
        "sunday": "sun"
    }

    for day, short_day in weekdays.items():

        if re.search(
            rf"\b(every|har)\s+{day}\b",
            lower
        ):

            recurrence = f"weekly:{short_day}"

    # --------------------------------------------------------
    # EXPLICIT TIME
    # --------------------------------------------------------

    time_patterns = [

        r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b",

        r"\b(\d{1,2})\s*(am|pm)\b",

        r"\bat\s+(\d{1,2})(?::(\d{2}))?\b",

        r"\b(\d{1,2})\s*(?:baje|bajay)\b"

    ]

    time_match = None

    for pattern in time_patterns:

        match = re.search(
            pattern,
            normalized,
            flags=re.IGNORECASE
        )

        if match:

            time_match = match
            break

    # --------------------------------------------------------
    # DATEPARSER
    # --------------------------------------------------------

    if dateparser:

        try:

            settings = {

                "PREFER_DATES_FROM": "future",

                "RELATIVE_BASE": now,

                "RETURN_AS_TIMEZONE_AWARE": False

            }

            parsed = dateparser.parse(
                normalized,
                settings=settings
            )

            if parsed:

                run_at = parsed

        except Exception:

            run_at = None

    # --------------------------------------------------------
    # MANUAL TIME FIX
    # --------------------------------------------------------

    if time_match:

        groups = time_match.groups()

        hour = int(groups[0])

        minute = 0

        ampm = None

        if len(groups) >= 2 and groups[1]:

            try:
                minute = int(groups[1])
            except:
                pass

        if len(groups) >= 3:

            ampm = groups[2]

        if ampm:

            ampm = ampm.lower()

            if ampm == "pm" and hour < 12:
                hour += 12

            if ampm == "am" and hour == 12:
                hour = 0

        # For Roman Urdu "5 baje", assume PM for common
        # working/evening language when no AM/PM is given.
        elif re.search(
            r"\b(shaam|sham|raat|dopahar)\b",
            original,
            re.IGNORECASE
        ):

            if hour < 12:
                hour += 12

        # "subah 9 baje"
        elif re.search(
            r"\b(subah|sawere|savera)\b",
            original,
            re.IGNORECASE
        ):

            if hour == 12:
                hour = 0

        # If dateparser produced a date, preserve its date.
        if run_at:

            run_at = run_at.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0
            )

        else:

            run_at = now.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0
            )

            if run_at <= now:

                run_at += timedelta(days=1)

    # --------------------------------------------------------
    # IF ONLY DATE WAS FOUND
    # --------------------------------------------------------

    if run_at:

        if run_at <= now and recurrence is None:

            run_at += timedelta(days=1)

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {
        "scheduled": run_at is not None,
        "run_at": run_at,
        "recurrence": recurrence,
        "original_text": original,
        "normalized_text": normalized
    }


# ============================================================
# ROUTER
# ============================================================

def bhai_demo_router(text):

    text_lower = text.lower()

    scores = {}

    for agent_id, keywords in KEYWORD_ROUTING.items():

        score = 0

        for keyword in keywords:

            if keyword.lower() in text_lower:

                score += 1

        if score > 0:

            scores[agent_id] = score

    # Scheduler gets priority if time/schedule is present
    schedule = parse_schedule_from_text(text)

    if schedule["scheduled"]:

        scores[21] = scores.get(21, 0) + 5

    if not scores:

        return [1, 4, 5]

    ranked = sorted(
        scores,
        key=scores.get,
        reverse=True
    )

    return ranked[:5]


def bhai_api_router(
    text,
    model
):

    prompt = f"""
You are the routing brain of BHAI.

Available agents:

1 Planner
2 Reminder
3 Calendar
4 Task
5 Productivity
6 Learning
7 Research
8 Communication
9 Email
10 Meeting
11 Health
12 Fitness
13 Finance
14 Shopping
15 Travel
16 News
17 Notes
18 File
19 Home
20 Entertainment
21 Email Notification / Scheduler

User request:

{text}

Return ONLY a JSON array of agent numbers.

Example:

[21, 9]

Choose only relevant agents.
"""

    result = call_openai(
        prompt,
        model=model
    )

    try:

        match = re.search(
            r"\[[^\]]+\]",
            result
        )

        if match:

            data = json.loads(
                match.group(0)
            )

            if isinstance(data, list):

                return [
                    int(x)
                    for x in data
                    if int(x) in AGENTS
                ][:5]

    except Exception:
        pass

    return bhai_demo_router(text)


# ============================================================
# DEMO AGENT
# ============================================================

def run_demo_agent(
    agent_id,
    user_text
):

    agent = AGENTS[agent_id]

    if agent_id == 21:

        schedule = parse_schedule_from_text(
            user_text
        )

        if schedule["scheduled"]:

            return (
                f"🔔 Scheduler detected a date/time: "
                f"{schedule['run_at'].strftime('%d-%m-%Y %I:%M %p')}"
            )

        return (
            "🔔 Email Notification Agent is ready "
            "to schedule reminders and emails."
        )

    responses = {

        1:
            "I can convert your request into a practical daily or weekly plan.",

        2:
            "Reminder Agent can create a reminder for the requested activity.",

        3:
            "Calendar Agent can organize the requested event or appointment.",

        4:
            "Task Agent can convert your request into an actionable task.",

        5:
            "Productivity Agent can optimize your workflow.",

        6:
            "Learning Agent can prepare a learning or study plan.",

        7:
            "Research Agent can structure the required research activity.",

        8:
            "Communication Agent can prepare your message.",

        9:
            "Email Agent can prepare a professional email.",

        10:
            "Meeting Agent can prepare the meeting agenda and action points.",

        11:
            "Health Agent can organize general wellness activities.",

        12:
            "Fitness Agent can prepare a workout routine.",

        13:
            "Finance Agent can organize your finance-related activity.",

        14:
            "Shopping Agent can prepare your shopping list.",

        15:
            "Travel Agent can organize your travel plan.",

        16:
            "News Agent can organize a news-related request.",

        17:
            "Notes Agent can save and organize your notes.",

        18:
            "File Agent can prepare documents and files.",

        19:
            "Home Agent can organize home-related activities.",

        20:
            "Entertainment Agent can suggest games and entertainment."
    }

    return responses.get(
        agent_id,
        f"{agent['name']} processed the request."
    )


# ============================================================
# API AGENT
# ============================================================

def run_api_agent(
    agent_id,
    user_text,
    model
):

    agent = AGENTS[agent_id]

    system_prompt = f"""
You are the {agent['name']} of BHAI AI.

Your role:
{agent['description']}

Provide a useful, practical response.
"""

    return call_openai(
        user_text,
        model=model,
        system_instruction=system_prompt
    )


# ============================================================
# EMAIL SENDER
# ============================================================

def get_smtp_settings():

    try:

        host = st.secrets.get(
            "SMTP_HOST",
            "smtp.gmail.com"
        )

        port = int(
            st.secrets.get(
                "SMTP_PORT",
                587
            )
        )

        username = st.secrets.get(
            "SMTP_USERNAME",
            ""
        )

        password = st.secrets.get(
            "SMTP_PASSWORD",
            ""
        )

        return host, port, username, password

    except Exception:

        return (
            "smtp.gmail.com",
            587,
            "",
            ""
        )


def send_email(
    recipient,
    subject,
    body
):

    host, port, username, password = (
        get_smtp_settings()
    )

    if not username or not password:

        return (
            False,
            "SMTP credentials are not configured."
        )

    try:

        msg = MIMEMultipart()

        msg["From"] = username

        msg["To"] = recipient

        msg["Subject"] = subject

        msg.attach(
            MIMEText(
                body,
                "plain",
                "utf-8"
            )
        )

        server = smtplib.SMTP(
            host,
            port,
            timeout=30
        )

        server.starttls()

        server.login(
            username,
            password
        )

        server.sendmail(
            username,
            recipient,
            msg.as_string()
        )

        server.quit()

        return (
            True,
            "Email sent successfully."
        )

    except Exception as e:

        return (
            False,
            f"Email sending failed: {e}"
        )


# ============================================================
# SCHEDULE EXECUTION
# ============================================================

def execute_scheduled_action(
    schedule_id
):

    conn = get_db()

    row = conn.execute(
        """
        SELECT *
        FROM schedules
        WHERE id = ?
        """,
        (schedule_id,)
    ).fetchone()

    conn.close()

    if not row:
        return

    if row["status"] != "Scheduled":
        return

    action_type = row["action_type"]

    success = False

    message = ""

    # --------------------------------------------------------
    # EMAIL
    # --------------------------------------------------------

    if action_type == "email":

        success, message = send_email(
            row["recipient"],
            row["subject"] or "BHAI Notification",
            row["message"] or ""
        )

    # --------------------------------------------------------
    # REMINDER
    # --------------------------------------------------------

    elif action_type in (
        "reminder",
        "task",
        "notification"
    ):

        # Email notification if recipient exists
        if row["recipient"]:

            success, message = send_email(
                row["recipient"],
                row["subject"] or "BHAI Reminder",
                row["message"] or row["title"] or ""
            )

        else:

            success = True

            message = (
                "Reminder triggered inside BHAI."
            )

    # --------------------------------------------------------
    # UPDATE DATABASE
    # --------------------------------------------------------

    with db_lock:

        conn = get_db()

        if success:

            conn.execute(
                """
                UPDATE schedules
                SET
                    status = ?,
                    last_run = ?
                WHERE id = ?
                """,
                (
                    "Completed",
                    datetime.now().isoformat(),
                    schedule_id
                )
            )

        else:

            conn.execute(
                """
                UPDATE schedules
                SET
                    last_run = ?
                WHERE id = ?
                """,
                (
                    datetime.now().isoformat(),
                    schedule_id
                )
            )

        conn.commit()

        conn.close()


# ============================================================
# APSCHEDULER
# ============================================================

@st.cache_resource
def get_scheduler():

    if BackgroundScheduler is None:

        return None

    scheduler = BackgroundScheduler(
        timezone="Asia/Karachi"
    )

    scheduler.start()

    return scheduler


def register_schedule_with_scheduler(
    schedule_id,
    run_at,
    recurrence=None
):

    scheduler = get_scheduler()

    if scheduler is None:
        return False

    try:

        if recurrence == "daily":

            scheduler.add_job(
                execute_scheduled_action,
                CronTrigger(
                    hour=run_at.hour,
                    minute=run_at.minute,
                    timezone="Asia/Karachi"
                ),
                args=[schedule_id],
                id=schedule_id,
                replace_existing=True
            )

        elif recurrence and recurrence.startswith(
            "weekly:"
        ):

            weekday = recurrence.split(":")[1]

            scheduler.add_job(
                execute_scheduled_action,
                CronTrigger(
                    day_of_week=weekday,
                    hour=run_at.hour,
                    minute=run_at.minute,
                    timezone="Asia/Karachi"
                ),
                args=[schedule_id],
                id=schedule_id,
                replace_existing=True
            )

        else:

            scheduler.add_job(
                execute_scheduled_action,
                DateTrigger(
                    run_date=run_at,
                    timezone="Asia/Karachi"
                ),
                args=[schedule_id],
                id=schedule_id,
                replace_existing=True
            )

        return True

    except Exception:

        return False


def restore_schedules():

    scheduler = get_scheduler()

    if scheduler is None:
        return

    rows = get_schedules()

    for row in rows:

        if row["status"] != "Scheduled":
            continue

        try:

            run_at = datetime.fromisoformat(
                row["run_at"]
            )

            if row["recurrence"] is None:

                if run_at <= datetime.now():

                    continue

            register_schedule_with_scheduler(
                row["id"],
                run_at,
                row["recurrence"]
            )

        except Exception:
            pass


restore_schedules()


# ============================================================
# CREATE AUTOMATIC SCHEDULE
# ============================================================

def create_automatic_schedule(
    user_text,
    action_type="notification",
    title=None,
    message=None,
    recipient=None,
    subject=None
):

    parsed = parse_schedule_from_text(
        user_text
    )

    if not parsed["scheduled"]:

        return {
            "success": False,
            "message": "No date/time detected."
        }

    run_at = parsed["run_at"]

    # --------------------------------------------------------
    # CONTACT RESOLUTION
    # --------------------------------------------------------

    if recipient:

        resolved = resolve_contact(
            recipient
        )

        if resolved:

            recipient = resolved

    # --------------------------------------------------------
    # CREATE DB RECORD
    # --------------------------------------------------------

    schedule_id = add_schedule_db(

        action_type=action_type,

        title=title
        or
        "BHAI Scheduled Task",

        message=message
        or
        user_text,

        recipient=recipient
        or
        "",

        subject=subject
        or
        "BHAI Notification",

        run_at=run_at,

        recurrence=parsed["recurrence"]
    )

    # --------------------------------------------------------
    # REGISTER
    # --------------------------------------------------------

    registered = register_schedule_with_scheduler(

        schedule_id,

        run_at,

        parsed["recurrence"]
    )

    return {

        "success": True,

        "schedule_id": schedule_id,

        "run_at": run_at,

        "recurrence": parsed["recurrence"],

        "registered": registered
    }


# ============================================================
# NATURAL LANGUAGE EMAIL DETECTION
# ============================================================

def extract_recipient_from_text(text):

    # First try direct email address

    email_match = re.search(
        r"[\w\.-]+@[\w\.-]+\.\w+",
        text
    )

    if email_match:

        return email_match.group(0)

    # Search contact names
    contacts = get_contacts()

    lower = text.lower()

    for contact in contacts:

        if contact["name"].lower() in lower:

            return contact["email"]

    return None


def looks_like_email_request(text):

    lower = text.lower()

    email_words = [

        "email",

        "e-mail",

        "mail",

        "email kar",

        "send email",

        "email bhej",

        "mail bhej",

        "email send"

    ]

    return any(
        word in lower
        for word in email_words
    )


# ============================================================
# MASTER PROCESSOR
# ============================================================

def process_bhai_chat(
    user_text,
    mode,
    model
):

    schedule = parse_schedule_from_text(
        user_text
    )

    # --------------------------------------------------------
    # ROUTING
    # --------------------------------------------------------

    if mode == "API Mode":

        agent_ids = bhai_api_router(
            user_text,
            model
        )

    else:

        agent_ids = bhai_demo_router(
            user_text
        )

    # --------------------------------------------------------
    # AUTOMATIC SCHEDULING
    # --------------------------------------------------------

    if schedule["scheduled"]:

        recipient = extract_recipient_from_text(
            user_text
        )

        is_email = looks_like_email_request(
            user_text
        )

        if is_email:

            result = create_automatic_schedule(

                user_text=user_text,

                action_type="email",

                title="Scheduled Email",

                message=user_text,

                recipient=recipient,

                subject="BHAI Scheduled Email"
            )

        else:

            result = create_automatic_schedule(

                user_text=user_text,

                action_type="reminder",

                title="Scheduled Reminder",

                message=user_text,

                recipient=recipient,

                subject="BHAI Reminder"
            )

        # Add scheduler agent
        if 21 not in agent_ids:

            agent_ids.insert(
                0,
                21
            )

    # --------------------------------------------------------
    # EXECUTE AGENTS
    # --------------------------------------------------------

    results = []

    for agent_id in agent_ids:

        if mode == "API Mode":

            output = run_api_agent(
                agent_id,
                user_text,
                model
            )

        else:

            output = run_demo_agent(
                agent_id,
                user_text
            )

        results.append(
            {
                "agent_id": agent_id,
                "agent": AGENTS[agent_id]["name"],
                "output": output
            }
        )

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    summary_parts = []

    summary_parts.append(
        f"BHAI activated {len(agent_ids)} agent(s)."
    )

    if schedule["scheduled"]:

        scheduled_time = schedule["run_at"].strftime(
            "%d %B %Y at %I:%M %p"
        )

        recurrence_text = ""

        if schedule["recurrence"]:

            recurrence_text = (
                f" | Recurrence: "
                f"{schedule['recurrence']}"
            )

        summary_parts.append(
            f"⏰ Automatically scheduled for "
            f"{scheduled_time}{recurrence_text}."
        )

        if looks_like_email_request(
            user_text
        ):

            if extract_recipient_from_text(
                user_text
            ):

                summary_parts.append(
                    "📧 Recipient was detected from Contacts/email."
                )

            else:

                summary_parts.append(
                    "⚠️ No recipient email was detected. "
                    "Add the recipient in Contacts."
                )

    else:

        summary_parts.append(
            "No explicit date/time was detected, "
            "so no automatic schedule was created."
        )

    return (
        agent_ids,
        results,
        "\n\n".join(summary_parts)
    )


# ============================================================
# EMAIL GENERATOR
# ============================================================

def generate_email(
    purpose,
    recipient_name,
    tone,
    model,
    mode
):

    prompt = f"""
Create a professional email.

Purpose:
{purpose}

Recipient:
{recipient_name}

Tone:
{tone}

Include:
- Subject
- Greeting
- Clear body
- Professional closing

Return the complete email.
"""

    if mode == "API Mode":

        result = call_openai(
            prompt,
            model=model
        )

    else:

        result = f"""
Subject: {purpose}

Dear {recipient_name},

I hope you are doing well.

I am writing regarding {purpose}.

Kindly consider the above request and let me know if
any further information is required.

Thank you for your time and consideration.

Best regards,

Engr. Bilal Mehmood
AI Course Director
PITAC Regional Center Karachi, Sindh
"""

    st.session_state.generated_emails.append(
        result
    )

    return result


# ============================================================
# WORD DOCUMENT
# ============================================================

def create_word_document(
    title,
    content,
    author
):

    if Document is None:

        return None

    document = Document()

    document.add_heading(
        title,
        level=0
    )

    document.add_paragraph(
        f"Author: {author}"
    )

    document.add_paragraph(
        f"Date: {datetime.now().strftime('%d %B %Y')}"
    )

    document.add_paragraph("")

    for paragraph in content.split("\n"):

        document.add_paragraph(
            paragraph
        )

    output = io.BytesIO()

    document.save(
        output
    )

    output.seek(0)

    return output


# ============================================================
# PDF DOCUMENT
# ============================================================

def create_pdf_document(
    title,
    content,
    author
):

    if SimpleDocTemplate is None:

        return None

    output = io.BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            title,
            styles["Title"]
        )
    )

    story.append(
        Spacer(
            1,
            12
        )
    )

    story.append(
        Paragraph(
            f"Author: {author}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            datetime.now().strftime(
                "%d %B %Y"
            ),
            styles["Normal"]
        )
    )

    story.append(
        Spacer(
            1,
            20
        )
    )

    for line in content.split("\n"):

        if line.strip():

            story.append(
                Paragraph(
                    line.replace(
                        "&",
                        "&amp;"
                    ),
                    styles["BodyText"]
                )
            )

            story.append(
                Spacer(
                    1,
                    6
                )
            )

    document.build(
        story
    )

    output.seek(0)

    return output


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "# 🤖 BHAI AI"
    )

    st.caption(
        "20-Agent Intelligent Daily Routine Automation System"
    )

    st.divider()

    mode = st.radio(
        "Operating Mode",
        [
            "Demo Mode",
            "API Mode"
        ]
    )

    model = st.text_input(
        "OpenAI Model",
        value="gpt-5"
    )

    if mode == "API Mode":

        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.manual_api_key
        )

        st.session_state.manual_api_key = api_key

    st.divider()

    st.markdown(
        "### 🧭 Navigation"
    )

    page = st.radio(
        "Select Page",
        [
            "Dashboard",
            "BHAI Master",
            "BHAI Chatbot",
            "Agent Navigation",
            "Reminders & Schedules",
            "Contacts",
            "Email Generator",
            "Word/PDF Generator"
        ]
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🤖 BHAI AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Master Agent for Intelligent Daily Routine Automation</div>',
    unsafe_allow_html=True
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.header(
        "📊 BHAI AI Dashboard"
    )

    schedules = get_schedules()

    contacts = get_contacts()

    active_schedules = [
        x for x in schedules
        if x["status"] == "Scheduled"
    ]

    completed_schedules = [
        x for x in schedules
        if x["status"] == "Completed"
    ]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "AI Agents",
        "20"
    )

    col2.metric(
        "Scheduled",
        len(active_schedules)
    )

    col3.metric(
        "Contacts",
        len(contacts)
    )

    col4.metric(
        "Completed",
        len(completed_schedules)
    )

    st.divider()

    st.subheader(
        "🧠 How BHAI Works"
    )

    st.markdown(
        """
        **User Command → BHAI Master → Intent Detection → Agent Routing → Date/Time Detection → Scheduler → Action**

        Example:

        `Kal 10 baje Director ko AI workshop proposal email kar dena.`

        BHAI automatically detects:

        - 📧 Email requirement
        - 👤 Recipient
        - 📅 Tomorrow
        - ⏰ 10:00 AM
        - 🔔 Scheduler Agent
        - 📤 Email action
        """
    )

    st.info(
        "Tip: Save your contacts first. Then you can simply mention a person's name in your command."
    )


# ============================================================
# BHAI MASTER
# ============================================================

elif page == "BHAI Master":

    st.header(
        "🧠 BHAI Master Agent"
    )

    st.write(
        "Give BHAI any task. If you mention a date/time, BHAI will automatically create a schedule."
    )

    examples = [
        "Kal 10 baje Director ko AI workshop proposal email kar dena.",
        "Aaj 5 PM par mujhe Python class yaad dilana.",
        "15 October ko 2 PM par Director ko workshop proposal send karna.",
        "Har Monday 9 AM par weekly meeting ka reminder email bhejna.",
        "Tomorrow at 11 AM prepare my daily plan."
    ]

    st.subheader(
        "💡 Example Commands"
    )

    for example in examples:

        st.code(
            example
        )

    st.divider()

    user_command = st.text_area(
        "Enter command for BHAI",
        height=130,
        placeholder="Example: Kal 10 baje Director ko email kar dena."
    )

    if st.button(
        "🚀 Execute BHAI",
        type="primary"
    ):

        if not user_command.strip():

            st.warning(
                "Please enter a command."
            )

        else:

            with st.spinner(
                "BHAI is processing..."
            ):

                agent_ids, results, summary = (
                    process_bhai_chat(
                        user_command,
                        mode,
                        model
                    )
                )

            st.session_state.last_agents = agent_ids

            st.session_state.last_results = results

            st.success(
                "BHAI command processed successfully."
            )

            st.markdown(
                "### 🧠 BHAI Summary"
            )

            st.info(
                summary
            )

            st.markdown(
                "### 🤖 Activated Agents"
            )

            for agent_id in agent_ids:

                st.write(
                    f"{AGENTS[agent_id]['icon']} "
                    f"**{AGENTS[agent_id]['name']}**"
                )

            st.markdown(
                "### 📋 Agent Results"
            )

            for result in results:

                with st.expander(
                    f"{AGENTS[result['agent_id']]['icon']} "
                    f"{result['agent']}"
                ):

                    st.write(
                        result["output"]
                    )


# ============================================================
# BHAI CHATBOT
# ============================================================

elif page == "BHAI Chatbot":

    st.header(
        "💬 BHAI Chatbot"
    )

    st.caption(
        "Chat naturally with BHAI. Time mentioned in your message is automatically scheduled."
    )

    for message in st.session_state.chat_messages:

        if message["role"] == "user":

            st.chat_message(
                "user"
            ).write(
                message["content"]
            )

        else:

            st.chat_message(
                "assistant"
            ).write(
                message["content"]
            )

    prompt = st.chat_input(
        "Ask BHAI anything..."
    )

    if prompt:

        st.session_state.chat_messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        agent_ids, results, summary = (
            process_bhai_chat(
                prompt,
                mode,
                model
            )
        )

        response_text = summary

        if results:

            response_text += "\n\n"

            for result in results:

                response_text += (
                    f"{AGENTS[result['agent_id']]['icon']} "
                    f"**{result['agent']}**: "
                    f"{result['output']}\n\n"
                )

        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": response_text
            }
        )

        st.rerun()


# ============================================================
# AGENT NAVIGATION
# ============================================================

elif page == "Agent Navigation":

    st.header(
        "🧭 Agent Navigation"
    )

    st.write(
        "Select any specialist agent."
    )

    cols = st.columns(3)

    for index, agent_id in enumerate(AGENTS):

        agent = AGENTS[agent_id]

        with cols[index % 3]:

            st.markdown(
                f"""
                <div class="agent-card">

                <h3>
                {agent['icon']} {agent['name']}
                </h3>

                <p>
                {agent['description']}
                </p>

                </div>
                """,
                unsafe_allow_html=True
            )

            with st.expander(
                "Open Agent"
            ):

                agent_prompt = st.text_area(
                    f"Task for {agent['name']}",
                    key=f"agent_prompt_{agent_id}",
                    height=100
                )

                if st.button(
                    f"Run {agent['name']}",
                    key=f"run_agent_{agent_id}"
                ):

                    if mode == "API Mode":

                        result = run_api_agent(
                            agent_id,
                            agent_prompt,
                            model
                        )

                    else:

                        result = run_demo_agent(
                            agent_id,
                            agent_prompt
                        )

                    st.success(
                        "Agent executed."
                    )

                    st.write(
                        result
                    )


# ============================================================
# REMINDERS & SCHEDULES
# ============================================================

elif page == "Reminders & Schedules":

    st.header(
        "⏰ Reminders & Automatic Schedules"
    )

    st.info(
        "BHAI automatically creates a schedule when you mention a date/time in your command."
    )

    st.subheader(
        "➕ Manual Schedule"
    )

    with st.form(
        "manual_schedule_form"
    ):

        title = st.text_input(
            "Task / Reminder Title"
        )

        message = st.text_area(
            "Message"
        )

        schedule_date = st.date_input(
            "Date",
            value=datetime.now().date()
        )

        schedule_time = st.time_input(
            "Time"
        )

        action_type = st.selectbox(
            "Action",
            [
                "reminder",
                "task",
                "email",
                "notification"
            ]
        )

        recipient = st.text_input(
            "Recipient Email (optional)"
        )

        subject = st.text_input(
            "Email Subject"
        )

        recurrence = st.selectbox(
            "Repeat",
            [
                "None",
                "Daily",
                "Every Monday",
                "Every Tuesday",
                "Every Wednesday",
                "Every Thursday",
                "Every Friday",
                "Every Saturday",
                "Every Sunday"
            ]
        )

        submit = st.form_submit_button(
            "🔔 Schedule"
        )

    if submit:

        run_at = datetime.combine(
            schedule_date,
            schedule_time
        )

        recurrence_value = None

        if recurrence == "Daily":

            recurrence_value = "daily"

        elif recurrence.startswith(
            "Every "
        ):

            day = recurrence.replace(
                "Every ",
                ""
            ).lower()

            recurrence_value = (
                "weekly:"
                + day[:3]
            )

        schedule_id = add_schedule_db(

            action_type=action_type,

            title=title,

            message=message,

            recipient=recipient,

            subject=subject,

            run_at=run_at,

            recurrence=recurrence_value
        )

        register_schedule_with_scheduler(
            schedule_id,
            run_at,
            recurrence_value
        )

        st.success(
            f"Scheduled successfully for {run_at.strftime('%d %B %Y %I:%M %p')}"
        )

    st.divider()

    st.subheader(
        "📋 Existing Schedules"
    )

    schedules = get_schedules()

    if not schedules:

        st.info(
            "No schedules found."
        )

    else:

        for schedule in schedules:

            with st.container(border=True):

                col1, col2, col3 = st.columns(
                    [4, 3, 1]
                )

                with col1:

                    st.markdown(
                        f"### {schedule['title']}"
                    )

                    st.write(
                        schedule["message"]
                    )

                with col2:

                    st.write(
                        f"**Run:** {schedule['run_at']}"
                    )

                    st.write(
                        f"**Type:** {schedule['action_type']}"
                    )

                    st.write(
                        f"**Status:** {schedule['status']}"
                    )

                    if schedule["recurrence"]:

                        st.write(
                            f"**Repeat:** {schedule['recurrence']}"
                        )

                with col3:

                    if schedule["status"] == "Scheduled":

                        if st.button(
                            "Cancel",
                            key=f"cancel_{schedule['id']}"
                        ):

                            delete_schedule(
                                schedule["id"]
                            )

                            st.rerun()


# ============================================================
# CONTACTS
# ============================================================

elif page == "Contacts":

    st.header(
        "👤 BHAI Contacts"
    )

    st.write(
        "Save recipient names and email addresses. BHAI can then detect the recipient from natural language."
    )

    with st.form(
        "contact_form"
    ):

        contact_name = st.text_input(
            "Contact Name",
            placeholder="Director"
        )

        contact_email = st.text_input(
            "Email Address",
            placeholder="director@example.com"
        )

        save_contact = st.form_submit_button(
            "💾 Save Contact"
        )

    if save_contact:

        if not contact_name or not contact_email:

            st.warning(
                "Please enter both name and email."
            )

        elif "@" not in contact_email:

            st.warning(
                "Please enter a valid email address."
            )

        else:

            add_contact_db(
                contact_name,
                contact_email
            )

            st.success(
                "Contact saved successfully."
            )

            st.rerun()

    st.divider()

    st.subheader(
        "📋 Saved Contacts"
    )

    contacts = get_contacts()

    if not contacts:

        st.info(
            "No contacts saved."
        )

    else:

        for contact in contacts:

            col1, col2, col3 = st.columns(
                [3, 5, 1]
            )

            with col1:

                st.write(
                    f"👤 **{contact['name']}**"
                )

            with col2:

                st.write(
                    contact["email"]
                )

            with col3:

                if st.button(
                    "Delete",
                    key=f"delete_contact_{contact['id']}"
                ):

                    delete_contact(
                        contact["id"]
                    )

                    st.rerun()


# ============================================================
# EMAIL GENERATOR
# ============================================================

elif page == "Email Generator":

    st.header(
        "📧 Email Generator"
    )

    purpose = st.text_area(
        "Email Purpose",
        placeholder="Request approval for AI workshop"
    )

    recipient_name = st.text_input(
        "Recipient Name",
        placeholder="Director"
    )

    tone = st.selectbox(
        "Tone",
        [
            "Professional",
            "Formal",
            "Friendly",
            "Short and Direct"
        ]
    )

    if st.button(
        "Generate Email",
        type="primary"
    ):

        if purpose.strip():

            email = generate_email(
                purpose,
                recipient_name,
                tone,
                model,
                mode
            )

            st.text_area(
                "Generated Email",
                email,
                height=350
            )

        else:

            st.warning(
                "Please enter the email purpose."
            )


# ============================================================
# WORD / PDF GENERATOR
# ============================================================

elif page == "Word/PDF Generator":

    st.header(
        "📄 Word & PDF Generator"
    )

    title = st.text_input(
        "Document Title",
        value="BHAI AI Document"
    )

    author = st.text_input(
        "Author",
        value="Engr. Bilal Mehmood"
    )

    content = st.text_area(
        "Document Content",
        height=400
    )

    if st.button(
        "Generate Document Files"
    ):

        if not content.strip():

            st.warning(
                "Please enter document content."
            )

        else:

            word_file = create_word_document(
                title,
                content,
                author
            )

            pdf_file = create_pdf_document(
                title,
                content,
                author
            )

            col1, col2 = st.columns(2)

            with col1:

                if word_file:

                    st.download_button(
                        "⬇️ Download Word",
                        data=word_file,
                        file_name="bhai_document.docx",
                        mime=(
                            "application/vnd.openxmlformats-officedocument."
                            "wordprocessingml.document"
                        )
                    )

            with col2:

                if pdf_file:

                    st.download_button(
                        "⬇️ Download PDF",
                        data=pdf_file,
                        file_name="bhai_document.pdf",
                        mime="application/pdf"
                    )


# ============================================================
# LAST EXECUTION
# ============================================================

if st.session_state.last_agents:

    with st.expander(
        "🧠 Last BHAI Execution"
    ):

        st.write(
            "Activated Agents:"
        )

        for agent_id in st.session_state.last_agents:

            st.write(
                f"{AGENTS[agent_id]['icon']} "
                f"{AGENTS[agent_id]['name']}"
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">

    <b>🤖 BHAI AI</b><br>

    20-Agent Intelligent Daily Routine Automation System<br>

    OpenAI API Mode • Demo Mode • Automatic Scheduler • Email Notification<br><br>

    <b>By Engr. Bilal Mehmood</b>

    </div>
    """,
    unsafe_allow_html=True
)
