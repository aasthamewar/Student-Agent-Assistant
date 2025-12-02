# agents/scheduler_agent.py

from google import genai
from database.memory_service import get_all_active_tasks, insert_schedule, get_task_by_id
import json
import traceback
import sys

client = genai.Client()

def create_and_save_schedule(task_id: int, task_details: dict) -> str:
    """
    Generates a detailed study/work schedule using the LLM and saves it to memory.
    
    Args:
        task_id: The ID of the task in the database (used to link the schedule).
        task_details: The structured data of the assignment being scheduled.
        
    Returns:
        A text summary of the schedule and existing conflicts.
    """
    # print("\n[SCHEDULER] Generating schedule...")

    # --- 1. Consult Memory for Context ---
    # Retrieve all *other* active tasks to ensure the new schedule avoids overlaps.
    active_tasks = get_all_active_tasks()
    
    # Filter out the task we are currently scheduling from the conflict list
    conflict_tasks = [t for t in active_tasks if str(t.get('id')) != str(task_id)]
    
    # Convert data back to clean strings for the model
    details_string = json.dumps(task_details, indent=2)
    conflict_string = json.dumps(conflict_tasks, indent=2)
    try:
    # --- 2. Construct the Memory-Aware Prompt ---
      scheduling_prompt = (
        "You are an expert academic scheduler. Your goal is to create a detailed, 5-day work schedule "
        "to complete the following task, ensuring the work finishes 1 day before the deadline. "
        "Include daily steps, estimated time, and a final review step. Format the schedule using Markdown tables for clarity."
        "\n\n--- TARGET TASK DETAILS ---\n"
        f"{details_string}"
        "\n\n--- EXISTING SCHEDULED CONFLICTS (Prioritize these deadlines) ---\n"
        f"{conflict_string}"
        "\n\nIMPORTANT: Note any potential time conflicts based on existing tasks and suggest adjustments in the final schedule table."
      )

    # --- 3. Generate Content ---
      response = client.models.generate_content(
        model="gemini-2.0-pro",  # Use Pro for better complex generation/formatting
        contents=scheduling_prompt
       )
    
      schedule_text = response.text
    
    # --- 4. Save Schedule to Database ---
      # print(f"[SCHEDULER] Saving schedule to memory (Task ID: {task_id})...")
      insert_schedule(task_id, schedule_text)
    
     # --- 5. Return Summary for Orchestrator ---
      summary = (
        f"Schedule generated and saved successfully for Task ID {task_id} "
        f"(Subject: {task_details.get('subject', 'N/A')}).\n\n"
        "Summary of new schedule:\n"
        # Ensure the slice is safe even if schedule_text is short
        f"{schedule_text[:300]}...\n\n" 
        "The schedule was designed to avoid conflicts with your existing tasks."
       )
      return summary

    except Exception as e:
        # PRINT THE FULL TECHNICAL ERROR HERE
        print("\n" + "="*50)
        print("[CRITICAL SCHEDULER AGENT ERROR: FULL TRACEBACK]")
        traceback.print_exc(file=sys.stderr) # <--- PRINTS THE FULL ERROR TRACE
        print("="*50 + "\n")

        # 2. EXIT THE PROGRAM IMMEDIATELY
        sys.exit(1)
        
        # Return a simple error message to the Orchestrator
        return f"ERROR: Internal schedule generation failed. Technical details logged to console."
