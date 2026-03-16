import os
import time
import schedule
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize connection
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Supabase URL or Key not found in environment variables.")

supabase: Client = create_client(url, key)

def db_automation_task():
    """
    This is the core task the agent executes.
    Example: Add a timestamped log entry to the database every minute.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    agent_message = f"Automated Agent Check-in at {timestamp}"
    
    print(f"[{timestamp}] Agent waking up... executing DB task.")
    
    try:
        # 1. Action: Insert a new record
        response = supabase.table("items").insert({
            "name": "Auto-Agent Log", 
            "description": agent_message
        }).execute()
        
        print(f"[{timestamp}] Success! Inserted record id: {response.data[0]['id']}")
        
        # 2. Action: You could also add logic to clean up old records here
        # Example: supabase.table("items").delete().eq("name", "Auto-Agent Log").execute()
        
    except Exception as e:
         print(f"[{timestamp}] Agent encountered an error: {e}")

# --- Agent Configuration ---

print("Starting Database Automation Agent...")
print("The agent will execute its task every 1 minute.")
print("Press Ctrl+C to stop the agent.")

# Schedule the task to run every 1 minute
schedule.every(1).minutes.do(db_automation_task)

# Keep the script running constantly to check the schedule
if __name__ == "__main__":
    # Run once immediately on startup
    db_automation_task()
    
    # Enter the infinite loop to wait for the next scheduled time
    while True:
        schedule.run_pending()
        time.sleep(1)
