```python
import os
import re
import io
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
except ImportError:
    BackgroundScheduler = None
    DateTrigger = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
    )
    from reportlab.lib.styles import getSampleStyleSheet
except ImportError:
    SimpleDocTemplate = None
    getSampleStyleSheet = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="BHAI AI - Master Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# APPLICATION CONSTANTS
# ============================================================

APP_NAME = "BHAI AI"
APP_VERSION = "4.0"
DEFAULT_MODEL = "gpt-6-luna"
DB_FILE = "bhai_ai.db"


# ============================================================
# AGENTS
# ============================================================

AGENTS = {
    1: {
        "icon": "🗓️",
        "name": "Planner Agent",
        "short": "Planner",
        "description": "Plans daily, weekly and long-term activities.",
        "guidance": [
            "Create a daily schedule.",
            "Prepare weekly plans.",
            "Prioritize important activities.",
            "Balance work, learning and personal activities.",
        ],
        "examples": [
            "Make my plan for tomorrow.",
            "Create my weekly work plan.",
            "Plan my day from 8 AM to 6 PM.",
            "Prioritize my activities for today.",
        ],
    },

    2: {
        "icon": "⏰",
        "name": "Reminder Agent",
        "short": "Reminder",
        "description": "Creates reminders, alerts and personal alarms.",
        "guidance": [
            "Create reminders.",
            "Understand common date/time expressions.",
            "Prepare alarm instructions.",
            "Manage reminder schedules.",
        ],
        "examples": [
            "Remind me tomorrow at 8 PM.",
            "Set an alarm for my meeting.",
            "Remind me every Monday.",
            "Yaad dilana kal subah 9 baje.",
        ],
    },

    3: {
        "icon": "📅",
        "name": "Calendar Agent",
        "short": "Calendar",
        "description": "Organizes appointments, events and calendar activities.",
        "guidance": [
            "Create event descriptions.",
            "Organize appointments.",
            "Prepare calendar schedules.",
            "Suggest suitable meeting times.",
        ],
        "examples": [
            "Create a meeting schedule for Monday.",
            "Prepare my calendar for tomorrow.",
            "Schedule a project review.",
        ],
    },

    4: {
        "icon": "✅",
        "name": "Task Agent",
        "short": "Tasks",
        "description": "Creates, organizes and prioritizes actionable tasks.",
        "guidance": [
            "Create task lists.",
            "Break large tasks into smaller tasks.",
            "Prioritize tasks.",
            "Create daily to-do lists.",
        ],
        "examples": [
            "Create today's task list.",
            "Break my project into 10 tasks.",
            "Prioritize these tasks.",
        ],
    },

    5: {
        "icon": "🚀",
        "name": "Productivity Agent",
        "short": "Productivity",
        "description": "Improves productivity, workflows and time management.",
        "guidance": [
            "Optimize workflows.",
            "Reduce repetitive work.",
            "Create productivity routines.",
            "Suggest automation ideas.",
        ],
        "examples": [
            "Improve my daily workflow.",
            "Create a productive morning routine.",
            "Automate my repetitive office tasks.",
        ],
    },

    6: {
        "icon": "📚",
        "name": "Learning Agent",
        "short": "Learning",
        "description": "Creates learning plans, study schedules and courses.",
        "guidance": [
            "Create study plans.",
            "Design learning roadmaps.",
            "Break subjects into modules.",
            "Create revision schedules.",
        ],
        "examples": [
            "Make a 30-day Python learning plan.",
            "Create a study timetable.",
            "Teach me Python from beginner level.",
        ],
    },

    7: {
        "icon": "🔬",
        "name": "Research Agent",
        "short": "Research",
        "description": "Supports research planning, analysis and academic work.",
        "guidance": [
            "Develop research ideas.",
            "Create literature review structures.",
            "Prepare research questions.",
            "Organize methodology ideas.",
        ],
        "examples": [
            "Give me AI research topics.",
            "Create a literature review structure.",
            "Prepare a research methodology.",
        ],
    },

    8: {
        "icon": "💬",
        "name": "Communication Agent",
        "short": "Communication",
        "description": "Prepares professional messages and communication.",
        "guidance": [
            "Write professional messages.",
            "Improve communication.",
            "Prepare announcements.",
            "Create short WhatsApp/SMS style messages.",
        ],
        "examples": [
            "Write a professional WhatsApp message.",
            "Prepare an announcement for students.",
            "Make this message more professional.",
        ],
    },

    9: {
        "icon": "📧",
        "name": "Email Agent",
        "short": "Email",
        "description": "Creates professional emails for work and personal communication.",
        "guidance": [
            "Create formal emails.",
            "Write professional replies.",
            "Generate subject lines.",
            "Adjust tone and length.",
        ],
        "examples": [
            "Write an email to my manager.",
            "Prepare a leave application email.",
            "Write a professional follow-up email.",
        ],
    },

    10: {
        "icon": "🤝",
        "name": "Meeting Agent",
        "short": "Meeting",
        "description": "Plans meetings, agendas, minutes and action points.",
        "guidance": [
            "Create meeting agendas.",
            "Prepare minutes of meetings.",
            "Generate action items.",
            "Create meeting follow-ups.",
        ],
        "examples": [
            "Create an agenda for an AI workshop.",
            "Prepare meeting minutes.",
            "Create action items from this meeting.",
        ],
    },

    11: {
        "icon": "❤️",
        "name": "Health Agent",
        "short": "Health",
        "description": "Organizes general wellness and healthy routines.",
        "guidance": [
            "Create general wellness routines.",
            "Suggest healthy habits.",
            "Organize sleep routines.",
            "Create hydration reminders.",
        ],
        "examples": [
            "Create a healthy daily routine.",
            "Make a hydration schedule.",
            "Suggest a better sleep routine.",
        ],
    },

    12: {
        "icon": "🏃",
        "name": "Fitness Agent",
        "short": "Fitness",
        "description": "Creates general fitness, exercise and workout routines.",
        "guidance": [
            "Create exercise schedules.",
            "Organize workout routines.",
            "Plan walking routines.",
            "Create fitness goals.",
        ],
        "examples": [
            "Create a beginner workout plan.",
            "Make a weekly exercise schedule.",
            "Create a morning walking routine.",
        ],
    },

    13: {
        "icon": "💰",
        "name": "Finance Agent",
        "short": "Finance",
        "description": "Organizes budgets, expenses and financial planning.",
        "guidance": [
            "Create personal budgets.",
            "Categorize expenses.",
            "Prepare savings plans.",
            "Analyze spending patterns.",
        ],
        "examples": [
            "Create a monthly budget.",
            "Categorize my expenses.",
            "Make a savings plan.",
        ],
    },

    14: {
        "icon": "🛒",
        "name": "Shopping Agent",
        "short": "Shopping",
        "description": "Creates and organizes shopping lists.",
        "guidance": [
            "Create shopping lists.",
            "Categorize products.",
            "Prioritize purchases.",
            "Prepare grocery lists.",
        ],
        "examples": [
            "Create my grocery list.",
            "Make a monthly shopping list.",
            "Organize these items by category.",
        ],
    },

    15: {
        "icon": "✈️",
        "name": "Travel Agent",
        "short": "Travel",
        "description": "Plans trips, itineraries and travel activities.",
        "guidance": [
            "Create travel itineraries.",
            "Plan daily trips.",
            "Prepare packing lists.",
            "Organize travel activities.",
        ],
        "examples": [
            "Plan a 3-day trip.",
            "Create a travel itinerary.",
            "Make a travel packing list.",
        ],
    },

    16: {
        "icon": "📰",
        "name": "News Agent",
        "short": "News",
        "description": "Handles news-related requests and information summaries.",
        "guidance": [
            "Summarize provided news.",
            "Create news categories.",
            "Prepare news brief formats.",
            "Organize current-affairs topics.",
        ],
        "examples": [
            "Summarize this news.",
            "Create a daily news briefing format.",
            "Explain this current event.",
        ],
    },

    17: {
        "icon": "📝",
        "name": "Notes Agent",
        "short": "Notes",
        "description": "Creates, structures and organizes notes.",
        "guidance": [
            "Create structured notes.",
            "Summarize information.",
            "Convert rough notes into organized notes.",
            "Create meeting notes.",
        ],
        "examples": [
            "Convert these points into notes.",
            "Summarize my lecture.",
            "Create structured project notes.",
        ],
    },

    18: {
        "icon": "📁",
        "name": "File Agent",
        "short": "Files",
        "description": "Prepares content for Word, PDF and other documents.",
        "guidance": [
            "Create document content.",
            "Prepare reports.",
            "Prepare proposals.",
            "Generate Word/PDF-ready content.",
        ],
        "examples": [
            "Create a project proposal.",
            "Prepare a formal report.",
            "Create a workshop document.",
        ],
    },

    19: {
        "icon": "🏠",
        "name": "Home Agent",
        "short": "Home",
        "description": "Organizes home-related routines and activities.",
        "guidance": [
            "Create household task lists.",
            "Plan cleaning routines.",
            "Organize home maintenance.",
            "Prepare household schedules.",
        ],
        "examples": [
            "Create a weekly home cleaning plan.",
            "Make a household task list.",
            "Plan home maintenance activities.",
        ],
    },

    20: {
        "icon": "🎮",
        "name": "Entertainment Agent",
        "short": "Entertainment",
        "description": "Handles entertainment, games and leisure planning.",
        "guidance": [
            "Suggest entertainment activities.",
            "Organize game sessions.",
            "Create leisure schedules.",
            "Prepare chess/game ideas.",
        ],
        "examples": [
            "Suggest games for tonight.",
            "Create a weekend entertainment plan.",
            "Give me chess practice ideas.",
        ],
    },

    21: {
        "icon": "🔔",
        "name": "Email Notification Agent",
        "short": "Email Notifications",
        "description": "Schedules automatic email notifications.",
        "guidance": [
            "Schedule email notifications.",
            "Prepare notification messages.",
            "Use SMTP for actual email delivery.",
            "Create future email reminders.",
        ],
        "examples": [
            "Send an email reminder tomorrow at 9 AM.",
            "Schedule a meeting notification.",
            "Notify me by email every Monday.",
        ],
    },
}


# ============================================================
# KEYWORD ROUTING
# ============================================================

KEYWORD_ROUTING = {
    1: ["plan", "planning", "daily plan", "weekly plan", "routine"],
    2: ["remind", "reminder", "alert", "yaad", "alarm"],
    3: ["calendar", "appointment", "event", "schedule"],
    4: ["task", "todo", "to do", "kaam"],
    5: ["productivity", "productive", "workflow", "automation"],
    6: ["learn", "learning", "study", "course", "class", "education"],
    7: ["research", "research paper", "literature", "methodology"],
    8: ["message", "communication", "whatsapp", "sms"],
    9: ["email", "mail", "send email", "email kar"],
    10: ["meeting", "agenda", "minutes", "moM"],
    11: ["health", "wellness", "healthy", "sleep"],
    12: ["fitness", "exercise", "workout", "gym"],
    13: ["finance", "money", "budget", "expense", "saving"],
    14: ["shopping", "buy", "purchase", "grocery"],
    15: ["travel", "trip", "flight", "hotel", "tour"],
    16: ["news", "latest news", "current affairs"],
    17: ["note", "notes", "remember", "summarize"],
    18: ["file", "document", "word", "pdf", "report"],
    19: ["home", "house", "cleaning"],
    20: ["game", "games", "entertainment", "movie", "chess"],
    21: [
        "notification",
        "notify",
        "scheduled email",
        "automatic email",
        "system alarm",
    ],
}


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.main-title {
    font-size: 46px;
    font-weight: 900;
    letter-spacing: -1px;
}

.subtitle {
    font-size: 18px;
    color: #777;
    margin-bottom: 25px;
}

.hero {
    padding: 35px;
    border-radius: 24px;
    border: 1px solid rgba(128,128,128,.20);
    background:
        linear-gradient(
            135deg,
            rgba(100,100,255,.10),
            rgba(0,200,180,.07)
        );
    margin-bottom: 25px;
}

.agent-card {
    border: 1px solid rgba(128,128,128,.20);
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 15px;
    background: rgba(128,128,128,.035);
    min-height: 145px;
}

.agent-card:hover {
    border-color: rgba(80,120,255,.45);
}

.agent-icon {
    font-size: 35px;
}

.agent-name {
    font-size: 21px;
    font-weight: 750;
}

.agent-description {
    color: #777;
    font-size: 14px;
}

.welcome-box {
    padding: 10px;
}

.status-box {
    border-radius: 15px;
    padding: 16px;
    border: 1px solid rgba(128,128,128,.20);
    margin: 8px 0;
}

.guide-box {
    border-left: 5px solid #777;
    padding: 15px;
    border-radius: 10px;
    background: rgba(128,128,128,.05);
}

.footer {
    text-align: center;
    margin-top: 60px;
    padding: 30px;
    color: #777;
    border-top: 1px solid rgba(128,128,128,.20);
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "mode": "Demo Mode",
    "manual_api_key": "",
    "model": DEFAULT_MODEL,
    "selected_agent": None,
    "chat_messages": [],
    "last_results": [],
    "last_agents": [],
    "generated_emails": [],
    "api_test_result": None,
    "welcome_seen": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# DATABASE
# ============================================================

db_lock = threading.Lock()


def get_db():
    conn = sqlite3.connect(
        DB_FILE,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():

    with db_lock:

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        cur.execute(
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
# CONTACT DATABASE FUNCTIONS
# ============================================================

def add_contact_db(name, email):

    with db_lock:

        conn = get_db()

        conn.execute(
            """
            INSERT INTO contacts
            VALUES (?, ?, ?, ?)
            """,
            (
                uuid.uuid4().hex[:10],
                name.strip(),
                email.strip(),
                datetime.now().isoformat(),
            ),
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
            "DELETE FROM contacts WHERE id=?",
            (contact_id,),
        )

        conn.commit()
        conn.close()


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
                None,
                "Scheduled",
                datetime.now().isoformat(),
                None,
            ),
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


def cancel_schedule(schedule_id):

    with db_lock:

        conn = get_db()

        conn.execute(
            """
            UPDATE schedules
            SET status='Cancelled'
            WHERE id=?
            """,
            (schedule_id,),
        )

        conn.commit()
        conn.close()


# ============================================================
# API MANAGEMENT
# ============================================================

def get_secret(name, default=""):

    try:

        value = st.secrets.get(name, default)

        if value is None:
            return default

        return str(value).strip()

    except Exception:

        return default


def get_api_key_source():

    if get_secret("OPENAI_API_KEY"):
        return "Streamlit Secrets"

    if os.getenv("OPENAI_API_KEY", "").strip():
        return "Environment Variable"

    if st.session_state.manual_api_key.strip():
        return "Manual Session Key"

    return "Not configured"


def get_api_key():

    secret_key = get_secret("OPENAI_API_KEY")

    if secret_key:
        return secret_key

    env_key = os.getenv(
        "OPENAI_API_KEY",
        "",
    ).strip()

    if env_key:
        return env_key

    return st.session_state.manual_api_key.strip()


def get_model():

    selected = st.session_state.get(
        "model",
        "",
    ).strip()

    if selected:
        return selected

    secret_model = get_secret(
        "OPENAI_MODEL"
    )

    if secret_model:
        return secret_model

    return DEFAULT_MODEL


def mask_key(key):

    if not key:
        return "Not configured"

    if len(key) <= 10:
        return "••••••••"

    return (
        f"{key[:5]}"
        "••••••••"
        f"{key[-4:]}"
    )


def api_status():

    if OpenAI is None:
        return "❌ OpenAI package not installed"

    if not get_api_key():
        return "⚪ API key not configured"

    return (
        f"🟢 API available via "
        f"{get_api_key_source()}"
    )


# ============================================================
# OPENAI CALL
# ============================================================

def call_openai(
    prompt,
    system_instruction=None,
):

    if OpenAI is None:

        return (
            "❌ OpenAI package is not installed.\n\n"
            "Install it with:\n"
            "`pip install openai`"
        )

    key = get_api_key()

    if not key:

        return (
            "❌ OpenAI API key is not configured.\n\n"
            "Go to:\n"
            "**🔐 API Management**"
        )

    model = get_model()

    try:

        client = OpenAI(
            api_key=key
        )

        response = client.responses.create(
            model=model,
            instructions=(
                system_instruction
                or
                "You are BHAI AI, a professional "
                "master multi-agent assistant."
            ),
            input=prompt,
        )

        result = getattr(
            response,
            "output_text",
            "",
        )

        return result or "No response generated."

    except Exception as e:

        message = str(e)

        if (
            "429" in message
            or
            "quota" in message.lower()
            or
            "credit" in message.lower()
        ):

            return (
                "❌ **OpenAI API Credits/Quota Error**\n\n"
                "Your API key may be valid, but the "
                "API project does not currently have "
                "sufficient credits/quota."
            )

        return f"❌ OpenAI Error:\n\n{message}"


# ============================================================
# API TEST
# ============================================================

def test_openai_connection():

    result = call_openai(
        "Reply with exactly: "
        "BHAI API connection successful."
    )

    if result.startswith("❌"):

        return False, result

    return True, result


# ============================================================
# ROUTING
# ============================================================

def detect_agents(text):

    text_lower = text.lower()

    found = []

    for agent_id, keywords in KEYWORD_ROUTING.items():

        for keyword in keywords:

            if keyword.lower() in text_lower:

                found.append(agent_id)
                break

    if not found:

        found = [1]

    return list(dict.fromkeys(found))[:5]


def build_agent_prompt(
    agent_id,
    user_request,
):

    agent = AGENTS[agent_id]

    return f"""
You are the {agent['name']} of BHAI AI.

AGENT PURPOSE:
{agent['description']}

AGENT RESPONSIBILITIES:
{chr(10).join("- " + x for x in agent['guidance'])}

USER REQUEST:
{user_request}

INSTRUCTIONS:

1. Understand the user's actual intent.
2. Give a practical response.
3. Use headings where helpful.
4. Give actionable steps.
5. Do not claim that an action was physically completed
   unless the application actually performed it.
6. If an action requires another service such as SMTP,
   explain the requirement.
7. If the user writes in Roman Urdu, you may answer
   in clear Roman Urdu or bilingual format.
"""


# ============================================================
# DEMO RESPONSE
# ============================================================

def demo_response(
    user_text,
    agent_ids,
):

    names = ", ".join(
        AGENTS[i]["name"]
        for i in agent_ids
    )

    return f"""
## 🤖 BHAI AI — Demo Mode

### 🔀 Agent Routing

{names}

### 📝 Your Request

{user_text}

### ✅ Demo Response

BHAI AI successfully understood your request and
routed it to the appropriate specialized agent(s).

This is currently **Demo Mode**, so the AI model was
not called.

Switch to:

**Sidebar → Operating Mode → API Mode**

to use the configured OpenAI API.

### 💡 Tip

You can also open the individual agent from:

**Sidebar → 🤖 AGENTS**

and use its dedicated guidance and example prompts.
"""


# ============================================================
# DATE/TIME PARSER
# ============================================================

def normalize_roman_urdu(text):

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
    }

    result = text

    for pattern, replacement in replacements.items():

        result = re.sub(
            pattern,
            replacement,
            result,
            flags=re.IGNORECASE,
        )

    return result


def parse_datetime_text(text):

    normalized = normalize_roman_urdu(text)

    now = datetime.now()

    if dateparser:

        try:

            result = dateparser.parse(
                normalized,
                settings={
                    "PREFER_DATES_FROM": "future",
                    "RELATIVE_BASE": now,
                },
            )

            if result:

                return result.replace(
                    tzinfo=None
                )

        except Exception:
            pass

    match = re.search(
        r"\b(\d{1,2})"
        r"(?::(\d{2}))?"
        r"\s*(am|pm)\b",
        normalized,
        re.IGNORECASE,
    )

    if match:

        hour = int(match.group(1))
        minute = int(
            match.group(2) or 0
        )

        ampm = match.group(3).lower()

        if ampm == "pm" and hour < 12:
            hour += 12

        if ampm == "am" and hour == 12:
            hour = 0

        result = now.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )

        if "tomorrow" in normalized.lower():

            result += timedelta(days=1)

        if result <= now:

            result += timedelta(days=1)

        return result

    return None


# ============================================================
# SMTP EMAIL
# ============================================================

def send_email_smtp(
    to_email,
    subject,
    body,
):

    host = get_secret(
        "SMTP_HOST",
        os.getenv("SMTP_HOST", ""),
    )

    port = int(
        get_secret(
            "SMTP_PORT",
            os.getenv("SMTP_PORT", "587"),
        )
        or 587
    )

    username = get_secret(
        "SMTP_USERNAME",
        os.getenv("SMTP_USERNAME", ""),
    )

    password = get_secret(
        "SMTP_PASSWORD",
        os.getenv("SMTP_PASSWORD", ""),
    )

    sender = get_secret(
        "SMTP_FROM",
        username,
    )

    if not all(
        [
            host,
            username,
            password,
            sender,
        ]
    ):

        return (
            False,
            "SMTP is not configured.",
        )

    try:

        msg = MIMEMultipart()

        msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(
            MIMEText(
                body,
                "plain",
                "utf-8",
            )
        )

        with smtplib.SMTP(
            host,
            port,
            timeout=20,
        ) as server:

            server.starttls()

            server.login(
                username,
                password,
            )

            server.sendmail(
                sender,
                [to_email],
                msg.as_string(),
            )

        return (
            True,
            "Email sent successfully.",
        )

    except Exception as e:

        return (
            False,
            f"SMTP Error: {e}",
        )


# ============================================================
# SCHEDULER
# ============================================================

scheduler = None

if BackgroundScheduler:

    try:

        scheduler = BackgroundScheduler(
            timezone="Asia/Karachi"
        )

        scheduler.start()

    except Exception:

        scheduler = None


def scheduled_email_job(
    schedule_id,
    recipient,
    subject,
    message,
):

    ok, _ = send_email_smtp(
        recipient,
        subject,
        message,
    )

    with db_lock:

        conn = get_db()

        conn.execute(
            """
            UPDATE schedules
            SET last_run=?,
                status=?
            WHERE id=?
            """,
            (
                datetime.now().isoformat(),
                "Completed"
                if ok
                else "Failed",
                schedule_id,
            ),
        )

        conn.commit()
        conn.close()


def schedule_email(
    schedule_id,
    recipient,
    subject,
    message,
    run_at,
):

    if not scheduler or not DateTrigger:

        return (
            False,
            "APScheduler is not installed/running.",
        )

    try:

        scheduler.add_job(
            scheduled_email_job,
            trigger=DateTrigger(
                run_date=run_at
            ),
            args=[
                schedule_id,
                recipient,
                subject,
                message,
            ],
            id=f"email_{schedule_id}",
            replace_existing=True,
        )

        return (
            True,
            "Email notification scheduled.",
        )

    except Exception as e:

        return (
            False,
            f"Scheduler error: {e}",
        )


# ============================================================
# DOCUMENT GENERATION
# ============================================================

def create_word(
    title,
    body,
):

    if Document is None:
        return None

    doc = Document()

    doc.add_heading(
        title,
        0,
    )

    for paragraph in body.split("\n"):

        if paragraph.strip():

            doc.add_paragraph(
                paragraph
            )

    output = io.BytesIO()

    doc.save(output)

    output.seek(0)

    return output.getvalue()


def create_pdf(
    title,
    body,
):

    if (
        SimpleDocTemplate is None
        or getSampleStyleSheet is None
    ):

        return None

    output = io.BytesIO()

    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
    )

    styles = getSampleStyleSheet()

    story = [
        Paragraph(
            title,
            styles["Title"],
        ),
        Spacer(1, 12),
    ]

    for paragraph in body.split("\n"):

        if paragraph.strip():

            story.append(
                Paragraph(
                    paragraph,
                    styles["BodyText"],
                )
            )

            story.append(
                Spacer(1, 7)
            )

    doc.build(story)

    output.seek(0)

    return output.getvalue()


# ============================================================
# WELCOME POPUP
# ============================================================

def show_welcome_popup():

    if st.session_state.welcome_seen:
        return

    @st.dialog("🤖 Welcome to BHAI AI", width="large")
    def welcome_dialog():

        st.markdown(
            """
            <div class="welcome-box">

            <h1>👋 Assalam-o-Alaikum!</h1>

            <h2>Welcome to BHAI AI</h2>

            <p style="font-size:18px;">
            <b>BHAI AI</b> is your intelligent
            Master Agent for managing daily routines,
            productivity, learning, communication,
            documents, reminders and more.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "🤖 AI Agents",
            "21",
        )

        c2.metric(
            "⚙️ Modes",
            "2",
        )

        c3.metric(
            "🧠 Architecture",
            "Master + Agents",
        )

        st.divider()

        st.subheader(
            "🚀 How BHAI AI Works"
        )

        st.markdown(
            """
            **User Request**
            ↓
            **BHAI Master Agent**
            ↓
            **Intent Detection**
            ↓
            **Specialized Agent**
            ↓
            **AI Response / Action**
            ↓
            **Result**
            """
        )

        st.divider()

        st.subheader(
            "🎯 What You Can Do"
        )

        capabilities = [
            "🗓️ Create plans",
            "⏰ Set reminders",
            "📅 Manage schedules",
            "📧 Generate emails",
            "🤝 Prepare meetings",
            "📚 Create learning plans",
            "🔬 Organize research",
            "📄 Generate documents",
            "💰 Manage budgets",
            "🛒 Create shopping lists",
            "✈️ Plan travel",
            "🎮 Manage entertainment",
        ]

        cols = st.columns(3)

        for i, item in enumerate(
            capabilities
        ):

            cols[
                i % 3
            ].markdown(
                f"**{item}**"
            )

        st.divider()

        st.subheader(
            "⚡ Two Operating Modes"
        )

        st.info(
            """
            **Demo Mode:**  
            Learn and test the BHAI interface
            without an API key.

            **API Mode:**  
            Use your configured OpenAI API
            for intelligent AI responses.
            """
        )

        st.divider()

        st.subheader(
            "🧭 Quick Start"
        )

        st.markdown(
            """
            **1.** Select **Demo Mode** or **API Mode**.

            **2.** Open **🧠 BHAI Master** for automatic
            agent routing.

            **3.** Open **🤖 AGENTS** to work directly
            with any individual agent.

            **4.** Use **🔐 API Management** to configure
            your API key.

            **5.** Use **⏰ Reminders & Schedules**
            for scheduled activities.
            """
        )

        st.success(
            "💡 Tip: Start with BHAI Master and simply "
            "write what you want in natural language."
        )

        if st.button(
            "🚀 Start Using BHAI AI",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.welcome_seen = True

            st.rerun()

    welcome_dialog()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="text-align:center;">
        <div style="font-size:50px;">🤖</div>
        <h2>BHAI AI</h2>
        <small>Master Agent System</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.session_state.mode = st.radio(
        "⚙️ Operating Mode",
        [
            "Demo Mode",
            "API Mode",
        ],
        index=(
            0
            if st.session_state.mode
            == "Demo Mode"
            else 1
        ),
    )

    st.divider()

    st.subheader("🧭 Navigation")

    navigation = [
        "🏠 Dashboard",
        "🧠 BHAI Master",
        "💬 BHAI Chatbot",
        "🤖 AGENTS",
        "⏰ Reminders & Schedules",
        "👥 Contacts",
        "📧 Email Generator",
        "📄 Word/PDF Generator",
        "🔐 API Management",
    ]

    page = st.radio(
        "Main Menu",
        navigation,
        label_visibility="collapsed",
    )

    st.divider()

    st.subheader("🤖 Quick Agent Access")

    search_agent = st.text_input(
        "Search agent",
        placeholder="e.g. Email",
    )

    if search_agent.strip():

        for agent_id, agent in AGENTS.items():

            if (
                search_agent.lower()
                in agent["name"].lower()
            ):

                if st.button(
                    f"{agent['icon']} {agent['name']}",
                    key=f"quick_{agent_id}",
                    use_container_width=True,
                ):

                    st.session_state.selected_agent = agent_id
                    st.session_state.agent_page = True
                    st.rerun()

    st.divider()

    if st.button(
        "👋 Show Welcome Guide",
        use_container_width=True,
    ):

        st.session_state.welcome_seen = False
        st.rerun()

    st.divider()

    st.caption(
        f"Version {APP_VERSION}"
    )

    st.caption(
        "By Engr. Bilal Mehmood"
    )


# ============================================================
# DASHBOARD
# ============================================================

def render_dashboard():

    st.markdown(
        '<div class="hero">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-title">🤖 BHAI AI</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="subtitle">
        Master Agent for Intelligent Daily Routine Automation
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        **Think → Ask BHAI → BHAI Routes → Agent Works → Result**
        """
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "🤖 Agents",
        len(AGENTS),
    )

    c2.metric(
        "⚙️ Mode",
        st.session_state.mode,
    )

    c3.metric(
        "🔑 API",
        get_api_key_source(),
    )

    c4.metric(
        "🧠 Model",
        get_model(),
    )

    st.divider()

    st.subheader(
        "🚀 BHAI AI Capabilities"
    )

    cards = [
        (
            "🧠",
            "Master Agent",
            "Automatically understands user intent and routes the request.",
        ),
        (
            "⏰",
            "System Alarms",
            "Create reminders and future schedules.",
        ),
        (
            "📧",
            "Email Automation",
            "Generate and schedule professional emails.",
        ),
        (
            "📄",
            "Documents",
            "Create Word and PDF documents.",
        ),
        (
            "🤖",
            "21 Specialized Agents",
            "Every major daily routine has a dedicated agent.",
        ),
        (
            "🔐",
            "API Management",
            "Manage API access through secure settings.",
        ),
    ]

    cols = st.columns(3)

    for i, (
        icon,
        title,
        description,
    ) in enumerate(cards):

        with cols[i % 3]:

            st.markdown(
                f"""
                <div class="agent-card">

                <div class="agent-icon">
                {icon}
                </div>

                <div class="agent-name">
                {title}
                </div>

                <div class="agent-description">
                {description}
                </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    st.subheader(
        "⚡ Quick Start"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button(
            "🧠 Open Master Agent",
            use_container_width=True,
        ):

            st.info(
                "Select 🧠 BHAI Master from the sidebar."
            )

    with c2:

        if st.button(
            "🤖 Explore Agents",
            use_container_width=True,
        ):

            st.info(
                "Select 🤖 AGENTS from the sidebar."
            )

    with c3:

        if st.button(
            "🔐 Configure API",
            use_container_width=True,
        ):

            st.info(
                "Select 🔐 API Management from the sidebar."
            )


# ============================================================
# MASTER AGENT
# ============================================================

def render_master():

    st.title(
        "🧠 BHAI Master Agent"
    )

    st.caption(
        "Your central AI controller. "
        "Write your request naturally and BHAI will select "
        "the most relevant specialized agent(s)."
    )

    st.divider()

    request = st.text_area(
        "💬 What do you want BHAI to do?",
        height=160,
        placeholder=(
            "Example:\n"
            "Make my plan for tomorrow, remind me at 8 PM, "
            "prepare an email and create a meeting agenda."
        ),
    )

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "🚀 Run BHAI Master",
            type="primary",
            use_container_width=True,
        ):

            if not request.strip():

                st.warning(
                    "Please enter a request."
                )

                return

            agents = detect_agents(
                request
            )

            st.session_state.last_agents = agents

            st.subheader(
                "🔀 Agent Routing"
            )

            cols = st.columns(
                min(len(agents), 3)
            )

            for index, agent_id in enumerate(
                agents
            ):

                agent = AGENTS[agent_id]

                cols[
                    index
                    % len(cols)
                ].info(
                    f"{agent['icon']} "
                    f"**{agent['name']}**"
                )

            if (
                st.session_state.mode
                == "API Mode"
            ):

                combined = "\n\n".join(
                    build_agent_prompt(
                        agent_id,
                        request,
                    )
                    for agent_id in agents
                )

                result = call_openai(
                    combined,
                    system_instruction=(
                        "You are BHAI AI Master Agent. "
                        "Coordinate specialized agents "
                        "and provide one clear actionable response."
                    ),
                )

            else:

                result = demo_response(
                    request,
                    agents,
                )

            st.session_state.last_results.append(
                result
            )

            st.divider()

            st.subheader(
                "📌 BHAI Result"
            )

            st.markdown(
                result
            )

    with c2:

        st.markdown(
            """
            <div class="guide-box">

            <b>💡 Master Agent Guidance</b>

            <br><br>

            You don't need to know which agent to select.

            Simply write something like:

            <br><br>

            • "Plan my day."<br>
            • "Remind me at 8 PM."<br>
            • "Write an email to my boss."<br>
            • "Create a Python study plan."<br>
            • "Prepare my meeting agenda."<br>
            • "Make a shopping list."

            <br><br>

            BHAI will automatically detect the relevant
            agent(s).

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# CHATBOT
# ============================================================

def render_chatbot():

    st.title(
        "💬 BHAI Chatbot"
    )

    st.caption(
        "Chat naturally with BHAI AI."
    )

    for message in st.session_state.chat_messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

    prompt = st.chat_input(
        "Ask BHAI anything..."
    )

    if prompt:

        st.session_state.chat_messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with st.chat_message("user"):

            st.markdown(prompt)

        agents = detect_agents(
            prompt
        )

        if (
            st.session_state.mode
            == "API Mode"
        ):

            result = call_openai(
                prompt,
                system_instruction=(
                    "You are BHAI AI.\n"
                    f"Relevant agents: "
                    f"{', '.join(AGENTS[a]['name'] for a in agents)}.\n"
                    "Answer professionally and practically."
                ),
            )

        else:

            result = demo_response(
                prompt,
                agents,
            )

        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": result,
            }
        )

        with st.chat_message(
            "assistant"
        ):

            st.markdown(result)


# ============================================================
# AGENT DIRECTORY
# ============================================================

def render_agent_directory():

    st.title(
        "🤖 BHAI Agent Center"
    )

    st.caption(
        "Every agent has its own dedicated workspace, "
        "guidance and example prompts."
    )

    st.divider()

    if (
        st.session_state.selected_agent
        and st.session_state.get(
            "agent_page",
            False,
        )
    ):

        render_single_agent(
            st.session_state.selected_agent
        )

        return

    search = st.text_input(
        "🔎 Search Agents",
        placeholder=(
            "Search Planner, Email, Research..."
        ),
    )

    filtered_agents = []

    for agent_id, agent in AGENTS.items():

        if not search.strip():

            filtered_agents.append(
                agent_id
            )

        elif (
            search.lower()
            in agent["name"].lower()
            or
            search.lower()
            in agent["description"].lower()
        ):

            filtered_agents.append(
                agent_id
            )

    st.write(
        f"**{len(filtered_agents)} agents available**"
    )

    cols = st.columns(3)

    for index, agent_id in enumerate(
        filtered_agents
    ):

        agent = AGENTS[agent_id]

        with cols[index % 3]:

            st.markdown(
                f"""
                <div class="agent-card">

                <div class="agent-icon">
                {agent['icon']}
                </div>

                <div class="agent-name">
                {agent_id}. {agent['name']}
                </div>

                <div class="agent-description">
                {agent['description']}
                </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                f"Open {agent['short']} Agent",
                key=f"open_agent_{agent_id}",
                use_container_width=True,
            ):

                st.session_state.selected_agent = agent_id
                st.session_state.agent_page = True

                st.rerun()


# ============================================================
# SINGLE AGENT PAGE
# ============================================================

def render_single_agent(
    agent_id
):

    agent = AGENTS[agent_id]

    if st.button(
        "⬅️ Back to Agent Center"
    ):

        st.session_state.agent_page = False
        st.session_state.selected_agent = None

        st.rerun()

    st.divider()

    st.markdown(
        f"""
        <div class="hero">

        <div style="font-size:60px;">
        {agent['icon']}
        </div>

        <div class="main-title">
        {agent['name']}
        </div>

        <div class="subtitle">
        {agent['description']}
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns(
        [1, 1]
    )

    with left:

        st.subheader(
            "📘 Agent Guidance"
        )

        for item in agent[
            "guidance"
        ]:

            st.markdown(
                f"✅ {item}"
            )

    with right:

        st.subheader(
            "💡 Example Requests"
        )

        for example in agent[
            "examples"
        ]:

            st.code(
                example,
                language="text",
            )

    st.divider()

    st.subheader(
        f"{agent['icon']} Talk to {agent['name']}"
    )

    prompt = st.text_area(
        "Your request",
        height=170,
        placeholder=(
            "Write your request here..."
        ),
        key=f"single_agent_prompt_{agent_id}",
    )

    c1, c2 = st.columns(2)

    with c1:

        run = st.button(
            "🚀 Run Agent",
            type="primary",
            use_container_width=True,
            key=f"run_single_{agent_id}",
        )

    with c2:

        if st.button(
            "🧹 Clear",
            use_container_width=True,
            key=f"clear_single_{agent_id}",
        ):

            st.session_state[
                f"single_agent_prompt_{agent_id}"
            ] = ""

            st.rerun()

    if run:

        if not prompt.strip():

            st.warning(
                "Please enter a request."
            )

            return

        with st.spinner(
            f"{agent['name']} is working..."
        ):

            if (
                st.session_state.mode
                == "API Mode"
            ):

                result = call_openai(
                    build_agent_prompt(
                        agent_id,
                        prompt,
                    ),
                    system_instruction=(
                        f"You are the {agent['name']} "
                        "of BHAI AI. "
                        "Focus only on your assigned role."
                    ),
                )

            else:

                result = demo_response(
                    prompt,
                    [agent_id],
                )

        st.divider()

        st.subheader(
            "📌 Agent Result"
        )

        st.markdown(
            result
        )


# ============================================================
# REMINDERS / SCHEDULES
# ============================================================

def render_schedules():

    st.title(
        "⏰ Reminders, Alarms & Schedules"
    )

    st.caption(
        "Create future reminders and email notifications."
    )

    with st.form(
        "schedule_form"
    ):

        action = st.selectbox(
            "Action",
            [
                "System Alarm",
                "Email Notification",
            ],
        )

        title = st.text_input(
            "Title",
            "BHAI Reminder",
        )

        message = st.text_area(
            "Message",
            "This is your scheduled reminder.",
        )

        recipient = ""
        subject = ""

        if action == "Email Notification":

            recipient = st.text_input(
                "Recipient Email"
            )

            subject = st.text_input(
                "Email Subject",
                title,
            )

        run_date = st.date_input(
            "Date",
            value=datetime.now().date(),
        )

        run_time = st.time_input(
            "Time",
            value=(
                datetime.now()
                + timedelta(minutes=5)
            ).time(),
        )

        submitted = st.form_submit_button(
            "⏰ Create Schedule"
        )

    if submitted:

        run_at = datetime.combine(
            run_date,
            run_time,
        )

        if run_at <= datetime.now():

            st.error(
                "Please select a future date/time."
            )

            return

        if (
            action
            == "Email Notification"
            and not recipient.strip()
        ):

            st.error(
                "Recipient email is required."
            )

            return

        schedule_id = add_schedule_db(
            (
                "email"
                if action
                == "Email Notification"
                else "alarm"
            ),
            title,
            message,
            recipient,
            subject,
            run_at,
        )

        if (
            action
            == "Email Notification"
        ):

            ok, msg = schedule_email(
                schedule_id,
                recipient,
                subject,
                message,
                run_at,
            )

            if ok:

                st.success(msg)

            else:

                st.warning(
                    f"Saved in database, "
                    f"but scheduler setup failed: {msg}"
                )

        else:

            st.success(
                "⏰ System alarm saved for "
                f"{run_at.strftime('%Y-%m-%d %H:%M')}"
            )

    st.divider()

    st.subheader(
        "📋 Existing Schedules"
    )

    rows = get_schedules()

    if not rows:

        st.info(
            "No schedules found."
        )

        return

    for row in rows:

        with st.container(
            border=True
        ):

            st.write(
                f"**{row['title']}**"
            )

            st.write(
                f"Action: `{row['action_type']}`"
            )

            st.write(
                f"Run at: `{row['run_at']}`"
            )

            st.write(
                f"Status: `{row['status']}`"
            )

            if row["status"] == "Scheduled":

                if st.button(
                    "Cancel",
                    key=f"cancel_{row['id']}",
                ):

                    cancel_schedule(
                        row["id"]
                    )

                    st.rerun()


# ============================================================
# CONTACTS
# ============================================================

def render_contacts():

    st.title(
        "👥 Contacts"
    )

    with st.form(
        "contact_form"
    ):

        name = st.text_input(
            "Name"
        )

        email = st.text_input(
            "Email"
        )

        submitted = st.form_submit_button(
            "➕ Add Contact"
        )

    if submitted:

        if (
            not name.strip()
            or
            not email.strip()
        ):

            st.error(
                "Name and email are required."
            )

        else:

            add_contact_db(
                name,
                email,
            )

            st.success(
                "Contact added."
            )

            st.rerun()

    st.divider()

    rows = get_contacts()

    if not rows:

        st.info(
            "No contacts available."
        )

        return

    for row in rows:

        c1, c2, c3 = st.columns(
            [2, 3, 1]
        )

        c1.write(
            row["name"]
        )

        c2.write(
            row["email"]
        )

        if c3.button(
            "Delete",
            key=f"del_{row['id']}",
        ):

            delete_contact(
                row["id"]
            )

            st.rerun()


# ============================================================
# EMAIL GENERATOR
# ============================================================

def render_email_generator():

    st.title(
        "📧 Email Generator"
    )

    st.caption(
        "Generate professional emails using the Email Agent."
    )

    recipient = st.text_input(
        "Recipient Name / Email"
    )

    purpose = st.text_area(
        "Email Purpose",
        height=130,
        placeholder=(
            "Example: Request approval for an AI workshop."
        ),
    )

    tone = st.selectbox(
        "Tone",
        [
            "Professional",
            "Friendly",
            "Formal",
            "Short",
        ],
    )

    if st.button(
        "✉️ Generate Email",
        type="primary",
    ):

        if not purpose.strip():

            st.warning(
                "Enter the email purpose."
            )

            return

        if (
            st.session_state.mode
            == "API Mode"
        ):

            result = call_openai(
                f"""
Create a professional email.

Recipient:
{recipient}

Purpose:
{purpose}

Tone:
{tone}

Return:

Subject:
Body:
""",
                system_instruction=(
                    "You are the BHAI Email Agent."
                ),
            )

        else:

            result = (
                f"Subject: Regarding "
                f"{purpose[:60]}\n\n"
                f"Dear "
                f"{recipient or 'Sir/Madam'},\n\n"
                f"I am writing regarding "
                f"{purpose}.\n\n"
                "Kind regards,\n"
                "BHAI AI"
            )

        st.session_state.generated_emails.append(
            result
        )

        st.text_area(
            "Generated Email",
            result,
            height=320,
        )


# ============================================================
# DOCUMENT GENERATOR
# ============================================================

def render_documents():

    st.title(
        "📄 Word / PDF Generator"
    )

    st.caption(
        "Create professional Word and PDF documents."
    )

    title = st.text_input(
        "Document Title",
        "BHAI AI Document",
    )

    body = st.text_area(
        "Document Content",
        height=320,
        placeholder=(
            "Write your report, proposal, "
            "letter or document content here..."
        ),
    )

    if st.button(
        "📄 Generate Documents",
        type="primary",
    ):

        if not body.strip():

            st.warning(
                "Enter document content."
            )

            return

        word_data = create_word(
            title,
            body,
        )

        pdf_data = create_pdf(
            title,
            body,
        )

        c1, c2 = st.columns(2)

        with c1:

            if word_data:

                st.download_button(
                    "⬇️ Download Word",
                    data=word_data,
                    file_name="bhai_document.docx",
                    mime=(
                        "application/"
                        "vnd.openxmlformats-officedocument."
                        "wordprocessingml.document"
                    ),
                    use_container_width=True,
                )

            else:

                st.error(
                    "python-docx is not installed."
                )

        with c2:

            if pdf_data:

                st.download_button(
                    "⬇️ Download PDF",
                    data=pdf_data,
                    file_name="bhai_document.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            else:

                st.error(
                    "reportlab is not installed."
                )


# ============================================================
# API MANAGEMENT
# ============================================================

def render_api_management():

    st.title(
        "🔐 API Management"
    )

    st.caption(
        "Securely manage the API configuration for BHAI AI."
    )

    c1, c2 = st.columns(2)

    with c1:

        st.subheader(
            "🔑 API Status"
        )

        if get_api_key():

            st.success(
                api_status()
            )

        else:

            st.warning(
                api_status()
            )

        st.write(
            f"**Source:** "
            f"{get_api_key_source()}"
        )

        st.write(
            f"**Key:** "
            f"`{mask_key(get_api_key())}`"
        )

    with c2:

        st.subheader(
            "🧠 Model"
        )

        secret_model = get_secret(
            "OPENAI_MODEL"
        )

        if secret_model:

            st.caption(
                f"Secrets model: `{secret_model}`"
            )

        st.session_state.model = st.text_input(
            "OpenAI API Model",
            value=(
                st.session_state.model
                or DEFAULT_MODEL
            ),
        )

    st.divider()

    st.subheader(
        "1️⃣ Streamlit Secrets"
    )

    st.code(
        """
# .streamlit/secrets.toml

OPENAI_API_KEY = "sk-your-key-here"
OPENAI_MODEL = "gpt-6-luna"

# Optional SMTP

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"
SMTP_FROM = "your-email@gmail.com"
""",
        language="toml",
    )

    st.warning(
        "Never upload secrets.toml to GitHub."
    )

    st.divider()

    st.subheader(
        "2️⃣ Temporary Session API Key"
    )

    entered_key = st.text_input(
        "OpenAI API Key",
        value=st.session_state.manual_api_key,
        type="password",
        placeholder="sk-...",
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button(
            "💾 Use Session Key",
            use_container_width=True,
        ):

            st.session_state.manual_api_key = (
                entered_key.strip()
            )

            st.success(
                "Session key updated."
            )

            st.rerun()

    with c2:

        if st.button(
            "🧪 Test API",
            use_container_width=True,
        ):

            with st.spinner(
                "Testing API..."
            ):

                ok, msg = (
                    test_openai_connection()
                )

            st.session_state.api_test_result = (
                ok,
                msg,
            )

    with c3:

        if st.button(
            "🗑️ Clear Session Key",
            use_container_width=True,
        ):

            st.session_state.manual_api_key = ""

            st.session_state.api_test_result = None

            st.rerun()

    if st.session_state.api_test_result:

        ok, msg = (
            st.session_state.api_test_result
        )

        if ok:

            st.success(msg)

        else:

            st.error(msg)

    st.divider()

    st.subheader(
        "3️⃣ Environment Variable"
    )

    st.code(
        """
Windows CMD:

set OPENAI_API_KEY=sk-your-key-here


PowerShell:

$env:OPENAI_API_KEY="sk-your-key-here"


Linux/macOS:

export OPENAI_API_KEY="sk-your-key-here"
""",
        language="bash",
    )

    st.divider()

    st.subheader(
        "🔒 Security Guidance"
    )

    st.markdown(
        """
        ✅ Prefer Streamlit Secrets for deployment.

        ✅ Do not hard-code API keys in Python.

        ✅ Do not store API keys in SQLite.

        ✅ Do not commit secrets.toml to GitHub.

        ✅ Use API keys with appropriate project permissions.

        ✅ Rotate a key immediately if it becomes exposed.

        ✅ API credits/quota are separate from the application itself.
        """
    )


# ============================================================
# ROUTING
# ============================================================

if page == "🏠 Dashboard":

    render_dashboard()

elif page == "🧠 BHAI Master":

    render_master()

elif page == "💬 BHAI Chatbot":

    render_chatbot()

elif page == "🤖 AGENTS":

    render_agent_directory()

elif page == "⏰ Reminders & Schedules":

    render_schedules()

elif page == "👥 Contacts":

    render_contacts()

elif page == "📧 Email Generator":

    render_email_generator()

elif page == "📄 Word/PDF Generator":

    render_documents()

elif page == "🔐 API Management":

    render_api_management()


# ============================================================
# WELCOME POPUP
# ============================================================

show_welcome_popup()


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">

    <b>🤖 BHAI AI</b><br>

    Master Agent for Intelligent Daily Routine Automation

    <br><br>

    21 Specialized AI Agents • Demo Mode • API Mode

    <br><br>

    <b>By Engr. Bilal Mehmood</b>

    </div>
    """,
    unsafe_allow_html=True,
)
```

### `requirements.txt`

Is code ke saath ye `requirements.txt` rakhein:

```text
streamlit
openai
python-dateutil
dateparser
apscheduler
python-docx
reportlab
```

### Streamlit Secrets

`.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "sk-your-api-key"
OPENAI_MODEL = "gpt-6-luna"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-gmail-app-password"
SMTP_FROM = "your-email@gmail.com"
```

**Important:** `secrets.toml` ko GitHub par upload na karein.

### Is version mein navigation ka flow

```text
🤖 BHAI AI
│
├── 🏠 Dashboard
│
├── 🧠 BHAI Master
│     └── Automatic Agent Routing
│
├── 💬 BHAI Chatbot
│
├── 🤖 AGENTS
│     ├── 🗓️ Planner
│     ├── ⏰ Reminder
│     ├── 📅 Calendar
│     ├── ✅ Task
│     ├── 🚀 Productivity
│     ├── 📚 Learning
│     ├── 🔬 Research
│     ├── 💬 Communication
│     ├── 📧 Email
│     ├── 🤝 Meeting
│     ├── ❤️ Health
│     ├── 🏃 Fitness
│     ├── 💰 Finance
│     ├── 🛒 Shopping
│     ├── ✈️ Travel
│     ├── 📰 News
│     ├── 📝 Notes
│     ├── 📁 File
│     ├── 🏠 Home
│     ├── 🎮 Entertainment
│     └── 🔔 Email Notification
│
├── ⏰ Reminders & Schedules
├── 👥 Contacts
├── 📧 Email Generator
├── 📄 Word/PDF Generator
└── 🔐 API Management
```

**Welcome popup** application open hote hi BHAI ka introduction, 21 agents, Demo/API modes, workflow aur quick-start guidance show karega. Sidebar mein **👋 Show Welcome Guide** se usay dobara bhi khola ja sakta hai.

Aapke existing design ke muqablay mein ye structure zyada scalable hai: **Master Agent → Intent Detection → Individual Agent → Action/Response**, aur har agent ka apna guidance panel hai.
