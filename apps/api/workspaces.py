"""
Workspaces module for v1.4 - Enterprise Readiness Pack 1
Provides workspace isolation and multi-tenancy support.
"""

import hashlib
import json
from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Session, select
from database import db, canonicalize_json


class WorkspaceModel(SQLModel, table=True):
    __tablename__ = "workspaces"
    
    workspace_id: str = Field(primary_key=True)
    name: str
    owner: str  # User identifier (email or ID)
    tags: str = Field(default="[]")  # JSON array
    created_at: str
    updated_at: str


def generate_workspace_id(owner: str, seed: str = "default") -> str:
    """Generate deterministic workspace ID from owner + seed"""
    canonical_input = canonicalize_json({"owner": owner, "seed": seed})
    hash_value = hashlib.sha256(canonical_input.encode('utf-8')).hexdigest()
    return hash_value[:32]


def create_workspace(name: str, owner: str, tags: Optional[List[str]] = None) -> dict:
    """Create or update a workspace"""
    workspace_id = generate_workspace_id(owner)
    now = datetime.utcnow().isoformat()
    
    with db.get_session() as session:
        existing = session.exec(
            select(WorkspaceModel).where(WorkspaceModel.workspace_id == workspace_id)
        ).first()
        
        if existing:
            existing.name = name
            existing.tags = json.dumps(tags or [])
            existing.updated_at = now
            session.add(existing)
            session.commit()
            session.refresh(existing)
            workspace = existing
        else:
            workspace = WorkspaceModel(
                workspace_id=workspace_id,
                name=name,
                owner=owner,
                tags=json.dumps(tags or []),
                created_at=now,
                updated_at=now
            )
            session.add(workspace)
            session.commit()
            session.refresh(workspace)
    
    return {
        "workspace_id": workspace.workspace_id,
        "name": workspace.name,
        "owner": workspace.owner,
        "tags": json.loads(workspace.tags),
        "created_at": workspace.created_at,
        "updated_at": workspace.updated_at
    }


def list_workspaces(owner: Optional[str] = None) -> List[dict]:
    """List all workspaces, optionally filtered by owner"""
    with db.get_session() as session:
        query = select(WorkspaceModel)
        if owner:
            query = query.where(WorkspaceModel.owner == owner)
        workspaces = session.exec(query).all()
        
        return [
            {
                "workspace_id": w.workspace_id,
                "name": w.name,
                "owner": w.owner,
                "tags": json.loads(w.tags),
                "created_at": w.created_at,
                "updated_at": w.updated_at
            }
            for w in workspaces
        ]


def get_workspace(workspace_id: str) -> Optional[dict]:
    """Get workspace by ID"""
    with db.get_session() as session:
        workspace = session.exec(
            select(WorkspaceModel).where(WorkspaceModel.workspace_id == workspace_id)
        ).first()
        
        if not workspace:
            return None
        
        return {
            "workspace_id": workspace.workspace_id,
            "name": workspace.name,
            "owner": workspace.owner,
            "tags": json.loads(workspace.tags),
            "created_at": workspace.created_at,
            "updated_at": workspace.updated_at
        }


def delete_workspace(workspace_id: str) -> bool:
    """Delete workspace and all associated data"""
    with db.get_session() as session:
        workspace = session.exec(
            select(WorkspaceModel).where(WorkspaceModel.workspace_id == workspace_id)
        ).first()
        
        if not workspace:
            return False
        
        session.delete(workspace)
        session.commit()
        return True
