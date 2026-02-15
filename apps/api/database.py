"""
Database models and storage layer for RiskCanvas v1.1+

Uses SQLModel for type-safe ORM with Pydantic integration.
Supports deterministic IDs based on content hashing.
"""

import json
import hashlib
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, create_engine, Session, select
from pathlib import Path
import os


# ===== Deterministic ID Generation =====


def canonicalize_json(obj: any) -> str:
    """
    Convert a Python object to canonical JSON string (deterministic).
    - Sorted keys
    - No whitespace
    - Consistent encoding
    """
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True, default=str)


def generate_portfolio_id(portfolio_data: dict) -> str:
    """
    Generate deterministic portfolio_id from canonicalized portfolio JSON.
    portfolio_id = SHA256(canonical_json(portfolio))
    """
    canonical = canonicalize_json(portfolio_data)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:32]


def generate_run_id(portfolio_id: str, run_params: dict, engine_version: str) -> str:
    """
    Generate deterministic run_id from portfolio + params + engine version.
    run_id = SHA256(portfolio_id + canonical_json(params) + engine_version)
    """
    canonical_params = canonicalize_json(run_params)
    combined = f"{portfolio_id}:{canonical_params}:{engine_version}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:32]


# ===== Database Models =====


class PortfolioModel(SQLModel, table=True):
    """Stored portfolio with deterministic ID"""
    __tablename__ = "portfolios"
    
    portfolio_id: str = Field(primary_key=True, max_length=32)
    name: Optional[str] = Field(default=None, max_length=255)
    tags: Optional[str] = Field(default=None)  # JSON array as string
    canonical_data: str = Field()  # Canonical JSON of portfolio
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class RunModel(SQLModel, table=True):
    """Stored analysis run with deterministic ID"""
    __tablename__ = "runs"
    
    run_id: str = Field(primary_key=True, max_length=32)
    portfolio_id: str = Field(foreign_key="portfolios.portfolio_id", max_length=32)
    run_params: str = Field()  # Canonical JSON of params
    engine_version: str = Field(max_length=32)
    
    # Computed outputs (all JSON strings)
    pricing_output: Optional[str] = Field(default=None)
    greeks_output: Optional[str] = Field(default=None)
    var_output: Optional[str] = Field(default=None)
    scenarios_output: Optional[str] = Field(default=None)
    
    # Hashes for determinism verification
    output_hash: Optional[str] = Field(default=None, max_length=64)
    report_bundle_id: Optional[str] = Field(default=None, max_length=32)
    
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ===== Storage Layer =====


class Database:
    """
    Database manager with configurable SQLite backend.
    Defaults to file-based DB, supports in-memory for tests.
    """
    
    def __init__(self, db_url: Optional[str] = None):
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
        SQLModel.metadata.create_all(self.engine)
    
    def get_session(self) -> Session:
        return Session(self.engine)
    
    # ===== Portfolio CRUD =====
    
    def create_portfolio(self, portfolio_data: dict, name: Optional[str] = None, tags: Optional[list] = None) -> PortfolioModel:
        """Create or update portfolio with deterministic ID"""
        portfolio_id = generate_portfolio_id(portfolio_data)
        canonical_data = canonicalize_json(portfolio_data)
        tags_json = json.dumps(tags) if tags else None
        
        with self.get_session() as session:
            # Check if exists
            existing = session.get(PortfolioModel, portfolio_id)
            if existing:
                # Update
                existing.canonical_data = canonical_data
                existing.updated_at = datetime.utcnow().isoformat()
                if name:
                    existing.name = name
                if tags_json:
                    existing.tags = tags_json
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            else:
                # Create
                portfolio = PortfolioModel(
                    portfolio_id=portfolio_id,
                    name=name or f"Portfolio {portfolio_id[:8]}",
                    tags=tags_json,
                    canonical_data=canonical_data
                )
                session.add(portfolio)
                session.commit()
                session.refresh(portfolio)
                return portfolio
    
    def get_portfolio(self, portfolio_id: str) -> Optional[PortfolioModel]:
        """Get portfolio by ID"""
        with self.get_session() as session:
            return session.get(PortfolioModel, portfolio_id)
    
    def list_portfolios(self) -> list[PortfolioModel]:
        """List all portfolios"""
        with self.get_session() as session:
            statement = select(PortfolioModel).order_by(PortfolioModel.updated_at.desc())
            results = session.exec(statement)
            return list(results.all())
    
    def delete_portfolio(self, portfolio_id: str) -> bool:
        """Delete portfolio by ID"""
        with self.get_session() as session:
            portfolio = session.get(PortfolioModel, portfolio_id)
            if portfolio:
                # Delete associated runs
                statement = select(RunModel).where(RunModel.portfolio_id == portfolio_id)
                runs = session.exec(statement).all()
                for run in runs:
                    session.delete(run)
                
                session.delete(portfolio)
                session.commit()
                return True
            return False
    
    # ===== Run CRUD =====
    
    def create_run(
        self,
        portfolio_id: str,
        run_params: dict,
        engine_version: str,
        outputs: dict
    ) -> RunModel:
        """Create run with deterministic ID"""
        run_id = generate_run_id(portfolio_id, run_params, engine_version)
        
        # Compute output hash
        output_hash = hashlib.sha256(
            canonicalize_json(outputs).encode('utf-8')
        ).hexdigest()
        
        with self.get_session() as session:
            # Check if exists (determinism - same inputs = same run_id)
            existing = session.get(RunModel, run_id)
            if existing:
                return existing
            
            run = RunModel(
                run_id=run_id,
                portfolio_id=portfolio_id,
                run_params=canonicalize_json(run_params),
                engine_version=engine_version,
                pricing_output=json.dumps(outputs.get("pricing")),
                greeks_output=json.dumps(outputs.get("greeks")),
                var_output=json.dumps(outputs.get("var")),
                scenarios_output=json.dumps(outputs.get("scenarios")),
                output_hash=output_hash
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            return run
    
    def get_run(self, run_id: str) -> Optional[RunModel]:
        """Get run by ID"""
        with self.get_session() as session:
            return session.get(RunModel, run_id)
    
    def list_runs(self, portfolio_id: Optional[str] = None) -> list[RunModel]:
        """List runs, optionally filtered by portfolio_id"""
        with self.get_session() as session:
            statement = select(RunModel).order_by(RunModel.created_at.desc())
            if portfolio_id:
                statement = statement.where(RunModel.portfolio_id == portfolio_id)
            results = session.exec(statement)
            return list(results.all())
    
    def update_run_report_bundle(self, run_id: str, report_bundle_id: str) -> Optional[RunModel]:
        """Update run with report bundle ID"""
        with self.get_session() as session:
            run = session.get(RunModel, run_id)
            if run:
                run.report_bundle_id = report_bundle_id
                session.add(run)
                session.commit()
                session.refresh(run)
                return run
            return None


# ===== Global DB instance =====

# Use in-memory for tests, file-based for production
_db_url = os.getenv("DATABASE_URL", None)
if os.getenv("PYTEST_CURRENT_TEST"):
    # Running under pytest - use in-memory
    _db_url = "sqlite:///:memory:"

db = Database(_db_url)
