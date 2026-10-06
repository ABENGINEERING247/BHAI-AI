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
# OPTIONAL LIBRARIES
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
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer
    )
    from reportlab.lib.styles import getSampleStyleSheet
except ImportError:
    SimpleDocTemplate = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="BHAI AI - 20 Agent AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 18px;
        color: #777;
        margin-bottom: 20px;
    }

    .agent-card {
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 15px;
        padding: 18px;
        margin-bottom: 12px;
        background: rgba(128,128,128,0.04);
    }

    .agent-header {
        font-size: 30px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .agent-description {
        color: #777;
        font-size: 15px;
    }

    .schedule-box {
        border: 1px solid #4285f4;
        border-radius: 12px;
        padding: 16px;
        background: rgba(66,133,244,0.08);
    }

    .success-box {
        border: 1px solid #34a853;
        border-radius: 12px;
        padding: 16px;
        background: rgba(52,168,83,0.08);
    }

    .footer {
        text-align: center;
        margin-top: 50px;
        padding: 25px;
        color: #777;
        border-top: 1px solid rgba(128,128,128,0.25);
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
        "description": "Plans daily, weekly and long-term activities."
    },

    2: {
        "name": "Reminder Agent",
        "icon": "⏰",
        "description": "Creates reminders and alerts."
    },

    3: {
        "name": "Calendar Agent",
        "icon": "📅",
        "description": "Manages appointments, events and calendar activities."
    },

    4: {
        "name": "Task Agent",
        "icon": "✅",
        "description": "Creates and manages actionable tasks."
    },

    5: {
        "name": "Productivity Agent",
        "icon": "🚀",
        "description": "Improves productivity and work processes."
    },

    6: {
        "name": "Learning Agent",
        "icon": "📚",
        "description": "Creates study plans, courses and learning schedules."
    },

    7: {
        "name": "Research Agent",
        "icon": "🔬",
        "description": "Supports research, analysis and information organization."
    },

    8: {
        "name": "Communication Agent",
        "icon": "💬",
        "description": "Prepares messages and communication."
    },

    9: {
        "name": "Email Agent",
        "icon": "📧",
        "description": "Creates professional emails."
    },

    10: {
        "name": "Meeting Agent",
        "icon": "🤝",
        "description": "Plans meetings, agendas and action points."
    },

    11: {
        "name": "Health Agent",
        "icon": "❤️",
        "description": "Helps organize general health and wellness routines."
    },

    12: {
        "name": "Fitness Agent",
        "icon": "🏃",
        "description": "Creates exercise and fitness plans."
    },

    13: {
        "name": "Finance Agent",
        "icon": "💰",
        "description": "Organizes budgets, expenses and financial tasks."
    },

    14: {
        "name": "Shopping Agent",
        "icon": "🛒",
        "description": "Creates and manages shopping lists."
    },

    15: {
        "name": "Travel Agent",
        "icon": "✈️",
        "description": "Plans trips, travel schedules and activities."
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
        "description": "Works with documents and files."
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
        "daily plan",
        "weekly plan"
    ],

    2: [
        "remind",
        "reminder",
        "alert",
        "yaad",
        "alarm"
    ],

    3: [
        "calendar",
        "appointment",
        "event",
        "schedule"
    ],

    4: [
        "task",
        "todo",
        "to do",
        "kaam"
    ],

    5: [
        "productivity",
        "productive",
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
        "purchase"
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
        "scheduled email",
        "automatic email",
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
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "chat_messages": [],
    "last_agents": [],
    "last_results": [],
    "generated_emails": [],
    "manual_api_key": "",
    "selected_agent": None
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# CONTACT DATABASE
# ============================================================

def add_contact_db(
    name,
    email
):

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


def delete_contact(
    contact_id
):

    with db_lock:

        conn = get_db()

        conn.execute(
            """
            DELETE FROM contacts
            WHERE id = ?
            """,
            (contact_id,)
        )

        conn.commit()
        conn.close()


def resolve_contact(
    name_or_email
):

    if not name_or_email:

        return None

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


def delete_schedule(
    schedule_id
):

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
# OPENAI
# ============================================================

def get_api_key():

    key = ""

    try:

        key = st.secrets.get(
            "OPENAI_API_KEY",
            ""
        )

    except Exception:
        pass

    if not key:

        key = os.getenv(
            "OPENAI_API_KEY",
            ""
        )

    if not key:

        key = st.session_state.manual_api_key

    return key.strip()


def call_openai(
    prompt,
    model="gpt-5",
    system_instruction=None
):

    if OpenAI is None:

        return (
            "OpenAI package is not installed."
        )

    api_key = get_api_key()

    if not api_key:

        return (
            "OpenAI API key is not configured."
        )

    try:

        client = OpenAI(
            api_key=api_key
        )

        response = client.responses.create(

            model=model,

            instructions=(
                system_instruction
                or
                """
                You are BHAI AI,
                a master multi-agent assistant.
                """
            ),

            input=prompt
        )

        return response.output_text

    except Exception as e:

        return f"OpenAI Error: {e}"


# ============================================================
# ROMAN URDU DATE/TIME NORMALIZATION
# ============================================================

def normalize_roman_urdu(
    text
):

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

        r"\bbajay\b": ""
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
# DATE/TIME PARSER
# ============================================================

def parse_schedule_from_text(
    text
):

    original = text

    normalized = normalize_roman_urdu(
        text
    )

    now = datetime.now()

    run_at = None

    recurrence = None

    lower = normalized.lower()

    # --------------------------------------------------------
    # RECURRENCE
    # --------------------------------------------------------

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

            recurrence = (
                f"weekly:{short_day}"
            )

    # --------------------------------------------------------
    # DATEPARSER
    # --------------------------------------------------------

    if dateparser:

        try:

            run_at = dateparser.parse(
                normalized,
                settings={
                    "PREFER_DATES_FROM": "future",
                    "RELATIVE_BASE": now,
                    "RETURN_AS_TIMEZONE_AWARE": False
                }
            )

        except Exception:

            run_at = None

    # --------------------------------------------------------
    # TIME REGEX
    # --------------------------------------------------------

    patterns = [

        r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b",

        r"\b(\d{1,2})\s*(am|pm)\b",

        r"\bat\s+(\d{1,2})(?::(\d{2}))?\b",

        r"\b(\d{1,2})\s*(?:baje|bajay)\b"

    ]

    match = None

    for pattern in patterns:

        found = re.search(
            pattern,
            normalized,
            re.IGNORECASE
        )

        if found:

            match = found
            break

    if match:

        groups = match.groups()

        hour = int(
            groups[0]
        )

        minute = 0

        if len(groups) > 1 and groups[1]:

            try:

                minute = int(
                    groups[1]
                )

            except Exception:

                minute = 0

        ampm = None

        if len(groups) > 2:

            ampm = groups[2]

        if ampm:

            ampm = ampm.lower()

            if ampm == "pm" and hour < 12:

                hour += 12

            elif ampm == "am" and hour == 12:

                hour = 0

        elif re.search(
            r"\b(shaam|sham|raat|dopahar)\b",
            original,
            re.IGNORECASE
        ):

            if hour < 12:

                hour += 12

        elif re.search(
            r"\b(subah|sawere|savera)\b",
            original,
            re.IGNORECASE
        ):

            if hour == 12:

                hour = 0

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

                run_at += timedelta(
                    days=1
                )

    if run_at and run_at <= now:

        if recurrence is None:

            run_at += timedelta(
                days=1
            )

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

def demo_router(
    text
):

    lower = text.lower()

    scores = {}

    for agent_id, keywords in KEYWORD_ROUTING.items():

        score = 0

        for keyword in keywords:

            if keyword in lower:

                score += 1

        if score:

            scores[agent_id] = score

    schedule = parse_schedule_from_text(
        text
    )

    if schedule["scheduled"]:

        scores[21] = (
            scores.get(21, 0) + 5
        )

    if not scores:

        return [
            1,
            4,
            5
        ]

    ranked = sorted(
        scores,
        key=scores.get,
        reverse=True
    )

    return ranked[:5]


def api_router(
    text,
    model
):

    prompt = f"""
You are the BHAI Master Router.

Select relevant agents from:

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

User:
{text}

Return ONLY JSON.

Example:
[21, 9]
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

            values = json.loads(
                match.group(0)
            )

            return [
                int(x)
                for x in values
                if int(x) in AGENTS
            ][:5]

    except Exception:
        pass

    return demo_router(
        text
    )


# ============================================================
# AGENT EXECUTION
# ============================================================

def demo_agent(
    agent_id,
    prompt
):

    if agent_id == 21:

        parsed = parse_schedule_from_text(
            prompt
        )

        if parsed["scheduled"]:

            return (
                "🔔 Time detected: "
                + parsed["run_at"].strftime(
                    "%d %B %Y %I:%M %p"
                )
            )

        return (
            "Email Notification Agent is ready."
        )

    return (
        f"{AGENTS[agent_id]['icon']} "
        f"{AGENTS[agent_id]['name']} processed your request.\n\n"
        f"Request: {prompt}\n\n"
        f"Demo Mode response: "
        f"This agent is ready for integration "
        f"with your real workflow."
    )


def api_agent(
    agent_id,
    prompt,
    model
):

    agent = AGENTS[agent_id]

    system = f"""
You are the {agent['name']} in BHAI AI.

Role:
{agent['description']}

Give a practical and useful response.
"""

    return call_openai(
        prompt,
        model=model,
        system_instruction=system
    )


# ============================================================
# EMAIL
# ============================================================

def smtp_settings():

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

        return (
            host,
            port,
            username,
            password
        )

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
        smtp_settings()
    )

    if not username or not password:

        return (
            False,
            "SMTP credentials are not configured."
        )

    try:

        message = MIMEMultipart()

        message["From"] = username
        message["To"] = recipient
        message["Subject"] = subject

        message.attach(
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
            message.as_string()
        )

        server.quit()

        return (
            True,
            "Email sent successfully."
        )

    except Exception as e:

        return (
            False,
            str(e)
        )


# ============================================================
# SCHEDULER
# ============================================================

def execute_schedule(
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

    success = False

    if row["action_type"] == "email":

        success, _ = send_email(
            row["recipient"],
            row["subject"] or "BHAI Notification",
            row["message"] or ""
        )

    else:

        if row["recipient"]:

            success, _ = send_email(
                row["recipient"],
                row["subject"] or "BHAI Reminder",
                row["message"] or row["title"]
            )

        else:

            success = True

    with db_lock:

        conn = get_db()

        conn.execute(
            """
            UPDATE schedules
            SET
                status = ?,
                last_run = ?
            WHERE id = ?
            """,
            (
                "Completed" if success else "Scheduled",
                datetime.now().isoformat(),
                schedule_id
            )
        )

        conn.commit()
        conn.close()


@st.cache_resource
def get_scheduler():

    if BackgroundScheduler is None:

        return None

    scheduler = BackgroundScheduler(
        timezone="Asia/Karachi"
    )

    scheduler.start()

    return scheduler


def register_schedule(
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
                execute_schedule,
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

            weekday = recurrence.split(
                ":"
            )[1]

            scheduler.add_job(
                execute_schedule,
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
                execute_schedule,
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

    rows = get_schedules()

    for row in rows:

        if row["status"] != "Scheduled":

            continue

        try:

            run_at = datetime.fromisoformat(
                row["run_at"]
            )

            if (
                row["recurrence"] is None
                and run_at <= datetime.now()
            ):

                continue

            register_schedule(
                row["id"],
                run_at,
                row["recurrence"]
            )

        except Exception:
            pass


restore_schedules()


# ============================================================
# AUTOMATIC SCHEDULING
# ============================================================

def extract_recipient(
    text
):

    email_match = re.search(
        r"[\w\.-]+@[\w\.-]+\.\w+",
        text
    )

    if email_match:

        return email_match.group(0)

    contacts = get_contacts()

    lower = text.lower()

    for contact in contacts:

        if contact["name"].lower() in lower:

            return contact["email"]

    return None


def is_email_request(
    text
):

    lower = text.lower()

    return any(
        x in lower
        for x in [
            "email",
            "e-mail",
            "send email",
            "email kar",
            "email bhej",
            "mail bhej"
        ]
    )


def automatic_schedule(
    user_text
):

    parsed = parse_schedule_from_text(
        user_text
    )

    if not parsed["scheduled"]:

        return None

    recipient = extract_recipient(
        user_text
    )

    if is_email_request(
        user_text
    ):

        action_type = "email"

    else:

        action_type = "reminder"

    schedule_id = add_schedule_db(

        action_type=action_type,

        title=(
            "Scheduled Email"
            if action_type == "email"
            else "Scheduled Reminder"
        ),

        message=user_text,

        recipient=recipient or "",

        subject="BHAI Automatic Notification",

        run_at=parsed["run_at"],

        recurrence=parsed["recurrence"]
    )

    registered = register_schedule(
        schedule_id,
        parsed["run_at"],
        parsed["recurrence"]
    )

    return {
        "id": schedule_id,
        "run_at": parsed["run_at"],
        "recurrence": parsed["recurrence"],
        "recipient": recipient,
        "action_type": action_type,
        "registered": registered
    }


# ============================================================
# MASTER PROCESS
# ============================================================

def process_master(
    user_text,
    mode,
    model
):

    if mode == "API Mode":

        agents = api_router(
            user_text,
            model
        )

    else:

        agents = demo_router(
            user_text
        )

    scheduled = automatic_schedule(
        user_text
    )

    if scheduled and 21 not in agents:

        agents.insert(
            0,
            21
        )

    results = []

    for agent_id in agents:

        if mode == "API Mode":

            result = api_agent(
                agent_id,
                user_text,
                model
            )

        else:

            result = demo_agent(
                agent_id,
                user_text
            )

        results.append(
            {
                "id": agent_id,
                "name": AGENTS[agent_id]["name"],
                "result": result
            }
        )

    summary = (
        f"BHAI activated {len(agents)} agent(s)."
    )

    if scheduled:

        summary += (
            "\n\n⏰ Scheduled: "
            + scheduled["run_at"].strftime(
                "%d %B %Y at %I:%M %p"
            )
        )

        if scheduled["recurrence"]:

            summary += (
                "\n🔁 Repeat: "
                + scheduled["recurrence"]
            )

        if scheduled["recipient"]:

            summary += (
                "\n📧 Recipient: "
                + scheduled["recipient"]
            )

    return (
        agents,
        results,
        summary
    )


# ============================================================
# EMAIL GENERATOR
# ============================================================

def generate_email(
    purpose,
    recipient,
    tone,
    mode,
    model
):

    prompt = f"""
Write a professional email.

Purpose:
{purpose}

Recipient:
{recipient}

Tone:
{tone}

Include subject, greeting, body and closing.
"""

    if mode == "API Mode":

        result = call_openai(
            prompt,
            model=model
        )

    else:

        result = f"""
Subject: {purpose}

Dear {recipient},

I hope you are doing well.

I am writing regarding {purpose}.

Kindly consider the above request.

Thank you for your time and consideration.

Best regards,

Engr. Bilal Mehmood
AI Course Director
PITAC Regional Center Karachi, Sindh
"""

    return result


# ============================================================
# WORD
# ============================================================

def create_word(
    title,
    content,
    author
):

    if Document is None:

        return None

    document = Document()

    document.add_heading(
        title,
        0
    )

    document.add_paragraph(
        f"Author: {author}"
    )

    document.add_paragraph(
        f"Date: {datetime.now().strftime('%d %B %Y')}"
    )

    for line in content.split(
        "\n"
    ):

        document.add_paragraph(
            line
        )

    output = io.BytesIO()

    document.save(
        output
    )

    output.seek(0)

    return output


# ============================================================
# PDF
# ============================================================

def create_pdf(
    title,
    content,
    author
):

    if SimpleDocTemplate is None:

        return None

    output = io.BytesIO()

    pdf = SimpleDocTemplate(
        output,
        pagesize=A4
    )

    styles = getSampleStyleSheet()

    story = [

        Paragraph(
            title,
            styles["Title"]
        ),

        Spacer(
            1,
            15
        ),

        Paragraph(
            f"Author: {author}",
            styles["Normal"]
        ),

        Spacer(
            1,
            15
        )
    ]

    for line in content.split(
        "\n"
    ):

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

    pdf.build(
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
        "20-Agent Intelligent Daily Routine Automation"
    )

    st.divider()

    mode = st.radio(
        "⚙️ Mode",
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

        st.session_state.manual_api_key = (
            st.text_input(
                "OpenAI API Key",
                value=st.session_state.manual_api_key,
                type="password"
            )
        )

    st.divider()

    # ========================================================
    # MAIN NAVIGATION
    # ========================================================

    st.markdown(
        "### 🧭 MAIN NAVIGATION"
    )

    if st.button(
        "🏠 Dashboard",
        use_container_width=True
    ):

        st.session_state.selected_agent = None

        st.session_state.page = "Dashboard"

        st.rerun()

    if st.button(
        "🧠 BHAI Master",
        use_container_width=True
    ):

        st.session_state.selected_agent = None

        st.session_state.page = "BHAI Master"

        st.rerun()

    if st.button(
        "💬 BHAI Chatbot",
        use_container_width=True
    ):

        st.session_state.selected_agent = None

        st.session_state.page = "BHAI Chatbot"

        st.rerun()

    st.divider()

    # ========================================================
    # ALL AGENTS
    # ========================================================

    st.markdown(
        "### 🤖 ALL AGENTS"
    )

    for agent_id, agent in AGENTS.items():

        if st.button(
            f"{agent['icon']} {agent['name']}",
            key=f"sidebar_agent_{agent_id}",
            use_container_width=True
        ):

            st.session_state.selected_agent = agent_id

            st.session_state.page = "Agent"

            st.rerun()

    st.divider()

    # ========================================================
    # TOOLS
    # ========================================================

    st.markdown(
        "### 🛠️ TOOLS"
    )

    if st.button(
        "⏰ Reminders & Schedules",
        use_container_width=True
    ):

        st.session_state.selected_agent = None

        st.session_state.page = "Schedules"

        st.rerun()

    if st.button(
        "👤 Contacts",
        use_container_width=True
    ):

        st.session_state.selected_agent = None

        st.session_state.page = "Contacts"

        st.rerun()

    if st.button(
        "📧 Email Generator",
        use_container_width=True
    ):

        st.session_state.selected_agent = None

        st.session_state.page = "Email Generator"

        st.rerun()

    if st.button(
        "📄 Word/PDF Generator",
        use_container_width=True
    ):

        st.session_state.selected_agent = None

        st.session_state.page = "Documents"

        st.rerun()


# ============================================================
# DEFAULT PAGE
# ============================================================

if "page" not in st.session_state:

    st.session_state.page = "Dashboard"


current_page = st.session_state.page


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

if current_page == "Dashboard":

    st.header(
        "🏠 Dashboard"
    )

    schedules = get_schedules()

    contacts = get_contacts()

    active = [
        x for x in schedules
        if x["status"] == "Scheduled"
    ]

    completed = [
        x for x in schedules
        if x["status"] == "Completed"
    ]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Agents",
        "20"
    )

    col2.metric(
        "Scheduled",
        len(active)
    )

    col3.metric(
        "Contacts",
        len(contacts)
    )

    col4.metric(
        "Completed",
        len(completed)
    )

    st.divider()

    st.subheader(
        "🧠 BHAI Architecture"
    )

    st.markdown(
        """
        **User → BHAI Master → Intent Detection → Agent Router → Specialist Agent → Scheduler → Action**

        If a date/time is mentioned, BHAI automatically detects it.

        Example:

        `Kal 10 baje Director ko AI workshop proposal email kar dena.`

        becomes:

        **Email Agent + Email Notification Agent + Automatic Schedule**
        """
    )


# ============================================================
# BHAI MASTER
# ============================================================

elif current_page == "BHAI Master":

    st.header(
        "🧠 BHAI Master Agent"
    )

    st.write(
        "Give one natural-language command and BHAI will decide which agents are required."
    )

    command = st.text_area(
        "Your Command",
        height=150,
        placeholder=(
            "Kal 10 baje Director ko AI workshop proposal email kar dena."
        )
    )

    if st.button(
        "🚀 Execute BHAI",
        type="primary"
    ):

        if not command.strip():

            st.warning(
                "Please enter a command."
            )

        else:

            with st.spinner(
                "BHAI is thinking..."
            ):

                agents, results, summary = process_master(
                    command,
                    mode,
                    model
                )

            st.session_state.last_agents = agents

            st.session_state.last_results = results

            st.success(
                "Command processed."
            )

            st.info(
                summary
            )

            st.subheader(
                "🤖 Activated Agents"
            )

            for agent_id in agents:

                st.write(
                    f"{AGENTS[agent_id]['icon']} "
                    f"{AGENTS[agent_id]['name']}"
                )

            st.subheader(
                "📋 Results"
            )

            for result in results:

                with st.expander(
                    result["name"]
                ):

                    st.write(
                        result["result"]
                    )


# ============================================================
# CHATBOT
# ============================================================

elif current_page == "BHAI Chatbot":

    st.header(
        "💬 BHAI Chatbot"
    )

    for message in st.session_state.chat_messages:

        with st.chat_message(
            message["role"]
        ):

            st.write(
                message["content"]
            )

    prompt = st.chat_input(
        "Talk to BHAI..."
    )

    if prompt:

        st.session_state.chat_messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        agents, results, summary = process_master(
            prompt,
            mode,
            model
        )

        response = summary

        for result in results:

            response += (
                "\n\n"
                + result["name"]
                + ":\n"
                + result["result"]
            )

        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": response
            }
        )

        st.rerun()


# ============================================================
# INDIVIDUAL AGENT PAGE
# ============================================================

elif current_page == "Agent":

    agent_id = st.session_state.selected_agent

    if agent_id not in AGENTS:

        st.warning(
            "Please select an agent from the left sidebar."
        )

    else:

        agent = AGENTS[agent_id]

        st.header(
            f"{agent['icon']} {agent['name']}"
        )

        st.write(
            agent["description"]
        )

        st.divider()

        # ----------------------------------------------------
        # SPECIAL UI FOR SCHEDULER AGENT
        # ----------------------------------------------------

        if agent_id == 21:

            st.subheader(
                "🔔 Automatic Notification Scheduler"
            )

            st.info(
                "Simply write your task and mention the date/time. BHAI will automatically schedule it."
            )

            st.code(
                "Kal 10 baje Director ko AI workshop proposal email kar dena."
            )

            st.code(
                "Aaj 5 PM par mujhe Python class yaad dilana."
            )

            st.code(
                "Har Monday 9 AM par weekly meeting ka reminder email bhejna."
            )

            scheduler_command = st.text_area(
                "Scheduler Command",
                height=150
            )

            if st.button(
                "⏰ Schedule Automatically",
                type="primary"
            ):

                if scheduler_command.strip():

                    result = automatic_schedule(
                        scheduler_command
                    )

                    if result:

                        st.success(
                            "Schedule created successfully."
                        )

                        st.write(
                            "📅 Date:",
                            result["run_at"].strftime(
                                "%d %B %Y"
                            )
                        )

                        st.write(
                            "⏰ Time:",
                            result["run_at"].strftime(
                                "%I:%M %p"
                            )
                        )

                        st.write(
                            "📧 Recipient:",
                            result["recipient"]
                            or
                            "Not specified"
                        )

                        st.write(
                            "🔁 Repeat:",
                            result["recurrence"]
                            or
                            "One time"
                        )

                    else:

                        st.warning(
                            "No date/time detected."
                        )

        else:

            # ------------------------------------------------
            # NORMAL AGENT PAGE
            # ------------------------------------------------

            st.subheader(
                f"{agent['icon']} {agent['name']} Workspace"
            )

            task = st.text_area(
                "Enter your task",
                height=180,
                placeholder=(
                    f"Tell the {agent['name']} what you want..."
                )
            )

            col1, col2 = st.columns(
                [1, 1]
            )

            with col1:

                if st.button(
                    f"🚀 Run {agent['name']}",
                    type="primary",
                    use_container_width=True
                ):

                    if not task.strip():

                        st.warning(
                            "Please enter a task."
                        )

                    else:

                        # Automatically detect scheduling
                        schedule = parse_schedule_from_text(
                            task
                        )

                        if mode == "API Mode":

                            result = api_agent(
                                agent_id,
                                task,
                                model
                            )

                        else:

                            result = demo_agent(
                                agent_id,
                                task
                            )

                        st.success(
                            "Agent executed successfully."
                        )

                        st.markdown(
                            "### 📋 Agent Result"
                        )

                        st.write(
                            result
                        )

                        if schedule["scheduled"]:

                            automatic = automatic_schedule(
                                task
                            )

                            if automatic:

                                st.markdown(
                                    "### ⏰ Automatic Schedule"
                                )

                                st.success(
                                    "Time detected and task scheduled automatically."
                                )

                                st.write(
                                    "📅",
                                    automatic["run_at"].strftime(
                                        "%d %B %Y"
                                    )
                                )

                                st.write(
                                    "⏰",
                                    automatic["run_at"].strftime(
                                        "%I:%M %p"
                                    )
                                )

            with col2:

                st.markdown(
                    "### 💡 Example"
                )

                examples = {

                    1:
                        "Plan my tomorrow from 9 AM to 5 PM.",

                    2:
                        "Remind me tomorrow at 5 PM about Python class.",

                    3:
                        "Schedule a meeting tomorrow at 10 AM.",

                    4:
                        "Create a task to prepare workshop proposal.",

                    5:
                        "Improve my daily productivity.",

                    6:
                        "Create a Python learning plan.",

                    7:
                        "Prepare a research workflow.",

                    8:
                        "Write a professional message.",

                    9:
                        "Write an email to the Director.",

                    10:
                        "Prepare agenda for AI meeting.",

                    11:
                        "Create a general wellness routine.",

                    12:
                        "Create a weekly workout plan.",

                    13:
                        "Create a monthly budget.",

                    14:
                        "Create a shopping list.",

                    15:
                        "Plan a three-day trip.",

                    16:
                        "Prepare a news summary.",

                    17:
                        "Create notes for today's meeting.",

                    18:
                        "Prepare content for a Word document.",

                    19:
                        "Create a home task list.",

                    20:
                        "Suggest some games.",

                }

                st.code(
                    examples.get(
                        agent_id,
                        "Give your instruction here."
                    )
                )


# ============================================================
# SCHEDULES PAGE
# ============================================================

elif current_page == "Schedules":

    st.header(
        "⏰ Reminders & Schedules"
    )

    st.info(
        "Schedules created by BHAI and the Scheduler Agent appear here."
    )

    rows = get_schedules()

    if not rows:

        st.info(
            "No schedules available."
        )

    for row in rows:

        with st.container(border=True):

            col1, col2, col3 = st.columns(
                [4, 3, 1]
            )

            with col1:

                st.subheader(
                    row["title"]
                )

                st.write(
                    row["message"]
                )

            with col2:

                st.write(
                    "📅",
                    row["run_at"]
                )

                st.write(
                    "🔔",
                    row["status"]
                )

                if row["recurrence"]:

                    st.write(
                        "🔁",
                        row["recurrence"]
                    )

            with col3:

                if row["status"] == "Scheduled":

                    if st.button(
                        "Cancel",
                        key=f"cancel_{row['id']}"
                    ):

                        delete_schedule(
                            row["id"]
                        )

                        st.rerun()


# ============================================================
# CONTACTS
# ============================================================

elif current_page == "Contacts":

    st.header(
        "👤 Contacts Manager"
    )

    st.write(
        "Save names and email addresses. BHAI can use the name in natural-language commands."
    )

    with st.form(
        "add_contact"
    ):

        name = st.text_input(
            "Contact Name",
            placeholder="Director"
        )

        email = st.text_input(
            "Email",
            placeholder="director@example.com"
        )

        submitted = st.form_submit_button(
            "💾 Save Contact"
        )

    if submitted:

        if not name or not email:

            st.warning(
                "Both fields are required."
            )

        elif "@" not in email:

            st.warning(
                "Enter a valid email address."
            )

        else:

            add_contact_db(
                name,
                email
            )

            st.success(
                "Contact saved."
            )

            st.rerun()

    st.divider()

    contacts = get_contacts()

    for contact in contacts:

        col1, col2, col3 = st.columns(
            [3, 5, 1]
        )

        with col1:

            st.write(
                "👤",
                contact["name"]
            )

        with col2:

            st.write(
                contact["email"]
            )

        with col3:

            if st.button(
                "Delete",
                key=f"delete_{contact['id']}"
            ):

                delete_contact(
                    contact["id"]
                )

                st.rerun()


# ============================================================
# EMAIL GENERATOR
# ============================================================

elif current_page == "Email Generator":

    st.header(
        "📧 Email Generator"
    )

    purpose = st.text_area(
        "Email Purpose",
        height=150
    )

    recipient = st.text_input(
        "Recipient Name"
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
        "📧 Generate Email",
        type="primary"
    ):

        if purpose.strip():

            result = generate_email(
                purpose,
                recipient,
                tone,
                mode,
                model
            )

            st.text_area(
                "Generated Email",
                result,
                height=400
            )

        else:

            st.warning(
                "Enter the email purpose."
            )


# ============================================================
# DOCUMENT GENERATOR
# ============================================================

elif current_page == "Documents":

    st.header(
        "📄 Word / PDF Generator"
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
        "Content",
        height=400
    )

    if st.button(
        "📄 Generate Files",
        type="primary"
    ):

        if not content.strip():

            st.warning(
                "Enter document content."
            )

        else:

            word = create_word(
                title,
                content,
                author
            )

            pdf = create_pdf(
                title,
                content,
                author
            )

            col1, col2 = st.columns(2)

            with col1:

                if word:

                    st.download_button(
                        "⬇️ Download Word",
                        word,
                        "BHAI_Document.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

            with col2:

                if pdf:

                    st.download_button(
                        "⬇️ Download PDF",
                        pdf,
                        "BHAI_Document.pdf",
                        "application/pdf"
                    )


# ============================================================
# LAST AGENTS
# ============================================================

if st.session_state.last_agents:

    with st.expander(
        "🧠 Last Activated Agents"
    ):

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
    OpenAI API Mode • Demo Mode • Automatic Scheduling • Email Notifications
    <br><br>
    <b>By Engr. Bilal Mehmood</b>

    </div>
    """,
    unsafe_allow_html=True
)
