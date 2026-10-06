import os
import io
from datetime import datetime, date

import streamlit as st

# ============================================================
# OPTIONAL / EXTERNAL PACKAGES
# ============================================================

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
    )
    from reportlab.lib.units import inch
except ImportError:
    A4 = None
    Document = None


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="BHAI AI - 20 Agent System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

.main-title {
    font-size: 44px;
    font-weight: 800;
    color: #1f4e79;
    margin-bottom: 0;
}

.subtitle {
    font-size: 20px;
    color: #555;
    margin-top: 0;
    margin-bottom: 20px;
}

.bhai-box {
    padding: 24px;
    border-radius: 16px;
    background: linear-gradient(
        135deg,
        #102a43,
        #1f5f8b
    );
    color: white;
    margin-bottom: 20px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.12);
}

.agent-card {
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #ddd;
    margin-bottom: 10px;
    background-color: #fafafa;
    min-height: 125px;
}

.agent-card:hover {
    border-color: #1f5f8b;
}

.chat-info {
    padding: 15px;
    border-radius: 12px;
    background-color: #f4f8fb;
    border: 1px solid #d5e4f0;
    margin-bottom: 15px;
}

.reminder-card {
    padding: 15px;
    border-radius: 12px;
    background-color: #fff8e1;
    border: 1px solid #ffcc80;
    margin-bottom: 10px;
}

.deadline-card {
    padding: 15px;
    border-radius: 12px;
    background-color: #ffebee;
    border: 1px solid #ef9a9a;
    margin-bottom: 10px;
}

.email-box {
    padding: 15px;
    border-radius: 12px;
    background-color: #e3f2fd;
    border: 1px solid #90caf9;
    margin-bottom: 10px;
}

.navigation-box {
    padding: 15px;
    border-radius: 12px;
    background-color: #eef7ff;
    border: 1px solid #90caf9;
    margin-bottom: 15px;
}

.footer {
    text-align: center;
    padding: 30px;
    color: #777;
}

.small-text {
    font-size: 13px;
    color: #666;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 20 SPECIALIST AGENTS
# ============================================================

AGENTS = {

    "Planner Agent":
        "Plans the user's day and sets priorities.",

    "Reminder Agent":
        "Creates and organizes reminders and recurring routines.",

    "Calendar Agent":
        "Plans events, meetings and time blocks.",

    "Task Agent":
        "Breaks goals into actionable tasks.",

    "Productivity Agent":
        "Improves focus, work routines and productivity.",

    "Learning Agent":
        "Creates study, education and learning plans.",

    "Research Agent":
        "Organizes research questions, literature and research tasks.",

    "Communication Agent":
        "Plans and drafts communication activities.",

    "Email Agent":
        "Generates professional emails and email-related tasks.",

    "Meeting Agent":
        "Creates meeting agendas, minutes and follow-up tasks.",

    "Health Agent":
        "Organizes general wellness routines; not medical diagnosis.",

    "Fitness Agent":
        "Creates general exercise and activity routines.",

    "Finance Agent":
        "Organizes budgets, expenses and financial tasks; not financial advice.",

    "Shopping Agent":
        "Creates shopping lists and purchasing priorities.",

    "Travel Agent":
        "Creates travel plans, itineraries and checklists.",

    "News Agent":
        "Organizes news-reading routines; this application does not provide live news browsing.",

    "Notes Agent":
        "Structures notes, ideas and knowledge.",

    "File Agent":
        "Organizes files and document tasks.",

    "Home Agent":
        "Organizes household and home routines.",

    "Entertainment Agent":
        "Plans games, hobbies, movies, music, chess and leisure activities.",
}


# ============================================================
# AGENT ICONS
# ============================================================

AGENT_ICONS = {

    "Planner Agent": "🧠",
    "Reminder Agent": "⏰",
    "Calendar Agent": "📅",
    "Task Agent": "✅",
    "Productivity Agent": "⚡",
    "Learning Agent": "📚",
    "Research Agent": "🔬",
    "Communication Agent": "💬",
    "Email Agent": "📧",
    "Meeting Agent": "🤝",
    "Health Agent": "❤️",
    "Fitness Agent": "🏃",
    "Finance Agent": "💰",
    "Shopping Agent": "🛒",
    "Travel Agent": "✈️",
    "News Agent": "📰",
    "Notes Agent": "📝",
    "File Agent": "📁",
    "Home Agent": "🏠",
    "Entertainment Agent": "🎮",
}


# ============================================================
# AGENT KEYWORDS
# ============================================================

KEYWORD_ROUTING = {

    "Planner Agent": [
        "plan",
        "daily",
        "day",
        "routine",
        "organize my day",
        "planning",
    ],

    "Reminder Agent": [
        "remind",
        "reminder",
        "remember",
        "alert",
        "notification",
    ],

    "Calendar Agent": [
        "calendar",
        "appointment",
        "event",
        "calendar event",
        "schedule meeting",
    ],

    "Task Agent": [
        "task",
        "todo",
        "to-do",
        "action item",
        "work task",
    ],

    "Productivity Agent": [
        "productive",
        "productivity",
        "focus",
        "time management",
        "deep work",
    ],

    "Learning Agent": [
        "learn",
        "learning",
        "study",
        "python",
        "education",
        "course",
        "training",
        "class",
        "programming",
    ],

    "Research Agent": [
        "research",
        "paper",
        "literature",
        "journal",
        "researcher",
        "publication",
        "thesis",
    ],

    "Communication Agent": [
        "message",
        "communication",
        "whatsapp",
        "reply",
        "contact",
    ],

    "Email Agent": [
        "email",
        "mail",
        "send email",
        "write email",
        "draft email",
    ],

    "Meeting Agent": [
        "meeting",
        "agenda",
        "minutes",
        "meeting notes",
    ],

    "Health Agent": [
        "health",
        "wellness",
        "sleep",
        "water",
        "hydration",
    ],

    "Fitness Agent": [
        "fitness",
        "exercise",
        "workout",
        "walk",
        "running",
        "gym",
    ],

    "Finance Agent": [
        "finance",
        "budget",
        "expense",
        "money",
        "salary",
        "saving",
    ],

    "Shopping Agent": [
        "shopping",
        "buy",
        "purchase",
        "shopping list",
    ],

    "Travel Agent": [
        "travel",
        "trip",
        "hotel",
        "flight",
        "tour",
        "journey",
    ],

    "News Agent": [
        "news",
        "headline",
        "current affairs",
    ],

    "Notes Agent": [
        "note",
        "notes",
        "idea",
        "knowledge",
    ],

    "File Agent": [
        "file",
        "files",
        "document",
        "folder",
        "pdf",
        "word",
        "docx",
        "report",
    ],

    "Home Agent": [
        "home",
        "house",
        "clean",
        "household",
        "maintenance",
    ],

    "Entertainment Agent": [
        "game",
        "games",
        "movie",
        "music",
        "hobby",
        "fun",
        "chess",
        "play",
    ],
}


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {

    "chat_messages": [],
    "last_agents": [],
    "last_results": [],
    "reminders": [],
    "deadlines": [],
    "generated_emails": [],
    "manual_api_key": "",
    "generated_document_content": "",
    "document_title": "",
    "document_author": "Engr. Bilal Mehmood",
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# OPENAI API KEY
# ============================================================

def get_api_key():

    try:

        secret_key = st.secrets.get(
            "OPENAI_API_KEY",
            ""
        )

    except Exception:

        secret_key = ""

    if secret_key:

        return secret_key

    environment_key = os.getenv(
        "OPENAI_API_KEY",
        ""
    )

    if environment_key:

        return environment_key

    return st.session_state.get(
        "manual_api_key",
        ""
    )


# ============================================================
# OPENAI CALL
# ============================================================

def call_openai(
    prompt,
    system_instruction,
    model,
    api_key,
):

    if OpenAI is None:

        return (
            "OpenAI package is not installed.\n\n"
            "Install it using:\n"
            "pip install openai"
        )

    if not api_key:

        return "OPENAI_API_KEY is missing."

    try:

        client = OpenAI(
            api_key=api_key
        )

        response = client.responses.create(
            model=model,
            instructions=system_instruction,
            input=prompt,
        )

        return response.output_text

    except Exception as error:

        return (
            "OpenAI API Error:\n\n"
            + str(error)
        )


# ============================================================
# DEMO MASTER ROUTER
# ============================================================

def bhai_demo_router(
    user_request,
    max_agents,
):

    text = user_request.lower()

    selected = []

    for agent_name, keywords in KEYWORD_ROUTING.items():

        for keyword in keywords:

            if keyword in text:

                if agent_name not in selected:

                    selected.append(
                        agent_name
                    )

                break

    if not selected:

        selected = [
            "Planner Agent",
            "Task Agent",
            "Productivity Agent",
        ]

    return selected[:max_agents]


# ============================================================
# OPENAI MASTER ROUTER
# ============================================================

def bhai_api_router(
    user_request,
    model,
    api_key,
    max_agents,
):

    agent_list = "\n".join(
        f"{i + 1}. {name}: {description}"
        for i, (name, description)
        in enumerate(AGENTS.items())
    )

    system_instruction = f"""
You are BHAI, the Master Agent.

BHAI means:

B = Brain
H = Helpful
A = AI
I = Intelligent

You control 20 specialist agents.

AVAILABLE AGENTS:

{agent_list}

USER REQUEST:

{user_request}

RULES:

1. Understand the user's intent.
2. Select only genuinely relevant agents.
3. Maximum {max_agents} agents.
4. Use multiple agents when the request has
   multiple requirements.
5. Return only exact agent names.
6. Separate names with commas.
7. Never invent an agent.
8. If the request is general daily planning,
   use Planner Agent, Task Agent and
   Productivity Agent.
"""

    result = call_openai(
        user_request,
        system_instruction,
        model,
        api_key,
    )

    selected = []

    for agent_name in AGENTS:

        if agent_name.lower() in result.lower():

            selected.append(
                agent_name
            )

    return selected[:max_agents]


# ============================================================
# DEMO SPECIALIST AGENTS
# ============================================================

def run_demo_agent(
    agent_name,
    user_request,
):

    responses = {

        "Planner Agent":
            "Create a priority-based daily plan.",

        "Reminder Agent":
            "Create reminders for important tasks, meetings and routines.",

        "Calendar Agent":
            "Allocate meetings, appointments and focused work blocks.",

        "Task Agent":
            "Break the request into small actionable tasks.",

        "Productivity Agent":
            "Use priority management, focus sessions and short breaks.",

        "Learning Agent":
            "Create a structured learning plan with objectives and study sessions.",

        "Research Agent":
            "Define research question → sources → analysis → summary.",

        "Communication Agent":
            "Identify communication purpose, audience and required message.",

        "Email Agent":
            "Prepare subject → greeting → body → closing.",

        "Meeting Agent":
            "Create agenda → discussion points → decisions → action items.",

        "Health Agent":
            "Include hydration, breaks, sleep and general wellness activities.",

        "Fitness Agent":
            "Create suitable walking, stretching or exercise activities.",

        "Finance Agent":
            "Organize expenses, budget categories and financial priorities.",

        "Shopping Agent":
            "Create and prioritize the required shopping list.",

        "Travel Agent":
            "Create itinerary → transport → accommodation → checklist.",

        "News Agent":
            "Create a routine for reviewing trusted news sources.",

        "Notes Agent":
            "Capture → organize → categorize → review notes.",

        "File Agent":
            "Organize documents, folders and document-generation tasks.",

        "Home Agent":
            "Prioritize household cleaning, maintenance and home activities.",

        "Entertainment Agent":
            "Plan games, hobbies, movies, music or chess activities.",
    }

    response = responses.get(
        agent_name,
        "Agent completed the request."
    )

    return f"""
## {AGENT_ICONS.get(agent_name, "🤖")} {agent_name}

### User Request

{user_request}

### Demo Result

{response}

### Status

✅ Completed in Demo Mode.

> Demo Mode simulates the agent response.
> It does not perform external actions.
"""


# ============================================================
# API SPECIALIST AGENT
# ============================================================

def run_api_agent(
    agent_name,
    user_request,
    model,
    api_key,
):

    description = AGENTS[
        agent_name
    ]

    system_instruction = f"""
You are the {agent_name}.

Your responsibility:

{description}

You work under the BHAI Master Agent.

USER REQUEST:

{user_request}

Rules:

1. Give practical and useful results.
2. Structure the answer clearly.
3. Be concise where possible.
4. Do not claim external actions were completed.
5. Do not invent important facts.
6. Do not override the BHAI Master Agent.
"""

    return call_openai(
        user_request,
        system_instruction,
        model,
        api_key,
    )


# ============================================================
# FINAL BHAI SYNTHESIS
# ============================================================

def bhai_final_summary(
    user_request,
    results,
    mode,
    model,
    api_key,
):

    combined = "\n\n".join(
        f"### {name}\n{result}"
        for name, result in results
    )

    if mode == "Demo Mode":

        return f"""
# 🤖 BHAI Final Response

### User Request

{user_request}

### Activated Agents

{", ".join(name for name, _ in results)}

### Combined Result

{combined}

### BHAI Status

✅ Request processed successfully in Demo Mode.

Demo Mode simulates agent behavior and does not
perform external actions.
"""

    system_instruction = """
You are BHAI, the Master Agent.

Combine the specialist agent outputs into one
clear and useful final response.

Rules:

1. Address the original user request.
2. Combine useful information.
3. Avoid unnecessary repetition.
4. Clearly distinguish planned actions,
   recommendations and completed actions.
5. Never claim an external action was completed
   unless an actual integration exists.
"""

    prompt = f"""
USER REQUEST:

{user_request}

SPECIALIST RESULTS:

{combined}

Create the final BHAI response.
"""

    return call_openai(
        prompt,
        system_instruction,
        model,
        api_key,
    )


# ============================================================
# CHAT PROCESSOR
# ============================================================

def process_bhai_chat(
    user_request,
    mode,
    model,
    api_key,
    max_agents,
):

    context = ""

    for message in st.session_state.chat_messages[-10:]:

        context += (
            message["role"].upper()
            + ": "
            + message["content"]
            + "\n\n"
        )

    enhanced_request = f"""
PREVIOUS CONVERSATION:

{context}

CURRENT USER REQUEST:

{user_request}

Use the previous conversation when relevant.
"""

    if mode == "Demo Mode":

        selected_agents = bhai_demo_router(
            enhanced_request,
            max_agents,
        )

    else:

        selected_agents = bhai_api_router(
            enhanced_request,
            model,
            api_key,
            max_agents,
        )

    if not selected_agents:

        selected_agents = [
            "Planner Agent",
            "Task Agent",
            "Productivity Agent",
        ]

    results = []

    for agent_name in selected_agents:

        if mode == "Demo Mode":

            result = run_demo_agent(
                agent_name,
                user_request,
            )

        else:

            result = run_api_agent(
                agent_name,
                enhanced_request,
                model,
                api_key,
            )

        results.append(
            (
                agent_name,
                result,
            )
        )

    final_response = bhai_final_summary(
        user_request,
        results,
        mode,
        model,
        api_key,
    )

    return (
        selected_agents,
        results,
        final_response,
    )


# ============================================================
# REMINDER FUNCTIONS
# ============================================================

def add_reminder(
    title,
    reminder_date,
    reminder_time,
    priority,
):

    st.session_state.reminders.append(
        {
            "title": title,
            "date": str(reminder_date),
            "time": str(reminder_time),
            "priority": priority,
            "created": datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            ),
        }
    )


# ============================================================
# DEADLINE FUNCTION
# ============================================================

def add_deadline(
    title,
    deadline_date,
    priority,
    notes,
):

    st.session_state.deadlines.append(
        {
            "title": title,
            "date": str(deadline_date),
            "priority": priority,
            "notes": notes,
            "created": datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            ),
        }
    )


# ============================================================
# EMAIL GENERATOR
# ============================================================

def generate_email(
    recipient,
    purpose,
    tone,
    details,
    mode,
    model,
    api_key,
):

    if mode == "Demo Mode":

        return f"""Subject: {purpose}

Dear {recipient},

I am writing regarding {purpose}.

{details}

Please let me know if you require any
additional information.

Best regards,

Engr. Bilal Mehmood
"""

    prompt = f"""
Create a professional email.

Recipient:
{recipient}

Purpose:
{purpose}

Tone:
{tone}

Details:
{details}

Return a subject and complete email body.
"""

    system_instruction = """
You are the BHAI Email Agent.

Write a clear, professional and grammatically
correct email.

Do not invent important facts.
"""

    return call_openai(
        prompt,
        system_instruction,
        model,
        api_key,
    )


# ============================================================
# WORD DOCUMENT GENERATOR
# ============================================================

def create_word_document(
    title,
    author,
    content,
):

    if Document is None:

        raise RuntimeError(
            "python-docx is not installed. "
            "Run: pip install python-docx"
        )

    document = Document()

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    document.add_heading(
        title,
        level=0,
    )

    # --------------------------------------------------------
    # AUTHOR
    # --------------------------------------------------------

    if author.strip():

        paragraph = document.add_paragraph()

        run = paragraph.add_run(
            f"Author: {author}"
        )

        run.bold = True

    document.add_paragraph()

    # --------------------------------------------------------
    # CONTENT
    # --------------------------------------------------------

    paragraphs = content.split("\n")

    for paragraph_text in paragraphs:

        text = paragraph_text.strip()

        if not text:

            document.add_paragraph()

            continue

        if text.startswith("# "):

            document.add_heading(
                text[2:].strip(),
                level=1,
            )

        elif text.startswith("## "):

            document.add_heading(
                text[3:].strip(),
                level=2,
            )

        elif text.startswith("### "):

            document.add_heading(
                text[4:].strip(),
                level=3,
            )

        else:

            document.add_paragraph(
                text
            )

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    section = document.sections[0]

    footer = section.footer

    footer_paragraph = footer.paragraphs[0]

    footer_paragraph.text = (
        "Generated by BHAI AI | "
        "By Engr. Bilal Mehmood"
    )

    # --------------------------------------------------------
    # MEMORY FILE
    # --------------------------------------------------------

    file_stream = io.BytesIO()

    document.save(
        file_stream
    )

    file_stream.seek(0)

    return file_stream.getvalue()


# ============================================================
# PDF DOCUMENT GENERATOR
# ============================================================

def create_pdf_document(
    title,
    author,
    content,
):

    if A4 is None:

        raise RuntimeError(
            "reportlab is not installed. "
            "Run: pip install reportlab"
        )

    file_stream = io.BytesIO()

    pdf = SimpleDocTemplate(
        file_stream,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]

    heading_style = styles["Heading2"]

    body_style = styles["BodyText"]

    story = []

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            title,
            title_style,
        )
    )

    story.append(
        Spacer(
            1,
            0.20 * inch,
        )
    )

    # --------------------------------------------------------
    # AUTHOR
    # --------------------------------------------------------

    if author.strip():

        story.append(
            Paragraph(
                f"<b>Author:</b> {author}",
                body_style,
            )
        )

        story.append(
            Spacer(
                1,
                0.20 * inch,
            )
        )

    # --------------------------------------------------------
    # CONTENT
    # --------------------------------------------------------

    paragraphs = content.split("\n")

    for paragraph_text in paragraphs:

        text = paragraph_text.strip()

        if not text:

            story.append(
                Spacer(
                    1,
                    0.08 * inch,
                )
            )

            continue

        if text.startswith("### "):

            text = text[4:]

            story.append(
                Paragraph(
                    text,
                    heading_style,
                )
            )

        elif text.startswith("## "):

            text = text[3:]

            story.append(
                Paragraph(
                    text,
                    heading_style,
                )
            )

        elif text.startswith("# "):

            text = text[2:]

            story.append(
                Paragraph(
                    text,
                    heading_style,
                )
            )

        else:

            # Escape basic HTML symbols
            text = (
                text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )

            story.append(
                Paragraph(
                    text,
                    body_style,
                )
            )

        story.append(
            Spacer(
                1,
                0.08 * inch,
            )
        )

    # --------------------------------------------------------
    # FOOTER TEXT
    # --------------------------------------------------------

    story.append(
        Spacer(
            1,
            0.25 * inch,
        )
    )

    story.append(
        Paragraph(
            "<b>Generated by BHAI AI</b><br/>"
            "By Engr. Bilal Mehmood",
            body_style,
        )
    )

    pdf.build(
        story
    )

    file_stream.seek(0)

    return file_stream.getvalue()


# ============================================================
# SAFE FILE NAME
# ============================================================

def safe_filename(name):

    allowed = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
        "_-"
    )

    cleaned = ""

    for character in name:

        if character in allowed:

            cleaned += character

        elif character in [" ", ".", "/"]:

            cleaned += "_"

    if not cleaned:

        cleaned = "BHAI_Document"

    return cleaned


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🤖 BHAI AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    '20-Agent Intelligent Daily Routine Automation System'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="bhai-box">

<h2>🧠 BHAI — Master Agent</h2>

BHAI understands your request, selects the required
specialist agents, coordinates their work and produces
a final response.

<br><br>

<b>
User Intent → BHAI → Agent Routing → Specialist Agents
→ Validation → Final Result
</b>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "🤖 BHAI NAVIGATION"
)

st.sidebar.caption(
    "20-Agent Intelligent Automation System"
)


# ============================================================
# SYSTEM MODE
# ============================================================

st.sidebar.subheader(
    "⚙️ System Control"
)

mode = st.sidebar.radio(
    "Operating Mode",
    [
        "Demo Mode",
        "OpenAI API Mode",
    ],
)


# ============================================================
# MODEL
# ============================================================

model = st.sidebar.text_input(
    "OpenAI Model",
    value="gpt-5",
)


# ============================================================
# MAX AGENTS
# ============================================================

max_agents = st.sidebar.slider(
    "Maximum Agents per Request",
    min_value=1,
    max_value=10,
    value=5,
)


# ============================================================
# API KEY
# ============================================================

api_key = ""

if mode == "OpenAI API Mode":

    st.sidebar.subheader(
        "🔐 API Configuration"
    )

    detected_key = get_api_key()

    if detected_key:

        api_key = detected_key

        st.sidebar.success(
            "OpenAI API key detected."
        )

    else:

        api_key = st.sidebar.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
        )

        st.session_state.manual_api_key = (
            api_key
        )

else:

    st.sidebar.success(
        "🟢 Demo Mode Active"
    )


# ============================================================
# MAIN NAVIGATION
# ============================================================

st.sidebar.divider()

st.sidebar.subheader(
    "🧭 Main Navigation"
)

navigation_options = [

    "🏠 BHAI Dashboard",

    "🧠 BHAI Master",

    "💬 BHAI Chatbot",

    "🧩 Agent Navigation",

    "⏰ Reminders",

    "📅 Deadlines",

    "📧 Email Generator",

    "📄 Word / PDF Generator",
]

page = st.sidebar.radio(
    "Go To",
    navigation_options,
)


# ============================================================
# DIRECT AGENT NAVIGATION
# ============================================================

st.sidebar.divider()

st.sidebar.subheader(
    "🧩 Direct Agent Access"
)

agent_navigation = [
    f"{i + 1:02d}. "
    f"{AGENT_ICONS[name]} "
    f"{name.replace(' Agent', '')}"
    for i, name in enumerate(
        AGENTS.keys()
    )
]

selected_agent_navigation = st.sidebar.selectbox(
    "Select Agent",
    ["None"] + agent_navigation,
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 BHAI Dashboard":

    st.header(
        "🏠 BHAI AI Dashboard"
    )

    st.markdown(
        """
<div class="navigation-box">

<b>Welcome to BHAI AI.</b>

<br><br>

BHAI is a Master-Agent system controlling
20 specialist agents for daily routines,
productivity, learning, communication,
wellness, finance, travel, files,
documents and entertainment.

</div>
""",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:

        st.metric(
            "🤖 Agents",
            "20",
        )

    with c2:

        st.metric(
            "💬 Chat Messages",
            len(
                st.session_state.chat_messages
            ),
        )

    with c3:

        st.metric(
            "⏰ Reminders",
            len(
                st.session_state.reminders
            ),
        )

    with c4:

        st.metric(
            "📅 Deadlines",
            len(
                st.session_state.deadlines
            ),
        )

    with c5:

        st.metric(
            "📧 Emails",
            len(
                st.session_state.generated_emails
            ),
        )

    st.divider()

    st.subheader(
        "🧩 20-Agent Network"
    )

    columns = st.columns(4)

    for index, (
        agent_name,
        description,
    ) in enumerate(
        AGENTS.items()
    ):

        with columns[index % 4]:

            icon = AGENT_ICONS.get(
                agent_name,
                "🤖",
            )

            st.markdown(
                f"""
<div class="agent-card">

<h4>
{icon} {index + 1}. {agent_name}
</h4>

<small>
{description}
</small>

</div>
""",
                unsafe_allow_html=True,
            )


# ============================================================
# BHAI MASTER
# ============================================================

elif page == "🧠 BHAI Master":

    st.header(
        "🧠 BHAI Master Agent"
    )

    st.info(
        "BHAI Master analyzes your request and "
        "selects the most relevant specialist agents."
    )

    master_request = st.text_area(
        "Enter your request",
        height=160,
        placeholder=(
            "Example:\n"
            "Plan my day. I need to learn Python, "
            "exercise, prepare an email and play chess."
        ),
    )

    if st.button(
        "🚀 RUN BHAI MASTER",
        type="primary",
        use_container_width=True,
    ):

        if not master_request.strip():

            st.warning(
                "Please enter a request."
            )

        elif (
            mode == "OpenAI API Mode"
            and not api_key
        ):

            st.error(
                "OpenAI API key is required."
            )

        else:

            with st.spinner(
                "🧠 BHAI is understanding your request..."
            ):

                if mode == "Demo Mode":

                    selected_agents = bhai_demo_router(
                        master_request,
                        max_agents,
                    )

                else:

                    selected_agents = bhai_api_router(
                        master_request,
                        model,
                        api_key,
                        max_agents,
                    )

            if not selected_agents:

                selected_agents = [
                    "Planner Agent",
                    "Task Agent",
                    "Productivity Agent",
                ]

            st.session_state.last_agents = (
                selected_agents
            )

            st.subheader(
                "🧩 Activated Agents"
            )

            for agent in selected_agents:

                st.success(
                    f"{AGENT_ICONS.get(agent, '🤖')} "
                    f"{agent}"
                )

            results = []

            progress = st.progress(0)

            for index, agent_name in enumerate(
                selected_agents
            ):

                if mode == "Demo Mode":

                    result = run_demo_agent(
                        agent_name,
                        master_request,
                    )

                else:

                    result = run_api_agent(
                        agent_name,
                        master_request,
                        model,
                        api_key,
                    )

                results.append(
                    (
                        agent_name,
                        result,
                    )
                )

                progress.progress(
                    (index + 1)
                    / len(selected_agents)
                )

            st.session_state.last_results = (
                results
            )

            with st.spinner(
                "🧠 BHAI is synthesizing the final result..."
            ):

                final_response = bhai_final_summary(
                    master_request,
                    results,
                    mode,
                    model,
                    api_key,
                )

            st.divider()

            st.subheader(
                "🤖 BHAI Final Response"
            )

            st.markdown(
                final_response
            )


# ============================================================
# BHAI CHATBOT
# ============================================================

elif page == "💬 BHAI Chatbot":

    st.header(
        "💬 BHAI Conversational AI"
    )

    st.markdown(
        """
<div class="chat-info">

<b>🤖 Talk naturally with BHAI.</b>

<br><br>

BHAI remembers recent conversation context
and automatically connects your request
with the appropriate specialist agents.

<br><br>

<b>
User → Chatbot → Master Agent → Specialist Agents
→ Final Response
</b>

</div>
""",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(
        [5, 1]
    )

    with col1:

        st.subheader(
            "💬 Conversation"
        )

    with col2:

        if st.button(
            "🗑️ Clear",
            use_container_width=True,
        ):

            st.session_state.chat_messages = []

            st.rerun()

    if not st.session_state.chat_messages:

        with st.chat_message(
            "assistant"
        ):

            st.markdown(
                """
### 👋 Hello! I am BHAI.

I control **20 specialist agents**.

Try asking:

> Plan my day with Python learning,
> exercise and chess.

or:

> Prepare a meeting agenda and professional email.

or:

> Create a research plan and save it as a document.
"""
            )

    for message in (
        st.session_state.chat_messages
    ):

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

            if message["role"] == "assistant":

                agents = message.get(
                    "agents",
                    [],
                )

                if agents:

                    st.caption(
                        "🧩 Activated Agents: "
                        + ", ".join(agents)
                    )

    chat_request = st.chat_input(
        "Ask BHAI anything..."
    )

    if chat_request:

        if (
            mode == "OpenAI API Mode"
            and not api_key
        ):

            st.error(
                "OpenAI API key is required."
            )

        else:

            st.session_state.chat_messages.append(
                {
                    "role": "user",
                    "content": chat_request,
                }
            )

            with st.chat_message(
                "user"
            ):

                st.markdown(
                    chat_request
                )

            with st.chat_message(
                "assistant"
            ):

                with st.spinner(
                    "🧠 BHAI is thinking..."
                ):

                    (
                        selected_agents,
                        results,
                        final_response,
                    ) = process_bhai_chat(
                        chat_request,
                        mode,
                        model,
                        api_key,
                        max_agents,
                    )

                st.markdown(
                    final_response
                )

                st.caption(
                    "🧩 Activated Agents: "
                    + ", ".join(
                        selected_agents
                    )
                )

            st.session_state.chat_messages.append(
                {
                    "role": "assistant",
                    "content": final_response,
                    "agents": selected_agents,
                }
            )

            st.session_state.last_agents = (
                selected_agents
            )

            st.session_state.last_results = (
                results
            )


# ============================================================
# AGENT NAVIGATION
# ============================================================

elif page == "🧩 Agent Navigation":

    st.header(
        "🧩 20-Agent Navigation Center"
    )

    st.info(
        "Select any specialist agent and send "
        "a direct request."
    )

    selected_agent = st.selectbox(
        "Select Specialist Agent",
        list(AGENTS.keys()),
    )

    icon = AGENT_ICONS.get(
        selected_agent,
        "🤖",
    )

    st.markdown(
        f"""
<div class="bhai-box">

<h2>
{icon} {selected_agent}
</h2>

{AGENTS[selected_agent]}

</div>
""",
        unsafe_allow_html=True,
    )

    agent_request = st.text_area(
        f"Request for {selected_agent}",
        height=150,
        placeholder=(
            f"Ask {selected_agent} to help you..."
        ),
    )

    if st.button(
        f"🚀 RUN {selected_agent}",
        type="primary",
        use_container_width=True,
    ):

        if not agent_request.strip():

            st.warning(
                "Please enter a request."
            )

        elif (
            mode == "OpenAI API Mode"
            and not api_key
        ):

            st.error(
                "OpenAI API key is required."
            )

        else:

            with st.spinner(
                f"{icon} {selected_agent} is working..."
            ):

                if mode == "Demo Mode":

                    result = run_demo_agent(
                        selected_agent,
                        agent_request,
                    )

                else:

                    result = run_api_agent(
                        selected_agent,
                        agent_request,
                        model,
                        api_key,
                    )

            st.success(
                f"✅ {selected_agent} completed."
            )

            st.subheader(
                "📋 Agent Response"
            )

            st.markdown(
                result
            )

            st.session_state.last_agents = [
                selected_agent
            ]

            st.session_state.last_results = [
                (
                    selected_agent,
                    result,
                )
            ]

    st.divider()

    st.subheader(
        "🗂️ All 20 Agents"
    )

    columns = st.columns(4)

    for index, (
        agent_name,
        description,
    ) in enumerate(
        AGENTS.items()
    ):

        with columns[index % 4]:

            icon = AGENT_ICONS.get(
                agent_name,
                "🤖",
            )

            st.markdown(
                f"""
<div class="agent-card">

<b>
{icon} {index + 1:02d}. {agent_name}
</b>

<br><br>

<small>
{description}
</small>

</div>
""",
                unsafe_allow_html=True,
            )


# ============================================================
# REMINDERS
# ============================================================

elif page == "⏰ Reminders":

    st.header(
        "⏰ Reminder Manager"
    )

    with st.form(
        "reminder_form"
    ):

        reminder_title = st.text_input(
            "Reminder",
            placeholder=(
                "Example: Submit AI workshop proposal"
            ),
        )

        reminder_date = st.date_input(
            "Reminder Date",
            value=date.today(),
        )

        reminder_time = st.time_input(
            "Reminder Time"
        )

        reminder_priority = st.selectbox(
            "Priority",
            [
                "High",
                "Medium",
                "Low",
            ],
        )

        submitted = st.form_submit_button(
            "➕ Add Reminder"
        )

        if submitted:

            if reminder_title.strip():

                add_reminder(
                    reminder_title,
                    reminder_date,
                    reminder_time,
                    reminder_priority,
                )

                st.success(
                    "Reminder added."
                )

            else:

                st.warning(
                    "Please enter a reminder."
                )

    st.divider()

    st.subheader(
        "📋 My Reminders"
    )

    if st.session_state.reminders:

        for index, reminder in enumerate(
            st.session_state.reminders
        ):

            st.markdown(
                f"""
<div class="reminder-card">

<b>
⏰ {reminder["title"]}
</b>

<br><br>

📅 {reminder["date"]}

&nbsp;&nbsp;

🕐 {reminder["time"]}

<br>

🔔 Priority:
<b>{reminder["priority"]}</b>

</div>
""",
                unsafe_allow_html=True,
            )

            if st.button(
                f"🗑️ Delete Reminder {index + 1}",
                key=f"delete_reminder_{index}",
            ):

                st.session_state.reminders.pop(
                    index
                )

                st.rerun()

    else:

        st.info(
            "No reminders created yet."
        )


# ============================================================
# DEADLINES
# ============================================================

elif page == "📅 Deadlines":

    st.header(
        "📅 Deadline Manager"
    )

    with st.form(
        "deadline_form"
    ):

        deadline_title = st.text_input(
            "Deadline",
            placeholder=(
                "Example: Submit Python project"
            ),
        )

        deadline_date = st.date_input(
            "Deadline Date",
            value=date.today(),
        )

        deadline_priority = st.selectbox(
            "Priority",
            [
                "Critical",
                "High",
                "Medium",
                "Low",
            ],
        )

        deadline_notes = st.text_area(
            "Notes",
            placeholder=(
                "Additional information..."
            ),
        )

        submitted = st.form_submit_button(
            "➕ Add Deadline"
        )

        if submitted:

            if deadline_title.strip():

                add_deadline(
                    deadline_title,
                    deadline_date,
                    deadline_priority,
                    deadline_notes,
                )

                st.success(
                    "Deadline added."
                )

            else:

                st.warning(
                    "Please enter a deadline."
                )

    st.divider()

    st.subheader(
        "📋 My Deadlines"
    )

    if st.session_state.deadlines:

        for index, deadline in enumerate(
            st.session_state.deadlines
        ):

            st.markdown(
                f"""
<div class="deadline-card">

<b>
📅 {deadline["title"]}
</b>

<br><br>

🗓️ Deadline:
<b>{deadline["date"]}</b>

<br>

🚨 Priority:
<b>{deadline["priority"]}</b>

<br>

📝 {deadline["notes"]}

</div>
""",
                unsafe_allow_html=True,
            )

            if st.button(
                f"🗑️ Delete Deadline {index + 1}",
                key=f"delete_deadline_{index}",
            ):

                st.session_state.deadlines.pop(
                    index
                )

                st.rerun()

    else:

        st.info(
            "No deadlines created yet."
        )


# ============================================================
# EMAIL GENERATOR
# ============================================================

elif page == "📧 Email Generator":

    st.header(
        "📧 BHAI AI Email Generator"
    )

    recipient = st.text_input(
        "Recipient Name / Department",
        placeholder=(
            "Example: Director / HR Department"
        ),
    )

    purpose = st.text_input(
        "Email Purpose",
        placeholder=(
            "Example: Request approval for AI workshop"
        ),
    )

    tone = st.selectbox(
        "Email Tone",
        [
            "Professional",
            "Formal",
            "Friendly",
            "Academic",
            "Official",
            "Short and Direct",
        ],
    )

    details = st.text_area(
        "Additional Details",
        height=160,
        placeholder=(
            "Enter important points..."
        ),
    )

    if st.button(
        "📧 GENERATE EMAIL",
        type="primary",
        use_container_width=True,
    ):

        if not recipient.strip():

            st.warning(
                "Please enter recipient."
            )

        elif not purpose.strip():

            st.warning(
                "Please enter email purpose."
            )

        elif (
            mode == "OpenAI API Mode"
            and not api_key
        ):

            st.error(
                "OpenAI API key is required."
            )

        else:

            with st.spinner(
                "📧 Email Agent is writing..."
            ):

                email = generate_email(
                    recipient,
                    purpose,
                    tone,
                    details,
                    mode,
                    model,
                    api_key,
                )

            st.session_state.generated_emails.append(
                email
            )

            st.success(
                "Email generated successfully."
            )

            st.markdown(
                '<div class="email-box">',
                unsafe_allow_html=True,
            )

            st.markdown(
                email
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )


# ============================================================
# WORD / PDF GENERATOR
# ============================================================

elif page == "📄 Word / PDF Generator":

    st.header(
        "📄 BHAI AI Word / PDF Generator"
    )

    st.markdown(
        """
<div class="bhai-box">

<h2>📄 Intelligent Document Generator</h2>

Create professional documents using BHAI AI.

<br><br>

📝 Manual Content
&nbsp;&nbsp; | &nbsp;&nbsp;
🤖 AI Content
&nbsp;&nbsp; | &nbsp;&nbsp;
📝 Word
&nbsp;&nbsp; | &nbsp;&nbsp;
📕 PDF

</div>
""",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # DOCUMENT INFORMATION
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        document_title = st.text_input(
            "📌 Document Title",
            value=st.session_state.document_title,
            placeholder=(
                "Example: AI Workshop Proposal"
            ),
        )

        st.session_state.document_title = (
            document_title
        )

    with col2:

        document_author = st.text_input(
            "👤 Author",
            value=st.session_state.document_author,
        )

        st.session_state.document_author = (
            document_author
        )

    # --------------------------------------------------------
    # CONTENT CREATION METHOD
    # --------------------------------------------------------

    content_mode = st.radio(
        "Content Creation Method",
        [
            "✍️ Write Content Manually",
            "🤖 Generate Content with BHAI AI",
        ],
        horizontal=True,
    )

    # ========================================================
    # MANUAL MODE
    # ========================================================

    if content_mode == "✍️ Write Content Manually":

        manual_content = st.text_area(
            "📝 Document Content",
            height=350,
            value=st.session_state.generated_document_content,
            placeholder=(
                "Write your document content here..."
            ),
        )

        st.session_state.generated_document_content = (
            manual_content
        )

    # ========================================================
    # AI MODE
    # ========================================================

    else:

        ai_request = st.text_area(
            "🤖 Describe the document you want",
            height=180,
            placeholder=(
                "Example:\n"
                "Create a formal proposal for a "
                "3-day Python and AI workshop for "
                "engineering students."
            ),
        )

        if st.button(
            "🤖 GENERATE DOCUMENT CONTENT",
            type="primary",
            use_container_width=True,
        ):

            if not ai_request.strip():

                st.warning(
                    "Please describe the document."
                )

            elif (
                mode == "OpenAI API Mode"
                and not api_key
            ):

                st.error(
                    "OpenAI API key is required."
                )

            else:

                with st.spinner(
                    "🧠 BHAI is creating document content..."
                ):

                    if mode == "Demo Mode":

                        generated_content = f"""
# {document_title or "BHAI AI Document"}

## Introduction

This document was generated by BHAI AI
in Demo Mode.

## Purpose

{ai_request}

## Main Content

BHAI AI has processed the document
requirements and prepared structured
content for Word and PDF generation.

## Conclusion

The document is ready for export.

Generated by BHAI AI.
By Engr. Bilal Mehmood.
"""

                    else:

                        generated_content = call_openai(
                            ai_request,
                            """
You are the BHAI AI Document Agent.

Create professional document content
based on the user's request.

Use:

# Main Heading

## Section Heading

### Subsection

Write clear paragraphs.

The output should be suitable for
a professional Word and PDF document.

Do not invent important facts.
""",
                            model,
                            api_key,
                        )

                st.session_state.generated_document_content = (
                    generated_content
                )

                st.success(
                    "✅ Document content generated."
                )

    # ========================================================
    # DOCUMENT PREVIEW
    # ========================================================

    document_content = (
        st.session_state.generated_document_content
    )

    if document_content.strip():

        st.divider()

        st.subheader(
            "👁️ Document Preview / Edit"
        )

        edited_content = st.text_area(
            "Edit document content before download",
            value=document_content,
            height=400,
        )

        st.session_state.generated_document_content = (
            edited_content
        )

        document_content = edited_content

        # ----------------------------------------------------
        # CREATE FILES
        # ----------------------------------------------------

        try:

            word_file = create_word_document(
                document_title or "BHAI Document",
                document_author,
                document_content,
            )

            pdf_file = create_pdf_document(
                document_title or "BHAI Document",
                document_author,
                document_content,
            )

            st.divider()

            st.subheader(
                "📥 Download Files"
            )

            file_col1, file_col2 = st.columns(2)

            filename = safe_filename(
                document_title
                or "BHAI_Document"
            )

            with file_col1:

                st.download_button(
                    label="📝 Download Word (.docx)",
                    data=word_file,
                    file_name=f"{filename}.docx",
                    mime=(
                        "application/"
                        "vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document"
                    ),
                    use_container_width=True,
                )

            with file_col2:

                st.download_button(
                    label="📕 Download PDF (.pdf)",
                    data=pdf_file,
                    file_name=f"{filename}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            st.success(
                "✅ Word and PDF files are ready."
            )

        except Exception as error:

            st.error(
                f"Document generation error: {error}"
            )

    else:

        st.info(
            "Enter or generate document content "
            "to enable Word/PDF downloads."
        )


# ============================================================
# DIRECT AGENT ACCESS FROM SIDEBAR
# ============================================================

if (
    selected_agent_navigation != "None"
    and page == "🏠 BHAI Dashboard"
):

    # Extract agent number safely
    try:

        agent_number = int(
            selected_agent_navigation[
                :2
            ]
        )

    except Exception:

        agent_number = 0

    agent_names = list(
        AGENTS.keys()
    )

    if 1 <= agent_number <= 20:

        direct_agent = agent_names[
            agent_number - 1
        ]

        icon = AGENT_ICONS.get(
            direct_agent,
            "🤖",
        )

        st.divider()

        st.header(
            f"{icon} {direct_agent}"
        )

        st.info(
            AGENTS[direct_agent]
        )

        direct_request = st.text_area(
            "Direct Agent Request",
            height=130,
            placeholder=(
                f"Ask {direct_agent} to do something..."
            ),
            key="direct_agent_request",
        )

        if st.button(
            "🚀 RUN DIRECT AGENT",
            type="primary",
            key="direct_agent_button",
        ):

            if not direct_request.strip():

                st.warning(
                    "Please enter a request."
                )

            elif (
                mode == "OpenAI API Mode"
                and not api_key
            ):

                st.error(
                    "OpenAI API key is required."
                )

            else:

                with st.spinner(
                    f"{direct_agent} is working..."
                ):

                    if mode == "Demo Mode":

                        direct_result = run_demo_agent(
                            direct_agent,
                            direct_request,
                        )

                    else:

                        direct_result = run_api_agent(
                            direct_agent,
                            direct_request,
                            model,
                            api_key,
                        )

                st.subheader(
                    "📋 Agent Response"
                )

                st.markdown(
                    direct_result
                )

                st.session_state.last_agents = [
                    direct_agent
                ]

                st.session_state.last_results = [
                    (
                        direct_agent,
                        direct_result,
                    )
                ]


# ============================================================
# LAST EXECUTION
# ============================================================

if st.session_state.last_agents:

    st.divider()

    st.subheader(
        "📊 Last BHAI Execution"
    )

    st.write(
        "Recently activated agents:"
    )

    number_of_columns = min(
        len(
            st.session_state.last_agents
        ),
        5,
    )

    columns = st.columns(
        number_of_columns
    )

    for index, agent in enumerate(
        st.session_state.last_agents
    ):

        with columns[
            index % number_of_columns
        ]:

            st.success(
                f"{AGENT_ICONS.get(agent, '🤖')} "
                f"{agent}"
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
<div class="footer">

🤖 <b>BHAI AI</b>

<br><br>

20-Agent Intelligent Daily Routine Automation System

<br><br>

🧠 Master Agent
&nbsp; | &nbsp;
💬 AI Chatbot
&nbsp; | &nbsp;
🧩 20 Specialist Agents
&nbsp; | &nbsp;
📄 Word
&nbsp; | &nbsp;
📕 PDF
&nbsp; | &nbsp;
⏰ Reminders
&nbsp; | &nbsp;
📅 Deadlines
&nbsp; | &nbsp;
📧 Email

<br><br>

<b>By Engr. Bilal Mehmood</b>

</div>
""",
    unsafe_allow_html=True,
)
