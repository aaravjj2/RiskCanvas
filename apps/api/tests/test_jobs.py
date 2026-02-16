"""
Tests for job queue system (v2.4+).
"""
import pytest
import hashlib
import json
from jobs import (
    Job,
    JobType,
    JobStatus,
    JobStore,
    generate_job_id,
    canonicalize_job_input,
    execute_job_inline
)


class TestJobIDGeneration:
    """Test deterministic job ID generation."""
    
    def test_same_input_same_id(self):
        """Test that same input produces same job ID."""
        workspace_id = "workspace_test"
        job_type = "run"
        payload = {"portfolio_id": "port_123", "params": {"confidence": 0.95}}
        version = "2.4.0"
        
        job_id_1 = generate_job_id(workspace_id, job_type, payload, version)
        job_id_2 = generate_job_id(workspace_id, job_type, payload, version)
        
        assert job_id_1 == job_id_2
        assert len(job_id_1) == 32
    
    def test_different_input_different_id(self):
        """Test that different inputs produce different job IDs."""
        workspace_id = "workspace_test"
        version = "2.4.0"
        
        job_id_1 = generate_job_id(
            workspace_id, "run", {"portfolio_id": "port_1"}, version
        )
        job_id_2 = generate_job_id(
            workspace_id, "run", {"portfolio_id": "port_2"}, version
        )
        job_id_3 = generate_job_id(
            workspace_id, "report", {"portfolio_id": "port_1"}, version
        )
        
        assert job_id_1 != job_id_2
        assert job_id_1 != job_id_3
        assert job_id_2 != job_id_3
    
    def test_canonical_input(self):
        """Test canonical input generation."""
        # Order shouldn't matter
        payload_1 = {"a": 1, "b": 2}
        payload_2 = {"b": 2, "a": 1}
        
        canonical_1 = canonicalize_job_input("run", payload_1)
        canonical_2 = canonicalize_job_input("run", payload_2)
        
        assert canonical_1 == canonical_2


class TestJobModel:
    """Test Job model."""
    
    def test_job_creation(self):
        """Test creating a job."""
        job = Job(
            job_id="job_123",
            workspace_id="ws_1",
            job_type=JobType.RUN,
            payload={"portfolio_id": "port_1"}
        )
        
        assert job.job_id == "job_123"
        assert job.workspace_id == "ws_1"
        assert job.job_type == JobType.RUN
        assert job.status == JobStatus.QUEUED
        assert job.result is None
        assert job.error is None
        assert job.created_at is not None
    
    def test_job_to_dict(self):
        """Test job serialization."""
        job = Job(
            job_id="job_123",
            workspace_id="ws_1",
            job_type=JobType.RUN,
            payload={"test": "data"},
            status=JobStatus.SUCCEEDED,
            result={"output": "success"}
        )
        
        job_dict = job.to_dict()
        
        assert job_dict["job_id"] == "job_123"
        assert job_dict["workspace_id"] == "ws_1"
        assert job_dict["job_type"] == "run"
        assert job_dict["status"] == "succeeded"
        assert job_dict["result"] == {"output": "success"}
    
    def test_job_from_dict(self):
        """Test job deserialization."""
        job_dict = {
            "job_id": "job_456",
            "workspace_id": "ws_2",
            "job_type": "report",
            "payload": {"run_id": "run_123"},
            "status": "queued",
            "result": None,
            "error": None,
            "created_at": "2026-02-16T12:00:00Z",
            "started_at": None,
            "completed_at": None
        }
        
        job = Job.from_dict(job_dict)
        
        assert job.job_id == "job_456"
        assert job.job_type == JobType.REPORT
        assert job.status == JobStatus.QUEUED


class TestJobStore:
    """Test JobStore operations."""
    
    def setup_method(self):
        """Create fresh job store."""
        self.store = JobStore()
    
    def test_create_and_get(self):
        """Test creating and retrieving jobs."""
        job = Job(
            job_id="job_create",
            workspace_id="ws_1",
            job_type=JobType.RUN,
            payload={}
        )
        
        created = self.store.create(job)
        assert created.job_id == job.job_id
        
        retrieved = self.store.get("job_create")
        assert retrieved is not None
        assert retrieved.job_id == "job_create"
        
        not_found = self.store.get("nonexistent")
        assert not_found is None
    
    def test_list_jobs(self):
        """Test listing jobs with filters."""
        # Create multiple jobs
        jobs = [
            Job("job_1", "ws_1", JobType.RUN, {}, status=JobStatus.SUCCEEDED),
            Job("job_2", "ws_1", JobType.REPORT, {}, status=JobStatus.QUEUED),
            Job("job_3", "ws_2", JobType.RUN, {}, status=JobStatus.SUCCEEDED),
            Job("job_4", "ws_1", JobType.HEDGE, {}, status=JobStatus.FAILED),
        ]
        
        for job in jobs:
            self.store.create(job)
        
        # List all
        all_jobs = self.store.list()
        assert len(all_jobs) == 4
        
        # Filter by workspace
        ws1_jobs = self.store.list(workspace_id="ws_1")
        assert len(ws1_jobs) == 3
        
        # Filter by type
        run_jobs = self.store.list(job_type=JobType.RUN)
        assert len(run_jobs) == 2
        
        # Filter by status
        succeeded_jobs = self.store.list(status=JobStatus.SUCCEEDED)
        assert len(succeeded_jobs) == 2
        
        # Combined filters
        ws1_run_jobs = self.store.list(workspace_id="ws_1", job_type=JobType.RUN)
        assert len(ws1_run_jobs) == 1
    
    def test_update_status(self):
        """Test updating job status."""
        job = Job("job_update", "ws_1", JobType.RUN, {})
        self.store.create(job)
        
        # Update to running
        updated = self.store.update_status("job_update", JobStatus.RUNNING)
        assert updated.status == JobStatus.RUNNING
        assert updated.started_at is not None
        
        # Update to succeeded
        result = {"output": "success"}
        updated = self.store.update_status("job_update", JobStatus.SUCCEEDED, result=result)
        assert updated.status == JobStatus.SUCCEEDED
        assert updated.result == result
        assert updated.completed_at is not None
    
    def test_delete(self):
        """Test deleting jobs."""
        job = Job("job_delete", "ws_1", JobType.RUN, {})
        self.store.create(job)
        
        assert self.store.get("job_delete") is not None
        
        deleted = self.store.delete("job_delete")
        assert deleted is True
        assert self.store.get("job_delete") is None
        
        # Delete non-existent
        deleted_again = self.store.delete("job_delete")
        assert deleted_again is False


class TestJobExecution:
    """Test job execution (DEMO mode)."""
    
    def setup_method(self):
        """Set up test environment."""
        import os
        os.environ["DEMO_MODE"] = "true"
    
    def teardown_method(self):
        """Clean up."""
        import os
        if "DEMO_MODE" in os.environ:
            del os.environ["DEMO_MODE"]
    
    def test_deterministic_job_lifecycle(self):
        """Test complete job lifecycle with deterministic IDs."""
        workspace_id = "test_workspace"
        payload = {"portfolio_id": "test_portfolio", "params": {}}
        version = "2.4.0"
        
        # Generate job ID
        job_id = generate_job_id(workspace_id, JobType.RUN.value, payload, version)
        
        # Same input should produce same ID
        job_id_again = generate_job_id(workspace_id, JobType.RUN.value, payload, version)
        assert job_id == job_id_again
        
        # Create job
        job = Job(
            job_id=job_id,
            workspace_id=workspace_id,
            job_type=JobType.RUN,
            payload=payload
        )
        
        assert job.status == JobStatus.QUEUED
        
        # Simulate status transitions
        job.status = JobStatus.RUNNING
        assert job.status == JobStatus.RUNNING
        
        job.status = JobStatus.SUCCEEDED
        assert job.status == JobStatus.SUCCEEDED
