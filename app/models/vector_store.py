from sqlalchemy import Column, Integer, String
from database.connection import Base

class VectorStore(Base):
    __tablename__ = "vector_stores"
    
    id = Column(Integer, primary_key=True, index=True)
    filepath = Column(String, nullable=False)
