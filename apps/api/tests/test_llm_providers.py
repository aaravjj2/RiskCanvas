"""
Test suite for LLM providers
"""

import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.providers import (
    MockProvider,
    FoundryProvider,
    LLMFactory,
    generate_narrative
)


def test_mock_provider_generation():
    """Test MockProvider deterministic generation"""
    provider = MockProvider()
    
    # Test keyword-based responses
    response1 = provider.generate("Please analyze this portfolio")
    assert "analyze" in response1.lower() or "portfolio" in response1.lower()
    
    response2 = provider.generate("Calculate risk metrics")
    assert "risk" in response2.lower()
    
    # Test determinism
    results = [provider.generate("analyze portfolio") for _ in range(5)]
    assert len(set(results)) == 1  # All identical


def test_mock_provider_chat():
    """Test MockProvider chat interface"""
    provider = MockProvider()
    
    messages = [
        {"role": "system", "content": "You are a risk analyst"},
        {"role": "user", "content": "Analyze my portfolio"}
    ]
    
    response = provider.chat(messages)
    assert isinstance(response, str)
    assert len(response) > 0


def test_mock_provider_always_available():
    """Test MockProvider is always available"""
    provider = MockProvider()
    assert provider.is_available()


def test_foundry_provider_without_credentials():
    """Test FoundryProvider without credentials"""
    # Ensure no credentials in env
    old_endpoint = os.getenv("FOUNDRY_ENDPOINT")
    old_key = os.getenv("FOUNDRY_API_KEY")
    
    if old_endpoint:
        del os.environ["FOUNDRY_ENDPOINT"]
    if old_key:
        del os.environ["FOUNDRY_API_KEY"]
    
    try:
        provider = FoundryProvider()
        assert not provider.is_available()
        
        # Should raise error when trying to generate
        with pytest.raises(RuntimeError, match="not configured"):
            provider.generate("test prompt")
    
    finally:
        # Restore
        if old_endpoint:
            os.environ["FOUNDRY_ENDPOINT"] = old_endpoint
        if old_key:
            os.environ["FOUNDRY_API_KEY"] = old_key


def test_foundry_provider_with_mock_credentials():
    """Test FoundryProvider with mock credentials (placeholder mode)"""
    os.environ["FOUNDRY_ENDPOINT"] = "https://test.openai.azure.com"
    os.environ["FOUNDRY_API_KEY"] = "test-key-12345"
    
    try:
        provider = FoundryProvider()
        
        # In placeholder mode, it should be "available" but return placeholder responses
        assert provider.endpoint == "https://test.openai.azure.com"
        assert provider.api_key == "test-key-12345"
        
        # The actual availability depends on whether client initialization succeeds
        # In this test environment without real SDK, it will use placeholder
    
    finally:
        # Clean up
        del os.environ["FOUNDRY_ENDPOINT"]
        del os.environ["FOUNDRY_API_KEY"]


def test_llm_factory_auto_detect_demo_mode():
    """Test LLMFactory auto-detects DEMO mode"""
    os.environ["DEMO_MODE"] = "true"
    
    try:
        provider = LLMFactory.create_provider()
        assert isinstance(provider, MockProvider)
    
    finally:
        if "DEMO_MODE" in os.environ:
            del os.environ["DEMO_MODE"]


def test_llm_factory_mock_provider():
    """Test LLMFactory creates MockProvider"""
    os.environ["DEMO_MODE"] = "false"
    
    try:
        provider = LLMFactory.create_provider("mock")
        assert isinstance(provider, MockProvider)
        assert provider.is_available()
    
    finally:
        if "DEMO_MODE" in os.environ:
            del os.environ["DEMO_MODE"]


def test_llm_factory_foundry_fallback():
    """Test LLMFactory falls back to Mock when Foundry unavailable"""
    os.environ["DEMO_MODE"] = "false"
    
    # Ensure no Foundry credentials
    old_endpoint = os.getenv("FOUNDRY_ENDPOINT")
    old_key = os.getenv("FOUNDRY_API_KEY")
    
    if old_endpoint:
        del os.environ["FOUNDRY_ENDPOINT"]
    if old_key:
        del os.environ["FOUNDRY_API_KEY"]
    
    try:
        provider = LLMFactory.create_provider("foundry")
        # Should fall back to MockProvider
        assert isinstance(provider, MockProvider)
    
    finally:
        if old_endpoint:
            os.environ["FOUNDRY_ENDPOINT"] = old_endpoint
        if old_key:
            os.environ["FOUNDRY_API_KEY"] = old_key
        if "DEMO_MODE" in os.environ:
            del os.environ["DEMO_MODE"]


def test_llm_factory_default_provider():
    """Test LLMFactory.get_default_provider()"""
    os.environ["DEMO_MODE"] = "true"
    
    try:
        provider = LLMFactory.get_default_provider()
        assert isinstance(provider, MockProvider)
    
    finally:
        if "DEMO_MODE" in os.environ:
            del os.environ["DEMO_MODE"]


def test_generate_narrative_utility():
    """Test generate_narrative utility function"""
    os.environ["DEMO_MODE"] = "true"
    
    try:
        response = generate_narrative("Analyze this portfolio for risk")
        assert isinstance(response, str)
        assert len(response) > 0
    
    finally:
        if "DEMO_MODE" in os.environ:
            del os.environ["DEMO_MODE"]


def test_provider_selection_logic():
    """Test provider selection logic is correct and safe"""
    os.environ["DEMO_MODE"] = "true"
    
    try:
        # In DEMO mode, should always get Mock
        provider = LLMFactory.create_provider()
        assert isinstance(provider, MockProvider)
        
        # Even if we explicitly ask for Foundry in DEMO mode
        provider = LLMFactory.create_provider("foundry")
        assert isinstance(provider, MockProvider)
    
    finally:
        if "DEMO_MODE" in os.environ:
            del os.environ["DEMO_MODE"]


def test_determinism_in_demo_mode():
    """Test that DEMO mode outputs are deterministic"""
    os.environ["DEMO_MODE"] = "true"
    
    try:
        provider = LLMFactory.get_default_provider()
        
        # Generate same prompt multiple times
        results = [provider.generate("analyze portfolio risk") for _ in range(10)]
        
        # All should be identical
        assert len(set(results)) == 1
    
    finally:
        if "DEMO_MODE" in os.environ:
            del os.environ["DEMO_MODE"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
