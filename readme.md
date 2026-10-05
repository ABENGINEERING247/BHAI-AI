# 🤖 BHAI AI — 20-Agent Intelligent Daily Routine System

**BHAI** is a multi-agent AI assistant built with **Python + Streamlit + OpenAI API**.

BHAI acts as the **Master Agent** that understands the user's request, selects the most relevant specialist agents, coordinates their responses, and produces a final consolidated result.

The system supports two operating modes:

* 🟢 **Demo Mode** — runs without an OpenAI API key
* 🔵 **OpenAI API Mode** — uses OpenAI models for intelligent agent routing and responses

---

## 🚀 Project Overview

BHAI is designed to manage and organize everyday activities through a centralized AI architecture.

### Core Architecture

```text
                    👤 USER
                      │
                      ▼
              ┌───────────────┐
              │  BHAI MASTER  │
              │     AGENT     │
              └───────┬───────┘
                      │
                Intent Analysis
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Agent 01    Agent 02    Agent 03
          │           │           │
          │      Specialist      │
          │       Agents         │
          │           │           │
          └───────────┼───────────┘
                      ▼
             Validation / Synthesis
                      │
                      ▼
              🤖 BHAI FINAL RESULT
```

---

# 🧠 BHAI Master Agent

BHAI is the central controller of the system.

Its responsibilities include:

1. Understanding the user's request
2. Identifying the user's intent
3. Selecting relevant specialist agents
4. Controlling the number of agents
5. Passing the request to specialist agents
6. Collecting agent responses
7. Validating and combining results
8. Producing the final response

### BHAI Workflow

```text
User Request
     ↓
BHAI Understands Intent
     ↓
Agent Selection
     ↓
Specialist Agent Execution
     ↓
Result Collection
     ↓
Validation
     ↓
Final BHAI Response
```

---

# 🧩 20 Specialist Agents

BHAI controls the following 20 agents.

| #  | Agent               | Main Responsibility              |
| -- | ------------------- | -------------------------------- |
| 01 | Planner Agent       | Daily planning                   |
| 02 | Reminder Agent      | Reminders and recurring routines |
| 03 | Calendar Agent      | Events and time blocks           |
| 04 | Task Agent          | Tasks and to-do management       |
| 05 | Productivity Agent  | Focus and productivity           |
| 06 | Learning Agent      | Learning and study planning      |
| 07 | Research Agent      | Research organization            |
| 08 | Communication Agent | Communication planning           |
| 09 | Email Agent         | Email drafting and planning      |
| 10 | Meeting Agent       | Meeting agendas and follow-up    |
| 11 | Health Agent        | General wellness routines        |
| 12 | Fitness Agent       | Exercise and activity planning   |
| 13 | Finance Agent       | Budget and expense organization  |
| 14 | Shopping Agent      | Shopping lists                   |
| 15 | Travel Agent        | Travel planning                  |
| 16 | News Agent          | News-reading routines            |
| 17 | Notes Agent         | Notes and ideas                  |
| 18 | File Agent          | File/document organization       |
| 19 | Home Agent          | Household routines               |
| 20 | Entertainment Agent | Games and hobbies                |

---

# ⚙️ Operating Modes

## 🟢 Demo Mode

Demo Mode does not require an OpenAI API key.

It uses predefined routing logic and simulated agent responses.

### Benefits

* No API cost
* No API key required
* Useful for classroom demonstrations
* Useful for testing the user interface
* Useful for understanding the multi-agent architecture
* Can run offline after dependencies are installed

Example:

```text
User:
Plan my day with Python study and exercise.

BHAI:
Planner Agent
Learning Agent
Fitness Agent
Productivity Agent
```

---

# 🔵 OpenAI API Mode

OpenAI API Mode provides intelligent routing and AI-generated specialist responses.

The architecture uses:

```text
Streamlit
     ↓
BHAI Master Agent
     ↓
OpenAI API
     ↓
Specialist Agents
     ↓
OpenAI API
     ↓
BHAI Final Synthesis
```

An API key is required.

---

# 📁 Project Structure

Recommended project structure:

```text
bhai_ai/
│
├── app.py
│
├── requirements.txt
│
└── README.md
```

### `app.py`

Main Streamlit application containing:

* BHAI Master Agent
* 20 specialist agents
* Demo Mode
* OpenAI API Mode
* Agent routing
* Agent execution
* Final response synthesis
* User interface

### `requirements.txt`

Contains the required Python packages.

### `README.md`

Project documentation.

---

# 💻 Installation

## Step 1 — Create Project Folder

Open Command Prompt or Terminal:

```bash
mkdir bhai_ai
cd bhai_ai
```

---

## Step 2 — Create Virtual Environment

```bash
python -m venv .venv
```

---

## Step 3 — Activate Virtual Environment

### Windows CMD

```cmd
.venv\Scripts\activate.bat
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
source .venv/bin/activate
```

---

# 📦 Step 4 — Install Dependencies

Create `requirements.txt`:

```text
streamlit
openai
```

Then install:

```bash
pip install -r requirements.txt
```

---

# ▶️ Step 5 — Run BHAI

Run:

```bash
streamlit run app.py
```

The application will normally open at:

```text
http://localhost:8501
```

---

# 🔐 OpenAI API Key

For API Mode, provide your OpenAI API key.

## Windows CMD

```cmd
set OPENAI_API_KEY=your_api_key_here
```

Then run:

```cmd
streamlit run app.py
```

For permanent or deployed applications, use environment variables or Streamlit Secrets rather than hard-coding the API key in `app.py`.

---

# 🗝️ Streamlit Secrets

For deployment, create:

```text
.streamlit/
└── secrets.toml
```

Example:

```toml
OPENAI_API_KEY = "your_api_key_here"
```

Do **not** publish your API key on GitHub.

Add this to `.gitignore`:

```text
.streamlit/secrets.toml
.venv/
__pycache__/
*.pyc
```

---

# 💬 Example Commands

Users can communicate with BHAI using natural language.

### Daily Planning

```text
BHAI, plan my complete day.
```

### Study

```text
BHAI, create a Python learning plan for today.
```

### Fitness

```text
BHAI, create my daily fitness routine.
```

### Work

```text
BHAI, organize my work tasks and priorities.
```

### Email

```text
BHAI, help me organize today's emails.
```

### Meeting

```text
BHAI, prepare my meeting agenda and follow-up tasks.
```

### Finance

```text
BHAI, organize today's financial tasks.
```

### Shopping

```text
BHAI, create my shopping list.
```

### Travel

```text
BHAI, prepare a travel checklist.
```

### Games

```text
BHAI, schedule some chess time after my work.
```

---

# 🧠 Example Multi-Agent Execution

User enters:

```text
BHAI, plan my day. I have a meeting,
need to study Python, exercise, check emails,
and play chess in the evening.
```

BHAI may select:

```text
Planner Agent
        ↓
Meeting Agent
        ↓
Learning Agent
        ↓
Fitness Agent
        ↓
Email Agent
        ↓
Entertainment Agent
```

The specialist results are then sent to BHAI for final synthesis.

```text
Specialist Results
       ↓
BHAI Validation
       ↓
BHAI Final Plan
```

---

# 🎛️ Agent Control

The Streamlit sidebar provides controls for:

### Operating Mode

```text
Demo Mode
OpenAI API Mode
```

### Model

The application provides a model-selection field.

### Maximum Agents

The user can control how many specialist agents BHAI can activate for one request.

Example:

```text
Maximum Agents = 5
```

BHAI will select no more than five agents.

---

# 🛡️ Safety Design

BHAI does not falsely claim to have completed external actions.

For example, without a real email integration:

```text
BHAI can:
✓ Draft an email
✓ Suggest recipients
✓ Create an email task

BHAI cannot claim:
✗ Email was actually sent
```

Similarly, without a calendar integration:

```text
BHAI can:
✓ Create a proposed schedule

BHAI cannot claim:
✗ Calendar event was actually created
```

This architecture makes the system suitable for demonstration and future integration.

---

# 🔌 Future Integrations

BHAI can later be connected to external services.

Possible architecture:

```text
                    BHAI
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
      Email        Calendar       Tasks
        │             │             │
        ▼             ▼             ▼
     Gmail         Calendar       Database
```

Other possible integrations include:

* Google Calendar
* Gmail
* Microsoft Outlook
* Google Drive
* WhatsApp
* Telegram
* Slack
* Notion
* Trello
* GitHub
* n8n
* databases
* IoT systems
* robotics systems

These integrations require appropriate APIs, authentication and permissions.

---

# 🔄 Future Agentic Architecture

A future production version can use:

```text
                         USER
                           │
                           ▼
                    ┌─────────────┐
                    │     BHAI    │
                    │ MASTER AGENT│
                    └──────┬──────┘
                           │
                    Intent + Planning
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
           Planning     Personal     Productivity
            Agents       Agents         Agents
              │            │            │
              └────────────┼────────────┘
                           ▼
                       Validator
                           │
                           ▼
                       BHAI AI
                           │
                           ▼
                         USER
```

---

# 🏗️ Recommended Production Architecture

For a larger production system:

```text
Frontend
   │
   ▼
Streamlit
   │
   ▼
BHAI Orchestrator
   │
   ├── Planning
   ├── Productivity
   ├── Learning
   ├── Communication
   ├── Wellness
   ├── Finance
   ├── Travel
   ├── Home
   └── Entertainment
   │
   ▼
OpenAI API
   │
   ▼
Tools / APIs / Databases
```

---

# 📊 Current Version

### Version

```text
BHAI AI v1.0
```

### Technology

```text
Python
Streamlit
OpenAI API
```

### Modes

```text
Demo Mode
OpenAI API Mode
```

### Agents

```text
20 Specialist Agents
+
1 Master Agent
```

### Total Intelligent Components

```text
21 Agents
```

---

# 🎯 Project Objective

The objective of BHAI is to create a centralized AI assistant capable of coordinating multiple specialized AI agents for everyday activities.

Instead of interacting separately with multiple AI systems, the user communicates with one central agent:

```text
                  USER
                    │
                    ▼
              🤖 BHAI
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
    Planning     Learning     Productivity
       │            │            │
       └────────────┼────────────┘
                    ▼
              FINAL RESULT
```

---

# 🚀 Future Roadmap

## Phase 1 — Completed

* [x] Streamlit interface
* [x] BHAI Master Agent
* [x] 20 specialist agents
* [x] Demo Mode
* [x] OpenAI API Mode
* [x] Agent routing
* [x] Final response synthesis

## Phase 2

* [ ] Persistent user profiles
* [ ] Database
* [ ] Task history
* [ ] Conversation memory
* [ ] Authentication
* [ ] Agent logs
* [ ] Agent performance monitoring

## Phase 3

* [ ] Gmail integration
* [ ] Google Calendar
* [ ] Google Drive
* [ ] WhatsApp/Telegram
* [ ] n8n workflows
* [ ] Notifications
* [ ] Automated reminders

## Phase 4

* [ ] Voice control
* [ ] Mobile interface
* [ ] IoT integration
* [ ] Robotics integration
* [ ] Autonomous workflows
* [ ] Advanced multi-agent planning

---

# ⚠️ Important Notes

BHAI is an AI orchestration framework. The initial version generates plans and responses but does not automatically perform real-world actions unless an appropriate external integration is connected.

API usage may incur charges according to the OpenAI account and selected model.

Never expose your OpenAI API key in:

* GitHub repositories
* Public Streamlit applications
* Screenshots
* Source code
* Public documentation

---

# 👨‍💻 Author

**Engr. Bilal Mehmood**

AI Course Director / AI Instructor
PITAC Regional Center Karachi, Sindh

---

# ⭐ BHAI Concept

> **One User → One Master Agent → 20 Specialist Agents → One Intelligent Result**

**BHAI — Your Master AI for Daily Routines**

```text
Think → Plan → Delegate → Execute → Validate → Respond
```
