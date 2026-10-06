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
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="BHAI AI - Master Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONSTANTS
# ============================================================

APP_NAME = "BHAI AI"
APP_VERSION = "3.0"
DEFAULT_MODEL = "gpt-6-luna"
DB_FILE = "bhai_ai.db"

AGENTS = {
    1: ("🗓️", "Planner Agent", "Plans daily, weekly and long-term activities."),
    2: ("⏰", "Reminder Agent", "Creates reminders and alarms."),
    3: ("📅", "Calendar Agent", "Manages appointments and calendar activities."),
    4: ("✅", "Task Agent", "Creates and manages actionable tasks."),
    5: ("🚀", "Productivity Agent", "Improves productivity and workflows."),
    6: ("📚", "Learning Agent", "Creates study plans and learning schedules."),
    7: ("🔬", "Research Agent", "Supports research and information organization."),
    8: ("💬", "Communication Agent", "Prepares professional communication."),
    9: ("📧", "Email Agent", "Creates professional emails."),
    10: ("🤝", "Meeting Agent", "Plans meetings, agendas and action points."),
    11: ("❤️", "Health Agent", "Organizes general wellness routines."),
    12: ("🏃", "Fitness Agent", "Creates exercise and fitness plans."),
    13: ("💰", "Finance Agent", "Organizes budgets and expenses."),
    14: ("🛒", "Shopping Agent", "Creates and manages shopping lists."),
    15: ("✈️", "Travel Agent", "Plans trips and travel activities."),
    16: ("📰", "News Agent", "Handles news-related requests."),
    17: ("📝", "Notes Agent", "Creates and organizes notes."),
    18: ("📁", "File Agent", "Works with document/file generation."),
    19: ("🏠", "Home Agent", "Manages home-related routines."),
    20: ("🎮", "Entertainment Agent", "Handles entertainment and games."),
    21: ("🔔", "Email Notification Agent", "Schedules automatic email notifications."),
}

KEYWORD_ROUTING = {
    1: ["plan", "planning", "daily plan", "weekly plan"],
    2: ["remind", "reminder", "alert", "yaad", "alarm"],
    3: ["calendar", "appointment", "event", "schedule"],
    4: ["task", "todo", "to do", "kaam"],
    5: ["productivity", "productive", "workflow"],
    6: ["learn", "learning", "study", "course", "class"],
    7: ["research", "research paper", "literature", "analysis"],
    8: ["message", "communication", "whatsapp", "sms"],
    9: ["email", "mail", "send email", "email kar"],
    10: ["meeting", "agenda", "minutes"],
    11: ["health", "wellness", "medicine"],
    12: ["fitness", "exercise", "workout", "gym"],
    13: ["finance", "money", "budget", "expense"],
    14: ["shopping", "buy", "purchase"],
    15: ["travel", "trip", "flight", "hotel"],
    16: ["news", "latest news"],
    17: ["note", "notes", "remember"],
    18: ["file", "document", "word", "pdf"],
    19: ["home", "house"],
    20: ["game", "games", "entertainment", "movie", "chess"],
    21: ["notification", "notify", "scheduled email", "automatic email", "system alarm"],
}


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
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 15px;
        padding: 18px;
        margin-bottom: 12px;
        background: rgba(128,128,128,.04);
    }
    .agent-header {
        font-size: 25px;
        font-weight: 700;
    }
    .status-box {
        border-radius: 12px;
        padding: 14px;
        margin: 8px 0;
        border: 1px solid rgba(128,128,128,.25);
    }
    .footer {
        text-align: center;
        margin-top: 50px;
        padding: 25px;
        color: #777;
        border-top: 1px solid rgba(128,128,128,.25);
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
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ============================================================
# DATABASE
# ============================================================

db_lock = threading.Lock()


def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
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
# CONTACTS
# ============================================================

def add_contact_db(name, email):
    with db_lock:
        conn = get_db()
        conn.execute(
            "INSERT INTO contacts VALUES (?, ?, ?, ?)",
            (uuid.uuid4().hex[:10], name.strip(), email.strip(),
             datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()


def get_contacts():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM contacts ORDER BY name"
    ).fetchall()
    conn.close()
    return rows


def delete_contact(contact_id):
    with db_lock:
        conn = get_db()
        conn.execute("DELETE FROM contacts WHERE id=?", (contact_id,))
        conn.commit()
        conn.close()


def resolve_contact(value):
    if not value:
        return None

    value = value.lower().strip()

    for c in get_contacts():
        if c["email"].lower() == value:
            return c["email"]
        if c["name"].lower() == value:
            return c["email"]

    for c in get_contacts():
        if value in c["name"].lower():
            return c["email"]

    return None


# ============================================================
# SCHEDULES
# ============================================================

def add_schedule_db(action_type, title, message, recipient, subject,
                     run_at, recurrence=None):
    schedule_id = uuid.uuid4().hex[:10]

    with db_lock:
        conn = get_db()
        conn.execute(
            """
            INSERT INTO schedules
            (id, action_type, title, message, recipient, subject,
             run_at, recurrence, status, created_at, last_run)
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
                None,
            ),
        )
        conn.commit()
        conn.close()

    return schedule_id


def get_schedules():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM schedules ORDER BY run_at"
    ).fetchall()
    conn.close()
    return rows


def cancel_schedule(schedule_id):
    with db_lock:
        conn = get_db()
        conn.execute(
            "UPDATE schedules SET status='Cancelled' WHERE id=?",
            (schedule_id,),
        )
        conn.commit()
        conn.close()


# ============================================================
# API / SETTINGS
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

    if st.session_state.get("manual_api_key", "").strip():
        return "Manual Session Key"

    return "Not configured"


def get_api_key():
    secret_key = get_secret("OPENAI_API_KEY")
    if secret_key:
        return secret_key

    env_key = os.getenv("OPENAI_API_KEY", "").strip()
    if env_key:
        return env_key

    return st.session_state.get("manual_api_key", "").strip()


def get_model():
    # Priority: UI-selected model, then Streamlit Secret, then default.
    selected = st.session_state.get("model", "").strip()
    secret_model = get_secret("OPENAI_MODEL")

    if selected:
        return selected

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

    key = get_api_key()

    if not key:
        return "⚪ API key not configured"

    return f"🟢 API key available via {get_api_key_source()}"


def test_openai_connection():
    if OpenAI is None:
        return False, "Install the OpenAI package: pip install openai"

    key = get_api_key()

    if not key:
        return False, "No API key configured."

    model = get_model()

    try:
        client = OpenAI(api_key=key)

        response = client.responses.create(
            model=model,
            input="Reply with exactly: BHAI API connection successful."
        )

        text = getattr(response, "output_text", "") or "Connection successful."
        return True, f"{text}\nModel: {model}"

    except Exception as e:
        message = str(e)

        if "429" in message or "quota" in message.lower():
            return False, (
                "API request reached a quota/credits limit. "
                "Check your OpenAI API billing/credits and project access."
            )

        return False, f"API Error: {message}"


def call_openai(prompt, system_instruction=None):
    if OpenAI is None:
        return "❌ OpenAI package is not installed. Run: pip install openai"

    key = get_api_key()

    if not key:
        return (
            "❌ OpenAI API key is not configured.\n\n"
            "Open Settings → API Management and add a key, "
            "or configure OPENAI_API_KEY in Streamlit Secrets."
        )

    model = get_model()

    try:
        client = OpenAI(api_key=key)

        response = client.responses.create(
            model=model,
            instructions=(
                system_instruction
                or
                "You are BHAI AI, a helpful master multi-agent assistant."
            ),
            input=prompt,
        )

        return getattr(response, "output_text", "") or "No text response."

    except Exception as e:
        message = str(e)

        if "429" in message or "quota" in message.lower():
            return (
                "❌ OpenAI quota/credits error.\n\n"
                "Your API key may be valid, but the API project has "
                "insufficient credits/quota."
            )

        return f"❌ OpenAI Error: {message}"


# ============================================================
# ROUTING
# ============================================================

def detect_agents(text):
    text_lower = text.lower()
    found = []

    for agent_id, keywords in KEYWORD_ROUTING.items():
        if any(k in text_lower for k in keywords):
            found.append(agent_id)

    if not found:
        found = [1]

    return found[:5]


def agent_prompt(agent_id, user_text):
    icon, name, description = AGENTS[agent_id]

    return f"""
You are the {name} of BHAI AI.

Agent purpose:
{description}

User request:
{user_text}

Provide a practical, structured response.
If the request involves an action that BHAI cannot actually execute,
clearly explain what can be prepared or scheduled inside the app.
"""


# ============================================================
# DEMO RESPONSES
# ============================================================

def demo_response(user_text, agent_ids):
    names = ", ".join(AGENTS[i][1] for i in agent_ids)

    return f"""
🤖 **BHAI AI Demo Mode**

**Routed Agent(s):** {names}

**Your request:**
{user_text}

**Demo result:**
I understood the request and routed it to the appropriate BHAI agent(s).

In **API Mode**, BHAI will use the configured OpenAI API model to
generate a more intelligent response.

You can configure the API from:
**Settings → API Management**
"""


# ============================================================
# ROMAN URDU DATE/TIME
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
            pattern, replacement, result, flags=re.IGNORECASE
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
                return result.replace(tzinfo=None)
        except Exception:
            pass

    match = re.search(
        r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b",
        normalized,
        re.IGNORECASE,
    )

    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        ampm = match.group(3).lower()

        if ampm == "pm" and hour < 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0

        result = now.replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )

        if "tomorrow" in normalized.lower():
            result += timedelta(days=1)

        if result <= now:
            result += timedelta(days=1)

        return result

    return None


# ============================================================
# EMAIL
# ============================================================

def send_email_smtp(to_email, subject, body):
    host = get_secret("SMTP_HOST", os.getenv("SMTP_HOST", ""))
    port = int(get_secret("SMTP_PORT", os.getenv("SMTP_PORT", "587")) or 587)
    username = get_secret("SMTP_USERNAME", os.getenv("SMTP_USERNAME", ""))
    password = get_secret("SMTP_PASSWORD", os.getenv("SMTP_PASSWORD", ""))
    sender = get_secret("SMTP_FROM", username)

    if not all([host, username, password, sender]):
        return False, (
            "SMTP is not configured. Add SMTP_HOST, SMTP_PORT, "
            "SMTP_USERNAME, SMTP_PASSWORD and SMTP_FROM to Secrets."
        )

    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(sender, [to_email], msg.as_string())

        return True, "Email sent successfully."

    except Exception as e:
        return False, f"SMTP error: {e}"


# ============================================================
# SCHEDULER
# ============================================================

scheduler = None

if BackgroundScheduler:
    try:
        scheduler = BackgroundScheduler(timezone="Asia/Karachi")
        scheduler.start()
    except Exception:
        scheduler = None


def scheduled_email_job(schedule_id, recipient, subject, message):
    ok, _ = send_email_smtp(recipient, subject, message)

    with db_lock:
        conn = get_db()
        conn.execute(
            """
            UPDATE schedules
            SET last_run=?, status=?
            WHERE id=?
            """,
            (
                datetime.now().isoformat(),
                "Completed" if ok else "Failed",
                schedule_id,
            ),
        )
        conn.commit()
        conn.close()


def schedule_email(schedule_id, recipient, subject, message, run_at):
    if not scheduler or not DateTrigger:
        return False, "APScheduler is not installed/running."

    try:
        scheduler.add_job(
            scheduled_email_job,
            trigger=DateTrigger(run_date=run_at),
            args=[schedule_id, recipient, subject, message],
            id=f"email_{schedule_id}",
            replace_existing=True,
        )
        return True, "Email notification scheduled."

    except Exception as e:
        return False, f"Scheduler error: {e}"


# ============================================================
# DOCUMENT GENERATION
# ============================================================

def create_word(title, body):
    if Document is None:
        return None

    doc = Document()
    doc.add_heading(title, 0)

    for paragraph in body.split("\n"):
        doc.add_paragraph(paragraph)

    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output.getvalue()


def create_pdf(title, body):
    if SimpleDocTemplate is None:
        return None

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4)
    styles = getSampleStyleSheet()

    story = [
        Paragraph(title, styles["Title"]),
        Spacer(1, 12),
    ]

    for paragraph in body.split("\n"):
        if paragraph.strip():
            story.append(Paragraph(paragraph, styles["BodyText"]))
            story.append(Spacer(1, 7))

    doc.build(story)
    output.seek(0)
    return output.getvalue()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("🤖 BHAI AI")
    st.caption("Master Agent for Intelligent Daily Routine Automation")

    st.divider()

    st.session_state.mode = st.radio(
        "Operating Mode",
        ["Demo Mode", "API Mode"],
        index=0 if st.session_state.mode == "Demo Mode" else 1,
    )

    st.divider()

    st.subheader("⚙️ Settings")

    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "🧠 BHAI Master",
            "💬 BHAI Chatbot",
            "🤖 All Agents",
            "⏰ Reminders & Schedules",
            "👥 Contacts",
            "📧 Email Generator",
            "📄 Word/PDF Generator",
            "🔐 API Management",
        ],
    )

    st.divider()

    st.caption(f"Version {APP_VERSION}")
    st.caption("By Engr. Bilal Mehmood")


# ============================================================
# API MANAGEMENT PAGE
# ============================================================

def render_api_management():
    st.title("🔐 API Management")
    st.write(
        "Manage BHAI AI API access through Streamlit Secrets, "
        "environment variables or a temporary session key."
    )

    st.info(
        "Recommended for Streamlit Cloud: store OPENAI_API_KEY "
        "in App → Settings → Secrets. The application does not "
        "write API keys into SQLite."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔑 API Status")
        st.success(api_status())

        source = get_api_key_source()
        key = get_api_key()

        st.write(f"**Source:** {source}")
        st.write(f"**Key:** `{mask_key(key)}`")

    with col2:
        st.subheader("🧠 Model")

        secret_model = get_secret("OPENAI_MODEL")

        if secret_model:
            st.caption(f"Secrets model detected: `{secret_model}`")

        st.session_state.model = st.text_input(
            "OpenAI API Model",
            value=st.session_state.model or DEFAULT_MODEL,
            help="Example: gpt-6-luna. You can change this if your API project supports another model.",
        )

    st.divider()

    st.subheader("1️⃣ Streamlit Secrets")

    st.code(
        """# .streamlit/secrets.toml

OPENAI_API_KEY = "sk-your-key-here"
OPENAI_MODEL = "gpt-6-luna"

# Optional SMTP configuration:
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USERNAME = "your-email@example.com"
SMTP_PASSWORD = "your-app-password"
SMTP_FROM = "your-email@example.com"
""",
        language="toml",
    )

    st.warning(
        "Never commit .streamlit/secrets.toml to GitHub. "
        "Add it to .gitignore."
    )

    st.subheader("2️⃣ Manual Session Key")

    st.caption(
        "This key is kept only in the current Streamlit session. "
        "It is not saved in the SQLite database."
    )

    entered_key = st.text_input(
        "Enter OpenAI API Key",
        value=st.session_state.manual_api_key,
        type="password",
        placeholder="sk-...",
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("💾 Use Session Key", use_container_width=True):
            st.session_state.manual_api_key = entered_key.strip()
            st.success("Session key updated.")
            st.rerun()

    with c2:
        if st.button("🧪 Test API", use_container_width=True):
            with st.spinner("Testing API..."):
                ok, msg = test_openai_connection()
            st.session_state.api_test_result = (ok, msg)

    with c3:
        if st.button("🗑️ Clear Session Key", use_container_width=True):
            st.session_state.manual_api_key = ""
            st.session_state.api_test_result = None
            st.success("Session key cleared.")
            st.rerun()

    if st.session_state.api_test_result:
        ok, msg = st.session_state.api_test_result
        if ok:
            st.success(msg)
        else:
            st.error(msg)

    st.divider()

    st.subheader("3️⃣ Environment Variable")

    st.code(
        """Windows CMD:
set OPENAI_API_KEY=sk-your-key-here

PowerShell:
$env:OPENAI_API_KEY="sk-your-key-here"

Linux/macOS:
export OPENAI_API_KEY="sk-your-key-here"
""",
        language="bash",
    )

    st.divider()

    st.subheader("🔒 Security Rules")
    st.markdown(
        """
        - Prefer **Streamlit Secrets** for deployment.
        - Do not put API keys directly in Python source code.
        - Do not store OpenAI API keys in SQLite.
        - Do not commit `secrets.toml` to GitHub.
        - Use a separate API key for a production application.
        - If a key is exposed publicly, revoke/rotate it immediately.
        """
    )


# ============================================================
# DASHBOARD
# ============================================================

def render_dashboard():
    st.markdown('<div class="main-title">🤖 BHAI AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Master Agent for Intelligent Daily Routine Automation</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Agents", len(AGENTS))
    c2.metric("Mode", st.session_state.mode)
    c3.metric("API Source", get_api_key_source())
    c4.metric("Model", get_model())

    st.divider()

    st.subheader("🚀 Capabilities")

    cards = [
        ("🧠", "Master Agent", "Understands intent and routes requests."),
        ("⏰", "System Alarms", "Creates reminders and scheduled notifications."),
        ("📧", "Email Automation", "Generates and sends email through SMTP."),
        ("📄", "Documents", "Generates Word and PDF documents."),
        ("🔐", "API Management", "Secrets, environment and session-key support."),
        ("🤖", "21 Agents", "Daily routine agents managed through BHAI."),
    ]

    cols = st.columns(3)

    for i, (icon, title, desc) in enumerate(cards):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="agent-card">
                    <div class="agent-header">{icon} {title}</div>
                    <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.info(
        "Use Settings → API Management to configure your OpenAI API. "
        "Demo Mode works without an API key."
    )


# ============================================================
# MASTER AGENT
# ============================================================

def render_master():
    st.title("🧠 BHAI Master Agent")

    request = st.text_area(
        "What do you want BHAI to do?",
        height=140,
        placeholder=(
            "Example: Make my plan for tomorrow, remind me at 8 PM, "
            "prepare an email and create a meeting agenda."
        ),
    )

    if st.button("🚀 Run BHAI Master", type="primary"):
        if not request.strip():
            st.warning("Please enter a request.")
            return

        agents = detect_agents(request)

        st.session_state.last_agents = agents

        st.write("### 🔀 Agent Routing")

        for agent_id in agents:
            icon, name, desc = AGENTS[agent_id]
            st.write(f"{icon} **{name}** — {desc}")

        if st.session_state.mode == "API Mode":
            combined = "\n\n".join(
                agent_prompt(a, request) for a in agents
            )

            result = call_openai(
                combined,
                system_instruction=(
                    "You are BHAI AI Master Agent. "
                    "Coordinate multiple specialized agents. "
                    "Return a clear, actionable answer."
                ),
            )
        else:
            result = demo_response(request, agents)

        st.session_state.last_results.append(result)

        st.markdown("### 📌 Result")
        st.markdown(result)


# ============================================================
# CHATBOT
# ============================================================

def render_chatbot():
    st.title("💬 BHAI Chatbot")

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask BHAI anything...")

    if prompt:
        st.session_state.chat_messages.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        agents = detect_agents(prompt)

        if st.session_state.mode == "API Mode":
            result = call_openai(
                prompt,
                system_instruction=(
                    "You are BHAI AI. "
                    f"Relevant agents: {', '.join(AGENTS[a][1] for a in agents)}. "
                    "Answer practically and professionally."
                ),
            )
        else:
            result = demo_response(prompt, agents)

        st.session_state.chat_messages.append(
            {"role": "assistant", "content": result}
        )

        with st.chat_message("assistant"):
            st.markdown(result)


# ============================================================
# ALL AGENTS
# ============================================================

def render_agents():
    st.title("🤖 All BHAI Agents")

    for agent_id, (icon, name, description) in AGENTS.items():
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])

            with c1:
                st.subheader(f"{icon} {agent_id}. {name}")
                st.write(description)

            with c2:
                if st.button(
                    "Open",
                    key=f"agent_{agent_id}",
                    use_container_width=True,
                ):
                    st.session_state.selected_agent = agent_id

    if st.session_state.selected_agent:
        agent_id = st.session_state.selected_agent
        icon, name, desc = AGENTS[agent_id]

        st.divider()
        st.subheader(f"{icon} {name}")

        prompt = st.text_area(
            "Agent request",
            key=f"agent_prompt_{agent_id}",
            placeholder=f"Give a task to {name}...",
        )

        if st.button("▶️ Run Agent", key=f"run_{agent_id}"):
            if not prompt.strip():
                st.warning("Enter a request.")
                return

            if st.session_state.mode == "API Mode":
                result = call_openai(
                    agent_prompt(agent_id, prompt),
                    system_instruction=f"You are the {name} of BHAI AI.",
                )
            else:
                result = demo_response(prompt, [agent_id])

            st.markdown(result)


# ============================================================
# REMINDERS / SYSTEM ALARMS
# ============================================================

def render_schedules():
    st.title("⏰ Reminders, Alarms & Schedules")

    st.write(
        "Create a system schedule. For automatic email notifications, "
        "SMTP must also be configured."
    )

    with st.form("schedule_form"):
        action = st.selectbox(
            "Action",
            ["System Alarm", "Email Notification"],
        )

        title = st.text_input("Title", "BHAI Reminder")
        message = st.text_area("Message", "This is your scheduled reminder.")

        recipient = ""
        subject = ""

        if action == "Email Notification":
            recipient = st.text_input("Recipient Email")
            subject = st.text_input("Email Subject", title)

        run_date = st.date_input(
            "Date",
            value=datetime.now().date(),
        )

        run_time = st.time_input(
            "Time",
            value=(datetime.now() + timedelta(minutes=5)).time(),
        )

        submitted = st.form_submit_button("⏰ Create Schedule")

    if submitted:
        run_at = datetime.combine(run_date, run_time)

        if run_at <= datetime.now():
            st.error("Please select a future date/time.")
        else:
            schedule_id = add_schedule_db(
                "email" if action == "Email Notification" else "alarm",
                title,
                message,
                recipient,
                subject,
                run_at,
            )

            if action == "Email Notification":
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
                        f"Schedule saved in database, but scheduler setup failed: {msg}"
                    )
            else:
                st.success(
                    f"System alarm saved for {run_at.strftime('%Y-%m-%d %H:%M')}"
                )

    st.divider()
    st.subheader("📋 Existing Schedules")

    rows = get_schedules()

    if not rows:
        st.info("No schedules found.")
        return

    for row in rows:
        with st.container(border=True):
            st.write(f"**{row['title']}**")
            st.write(f"Action: {row['action_type']}")
            st.write(f"Run at: {row['run_at']}")
            st.write(f"Status: {row['status']}")

            if row["status"] == "Scheduled":
                if st.button(
                    "Cancel",
                    key=f"cancel_{row['id']}",
                ):
                    cancel_schedule(row["id"])
                    st.rerun()


# ============================================================
# CONTACTS
# ============================================================

def render_contacts():
    st.title("👥 Contacts")

    with st.form("contact_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        submitted = st.form_submit_button("➕ Add Contact")

    if submitted:
        if not name.strip() or not email.strip():
            st.error("Name and email are required.")
        else:
            add_contact_db(name, email)
            st.success("Contact added.")
            st.rerun()

    st.divider()

    rows = get_contacts()

    if not rows:
        st.info("No contacts available.")
        return

    for row in rows:
        c1, c2, c3 = st.columns([2, 3, 1])

        c1.write(row["name"])
        c2.write(row["email"])

        if c3.button("Delete", key=f"del_contact_{row['id']}"):
            delete_contact(row["id"])
            st.rerun()


# ============================================================
# EMAIL GENERATOR
# ============================================================

def render_email_generator():
    st.title("📧 Email Generator")

    recipient = st.text_input("Recipient Name / Email")
    purpose = st.text_area(
        "Email purpose",
        placeholder="Write what the email should say...",
    )

    tone = st.selectbox(
        "Tone",
        ["Professional", "Friendly", "Formal", "Short"],
    )

    if st.button("✉️ Generate Email", type="primary"):
        if not purpose.strip():
            st.warning("Enter the email purpose.")
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
                system_instruction="You are BHAI Email Agent.",
            )
        else:
            result = (
                f"Subject: Regarding {purpose[:60]}\n\n"
                f"Dear {recipient or 'Sir/Madam'},\n\n"
                f"I am writing regarding {purpose}.\n\n"
                "Kind regards,\n"
                "BHAI AI"
            )

        st.session_state.generated_emails.append(result)
        st.text_area("Generated Email", result, height=300)


# ============================================================
# WORD / PDF GENERATOR
# ============================================================

def render_documents():
    st.title("📄 Word / PDF Generator")

    title = st.text_input("Document Title", "BHAI AI Document")
    body = st.text_area(
        "Document Content",
        height=300,
        placeholder="Write document content here...",
    )

    if st.button("Generate Documents", type="primary"):
        if not body.strip():
            st.warning("Enter document content.")
            return

        word_data = create_word(title, body)
        pdf_data = create_pdf(title, body)

        c1, c2 = st.columns(2)

        with c1:
            if word_data:
                st.download_button(
                    "⬇️ Download Word",
                    data=word_data,
                    file_name="bhai_document.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            else:
                st.error("python-docx is not installed.")

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
                st.error("reportlab is not installed.")


# ============================================================
# ROUTE PAGE
# ============================================================

if page == "🏠 Dashboard":
    render_dashboard()

elif page == "🧠 BHAI Master":
    render_master()

elif page == "💬 BHAI Chatbot":
    render_chatbot()

elif page == "🤖 All Agents":
    render_agents()

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

st.markdown(
    """
    <div class="footer">
        <b>🤖 BHAI AI</b><br>
        Master Agent for Intelligent Daily Routine Automation<br>
        By Engr. Bilal Mehmood
    </div>
    """,
    unsafe_allow_html=True,
)
