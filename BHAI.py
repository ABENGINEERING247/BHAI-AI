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
    padding: 25px;
    color: #777;
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

</style>
""", unsafe_allow_html=True)


# ============================================================
# 20 AGENTS
# ============================================================

AGENTS = {

    "Planner Agent":
        "Plans the user's day and sets priorities.",

    "Reminder Agent":
        "Creates and organizes reminders and recurring routine items.",

    "Calendar Agent":
        "Plans events, meetings and time blocks.",

    "Task Agent":
        "Breaks goals into actionable tasks.",

    "Productivity Agent":
        "Improves focus, work routines and productivity.",

    "Learning Agent":
        "Creates study and learning plans.",

    "Research Agent":
        "Organizes research questions and research tasks.",

    "Communication Agent":
        "Plans and drafts communication activities.",

    "Email Agent":
        "Generates professional emails and email-related task plans.",

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
        "Organizes file and document tasks.",

    "Home Agent":
        "Organizes household and daily home routines.",

    "Entertainment Agent":
        "Plans games, hobbies and leisure activities."
}


# ============================================================
# KEYWORD ROUTING
# ============================================================

KEYWORD_ROUTING = {

    "Planner Agent":
        ["plan", "day", "daily", "schedule", "routine"],

    "Reminder Agent":
        ["remind", "reminder", "remember", "alert", "notification"],

    "Calendar Agent":
        ["calendar", "event", "appointment", "meeting time"],

    "Task Agent":
        ["task", "todo", "to-do", "work"],

    "Productivity Agent":
        ["productive", "focus", "productivity"],

    "Learning Agent":
        ["learn", "study", "course", "python", "education"],

    "Research Agent":
        ["research", "paper", "literature", "researcher"],

    "Communication Agent":
        ["message", "communication", "whatsapp", "reply"],

    "Email Agent":
        ["email", "mail", "send email", "write email", "draft email"],

    "Meeting Agent":
        ["meeting", "agenda", "minutes"],

    "Health Agent":
        ["health", "wellness", "sleep", "water"],

    "Fitness Agent":
        ["fitness", "exercise", "workout", "walk"],

    "Finance Agent":
        ["finance", "budget", "expense", "money"],

    "Shopping Agent":
        ["shopping", "buy", "purchase", "list"],

    "Travel Agent":
        ["travel", "trip", "hotel", "flight"],

    "News Agent":
        ["news", "headline"],

    "Notes Agent":
        ["note", "notes", "idea"],

    "File Agent":
        ["file", "document", "folder"],

    "Home Agent":
        ["home", "house", "clean", "household"],

    "Entertainment Agent":
        ["game", "games", "movie", "music", "hobby", "fun", "chess"]
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

if "reminders" not in st.session_state:
    st.session_state.reminders = []

if "deadlines" not in st.session_state:
    st.session_state.deadlines = []

if "generated_emails" not in st.session_state:
    st.session_state.generated_emails = []


# ============================================================
# API KEY
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
# OPENAI FUNCTION
# ============================================================

def call_openai(
    prompt,
    system_instruction,
    model,
    api_key
):

    if not OpenAI:
        return (
            "OpenAI package is not installed. "
            "Run: pip install openai"
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

        return f"OpenAI API Error: {str(e)}"


# ============================================================
# DEMO ROUTER
# ============================================================

def bhai_demo_router(
    user_request,
    max_agents=5
):

    text = user_request.lower()

    selected = []

    for agent_name, keywords in KEYWORD_ROUTING.items():

        for keyword in keywords:

            if keyword in text:

                if agent_name not in selected:
                    selected.append(agent_name)

                break

    if not selected:

        selected = [
            "Planner Agent",
            "Task Agent",
            "Productivity Agent"
        ]

    return selected[:max_agents]


# ============================================================
# API ROUTER
# ============================================================

def bhai_api_router(
    user_request,
    model,
    api_key,
    max_agents
):

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

You are the MASTER AGENT of a
20-agent daily routine automation system.

Your job is to understand the user's request
and select the most relevant specialist agents.

Available agents:

{agent_list}

RULES:

1. Select only genuinely relevant agents.
2. Select maximum {max_agents} agents.
3. For general daily planning use:
   Planner Agent,
   Task Agent,
   Productivity Agent.
4. Return ONLY exact agent names separated by commas.
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
# DEMO SPECIALIST AGENTS
# ============================================================

def run_demo_agent(
    agent_name,
    user_request
):

    demo_responses = {

        "Planner Agent":
            f"Create a priority-based daily plan for: {user_request}",

        "Reminder Agent":
            "Create reminders for important tasks, meetings, "
            "learning sessions and daily routines.",

        "Calendar Agent":
            "Allocate focused work blocks, meetings and personal time.",

        "Task Agent":
            "Break the user's request into small actionable tasks.",

        "Productivity Agent":
            "Use focused work sessions with short breaks.",

        "Learning Agent":
            "Reserve a learning session and define today's objective.",

        "Research Agent":
            "Define question → collect sources → analyze → summarize.",

        "Communication Agent":
            "Identify recipient, purpose and required communication.",

        "Email Agent":
            "Prepare subject → greeting → message → closing → review.",

        "Meeting Agent":
            "Agenda → discussion → decisions → action items.",

        "Health Agent":
            "Hydration, breaks, sleep routine and general wellbeing.",

        "Fitness Agent":
            "Walking, stretching and suitable daily activity.",

        "Finance Agent":
            "Record expenses, review budget and financial tasks.",

        "Shopping Agent":
            "Create priority shopping list and separate urgent items.",

        "Travel Agent":
            "Itinerary → transport → accommodation → checklist.",

        "News Agent":
            "Reserve time for reviewing trusted news sources.",

        "Notes Agent":
            "Capture idea → organize → tag → review.",

        "File Agent":
            "Organize documents into logical folders.",

        "Home Agent":
            "Prioritize cleaning, maintenance and household tasks.",

        "Entertainment Agent":
            "Select a hobby, game, movie, music or chess activity."
    }

    return (
        "[DEMO] " +
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

    description = AGENTS[agent_name]

    system_instruction = f"""

You are the {agent_name}.

Your responsibility:

{description}

You are a specialist controlled by
the master agent BHAI.

User request:

{user_request}

RULES:

1. Give practical and concise results.
2. Do not claim external actions were performed
   unless a real integration exists.
3. Identify proposed actions clearly.
4. Return structured information.
5. Do not override BHAI.

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

**Request:** {user_request}

**Activated Agents:**

{", ".join(
    name for name, _ in results
)}

### Combined Plan

{combined}

### BHAI Status

✅ Request processed successfully in Demo Mode.

Demo Mode simulates agent behavior and does not
perform external actions.

"""

    system_instruction = """

You are BHAI, the master agent.

Combine specialist outputs into one clear final response.

Clearly distinguish:

- Recommendations
- Planned actions
- Completed actions

Never claim an external action was performed
unless an actual integration exists.

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
# REMINDER CREATOR
# ============================================================

def add_reminder(
    title,
    reminder_date,
    reminder_time,
    priority
):

    reminder = {
        "title": title,
        "date": str(reminder_date),
        "time": reminder_time,
        "priority": priority,
        "created": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )
    }

    st.session_state.reminders.append(
        reminder
    )


# ============================================================
# DEADLINE CREATOR
# ============================================================

def add_deadline(
    title,
    deadline_date,
    priority,
    notes
):

    deadline = {
        "title": title,
        "date": str(deadline_date),
        "priority": priority,
        "notes": notes,
        "created": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )
    }

    st.session_state.deadlines.append(
        deadline
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

    prompt = f"""

Create a professional email.

Recipient:
{recipient}

Purpose:
{purpose}

Tone:
{tone}

Additional details:
{details}

Return:

Subject:
...

Email Body:
...

"""

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

    system_instruction = """

You are the BHAI Email Generator Agent.

Write clear, professional and grammatically
correct emails.

Do not invent important facts.

Return the subject and complete email body.

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

st.markdown(
    """
<div class="bhai-box">

<h2>🧠 BHAI — Master Agent</h2>

BHAI understands your request, selects the appropriate
specialist agents, coordinates their work and produces
the final response.

<br><br>

<b>
User → BHAI → Specialist Agents → Validation → Final Result
</b>

</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header(
    "⚙️ BHAI Control Panel"
)

mode = st.sidebar.radio(
    "Operating Mode",
    [
        "Demo Mode",
        "OpenAI API Mode"
    ]
)

# Use a model available in your OpenAI account.
model = st.sidebar.text_input(
    "OpenAI Model",
    value="gpt-5"
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

    st.sidebar.subheader(
        "🔐 OpenAI API"
    )

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

st.subheader(
    "🧩 BHAI's 20 Specialist Agents"
)

cols = st.columns(4)

for i, (
    agent_name,
    description
) in enumerate(AGENTS.items()):

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
# AUTOMATION CENTER
# ============================================================

st.divider()

st.header(
    "⚡ BHAI Automation Center"
)

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "💬 BHAI Master",
        "⏰ Reminders",
        "📅 Deadlines",
        "📧 Email Generator"
    ]
)


# ============================================================
# TAB 1 - BHAI MASTER
# ============================================================

with tab1:

    st.subheader(
        "💬 Talk to BHAI"
    )

    user_request = st.text_area(
        "What do you want BHAI to manage?",
        placeholder=(
            "Example: Plan my day. I need to work, "
            "study Python, exercise, check my emails "
            "and relax in the evening."
        ),
        height=120
    )

    st.subheader(
        "⚡ Quick Commands"
    )

    quick_cols = st.columns(4)

    quick_commands = [
        "Plan my complete day",
        "Create my productivity routine",
        "Create a learning and fitness plan",
        "Organize my tasks and reminders"
    ]

    for i, command in enumerate(
        quick_commands
    ):

        if quick_cols[i].button(
            command,
            use_container_width=True
        ):

            user_request = command

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

        # ----------------------------------------------------
        # ROUTING
        # ----------------------------------------------------

        with st.spinner(
            "🧠 BHAI is understanding your request..."
        ):

            if mode == "Demo Mode":

                selected_agents = bhai_demo_router(
                    user_request,
                    max_agents
                )

            else:

                if not api_key:

                    st.error(
                        "OpenAI API key is required."
                    )

                    st.stop()

                selected_agents = bhai_api_router(
                    user_request,
                    model,
                    api_key,
                    max_agents
                )

        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------

        if not selected_agents:

            selected_agents = [
                "Planner Agent",
                "Task Agent",
                "Productivity Agent"
            ]

        st.session_state.last_agents = selected_agents

        # ----------------------------------------------------
        # ROUTING DISPLAY
        # ----------------------------------------------------

        st.subheader(
            "🧠 BHAI Agent Routing"
        )

        st.info(
            f"BHAI selected "
            f"{len(selected_agents)} specialist agent(s): "
            + ", ".join(selected_agents)
        )

        # ----------------------------------------------------
        # EXECUTE
        # ----------------------------------------------------

        results = []

        progress = st.progress(0)

        for index, agent_name in enumerate(
            selected_agents
        ):

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
                (
                    agent_name,
                    result
                )
            )

            progress.progress(
                (index + 1) /
                len(selected_agents)
            )

        st.session_state.last_results = results

        # ----------------------------------------------------
        # FINAL SYNTHESIS
        # ----------------------------------------------------

        with st.spinner(
            "🧠 BHAI is preparing final response..."
        ):

            final_response = bhai_final_summary(
                user_request,
                results,
                mode,
                model,
                api_key
            )

        st.divider()

        st.subheader(
            "🤖 BHAI Final Response"
        )

        st.markdown(
            final_response
        )


# ============================================================
# TAB 2 - REMINDERS
# ============================================================

with tab2:

    st.subheader(
        "⏰ Reminder Manager"
    )

    with st.form(
        "reminder_form"
    ):

        reminder_title = st.text_input(
            "Reminder",
            placeholder="Example: Submit AI workshop proposal"
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

        add_reminder_button = st.form_submit_button(
            "➕ Add Reminder"
        )

        if add_reminder_button:

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

<b>⏰ {reminder["title"]}</b>

<br>

📅 {reminder["date"]}

&nbsp;&nbsp;

🕐 {reminder["time"]}

<br>

🔔 Priority: <b>{reminder["priority"]}</b>

</div>
""",
                unsafe_allow_html=True
            )

            if st.button(
                f"🗑️ Delete Reminder {i + 1}",
                key=f"delete_reminder_{i}"
            ):

                st.session_state.reminders.pop(i)

                st.rerun()

    else:

        st.info(
            "No reminders created yet."
        )


# ============================================================
# TAB 3 - DEADLINES
# ============================================================

with tab3:

    st.subheader(
        "📅 Deadline Manager"
    )

    with st.form(
        "deadline_form"
    ):

        deadline_title = st.text_input(
            "Deadline",
            placeholder="Example: Submit project report"
        )

        deadline_date = st.date_input(
            "Deadline Date",
            value=date.today()
        )

        deadline_priority = st.selectbox(
            "Deadline Priority",
            [
                "Critical",
                "High",
                "Medium",
                "Low"
            ]
        )

        deadline_notes = st.text_area(
            "Notes",
            placeholder="Additional deadline information..."
        )

        add_deadline_button = st.form_submit_button(
            "➕ Add Deadline"
        )

        if add_deadline_button:

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

<b>📅 {deadline["title"]}</b>

<br>

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
                key=f"delete_deadline_{i}"
            ):

                st.session_state.deadlines.pop(i)

                st.rerun()

    else:

        st.info(
            "No deadlines created yet."
        )


# ============================================================
# TAB 4 - EMAIL GENERATOR
# ============================================================

with tab4:

    st.subheader(
        "📧 BHAI AI Email Generator"
    )

    st.write(
        "Describe the email you need and BHAI will "
        "generate a professional email."
    )

    recipient = st.text_input(
        "Recipient Name / Department",
        placeholder="Example: Director / HR Department"
    )

    email_purpose = st.text_input(
        "Email Purpose",
        placeholder=(
            "Example: Request approval for AI workshop"
        )
    )

    email_tone = st.selectbox(
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

    email_details = st.text_area(
        "Additional Details",
        placeholder=(
            "Write the main points you want "
            "to include in the email."
        ),
        height=150
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

        elif not email_purpose.strip():

            st.warning(
                "Please enter email purpose."
            )

        else:

            if mode == "OpenAI API Mode" and not api_key:

                st.error(
                    "OpenAI API key is required "
                    "for API Mode."
                )

            else:

                with st.spinner(
                    "📧 BHAI Email Agent is writing..."
                ):

                    generated_email = generate_email(
                        recipient,
                        email_purpose,
                        email_tone,
                        email_details,
                        mode,
                        model,
                        api_key
                    )

                st.session_state.generated_emails.append(
                    generated_email
                )

                st.success(
                    "Email generated successfully."
                )

                st.markdown(
                    '<div class="email-box">',
                    unsafe_allow_html=True
                )

                st.markdown(
                    generated_email
                )

                st.markdown(
                    '</div>',
                    unsafe_allow_html=True
                )


# ============================================================
# QUICK DASHBOARD
# ============================================================

st.divider()

st.header(
    "📊 BHAI Productivity Dashboard"
)

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "🤖 Agents",
        "20"
    )

with col2:

    st.metric(
        "⏰ Reminders",
        len(st.session_state.reminders)
    )

with col3:

    st.metric(
        "📅 Deadlines",
        len(st.session_state.deadlines)
    )

with col4:

    st.metric(
        "📧 Emails Generated",
        len(st.session_state.generated_emails)
    )


# ============================================================
# LAST EXECUTION
# ============================================================

if st.session_state.last_agents:

    st.divider()

    st.subheader(
        "📊 Last BHAI Execution"
    )

    for agent in st.session_state.last_agents:

        st.success(
            f"✅ {agent} completed"
        )


# ============================================================
# EXAMPLE REQUESTS
# ============================================================

st.divider()

st.subheader(
    "💡 Example BHAI Requests"
)

examples = [

    "BHAI, plan my day.",

    "BHAI, remind me to submit my AI report tomorrow at 10 AM.",

    "BHAI, create a deadline for my Python project on Friday.",

    "BHAI, organize my work and study schedule.",

    "BHAI, create a fitness and learning routine.",

    "BHAI, prepare my meeting and email tasks.",

    "BHAI, generate a professional email requesting workshop approval.",

    "BHAI, organize my finances and shopping list.",

    "BHAI, plan my travel checklist.",

    "BHAI, give me a productive daily routine with some chess time."

]

for example in examples:

    st.code(
        example
    )


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

⏰ Reminders |
📅 Deadlines |
📧 Email Generator |
🧠 AI Task Management

<br><br>

<b>By Engr. Bilal Mehmood</b>

</div>
""",
    unsafe_allow_html=True
)
