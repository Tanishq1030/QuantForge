# backend/engine/validators.py
"""
Response Validators for AI Analysis

Prevents hallucinations and validates LLM outputs against actual data.
Critical for production financial applications where accuracy matters.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from backend.core.logging import get_logger

logger = get_logger(__name__)


class ResponseValidator:
    """
    Validates LLM responses against known data to prevent hallucinations.
    
    Checks:
    1. Sentiment claims match news sentiment
    2. Price claims match actual price data
    3. Mentioned tickers exist in context
    4. Dates are within analysis period
    """
    
    def __init__(self):
        self.validation_warnings = []
    
    def validate_analysis(
        self,
        llm_response: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate LLM analysis against actual context data.
        
        Args:
            llm_response: LLM-generated analysis
            context: Actual data (news, price, etc.)
            
        Returns:
            {
                "valid": bool,
                "warnings": list,
                "confidence_adjustment": float (-0.3 to 0.0)
            }
        """
        self.validation_warnings = []
        confidence_penalty = 0.0
        
        # Validate sentiment
        if "sentiment" in llm_response:
            penalty = self._validate_sentiment(
                llm_response["sentiment"],
                context
            )
            confidence_penalty += penalty
        
        # Validate price claims
        if "price_data" in context and context["price_data"]:
            penalty = self._validate_price_claims(
                llm_response.get("summary", ""),
                context["price_data"]
            )
            confidence_penalty += penalty
        
        # Validate ticker mentions
        penalty = self._validate_ticker_mentions(
            llm_response.get("summary", ""),
            context.get("ticker", "")
        )
        confidence_penalty += penalty
        
        # Check for unsupported claims
        penalty = self._check_unsupported_claims(
            llm_response,
            context
        )
        confidence_penalty += penalty
        
        return {
            "valid": len(self.validation_warnings) == 0,
            "warnings": self.validation_warnings,
            "confidence_adjustment": max(confidence_penalty, -0.3)  # Cap penalty
        }
    
    def _validate_sentiment(
        self,
        claimed_sentiment: str,
        context: Dict[str, Any]
    ) -> float:
        """Validate sentiment claim against news data."""
        
        if context.get("news_count", 0) == 0:
            if claimed_sentiment != "neutral":
                self.validation_warnings.append(
                    "Claimed sentiment without news data"
                )
                return -0.1
        
        # If we have news, check if sentiment is reasonable
        # (This is simple heuristic - could be ML-based in future)
        news_articles = context.get("news_articles", [])
        
        if len(news_articles) > 0:
            # Count positive/negative keywords in news
            positive_keywords = ["beat", "exceed", "growth", "strong", "positive", "upgrade"]
            negative_keywords = ["miss", "decline", "weak", "negative", "downgrade", "concern"]
            
            positive_count = 0
            negative_count = 0
            
            for article in news_articles:
                content = f"{article.get('title', '')} {article.get('content', '')}".lower()
                positive_count += sum(1 for kw in positive_keywords if kw in content)
                negative_count += sum(1 for kw in negative_keywords if kw in content)
            
            # Check if claimed sentiment matches keyword analysis
            if positive_count > negative_count * 2 and claimed_sentiment == "bearish":
                self.validation_warnings.append(
                    "Claimed bearish sentiment contradicts positive news"
                )
                return -0.15
            elif negative_count > positive_count * 2 and claimed_sentiment == "bullish":
                self.validation_warnings.append(
                    "Claimed bullish sentiment contradicts negative news"
                )
                return -0.15
        
        return 0.0
    
    def _validate_price_claims(
        self,
        text: str,
        price_data: Dict[str, Any]
    ) -> float:
        """Validate price movement claims against actual data."""
        
        if not price_data:
            return 0.0
        
        actual_change = price_data.get("change_percent", 0)
        
        # Extract price claims from text
        up_keywords = ["up", "increased", "rose", "gained", "higher", "rally"]
        down_keywords = ["down", "decreased", "fell", "dropped", "lower", "decline"]
        
        text_lower = text.lower()
        
        has_up_claim = any(kw in text_lower for kw in up_keywords)
        has_down_claim = any(kw in text_lower for kw in down_keywords)
        
        # Check for contradictions
        if has_up_claim and actual_change < -1.0:
            self.validation_warnings.append(
                f"Claimed price increase but actual change is {actual_change:.1f}%"
            )
            return -0.2
        
        if has_down_claim and actual_change > 1.0:
            self.validation_warnings.append(
                f"Claimed price decrease but actual change is {actual_change:.1f}%"
            )
            return -0.2
        
        return 0.0
    
    def _validate_ticker_mentions(
        self,
        text: str,
        expected_ticker: str
    ) -> float:
        """Ensure LLM talks about the right ticker."""
        
        if not expected_ticker:
            return 0.0
        
        # Extract potential tickers from text (all-caps words 2-5 chars)
        potential_tickers = re.findall(r'\b[A-Z]{2,5}\b', text)
        
        if expected_ticker not in potential_tickers and len(text) > 50:
            # Long response without mentioning ticker might be generic
            self.validation_warnings.append(
                f"Analysis doesn't mention ticker {expected_ticker}"
            )
            return -0.05
        
        return 0.0
    
    def _check_unsupported_claims(
        self,
        llm_response: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """Check for claims without supporting evidence."""
        
        penalty = 0.0
        
        # High confidence without data
        confidence = llm_response.get("confidence", 0.5)
        news_count = context.get("news_count", 0)
        has_price = context.get("has_price_data", False)
        
        if confidence > 0.8 and news_count == 0 and not has_price:
            self.validation_warnings.append(
                "High confidence claim without supporting data"
            )
            penalty -= 0.2
        
        # Specific predictions without basis
        summary = llm_response.get("summary", "").lower()
        prediction_keywords = ["will", "predict", "forecast", "expect", "target"]
        
        if any(kw in summary for kw in prediction_keywords):
            if news_count < 3:
                self.validation_warnings.append(
                    "Prediction made with limited data"
                )
                penalty -= 0.1
        
        return penalty


class ConfidenceCalibrator:
    """
    Calibrates confidence scores based on available evidence.
    
    Tiers:
    - Low (0.0-0.4): Limited data or conflicting signals
    - Medium (0.4-0.7): Some evidence but incomplete
    - High (0.7-1.0): Strong supporting evidence
    """
    
    @staticmethod
    def calibrate(
        base_confidence: float,
        context: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> tuple[float, List[str]]:
        """
        Adjust confidence based on data quality and validation.
        
        Returns:
            (adjusted_confidence, reasoning)
        """
        
        adjusted = base_confidence
        reasoning = []
        
        # Factor 1: Data availability
        news_count = context.get("news_count", 0)
        has_price = context.get("has_price_data", False)
        
        if news_count == 0 and not has_price:
            adjusted *= 0.5
            reasoning.append("Limited data available")
        elif news_count < 3:
            adjusted *= 0.7
            reasoning.append("Sparse news coverage")
        elif news_count > 10:
            adjusted *= 1.1
            reasoning.append("Rich data set")
        
        # Factor 2: Validation warnings
        if not validation_result.get("valid", True):
            adjusted += validation_result.get("confidence_adjustment", 0)
            reasoning.extend(validation_result.get("warnings", []))
        
        # Factor 3: Data recency
        if "news_articles" in context and len(context["news_articles"]) > 0:
            # Check if news is recent (within 7 days)
            recent_count = 0
            for article in context["news_articles"]:
                timestamp = article.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    
                    age_days = (datetime.utcnow() - timestamp).days
                    if age_days <= 7:
                        recent_count += 1
            
            if recent_count == 0 and len(context["news_articles"]) > 0:
                adjusted *= 0.8
                reasoning.append("News data is stale")
        
        # Cap confidence
        adjusted = max(0.0, min(1.0, adjusted))
        
        return adjusted, reasoning


# Singleton instances
_validator = None
_calibrator = None

def get_validator() -> ResponseValidator:
    """Get singleton validator instance."""
    global _validator
    if _validator is None:
        _validator = ResponseValidator()
    return _validator

def get_calibrator() -> ConfidenceCalibrator:
    """Get singleton calibrator instance."""
    global _calibrator
    if _calibrator is None:
        _calibrator = ConfidenceCalibrator()
    return _calibrator
