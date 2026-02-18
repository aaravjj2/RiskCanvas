"""
Azure AI Foundry Provider for RiskCanvas v2.2+
Provides text generation via Azure AI Foundry with strict "numbers policy".
Model output cannot introduce numeric facts; must only reference computed fields.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class NumbersPolicyViolation(Exception):
    """Raised when model output invents numbers not present in inputs"""
    pass


class FoundryProvider:
    """
    Azure AI Foundry provider for orchestration agent text generation.
    Real mode uses Azure AI Foundry API (requires credentials).
    Mock mode returns deterministic responses for testing.
    """
    
    def __init__(self):
        self.mode = os.getenv("FOUNDRY_MODE", "mock").lower()
        self.endpoint = os.getenv("AZURE_FOUNDRY_ENDPOINT")
        self.api_key = os.getenv("AZURE_FOUNDRY_API_KEY")
        self.deployment_name = os.getenv("AZURE_FOUNDRY_DEPLOYMENT", "gpt-4")
        
        if self.mode == "real" and not (self.endpoint and self.api_key):
            raise ValueError(
                "FOUNDRY_MODE=real requires AZURE_FOUNDRY_ENDPOINT and AZURE_FOUNDRY_API_KEY"
            )
    
    def generate_text(
        self,
        prompt: str,
        context_data: Dict[str, Any],
        max_tokens: int = 500,
        temperature: float = 0.0
    ) -> str:
        """
        Generate text response using Azure AI Foundry.
        
        Args:
            prompt: Instruction prompt for the model
            context_data: Computed data that model can reference
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic)
        
        Returns:
            Generated text that only references context_data
        
        Raises:
            NumbersPolicyViolation: If output invents numbers
        """
        if self.mode == "mock":
            return self._mock_generate(prompt, context_data)
        else:
            return self._real_generate(prompt, context_data, max_tokens, temperature)
    
    def _mock_generate(self, prompt: str, context_data: Dict[str, Any]) -> str:
        """Mock generation for testing (deterministic)"""
        # Deterministic response based on prompt keywords
        if "portfolio" in prompt.lower():
            return f"Portfolio analysis completed with {context_data.get('asset_count', 0)} assets."
        elif "risk" in prompt.lower():
            return f"Risk analysis shows VaR of {context_data.get('var_value', 'N/A')}."
        elif "hedge" in prompt.lower():
            return f"Hedge recommendations generated for risk reduction."
        elif "report" in prompt.lower():
            return f"Report prepared with key metrics from analysis."
        else:
            return "Analysis completed successfully."
    
    def _real_generate(
        self,
        prompt: str,
        context_data: Dict[str, Any],
        max_tokens: int,
        temperature: float
    ) -> str:
        """
        Real generation via Azure AI Foundry API.
        Requires azure-ai-inference package.
        """
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
        except ImportError:
            raise ImportError(
                "azure-ai-inference package required for FOUNDRY_MODE=real. "
                "Install with: pip install azure-ai-inference"
            )
        
        client = ChatCompletionsClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key)
        )
        
        # Build system message with context data
        system_message = (
            "You are a risk analytics assistant. "
            "IMPORTANT: You must ONLY reference numbers from the provided context data. "
            "Never invent or calculate new numbers. "
            f"Context data: {json.dumps(context_data)}"
        )
        
        response = client.complete(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            model=self.deployment_name,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        output = response.choices[0].message.content
        
        # Validate numbers policy
        self._validate_numbers_policy(output, context_data)
        
        return output
    
    def _validate_numbers_policy(self, output: str, context_data: Dict[str, Any]) -> None:
        """
        Validate that output doesn't invent numbers.
        Simple heuristic: extract numbers from output and context, compare.
        Production implementation would be more sophisticated.
        """
        import re
        
        # Extract numbers from output
        output_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', output))
        
        # Extract numbers from context data (recursive)
        context_json = json.dumps(context_data)
        context_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', context_json))
        
        # Check if output has numbers not in context
        invented_numbers = output_numbers - context_numbers
        
        if invented_numbers:
            # Allow some common numbers (years, percentages like 95, 99)
            allowed = {'95', '99', '2024', '2025', '2026'}
            invented_numbers = invented_numbers - allowed
            
            if invented_numbers:
                raise NumbersPolicyViolation(
                    f"Model output contains numbers not in context: {invented_numbers}"
                )


# Global provider instance
_provider: Optional[FoundryProvider] = None


def get_foundry_provider() -> FoundryProvider:
    """Get or create global Foundry provider instance"""
    global _provider
    if _provider is None:
        _provider = FoundryProvider()
    return _provider


def generate_analysis_narrative(analysis: Dict[str, Any]) -> str:
    """Generate narrative text for analysis results"""
    provider = get_foundry_provider()
    
    prompt = (
        "Summarize the portfolio risk analysis results in 2-3 sentences. "
        "Reference the specific metrics provided."
    )
    
    context_data = {
        "total_pnl": analysis.get("metrics", {}).get("total_pnl"),
        "total_value": analysis.get("metrics", {}).get("total_value"),
        "asset_count": analysis.get("metrics", {}).get("asset_count"),
        "var_value": analysis.get("var", {}).get("var_value"),
        "var_method": analysis.get("var", {}).get("method"),
        "confidence_level": analysis.get("var", {}).get("confidence_level"),
    }
    
    return provider.generate_text(prompt, context_data)


def generate_report_summary(report_data: Dict[str, Any]) -> str:
    """Generate summary text for report"""
    provider = get_foundry_provider()
    
    prompt = "Create a brief executive summary of this report."
    
    return provider.generate_text(prompt, report_data)
