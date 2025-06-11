# Session Management Models
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Session(Base):
    """
    Session model for context management
    Allows users to work with multiple datasets without explicitly specifying dataset_id
    """
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=True)  # Future: user management
    default_dataset_id = Column(Integer, nullable=True)  # References datasets.id
    context_datasets = Column(JSON, nullable=True)  # Array of dataset info with metadata
    settings = Column(JSON, nullable=True)  # Session-specific settings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Session(id={self.id}, name='{self.name}', active={self.is_active})>"


class Workspace(Base):
    """
    Workspace model for grouping related datasets
    Enables advanced analytics across multiple datasets
    """
    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String(255), nullable=True)  # Future: user management
    settings = Column(JSON, nullable=True)  # Workspace-specific settings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Workspace(id={self.id}, name='{self.name}', active={self.is_active})>"


class WorkspaceDataset(Base):
    """
    Association table for workspace-dataset relationships
    Stores metadata about how each dataset is used in the workspace
    """
    __tablename__ = "workspace_datasets"

    workspace_id = Column(UUID(as_uuid=True), primary_key=True)  # References workspaces.id
    dataset_id = Column(Integer, primary_key=True)  # References datasets.id
    role = Column(String(50), default="primary")  # 'primary', 'secondary', 'reference'
    tags = Column(ARRAY(String), nullable=True)  # Tags for smart dataset selection
    priority = Column(Integer, default=0)  # Priority for auto-selection
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<WorkspaceDataset(workspace={self.workspace_id}, dataset={self.dataset_id}, role={self.role})>"


class QueryContext(Base):
    """
    Tracks context information for each query
    Enables analytics on how datasets are selected and used
    """
    __tablename__ = "query_contexts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_id = Column(Integer, nullable=True)  # References queries.id
    session_id = Column(UUID(as_uuid=True), nullable=True)  # References sessions.id
    workspace_id = Column(UUID(as_uuid=True), nullable=True)  # References workspaces.id
    selected_datasets = Column(ARRAY(Integer), nullable=True)  # Auto-selected dataset IDs
    selection_strategy = Column(String(50), nullable=True)  # How datasets were selected
    context_metadata = Column(JSON, nullable=True)  # Additional context information
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<QueryContext(id={self.id}, strategy={self.selection_strategy})>"
