# agents/orchestrator_tools.py

# We need to import the actual functions from our existing files
from tools.task_extractor_tool import task_extractor_tool
from tools.pdf_reader_tool import pdf_reader_tool
from database.memory_service import get_all_active_tasks,insert_task, mark_task_complete
from agents.scheduler_agent import create_and_save_schedule
import json
from agents.progress_agent import generate_progress_report
from google import genai

client = genai.Client()

def summarize_document_tool(file_path: str) -> str:
    """
    Summarizes a document (PDF, etc.). Use this when the user asks for a summary
    or reading comprehension. Returns the summary text.
    """
    return pdf_reader_tool(file_path)

def extract_assignment_data_tool(file_path: str) -> str:
    """
    Extracts structured assignment data and SAVES it to the database.
    Returns the extracted JSON data *including the database ID*.
    """
    # task_extractor_tool returns a dict, convert it to string for the Orchestrator
    
    task_data = task_extractor_tool(file_path)

    # 2. Save to database and get ID
    # This call is likely inside your implementation of task_extractor_tool or a wrapper.
    # ASSUMPTION: The task is saved and the ID is retrieved successfully.
    # Let's assume you save it and assign the ID here:
    task_id = insert_task(task_data)

    if task_id==-1:
        return json.dumps({"error": "Failed to save task to memory."})
    # 3. Add the ID to the task_data for the Orchestrator to see
    task_data['task_id'] = task_id # <-- THIS IS THE KEY LINE
    return json.dumps(task_data)

def retrieve_active_tasks() -> str:
    """
    Retrieves the list of all currently active (not completed) assignments 
    from the persistent memory database. Use this before planning a new schedule.
    Returns a list of tasks in JSON format as a string.
    """
    
    tasks = get_all_active_tasks()
    return json.dumps(tasks)

#  Scheduler Agent is built.
def schedule_task_tool(task_id: int, task_details: str) -> str:
    """
    Creates a detailed study schedule for a specific task and saves the schedule.
    Use this when the user asks to 'schedule', 'plan', or 'create a study plan'.
    Returns a success message and schedule summary.
    """
    # Convert JSON string back to Python dictionary for the scheduler function
    try:
        task_details_dict = json.loads(task_details)
    except json.JSONDecodeError:
        return "Error: Invalid JSON format provided for task details."

    # Call the main scheduler function
    return create_and_save_schedule(task_id, task_details_dict)

def get_progress_report_tool(task_id: int = None) -> str:
    """
    Generates a reminder and progress report. If task_id is provided, 
    the report focuses on that specific task's schedule and deadline.
    Use this when the user asks for a 'reminder', 'update', or 'progress report'.
    """
    return generate_progress_report(task_id=task_id)

def complete_task_tool(task_id: int) -> str:
    """
    Marks a specific task as completed in the database.
    Use this when the user says 'I finished', 'mark as done', or 'complete task ID X'.
    """
    if mark_task_complete(task_id):
        return f"SUCCESS: Task ID {task_id} has been marked as complete and moved to history."
    else:
        return f"ERROR: Could not find or mark Task ID {task_id} as complete."
    
# agents/orchestrator_tools.py (Add this function)

def generate_practice_worksheet(topic: str, num_problems: int) -> str:
    """
    Generates a specified number of practice problems for a given technical topic, 
    saving the output as a downloadable text file (simulated).
    
    Args:
        topic: The specific technical subject for the worksheet (e.g., 'SJF Non-Preemptive Scheduling').
        num_problems: The number of practice problems to generate (e.g., 3).
        
    Returns:
        A success message containing the generated content and a simulated file path.
    """
    
    
    
    # Use a specific, powerful prompt to force structured content generation
    prompt = (
        f"You are an expert academic tutor. Generate a practice worksheet consisting of {num_problems} distinct "
        f"and challenging numerical problems on the topic of '{topic}'. "
        "For each problem, define the Process ID, Arrival Time, and Burst Time. "
        "Do NOT provide the solution. Format the output clearly with headings for each problem."
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        
        # Simulate saving the content to a file
        file_name = f"downloads/{topic.replace(' ', '_')}_worksheet.txt"
        
        # In a real app, you would save it here:
        # with open(file_name, 'w') as f:
        #     f.write(response.text)

        return (f"SUCCESS: A practice worksheet with {num_problems} problems on '{topic}' "
                f"has been generated and is ready for download. "
                f"Simulated File Path: {file_name}\n\n"
                f"--- GENERATED CONTENT START ---\n"
                f"{response.text}\n"
                f"--- GENERATED CONTENT END ---")
        
    except Exception as e:
        return f"ERROR: Failed to generate content: {e}"