import json
from typing import List, Dict
from database.connection import get_db, get_db_name
from sqlalchemy import text
from sqlalchemy.orm import Session


def execute_sql_query(query: str, db: Session) -> List[Dict]:
    try:
        query = query.strip().rstrip(';')
      
        if not is_sql_query_safe(query):
            raise Exception("SQL query is unsafe")

        result = db.execute(text(query))
        rows = result.fetchall()

        if rows:
            data = []
            for row in rows:
                data.append(dict(zip(result.keys(), row)))
            return data
        else:
            return []

    except Exception as e:
        print(f"Error: {e}")
        return []
    
    
def is_sql_query_safe(sql_query):
    prohibited_phrases = [
        "DROP", "DELETE", "INSERT", "ALTER", "TRUNCATE",
        "EXEC", "--", "/*", "*/", "@@", "@", "SHUTDOWN",
        "GRANT", "REVOKE"
    ]
    for phrase in prohibited_phrases:
        if phrase.lower() in sql_query.lower():
            return False
    return True

