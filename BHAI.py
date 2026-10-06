import os
from datetime import datetime, date

import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="BHAI AI - 20 Agent System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
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
    padding: 14px;
    border-radius: 12px;
    border: 1px solid #ddd;
    margin-bottom: 10px;
    background-color: #fafafa;
    min-height: 95px;
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
    padding: 12px;
    border-radius: 10px;
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
""", unsafe_allow_html=True)


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
        "Organizes news-reading routines; no live browsing in this application.",

    "Notes Agent":
        "Structures notes, ideas and knowledge.",

    "File Agent":
        "Organizes files and document tasks.",

    "Home Agent":
        "Organizes household and home routines.",

    "Entertainment Agent":
        "Plans games, hobbies, movies, music and leisure activities."
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
    "Entertainment Agent": "🎮"
}


# ============================================================
# KEYWORD ROUTING
# ============================================================

KEYWORD_ROUTING = {

    "Planner Agent": [
        "plan",
        "daily",
        "day",
        "routine",
        "schedule",
        "organize my day"
    ],

    "Reminder Agent": [
        "remind",
        "reminder",
        "remember",
        "alert",
        "notification"
    ],

    "Calendar Agent": [
        "calendar",
        "appointment",
        "event",
        "meeting time",
        "schedule meeting"
    ],

    "Task Agent": [
        "task",
        "todo",
        "to-do",
        "action item",
        "work"
    ],

    "Productivity Agent": [
        "productive",
        "productivity",
        "focus",
        "time management"
    ],

    "Learning Agent": [
        "learn",
        "learning",
        "study",
        "python",
        "education",
        "course",
        "training",
        "class"
    ],

    "Research Agent": [
        "research",
        "paper",
        "literature",
        "journal",
        "researcher",
        "publication"
    ],

    "Communication Agent": [
        "message",
        "communication",
        "whatsapp",
        "reply",
        "contact"
    ],

    "Email Agent": [
        "email",
        "mail",
        "send email",
        "write email",
        "draft email"
    ],

    "Meeting Agent": [
        "meeting",
        "agenda",
        "minutes",
        "meeting notes"
    ],

    "Health Agent": [
        "health",
        "wellness",
        "sleep",
        "water",
        "hydration"
    ],

    "Fitness Agent": [
        "fitness",
        "exercise",
        "workout",
        "walk",
        "running",
        "gym"
    ],

    "Finance Agent": [
        "finance",
        "budget",
        "expense",
        "money",
        "salary",
        "saving"
    ],

    "Shopping Agent": [
        "shopping",
        "buy",
        "purchase",
        "shopping list"
    ],

    "Travel Agent": [
        "travel",
        "trip",
        "hotel",
        "flight",
        "tour",
        "journey"
    ],

    "News Agent": [
        "news",
        "headline",
        "current affairs"
    ],

    "Notes Agent": [
        "note",
        "notes",
        "idea",
        "knowledge"
    ],

    "File Agent": [
        "file",
        "files",
        "document",
        "folder",
        "pdf",
        "report"
    ],

    "Home Agent": [
        "home",
        "house",
        "clean",
        "household",
        "maintenance"
    ],

    "Entertainment Agent": [
        "game",
        "games",
        "movie",
        "music",
        "hobby",
        "fun",
        "chess",
        "play"
    ]
}


# ============================================================
# SESSION STATE
# ============================================================

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "last_agents" not in st.session_state:
    st.session_state.last_agents = []

if "last_results" not in st.session_state:
    st.session_state.last_results = []

if "reminders" not in st.session_state:
    st.session_state.reminders = []

if "deadlines" not in st.session_state:
    st.session_state.deadlines = []

if "generated_emails" not in st.session_state:
    st.session_state.generated_emails = []

if "manual_api_key" not in st.session_state:
    st.session_state.manual_api_key = ""


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

    env_key = os.getenv(
        "OPENAI_API_KEY",
        ""
    )

    if env_key:
        return env_key

    return st.session_state.get(
        "manual_api_key",
        ""
    )


# ============================================================
# OPENAI API CALL
# ============================================================

def call_openai(
    prompt,
    system_instruction,
    model,
    api_key
):

    if OpenAI is None:

        return (
            "OpenAI package is not installed.\n\n"
            "Please run:\n"
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
            input=prompt
        )

        return response.output_text

    except Exception as e:

        return (
            "OpenAI API Error:\n"
            + str(e)
        )


# ============================================================
# DEMO ROUTER
# ============================================================

def bhai_demo_router(
    user_request,
    max_agents
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
            "Productivity Agent"
        ]

    return selected[:max_agents]


# ============================================================
# OPENAI MASTER ROUTER
# ============================================================

def bhai_api_router(
    user_request,
    model,
    api_key,
    max_agents
):

    agent_list = "\n".join(
        f"{i + 1}. {name}: {description}"
        for i, (name, description)
        in enumerate(AGENTS.items())
    )

    system_instruction = f"""

You are BHAI.

BHAI means:

B = Brain
H = Helpful
A = AI
I = Intelligent

You are the MASTER AGENT controlling
20 specialist agents.

AVAILABLE AGENTS:

{agent_list}

USER REQUEST:

{user_request}

RULES:

1. Understand the user's intent.
2. Select only genuinely relevant agents.
3. Maximum {max_agents} agents.
4. Use multiple agents when the request
   contains multiple requirements.
5. Return ONLY exact agent names.
6. Separate names with commas.
7. Never invent an agent.
8. Do not provide explanations.
9. If the request is general daily planning,
   use Planner Agent, Task Agent and
   Productivity Agent.

"""

    result = call_openai(
        user_request,
        system_instruction,
        model,
        api_key
    )

    selected = []

    for agent_name in AGENTS:

        if agent_name.lower() in result.lower():

            selected.append(
                agent_name
            )

    return selected[:max_agents]


# ============================================================
# DEMO AGENT EXECUTION
# ============================================================

def run_demo_agent(
    agent_name,
    user_request
):

    demo_responses = {

        "Planner Agent":
            f"Create a priority-based daily plan for:\n"
            f"{user_request}",

        "Reminder Agent":
            "Create reminders for important tasks, "
            "meetings, learning sessions and routines.",

        "Calendar Agent":
            "Allocate meetings, appointments, focused "
            "work blocks and personal time.",

        "Task Agent":
            "Break the request into small actionable tasks.",

        "Productivity Agent":
            "Use priority management, focused work "
            "sessions and short breaks.",

        "Learning Agent":
            "Create a structured learning session "
            "with objectives and study time.",

        "Research Agent":
            "Define research question → sources → "
            "analysis → summary.",

        "Communication Agent":
            "Identify recipient, purpose and "
            "communication requirements.",

        "Email Agent":
            "Prepare subject → greeting → message → "
            "closing → review.",

        "Meeting Agent":
            "Agenda → discussion → decisions → "
            "action items.",

        "Health Agent":
            "Include hydration, breaks, sleep and "
            "general wellbeing activities.",

        "Fitness Agent":
            "Create suitable walking, stretching "
            "or exercise activities.",

        "Finance Agent":
            "Organize expenses, budget and "
            "financial priorities.",

        "Shopping Agent":
            "Create and prioritize the required "
            "shopping list.",

        "Travel Agent":
            "Create itinerary → transport → "
            "accommodation → checklist.",

        "News Agent":
            "Create a routine for reviewing "
            "trusted news sources.",

        "Notes Agent":
            "Capture → organize → categorize → review.",

        "File Agent":
            "Organize documents and files into "
            "logical folders.",

        "Home Agent":
            "Prioritize household cleaning, "
            "maintenance and home activities.",

        "Entertainment Agent":
            "Plan suitable games, hobbies, movies, "
            "music or chess time."
    }

    return (
        "[DEMO MODE]\n\n"
        +
        demo_responses.get(
            agent_name,
            "Agent completed the request."
        )
    )


# ============================================================
# API SPECIALIST AGENT
# ============================================================

def run_api_agent(
    agent_name,
    user_request,
    model,
    api_key
):

    description = AGENTS[
        agent_name
    ]

    system_instruction = f"""

You are the specialist:

{agent_name}

RESPONSIBILITY:

{description}

You operate under the BHAI Master Agent.

USER REQUEST:

{user_request}

RULES:

1. Give practical results.
2. Be concise but useful.
3. Structure the response clearly.
4. Do not claim external actions were completed.
5. Only propose actions that require integrations.
6. Do not override the BHAI Master Agent.
7. Do not invent facts.

"""

    return call_openai(
        user_request,
        system_instruction,
        model,
        api_key
    )


# ============================================================
# FINAL BHAI SYNTHESIS
# ============================================================

def bhai_final_summary(
    user_request,
    results,
    mode,
    model,
    api_key
):

    combined = "\n\n".join(
        f"{name}:\n{result}"
        for name, result in results
    )

    if mode == "Demo Mode":

        return f"""
### 🤖 BHAI FINAL RESPONSE

**Request**

{user_request}

### 🧩 Activated Agents

{", ".join(
    name for name, _ in results
)}

### 📋 Combined Result

{combined}

### BHAI Status

✅ Request processed successfully
in Demo Mode.

Demo Mode simulates agent behavior
and does not perform external actions.
"""

    system_instruction = """

You are BHAI, the MASTER AGENT.

Combine the specialist outputs into one
clear final response.

The response must:

1. Address the user's original request.
2. Combine useful information from agents.
3. Avoid unnecessary repetition.
4. Clearly distinguish recommendations,
   planned actions and completed actions.
5. Never claim an external action was
   performed unless an actual integration exists.

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
        api_key
    )


# ============================================================
# CONTEXT-AWARE CHAT PROCESSOR
# ============================================================

def process_bhai_chat(
    user_request,
    mode,
    model,
    api_key,
    max_agents
):

    context = ""

    for message in (
        st.session_state.chat_messages[-10:]
    ):

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

Use previous conversation context
when it is relevant.
"""

    # --------------------------------------------------------
    # ROUTING
    # --------------------------------------------------------

    if mode == "Demo Mode":

        selected_agents = bhai_demo_router(
            enhanced_request,
            max_agents
        )

    else:

        selected_agents = bhai_api_router(
            enhanced_request,
            model,
            api_key,
            max_agents
        )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if not selected_agents:

        selected_agents = [
            "Planner Agent",
            "Task Agent",
            "Productivity Agent"
        ]

    # --------------------------------------------------------
    # RUN AGENTS
    # --------------------------------------------------------

    results = []

    for agent_name in selected_agents:

        if mode == "Demo Mode":

            result = run_demo_agent(
                agent_name,
                user_request
            )

        else:

            result = run_api_agent(
                agent_name,
                enhanced_request,
                model,
                api_key
            )

        results.append(
            (
                agent_name,
                result
            )
        )

    # --------------------------------------------------------
    # SYNTHESIS
    # --------------------------------------------------------

    final_response = bhai_final_summary(
        user_request,
        results,
        mode,
        model,
        api_key
    )

    return (
        selected_agents,
        results,
        final_response
    )


# ============================================================
# REMINDER
# ============================================================

def add_reminder(
    title,
    reminder_date,
    reminder_time,
    priority
):

    st.session_state.reminders.append(
        {
            "title": title,
            "date": str(reminder_date),
            "time": str(reminder_time),
            "priority": priority,
            "created": datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )
        }
    )


# ============================================================
# DEADLINE
# ============================================================

def add_deadline(
    title,
    deadline_date,
    priority,
    notes
):

    st.session_state.deadlines.append(
        {
            "title": title,
            "date": str(deadline_date),
            "priority": priority,
            "notes": notes,
            "created": datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )
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
    api_key
):

    if mode == "Demo Mode":

        return f"""Subject: {purpose}

Dear {recipient},

I am writing regarding {purpose}.

{details}

Please let me know if you require
any additional information.

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

Return:

Subject:
...

Email Body:
...

"""

    system_instruction = """

You are the BHAI Email Agent.

Write a clear, professional and
grammatically correct email.

Do not invent important facts.

"""

    return call_openai(
        prompt,
        system_instruction,
        model,
        api_key
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🤖 BHAI AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    '20-Agent Intelligent Daily Routine Automation System'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
<div class="bhai-box">

<h2>🧠 BHAI — Master Agent</h2>

BHAI understands your request, selects the required
specialist agents, coordinates their work and generates
a final response.

<br><br>

<b>
User → BHAI Chatbot → Master Agent → Specialist Agents
→ Validation → Final Result
</b>

</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🤖 BHAI NAVIGATION")

st.sidebar.caption(
    "20-Agent Intelligent Automation System"
)

# ------------------------------------------------------------
# MODE
# ------------------------------------------------------------

st.sidebar.subheader(
    "⚙️ System Control"
)

mode = st.sidebar.radio(
    "Operating Mode",
    [
        "Demo Mode",
        "OpenAI API Mode"
    ]
)

model = st.sidebar.text_input(
    "OpenAI Model",
    value="gpt-5"
)

max_agents = st.sidebar.slider(
    "Maximum Agents per Request",
    1,
    10,
    5
)


# ============================================================
# API KEY
# ============================================================

api_key = ""

if mode == "OpenAI API Mode":

    st.sidebar.subheader(
        "🔐 API Configuration"
    )

    existing_key = get_api_key()

    if existing_key:

        api_key = existing_key

        st.sidebar.success(
            "OpenAI API key detected."
        )

    else:

        api_key = st.sidebar.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-..."
        )

        st.session_state.manual_api_key = (
            api_key
        )

else:

    st.sidebar.success(
        "🟢 Demo Mode Active"
    )


# ============================================================
# SIDEBAR NAVIGATION
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
    "📧 Email Generator"
]

page = st.sidebar.radio(
    "Go To",
    navigation_options
)


# ============================================================
# AGENT QUICK NAVIGATION
# ============================================================

st.sidebar.divider()

st.sidebar.subheader(
    "🧩 20 Specialist Agents"
)

agent_menu = []

for index, agent_name in enumerate(
    AGENTS.keys()
):

    icon = AGENT_ICONS.get(
        agent_name,
        "🤖"
    )

    agent_menu.append(
        f"{icon} {index + 1:02d} - {agent_name.replace(' Agent', '')}"
    )

selected_agent_menu = st.sidebar.selectbox(
    "Direct Agent Access",
    ["None"] + agent_menu
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
wellness, finance, travel and entertainment.

</div>
""",
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # DASHBOARD METRICS
    # --------------------------------------------------------

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:

        st.metric(
            "🤖 Agents",
            "20"
        )

    with c2:

        st.metric(
            "💬 Chat Messages",
            len(
                st.session_state.chat_messages
            )
        )

    with c3:

        st.metric(
            "⏰ Reminders",
            len(
                st.session_state.reminders
            )
        )

    with c4:

        st.metric(
            "📅 Deadlines",
            len(
                st.session_state.deadlines
            )
        )

    with c5:

        st.metric(
            "📧 Emails",
            len(
                st.session_state.generated_emails
            )
        )

    st.divider()

    st.subheader(
        "🧩 20-Agent Network"
    )

    cols = st.columns(4)

    for i, (
        agent_name,
        description
    ) in enumerate(
        AGENTS.items()
    ):

        with cols[i % 4]:

            icon = AGENT_ICONS.get(
                agent_name,
                "🤖"
            )

            st.markdown(
                f"""
<div class="agent-card">

<h4>
{icon} {i + 1}. {agent_name}
</h4>

<small>
{description}
</small>

</div>
""",
                unsafe_allow_html=True
            )


# ============================================================
# BHAI MASTER
# ============================================================

elif page == "🧠 BHAI Master":

    st.header(
        "🧠 BHAI Master Agent"
    )

    st.info(
        "The BHAI Master understands your request "
        "and routes it to the most relevant agents."
    )

    master_request = st.text_area(
        "Enter your request",
        placeholder=(
            "Example: Plan my day with Python learning, "
            "exercise, email work and chess."
        ),
        height=150
    )

    if st.button(
        "🚀 RUN BHAI MASTER",
        type="primary",
        use_container_width=True
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
                "🧠 BHAI is routing your request..."
            ):

                if mode == "Demo Mode":

                    selected_agents = (
                        bhai_demo_router(
                            master_request,
                            max_agents
                        )
                    )

                else:

                    selected_agents = (
                        bhai_api_router(
                            master_request,
                            model,
                            api_key,
                            max_agents
                        )
                    )

            if not selected_agents:

                selected_agents = [
                    "Planner Agent",
                    "Task Agent",
                    "Productivity Agent"
                ]

            st.session_state.last_agents = (
                selected_agents
            )

            st.subheader(
                "🧩 Selected Agents"
            )

            for agent in selected_agents:

                icon = AGENT_ICONS.get(
                    agent,
                    "🤖"
                )

                st.success(
                    f"{icon} {agent}"
                )

            results = []

            progress = st.progress(0)

            for i, agent_name in enumerate(
                selected_agents
            ):

                st.write(
                    f"⚙️ Running **{agent_name}**..."
                )

                if mode == "Demo Mode":

                    result = run_demo_agent(
                        agent_name,
                        master_request
                    )

                else:

                    result = run_api_agent(
                        agent_name,
                        master_request,
                        model,
                        api_key
                    )

                results.append(
                    (
                        agent_name,
                        result
                    )
                )

                progress.progress(
                    (i + 1)
                    / len(selected_agents)
                )

            st.session_state.last_results = (
                results
            )

            with st.spinner(
                "🧠 BHAI is synthesizing..."
            ):

                final_response = (
                    bhai_final_summary(
                        master_request,
                        results,
                        mode,
                        model,
                        api_key
                    )
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

BHAI remembers the recent conversation and
selects the appropriate specialist agents.

<br><br>

<b>
Chat → BHAI → Agent Routing → 20 Agents → Final Response
</b>

</div>
""",
        unsafe_allow_html=True
    )

    top1, top2 = st.columns(
        [4, 1]
    )

    with top1:

        st.subheader(
            "💬 Conversation"
        )

    with top2:

        if st.button(
            "🗑️ Clear Chat",
            use_container_width=True
        ):

            st.session_state.chat_messages = []

            st.rerun()

    # --------------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------------

    if not st.session_state.chat_messages:

        with st.chat_message(
            "assistant"
        ):

            st.markdown(
                """
### 👋 Hello! I am BHAI.

I control **20 specialist agents**.

Try:

**"Plan my day with Python learning,
exercise and chess."**

or

**"Prepare my meeting agenda and email."**

I will select the appropriate agents automatically.
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
                    []
                )

                if agents:

                    st.caption(
                        "🧩 Activated Agents: "
                        +
                        ", ".join(agents)
                    )

    # --------------------------------------------------------
    # CHAT INPUT
    # --------------------------------------------------------

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
                    "content": chat_request
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
                        final_response
                    ) = process_bhai_chat(
                        chat_request,
                        mode,
                        model,
                        api_key,
                        max_agents
                    )

                st.markdown(
                    final_response
                )

                st.caption(
                    "🧩 Activated Agents: "
                    +
                    ", ".join(
                        selected_agents
                    )
                )

            st.session_state.chat_messages.append(
                {
                    "role": "assistant",
                    "content": final_response,
                    "agents": selected_agents
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
        "Select a specialist agent below and send "
        "a direct request to that agent."
    )

    selected_agent = st.selectbox(
        "Select Specialist Agent",
        list(AGENTS.keys())
    )

    icon = AGENT_ICONS.get(
        selected_agent,
        "🤖"
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
        unsafe_allow_html=True
    )

    agent_request = st.text_area(
        f"Request for {selected_agent}",
        placeholder=(
            f"Example: Ask {selected_agent} "
            "to help me..."
        ),
        height=150
    )

    if st.button(
        f"🚀 RUN {selected_agent}",
        type="primary",
        use_container_width=True
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
                        agent_request
                    )

                else:

                    result = run_api_agent(
                        selected_agent,
                        agent_request,
                        model,
                        api_key
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
                    result
                )
            ]

    # --------------------------------------------------------
    # AGENT GRID
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "🗂️ All 20 Agents"
    )

    cols = st.columns(4)

    for i, (
        agent_name,
        description
    ) in enumerate(
        AGENTS.items()
    ):

        with cols[i % 4]:

            icon = AGENT_ICONS.get(
                agent_name,
                "🤖"
            )

            st.markdown(
                f"""
<div class="agent-card">

<b>
{icon} {i + 1:02d}. {agent_name}
</b>

<br><br>

<small>
{description}
</small>

</div>
""",
                unsafe_allow_html=True
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
            )
        )

        reminder_date = st.date_input(
            "Reminder Date",
            value=date.today()
        )

        reminder_time = st.time_input(
            "Reminder Time"
        )

        reminder_priority = st.selectbox(
            "Priority",
            [
                "High",
                "Medium",
                "Low"
            ]
        )

        submit = st.form_submit_button(
            "➕ Add Reminder"
        )

        if submit:

            if reminder_title.strip():

                add_reminder(
                    reminder_title,
                    reminder_date,
                    reminder_time,
                    reminder_priority
                )

                st.success(
                    "Reminder added successfully."
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

        for i, reminder in enumerate(
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
                unsafe_allow_html=True
            )

            if st.button(
                f"🗑️ Delete Reminder {i + 1}",
                key=f"rem_{i}"
            ):

                st.session_state.reminders.pop(
                    i
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
            )
        )

        deadline_date = st.date_input(
            "Deadline Date",
            value=date.today()
        )

        deadline_priority = st.selectbox(
            "Priority",
            [
                "Critical",
                "High",
                "Medium",
                "Low"
            ]
        )

        deadline_notes = st.text_area(
            "Notes",
            placeholder="Additional information..."
        )

        submit = st.form_submit_button(
            "➕ Add Deadline"
        )

        if submit:

            if deadline_title.strip():

                add_deadline(
                    deadline_title,
                    deadline_date,
                    deadline_priority,
                    deadline_notes
                )

                st.success(
                    "Deadline added successfully."
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

        for i, deadline in enumerate(
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
                unsafe_allow_html=True
            )

            if st.button(
                f"🗑️ Delete Deadline {i + 1}",
                key=f"deadline_{i}"
            ):

                st.session_state.deadlines.pop(
                    i
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
        placeholder="Example: Director / HR Department"
    )

    purpose = st.text_input(
        "Email Purpose",
        placeholder=(
            "Example: Request approval for AI workshop"
        )
    )

    tone = st.selectbox(
        "Email Tone",
        [
            "Professional",
            "Formal",
            "Friendly",
            "Academic",
            "Official",
            "Short and Direct"
        ]
    )

    details = st.text_area(
        "Additional Details",
        height=160,
        placeholder=(
            "Enter the important points "
            "you want to include."
        )
    )

    if st.button(
        "📧 GENERATE EMAIL",
        type="primary",
        use_container_width=True
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
                    api_key
                )

            st.session_state.generated_emails.append(
                email
            )

            st.success(
                "Email generated successfully."
            )

            st.markdown(
                '<div class="email-box">',
                unsafe_allow_html=True
            )

            st.markdown(
                email
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


# ============================================================
# DIRECT AGENT QUICK ACCESS
# ============================================================

if (
    selected_agent_menu != "None"
    and page == "🏠 BHAI Dashboard"
):

    selected_number = int(
        selected_agent_menu.split("-")[0]
        .replace("🧠", "")
        .replace("⏰", "")
        .replace("📅", "")
        .replace("✅", "")
        .replace("⚡", "")
        .replace("📚", "")
        .replace("🔬", "")
        .replace("💬", "")
        .replace("📧", "")
        .replace("🤝", "")
        .replace("❤️", "")
        .replace("🏃", "")
        .replace("💰", "")
        .replace("🛒", "")
        .replace("✈️", "")
        .replace("📰", "")
        .replace("📝", "")
        .replace("📁", "")
        .replace("🏠", "")
        .replace("🎮", "")
        .strip()
    )

    agent_names = list(
        AGENTS.keys()
    )

    if 1 <= selected_number <= 20:

        direct_agent = agent_names[
            selected_number - 1
        ]

        st.divider()

        st.header(
            f"{AGENT_ICONS[direct_agent]} "
            f"{direct_agent}"
        )

        st.info(
            AGENTS[direct_agent]
        )

        direct_request = st.text_area(
            "Direct Agent Request",
            placeholder=(
                f"Ask {direct_agent} to do something..."
            ),
            height=120,
            key="direct_agent_request"
        )

        if st.button(
            "🚀 RUN DIRECT AGENT",
            type="primary",
            key="direct_agent_button"
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

                        direct_result = (
                            run_demo_agent(
                                direct_agent,
                                direct_request
                            )
                        )

                    else:

                        direct_result = (
                            run_api_agent(
                                direct_agent,
                                direct_request,
                                model,
                                api_key
                            )
                        )

                st.subheader(
                    "📋 Agent Response"
                )

                st.markdown(
                    direct_result
                )


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

    cols = st.columns(
        min(
            len(
                st.session_state.last_agents
            ),
            5
        )
    )

    for i, agent in enumerate(
        st.session_state.last_agents
    ):

        with cols[
            i % len(cols)
        ]:

            icon = AGENT_ICONS.get(
                agent,
                "🤖"
            )

            st.success(
                f"{icon} {agent}"
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
<div class="footer">

🤖 <b>BHAI AI</b>

<br>

20-Agent Intelligent Daily Routine Automation System

<br><br>

🧠 Master Agent |
💬 AI Chatbot |
🧩 20 Specialist Agents |
⏰ Reminders |
📅 Deadlines |
📧 Email Generator

<br><br>

<b>By Engr. Bilal Mehmood</b>

</div>
""",
    unsafe_allow_html=True
)
