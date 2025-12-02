# backend/engine/llm/prompts.py
"""
Prompt Template Manager

Versioned prompts for different analysis types.
Follows production MLOps best practices.
"""

from typing import Dict, Any, Optional
from enum import Enum


class PromptType(str, Enum):
    """Available prompt types"""
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    PRICE_EXPLANATION = "price_explanation"
    RISK_ASSESSMENT = "risk_assessment"
    RECOMMENDATION = "recommendation"
    MARKET_SUMMARY = "market_summary"


class PromptManager:
    """
    Manages prompt templates for different analysis tasks.
    
    Usage:
        pm = PromptManager()
        prompt = pm.get_prompt(
            PromptType.SENTIMENT_ANALYSIS,
            ticker="AAPL",
            news="Apple reports earnings..."
        )
    """
    
    # Version tracking for A/B testing
    VERSION = "v1"
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[PromptType, Dict[str, str]]:
        """Load all prompt templates."""
        return {
            PromptType.SENTIMENT_ANALYSIS: {
                "system": "You are an expert financial analyst. Analyze sentiment objectively based on facts.",
                "template": """Analyze the sentiment of the following financial news about {ticker}:

News Articles:
{news_text}

Provide:
1. Overall sentiment (bullish/bearish/neutral)
2. Confidence score (0.0 to 1.0)
3. Key themes (3-5 bullet points)
4. Potential market impact

Respond in JSON format:
{{
    "sentiment": "bullish/bearish/neutral",
    "confidence": 0.85,
    "themes": ["theme1", "theme2", "theme3"],
    "impact": "short explanation"
}}"""
            },
            
            PromptType.PRICE_EXPLANATION: {
                "system": "You are a professional market researcher. Explain price movements using factual analysis.",
                "template": """Explain why {ticker} price moved as follows:

Price Data:
- Period: {start_date} to {end_date}
- Open: ${open_price}
- Close: ${close_price}
- High: ${high_price}
- Low: ${low_price}
- Change: {price_change}%

Recent News:
{news_summary}

Provide:
1. Primary drivers of price movement
2. Technical factors (if applicable)
3. Macro/market factors
4. Confidence in explanation (0.0 to 1.0)

Respond in JSON format:
{{
    "primary_drivers": ["driver1", "driver2"],
    "technical_factors": ["factor1", "factor2"],
    "macro_factors": ["macro1", "macro2"],
    "confidence": 0.80
}}"""
            },
            
            PromptType.RISK_ASSESSMENT: {
                "system": "You are a risk analyst. Assess risks objectively without speculation.",
                "template": """Assess the investment risk for {ticker}:

Recent News:
{news_text}

Price Volatility:
- 7-day volatility: {volatility_7d}%
- 30-day volatility: {volatility_30d}%

Market Context:
{market_context}

Provide:
1. Overall risk level (low/medium/high)
2. Specific risk factors (3-5 items)
3. Risk score (0.0 = no risk, 1.0 = extreme risk)
4. Mitigation suggestions

Respond in JSON format:
{{
    "risk_level": "medium",
    "risk_score": 0.65,
    "risk_factors": ["factor1", "factor2", "factor3"],
    "mitigations": ["mitigation1", "mitigation2"]
}}"""
            },
            
            PromptType.RECOMMENDATION: {
                "system": "You are a portfolio analyst. Provide balanced guidance based on data, NOT direct financial advice.",
                "template": """Based on this analysis of {ticker}, provide guidance:

Analysis Summary:
{analysis_summary}

Current Price: ${current_price}
Sentiment: {sentiment}
Risk Level: {risk_level}

Provide:
1. Suggested action (BUY/HOLD/SELL/WAIT)
2. Rationale (3-5 bullet points)
3. Confidence level (0.0 to 1.0)
4. Key considerations

IMPORTANT: Frame as informational guidance, NOT direct financial advice.

Respond in JSON format:
{{
    "action": "HOLD",
    "rationale": ["reason1", "reason2", "reason3"],
    "confidence": 0.75,
    "considerations": ["consider1", "consider2"]
}}"""
            },
            
            PromptType.MARKET_SUMMARY: {
                "system": "You are a financial journalist. Summarize market events clearly and concisely.",
                "template": """Summarize this market event for {ticker}:

Event Details:
{event_text}

Price Impact:
{price_impact}

Provide a concise summary (under 150 words) covering:
1. What happened
2. Why it matters
3. Immediate market reaction

Respond in JSON format:
{{
    "summary": "concise summary text here",
    "key_points": ["point1", "point2", "point3"]
}}"""
            }
        }
    
    def get_prompt(
        self,
        prompt_type: PromptType,
        **kwargs
    ) -> Dict[str, str]:
        """
        Get formatted prompt for a task.
        
        Args:
            prompt_type: Type of analysis prompt
            **kwargs: Variables to fill in template
            
        Returns:
            {
                "system": "system message",
                "user": "formatted prompt"
            }
        """
        if prompt_type not in self.templates:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
        
        template = self.templates[prompt_type]
        
        try:
            formatted_prompt = template["template"].format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {e}")
        
        return {
            "system": template["system"],
            "user": formatted_prompt,
            "version": self.VERSION
        }
    
    def get_available_types(self) -> list:
        """Get list of available prompt types."""
        return [pt.value for pt in PromptType]


# Singleton instance
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """Get singleton PromptManager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
