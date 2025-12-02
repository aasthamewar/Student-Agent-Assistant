## 🚀 Overview
The Autonomous Study Agent is a powerful, AI-driven assistant designed to manage a student's academic workload. Utilizing the Google Gemini API with advanced **Function Calling** capabilities, the agent can analyze assignment files (PDFs, images), automatically extract key details (deadline, subject, priority), save tasks to a persistent SQLite database, and generate personalized study schedules.

The agent operates via a central **Orchestrator** that intelligently sequences tool calls (like Extraction, Database Insertion, and Scheduling) to fulfill complex user requests in a single prompt.

---
## Here is how thinks works

<img width="1015" height="553" alt="blueprint of Agent project (1)" src="https://github.com/user-attachments/assets/be7e2022-dac9-4406-8176-0f8870340c8e" />


## ✨ Key Features

* **Intelligent Task Extraction:** Analyzes documents (`.pdf`, `.jpg`, etc.) using the `gemini-2.5-flash` model to extract structured data like deadline, subject, task type, and priority.
* **Persistent Memory:** Uses **SQLite** (`student_agent_memory.db`) to store tasks, deadlines, and generated schedules.
* **Orchestration Logic:** A central agent determines the necessary sequence of function calls (e.g., Extract $\rightarrow$ Insert $\rightarrow$ Schedule) to complete multi-step requests.
* **Adaptive Scheduling:** Generates detailed, multi-day study plans based on the task deadline, priority, and existing workload.
* **Error Resilience:** Includes robust **deadline safeguards** to prevent database crashes and **retry logic (Exponential Backoff)** to handle intermittent API rate limits (`429 RESOURCE_EXHAUSTED`).

---

## 🛠️ Project Structure

The project is organized into modular directories for clean separation of concerns:

| Directory | Purpose | Key Files |
| :--- | :--- | :--- |
| **`agents/`** | Core decision-making and logic flow. | `orchestrator_agent.py`,`progress_agent`,`router_agent`,`pdf_agent` |
| **`database/`**| Handles all SQLite database interactions. | `memory_service.py` |
| **`tools/`** | Contains Python functions wrapped for the Gemini API. | `task_extractor_tool.py`, `orchestrator_tools.py` |
| **`uploads/`** | Directory for user-provided assignment files. | `example` |
| **Root** | Main application entry point and configuration. | `main.py`, `config.py` |

---

## ⚙️ Setup and Installation

### 1. Clone the Repository (If Applicable)

```bash
git clone [YOUR_REPO_URL]
cd autonomous-study-agent
```

## 2. Set Up the Environment
```
# Create the virtual environment (using Python 3.10 as specified in project)
# If your default is 3.10:
python -m venv ai_env
# Otherwise, specify the version:
py -3.10 -m venv ai_env

# Activate the environment
.\ai_env\Scripts\activate  # On Windows PowerShell
# source ai_env/bin/activate  # On Linux/macOS
```
## 3. Install Dependencies
```
pip install -r requirements.txt
```
```
Required requirements.txt Content:

google-genai
flask
pydantic
python-dotenv
```
## 4. Configure API Key
```
# Replace YOUR_API_KEY_HERE with your actual key
export GEMINI_API_KEY="YOUR_API_KEY_HERE"  # Linux/macOS
# OR
$env:GEMINI_API_KEY="YOUR_API_KEY_HERE" # Windows PowerShell
```

## 5. Run the Agent
```
python main.py
```
