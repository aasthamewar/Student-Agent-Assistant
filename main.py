# # main.py

# from google import genai
# import time
# import json 
# from agents.orchestrator_agent import run_orchestrator 


# # --- Client Initialization ---
# client = genai.Client()

# # NOTE: These functions should ideally be moved entirely into a dedicated
# # 'scheduler_agent.py' file once that agent is fully built.
# def generate_study_plan(summary_text: str) -> str:
#     """Generates a 1-week study plan based on a document summary. (Now a Scheduler Task)"""
#     # NOTE: Function definition is kept but execution is commented out for clean transition
#     return "This function's logic is now delegated by the Orchestrator."

# def create_schedule(task_details: dict) -> str:
#     """Generates a study/work schedule based on extracted task details. (Now a Scheduler Task)"""
#     # NOTE: Function definition is kept but execution is commented out for clean transition
#     return "This function's logic is now delegated by the Orchestrator."

# def run_test(test_name: str, user_prompt: str, file_path: str = None):
#     """Utility function to run and print the orchestrator result."""
#     print("\n" + "="*50)
#     print(f"🚀 Running Test: {test_name}")
#     print(f"User Request: {user_prompt}")
#     print(f"File Path: {file_path}")
#     print("="*50)

#     # Run the orchestrator with the request
#     final_result = run_orchestrator(user_prompt, file_path)

#     print("\n" + "="*50)
#     print(f"✨ ORCHESTRATOR FINAL RESULT ({test_name})")
#     print("="*50)
#     print(final_result)
#     print("\n")

# # --- Main Execution Block ---

# if __name__ == "__main__":
    
#     # --- Configuration ---
#     # The file path is now managed by the Orchestrator's instructions
#     # IMPORTANT: Ensure this file exists in your 'uploads' folder for the demo to run!
#     input_file_path = "uploads/CN_PAPER.pdf"
    
#     # Example 1: A complex request requiring multiple steps
#     user_request = (
#         f"I've uploaded a new assignment located at '{input_file_path}'. "
#         "I need you to extract the details, save the task, show me all active tasks, "
#         "**AND THEN CREATE AND SAVE A DETAILED 5-DAY STUDY PLAN for this new assignment.**" 
#         # The bolded text explicitly triggers the schedule_task_tool
#     )
    
#     print("=========================================================")
#     print("🚀 Running Orchestrator Agent Demo")
#     print(f"User Request: {user_request}")
#     print("=========================================================")
    
#     # Call the Orchestrator
#     # The Orchestrator will now orchestrate the calls to the necessary tools
#     final_output = run_orchestrator(user_request, input_file_path)
    
#     print("\n\n=========================================================")
#     print("✨ ORCHESTRATOR FINAL RESULT")
#     print("=========================================================")
#     print(final_output)

# main.py

from google import genai
from agents.orchestrator_agent import run_orchestrator 
import os
import threading,time
# from database.memory_service import get_due_reminders

# --- Client Initialization (Used by the Orchestrator, good to keep here) ---
client = genai.Client()

# --- NEW GLOBAL FLAG ---
PAUSE_DAEMON_CHECK = False 
# -----------------------

# --- Utility Function ---
def run_test(test_name: str, user_prompt: str, file_path: str = None):
    """Utility function to run and print the orchestrator result."""
    print("\n" + "="*75)
    print(f"🚀 Running Test: {test_name}")
    print(f"User Request: {user_prompt}")
    # print(f"File Path: {file_path}")
    print("="*75)

    # Run the orchestrator with the request
    final_result = run_orchestrator(user_prompt, file_path)

    print("\n" + "="*75)
    print(f"✨ ORCHESTRATOR FINAL RESULT ({test_name})")
    print("="*75)
    print(final_result)
    print("\n")



def run_interactive_cli():
    """
    Starts an interactive command-line interface and the reminder daemon.
    Includes logic to pause the reminder daemon when a short-term reminder 
    is set, preventing instant alerts.
    """
    # print("="*60)
    # print("🧠 Student Agent CLI - Orchestrator Ready")
    # print("="*60)
    # print("Type your request. Examples:")
    # print("  1. I uploaded 'CN_PAPER.pdf'. Extract the details and create a schedule.")
    # print("  2. Give me a progress update for my upcoming deadlines.")
    # print("  3. I finished Task ID 5. Mark it as complete.")
    # print("  4. Type 'exit' or 'quit' to close the CLI.")
    # print("-" * 60)
    
    # # --- START THE DAEMON THREAD ---
    # daemon_thread = threading.Thread(target=reminder_daemon, daemon=True)
    # daemon_thread.start()

    # --- Main Interaction Loop ---
    while True:
        # Define global flag logic here to ensure access
        global PAUSE_DAEMON_CHECK 
        should_pause = False
        duration = 0
        
        try:
            # Get user input
            user_input = input("\nAgent CLI > ")

            if user_input.lower() in ['exit', 'quit']:
                print("\nShutting down Agent CLI. Goodbye!")
                break
            if not user_input.strip():
                continue
            
            # --- DYNAMIC PAUSE LOGIC ---
            # Check if the user is setting a new, short-term reminder
            if "reminder" in user_input.lower() and ("second" in user_input.lower() or "minute" in user_input.lower()):
                
                # Simple extraction of the duration number
                for word in user_input.split():
                    if word.isdigit():
                        duration = int(word)
                        break
                
                if duration > 0:
                    PAUSE_DAEMON_CHECK = True # PAUSE THE CHECKER
                    should_pause = True
                    print(f"[ORCHESTRATOR] Daemon paused for {duration} seconds to ensure accurate timing.")


            # --- File Path Extraction (as it was) ---
            file_path = None
            if "uploaded" in user_input.lower() or "file" in user_input.lower():
                # words = user_input.split()
                words = user_input.replace("'", " ").replace('"', " ").split()
                for word in words:
                    if '.' in word:
                        # potential_path = word.strip("'\"")
                        potential_name = word.strip()
                        # if os.path.exists(potential_path):
                        #     file_path = potential_path
                        #     break
                        # elif os.path.exists(f"uploads/{potential_path}"):
                        #     file_path = f"uploads/{potential_path}"
                        #     break
                        # 1. Check if the name exists exactly as provided (e.g., if user types 'uploads/foo.pdf')
                        if os.path.exists(potential_name):
                            file_path = potential_name
                            break
                            
                        # 2. Check the common 'uploads' location (most common case)
                        uploads_path = os.path.join("uploads", potential_name)
                        if os.path.exists(uploads_path):
                            file_path = uploads_path
                            break
            # Check the final result of the extraction and inform the user
            if file_path:
                print(f"[CLI] File path successfully identified: {file_path}")
            elif "uploaded" in user_input.lower() or "file" in user_input.lower():
                print(f"[CLI] WARNING: File path could not be found based on input. Passing None to Orchestrator.")
                # The Orchestrator will now receive None, which should lead to an error from the tool, but at least we know *why* here.
                            
            # --- Call the Orchestrator ---
            print("\n[ORCHESTRATOR] Processing request...")
            final_output = run_orchestrator(user_input, file_path)
            
            # --- Resume Daemon if necessary (After Orchestrator completes) ---
            if should_pause:
                # Wait for the calculated duration plus a 5-second buffer for execution time
                sleep_time = duration + 5
                print(f"[ORCHESTRATOR] Resuming daemon in {sleep_time} seconds...")
                time.sleep(sleep_time) 
                PAUSE_DAEMON_CHECK = False
                print("\n[ORCHESTRATOR] Daemon resumed.")
            
            # --- Display Final Result ---
            print("\n" + "="*60)
            print("✨ AGENT RESPONSE")
            print("="*60)
            print(final_output)
            print("-" * 60)
            
        except Exception as e:
            print(f"\n[CRITICAL ERROR] An unexpected error occurred: {e}")
            print("Please try again.")
            
            # Ensure the daemon unpauses even on error
            if should_pause:
                PAUSE_DAEMON_CHECK = False




# --- Main Execution Block ---

if __name__ == "__main__":
    
    # --- Configuration ---
    # IMPORTANT: Ensure this file exists in your 'uploads' folder for Test 1!
    PAPER_PATH = "software.pdf" 
    
    # =========================================================
    # 1. TEST: FULL EXTRACTION & SCHEDULING WORKFLOW
    # -> Tests: extract_assignment_data_tool, schedule_task_tool, retrieve_active_tasks
    # -> Requires: The file at CN_PAPER_PATH
    # =========================================================
    test_1_request = (
        f"I've uploaded a new assignment located at '{PAPER_PATH}'. "
        "Extract the details, save the task, and create and save a detailed 5-day study schedule for it."
    )
    
    # UNCOMMENT the line below to run this test
    run_test("1. Extraction and Scheduling", test_1_request, PAPER_PATH)
    
    
    # =========================================================
    # 2. TEST: PROGRESS & REMINDER AGENT (Retrieves schedule and gives reminder)
    # -> Tests: get_progress_report_tool
    # -> Requires: Tasks (like Task ID 2, 3, 4) to be in the database
    # =========================================================
    test_2_request = (
        "Give me a detailed progress update for my upcoming deadlines and suggest my next study step."
    )
    
    # UNCOMMENT the line below to run this test
    run_test("2. Progress and Reminder", test_2_request, None)
    
    
    # =========================================================
    # 3. TEST: TASK COMPLETION AGENT (Marks a task as done)
    # -> Tests: complete_task_tool
    # -> Requires: A specific, active Task ID (e.g., Task ID 4) to be in the database
    # =========================================================
    TASK_ID_TO_COMPLETE = 4 
    test_3_request = (
        f"I finished Task ID {TASK_ID_TO_COMPLETE}. Mark it as complete."
    )
    
    # UNCOMMENT the line below to run this test
    run_test("3. Task Completion", test_3_request, None)

    
    # =========================================================
    # 4. TEST: SIMPLE RETRIEVAL (Checks that tasks are still present)
    # -> Tests: retrieve_active_tasks
    # =========================================================
    test_4_request = (
        "Just show me all my active assignments."
    )
    
    # UNCOMMENT the line below to run this test
    run_test("4. Simple Retrieval", test_4_request, None)

    
    print("\n--- Testing Complete ---")
    print("Uncomment the 'run_test(...)' lines to execute specific agent workflows.")

    if input("Enter 'run' to execute the uncommented tests, or press Enter to exit: ") == 'run':
        
        # --- ADD THESE CONDITIONAL CALLS ---
        if 'test_1_request' in locals() and '#' not in globals().get('test_1_request', ''):
            run_test("2. Progress and Reminder", test_2_request, None) # <-- UNCOMMENTED
        else:
         print("Test run cancelled.")

    # Ensure the database is initialized (if not already done via import)
    try:
        from database.memory_service import initialize_database
        initialize_database()
    except ImportError:
        print("Warning: Could not import initialize_database. Ensure your memory_service is set up.")
        
    run_interactive_cli()