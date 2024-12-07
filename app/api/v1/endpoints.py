# general imports
import json
from fastapi import APIRouter, File, HTTPException, Depends, UploadFile
from app.crud.vector_store_crud import create_or_update_vector_store
from app.models.agent_sql_query_request import AgentQueryRequest
from app.services.sql_agent_service import AgentLLMService
from app.utils.config import load_config
from requests import Session


# SQL imports
from app.models.sql_query_request import SQLQueryRequest
from app.models.sql_query_response import SQLQueryResponse
from app.services.sql_llm_service import generate_sql_query, get_sql_results_summary
from app.services.db_service import execute_sql_query, is_sql_query_safe
from database.connection import get_database_schema, get_db
from database.connection import SessionLocal
from sqlalchemy import text

router = APIRouter()
config = load_config()


@router.get("/db/schema/")
def get_db_schema(db: Session = Depends(get_db)):
    schema_dict = json.loads(get_database_schema())
    return {"schema": schema_dict}

@router.post("/run_sql/")
def run_sql(query: str):
    try:
        query = query.strip().rstrip(';')
        session = SessionLocal()
        result = session.execute(text(query))

        rows = result.fetchall()

        if rows:
            data = []
            for row in rows:
                data.append(dict(zip(result.keys(), row)))

            return {"results": data}
        else:
            return {"error": "The query returned an empty result"}

    except Exception as e:
        return {"error": str(e)} 

    finally:
        session.close()


@router.post("/ask_to_database/", response_model=SQLQueryResponse) 
async def generate_sql(request: SQLQueryRequest, db: Session = Depends(get_db)):
    sql_query = await generate_sql_query(request.user_query, db, model=request.model)
    print('sql_query', sql_query)

    if not is_sql_query_safe(sql_query):
        raise HTTPException(status_code=400, detail="Generated SQL query is unsafe.")
    results = execute_sql_query(sql_query, db)
    
    print('results', results)
    
    human_readable_response = await get_sql_results_summary(results, request.user_query, request.model)
    
    return SQLQueryResponse(results=human_readable_response)


@router.post("/ask_to_database_with_agent")
def query(request: AgentQueryRequest):
    agent = AgentLLMService()
    question = request.question
    try:
        sql_response = agent.process_query_with_sql_agent(question)
        print("AGENT SQL RESPONSE", sql_response)
        human_response = agent.humanize_response("Consulta generada automáticamente", sql_response)
        return {"question": question, "response": human_response}
    except Exception as e:
        print(f"Error al procesar la consulta: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar la consulta.")



    