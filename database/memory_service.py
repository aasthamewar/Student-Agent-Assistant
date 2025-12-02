import sqlite3
from sqlite3 import Error
from datetime import datetime, timedelta

DATABASE_FILE = 'student_agent_memory.db'

def create_connection():
    """Create a database connection to the SQLite database"""
    conn = None
    try:
        # This will create the file if it doesn't exist, or connect if it does
        conn = sqlite3.connect(DATABASE_FILE)
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def close_connection(conn):
    """Close the database connection."""
    if conn:
        conn.close()

def create_tables(conn):
    """Create the necessary database tables."""

    #--- 1. Tasks Table ---
    # Stores assignment details (used by scheduler & Progress Agents)
    sql_create_tasks_table = """ CREATE TABLE IF NOT EXISTS tasks (
                                    id INTEGER PRIMARY KEY,
                                    subject TEXT NOT NULL,
                                    task_type TEXT,
                                    description_snippet TEXT,
                                    deadline TEXT NOT NULL,
                                    priority TEXT,
                                    word_count_or_length TEXT,
                                    is_completed INTEGER DEFAULT 0,
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                ); """
    
    # --- 2. Schedules Table ---
    # Stores the generated study plans/schedules (used by Progress Agent)
    sql_create_schedules_table = """ CREATE TABLE IF NOT EXISTS schedules (
                                        id INTEGER PRIMARY KEY,
                                        task_id INTEGER NOT NULL,
                                        schedule_text TEXT NOT NULL,
                                        date_generated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                        FOREIGN KEY (task_id) REFERENCES tasks (id)
                                    ); """
    try:
        cursor = conn.cursor()
        cursor.execute(sql_create_tasks_table)
        cursor.execute(sql_create_schedules_table)
        conn.commit()
    except Error as e:
        print(f"Error creating tables: {e}")

    # ---- 3.Reminders Table ----
    sql_create_reminders_table = """ CREATE TABLE IF NOT EXISTS reminders (
                                        id INTEGER PRIMARY KEY,
                                        reminder_text TEXT NOT NULL,
                                        target_datetime TEXT NOT NULL,
                                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                    ); """
    try:
        cursor = conn.cursor()
        cursor.execute(sql_create_tasks_table)
        cursor.execute(sql_create_schedules_table)
        cursor.execute(sql_create_reminders_table)
    except Error as e:
        print(f"Error creating tables: {e}")

# # Add the function to insert a new reminder:
# def insert_reminder(reminder_text: str, target_datetime: str) -> int:
#     """Inserts a new reminder into the reminders table."""
#     conn = create_connection()
#     if conn is None:
#         return -1

#     sql = ''' INSERT INTO reminders(reminder_text, target_datetime)
#               VALUES(?, ?) '''

#     try:
#         cursor = conn.cursor()
#         cursor.execute(sql, (reminder_text, target_datetime))
#         conn.commit()
#         return cursor.lastrowid
#     except Error as e:
#         print(f"Error inserting reminder: {e}")
#         return -1
#     finally:
#         close_connection(conn)

# --- Initialize the database when the module is imported ---
def initialize_database():
    """Initializes the connection and creates tables if they don't exist."""
    conn = create_connection()
    if conn:
        create_tables(conn)
        close_connection(conn)

initialize_database()

#This function will be called immediately after the Task Extractor successfully returns the structured JSON data.

def insert_task(task_data: dict)-> int:
    """Insert a new task into tasks table."""
    conn = create_connection()
    if conn  is None:
        return -1
    
    sql = ''' INSERT INTO tasks(subject, task_type,        description_snippet, deadline, priority,             word_count_or_length)
              VALUES(?, ?, ?, ?, ?, ?) '''
    
    try:
        cursor = conn.cursor()
        deadline_value = task_data.get('deadline')

        if not deadline_value or deadline_value.lower().strip() in ['none', 'null', 'n/a', 'missing', '']:
            default_deadline = datetime.now() + timedelta(days=7)
            deadline_value = default_deadline.strftime("%Y-%m-%d %H:%M")
            print(f"[DB SERVICE] WARNING: Deadline missing on insert. Using default: {deadline_value}")
        # Use .get() with a default value to safely handle potentially missing keys
        data = (
            task_data.get('subject', 'N/A'),
            task_data.get('task_type', 'N/A'),
            task_data.get('description_snippet', 'No snippet'),
            deadline_value, # Deadline is required (per JSON schema)
            task_data.get('priority', 'Medium'),
            task_data.get('word_count_or_length', 'N/A')
        )
        cursor.execute(sql, data)
        conn.commit()
        return cursor.lastrowid # Returns the ID of the newly inserted task
    except Error as e:
        print(f"Error inserting task: {e}")
        return -1
    finally:
        close_connection(conn)

# These are used by the Scheduler Agent to check for conflicts and save the new plan.

def get_all_active_tasks():
    """Retrieves all tasks that are not marked as completed."""
    conn = create_connection()
    if conn is None:
        return []
    
    sql = "SELECT * FROM tasks WHERE is_completed = 0 ORDER BY deadline ASC"

    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        # Fetch all results and return them as a list of dictionaries
        rows = cursor.fetchall()
        
        # Get column names to create dictionary keys
        cols = [column[0] for column in cursor.description]
        return [dict(zip(cols, row)) for row in rows]
        
    except Error as e:
        print(f"Error retrieving tasks: {e}")
        return []
    finally:
        close_connection(conn)

def insert_schedule(task_id: int, schedule_text: str):
    """Inserts a generated schedule linked to a specific task ID."""
    conn = create_connection()
    if conn is None:
        return False
    
    sql = ''' INSERT INTO schedules(task_id, schedule_text)
              VALUES(?, ?) '''
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (task_id, schedule_text))
        conn.commit()
        return True
    except Error as e:
        print(f"Error inserting schedule: {e}")
        return False
    finally:
        close_connection(conn)

def get_schedule_by_task_id(task_id: int)->str:
    """Retrieves the schedule text for a specific task ID"""
    conn = create_connection()
    if conn is None:
        return "Error: Could not connect to database."
    
    sql = "SELECT schedule_text FROM schedules WHERE task_id = ?"

    try:
        cursor = conn.cursor()
        cursor.execute(sql,(task_id,))
        row = cursor.fetchone()

        return row[0] if row else "No schedule found for this task."
    except Error as e:
        print(f"Error retrieving schedule: {e}")
        return "Error retrieving schedule from database."
    finally:
        close_connection(conn)

def mark_task_complete(task_id: int) -> bool:
    """Marks a specific task as completed in the tasks table."""
    conn = create_connection()
    if conn is None:
        return False
        
    sql = ''' UPDATE tasks
              SET is_completed = 1 
              WHERE id = ?'''
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (task_id,))
        conn.commit()
        return cursor.rowcount > 0 # Returns True if a row was updated
        
    except Error as e:
        print(f"Error marking task complete: {e}")
        return False
    finally:
        close_connection(conn)

# def get_due_reminders():
#     """Retrieves and processes all reminders whose target_datetime is now or in the past."""
#     conn = create_connection()
#     if conn is None:
#         return []

#     # 1. Get current time for comparison
#     current_time = datetime.now()
#     due_reminders_to_fire = []
    
#     # Select ALL reminders (we will filter in Python for reliability)
#     sql_select_all = "SELECT id, reminder_text, target_datetime FROM reminders"

#     try:
#         cursor = conn.cursor()
#         cursor.execute(sql_select_all)
#         rows = cursor.fetchall()
        
#         # 2. Loop through all reminders and check for due status
#         for row in rows:
#             reminder_id, reminder_text, target_datetime_str = row
            
#             # Convert the stored string back into a Python datetime object
#             # This is the most critical step for reliable comparison
#             try:
#                 target_time = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
                
#                 # Check if the target time is less than or equal to the current time
#                 if target_time <= current_time:
#                     due_reminders_to_fire.append({
#                         'id': reminder_id, 
#                         'reminder_text': reminder_text
#                     })
#             except ValueError:
#                 # Handle cases where the datetime string format was wrong (e.g., from an old test)
#                 print(f"[ERROR] Invalid datetime format found for Reminder ID {reminder_id}: {target_datetime_str}")
                
#         # 3. Process and delete due reminders
#         if due_reminders_to_fire:
#             due_ids = [str(r['id']) for r in due_reminders_to_fire]
#             delete_sql = f"DELETE FROM reminders WHERE id IN ({','.join(due_ids)})"
#             cursor.execute(delete_sql)
#             conn.commit()
            
#         return due_reminders_to_fire

#     except Error as e:
#         print(f"Error in get_due_reminders: {e}")
#         return []
#     finally:
#         close_connection(conn)
