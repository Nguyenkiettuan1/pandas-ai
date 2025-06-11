from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Query(Base):
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    sql_query = Column(Text)
    result = Column(Text)
    execution_time = Column(Integer)  # in milliseconds
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with dataset
    dataset = relationship("Dataset", back_populates="queries")
