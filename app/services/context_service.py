# Context Management Service
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Union
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import logging

from app.core.response_handler import ResponseHandler, ResponseType
from app.models.context_models import Session as SessionModel, Workspace, WorkspaceDataset, QueryContext
from app.models.dataset import Dataset
from app.schemas.context_schemas import (
    SessionCreateRequest, SessionResponse, 
    WorkspaceCreateRequest, WorkspaceResponse,
    ContextDataset
)

logger = logging.getLogger(__name__)


class ContextService:
    """Service for managing sessions, workspaces, and query contexts"""

    def __init__(self, db: Session):
        self.db = db

    # Session Management
    async def create_session(self, request: SessionCreateRequest) -> Dict[str, Any]:
        """Create a new session with context information"""
        try:
            # Calculate expiration time
            expires_at = None
            if request.expires_in_hours:
                expires_at = datetime.utcnow() + timedelta(hours=request.expires_in_hours)

            # Validate default dataset if provided
            if request.default_dataset_id:
                dataset = self.db.query(Dataset).filter(Dataset.id == request.default_dataset_id).first()
                if not dataset:
                    return ResponseHandler.create_error_response(
                        error=f"Dataset {request.default_dataset_id} not found",
                        message="Default dataset not found",
                        response_type=ResponseType.VALIDATION_ERROR
                    )

            # Validate context datasets if provided
            if request.context_datasets:
                dataset_ids = [cd.id for cd in request.context_datasets]
                existing_datasets = self.db.query(Dataset).filter(Dataset.id.in_(dataset_ids)).all()
                existing_ids = {d.id for d in existing_datasets}
                missing_ids = set(dataset_ids) - existing_ids
                
                if missing_ids:
                    return ResponseHandler.create_error_response(
                        error=f"Datasets not found: {list(missing_ids)}",
                        message="Some context datasets not found",
                        response_type=ResponseType.VALIDATION_ERROR
                    )

            # Create session
            session = SessionModel(
                id=uuid4(),
                name=request.name,
                user_id=request.user_id,
                default_dataset_id=request.default_dataset_id,
                context_datasets=[cd.dict() for cd in request.context_datasets] if request.context_datasets else None,
                settings=request.settings,
                expires_at=expires_at
            )

            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            session_data = {
                "id": session.id,
                "name": session.name,
                "user_id": session.user_id,
                "default_dataset_id": session.default_dataset_id,
                "context_datasets": session.context_datasets,
                "settings": session.settings,
                "created_at": session.created_at,
                "expires_at": session.expires_at,
                "is_active": session.is_active
            }

            logger.info(f"Created session: {session.id} - {session.name}")

            return ResponseHandler.create_success_response(
                data=session_data,
                message="Session created successfully",
                response_type=ResponseType.GENERAL
            )

        except Exception as e:
            logger.error(f"Error creating session: {e}")
            self.db.rollback()
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to create session",
                response_type=ResponseType.GENERAL
            )

    async def get_session(self, session_id: Union[str, UUID]) -> Dict[str, Any]:
        """Get session information by ID"""
        try:
            session = self.db.query(SessionModel).filter(
                SessionModel.id == session_id,
                SessionModel.is_active == True
            ).first()

            if not session:
                return ResponseHandler.create_error_response(
                    error="Session not found",
                    message=f"No active session found with ID: {session_id}",
                    response_type=ResponseType.GENERAL
                )

            # Check if session is expired
            if session.expires_at and session.expires_at < datetime.utcnow():
                return ResponseHandler.create_error_response(
                    error="Session expired",
                    message="Session has expired",
                    response_type=ResponseType.GENERAL
                )

            session_data = {
                "id": session.id,
                "name": session.name,
                "user_id": session.user_id,
                "default_dataset_id": session.default_dataset_id,
                "context_datasets": session.context_datasets,
                "settings": session.settings,
                "created_at": session.created_at,
                "expires_at": session.expires_at,
                "is_active": session.is_active
            }

            return ResponseHandler.create_success_response(
                data=session_data,
                message="Session retrieved successfully",
                response_type=ResponseType.GENERAL
            )

        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to retrieve session",
                response_type=ResponseType.GENERAL
            )

    # Workspace Management
    async def create_workspace(self, request: WorkspaceCreateRequest) -> Dict[str, Any]:
        """Create a new workspace with dataset associations"""
        try:
            # Validate datasets if provided
            if request.datasets:
                dataset_ids = [d.id for d in request.datasets]
                existing_datasets = self.db.query(Dataset).filter(Dataset.id.in_(dataset_ids)).all()
                existing_ids = {d.id for d in existing_datasets}
                missing_ids = set(dataset_ids) - existing_ids
                
                if missing_ids:
                    return ResponseHandler.create_error_response(
                        error=f"Datasets not found: {list(missing_ids)}",
                        message="Some datasets not found",
                        response_type=ResponseType.VALIDATION_ERROR
                    )

            # Create workspace
            workspace = Workspace(
                id=uuid4(),
                name=request.name,
                description=request.description,
                user_id=request.user_id,
                settings=request.settings
            )

            self.db.add(workspace)
            self.db.flush()  # Get the workspace ID

            # Add dataset associations
            if request.datasets:
                for dataset_info in request.datasets:
                    workspace_dataset = WorkspaceDataset(
                        workspace_id=workspace.id,
                        dataset_id=dataset_info.id,
                        role=dataset_info.role,
                        tags=dataset_info.tags,
                        priority=dataset_info.priority
                    )
                    self.db.add(workspace_dataset)

            self.db.commit()
            self.db.refresh(workspace)

            workspace_data = {
                "id": workspace.id,
                "name": workspace.name,
                "description": workspace.description,
                "user_id": workspace.user_id,
                "settings": workspace.settings,
                "created_at": workspace.created_at,
                "updated_at": workspace.updated_at,
                "is_active": workspace.is_active
            }

            logger.info(f"Created workspace: {workspace.id} - {workspace.name}")

            return ResponseHandler.create_success_response(
                data=workspace_data,
                message="Workspace created successfully",
                response_type=ResponseType.GENERAL
            )

        except Exception as e:
            logger.error(f"Error creating workspace: {e}")
            self.db.rollback()
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to create workspace",
                response_type=ResponseType.GENERAL
            )

    async def get_workspace(self, workspace_id: Union[str, UUID]) -> Dict[str, Any]:
        """Get workspace information with associated datasets"""
        try:
            workspace = self.db.query(Workspace).filter(
                Workspace.id == workspace_id,
                Workspace.is_active == True
            ).first()

            if not workspace:
                return ResponseHandler.create_error_response(
                    error="Workspace not found",
                    message=f"No active workspace found with ID: {workspace_id}",
                    response_type=ResponseType.GENERAL
                )

            # Get associated datasets
            workspace_datasets = self.db.query(WorkspaceDataset).filter(
                WorkspaceDataset.workspace_id == workspace_id
            ).all()

            datasets_info = []
            for wd in workspace_datasets:
                dataset = self.db.query(Dataset).filter(Dataset.id == wd.dataset_id).first()
                if dataset:
                    datasets_info.append({
                        "id": dataset.id,
                        "name": dataset.name,
                        "role": wd.role,
                        "tags": wd.tags,
                        "priority": wd.priority,
                        "added_at": wd.added_at
                    })

            workspace_data = {
                "id": workspace.id,
                "name": workspace.name,
                "description": workspace.description,
                "user_id": workspace.user_id,
                "settings": workspace.settings,
                "created_at": workspace.created_at,
                "updated_at": workspace.updated_at,
                "is_active": workspace.is_active,
                "datasets": datasets_info
            }

            return ResponseHandler.create_success_response(
                data=workspace_data,
                message="Workspace retrieved successfully",
                response_type=ResponseType.GENERAL
            )

        except Exception as e:
            logger.error(f"Error getting workspace {workspace_id}: {e}")
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to retrieve workspace",
                response_type=ResponseType.GENERAL
            )

    # Context Resolution
    async def resolve_query_context(
        self, 
        session_id: Optional[Union[str, UUID]] = None,
        workspace_id: Optional[Union[str, UUID]] = None,
        dataset_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Resolve query context and return available datasets
        Priority: explicit dataset_id > session context > workspace context
        """
        try:
            context_info = {
                "strategy": "unknown",
                "available_datasets": [],
                "default_dataset": None,
                "context_metadata": {}
            }

            # Priority 1: Explicit dataset_id (legacy mode)
            if dataset_id:
                dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
                if not dataset:
                    return ResponseHandler.create_error_response(
                        error=f"Dataset {dataset_id} not found",
                        message="Specified dataset not found",
                        response_type=ResponseType.VALIDATION_ERROR
                    )
                
                context_info.update({
                    "strategy": "explicit",
                    "available_datasets": [dataset_id],
                    "default_dataset": dataset_id,
                    "context_metadata": {"dataset_name": dataset.name}
                })

            # Priority 2: Session context
            elif session_id:
                session_response = await self.get_session(session_id)
                if not ResponseHandler.is_success(session_response):
                    return session_response

                session_data = ResponseHandler.extract_data_safely(session_response)
                available_datasets = []

                # Add default dataset
                if session_data.get("default_dataset_id"):
                    available_datasets.append(session_data["default_dataset_id"])

                # Add context datasets
                if session_data.get("context_datasets"):
                    for cd in session_data["context_datasets"]:
                        if cd.get("id") not in available_datasets:
                            available_datasets.append(cd["id"])

                context_info.update({
                    "strategy": "session",
                    "available_datasets": available_datasets,
                    "default_dataset": session_data.get("default_dataset_id"),
                    "context_metadata": {
                        "session_name": session_data.get("name"),
                        "session_settings": session_data.get("settings")
                    }
                })

            # Priority 3: Workspace context
            elif workspace_id:
                workspace_response = await self.get_workspace(workspace_id)
                if not ResponseHandler.is_success(workspace_response):
                    return workspace_response

                workspace_data = ResponseHandler.extract_data_safely(workspace_response)
                datasets = workspace_data.get("datasets", [])
                
                # Sort by priority (highest first)
                datasets.sort(key=lambda x: x.get("priority", 0), reverse=True)
                
                available_datasets = [d["id"] for d in datasets]
                default_dataset = available_datasets[0] if available_datasets else None

                context_info.update({
                    "strategy": "workspace",
                    "available_datasets": available_datasets,
                    "default_dataset": default_dataset,
                    "context_metadata": {
                        "workspace_name": workspace_data.get("name"),
                        "workspace_description": workspace_data.get("description"),
                        "datasets_info": datasets
                    }
                })

            # No context provided - return error
            else:
                return ResponseHandler.create_error_response(
                    error="No context provided",
                    message="Must provide dataset_id, session_id, or workspace_id",
                    response_type=ResponseType.VALIDATION_ERROR
                )

            return ResponseHandler.create_success_response(
                data=context_info,
                message="Query context resolved successfully",
                response_type=ResponseType.GENERAL
            )

        except Exception as e:
            logger.error(f"Error resolving query context: {e}")
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to resolve query context",
                response_type=ResponseType.GENERAL
            )
