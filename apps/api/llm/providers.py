"""
LLM Provider Interface for Microsoft Foundry and Mock Provider
"""

import os
import json
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        pass
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat response"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available/configured"""
        pass


class MockProvider(LLMProvider):
    """
    Mock LLM provider for deterministic testing and DEMO mode.
    Returns pre-defined responses based on prompt keywords.
    """
    
    def __init__(self):
        self.responses = {
            "analyze": "Based on the portfolio analysis, I recommend monitoring the delta exposure and implementing appropriate hedging strategies.",
            "risk": "The portfolio shows moderate risk with VaR at 95% confidence level. Consider diversification to reduce concentration risk.",
            "scenario": "Under the stress test scenarios, the portfolio demonstrates resilience to moderate market shocks but may require hedging for extreme events.",
            "report": "Portfolio Summary: The analysis indicates balanced exposure with opportunities for optimization through strategic rebalancing.",
            "default": "Analysis complete. The portfolio metrics are within acceptable risk parameters."
        }
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate deterministic response based on prompt keywords"""
        prompt_lower = prompt.lower()
        
        for keyword, response in self.responses.items():
            if keyword in prompt_lower:
                return response
        
        return self.responses["default"]
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat response from messages"""
        # Get last user message
        user_messages = [m["content"] for m in messages if m.get("role") == "user"]
        if user_messages:
            return self.generate(user_messages[-1], **kwargs)
        return self.responses["default"]
    
    def is_available(self) -> bool:
        """Mock provider is always available"""
        return True


class FoundryProvider(LLMProvider):
    """
    Microsoft Foundry provider.
    Real integration via Azure AI Foundry SDK (activated only when env vars exist).
    """
    
    def __init__(self):
        self.endpoint = os.getenv("FOUNDRY_ENDPOINT")
        self.api_key = os.getenv("FOUNDRY_API_KEY")
        self.deployment = os.getenv("FOUNDRY_DEPLOYMENT", "gpt-4")
        self.client = None
        
        # Only import and initialize if credentials exist
        if self.endpoint and self.api_key:
            try:
                # Real Azure OpenAI SDK import (would be in production)
                # from openai import AzureOpenAI
                # self.client = AzureOpenAI(
                #     azure_endpoint=self.endpoint,
                #     api_key=self.api_key,
                #     api_version="2024-02-15-preview"
                # )
                
                # For now, we'll use a placeholder
                self.client = "FOUNDRY_CLIENT_PLACEHOLDER"
            except Exception as e:
                print(f"Warning: Failed to initialize Foundry client: {e}")
                self.client = None
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Foundry"""
        if not self.is_available():
            raise RuntimeError("Foundry provider not configured. Set FOUNDRY_ENDPOINT and FOUNDRY_API_KEY env vars.")
        
        # Real implementation would call:
        # response = self.client.completions.create(
        #     model=self.deployment,
        #     prompt=prompt,
        #     max_tokens=kwargs.get("max_tokens", 500),
        #     temperature=kwargs.get("temperature", 0.7)
        # )
        # return response.choices[0].text
        
        # Placeholder for demo (would be replaced with real SDK call)
        return f"[Foundry Response to: {prompt[:50]}...]"
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat response using Foundry"""
        if not self.is_available():
            raise RuntimeError("Foundry provider not configured.")
        
        # Real implementation would call:
        # response = self.client.chat.completions.create(
        #     model=self.deployment,
        #     messages=messages,
        #     max_tokens=kwargs.get("max_tokens", 500),
        #     temperature=kwargs.get("temperature", 0.7)
        # )
        # return response.choices[0].message.content
        
        # Placeholder for demo
        return f"[Foundry Chat Response]"
    
    def is_available(self) -> bool:
        """Check if Foundry is configured and available"""
        return self.client is not None and self.endpoint is not None and self.api_key is not None


class LLMFactory:
    """Factory for creating LLM providers"""
    
    @staticmethod
    def create_provider(provider_type: Optional[str] = None) -> LLMProvider:
        """
        Create LLM provider based on type or environment.
        
        Args:
            provider_type: "foundry", "mock", or None (auto-detect)
        
        Returns:
            LLMProvider instance
        """
        # Auto-detect if not specified
        if provider_type is None:
            provider_type = os.getenv("LLM_PROVIDER", "mock").lower()
        
        # In DEMO/test mode, always use mock
        demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"
        if demo_mode:
            return MockProvider()
        
        if provider_type == "foundry":
            foundry = FoundryProvider()
            if not foundry.is_available():
                print("Warning: Foundry not configured, falling back to MockProvider")
                return MockProvider()
            return foundry
        elif provider_type == "mock":
            return MockProvider()
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
    
    @staticmethod
    def get_default_provider() -> LLMProvider:
        """Get default provider (respects DEMO_MODE)"""
        return LLMFactory.create_provider()


def generate_narrative(prompt: str, provider: Optional[LLMProvider] = None) -> str:
    """
    Utility function to generate narrative using configured provider.
    
    Args:
        prompt: Input prompt
        provider: Optional provider instance (uses default if None)
    
    Returns:
        Generated narrative
    """
    if provider is None:
        provider = LLMFactory.get_default_provider()
    
    return provider.generate(prompt)
