from pydantic import BaseModel
class SQLQueryRequest(BaseModel):
    user_query: str
    model: str