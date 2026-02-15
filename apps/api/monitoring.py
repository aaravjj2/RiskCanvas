"""
Monitoring module for v1.6 - Risk Monitoring
Provides scheduled portfolio monitoring with alerts and drift detection.
"""

import hashlib
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import Field, SQLModel, Session, select
from database import db, canonicalize_json


class MonitorModel(SQLModel, table=True):
    __tablename__ = "monitors"
    
    monitor_id: str = Field(primary_key=True)
    workspace_id: Optional[str] = None
    portfolio_id: str
    name: str
    schedule: str  # "manual", "daily", "weekly"
    scenario_preset: Optional[str] = None  # JSON of scenario config
    thresholds: str  # JSON: {"var_95_max": -50000, "loss_max": -25000}
    enabled: bool = Field(default=True)
    last_run_id: Optional[str] = None
    last_run_sequence: int = Field(default=0)
    created_at: str
    updated_at: str


class AlertModel(SQLModel, table=True):
    __tablename__ = "alerts"
    
    alert_id: str = Field(primary_key=True)
    monitor_id: str
    run_id: str
    severity: str  # "info", "warning", "critical"
    rule: str  # Which threshold was breached
    message: str
    triggered_value: float
    threshold_value: float
    sequence: int
    created_at: str


class DriftSummaryModel(SQLModel, table=True):
    __tablename__ = "drift_summaries"
    
    drift_id: str = Field(primary_key=True)
    monitor_id: str
    previous_run_id: str
    current_run_id: str
    changes: str  # JSON of detected changes
    drift_score: float  # Normalized measure of drift
    sequence: int
    created_at: str


# Global sequence counter for determinism
_monitor_sequence = 0
_alert_sequence = 0
_drift_sequence = 0


def reset_monitor_sequences():
    """Reset all monitor-related sequences for tests"""
    global _monitor_sequence, _alert_sequence, _drift_sequence
    _monitor_sequence = 0
    _alert_sequence = 0
    _drift_sequence = 0


def generate_monitor_id(workspace_id: Optional[str], portfolio_id: str, name: str) -> str:
    """Generate deterministic monitor ID"""
    canonical_input = canonicalize_json({
        "workspace_id": workspace_id,
        "portfolio_id": portfolio_id,
        "name": name
    })
    hash_value = hashlib.sha256(canonical_input.encode('utf-8')).hexdigest()
    return hash_value[:32]


def create_monitor(
    portfolio_id: str,
    name: str,
    schedule: str,
    thresholds: Dict[str, float],
    workspace_id: Optional[str] = None,
    scenario_preset: Optional[dict] = None
) -> dict:
    """Create a risk monitor"""
    monitor_id = generate_monitor_id(workspace_id, portfolio_id, name)
    now = datetime.utcnow().isoformat()
    
    with db.get_session() as session:
        existing = session.exec(
            select(MonitorModel).where(MonitorModel.monitor_id == monitor_id)
        ).first()
        
        if existing:
            existing.schedule = schedule
            existing.thresholds = json.dumps(thresholds)
            existing.scenario_preset = json.dumps(scenario_preset) if scenario_preset else None
            existing.updated_at = now
            session.add(existing)
            session.commit()
            session.refresh(existing)
            monitor = existing
        else:
            monitor = MonitorModel(
                monitor_id=monitor_id,
                workspace_id=workspace_id,
                portfolio_id=portfolio_id,
                name=name,
                schedule=schedule,
                scenario_preset=json.dumps(scenario_preset) if scenario_preset else None,
                thresholds=json.dumps(thresholds),
                enabled=True,
                last_run_id=None,
                last_run_sequence=0,
                created_at=now,
                updated_at=now
            )
            session.add(monitor)
            session.commit()
            session.refresh(monitor)
    
    return _monitor_to_dict(monitor)


def list_monitors(workspace_id: Optional[str] = None, portfolio_id: Optional[str] = None) -> List[dict]:
    """List monitors with optional filters"""
    with db.get_session() as session:
        query = select(MonitorModel)
        if workspace_id:
            query = query.where(MonitorModel.workspace_id == workspace_id)
        if portfolio_id:
            query = query.where(MonitorModel.portfolio_id == portfolio_id)
        monitors = session.exec(query).all()
        return [_monitor_to_dict(m) for m in monitors]


def get_monitor(monitor_id: str) -> Optional[dict]:
    """Get monitor by ID"""
    with db.get_session() as session:
        monitor = session.exec(
            select(MonitorModel).where(MonitorModel.monitor_id == monitor_id)
        ).first()
        return _monitor_to_dict(monitor) if monitor else None


def update_monitor_last_run(monitor_id: str, run_id: str, sequence: int):
    """Update monitor's last run info"""
    with db.get_session() as session:
        monitor = session.exec(
            select(MonitorModel).where(MonitorModel.monitor_id == monitor_id)
        ).first()
        if monitor:
            monitor.last_run_id = run_id
            monitor.last_run_sequence = sequence
            monitor.updated_at = datetime.utcnow().isoformat()
            session.add(monitor)
            session.commit()


def create_alert(
    monitor_id: str,
    run_id: str,
    severity: str,
    rule: str,
    message: str,
    triggered_value: float,
    threshold_value: float
) -> dict:
    """Create an alert for a monitor"""
    global _alert_sequence
    _alert_sequence += 1
    
    canonical_input = canonicalize_json({
        "monitor_id": monitor_id,
        "run_id": run_id,
        "rule": rule,
        "sequence": _alert_sequence
    })
    alert_id = hashlib.sha256(canonical_input.encode('utf-8')).hexdigest()[:32]
    now = datetime.utcnow().isoformat()
    
    with db.get_session() as session:
        alert = AlertModel(
            alert_id=alert_id,
            monitor_id=monitor_id,
            run_id=run_id,
            severity=severity,
            rule=rule,
            message=message,
            triggered_value=triggered_value,
            threshold_value=threshold_value,
            sequence=_alert_sequence,
            created_at=now
        )
        session.add(alert)
        session.commit()
        session.refresh(alert)
    
    return {
        "alert_id": alert.alert_id,
        "monitor_id": alert.monitor_id,
        "run_id": alert.run_id,
        "severity": alert.severity,
        "rule": alert.rule,
        "message": alert.message,
        "triggered_value": alert.triggered_value,
        "threshold_value": alert.threshold_value,
        "sequence": alert.sequence,
        "created_at": alert.created_at
    }


def list_alerts(monitor_id: Optional[str] = None, limit: int = 100) -> List[dict]:
    """List alerts with optional filters"""
    with db.get_session() as session:
        query = select(AlertModel)
        if monitor_id:
            query = query.where(AlertModel.monitor_id == monitor_id)
        query = query.order_by(AlertModel.sequence.desc()).limit(limit)
        alerts = session.exec(query).all()
        
        return [
            {
                "alert_id": a.alert_id,
                "monitor_id": a.monitor_id,
                "run_id": a.run_id,
                "severity": a.severity,
                "rule": a.rule,
                "message": a.message,
                "triggered_value": a.triggered_value,
                "threshold_value": a.threshold_value,
                "sequence": a.sequence,
                "created_at": a.created_at
            }
            for a in alerts
        ]


def create_drift_summary(
    monitor_id: str,
    previous_run_id: str,
    current_run_id: str,
    changes: Dict[str, Any],
    drift_score: float
) -> dict:
    """Create a drift summary comparing two runs"""
    global _drift_sequence
    _drift_sequence += 1
    
    canonical_input = canonicalize_json({
        "monitor_id": monitor_id,
        "previous_run_id": previous_run_id,
        "current_run_id": current_run_id,
        "sequence": _drift_sequence
    })
    drift_id = hashlib.sha256(canonical_input.encode('utf-8')).hexdigest()[:32]
    now = datetime.utcnow().isoformat()
    
    with db.get_session() as session:
        drift = DriftSummaryModel(
            drift_id=drift_id,
            monitor_id=monitor_id,
            previous_run_id=previous_run_id,
            current_run_id=current_run_id,
            changes=json.dumps(changes),
            drift_score=drift_score,
            sequence=_drift_sequence,
            created_at=now
        )
        session.add(drift)
        session.commit()
        session.refresh(drift)
    
    return {
        "drift_id": drift.drift_id,
        "monitor_id": drift.monitor_id,
        "previous_run_id": drift.previous_run_id,
        "current_run_id": drift.current_run_id,
        "changes": json.loads(drift.changes),
        "drift_score": drift.drift_score,
        "sequence": drift.sequence,
        "created_at": drift.created_at
    }


def list_drift_summaries(monitor_id: Optional[str] = None, limit: int = 50) -> List[dict]:
    """List drift summaries with optional filters"""
    with db.get_session() as session:
        query = select(DriftSummaryModel)
        if monitor_id:
            query = query.where(DriftSummaryModel.monitor_id == monitor_id)
        query = query.order_by(DriftSummaryModel.sequence.desc()).limit(limit)
        drifts = session.exec(query).all()
        
        return [
            {
                "drift_id": d.drift_id,
                "monitor_id": d.monitor_id,
                "previous_run_id": d.previous_run_id,
                "current_run_id": d.current_run_id,
                "changes": json.loads(d.changes),
                "drift_score": d.drift_score,
                "sequence": d.sequence,
                "created_at": d.created_at
            }
            for d in drifts
        ]


def _monitor_to_dict(monitor: MonitorModel) -> dict:
    """Convert monitor model to dict"""
    return {
        "monitor_id": monitor.monitor_id,
        "workspace_id": monitor.workspace_id,
        "portfolio_id": monitor.portfolio_id,
        "name": monitor.name,
        "schedule": monitor.schedule,
        "scenario_preset": json.loads(monitor.scenario_preset) if monitor.scenario_preset else None,
        "thresholds": json.loads(monitor.thresholds),
        "enabled": monitor.enabled,
        "last_run_id": monitor.last_run_id,
        "last_run_sequence": monitor.last_run_sequence,
        "created_at": monitor.created_at,
        "updated_at": monitor.updated_at
    }
