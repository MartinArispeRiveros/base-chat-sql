from pydantic import BaseModel


class AgentQueryRequest(BaseModel):
    question: str
