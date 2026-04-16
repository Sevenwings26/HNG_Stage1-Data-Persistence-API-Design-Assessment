import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect("DATABASE_URL")
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")