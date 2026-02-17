"""
Server-Sent Events (SSE) for real-time updates (v2.7+).

Provides live updates for jobs and runs without polling.
Supports deterministic replay in DEMO mode for testing.
"""
import asyncio
import json
from typing import AsyncGenerator, Dict, Any, Optional, List
from datetime import datetime
import os


class EventStream:
    """
    SSE event stream manager.
    Broadcasts events to all connected clients.
    """
    
    def __init__(self):
        self._subscribers: List[asyncio.Queue] = []
        self._demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        self._event_history: List[Dict[str, Any]] = []  # For demo replay
    
    async def subscribe(self) -> asyncio.Queue:
        """Subscribe to event stream."""
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue
    
    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from event stream."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)
    
    async def publish(self, event_type: str, data: Dict[str, Any]):
        """
        Publish event to all subscribers.
        
        Args:
            event_type: Event type (e.g., "job.status_changed")
            data: Event data payload
        """
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Store in history for demo replay
        if self._demo_mode:
            self._event_history.append(event)
        
        # Broadcast to all subscribers
        dead_queues = []
        for queue in self._subscribers:
            try:
                await asyncio.wait_for(queue.put(event), timeout=1.0)
            except asyncio.TimeoutError:
                dead_queues.append(queue)
        
        # Clean up dead subscribers
        for queue in dead_queues:
            self.unsubscribe(queue)
    
    def get_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get event history (DEMO mode only).
        
        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return
        
        Returns:
            List of events in chronological order
        """
        if not self._demo_mode:
            return []
        
        events = self._event_history
        
        if event_type:
            events = [e for e in events if e["type"] == event_type]
        
        return events[-limit:]


# Global event streams
_job_stream = EventStream()
_run_stream = EventStream()


def get_job_stream() -> EventStream:
    """Get job event stream."""
    return _job_stream


def get_run_stream() -> EventStream:
    """Get run event stream."""
    return _run_stream


async def sse_generator(queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    """
    Generate SSE-formatted messages from event queue.
    
    Args:
        queue: Event queue to consume
    
    Yields:
        SSE-formatted strings
    """
    try:
        while True:
            event = await queue.get()
            
            # Format as SSE
            event_str = f"event: {event['type']}\n"
            event_str += f"data: {json.dumps(event['data'])}\n"
            event_str += f"id: {event['timestamp']}\n\n"
            
            yield event_str
    
    except asyncio.CancelledError:
        # Client disconnected
        pass


async def emit_job_event(event_type: str, job_data: Dict[str, Any]):
    """
    Emit job-related event.
    
    Args:
        event_type: Event type (e.g., "job.created", "job.status_changed")
        job_data: Job data payload
    """
    stream = get_job_stream()
    await stream.publish(event_type, job_data)


async def emit_run_event(event_type: str, run_data: Dict[str, Any]):
    """
    Emit run-related event.
    
    Args:
        event_type: Event type (e.g., "run.created", "run.completed")
        run_data: Run data payload
    """
    stream = get_run_stream()
    await stream.publish(event_type, run_data)
