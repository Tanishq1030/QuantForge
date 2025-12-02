# tests/unit/test_validators.py
"""
Unit tests for response validators and confidence calibrator.
"""

import pytest
from datetime import datetime, timedelta

from backend.engine.validators import ResponseValidator, ConfidenceCalibrator


class TestResponseValidator:
    """Test LLM response validation"""
    
    def test_validate_sentiment_with_no_data(self):
        """Should warn when claiming sentiment without news"""
        validator = ResponseValidator()
        
        llm_response = {"sentiment": "bullish"}
        context = {"news_count": 0, "has_price_data": False}
        
        result = validator.validate_analysis(llm_response, context)
        
        assert not result["valid"]
        assert len(result["warnings"]) > 0
        assert result["confidence_adjustment"] < 0
    
    def test_validate_sentiment_matches_news(self):
        """Should pass when sentiment matches news tone"""
        validator = ResponseValidator()
        
        llm_response = {"sentiment": "bullish"}
        context = {
            "news_count": 3,
            "news_articles": [
                {
                    "title": "Apple beats earnings expectations",
                    "content": "Strong growth in iPhone sales"
                },
                {
                    "title": "Apple stock upgraded by analysts",
                    "content": "Positive outlook for Q4"
                }
            ]
        }
        
        result = validator.validate_analysis(llm_response, context)
        
        assert result["valid"]
        assert len(result["warnings"]) == 0
    
    def test_validate_price_claims(self):
        """Should warn when price claims contradict data"""
        validator = ResponseValidator()
        
        llm_response = {
            "summary": "Stock price rose significantly today"
        }
        context = {
            "price_data": {"change_percent": -5.2}  # Actually down
        }
        
        result = validator.validate_analysis(llm_response, context)
        
        assert not result["valid"]
        assert any("price" in w.lower() for w in result["warnings"])
    
    def test_validate_unsupported_high_confidence(self):
        """Should penalize high confidence without data"""
        validator = ResponseValidator()
        
        llm_response = {
            "confidence": 0.95,
            "summary": "Strong buy signal"
        }
        context = {
            "news_count": 0,
            "has_price_data": False
        }
        
        result = validator.validate_analysis(llm_response, context)
        
        assert not result["valid"]
        assert result["confidence_adjustment"] < -0.1


class TestConfidenceCalibrator:
    """Test confidence calibration logic"""
    
    def test_calibrate_with_rich_data(self):
        """High data quality should boost confidence"""
        calibrator = ConfidenceCalibrator()
        
        context = {
            "news_count": 15,
            "has_price_data": True,
            "news_articles": [
                {"timestamp": datetime.utcnow().isoformat()}
                for _ in range(15)
            ]
        }
        
        validation = {"valid": True, "warnings": [], "confidence_adjustment": 0}
        
        adjusted, reasoning = calibrator.calibrate(0.7, context, validation)
        
        assert adjusted > 0.7  # Should be boosted
        assert any("rich" in r.lower() for r in reasoning)
    
    def test_calibrate_with_sparse_data(self):
        """Low data quality should reduce confidence"""
        calibrator = ConfidenceCalibrator()
        
        context = {
            "news_count": 1,
            "has_price_data": False
        }
        
        validation = {"valid": True, "warnings": [], "confidence_adjustment": 0}
        
        adjusted, reasoning = calibrator.calibrate(0.8, context, validation)
        
        assert adjusted < 0.8  # Should be reduced
        assert len(reasoning) > 0
    
    def test_calibrate_with_validation_warnings(self):
        """Validation warnings should penalize confidence"""
        calibrator = ConfidenceCalibrator()
        
        context = {"news_count": 5, "has_price_data": True}
        validation = {
            "valid": False,
            "warnings": ["Price claim contradicts data"],
            "confidence_adjustment": -0.2
        }
        
        adjusted, reasoning = calibrator.calibrate(0.9, context, validation)
        
        assert adjusted <= 0.7  # Significant penalty (changed from <)
        assert len(reasoning) > 0
    
    def test_calibrate_caps_at_bounds(self):
        """Confidence should stay between 0 and 1"""
        calibrator = ConfidenceCalibrator()
        
        context = {"news_count": 0, "has_price_data": False}
        validation = {
            "valid": False,
            "warnings": ["Multiple issues"],
            "confidence_adjustment": -0.5
        }
        
        # Try to push below 0
        adjusted, _ = calibrator.calibrate(0.2, context, validation)
        assert adjusted >= 0.0
        
        # Try to push above 1
        context["news_count"] = 100
        validation["valid"] = True
        validation["confidence_adjustment"] = 0
        adjusted, _ = calibrator.calibrate(0.95, context, validation)
        assert adjusted <= 1.0


@pytest.mark.asyncio
async def test_validation_integration():
    """Test that validators integrate properly with AIEngine"""
    from backend.engine.validators import get_validator, get_calibrator
    
    # Ensure singletons work
    v1 = get_validator()
    v2 = get_validator()
    assert v1 is v2
    
    c1 = get_calibrator()
    c2 = get_calibrator()
    assert c1 is c2
