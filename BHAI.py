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
# BLUE & WHITE THEME + SCROLLING TICKER
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       COLOR SYSTEM
       ======================================================== */

    :root {
        --bhai-blue: #0B5ED7;
        --bhai-dark-blue: #084298;
        --bhai-blue-2: #146CDA;
        --bhai-light-blue: #EAF3FF;
        --bhai-light-blue-2: #F3F8FF;
        --bhai-border: #C9DDF7;
        --bhai-white: #FFFFFF;
        --bhai-text: #16324F;
        --bhai-muted: #607D9B;
    }


    /* ========================================================
       APPLICATION BACKGROUND
       ======================================================== */

    .stApp {
        background: #F5F9FF;
        color: #16324F;
    }

    .main {
        background: #F5F9FF;
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
    }


    /* ========================================================
       SCROLLING TICKER
       TEAM AI MARKHORS
       ======================================================== */

    .ticker-wrapper {
        width: 100%;
        overflow: hidden;
        white-space: nowrap;

        background:
            linear-gradient(
                90deg,
                #084298,
                #0B5ED7,
                #146CDA,
                #0B5ED7,
                #084298
            );

        border-radius: 12px;

        border: 1px solid #6EA8E8;

        box-shadow:
            0 5px 18px rgba(11, 94, 215, 0.16);

        margin-bottom: 20px;

        height: 42px;

        display: flex;
        align-items: center;
    }

    .ticker-content {
        display: inline-block;

        padding-left: 100%;

        animation:
            ticker-scroll 22s linear infinite;

        color: #FFFFFF;

        font-size: 18px;

        font-weight: 800;

        letter-spacing: 3px;

        text-transform: uppercase;
    }

    .ticker-content span {
        margin-right: 80px;
    }

    @keyframes ticker-scroll {

        0% {
            transform: translateX(0);
        }

        100% {
            transform: translateX(-100%);
        }

    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background: #FFFFFF !important;
        border-right: 2px solid #D9E8FA;
    }

    section[data-testid="stSidebar"] > div {
        background: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] * {
        color: #16324F;
    }


    /* ========================================================
       HEADINGS
       ======================================================== */

    h1 {
        color: #084298 !important;
        font-weight: 800 !important;
    }

    h2 {
        color: #0B5ED7 !important;
        font-weight: 750 !important;
    }

    h3 {
        color: #146CDA !important;
        font-weight: 700 !important;
    }

    h4 {
        color: #084298 !important;
    }

    p {
        color: #16324F;
    }


    /* ========================================================
       HERO
       ======================================================== */

    .hero {
        background:
            linear-gradient(
                135deg,
                #FFFFFF 0%,
                #EAF3FF 100%
            );

        border: 1px solid #B9D4F5;

        border-left: 7px solid #0B5ED7;

        border-radius: 22px;

        padding: 32px;

        margin-bottom: 25px;

        box-shadow:
            0 8px 25px rgba(11, 94, 215, 0.08);
    }

    .main-title {
        color: #084298 !important;

        font-size: 46px;

        font-weight: 900;

        letter-spacing: -1px;
    }

    .subtitle {
        color: #55708D !important;

        font-size: 18px;

        margin-top: 6px;

        margin-bottom: 15px;
    }


    /* ========================================================
       AGENT CARDS
       ======================================================== */

    .agent-card {
        background: #FFFFFF;

        border: 1px solid #C9DDF7;

        border-radius: 18px;

        padding: 20px;

        margin-bottom: 16px;

        min-height: 175px;

        box-shadow:
            0 5px 18px rgba(11, 94, 215, 0.06);

        transition:
            transform 0.2s ease,
            box-shadow 0.2s ease,
            border-color 0.2s ease;
    }

    .agent-card:hover {
        transform: translateY(-3px);

        border-color: #0B5ED7;

        box-shadow:
            0 10px 25px rgba(11, 94, 215, 0.14);
    }

    .agent-icon {
        font-size: 40px;
    }

    .agent-name {
        color: #084298;

        font-size: 21px;

        font-weight: 800;

        margin-top: 8px;
    }

    .agent-description {
        color: #607D9B;

        font-size: 14px;

        margin-top: 7px;

        line-height: 1.5;
    }


    /* ========================================================
       GUIDE BOX
       ======================================================== */

    .guide-box {
        background: #FFFFFF;

        border-left: 5px solid #0B5ED7;

        border-radius: 12px;

        padding: 18px;

        box-shadow:
            0 4px 15px rgba(11, 94, 215, 0.06);
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    .stButton > button {
        background: #0B5ED7 !important;

        color: #FFFFFF !important;

        border: 1px solid #0B5ED7 !important;

        border-radius: 10px !important;

        font-weight: 700 !important;

        min-height: 42px;

        transition:
            background 0.2s ease,
            transform 0.2s ease,
            box-shadow 0.2s ease;
    }

    .stButton > button:hover {
        background: #084298 !important;

        border-color: #084298 !important;

        color: #FFFFFF !important;

        transform: translateY(-1px);

        box-shadow:
            0 6px 16px rgba(11, 94, 215, 0.20);
    }

    button[kind="primary"] {
        background: #0B5ED7 !important;

        color: #FFFFFF !important;

        border-color: #0B5ED7 !important;
    }

    button[kind="primary"]:hover {
        background: #084298 !important;

        border-color: #084298 !important;
    }


    /* ========================================================
       INPUTS
       ======================================================== */

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    .stDateInput input,
    .stTimeInput input {

        background: #FFFFFF !important;

        color: #16324F !important;

        border: 1px solid #B9D4F5 !important;

        border-radius: 10px !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stNumberInput input:focus,
    .stDateInput input:focus,
    .stTimeInput input:focus {

        border-color: #0B5ED7 !important;

        box-shadow:
            0 0 0 2px rgba(11, 94, 215, 0.12) !important;
    }


    /* ========================================================
       SELECTBOX
       ======================================================== */

    div[data-baseweb="select"] > div {

        background: #FFFFFF !important;

        border: 1px solid #B9D4F5 !important;

        border-radius: 10px !important;

        color: #16324F !important;
    }


    /* ========================================================
       RADIO / CHECKBOX
       ======================================================== */

    .stRadio label,
    .stCheckbox label {

        color: #16324F !important;

        font-weight: 600;
    }


    /* ========================================================
       METRICS
       ======================================================== */

    div[data-testid="stMetric"] {

        background: #FFFFFF;

        border: 1px solid #C9DDF7;

        border-radius: 16px;

        padding: 18px;

        box-shadow:
            0 5px 15px rgba(11, 94, 215, 0.06);
    }

    div[data-testid="stMetricLabel"] {
        color: #607D9B !important;
    }

    div[data-testid="stMetricValue"] {
        color: #084298 !important;

        font-weight: 800 !important;
    }


    /* ========================================================
       EXPANDERS
       ======================================================== */

    div[data-testid="stExpander"] {

        background: #FFFFFF;

        border: 1px solid #C9DDF7;

        border-radius: 14px;
    }

    div[data-testid="stExpander"] summary {

        color: #084298 !important;

        font-weight: 700;
    }


    /* ========================================================
       ALERTS
       ======================================================== */

    div[data-testid="stAlert"] {
        border-radius: 12px;

        border: 1px solid #C9DDF7;
    }


    /* ========================================================
       DATAFRAME
       ======================================================== */

    div[data-testid="stDataFrame"] {

        border: 1px solid #C9DDF7;

        border-radius: 12px;

        overflow: hidden;
    }


    /* ========================================================
       CODE
       ======================================================== */

    pre {

        background: #EAF3FF !important;

        border: 1px solid #C9DDF7 !important;

        border-radius: 12px !important;
    }

    code {
        color: #084298 !important;
    }


    /* ========================================================
       CHAT
       ======================================================== */

    div[data-testid="stChatMessage"] {

        background: #FFFFFF;

        border: 1px solid #C9DDF7;

        border-radius: 16px;

        margin-bottom: 10px;
    }

    div[data-testid="stChatInput"] {

        border: 1px solid #B9D4F5;

        border-radius: 12px;
    }


    /* ========================================================
       WELCOME DIALOG
       ======================================================== */

    div[role="dialog"] {

        background: #FFFFFF !important;

        border: 2px solid #B9D4F5 !important;

        border-radius: 24px !important;

        box-shadow:
            0 20px 60px rgba(8, 66, 152, 0.20) !important;
    }

    div[role="dialog"] h1 {
        color: #084298 !important;
    }


    /* ========================================================
       DOWNLOAD BUTTON
       ======================================================== */

    .stDownloadButton > button {

        background: #FFFFFF !important;

        color: #084298 !important;

        border: 2px solid #0B5ED7 !important;

        border-radius: 10px !important;

        font-weight: 700 !important;
    }

    .stDownloadButton > button:hover {

        background: #EAF3FF !important;

        color: #084298 !important;
    }


    /* ========================================================
       DIVIDER
       ======================================================== */

    hr {
        border-color: #D9E8FA !important;
    }


    /* ========================================================
       FOOTER
       ======================================================== */

    .footer {

        text-align: center;

        margin-top: 60px;

        padding: 30px;

        color: #607D9B;

        border-top: 1px solid #D9E8FA;

        background: #FFFFFF;

        border-radius: 18px 18px 0 0;
    }

    .footer b {
        color: #084298;
    }


    /* ========================================================
       SCROLLBAR
       ======================================================== */

    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #F5F9FF;
    }

    ::-webkit-scrollbar-thumb {
        background: #9CC2ED;

        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #0B5ED7;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TEAM AI MARKHORS TICKER
# ============================================================

st.markdown(
    """
    <div class="ticker-wrapper">
        <div class="ticker-content">
            <span>🏆 TEAM AI MARKHORS</span>
            <span>🤖 BHAI AI</span>
            <span>🚀 ARTIFICIAL INTELLIGENCE</span>
            <span>💡 INNOVATION</span>
            <span>🏆 TEAM AI MARKHORS</span>
            <span>🤖 BHAI AI</span>
            <span>🚀 ARTIFICIAL INTELLIGENCE</span>
            <span>💡 INNOVATION</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# AGENTS
# ============================================================

AGENTS = {
    1: {
        "icon": "🗓️",
        "name": "Planner Agent",
        "description": "Plans daily, weekly and long-term activities.",
        "guidance": [
            "Create daily plans.",
            "Create weekly plans.",
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
        "description": "Creates reminders, alerts and alarms.",
        "guidance": [
            "Create reminders.",
            "Understand common date and time expressions.",
            "Prepare alarm schedules.",
            "Organize personal reminders.",
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
        "description": "Manages appointments, events and schedules.",
        "guidance": [
            "Create event plans.",
            "Organize appointments.",
            "Prepare calendar schedules.",
            "Prepare event descriptions.",
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
        "description": "Creates and manages actionable tasks.",
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
        "description": "Improves productivity, workflows and time management.",
        "guidance": [
            "Optimize workflows.",
            "Reduce repetitive work.",
            "Create productivity routines.",
            "Suggest automation opportunities.",
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
        "description": "Creates learning plans, study schedules and roadmaps.",
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
        "description": "Supports research planning and academic work.",
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
        "description": "Prepares professional messages and communication.",
        "guidance": [
            "Write professional messages.",
            "Prepare announcements.",
            "Improve communication tone.",
            "Create WhatsApp or SMS messages.",
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
        "description": "Creates professional emails.",
        "guidance": [
            "Create formal emails.",
            "Write professional replies.",
            "Generate subject lines.",
            "Adjust email tone and length.",
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
        "description": "Organizes general wellness routines.",
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
        "description": "Creates general fitness and exercise routines.",
        "guidance": [
            "Create exercise schedules.",
            "Organize workout routines.",
            "Plan walking routines.",
            "Create general fitness goals.",
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
        "description": "Organizes budgets, expenses and savings.",
        "guidance": [
            "Create budgets.",
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
        "description": "Handles news-related requests and summaries.",
        "guidance": [
            "Summarize provided news.",
            "Organize news topics.",
            "Prepare briefing formats.",
            "Explain current-affairs content provided by the user.",
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
        "description": "Creates and organizes notes.",
        "guidance": [
            "Create structured notes.",
            "Summarize information.",
            "Convert rough notes into organized notes.",
            "Create project and meeting notes.",
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
        "description": "Prepares reports, documents and file content.",
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
        "description": "Handles entertainment, games and leisure planning.",
        "guidance": [
            "Suggest entertainment activities.",
            "Organize game sessions.",
            "Create leisure schedules.",
            "Prepare chess and game practice ideas.",
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
    10: ["meeting", "agenda", "minutes", "mom"],
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
    21: ["notification", "notify", "scheduled email", "automatic email", "system alarm"],
}


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
# CONTACTS
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
# SCHEDULES
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
# API SETTINGS
# ============================================================

def get_secret(name, default=""):

    try:

        value = st.secrets.get(
            name,
            default,
        )

        if value is None:
            return default

        return str(value).strip()

    except Exception:

        return default


def get_api_key_source():

    if get_secret("OPENAI_API_KEY"):
        return "Streamlit Secrets"

    if os.getenv(
        "OPENAI_API_KEY",
        "",
    ).strip():

        return "Environment Variable"

    if st.session_state.manual_api_key.strip():

        return "Session Key"

    return "Not Configured"


def get_api_key():

    secret_key = get_secret(
        "OPENAI_API_KEY"
    )

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

    selected = st.session_state.model.strip()

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

    return f"{key[:5]}••••••••{key[-4:]}"


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
# OPENAI
# ============================================================

def call_openai(
    prompt,
    system_instruction=None,
):

    if OpenAI is None:

        return (
            "❌ OpenAI package is not installed.\n\n"
            "Install it with:\n"
            "pip install openai"
        )

    api_key = get_api_key()

    if not api_key:

        return (
            "❌ OpenAI API key is not configured.\n\n"
            "Open 🔐 API Management and configure "
            "your API key."
        )

    model = get_model()

    try:

        client = OpenAI(
            api_key=api_key
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

        return (
            result
            or
            "No response generated."
        )

    except Exception as exc:

        error_text = str(exc)

        if (
            "429" in error_text
            or "quota" in error_text.lower()
            or "credit" in error_text.lower()
        ):

            return (
                "❌ OpenAI API quota/credits error.\n\n"
                "The API key may be valid, but the "
                "associated API project may have "
                "insufficient credits or quota."
            )

        return (
            f"❌ OpenAI Error:\n\n{error_text}"
        )


def test_openai_connection():

    result = call_openai(
        "Reply with exactly: BHAI API connection successful."
    )

    if result.startswith("❌"):

        return False, result

    return True, result


# ============================================================
# AGENT ROUTING
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

    return list(
        dict.fromkeys(found)
    )[:5]


def build_agent_prompt(
    agent_id,
    request,
):

    agent = AGENTS[agent_id]

    guidance = "\n".join(
        f"- {item}"
        for item in agent["guidance"]
    )

    return f"""
You are the {agent["name"]} of BHAI AI.

YOUR ROLE:
{agent["description"]}

YOUR GUIDANCE:
{guidance}

USER REQUEST:
{request}

RESPONSE RULES:
1. Understand the user's actual intent.
2. Give a practical and structured response.
3. Use headings and bullet points where useful.
4. Give actionable steps.
5. Do not claim that an external action has been completed
   unless the application actually performed it.
6. If another service is required, clearly explain it.
7. If the user writes in Roman Urdu, answer in clear
   Roman Urdu or bilingual format when appropriate.
"""


def demo_response(
    request,
    agent_ids,
):

    names = ", ".join(
        AGENTS[item]["name"]
        for item in agent_ids
    )

    return f"""
## 🤖 BHAI AI — Demo Mode

### 🔀 Routed Agent(s)

{names}

### 📝 Your Request

{request}

### ✅ Demo Result

BHAI understood your request and routed it to the
appropriate specialized agent.

You are currently using **Demo Mode**, so an external
AI API was not called.

### 🚀 To Enable AI Mode

Go to:

**Sidebar → Operating Mode → API Mode**

Then configure your API from:

**🔐 API Management**
"""


# ============================================================
# DATE/TIME
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
        r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b",
        normalized,
        re.IGNORECASE,
    )

    if match:

        hour = int(
            match.group(1)
        )

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

            result += timedelta(
                days=1
            )

        if result <= now:

            result += timedelta(
                days=1
            )

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
        os.getenv(
            "SMTP_HOST",
            "",
        ),
    )

    port_value = get_secret(
        "SMTP_PORT",
        os.getenv(
            "SMTP_PORT",
            "587",
        ),
    )

    username = get_secret(
        "SMTP_USERNAME",
        os.getenv(
            "SMTP_USERNAME",
            "",
        ),
    )

    password = get_secret(
        "SMTP_PASSWORD",
        os.getenv(
            "SMTP_PASSWORD",
            "",
        ),
    )

    sender = get_secret(
        "SMTP_FROM",
        username,
    )

    try:

        port = int(
            port_value or 587
        )

    except ValueError:

        port = 587

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

        message = MIMEMultipart()

        message["From"] = sender
        message["To"] = to_email
        message["Subject"] = subject

        message.attach(
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
                message.as_string(),
            )

        return (
            True,
            "Email sent successfully.",
        )

    except Exception as exc:

        return (
            False,
            f"SMTP Error: {exc}",
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

    success, _ = send_email_smtp(
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
                (
                    "Completed"
                    if success
                    else
                    "Failed"
                ),
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
            "APScheduler is not installed or running.",
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

    except Exception as exc:

        return (
            False,
            f"Scheduler error: {exc}",
        )


# ============================================================
# DOCUMENT GENERATORS
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
        0,
    )

    for line in body.split("\n"):

        if line.strip():

            document.add_paragraph(
                line
            )

    output = io.BytesIO()

    document.save(output)

    output.seek(0)

    return output.getvalue()


def create_pdf(
    title,
    body,
):

    if (
        SimpleDocTemplate is None
        or Paragraph is None
        or Spacer is None
        or getSampleStyleSheet is None
    ):

        return None

    output = io.BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4,
    )

    styles = getSampleStyleSheet()

    story = [

        Paragraph(
            title,
            styles["Title"],
        ),

        Spacer(
            1,
            12,
        ),
    ]

    for line in body.split("\n"):

        if line.strip():

            story.append(
                Paragraph(
                    line,
                    styles["BodyText"],
                )
            )

            story.append(
                Spacer(
                    1,
                    7,
                )
            )

    document.build(story)

    output.seek(0)

    return output.getvalue()


# ============================================================
# WELCOME POPUP
# ============================================================

def show_welcome_popup():

    if st.session_state.welcome_seen:

        return

    @st.dialog(
        "🤖 Welcome to BHAI AI",
        width="large",
    )
    def welcome_dialog():

        st.markdown(
            """
            <div style="
                text-align:center;
                padding:20px;
                background:
                    linear-gradient(
                        135deg,
                        #FFFFFF,
                        #EAF3FF
                    );
                border-radius:20px;
                border:1px solid #B9D4F5;
            ">

                <div style="
                    font-size:70px;
                ">
                    🤖
                </div>

                <h1 style="
                    color:#084298;
                    font-size:38px;
                ">
                    Welcome to BHAI AI
                </h1>

                <p style="
                    color:#607D9B;
                    font-size:18px;
                ">
                    Your Intelligent Master Agent
                </p>

                <div style="
                    color:#0B5ED7;
                    font-weight:700;
                    font-size:16px;
                ">
                    Think → Ask → Route → Agent → Action → Result
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "🤖 AI Agents",
                "21",
            )

        with col2:

            st.metric(
                "⚙️ Modes",
                "2",
            )

        with col3:

            st.metric(
                "🧠 Controller",
                "BHAI Master",
            )

        st.divider()

        st.subheader(
            "🚀 What is BHAI AI?"
        )

        st.write(
            """
            BHAI AI is a multi-agent assistant designed
            to organize daily routines, productivity,
            learning, communication, research, documents,
            reminders and other activities.
            """
        )

        st.subheader(
            "🧠 How BHAI Works"
        )

        st.info(
            """
            User Request
            ↓
            BHAI Master Agent
            ↓
            Intent Detection
            ↓
            Specialized Agent
            ↓
            AI Response / Application Action
            ↓
            Result
            """
        )

        st.subheader(
            "⚡ Two Operating Modes"
        )

        mode1, mode2 = st.columns(2)

        with mode1:

            st.success(
                """
                **Demo Mode**

                • No API key required
                • Explore the application
                • Test routing
                • Learn the agent system
                """
            )

        with mode2:

            st.info(
                """
                **API Mode**

                • Uses configured OpenAI API
                • Intelligent responses
                • Individual agent intelligence
                • Master Agent coordination
                """
            )

        st.subheader(
            "🎯 Quick Start"
        )

        st.markdown(
            """
            **1.** Select Demo Mode or API Mode.

            **2.** Open **🧠 BHAI Master**.

            **3.** Describe what you need.

            **4.** BHAI identifies the relevant agent.

            **5.** Open **🤖 Agent Center** for direct
            agent access.

            **6.** Use **🔐 API Management** for API settings.
            """
        )

        st.divider()

        st.success(
            "💡 You do not need to remember which agent to use. "
            "Just tell BHAI what you want."
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
# DASHBOARD
# ============================================================

def render_dashboard():

    st.markdown(
        """
        <div class="hero">

            <div class="main-title">
                🤖 BHAI AI
            </div>

            <div class="subtitle">
                Master Agent for Intelligent Daily Routine Automation
            </div>

            <b>
                Think → Ask → Route → Agent → Action → Result
            </b>

        </div>
        """,
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
            "Automatically routes requests to specialized agents.",
        ),

        (
            "⏰",
            "Reminders",
            "Create reminders and scheduled activities.",
        ),

        (
            "📧",
            "Email Automation",
            "Generate and schedule professional emails.",
        ),

        (
            "📄",
            "Documents",
            "Generate Word and PDF documents.",
        ),

        (
            "🤖",
            "21 Agents",
            "Dedicated agents for daily routines.",
        ),

        (
            "🔐",
            "API Management",
            "Manage API access securely.",
        ),
    ]

    columns = st.columns(3)

    for index, card in enumerate(cards):

        icon, title, description = card

        with columns[index % 3]:

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
        "💡 Example"
    )

    st.code(
        """
Make my plan for tomorrow,
remind me at 8 PM,
prepare an email for my manager,
and create a meeting agenda.
""",
        language="text",
    )

    st.write(
        "BHAI Master can identify multiple relevant agents "
        "from a single request."
    )


# ============================================================
# MASTER AGENT
# ============================================================

def render_master():

    st.title(
        "🧠 BHAI Master Agent"
    )

    st.caption(
        "Central controller for all 21 BHAI agents."
    )

    request = st.text_area(
        "💬 What do you want BHAI to do?",
        height=170,
        placeholder=(
            "Example:\n"
            "Make my plan for tomorrow, remind me at 8 PM, "
            "prepare an email and create a meeting agenda."
        ),
    )

    if st.button(
        "🚀 Run BHAI Master",
        type="primary",
        use_container_width=True,
    ):

        if not request.strip():

            st.warning(
                "Please enter your request."
            )

            return

        agents = detect_agents(
            request
        )

        st.session_state.last_agents = agents

        st.subheader(
            "🔀 Agent Routing"
        )

        route_columns = st.columns(
            min(len(agents), 3)
        )

        for index, agent_id in enumerate(agents):

            agent = AGENTS[agent_id]

            route_columns[
                index % len(route_columns)
            ].info(
                f"{agent['icon']} {agent['name']}"
            )

        if st.session_state.mode == "API Mode":

            prompts = []

            for agent_id in agents:

                prompts.append(
                    build_agent_prompt(
                        agent_id,
                        request,
                    )
                )

            combined_prompt = "\n\n".join(
                prompts
            )

            result = call_openai(
                combined_prompt,
                system_instruction=(
                    "You are BHAI AI Master Agent. "
                    "Coordinate the relevant specialized "
                    "agents and produce one clear, practical "
                    "and structured answer."
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


# ============================================================
# CHATBOT
# ============================================================

def render_chatbot():

    st.title(
        "💬 BHAI Chatbot"
    )

    st.caption(
        "Talk naturally with BHAI AI."
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

            st.markdown(
                prompt
            )

        agents = detect_agents(
            prompt
        )

        if st.session_state.mode == "API Mode":

            agent_names = ", ".join(
                AGENTS[item]["name"]
                for item in agents
            )

            result = call_openai(
                prompt,
                system_instruction=(
                    "You are BHAI AI. "
                    f"Relevant agents: {agent_names}. "
                    "Answer practically and professionally."
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

            st.markdown(
                result
            )


# ============================================================
# AGENT CENTER
# ============================================================

def render_agent_center():

    if st.session_state.agent_page:

        render_single_agent(
            st.session_state.selected_agent
        )

        return

    st.title(
        "🤖 BHAI Agent Center"
    )

    st.caption(
        "Select an individual agent for dedicated guidance "
        "and execution."
    )

    st.divider()

    search = st.text_input(
        "🔎 Search Agents",
        placeholder=(
            "Search Email, Planner, Research..."
        ),
    )

    filtered = []

    for agent_id, agent in AGENTS.items():

        searchable = (
            agent["name"]
            + " "
            + agent["description"]
        ).lower()

        if (
            not search.strip()
            or search.lower() in searchable
        ):

            filtered.append(
                agent_id
            )

    st.write(
        f"**{len(filtered)} agent(s) available**"
    )

    columns = st.columns(3)

    for index, agent_id in enumerate(filtered):

        agent = AGENTS[agent_id]

        with columns[index % 3]:

            st.markdown(
                f"""
                <div class="agent-card">

                    <div class="agent-icon">
                        {agent["icon"]}
                    </div>

                    <div class="agent-name">
                        {agent_id}. {agent["name"]}
                    </div>

                    <div class="agent-description">
                        {agent["description"]}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                f"Open {agent['name']}",
                key=f"open_agent_{agent_id}",
                use_container_width=True,
            ):

                st.session_state.selected_agent = agent_id

                st.session_state.agent_page = True

                st.rerun()


# ============================================================
# INDIVIDUAL AGENT
# ============================================================

def render_single_agent(
    agent_id
):

    agent = AGENTS[agent_id]

    if st.button(
        "⬅️ Back to Agent Center"
    ):

        st.session_state.agent_page = False

        st.rerun()

    st.divider()

    st.markdown(
        f"""
        <div class="hero">

            <div style="font-size:60px;">
                {agent["icon"]}
            </div>

            <div class="main-title">
                {agent["name"]}
            </div>

            <div class="subtitle">
                {agent["description"]}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)

    with left:

        st.subheader(
            "📘 Agent Guidance"
        )

        for item in agent["guidance"]:

            st.markdown(
                f"✅ {item}"
            )

    with right:

        st.subheader(
            "💡 Example Requests"
        )

        for example in agent["examples"]:

            st.code(
                example,
                language="text",
            )

    st.divider()

    st.subheader(
        f"{agent['icon']} Talk to {agent['name']}"
    )

    prompt = st.text_area(
        "Your Request",
        height=180,
        key=f"agent_prompt_{agent_id}",
        placeholder=(
            f"Enter a request for {agent['name']}..."
        ),
    )

    if st.button(
        "🚀 Run Agent",
        type="primary",
        use_container_width=True,
        key=f"run_agent_{agent_id}",
    ):

        if not prompt.strip():

            st.warning(
                "Please enter a request."
            )

            return

        with st.spinner(
            f"{agent['name']} is working..."
        ):

            if st.session_state.mode == "API Mode":

                result = call_openai(
                    build_agent_prompt(
                        agent_id,
                        prompt,
                    ),
                    system_instruction=(
                        f"You are the {agent['name']} "
                        "of BHAI AI. Stay focused on "
                        "your assigned responsibilities."
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
# REMINDERS & SCHEDULES
# ============================================================

def render_schedules():

    st.title(
        "⏰ Reminders & Schedules"
    )

    st.caption(
        "Create future system reminders or email notifications."
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
                "Please select a future date and time."
            )

            return

        if (
            action == "Email Notification"
            and not recipient.strip()
        ):

            st.error(
                "Recipient email is required."
            )

            return

        schedule_id = add_schedule_db(
            (
                "email"
                if action == "Email Notification"
                else "alarm"
            ),
            title,
            message,
            recipient,
            subject,
            run_at,
        )

        if action == "Email Notification":

            success, result = schedule_email(
                schedule_id,
                recipient,
                subject,
                message,
                run_at,
            )

            if success:

                st.success(
                    result
                )

            else:

                st.warning(
                    "Schedule saved, but scheduler failed: "
                    + result
                )

        else:

            st.success(
                "⏰ System alarm saved for "
                + run_at.strftime(
                    "%Y-%m-%d %H:%M"
                )
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
            or not email.strip()
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
            key=f"delete_{row['id']}",
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
        "Generate professional emails with the Email Agent."
    )

    recipient = st.text_input(
        "Recipient Name / Email"
    )

    purpose = st.text_area(
        "Email Purpose",
        height=140,
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
                "Please enter the email purpose."
            )

            return

        if st.session_state.mode == "API Mode":

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
                f"Dear {recipient or 'Sir/Madam'},\n\n"
                f"I am writing regarding {purpose}.\n\n"
                "Kind regards,\n"
                "BHAI AI"
            )

        st.session_state.generated_emails.append(
            result
        )

        st.text_area(
            "Generated Email",
            result,
            height=330,
        )


# ============================================================
# WORD / PDF
# ============================================================

def render_documents():

    st.title(
        "📄 Word / PDF Generator"
    )

    title = st.text_input(
        "Document Title",
        "BHAI AI Document",
    )

    body = st.text_area(
        "Document Content",
        height=330,
        placeholder=(
            "Write your report, proposal, letter "
            "or document content here..."
        ),
    )

    if st.button(
        "📄 Generate Documents",
        type="primary",
    ):

        if not body.strip():

            st.warning(
                "Please enter document content."
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
        "Configure and test BHAI AI API access."
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
            f"**Source:** {get_api_key_source()}"
        )

        st.write(
            f"**Key:** `{mask_key(get_api_key())}`"
        )

    with c2:

        st.subheader(
            "🧠 Model"
        )

        st.session_state.model = st.text_input(
            "OpenAI Model",
            value=st.session_state.model,
        )

        st.caption(
            "The model name must be available to your API project."
        )

    st.divider()

    st.subheader(
        "1️⃣ Streamlit Secrets"
    )

    st.code(
        """
OPENAI_API_KEY = "sk-your-api-key"
OPENAI_MODEL = "gpt-6-luna"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"
SMTP_FROM = "your-email@gmail.com"
""",
        language="toml",
    )

    st.warning(
        "Do not commit your secrets.toml file to GitHub."
    )

    st.divider()

    st.subheader(
        "2️⃣ Temporary Session Key"
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

                result = test_openai_connection()

            st.session_state.api_test_result = result

    with c3:

        if st.button(
            "🗑️ Clear Session Key",
            use_container_width=True,
        ):

            st.session_state.manual_api_key = ""

            st.session_state.api_test_result = None

            st.rerun()

    if st.session_state.api_test_result:

        success, message = (
            st.session_state.api_test_result
        )

        if success:

            st.success(
                message
            )

        else:

            st.error(
                message
            )

    st.divider()

    st.subheader(
        "3️⃣ Environment Variable"
    )

    st.code(
        """
Windows CMD:
set OPENAI_API_KEY=sk-your-key

PowerShell:
$env:OPENAI_API_KEY="sk-your-key"

Linux/macOS:
export OPENAI_API_KEY="sk-your-key"
""",
        language="bash",
    )

    st.divider()

    st.subheader(
        "🔒 Security Guidance"
    )

    st.markdown(
        """
        - Use Streamlit Secrets for deployment.
        - Never hard-code API keys in Python.
        - Never store API keys in SQLite.
        - Never commit secrets.toml to GitHub.
        - Rotate exposed API keys immediately.
        - Keep production API keys separate from development keys.
        """
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:10px;
        ">

            <div style="
                font-size:52px;
            ">
                🤖
            </div>

            <h2 style="
                color:#084298 !important;
            ">
                BHAI AI
            </h2>

            <small style="
                color:#607D9B;
            ">
                Master Agent System
            </small>

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
            if st.session_state.mode == "Demo Mode"
            else 1
        ),
    )

    st.divider()

    st.subheader(
        "🧭 Main Navigation"
    )

    page = st.radio(
        "Select Page",
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
        label_visibility="collapsed",
    )

    st.divider()

    st.subheader(
        "🤖 Individual Agent Navigation"
    )

    selected_agent_name = st.selectbox(
        "Open Agent",
        [
            f"{agent['icon']} {agent['name']}"
            for agent in AGENTS.values()
        ],
    )

    selected_id = next(
        (
            agent_id
            for agent_id, agent in AGENTS.items()
            if selected_agent_name
            ==
            f"{agent['icon']} {agent['name']}"
        ),
        1,
    )

    if st.button(
        "🚀 Open Selected Agent",
        use_container_width=True,
    ):

        st.session_state.selected_agent = selected_id

        st.session_state.agent_page = True

        st.rerun()

    st.divider()

    if st.button(
        "👋 Welcome / User Guide",
        use_container_width=True,
    ):

        st.session_state.welcome_seen = False

        st.rerun()

    st.divider()

    st.caption(
        f"Version {APP_VERSION}"
    )

    st.caption(
        "🏆 TEAM AI MARKHORS"
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
# WELCOME POPUP
# ============================================================

show_welcome_popup()


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">

        <div style="
            font-size:28px;
            color:#084298;
            font-weight:800;
        ">
            🤖 BHAI AI
        </div>

        <div style="
            color:#607D9B;
            margin-top:8px;
        ">
            Master Agent for Intelligent Daily Routine Automation
        </div>

        <div style="
            color:#0B5ED7;
            font-weight:800;
            margin-top:12px;
            letter-spacing:2px;
        ">
            🏆 TEAM AI MARKHORS
        </div>

        <div style="
            margin-top:12px;
            color:#607D9B;
        ">
            21 Specialized Agents • Demo Mode • API Mode
        </div>

        <div style="
            margin-top:15px;
            color:#084298;
            font-weight:700;
        ">
            By Engr. Bilal Mehmood
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)
