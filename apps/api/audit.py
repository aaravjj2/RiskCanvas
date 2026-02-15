"""
Audit logging module for v1.4
Provides deterministic audit trail for all API actions.
"""

import hashlib
import json
from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Session, select, or_
from database import db, canonicalize_json


class AuditEventModel(SQLModel, table=True):
    __tablename__ = "audit_events"
    
    event_id: str = Field(primary_key=True)
    workspace_id: Optional[str] = None
    actor: str  # User identifier
    actor_role: str  # Role at time of action
    action: str  # create/read/update/delete/execute
    resource_type: str  # portfolio/run/report/hedge/monitor
    resource_id: Optional[str] = None
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None
    result: str  # success/failure/error
    error_message: Optional[str] = None
    sequence: int  # Monotonic sequence number for determinism
    created_at: str


# Global sequence counter (reset in tests)
_audit_sequence = 0


def reset_audit_sequence():
    """Reset audit sequence for tests"""
    global _audit_sequence
    _audit_sequence = 0


def generate_audit_event_id(
    workspace_id: Optional[str],
    actor: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str],
    sequence: int
) -> str:
    """Generate deterministic audit event ID"""
    canonical_input = canonicalize_json({
        "workspace_id": workspace_id,
        "actor": actor,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "sequence": sequence
    })
    hash_value = hashlib.sha256(canonical_input.encode('utf-8')).hexdigest()
    return hash_value[:32]


def log_audit_event(
    actor: str,
    actor_role: str,
    action: str,
    resource_type: str,
    workspace_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    input_data: Optional[dict] = None,
    output_data: Optional[dict] = None,
    result: str = "success",
    error_message: Optional[str] = None
) -> dict:
    """Log an audit event with deterministic ID"""
    global _audit_sequence
    _audit_sequence += 1
    sequence = _audit_sequence
    
    # Compute hashes
    input_hash = None
    if input_data:
        canonical_input = canonicalize_json(input_data)
        input_hash = hashlib.sha256(canonical_input.encode('utf-8')).hexdigest()[:32]
    
    output_hash = None
    if output_data:
        canonical_output = canonicalize_json(output_data)
        output_hash = hashlib.sha256(canonical_output.encode('utf-8')).hexdigest()[:32]
    
    event_id = generate_audit_event_id(
        workspace_id, actor, action, resource_type, resource_id, sequence
    )
    now = datetime.utcnow().isoformat()
    
    with db.get_session() as session:
        event = AuditEventModel(
            event_id=event_id,
            workspace_id=workspace_id,
            actor=actor,
            actor_role=actor_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            input_hash=input_hash,
            output_hash=output_hash,
            result=result,
            error_message=error_message,
            sequence=sequence,
            created_at=now
        )
        session.add(event)
        session.commit()
        session.refresh(event)
    
    return {
        "event_id": event.event_id,
        "workspace_id": event.workspace_id,
        "actor": event.actor,
        "actor_role": event.actor_role,
        "action": event.action,
        "resource_type": event.resource_type,
        "resource_id": event.resource_id,
        "input_hash": event.input_hash,
        "output_hash": event.output_hash,
        "result": event.result,
        "error_message": event.error_message,
        "sequence": event.sequence,
        "created_at": event.created_at
    }


def list_audit_events(
    workspace_id: Optional[str] = None,
    actor: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100
) -> List[dict]:
    """List audit events with optional filters"""
    with db.get_session() as session:
        query = select(AuditEventModel)
        
        filters = []
        if workspace_id:
            filters.append(AuditEventModel.workspace_id == workspace_id)
        if actor:
            filters.append(AuditEventModel.actor == actor)
        if resource_type:
            filters.append(AuditEventModel.resource_type == resource_type)
        
        if filters:
            query = query.where(or_(*filters))
        
        query = query.order_by(AuditEventModel.sequence.desc()).limit(limit)
        events = session.exec(query).all()
        
        return [
            {
                "event_id": e.event_id,
                "workspace_id": e.workspace_id,
                "actor": e.actor,
                "actor_role": e.actor_role,
                "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "input_hash": e.input_hash,
                "output_hash": e.output_hash,
                "result": e.result,
                "error_message": e.error_message,
                "sequence": e.sequence,
                "created_at": e.created_at
            }
            for e in events
        ]
