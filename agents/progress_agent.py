# agents/progress_agent.py

from google import genai
from database.memory_service import get_all_active_tasks, get_schedule_by_task_id
import json
from datetime import datetime
from tools import orchestrator_tools
from google.genai.errors import APIError

client = genai.Client()


def generate_progress_report(task_id: int = None) -> str:
    """
    Generates a progress report/reminder based on active tasks and schedules.
    If task_id is provided, it focuses on that task. Otherwise, it reviews all active tasks.
    """
    print("\n[PROGRESS AGENT] Generating progress report...")
    
    active_tasks = get_all_active_tasks()
    
    if not active_tasks:
        return "You have no active assignments. Enjoy your free time!"

    # Prepare context for the LLM
    tasks_context = json.dumps(active_tasks, indent=2)
    schedule_context = ""
    
    if task_id:
        # If a specific ID is requested, get its schedule
        schedule_text = get_schedule_by_task_id(task_id)
        if schedule_text and "No schedule found" not in schedule_text:
            schedule_context = f"\n\n--- SPECIFIC SCHEDULE FOR TASK ID {task_id} ---\n{schedule_text}"

    # --- Construct the LLM Prompt ---
    current_date = datetime.now().strftime("%A, %B %d, %Y, %H:%M:%S")

    PROGRESS_AGENT_TOOLS = [
    # tool for reading the current tasks(essential for its function)
    get_all_active_tasks,

    # tool for proactive resource generation
    orchestrator_tools.generate_practice_worksheet,
    ]
    
    SYSTEM_INSTRUCTION = (
        f"You are the Progress and Resource Agent. The current date and time is {current_date}. "
        "Your goal is to provide a comprehensive, motivational report. "
        "Analyze the user's active tasks and schedules."
        
        # PROACTIVE RULE IMPLEMENTATION:
        "CRITICAL PROACTIVE RULE: If your analysis shows the **highest-priority next step** "
        "is a numerical problem, a calculation, or a concept that requires immediate practice "
        "(e.g., 'SJF Non-Preemptive Scheduling', 'IP Subnetting'), "
        "you MUST proactively generate a resource. In this scenario, you MUST call the "
        "'generate_practice_worksheet' tool immediately, suggesting 3 problems by default. "
        "If you call the tool, you must incorporate its result into the final report. "
        "If you do NOT call a tool, your final output must be a clean, motivational text report."
    )
    
    user_prompt = (
        "Analyze the following data and generate the report and/or call the necessary tool. "
        "\n\n--- ALL ACTIVE TASKS ---\n"
        f"{tasks_context}"
        f"{schedule_context}"
    )

    # --- 3. Execute the Tool-Calling Loop ---
    # The progress agent now acts as a mini-orchestrator using its own tools
    
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=[SYSTEM_INSTRUCTION, user_prompt],
        config={"tools": PROGRESS_AGENT_TOOLS}
    )
    
    # Simple loop to handle one tool call
    if response.function_calls:
        function_call = response.function_calls[0]
        tool_name = function_call.name
        tool_args = dict(function_call.args)
        
        # --- Check for the desired proactive call ---
        if tool_name == orchestrator_tools.generate_practice_worksheet.__name__:
            print(f"[PROGRESS AGENT] Proactively calling tool: {tool_name} with args: {tool_args}")
            
            # Execute the Content Generation Tool
            tool_output = orchestrator_tools.generate_practice_worksheet(**tool_args)
            
            # Now, send the tool output back to the LLM to format the final report
            final_response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    SYSTEM_INSTRUCTION, 
                    user_prompt, 
                    response.candidates[0].content, # The original tool call
                    {"functionResponse": {"name": tool_name, "response": {"content": tool_output}}} # Tool Result
                ],
                config={"tools": PROGRESS_AGENT_TOOLS}
            )
            return final_response.text

    # If no tool was called (or if the tool loop completes without a second call), return the text.
    return response.text