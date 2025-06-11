from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.conversation import Conversation

class ConversationService:
    def __init__(self, db: Session):
        self.db = db
    
    async def save_conversation(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        query_id: int = None
    ) -> Conversation:
        """Save a conversation exchange"""
        conversation = Conversation(
            session_id=session_id,
            user_message=user_message,
            assistant_response=assistant_response,
            query_id=query_id
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: int = 20
    ) -> List[Dict]:
        """Get conversation history for a session"""
        conversations = (
            self.db.query(Conversation)
            .filter(Conversation.session_id == session_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                "id": c.id,
                "user_message": c.user_message,
                "assistant_response": c.assistant_response,
                "query_id": c.query_id,
                "created_at": c.created_at
            }
            for c in reversed(conversations)  # Return in chronological order
        ]
