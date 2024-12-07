from pydantic import BaseModel
class SQLQueryResponse(BaseModel): 
    results: str