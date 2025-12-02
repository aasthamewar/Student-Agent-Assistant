from google import genai
from google.genai import types
from tools import orchestrator_tools
import json
import time
import logging # Import logging to handle potential warnings cleanly
# Configure logging to suppress the frequent 'non-text parts' warning
# NOTE: This is optional but makes the console output much cleaner.
logging.getLogger("google_genai.types").setLevel(logging.ERROR)


client = genai.Client()

# Define the list of tools the orchestrator can call
ORCHESTRATOR_TOOLS = [
    orchestrator_tools.summarize_document_tool,
    orchestrator_tools.extract_assignment_data_tool,
    orchestrator_tools.retrieve_active_tasks,
    orchestrator_tools.schedule_task_tool,
    orchestrator_tools.get_progress_report_tool,
    orchestrator_tools.complete_task_tool,
    orchestrator_tools.generate_practice_worksheet,
    
]

def run_orchestrator(user_prompt: str, file_path: str) -> str:
    """
    The main loop for the Orchestrator Agent. It uses Function Calling
    to determine the necessary sequence of actions and iteratively calls the model.
    """

    # current_time_str = datetime.now().strftime("%A, %B %d, %Y, %H:%M:%S")
    
    # --- 1. Initial Prompt Setup ---
    system_instruction = (
        "You are the Orchestrator Agent. Your task is to analyze the user's request "
        "and determine the exact sequence of tool calls needed to fulfill it. "
        "The file involved is located at: "
        f"'{file_path}'. Always use this file path in your tool calls."
        "You MUST first call any necessary tools, and then provide a final summary answer."

        "CRITICAL RULE: When 'extract_assignment_data_tool' is called, its result will contain the 'task_id'. "
        "You MUST parse this 'task_id' and the full task details from the output "
        "and use them as arguments for the 'schedule_task_tool' in the subsequent step."
        
       
    )
    
    # Start the conversation history with only the user prompt.
    history = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_prompt)]
        )
    ]

    max_steps = 5 # Limit the number of steps to prevent infinite loops

    for step in range(max_steps):
        # print(f"\n[ORCHESTRATOR] STEP {step + 1}: Asking Gemini for next action...")

        # --- 2. Call the Model with Tools and System Instruction ---
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=history,
            config=types.GenerateContentConfig(
                tools=ORCHESTRATOR_TOOLS,
                system_instruction=system_instruction
            )
        )
        
        # --- Get Candidate Content for consistent access ---
        candidate_content = response.candidates[0].content
        
        # --- 3. Check for Function Calls ---
        if response.function_calls:
            # We process the first function call only for simplicity
            function_call = response.function_calls[0]
            func_name = function_call.name
            func_args = dict(function_call.args)

            print(f"[ORCHESTRATOR] Delegating task to tool: {func_name} with args: {func_args}")

            # Use getattr() to find and execute the actual Python function
            tool_function = getattr(orchestrator_tools, func_name, None) # Corrected to one call

            if tool_function:
                # Execute the tool function
                tool_output = tool_function(**func_args)

                # =========================================================
                # === CRITICAL FIX: Intercept Extraction Tool Output ===
                # =========================================================
                if func_name == 'extract_assignment_data_tool':
                    # The tool_output is a dictionary (from task_extractor_tool.py)
                    
                    if "error" in tool_output:
                        # Case 1: The extractor tool failed (e.g., file not found, API error)
                        return f"ERROR: Assignment data extraction failed: {tool_output['error']}"

                    # Note: memory_service.insert_task returns the new task_id (integer)
                    # If the database insertion failed (NOT NULL error), it returns -1.
                    if isinstance(tool_output, int) and tool_output == -1:
                        # Case 2: The database insertion failed (This is the source of the persistent crash)
                        return "ERROR: Failed to save task data to the database due to missing required fields (e.g., deadline). Check database constraints."

                    # Case 3: SUCCESS. The output is the task_id. We must now pass the ID and the full data to the scheduler.
                    task_id = tool_output
                    
                    # You MUST get the full task data back from the DB to pass to the Scheduler.
                    # Since that logic is missing, we'll force the next call:
                    
                    # Construct a function response that FORCES the LLM to schedule next.
                    tool_output_for_llm = {
                        "task_id": task_id,
                        "status": "Task successfully saved to database. Proceed to scheduling."
                    }
                    tool_output = tool_output_for_llm # Use this for the model response below

                print(f"[ORCHESTRATOR] Tool output received (length: {len(tool_output)} chars).")

                # Append both the model's call and the function's result to the history
                history.append(candidate_content) # The model's call is already structured
                history.append(types.Content(
                    role="user", # The tool's output is context for the next user turn
                    parts=[ 
                        types.Part.from_function_response(
                            name=func_name,
                            response={"result": tool_output}
                        )
                    ]
                ))
                # Continue the loop to send the tool output back to the model
                continue 
            else:
                return f"Error: Tool '{func_name}' not found."

        # --- 4. Check for Final Text Response (Only if no tool call was made) ---
        # We check the content parts directly to avoid the `.text` warning
        elif response.text:
            print("[ORCHESTRATOR] Received final text response.")
            # Use the .text shortcut, now that we've checked for function calls
            # The warning is suppressed by the logging configuration above.
            return response.text
        
        else:
            # Check for block reasons if no text or function call is present
            finish_reason = response.candidates[0].finish_reason.name
            if finish_reason == "SAFETY":
                 return "The response was blocked due to safety settings."
            elif finish_reason == "RECITATION":
                 return "The response was blocked due to potential data recitation."
            return f"Orchestrator failed to produce an output or call a tool. Finish reason: {finish_reason}"

    return "Orchestrator reached maximum steps without completing the task."