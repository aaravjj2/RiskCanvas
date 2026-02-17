"""
Tests for SSE (Server-Sent Events) functionality (v2.7+).
"""
import pytest
import asyncio
from sse import (
    EventStream,
    get_job_stream,
    get_run_stream,
    sse_generator,
    emit_job_event,
    emit_run_event
)


class TestEventStream:
    """Test EventStream pub/sub functionality."""
    
    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self):
        """Test subscribing and receiving events."""
        stream = EventStream()
        queue = await stream.subscribe()
        
        # Publish event
        await stream.publish("test.event", {"foo": "bar"})
        
        # Receive event
        event = await asyncio.wait_for(queue.get(), timeout=1.0)
        
        assert event["type"] == "test.event"
        assert event["data"] == {"foo": "bar"}
        assert "timestamp" in event
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self):
        """Test multiple subscribers receive same event."""
        stream = EventStream()
        queue1 = await stream.subscribe()
        queue2 = await stream.subscribe()
        
        # Publish event
        await stream.publish("test.event", {"value": 123})
        
        # Both should receive
        event1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
        event2 = await asyncio.wait_for(queue2.get(), timeout=1.0)
        
        assert event1["type"] == "test.event"
        assert event2["type"] == "test.event"
        assert event1["data"] == event2["data"]
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """Test unsubscribing from stream."""
        stream = EventStream()
        queue = await stream.subscribe()
        
        # Unsubscribe
        stream.unsubscribe(queue)
        
        # Publish event - should not be received
        await stream.publish("test.event", {"foo": "bar"})
        
        # Queue should be empty
        assert queue.empty()
    
    def test_get_history_demo_mode(self):
        """Test event history in DEMO mode."""
        import os
        old_demo_mode = os.getenv("DEMO_MODE")
        os.environ["DEMO_MODE"] = "true"
        
        try:
            stream = EventStream()
            
            # Publish some events (need to run async)
            async def publish_events():
                await stream.publish("test.event1", {"n": 1})
                await stream.publish("test.event2", {"n": 2})
                await stream.publish("test.event1", {"n": 3})
            
            asyncio.run(publish_events())
            
            # Get all history
            history = stream.get_history()
            assert len(history) == 3
            
            # Filter by type
            type1_history = stream.get_history(event_type="test.event1")
            assert len(type1_history) == 2
            
            # Limit
            limited = stream.get_history(limit=2)
            assert len(limited) == 2
        
        finally:
            if old_demo_mode:
                os.environ["DEMO_MODE"] = old_demo_mode
            else:
                del os.environ["DEMO_MODE"]


class TestSSEGenerator:
    """Test SSE message formatting."""
    
    @pytest.mark.asyncio
    async def test_sse_format(self):
        """Test SSE message format."""
        queue = asyncio.Queue()
        
        # Put test event
        event = {
            "type": "test.event",
            "data": {"key": "value"},
            "timestamp": "2024-01-01T00:00:00Z"
        }
        await queue.put(event)
        
        # Generate SSE message
        gen = sse_generator(queue)
        message = await anext(gen)
        
        # Check SSE format
        assert "event: test.event\n" in message
        assert "data: {\"key\": \"value\"}\n" in message
        assert "id: 2024-01-01T00:00:00Z\n\n" in message


class TestJobEvents:
    """Test job-specific event helpers."""
    
    @pytest.mark.asyncio
    async def test_emit_job_event(self):
        """Test emitting job events."""
        stream = get_job_stream()
        queue = await stream.subscribe()
        
        # Emit job event
        job_data = {
            "job_id": "test_job",
            "status": "running",
            "job_type": "run"
        }
        await emit_job_event("job.status_changed", job_data)
        
        # Receive event
        event = await asyncio.wait_for(queue.get(), timeout=1.0)
        
        assert event["type"] == "job.status_changed"
        assert event["data"]["job_id"] == "test_job"
        assert event["data"]["status"] == "running"
        
        stream.unsubscribe(queue)


class TestRunEvents:
    """Test run-specific event helpers."""
    
    @pytest.mark.asyncio
    async def test_emit_run_event(self):
        """Test emitting run events."""
        stream = get_run_stream()
        queue = await stream.subscribe()
        
        # Emit run event
        run_data = {
            "run_id": "test_run",
            "portfolio_id": "port_123",
            "status": "completed"
        }
        await emit_run_event("run.created", run_data)
        
        # Receive event
        event = await asyncio.wait_for(queue.get(), timeout=1.0)
        
        assert event["type"] == "run.created"
        assert event["data"]["run_id"] == "test_run"
        assert event["data"]["portfolio_id"] == "port_123"
        
        stream.unsubscribe(queue)
