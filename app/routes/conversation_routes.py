from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.core.database import get_db
from app.services.conversation_service import ConversationService
from app.services.query_service import QueryService
from app.schemas.conversation_schemas import ConversationResponse
from app.schemas.query_schemas import QueryRequest, QueryResponse

# Create router for conversation endpoints
conversation_router = APIRouter(prefix="/conversations", tags=["Conversations"])

@conversation_router.get("/{session_id}", response_model=List[ConversationResponse])
async def get_conversation_history(
    session_id: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get conversation history for a session"""
    try:
        service = ConversationService(db)
        return await service.get_conversation_history(session_id=session_id, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@conversation_router.post("/chat/", response_model=QueryResponse)
async def chat(
    query_request: QueryRequest,
    db: Session = Depends(get_db)
):
    """Chat endpoint with conversation context"""
    try:
        # Generate session ID if not provided
        session_id = query_request.session_id or str(uuid.uuid4())
        
        # Process the query
        query_service = QueryService(db)
        result = await query_service.process_natural_language_query(
            question=query_request.question,
            dataset_id=query_request.dataset_id,
            session_id=session_id
        )
        
        # Save conversation
        conversation_service = ConversationService(db)
        await conversation_service.save_conversation(
            session_id=session_id,
            user_message=query_request.question,
            assistant_response=str(result['result']),
            query_id=result['query_id']
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
