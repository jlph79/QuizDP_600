import psycopg2
import json
import os

def safe_json_loads(data):
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return f"Raw data (JSON parse failed): {data}"
    return None

def check_user_progress(user_id=4):
    db_url = "postgresql://postgres:AkxzbtDGKXDcLzsSEPwEdgUVxiCRDwXj@viaduct.proxy.rlwy.net:20628/railway"

    print(f"Attempting to connect with URL: {db_url}")

    try:
        conn = psycopg2.connect(db_url)
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_progress WHERE user_id = %s", (user_id,))
        rows = cursor.fetchall()
        
        print("\nUser Progress Data:")
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"User ID: {row[1]}")
            print(f"Current Index: {row[2]}")
            print(f"Score: {safe_json_loads(row[3])}")
            print(f"User Answers: {safe_json_loads(row[4])}")
            print(f"Mode: {row[5]}")
            print(f"Practiced Questions: {safe_json_loads(row[6])}")
            print(f"Incorrect Answers: {safe_json_loads(row[7])}")
            print(f"Review List: {safe_json_loads(row[8])}")
            print(f"Algorithm Performance: {safe_json_loads(row[8])}")
            print("---")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    check_user_progress()