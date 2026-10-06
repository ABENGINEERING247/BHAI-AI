import os
import io
import re
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
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
except ImportError:
    A4 = None
    SimpleDocTemplate = None
    Paragraph = None
    Spacer = None
    getSampleStyleSheet = None


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="BHAI AI - Master Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# APPLICATION SETTINGS
# ============================================================

APP_NAME = "BHAI AI"
APP_VERSION = "5.0"
DEFAULT_MODEL = "gpt-6-luna"
DB_FILE = "bhai_ai.db"


# ============================================================
# BLUE / WHITE STREAMLIT THEME
# NO HTML
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f7fbff;
    }

    [data-testid="stSidebar"] {
        background-color: #eef6ff;
    }

    .stButton > button {
        border-radius: 8px;
        font-weight: 700;
    }

    .stTextInput input,
    .stTextArea textarea {
        border-radius: 8px;
    }

    [data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #d5e8ff;
        border-radius: 12px;
        padding: 10px;
    }

    [data-testid="stExpander"] {
        border-radius: 10px;
        border: 1px solid #d5e8ff;
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
    "selected_agent": 1,
    "agent_page": False,
    "chat_messages": [],
    "last_results": [],
    "last_agents": [],
    "generated_emails": [],
    "api_test_result": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# AGENTS
# ============================================================

AGENTS = {
    1: {
        "icon": "🗓️",
        "name": "Planner Agent",
        "description": "Creates daily, weekly and project plans.",
        "guidance": "Convert goals into practical schedules and action plans.",
        "examples": [
            "Create my daily plan",
            "Make a weekly work plan",
            "Plan my project tasks",
        ],
    },
    2: {
        "icon": "⏰",
        "name": "Reminder Agent",
        "description": "Creates reminders, alerts and scheduled activities.",
        "guidance": "Identify reminder date, time and message.",
        "examples": [
            "Remind me at 5 PM",
            "Set a reminder for tomorrow",
            "Alarm me about the meeting",
        ],
    },
    3: {
        "icon": "📅",
        "name": "Calendar Agent",
        "description": "Manages appointments, events and schedules.",
        "guidance": "Organize meetings, appointments and calendar activities.",
        "examples": [
            "Schedule a meeting",
            "Create an appointment",
            "Plan tomorrow's events",
        ],
    },
    4: {
        "icon": "✅",
        "name": "Task Agent",
        "description": "Manages tasks, to-do lists and work items.",
        "guidance": "Convert requests into actionable tasks.",
        "examples": [
            "Create my task list",
            "Add a new task",
            "Show today's tasks",
        ],
    },
    5: {
        "icon": "🚀",
        "name": "Productivity Agent",
        "description": "Improves workflow, productivity and automation.",
        "guidance": "Optimize routine activities and workflows.",
        "examples": [
            "Improve my workflow",
            "Automate repetitive work",
            "Create a productive routine",
        ],
    },
    6: {
        "icon": "📚",
        "name": "Learning Agent",
        "description": "Supports learning, courses, study and education.",
        "guidance": "Create learning plans, explanations and study material.",
        "examples": [
            "Teach me Python",
            "Create a study plan",
            "Explain machine learning",
        ],
    },
    7: {
        "icon": "🔬",
        "name": "Research Agent",
        "description": "Supports research, literature review and analysis.",
        "guidance": "Structure research ideas and academic workflows.",
        "examples": [
            "Create a research methodology",
            "Prepare literature review points",
            "Suggest research topics",
        ],
    },
    8: {
        "icon": "💬",
        "name": "Communication Agent",
        "description": "Creates professional messages and communication.",
        "guidance": "Prepare clear and professional communication.",
        "examples": [
            "Write a WhatsApp message",
            "Write a professional message",
            "Prepare an announcement",
        ],
    },
    9: {
        "icon": "📧",
        "name": "Email Agent",
        "description": "Drafts professional emails.",
        "guidance": "Create concise and professional email messages.",
        "examples": [
            "Write an official email",
            "Draft a meeting email",
            "Write a leave request",
        ],
    },
    10: {
        "icon": "🤝",
        "name": "Meeting Agent",
        "description": "Prepares meeting agendas, minutes and action points.",
        "guidance": "Organize meeting preparation and follow-up.",
        "examples": [
            "Create a meeting agenda",
            "Prepare meeting minutes",
            "Create action points",
        ],
    },
    11: {
        "icon": "❤️",
        "name": "Health Agent",
        "description": "Provides general wellness and healthy routine guidance.",
        "guidance": "Provide general wellness-oriented suggestions.",
        "examples": [
            "Create a healthy routine",
            "Suggest wellness habits",
            "Improve my daily routine",
        ],
    },
    12: {
        "icon": "🏃",
        "name": "Fitness Agent",
        "description": "Helps organize exercise and fitness routines.",
        "guidance": "Create practical fitness and exercise routines.",
        "examples": [
            "Create a workout routine",
            "Plan weekly exercise",
            "Create a walking routine",
        ],
    },
    13: {
        "icon": "💰",
        "name": "Finance Agent",
        "description": "Helps organize budgets, expenses and savings.",
        "guidance": "Structure personal finance information.",
        "examples": [
            "Create a monthly budget",
            "Track expenses",
            "Create a saving plan",
        ],
    },
    14: {
        "icon": "🛒",
        "name": "Shopping Agent",
        "description": "Creates shopping and purchasing lists.",
        "guidance": "Organize purchases, groceries and shopping requirements.",
        "examples": [
            "Create a grocery list",
            "Make a shopping list",
            "Organize my purchases",
        ],
    },
    15: {
        "icon": "✈️",
        "name": "Travel Agent",
        "description": "Plans trips, itineraries and travel activities.",
        "guidance": "Create structured travel plans and itineraries.",
        "examples": [
            "Plan a trip",
            "Create a travel itinerary",
            "Plan a weekend tour",
        ],
    },
    16: {
        "icon": "📰",
        "name": "News Agent",
        "description": "Helps organize news and current-information requests.",
        "guidance": "Summarize or structure requested news information.",
        "examples": [
            "Give me latest news",
            "Summarize today's news",
            "Find technology news",
        ],
    },
    17: {
        "icon": "📝",
        "name": "Notes Agent",
        "description": "Creates, organizes and summarizes notes.",
        "guidance": "Convert information into organized notes.",
        "examples": [
            "Create notes",
            "Summarize this topic",
            "Organize my notes",
        ],
    },
    18: {
        "icon": "📁",
        "name": "File Agent",
        "description": "Helps create and organize documents and files.",
        "guidance": "Prepare content for Word, PDF and reports.",
        "examples": [
            "Create a report",
            "Prepare a PDF",
            "Create a Word document",
        ],
    },
    19: {
        "icon": "🏠",
        "name": "Home Agent",
        "description": "Organizes home-related routines and activities.",
        "guidance": "Create household routines and task lists.",
        "examples": [
            "Create a cleaning plan",
            "Organize home tasks",
            "Create a weekly home routine",
        ],
    },
    20: {
        "icon": "🎮",
        "name": "Entertainment Agent",
        "description": "Handles games, entertainment and leisure activities.",
        "guidance": "Suggest or organize entertainment activities.",
        "examples": [
            "Suggest a game",
            "Plan entertainment activities",
            "Let's play chess",
        ],
    },
    21: {
        "icon": "🔔",
        "name": "Email Notification Agent",
        "description": "Handles scheduled email notifications and system alarms.",
        "guidance": "Create scheduled notification and email activities.",
        "examples": [
            "Schedule an email",
            "Set a system alarm",
            "Notify me tomorrow",
        ],
    },
}


# ============================================================
# KEYWORD ROUTING
# ============================================================

KEYWORD_ROUTING = {
    1: [
        "plan",
        "planning",
        "daily plan",
        "weekly plan",
        "routine",
    ],
    2: [
        "remind",
        "reminder",
        "alert",
        "yaad",
        "alarm",
    ],
    3: [
        "calendar",
        "appointment",
        "event",
        "schedule",
    ],
    4: [
        "task",
        "todo",
        "to do",
        "kaam",
    ],
    5: [
        "productivity",
        "productive",
        "workflow",
        "automation",
    ],
    6: [
        "learn",
        "learning",
        "study",
        "course",
        "class",
        "education",
    ],
    7: [
        "research",
        "research paper",
        "literature",
        "methodology",
    ],
    8: [
        "message",
        "communication",
        "whatsapp",
        "sms",
    ],
    9: [
        "email",
        "mail",
        "send email",
        "email kar",
    ],
    10: [
        "meeting",
        "agenda",
        "minutes",
        "mom",
    ],
    11: [
        "health",
        "wellness",
        "healthy",
        "sleep",
    ],
    12: [
        "fitness",
        "exercise",
        "workout",
        "gym",
    ],
    13: [
        "finance",
        "money",
        "budget",
        "expense",
        "saving",
    ],
    14: [
        "shopping",
        "buy",
        "purchase",
        "grocery",
    ],
    15: [
        "travel",
        "trip",
        "flight",
        "hotel",
        "tour",
    ],
    16: [
        "news",
        "latest news",
        "current affairs",
    ],
    17: [
        "note",
        "notes",
        "remember",
        "summarize",
    ],
    18: [
        "file",
        "document",
        "word",
        "pdf",
        "report",
    ],
    19: [
        "home",
        "house",
        "cleaning",
    ],
    20: [
        "game",
        "games",
        "entertainment",
        "movie",
        "chess",
    ],
    21: [
        "notification",
        "notify",
        "scheduled email",
        "automatic email",
        "system alarm",
    ],
}


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
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                title TEXT NOT NULL,
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
            (name, email, created_at)
            VALUES (?, ?, ?)
            """,
            (
                name,
                email,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()


def get_contacts():
    with db_lock:
        conn = get_db()
        rows = conn.execute(
            """
            SELECT *
            FROM contacts
            ORDER BY id DESC
            """
        ).fetchall()
        conn.close()
        return rows


def delete_contact(contact_id):
    with db_lock:
        conn = get_db()
        conn.execute(
            "DELETE FROM contacts WHERE id = ?",
            (contact_id,),
        )
        conn.commit()
        conn.close()


# ============================================================
# SCHEDULE DATABASE FUNCTIONS
# ============================================================

def add_schedule_db(
    action_type,
    title,
    message,
    recipient,
    subject,
    run_at,
):
    with db_lock:
        conn = get_db()

        conn.execute(
            """
            INSERT INTO schedules
            (
                action_type,
                title,
                message,
                recipient,
                subject,
                run_at,
                recurrence,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                action_type,
                title,
                message,
                recipient,
                subject,
                run_at,
                "once",
                "Scheduled",
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()


def get_schedules():
    with db_lock:
        conn = get_db()

        rows = conn.execute(
            """
            SELECT *
            FROM schedules
            ORDER BY run_at DESC
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
            SET status = 'Cancelled'
            WHERE id = ?
            """,
            (schedule_id,),
        )

        conn.commit()
        conn.close()


# ============================================================
# API / SECRETS MANAGEMENT
# ============================================================

def get_secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def get_api_key_source():
    secret_key = get_secret("OPENAI_API_KEY")

    if secret_key:
        return "Streamlit Secrets"

    env_key = os.getenv("OPENAI_API_KEY")

    if env_key:
        return "Environment Variable"

    if st.session_state.get("manual_api_key"):
        return "Session API Key"

    return "Not Configured"


def get_api_key():
    secret_key = get_secret("OPENAI_API_KEY")

    if secret_key:
        return secret_key

    env_key = os.getenv("OPENAI_API_KEY")

    if env_key:
        return env_key

    return st.session_state.get(
        "manual_api_key",
        "",
    )


def get_model():
    session_model = st.session_state.get(
        "model",
        "",
    ).strip()

    if session_model:
        return session_model

    secret_model = get_secret(
        "OPENAI_MODEL",
        DEFAULT_MODEL,
    )

    return secret_model


def mask_key(key):
    if not key:
        return "Not configured"

    if len(key) <= 10:
        return "********"

    return (
        key[:5]
        + "..."
        + key[-4:]
    )


def api_status():
    if OpenAI is None:
        return "OpenAI package not installed"

    if get_api_key():
        return "API Ready"

    return "API Key Missing"


# ============================================================
# OPENAI CALL
# ============================================================

def call_openai(
    prompt,
    system_instruction=None,
):
    if OpenAI is None:
        return (
            "OpenAI package is not installed. "
            "Install it with: pip install openai"
        )

    api_key = get_api_key()

    if not api_key:
        return (
            "OpenAI API key is not configured. "
            "Please add OPENAI_API_KEY in Streamlit Secrets "
            "or use API Management."
        )

    try:
        client = OpenAI(
            api_key=api_key
        )

        if not system_instruction:
            system_instruction = (
                "You are BHAI AI, a master AI assistant "
                "that coordinates specialized agents. "
                "Provide useful, clear and professional answers."
            )

        response = client.responses.create(
            model=get_model(),
            instructions=system_instruction,
            input=prompt,
        )

        return response.output_text

    except Exception as e:
        error_text = str(e)

        if (
            "429" in error_text
            or "quota" in error_text.lower()
            or "credit" in error_text.lower()
            or "insufficient" in error_text.lower()
        ):
            return (
                "OpenAI API Error: Your API account appears "
                "to have insufficient credits/quota. "
                "Please check your API billing and credits."
            )

        return f"OpenAI Error: {error_text}"


def test_openai_connection():
    result = call_openai(
        "Reply with exactly: BHAI AI API connection successful."
    )

    return result


# ============================================================
# ROUTING
# ============================================================

def detect_agents(text):
    text = text.lower()

    detected = []

    for agent_id, keywords in KEYWORD_ROUTING.items():

        for keyword in keywords:

            if keyword.lower() in text:
                detected.append(agent_id)
                break

    if not detected:
        detected = [1]

    return detected[:5]


# ============================================================
# AGENT PROMPT
# ============================================================

def build_agent_prompt(
    agent_id,
    request,
):
    agent = AGENTS[agent_id]

    return f"""
You are the {agent["name"]} of BHAI AI.

Agent description:
{agent["description"]}

Agent guidance:
{agent["guidance"]}

User request:
{request}

Perform the task professionally.

Give practical, structured and easy-to-understand output.

If dates, times, names or other information are missing,
make reasonable assumptions only when appropriate and clearly
state those assumptions.
"""


# ============================================================
# DEMO MODE
# ============================================================

def demo_response(
    request,
    agent_ids,
):
    lines = []

    lines.append(
        "## 🤖 BHAI AI Demo Mode"
    )

    lines.append(
        f"**Request:** {request}"
    )

    lines.append(
        ""
    )

    lines.append(
        "### Agents Activated"
    )

    for agent_id in agent_ids:
        agent = AGENTS[agent_id]

        lines.append(
            f"- {agent['icon']} **{agent['name']}**"
        )

    lines.append(
        ""
    )

    lines.append(
        "### Demo Result"
    )

    lines.append(
        "BHAI AI has analyzed the request and routed it "
        "to the appropriate specialized agent(s)."
    )

    lines.append(
        ""
    )

    lines.append(
        "Switch to **API Mode** and configure your OpenAI API "
        "key to receive AI-generated responses."
    )

    return "\n".join(lines)


# ============================================================
# ROMAN URDU NORMALIZATION
# ============================================================

def normalize_roman_urdu(text):

    replacements = {
        "krdo": "kar do",
        "kardo": "kar do",
        "krna": "karna",
        "bnao": "banao",
        "banao": "banao",
        "likho": "likho",
        "mujhe": "mujhe",
        "chahiye": "chahiye",
        "kal": "tomorrow",
        "aj": "today",
        "aaj": "today",
        "subha": "morning",
        "shaam": "evening",
        "raat": "night",
    }

    result = text.lower()

    for old, new in replacements.items():
        result = re.sub(
            rf"\b{re.escape(old)}\b",
            new,
            result,
        )

    return result


# ============================================================
# DATE / TIME PARSER
# ============================================================

def parse_datetime_text(text):

    normalized = normalize_roman_urdu(text)

    if dateparser is not None:

        try:
            parsed = dateparser.parse(
                normalized,
                settings={
                    "PREFER_DATES_FROM": "future",
                    "TIMEZONE": "Asia/Karachi",
                    "RETURN_AS_TIMEZONE_AWARE": False,
                },
            )

            if parsed:
                return parsed

        except Exception:
            pass

    now = datetime.now()

    match = re.search(
        r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b",
        normalized,
        re.IGNORECASE,
    )

    if match:

        hour = int(match.group(1))
        minute = int(match.group(2))

        meridian = match.group(3)

        if meridian:

            meridian = meridian.lower()

            if meridian == "pm" and hour < 12:
                hour += 12

            if meridian == "am" and hour == 12:
                hour = 0

        result = now.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )

        if result <= now:
            result += timedelta(days=1)

        return result

    return None


# ============================================================
# SMTP
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

    port = get_secret(
        "SMTP_PORT",
        os.getenv("SMTP_PORT", "587"),
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
        os.getenv("SMTP_FROM", username),
    )

    if not host or not username or not password:
        return (
            False,
            "SMTP configuration is incomplete."
        )

    try:
        port = int(port)

        message = MIMEMultipart()

        message["From"] = sender
        message["To"] = to_email
        message["Subject"] = subject

        message.attach(
            MIMEText(
                body,
                "plain",
            )
        )

        server = smtplib.SMTP(
            host,
            port,
            timeout=30,
        )

        server.starttls()

        server.login(
            username,
            password,
        )

        server.sendmail(
            sender,
            to_email,
            message.as_string(),
        )

        server.quit()

        return (
            True,
            "Email sent successfully."
        )

    except Exception as e:
        return (
            False,
            f"Email error: {e}"
        )


# ============================================================
# SCHEDULER
# ============================================================

scheduler = None

if BackgroundScheduler is not None:

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

    success, result = send_email_smtp(
        recipient,
        subject,
        message,
    )

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
                "Completed" if success else "Failed",
                datetime.now().isoformat(),
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

    if scheduler is None:
        return False

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

        return True

    except Exception:
        return False


# ============================================================
# DOCUMENT GENERATION
# ============================================================

def create_word(
    title,
    body,
):

    if Document is None:
        return None

    document = Document()

    document.add_heading(
        title,
        level=1,
    )

    for paragraph in body.split("\n"):
        document.add_paragraph(
            paragraph
        )

    output = io.BytesIO()

    document.save(output)

    output.seek(0)

    return output


def create_pdf(
    title,
    body,
):

    if SimpleDocTemplate is None:
        return None

    output = io.BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4,
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            title,
            styles["Title"],
        )
    )

    story.append(
        Spacer(
            1,
            15,
        )
    )

    for paragraph in body.split("\n"):

        if paragraph.strip():

            story.append(
                Paragraph(
                    paragraph,
                    styles["BodyText"],
                )
            )

            story.append(
                Spacer(
                    1,
                    8,
                )
            )

    document.build(story)

    output.seek(0)

    return output


# ============================================================
# DASHBOARD
# ============================================================

def render_dashboard():

    st.title("🤖 BHAI AI")

    st.subheader(
        "Master Agent for Intelligent Daily Routine Automation"
    )

    st.info(
        "TEAM AI MARKHORS"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Agents",
            "21",
        )

    with col2:
        st.metric(
            "Mode",
            st.session_state.mode,
        )

    with col3:
        st.metric(
            "API",
            api_status(),
        )

    with col4:
        st.metric(
            "Model",
            get_model(),
        )

    st.divider()

    st.subheader(
        "BHAI AI Capabilities"
    )

    columns = st.columns(3)

    capabilities = [
        (
            "🧠",
            "Master Agent",
            "Coordinates specialized agents.",
        ),
        (
            "🤖",
            "21 AI Agents",
            "Separate agents for daily activities.",
        ),
        (
            "⏰",
            "Schedules",
            "Reminders, alarms and notifications.",
        ),
        (
            "📧",
            "Email",
            "Generate and schedule emails.",
        ),
        (
            "📄",
            "Documents",
            "Generate Word and PDF documents.",
        ),
        (
            "🔐",
            "API Management",
            "Manage OpenAI configuration.",
        ),
    ]

    for index, item in enumerate(capabilities):

        col = columns[index % 3]

        with col:

            st.info(
                f"{item[0]} **{item[1]}**\n\n"
                f"{item[2]}"
            )

    st.divider()

    st.subheader(
        "Example"
    )

    st.code(
        "Create my daily plan, remind me at 5 PM, "
        "prepare an email for tomorrow's meeting "
        "and create a PDF report.",
        language="text",
    )

    st.caption(
        "BHAI AI automatically identifies the relevant agents."
    )


# ============================================================
# MASTER AGENT
# ============================================================

def render_master():

    st.title(
        "🧠 BHAI Master Agent"
    )

    st.write(
        "The Master Agent receives your request and routes "
        "it to the appropriate specialized agents."
    )

    request = st.text_area(
        "Enter your request",
        height=180,
        placeholder=(
            "Example: Create my daily plan, remind me at 5 PM "
            "and prepare an email for tomorrow's meeting."
        ),
    )

    if st.button(
        "🚀 Run BHAI Master Agent",
        use_container_width=True,
    ):

        if not request.strip():
            st.warning(
                "Please enter a request."
            )
            return

        agent_ids = detect_agents(
            request
        )

        st.session_state.last_agents = agent_ids

        st.subheader(
            "Agents Activated"
        )

        for agent_id in agent_ids:

            agent = AGENTS[agent_id]

            st.success(
                f"{agent['icon']} {agent['name']}"
            )

        if st.session_state.mode == "API Mode":

            results = []

            for agent_id in agent_ids:

                prompt = build_agent_prompt(
                    agent_id,
                    request,
                )

                result = call_openai(
                    prompt,
                    (
                        "You are a specialized BHAI AI agent. "
                        "Perform only the requested task "
                        "and provide practical output."
                    ),
                )

                results.append(
                    f"### {AGENTS[agent_id]['icon']} "
                    f"{AGENTS[agent_id]['name']}\n\n"
                    f"{result}"
                )

            final_result = "\n\n---\n\n".join(
                results
            )

        else:

            final_result = demo_response(
                request,
                agent_ids,
            )

        st.session_state.last_results.append(
            final_result
        )

        st.subheader(
            "Result"
        )

        st.markdown(
            final_result
        )


# ============================================================
# CHATBOT
# ============================================================

def render_chatbot():

    st.title(
        "💬 BHAI Chatbot"
    )

    st.write(
        "Chat naturally with BHAI AI."
    )

    for message in st.session_state.chat_messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

    user_message = st.chat_input(
        "Ask BHAI AI anything..."
    )

    if user_message:

        st.session_state.chat_messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        agent_ids = detect_agents(
            user_message
        )

        if st.session_state.mode == "API Mode":

            combined_prompt = []

            for agent_id in agent_ids:

                combined_prompt.append(
                    build_agent_prompt(
                        agent_id,
                        user_message,
                    )
                )

            answer = call_openai(
                "\n\n".join(
                    combined_prompt
                ),
                (
                    "You are BHAI AI Master Agent. "
                    "Coordinate the requested specialized "
                    "agents and provide one useful response."
                ),
            )

        else:

            answer = demo_response(
                user_message,
                agent_ids,
            )

        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.rerun()


# ============================================================
# AGENT CENTER
# ============================================================

def render_agent_center():

    if st.session_state.agent_page:

        agent_id = st.session_state.selected_agent

        agent = AGENTS[agent_id]

        if st.button(
            "⬅️ Back to Agent Center"
        ):
            st.session_state.agent_page = False
            st.rerun()

        st.title(
            f"{agent['icon']} {agent['name']}"
        )

        st.write(
            agent["description"]
        )

        st.info(
            agent["guidance"]
        )

        st.subheader(
            "Example Requests"
        )

        for example in agent["examples"]:
            st.write(
                f"• {example}"
            )

        request = st.text_area(
            "Enter request for this agent",
            height=180,
        )

        if st.button(
            "🚀 Run Agent",
            use_container_width=True,
        ):

            if not request.strip():

                st.warning(
                    "Please enter a request."
                )

                return

            if st.session_state.mode == "API Mode":

                result = call_openai(
                    build_agent_prompt(
                        agent_id,
                        request,
                    )
                )

            else:

                result = demo_response(
                    request,
                    [agent_id],
                )

            st.subheader(
                "Agent Result"
            )

            st.markdown(
                result
            )

        return

    st.title(
        "🤖 Agent Center"
    )

    search = st.text_input(
        "Search agents"
    ).lower()

    for agent_id, agent in AGENTS.items():

        searchable = (
            agent["name"]
            + " "
            + agent["description"]
        ).lower()

        if search and search not in searchable:
            continue

        with st.expander(
            f"{agent['icon']} {agent['name']}"
        ):

            st.write(
                agent["description"]
            )

            st.caption(
                agent["guidance"]
            )

            if st.button(
                f"Open {agent['name']}",
                key=f"open_agent_{agent_id}",
            ):

                st.session_state.selected_agent = agent_id
                st.session_state.agent_page = True

                st.rerun()


# ============================================================
# REMINDERS / SCHEDULES
# ============================================================

def render_schedules():

    st.title(
        "⏰ Reminders & Schedules"
    )

    st.write(
        "Create system alarms and scheduled email notifications."
    )

    action_type = st.selectbox(
        "Action Type",
        [
            "System Alarm",
            "Email Notification",
        ],
    )

    title = st.text_input(
        "Title"
    )

    message = st.text_area(
        "Message",
        height=120,
    )

    recipient = ""
    subject = ""

    if action_type == "Email Notification":

        recipient = st.text_input(
            "Recipient Email"
        )

        subject = st.text_input(
            "Email Subject"
        )

    schedule_date = st.date_input(
        "Date"
    )

    schedule_time = st.time_input(
        "Time"
    )

    run_at = datetime.combine(
        schedule_date,
        schedule_time,
    )

    if st.button(
        "➕ Create Schedule",
        use_container_width=True,
    ):

        if not title.strip():

            st.warning(
                "Please enter a title."
            )

        elif run_at <= datetime.now():

            st.warning(
                "Please select a future date and time."
            )

        elif (
            action_type == "Email Notification"
            and not recipient.strip()
        ):

            st.warning(
                "Please enter recipient email."
            )

        else:

            add_schedule_db(
                action_type,
                title,
                message,
                recipient,
                subject,
                run_at.isoformat(),
            )

            schedules = get_schedules()

            latest = schedules[0]

            if action_type == "Email Notification":

                scheduled = schedule_email(
                    latest["id"],
                    recipient,
                    subject,
                    message,
                    run_at,
                )

                if scheduled:

                    st.success(
                        "Email notification scheduled successfully."
                    )

                else:

                    st.warning(
                        "Schedule saved, but the email scheduler "
                        "is not available."
                    )

            else:

                st.success(
                    "System alarm saved successfully."
                )

    st.divider()

    st.subheader(
        "Existing Schedules"
    )

    schedules = get_schedules()

    if not schedules:

        st.info(
            "No schedules found."
        )

    else:

        for schedule in schedules:

            with st.expander(
                f"{schedule['action_type']} | "
                f"{schedule['title']} | "
                f"{schedule['status']}"
            ):

                st.write(
                    f"**Run At:** {schedule['run_at']}"
                )

                st.write(
                    f"**Message:** {schedule['message']}"
                )

                if schedule["recipient"]:
                    st.write(
                        f"**Recipient:** {schedule['recipient']}"
                    )

                if schedule["subject"]:
                    st.write(
                        f"**Subject:** {schedule['subject']}"
                    )

                if schedule["status"] not in [
                    "Cancelled",
                    "Completed",
                ]:

                    if st.button(
                        "Cancel",
                        key=f"cancel_schedule_{schedule['id']}",
                    ):

                        cancel_schedule(
                            schedule["id"]
                        )

                        st.rerun()


# ============================================================
# CONTACTS
# ============================================================

def render_contacts():

    st.title(
        "👥 Contacts"
    )

    st.subheader(
        "Add Contact"
    )

    name = st.text_input(
        "Name"
    )

    email = st.text_input(
        "Email"
    )

    if st.button(
        "➕ Add Contact"
    ):

        if not name.strip() or not email.strip():

            st.warning(
                "Please enter both name and email."
            )

        elif "@" not in email:

            st.warning(
                "Please enter a valid email address."
            )

        else:

            add_contact_db(
                name,
                email,
            )

            st.success(
                "Contact added successfully."
            )

            st.rerun()

    st.divider()

    st.subheader(
        "Saved Contacts"
    )

    contacts = get_contacts()

    if not contacts:

        st.info(
            "No contacts available."
        )

    for contact in contacts:

        col1, col2, col3 = st.columns(
            [3, 4, 1]
        )

        with col1:
            st.write(
                contact["name"]
            )

        with col2:
            st.write(
                contact["email"]
            )

        with col3:

            if st.button(
                "Delete",
                key=f"delete_contact_{contact['id']}",
            ):

                delete_contact(
                    contact["id"]
                )

                st.rerun()


# ============================================================
# EMAIL GENERATOR
# ============================================================

def render_email_generator():

    st.title(
        "📧 Email Generator"
    )

    recipient = st.text_input(
        "Recipient"
    )

    purpose = st.text_area(
        "Email Purpose",
        height=130,
        placeholder=(
            "Example: Request a meeting with the department."
        ),
    )

    tone = st.selectbox(
        "Tone",
        [
            "Professional",
            "Formal",
            "Friendly",
            "Short",
        ],
    )

    if st.button(
        "✉️ Generate Email",
        use_container_width=True,
    ):

        if not purpose.strip():

            st.warning(
                "Please enter the email purpose."
            )

            return

        if st.session_state.mode == "API Mode":

            prompt = f"""
Create a professional email.

Recipient:
{recipient}

Purpose:
{purpose}

Tone:
{tone}

Provide:
1. Subject
2. Email body

Do not add unnecessary explanation.
"""

            result = call_openai(
                prompt,
                "You are BHAI AI Email Agent.",
            )

        else:

            result = (
                f"Subject: {purpose}\n\n"
                f"Dear Sir/Madam,\n\n"
                f"I am writing regarding {purpose.lower()}.\n\n"
                f"Kindly consider this request.\n\n"
                f"Regards,\n"
                f"Engr. Bilal Mehmood"
            )

        st.session_state.generated_emails.append(
            {
                "recipient": recipient,
                "content": result,
            }
        )

        st.subheader(
            "Generated Email"
        )

        st.text_area(
            "Email",
            value=result,
            height=300,
        )


# ============================================================
# WORD / PDF GENERATOR
# ============================================================

def render_documents():

    st.title(
        "📄 Word / PDF Generator"
    )

    title = st.text_input(
        "Document Title"
    )

    body = st.text_area(
        "Document Content",
        height=350,
    )

    if st.button(
        "📄 Generate Documents",
        use_container_width=True,
    ):

        if not title.strip():

            st.warning(
                "Please enter a document title."
            )

            return

        if not body.strip():

            st.warning(
                "Please enter document content."
            )

            return

        word_file = create_word(
            title,
            body,
        )

        pdf_file = create_pdf(
            title,
            body,
        )

        col1, col2 = st.columns(2)

        with col1:

            if word_file:

                st.download_button(
                    "⬇️ Download Word",
                    data=word_file,
                    file_name=(
                        title.replace(" ", "_")
                        + ".docx"
                    ),
                    mime=(
                        "application/vnd.openxmlformats-"
                        "officedocument.wordprocessingml.document"
                    ),
                    use_container_width=True,
                )

            else:

                st.error(
                    "python-docx is not installed."
                )

        with col2:

            if pdf_file:

                st.download_button(
                    "⬇️ Download PDF",
                    data=pdf_file,
                    file_name=(
                        title.replace(" ", "_")
                        + ".pdf"
                    ),
                    mime="application/pdf",
                    use_container_width=True,
                )

            else:

                st.error(
                    "ReportLab is not installed."
                )


# ============================================================
# API MANAGEMENT
# ============================================================

def render_api_management():

    st.title(
        "🔐 API Management"
    )

    st.write(
        "Manage your API configuration without changing the application code."
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "API Status",
            api_status(),
        )

    with col2:

        st.metric(
            "API Source",
            get_api_key_source(),
        )

    with col3:

        st.metric(
            "Model",
            get_model(),
        )

    st.divider()

    st.subheader(
        "Current API Key"
    )

    st.code(
        mask_key(
            get_api_key()
        )
    )

    st.subheader(
        "Model"
    )

    model = st.text_input(
        "OpenAI Model",
        value=st.session_state.model,
    )

    if st.button(
        "💾 Save Model"
    ):

        st.session_state.model = model.strip()

        st.success(
            "Model setting saved for this session."
        )

    st.divider()

    st.subheader(
        "Temporary Session API Key"
    )

    manual_key = st.text_input(
        "API Key",
        value=st.session_state.manual_api_key,
        type="password",
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button(
            "🔑 Use This Key",
            use_container_width=True,
        ):

            st.session_state.manual_api_key = manual_key

            st.success(
                "Temporary session API key saved."
            )

    with col2:

        if st.button(
            "🧪 Test API",
            use_container_width=True,
        ):

            result = test_openai_connection()

            st.session_state.api_test_result = result

    with col3:

        if st.button(
            "🗑️ Clear Session Key",
            use_container_width=True,
        ):

            st.session_state.manual_api_key = ""

            st.success(
                "Session API key cleared."
            )

    if st.session_state.api_test_result:

        st.subheader(
            "API Test Result"
        )

        st.info(
            st.session_state.api_test_result
        )

    st.divider()

    st.subheader(
        "Recommended Streamlit Secrets"
    )

    st.code(
        '''OPENAI_API_KEY = "sk-your-api-key"
OPENAI_MODEL = "gpt-6-luna"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"
SMTP_FROM = "your-email@gmail.com"''',
        language="toml",
    )

    st.subheader(
        "Environment Variables"
    )

    st.code(
        """Windows CMD:
set OPENAI_API_KEY=your_api_key

Windows PowerShell:
$env:OPENAI_API_KEY="your_api_key"

Linux / macOS:
export OPENAI_API_KEY="your_api_key"
""",
        language="text",
    )

    st.warning(
        "Never publish your API key inside GitHub source code. "
        "Use Streamlit Secrets or environment variables."
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title(
        "🤖 BHAI AI"
    )

    st.caption(
        "Master Agent"
    )

    st.divider()

    st.subheader(
        "Operating Mode"
    )

    st.session_state.mode = st.radio(
        "Select Mode",
        [
            "Demo Mode",
            "API Mode",
        ],
        index=(
            0
            if st.session_state.mode == "Demo Mode"
            else 1
        ),
    )

    st.divider()

    st.subheader(
        "Navigation"
    )

    page = st.radio(
        "Main Menu",
        [
            "🏠 Dashboard",
            "🧠 BHAI Master",
            "💬 BHAI Chatbot",
            "🤖 Agent Center",
            "⏰ Reminders & Schedules",
            "👥 Contacts",
            "📧 Email Generator",
            "📄 Word/PDF Generator",
            "🔐 API Management",
        ],
    )

    st.divider()

    st.subheader(
        "Individual Agent"
    )

    agent_options = {
        f"{agent['icon']} {agent['name']}": agent_id
        for agent_id, agent in AGENTS.items()
    }

    selected_agent_name = st.selectbox(
        "Select Agent",
        list(agent_options.keys()),
    )

    if st.button(
        "Open Selected Agent",
        use_container_width=True,
    ):

        st.session_state.selected_agent = (
            agent_options[selected_agent_name]
        )

        st.session_state.agent_page = True

        page = "🤖 Agent Center"

    st.divider()

    st.caption(
        f"Version {APP_VERSION}"
    )

    st.caption(
        "By Engr. Bilal Mehmood"
    )


# ============================================================
# PAGE ROUTER
# ============================================================

if page == "🏠 Dashboard":

    render_dashboard()

elif page == "🧠 BHAI Master":

    render_master()

elif page == "💬 BHAI Chatbot":

    render_chatbot()

elif page == "🤖 Agent Center":

    render_agent_center()

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
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🤖 BHAI AI | Master Agent for Intelligent Daily Routine Automation"
)

st.caption(
    "21 Specialized Agents • Demo Mode • API Mode"
)

st.caption(
    "By Engr. Bilal Mehmood"
)
