
# tools/task_extractor_tool.py

from google import genai
from google.genai import types
from google.genai.errors import ClientError # <-- NEW IMPORT
import json
import os
from datetime import datetime, timedelta
import time
# print(os.environ.get('GEMINI_API_KEY'))
client = genai.Client()
MAX_RETRIES = 5

def extract_assignment_details(file_path: str) -> dict:

    """
    Uploads a file (PDF, image, text) and extracts structured assignment details, with Exponential Backoff for 429 errors.

    Args:

        file_path: Path to the input file (assignment details).

    Returns:

        A dictionary containing the extracted assignment details.

    """

    if not os.path.exists(file_path):

        return {"error": f"File not found at: {file_path}"}

    print(f"\n[Extraction Tool] Uploading file for analysis: {file_path}")

    # --- 1. Upload File ---
    # --- 1. Upload File ---
    assignment_file = None
    extracted_data = {}
    try:
        assignment_file = client.files.upload(file=file_path)

    except Exception as e:
        return {"error": f"Failed to upload file: {e}"}

    # --- 2. Define Extraction Prompt and Structure ---

    # We use JSON schema to force the model to return clean, structured data.

    json_schema = {

        "type": "object",

        "properties": {

            "deadline": {"type": "string", "description": "The date and time the assignment is due, in YYYY-MM-DD HH:MM format."},

            "task_type": {"type": "string", "description": "e.g., 'Essay', 'Presentation', 'Problem Set', 'Lab Report', 'Reading'"},

            "subject": {"type": "string", "description": "The course or topic the assignment belongs to, e.g., 'Calculus', 'Microeconomics'"},

            "priority": {"type": "string", "description": "One of: 'High', 'Medium', 'Low'. Based on deadline and difficulty."},

            "word_count_or_length": {"type": "string", "description": "Required length, e.g., '2000 words', '10 slides', 'Chapter 5'"},

            "description_snippet": {"type": "string", "description": "A very short (5-10 word) summary of the task."},

            
        },

        "required": ["deadline", "task_type", "subject", "priority"]

    }

    extraction_prompt = (

        "Analyze the provided document (which may be a PDF, image, or text) "

        "and extract the required assignment details into a perfect JSON object. "

        "Infer any missing information (like priority) based on the context."

    )
    # --- 3. Generate Content (JSON Extraction) ---

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[assignment_file, extraction_prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=json_schema
                )
            )
            
            # If successful, parse and break the retry loop
            extracted_data = json.loads(response.text)
            break # Success, exit the loop
            
        except ClientError as e:
            if e.status_code == 429 and attempt < MAX_RETRIES - 1:
                # Exponential Backoff: Wait 2^attempt seconds, max 16s
                wait_time = 2 ** attempt
                print(f"[EXTRACTION TOOL] Rate limit hit (429). Waiting {wait_time}s before retry ({attempt + 1}/{MAX_RETRIES}).")
                time.sleep(wait_time)
                continue # Retry
            else:
                # Unrecoverable ClientError or max retries reached
                extracted_data = {"error": f"API/Extraction failed on attempt {attempt+1}: {e}"}
                break # Exit loop
        
        except json.JSONDecodeError as e:
            # Handle case where the LLM returns text instead of valid JSON
            extracted_data = {"error": f"JSON parsing failed: {e}. Raw LLM output was likely invalid."}
            break # Exit loop
        
        except Exception as e:
            extracted_data = {"error": f"General Extraction failure: {e}"}
            break # Exit loop
            
    # --- 4. Clean up the uploaded file ---
    # ... (Cleanup logic remains the same) ...

    # ======================================================================
    # === 5. DEADLINE SAFEGUARD (Unchanged and still critical) ===
    # ======================================================================
    
    # ... (Safeguard logic remains the same) ...
    if 'error' not in extracted_data:
        deadline_str = extracted_data.get('deadline')
        
        # Check if deadline is missing, explicitly 'None', or just an empty string
        if not deadline_str or deadline_str.lower().strip() in ['none', 'null', 'n/a', 'missing', '']:
            # Set a default deadline 7 days from now (Use current time for precise fallback)
            current_time = datetime.now()
            default_deadline = current_time + timedelta(days=7)
            # Ensure the format matches the YYYY-MM-DD HH:MM expected by the database/schema
            deadline_str = default_deadline.strftime("%Y-%m-%d %H:%M") 
            
            # Update the task_data dictionary for the database
            extracted_data['deadline'] = deadline_str
            print(f"[Extraction Tool] WARNING: Deadline missing. Defaulting to {deadline_str}")

            
    return extracted_data

# The function to be imported
task_extractor_tool = extract_assignment_details