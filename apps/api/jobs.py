"""
Job Queue System for RiskCanvas (v2.6+).
Supports async execution of runs, reports, and hedges with deterministic job IDs.
v2.4: In-memory job store (DEMO mode)
v2.6: SQLite-based job store with persistence
"""
import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Protocol
from pathlib import Path
import os
from sqlmodel import Field, SQLModel, create_engine, Session, select


class JobType(str, Enum):
    """Job types supported by the queue."""
    RUN = "run"
    REPORT = "report"
    HEDGE = "hedge"


class JobStatus(str, Enum):
    """Job execution status."""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


def canonicalize_job_input(job_type: str, payload: Dict[str, Any]) -> str:
    """Convert job input to canonical JSON."""
    return json.dumps({"type": job_type, "payload": payload}, sort_keys=True, separators=(',', ':'))


def generate_job_id(workspace_id: str, job_type: str, payload: Dict[str, Any], version: str) -> str:
    """
    Generate deterministic job ID.
    job_id = SHA256(workspace_id + canonical_job_input + version)[:32]
    """
    canonical_input = canonicalize_job_input(job_type, payload)
    combined = f"{workspace_id}:{canonical_input}:{version}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:32]


class Job:
    """Job model with deterministic properties."""
    
    def __init__(
        self,
        job_id: str,
        workspace_id: str,
        job_type: JobType,
        payload: Dict[str, Any],
        status: JobStatus = JobStatus.QUEUED,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        created_at: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None
    ):
        self.job_id = job_id
        self.workspace_id = workspace_id
        self.job_type = job_type
        self.payload = payload
        self.status = status
        self.result = result
        self.error = error
        self.created_at = created_at or datetime.utcnow().isoformat() + "Z"
        self.started_at = started_at
        self.completed_at = completed_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return {
            "job_id": self.job_id,
            "workspace_id": self.workspace_id,
            "job_type": self.job_type.value,
            "payload": self.payload,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary."""
        return cls(
            job_id=data["job_id"],
            workspace_id=data["workspace_id"],
            job_type=JobType(data["job_type"]),
            payload=data["payload"],
            status=JobStatus(data["status"]),
            result=data.get("result"),
            error=data.get("error"),
            created_at=data.get("created_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at")
        )


# ===== SQLModel for Database Persistence (v2.6+) =====


class JobModel(SQLModel, table=True):
    """
    Job model for SQLite persistence.
    Enables jobs to survive server restarts.
    """
    __tablename__ = "jobs"
    
    job_id: str = Field(primary_key=True, max_length=32)
    workspace_id: str = Field(max_length=32, index=True)
    job_type: str = Field(max_length=32, index=True)  # JobType enum value
    payload: str = Field()  # JSON string
    status: str = Field(default="queued", max_length=32, index=True)  # JobStatus enum value
    result: Optional[str] = Field(default=None)  # JSON string
    error: Optional[str] = Field(default=None)
    created_at: str = Field()
    started_at: Optional[str] = Field(default=None)
    completed_at: Optional[str] = Field(default=None)
    
    def to_job(self) -> Job:
        """Convert JobModel to Job instance."""
        return Job(
            job_id=self.job_id,
            workspace_id=self.workspace_id,
            job_type=JobType(self.job_type),
            payload=json.loads(self.payload),
            status=JobStatus(self.status),
            result=json.loads(self.result) if self.result else None,
            error=self.error,
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at
        )
    
    @staticmethod
    def from_job(job: Job) -> 'JobModel':
        """Convert Job instance to JobModel."""
        return JobModel(
            job_id=job.job_id,
            workspace_id=job.workspace_id,
            job_type=job.job_type.value,
            payload=json.dumps(job.payload),
            status=job.status.value,
            result=json.dumps(job.result) if job.result else None,
            error=job.error,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )


# ===== Job Store Interface =====


class JobStoreProtocol(Protocol):
    """Protocol for job store implementations."""
    
    def create(self, job: Job) -> Job:
        ...
    
    def get(self, job_id: str) -> Optional[Job]:
        ...
    
    def list(
        self,
        workspace_id: Optional[str] = None,
        job_type: Optional[JobType] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100
    ) -> List[Job]:
        ...
    
    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Optional[Job]:
        ...
    
    def delete(self, job_id: str) -> bool:
        ...
    
    def clear(self):
        ...


class JobStore:
    """
    Simple in-memory job store (v2.4 MVP).
    Used for DEMO mode and testing.
    """
    
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
    
    def create(self, job: Job) -> Job:
        """Create new job."""
        self._jobs[job.job_id] = job
        return job
    
    def get(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self._jobs.get(job_id)
    
    def list(
        self,
        workspace_id: Optional[str] = None,
        job_type: Optional[JobType] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100
    ) -> List[Job]:
        """List jobs with filters."""
        jobs = list(self._jobs.values())
        
        if workspace_id:
            jobs = [j for j in jobs if j.workspace_id == workspace_id]
        
        if job_type:
            jobs = [j for j in jobs if j.job_type == job_type]
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        return jobs[:limit]
    
    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Optional[Job]:
        """Update job status and result."""
        job = self._jobs.get(job_id)
        if not job:
            return None
        
        job.status = status
        
        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.utcnow().isoformat() + "Z"
        
        if status in [JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.completed_at = datetime.utcnow().isoformat() + "Z"
            if result:
                job.result = result
            if error:
                job.error = error
        
        return job
    
    def delete(self, job_id: str) -> bool:
        """Delete job."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False
    
    def clear(self):
        """Clear all jobs (for testing)."""
        self._jobs.clear()


class JobStoreSQLite:
    """
    SQLite-based job store (v2.6+).
    Provides persistence across server restarts.
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize SQLite job store.
        
        Args:
            db_url: SQLite database URL. If None, uses default location.
        """
        if db_url is None:
            # Default: file-based SQLite in /apps/api/data/riskcanvas.db
            db_dir = Path(__file__).parent / "data"
            db_dir.mkdir(exist_ok=True)
            db_path = db_dir / "riskcanvas.db"
            db_url = f"sqlite:///{db_path}"
        
        self.engine = create_engine(
            db_url,
            echo=False,
            connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {}
        )
        
        # Create jobs table if not exists
        SQLModel.metadata.create_all(self.engine)
    
    def create(self, job: Job) -> Job:
        """Create new job."""
        with Session(self.engine) as session:
            job_model = JobModel.from_job(job)
            session.add(job_model)
            session.commit()
            session.refresh(job_model)
            return job_model.to_job()
    
    def get(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        with Session(self.engine) as session:
            statement = select(JobModel).where(JobModel.job_id == job_id)
            job_model = session.exec(statement).first()
            return job_model.to_job() if job_model else None
    
    def list(
        self,
        workspace_id: Optional[str] = None,
        job_type: Optional[JobType] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100
    ) -> List[Job]:
        """List jobs with filters."""
        with Session(self.engine) as session:
            statement = select(JobModel)
            
            if workspace_id:
                statement = statement.where(JobModel.workspace_id == workspace_id)
            
            if job_type:
                statement = statement.where(JobModel.job_type == job_type.value)
            
            if status:
                statement = statement.where(JobModel.status == status.value)
            
            # Sort by created_at descending
            statement = statement.order_by(JobModel.created_at.desc()).limit(limit)
            
            job_models = session.exec(statement).all()
            return [jm.to_job() for jm in job_models]
    
    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Optional[Job]:
        """Update job status and result."""
        with Session(self.engine) as session:
            statement = select(JobModel).where(JobModel.job_id == job_id)
            job_model = session.exec(statement).first()
            
            if not job_model:
                return None
            
            job_model.status = status.value
            
            if status == JobStatus.RUNNING and not job_model.started_at:
                job_model.started_at = datetime.utcnow().isoformat() + "Z"
            
            if status in [JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED]:
                job_model.completed_at = datetime.utcnow().isoformat() + "Z"
                if result:
                    job_model.result = json.dumps(result)
                if error:
                    job_model.error = error
            
            session.add(job_model)
            session.commit()
            session.refresh(job_model)
            return job_model.to_job()
    
    def delete(self, job_id: str) -> bool:
        """Delete job."""
        with Session(self.engine) as session:
            statement = select(JobModel).where(JobModel.job_id == job_id)
            job_model = session.exec(statement).first()
            
            if job_model:
                session.delete(job_model)
                session.commit()
                return True
            return False
    
    def clear(self):
        """Clear all jobs (for testing)."""
        with Session(self.engine) as session:
            statement = select(JobModel)
            job_models = session.exec(statement).all()
            for jm in job_models:
                session.delete(jm)
            session.commit()


# ===== Global Job Store Configuration =====


_job_store_backend: str = os.getenv("JOB_STORE_BACKEND", "memory")  # "memory" or "sqlite"
_job_store: Optional[JobStoreProtocol] = None


def get_job_store() -> JobStoreProtocol:
    """
    Get global job store instance.
    
    Backend is configured via JOB_STORE_BACKEND env var:
    - "memory": In-memory store (default, for DEMO mode)
    - "sqlite": SQLite-based store (for persistence)
    """
    global _job_store, _job_store_backend
    
    if _job_store is None:
        if _job_store_backend == "sqlite":
            _job_store = JobStoreSQLite()
        else:
            _job_store = JobStore()
    
    return _job_store


def get_job_store_backend() -> str:
    """Get current job store backend type."""
    return _job_store_backend


def execute_job_inline(job: Job) -> Dict[str, Any]:
    """
    Execute job inline (for DEMO mode).
    Returns result dict with output references.
    """
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    if not demo_mode:
        raise RuntimeError("Inline execution only allowed in DEMO mode")
    
    # Import here to avoid circular dependencies
    from database import db
    import sys
    from pathlib import Path
    
    # Ensure engine is in path
    engine_path = str(Path(__file__).parent.parent.parent / "packages" / "engine")
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    
    result = {}
    
    try:
        if job.job_type == JobType.RUN:
            # Execute run
            from src import (
                portfolio_pnl,
                portfolio_greeks,
                var_parametric,
                var_historical
            )
            
            portfolio_id = job.payload.get("portfolio_id")
            params = job.payload.get("params", {})
            
            # Get portfolio
            portfolio_model = db.get_portfolio(portfolio_id)
            if not portfolio_model:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            portfolio_data = json.loads(portfolio_model.canonical_data)
            
            # Run pricing
            pricing = portfolio_pnl(portfolio_data, params)
            
            # Run greeks if options present
            greeks = None
            has_options = any(a.get("type") == "option" for a in portfolio_data.get("assets", []))
            if has_options:
                greeks = portfolio_greeks(portfolio_data, params)
            
            # Run VaR
            var_result = var_parametric(portfolio_data, params)
            
            # Generate run_id deterministically
            from database import generate_run_id
            run_id = generate_run_id(portfolio_id, params, "2.4.0")
            
            # Store run (minimal for job result)
            result = {
                "run_id": run_id,
                "portfolio_id": portfolio_id,
                "outputs": {
                    "pricing": pricing,
                    "greeks": greeks,
                    "var": var_result
                }
            }
        
        elif job.job_type == JobType.REPORT:
            # Execute report build
            from report_bundle import (
                generate_report_bundle_id,
                store_report_bundle_to_storage
            )
            from storage import get_storage_provider
            
            run_id = job.payload.get("run_id")
            run = db.get_run(run_id)
            if not run:
                raise ValueError(f"Run {run_id} not found")
            
            # Get portfolio
            portfolio_model = db.get_portfolio(run.portfolio_id)
            portfolio_data = json.loads(portfolio_model.canonical_data)
            
            # Build run data
            run_data = {
                "run_id": run.run_id,
                "portfolio_id": run.portfolio_id,
                "engine_version": run.engine_version,
                "run_params": json.loads(run.run_params),
                "outputs": {
                    "pricing": json.loads(run.pricing_output) if run.pricing_output else None,
                    "greeks": json.loads(run.greeks_output) if run.greeks_output else None,
                    "var": json.loads(run.var_output) if run.var_output else None,
                },
                "output_hash": run.output_hash,
                "created_at": run.created_at
            }
            
            # Generate and store bundle
            report_bundle_id = generate_report_bundle_id(run.run_id, run_data["outputs"])
            manifest = store_report_bundle_to_storage(
                report_bundle_id, run_data, portfolio_data, get_storage_provider()
            )
            
            result = {
                "report_bundle_id": report_bundle_id,
                "run_id": run_id,
                "manifest": manifest
            }
        
        elif job.job_type == JobType.HEDGE:
            # Execute hedge generation
            from hedge_engine import generate_hedge_candidates
            
            portfolio_id = job.payload.get("portfolio_id")
            target_reduction = job.payload.get("target_reduction", 0.5)
            
            # Get portfolio
            portfolio_model = db.get_portfolio(portfolio_id)
            if not portfolio_model:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            portfolio_data = json.loads(portfolio_model.canonical_data)
            
            # Generate hedges
            hedges = generate_hedge_candidates(portfolio_data, target_reduction)
            
            result = {
                "portfolio_id": portfolio_id,
                "target_reduction": target_reduction,
                "hedges": hedges
            }
        
        else:
            raise ValueError(f"Unknown job type: {job.job_type}")
        
        return result
    
    except Exception as e:
        raise RuntimeError(f"Job execution failed: {str(e)}")
