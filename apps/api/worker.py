"""
Worker entrypoint for RiskCanvas job execution (v2.6+).

Polls job queue for QUEUED jobs and executes them asynchronously.
Supports graceful shutdown and configurable polling intervals.

Usage:
    python -m apps.api.worker

Environment Variables:
    JOB_STORE_BACKEND: "memory" or "sqlite" (default: memory)
    DEMO_MODE: "true" or "false" (default: false)
    WORKER_POLL_INTERVAL: Seconds between polls (default: 5)
    WORKER_MAX_RETRIES: Max retries for failed jobs (default: 0)
"""
import os
import sys
import time
import signal
from pathlib import Path
from typing import Optional

# Ensure API directory is in path
api_dir = Path(__file__).parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from jobs import (
    Job,
    JobType,
    JobStatus,
    get_job_store,
    get_job_store_backend,
    execute_job_inline
)


class Worker:
    """Job worker that polls queue and executes jobs."""
    
    def __init__(
        self,
        poll_interval: float = 5.0,
        max_retries: int = 0
    ):
        """
        Initialize worker.
        
        Args:
            poll_interval: Seconds to wait between polling cycles
            max_retries: Maximum retries for failed jobs (not implemented yet)
        """
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.running = False
        self.job_store = get_job_store()
        self.backend = get_job_store_backend()
        
        # Demo mode check
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        
        if not self.demo_mode:
            print("WARNING: Worker is running in PRODUCTION mode but job execution requires DEMO_MODE=true")
    
    def start(self):
        """Start worker polling loop."""
        self.running = True
        
        print(f"🚀 RiskCanvas Worker v2.6 started")
        print(f"   Job Store Backend: {self.backend}")
        print(f"   Demo Mode: {self.demo_mode}")
        print(f"   Poll Interval: {self.poll_interval}s")
        print(f"   Waiting for jobs...")
        print()
        
        try:
            while self.running:
                self._poll_and_execute()
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("\n⏸  Worker interrupted by user")
        finally:
            self.stop()
    
    def stop(self):
        """Stop worker gracefully."""
        if self.running:
            print("🛑 Worker stopped")
            self.running = False
    
    def _poll_and_execute(self):
        """Poll for queued jobs and execute them."""
        try:
            # Get all queued jobs
            queued_jobs = self.job_store.list(status=JobStatus.QUEUED, limit=10)
            
            if not queued_jobs:
                return  # No jobs to process
            
            for job in queued_jobs:
                print(f"📋 Processing job {job.job_id} (type={job.job_type.value})")
                self._execute_job(job)
        
        except Exception as e:
            print(f"❌ Error during polling: {e}")
    
    def _execute_job(self, job: Job):
        """
        Execute a single job.
        
        Args:
            job: Job to execute
        """
        try:
            # Update status to RUNNING
            self.job_store.update_status(job.job_id, JobStatus.RUNNING)
            print(f"   ⏳ Job {job.job_id} started...")
            
            # Execute job
            result = execute_job_inline(job)
            
            # Update status to SUCCEEDED
            self.job_store.update_status(job.job_id, JobStatus.SUCCEEDED, result=result)
            print(f"   ✅ Job {job.job_id} succeeded")
        
        except Exception as e:
            # Update status to FAILED
            error_message = str(e)
            self.job_store.update_status(job.job_id, JobStatus.FAILED, error=error_message)
            print(f"   ❌ Job {job.job_id} failed: {error_message}")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print("\n⚠️  Received shutdown signal")
    sys.exit(0)


def main():
    """Main worker entrypoint."""
    # Parse environment variables
    poll_interval = float(os.getenv("WORKER_POLL_INTERVAL", "5.0"))
    max_retries = int(os.getenv("WORKER_MAX_RETRIES", "0"))
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start worker
    worker = Worker(
        poll_interval=poll_interval,
        max_retries=max_retries
    )
    
    try:
        worker.start()
    except Exception as e:
        print(f"💥 Worker crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
