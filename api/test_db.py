import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Get the value from the .env file
db_url = os.getenv("DATABASE_URL")

try:
    # Pass the actual variable, not the string name
    conn = psycopg2.connect(db_url) 
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
    print(f"Check if your DATABASE_URL in .env starts with 'postgres://' or 'postgresql://'")