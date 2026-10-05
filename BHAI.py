import os
import re
from datetime import datetime

import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="BHAI - 20 Agent AI",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #1f4e79;
    margin-bottom: 0;
}

.subtitle {
    font-size: 20px;
    color: #555;
    margin-top: 0;
}

.bhai-box {
    padding: 20px;
    border-radius: 15px;
    background: linear-gradient(135deg, #102a43, #1f5f8b);
    color: white;
    margin-bottom: 20px;
}

.agent-card {
    padding: 12px;
    border-radius: 12px;
    border: 1px solid #ddd;
    margin-bottom: 8px;
    background-color: #fafafa;
}

.status-success {
    padding: 10px;
    border-radius: 8px;
    background-color: #e8f5e9;
    color: #1b5e20;
}

.status-api {
    padding: 10px;
    border-radius: 8px;
    background-color: #e3f2fd;
    color: #0d47a1;
}

.footer {
    text-align: center;
    padding: 20px;
    color: #777;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# 20 AGENTS
# ============================================================

AGENTS = {
    "Planner Agent": "Plans the user's day and sets priorities.",
    "Reminder Agent": "Organizes reminders and recurring routine items.",
    "Calendar Agent": "Plans events, meetings and time blocks.",
    "Task Agent": "Breaks goals into actionable tasks.",
    "Productivity Agent": "Improves focus, work routines and productivity.",
    "Learning Agent": "Creates study and learning plans.",
    "Research Agent": "Organizes research questions and research tasks.",
    "Communication Agent": "Plans and drafts communication activities.",
    "Email Agent": "Prepares email drafts and email-related task plans.",
    "Meeting Agent": "Creates meeting agendas, minutes and follow-up tasks.",
    "Health Agent": "Organizes general wellness routines; not medical diagnosis.",
    "Fitness Agent": "Creates general exercise and activity routines.",
    "Finance Agent": "Organizes budgets, expenses and financial tasks; not financial advice.",
    "Shopping Agent": "Creates shopping lists and purchasing priorities.",
    "Travel Agent": "Creates travel plans, itineraries and checklists.",
    "News Agent": "Organizes news-reading routines; no live browsing in this application.",
    "Notes Agent": "Structures notes, ideas and knowledge.",
    "File Agent": "Organizes file and document tasks.",
    "Home Agent": "Organizes household and daily home routines.",
    "Entertainment Agent": "Plans games, hobbies and leisure activities."
}


# ============================================================
# DEMO KEYWORD ROUTING
# ============================================================

KEYWORD_ROUTING = {
    "Planner Agent": [
        "plan", "day", "daily", "schedule", "routine"
    ],
    "Reminder Agent": [
        "remind", "reminder", "remember"
    ],
    "Calendar Agent": [
        "calendar", "event", "appointment", "meeting time"
    ],
    "Task Agent": [
        "task", "todo", "to-do", "work"
    ],
    "Productivity Agent": [
        "productive", "focus", "productivity"
    ],
    "Learning Agent": [
        "learn", "study", "course", "python", "education"
    ],
    "Research Agent": [
        "research", "paper", "literature", "researcher"
    ],
    "Communication Agent": [
        "message", "communication", "whatsapp", "reply"
    ],
    "Email Agent": [
        "email", "mail"
    ],
    "Meeting Agent": [
        "meeting", "agenda", "minutes"
    ],
    "Health Agent": [
        "health", "wellness", "sleep", "water"
    ],
    "Fitness Agent": [
        "fitness", "exercise", "workout", "walk"
    ],
    "Finance Agent": [
        "finance", "budget", "expense", "money"
    ],
    "Shopping Agent": [
        "shopping", "buy", "purchase", "list"
    ],
    "Travel Agent": [
        "travel", "trip", "hotel", "flight"
    ],
    "News Agent": [
        "news", "headline"
    ],
    "Notes Agent": [
        "note", "notes", "idea"
    ],
    "File Agent": [
        "file", "document", "folder"
    ],
    "Home Agent": [
        "home", "house", "clean", "household"
    ],
    "Entertainment Agent": [
        "game", "games", "movie", "music", "hobby", "fun", "chess"
    ]
}


# ============================================================
# SESSION STATE
# ============================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_agents" not in st.session_state:
    st.session_state.last_agents = []

if "last_results" not in st.session_state:
    st.session_state.last_results = []


# ============================================================
# OPENAI CLIENT
# ============================================================

def get_api_key():
    """
    Gets API key from:
    1. Streamlit secrets
    2. Environment variable
    3. Sidebar input
    """

    try:
        secret_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        secret_key = ""

    if secret_key:
        return secret_key

    env_key = os.getenv("OPENAI_API_KEY", "")

    if env_key:
        return env_key

    return st.session_state.get("manual_api_key", "")


def call_openai(prompt, system_instruction, model, api_key):
    """
    OpenAI Responses API call.
    """

    if not OpenAI:
        return "OpenAI package is not installed. Run: pip install openai"

    if not api_key:
        return "OPENAI_API_KEY is missing."

    try:

        client = OpenAI(api_key=api_key)

        response = client.responses.create(
            model=model,
            instructions=system_instruction,
            input=prompt
        )

        return response.output_text

    except Exception as e:
        return f"OpenAI API Error: {str(e)}"


# ============================================================
# BHAI DEMO ROUTER
# ============================================================

def bhai_demo_router(user_request, max_agents=5):

    text = user_request.lower()

    selected = []

    for agent_name, keywords in KEYWORD_ROUTING.items():

        for keyword in keywords:

            if keyword in text:

                if agent_name not in selected:
                    selected.append(agent_name)

                break

    # If no keyword matched, BHAI chooses general agents
    if not selected:

        selected = [
            "Planner Agent",
            "Task Agent",
            "Productivity Agent"
        ]

    return selected[:max_agents]


# ============================================================
# BHAI API ROUTER
# ============================================================

def bhai_api_router(user_request, model, api_key, max_agents):

    agent_list = "\n".join(
        f"- {name}: {description}"
        for name, description in AGENTS.items()
    )

    system_instruction = f"""
You are BHAI.

BHAI means:
B = Brain
H = Helpful
A = AI
I = Intelligent

You are the MASTER AGENT of a 20-agent daily routine automation system.

Your job is to understand the user's request and select the most relevant
specialist agents.

Available agents:

{agent_list}

RULES:

1. Select only agents that are genuinely relevant.
2. Select maximum {max_agents} agents.
3. If the request is general daily planning, use Planner Agent,
   Task Agent and Productivity Agent.
4. Return ONLY the exact agent names separated by commas.
5. Do not add explanations.
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

            selected.append(agent_name)

    return selected[:max_agents]


# ============================================================
# SPECIALIST AGENT - DEMO MODE
# ============================================================

def run_demo_agent(agent_name, user_request):

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    demo_responses = {

        "Planner Agent":
            f"Create a priority-based daily plan for: {user_request}",

        "Reminder Agent":
            "Demo reminder plan: Morning tasks, important work, "
            "learning session and evening review.",

        "Calendar Agent":
            "Demo calendar plan: Allocate focused work blocks, "
            "meetings and personal time.",

        "Task Agent":
            "Demo task breakdown: convert the user's request into "
            "small actionable tasks.",

        "Productivity Agent":
            "Demo productivity recommendation: use focused work "
            "sessions with short breaks.",

        "Learning Agent":
            "Demo learning plan: reserve a dedicated learning "
            "session and define today's learning objective.",

        "Research Agent":
            "Demo research workflow: define question → collect "
            "sources → analyze → summarize.",

        "Communication Agent":
            "Demo communication plan: identify the recipient, "
            "purpose and required response.",

        "Email Agent":
            "Demo email workflow: prepare subject → draft → review → send.",

        "Meeting Agent":
            "Demo meeting workflow: agenda → discussion → decisions "
            "→ action items.",

        "Health Agent":
            "Demo wellness routine: hydration, breaks, sleep routine "
            "and general wellbeing activities.",

        "Fitness Agent":
            "Demo fitness routine: walking, stretching and a suitable "
            "daily activity session.",

        "Finance Agent":
            "Demo finance routine: record expenses, review budget "
            "and identify today's financial tasks.",

        "Shopping Agent":
            "Demo shopping routine: create priority shopping list "
            "and separate urgent/non-urgent purchases.",

        "Travel Agent":
            "Demo travel routine: itinerary → transport → accommodation "
            "→ checklist.",

        "News Agent":
            "Demo news routine: reserve a short period for reviewing "
            "trusted news sources.",

        "Notes Agent":
            "Demo notes workflow: capture idea → organize → tag → review.",

        "File Agent":
            "Demo file routine: organize documents into logical folders "
            "and use consistent filenames.",

        "Home Agent":
            "Demo home routine: cleaning, maintenance and household "
            "tasks prioritized by urgency.",

        "Entertainment Agent":
            "Demo leisure routine: select a hobby/game/activity "
            "without disturbing priority work."
    }

    return f"[DEMO] {demo_responses.get(agent_name, 'Agent completed the request.')}"


# ============================================================
# SPECIALIST AGENT - API MODE
# ============================================================

def run_api_agent(agent_name, user_request, model, api_key):

    description = AGENTS[agent_name]

    system_instruction = f"""
You are the {agent_name}.

Your responsibility:
{description}

You are a specialist controlled by the master agent BHAI.

User request:
{user_request}

Rules:

1. Give practical and concise results.
2. Do not claim to have actually sent emails, changed calendars,
   transferred money or performed external actions unless a real
   integration is connected.
3. If an action would require an external service, clearly identify
   the action as a proposed action.
4. Return useful structured information.
5. Do not override BHAI.
"""

    return call_openai(
        user_request,
        system_instruction,
        model,
        api_key
    )


# ============================================================
# BHAI FINAL SYNTHESIS
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

**Request:** {user_request}

The following specialist agents were activated:

{", ".join(name for name, _ in results)}

### Combined Plan

{combined}

### BHAI Status

✅ Request processed successfully in Demo Mode.

Demo Mode simulates agent behavior and does not perform external actions.
"""

    system_instruction = """
You are BHAI, the master agent.

Combine the outputs from specialist agents into one clear final response.

Do not invent actions that were not performed.

Clearly distinguish:
- recommendations
- planned actions
- completed actions

Keep the answer practical and organized.
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
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🤖 BHAI AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    '20-Agent Daily Routine Intelligent Automation System'
    '</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="bhai-box">

<h2>🧠 BHAI — Master Agent</h2>

BHAI understands your request, selects the appropriate specialist
agents, coordinates their work and produces the final response.

<b>User → BHAI → Specialist Agents → Validation → Final Result</b>

</div>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ BHAI Control Panel")

mode = st.sidebar.radio(
    "Operating Mode",
    [
        "Demo Mode",
        "OpenAI API Mode"
    ]
)

model = st.sidebar.selectbox(
    "OpenAI Model",
    [
        "gpt-6-luna",
        "gpt-6-sol",
        "gpt-6-astra"
    ]
)

max_agents = st.sidebar.slider(
    "Maximum Agents per Request",
    min_value=1,
    max_value=10,
    value=5
)


# ============================================================
# API KEY
# ============================================================

api_key = ""

if mode == "OpenAI API Mode":

    st.sidebar.subheader("🔐 OpenAI API")

    existing_key = get_api_key()

    if existing_key:

        st.sidebar.success(
            "OpenAI API key detected."
        )

        api_key = existing_key

    else:

        api_key = st.sidebar.text_input(
            "Enter OpenAI API Key",
            type="password",
            placeholder="sk-..."
        )

        st.session_state.manual_api_key = api_key


# ============================================================
# MODE STATUS
# ============================================================

if mode == "Demo Mode":

    st.sidebar.success(
        "🟢 Demo Mode Active"
    )

else:

    if api_key:

        st.sidebar.success(
            "🔵 OpenAI API Mode Active"
        )

    else:

        st.sidebar.warning(
            "OpenAI API key required."
        )


# ============================================================
# AGENT DASHBOARD
# ============================================================

st.subheader("🧩 BHAI's 20 Specialist Agents")

cols = st.columns(4)

for i, (agent_name, description) in enumerate(AGENTS.items()):

    with cols[i % 4]:

        st.markdown(
            f"""
            <div class="agent-card">

            <b>{i + 1}. {agent_name}</b>

            <br>

            <small>{description}</small>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# USER REQUEST
# ============================================================

st.divider()

st.subheader("💬 Talk to BHAI")

user_request = st.text_area(
    "What do you want BHAI to manage?",
    placeholder=(
        "Example: Plan my day. I need to work, study Python, "
        "exercise, check my emails and relax in the evening."
    ),
    height=120
)


# ============================================================
# QUICK COMMANDS
# ============================================================

st.subheader("⚡ Quick Commands")

quick_cols = st.columns(4)

quick_commands = [
    "Plan my complete day",
    "Create my productivity routine",
    "Create a learning and fitness plan",
    "Organize my tasks and reminders"
]

for i, command in enumerate(quick_commands):

    if quick_cols[i].button(
        command,
        use_container_width=True
    ):

        user_request = command


# ============================================================
# RUN BHAI
# ============================================================

if st.button(
    "🚀 RUN BHAI MASTER AGENT",
    type="primary",
    use_container_width=True
):

    if not user_request.strip():

        st.warning(
            "Please enter a request for BHAI."
        )

        st.stop()


    # --------------------------------------------------------
    # MASTER AGENT ROUTING
    # --------------------------------------------------------

    with st.spinner("🧠 BHAI is understanding your request..."):

        if mode == "Demo Mode":

            selected_agents = bhai_demo_router(
                user_request,
                max_agents
            )

        else:

            if not api_key:

                st.error(
                    "OpenAI API key is required for API Mode."
                )

                st.stop()

            selected_agents = bhai_api_router(
                user_request,
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


    st.session_state.last_agents = selected_agents


    # --------------------------------------------------------
    # DISPLAY ROUTING
    # --------------------------------------------------------

    st.subheader("🧠 BHAI Agent Routing")

    st.info(
        f"BHAI selected {len(selected_agents)} specialist agent(s): "
        + ", ".join(selected_agents)
    )


    # --------------------------------------------------------
    # EXECUTE SPECIALISTS
    # --------------------------------------------------------

    results = []

    progress = st.progress(0)

    for index, agent_name in enumerate(selected_agents):

        st.write(
            f"⚙️ Running **{agent_name}**..."
        )

        if mode == "Demo Mode":

            result = run_demo_agent(
                agent_name,
                user_request
            )

        else:

            result = run_api_agent(
                agent_name,
                user_request,
                model,
                api_key
            )

        results.append(
            (agent_name, result)
        )

        progress.progress(
            (index + 1) / len(selected_agents)
        )


    st.session_state.last_results = results


    # --------------------------------------------------------
    # FINAL BHAI SYNTHESIS
    # --------------------------------------------------------

    with st.spinner(
        "🧠 BHAI is validating and preparing the final response..."
    ):

        final_response = bhai_final_summary(
            user_request,
            results,
            mode,
            model,
            api_key
        )


    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    st.divider()

    st.subheader("🤖 BHAI Final Response")

    st.markdown(final_response)


# ============================================================
# PREVIOUS AGENTS
# ============================================================

if st.session_state.last_agents:

    st.divider()

    st.subheader("📊 Last Execution")

    for agent in st.session_state.last_agents:

        st.success(
            f"✅ {agent} completed"
        )


# ============================================================
# CHAT HISTORY
# ============================================================

st.divider()

st.subheader("💡 Example Requests")

examples = [
    "BHAI, plan my day.",
    "BHAI, organize my work and study schedule.",
    "BHAI, create a fitness and learning routine.",
    "BHAI, prepare my meeting and email tasks.",
    "BHAI, organize my finances and shopping list.",
    "BHAI, plan my travel checklist.",
    "BHAI, give me a productive daily routine with some chess time."
]

for example in examples:

    st.code(example)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">

    🤖 <b>BHAI AI — 20-Agent Intelligent Daily Routine System</b>
    <br>
    Master Agent + 20 Specialist Agents
    <br><br>
    <b>By Engr. Bilal Mehmood</b>

    </div>
    """,
    unsafe_allow_html=True
)