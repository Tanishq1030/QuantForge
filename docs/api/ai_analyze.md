# AI Analysis API Reference

## Overview

The QuantForge AI Analysis API provides intelligent financial analysis using multi-provider LLM orchestration with automatic validation and confidence calibration.

**Base URL:** `https://api.quantforge.com` (production)  
**Base URL:** `http://localhost:8000` (development)

---

## Authentication

Include your API key in the request headers:

```
X-User-ID: your_user_id
X-User-Tier: free|pro|enterprise
Authorization: Bearer your_api_key_here
```

---

## Rate Limits

| Tier | Requests/Day | Requests/Hour | Max Tokens |
|------|--------------|---------------|------------|
| **Free** | 50 | 10 | 1,000 |
| **Pro** | 10,000 | 500 | 2,000 |
| **Enterprise** | Unlimited | Unlimited | 5,000 |

**Rate Limit Headers:**
- `X-RateLimit-Limit`: Total requests allowed per day
- `X-RateLimit-Remaining`: Requests remaining today

---

## Endpoints

### POST `/v1/ai/analyze`

Analyze a financial asset using AI.

**Request Body:**

```json
{
  "ticker": "AAPL",
  "analysis_type": "quick|comprehensive|sentiment_only|risk_only",
  "days_before": 7,
  "timezone": "UTC"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Asset symbol (e.g., "AAPL", "BTC") |
| `analysis_type` | string | No | Type of analysis (default: "quick") |
| `days_before` | integer | No | Days of historical data (default: 7) |
| `timezone` | string | No | Timezone for analysis (default: "UTC") |

**Analysis Types:**

- `quick`: Rule-based analysis (<500ms, no LLM)
- `comprehensive`: Full AI analysis with LLM reasoning
- `sentiment_only`: News sentiment analysis only
- `risk_only`: Risk assessment only

**Response:**

```json
{
  "ticker": "AAPL",
  "analysis_type": "comprehensive",
  "summary": "Apple shows strong bullish momentum...",
  "sentiment": "bullish",
  "recommendation": "BUY",
  "confidence": 0.85,
  "key_insights": [
    "Q4 earnings beat expectations",
    "iPhone sales up 12% YoY",
    "Services revenue accelerating"
  ],
  "validation_warnings": [],
  "confidence_reasoning": ["Rich data set", "Recent news available"],
  "meta": {
    "analysis_date": "2025-12-03T00:45:00Z",
    "processing_time_ms": 8915,
    "news_count": 15,
    "has_price_data": true,
    "model_used": "ollama",
    "version": "1.0"
  }
}
```

**Status Codes:**

- `200 OK`: Analysis successful
- `400 Bad Request`: Invalid parameters
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

---

### GET `/v1/ai/status`

Check AI engine status.

**Response:**

```json
{
  "status": "operational",
  "llm_providers": ["ollama", "openai", "huggingface"],
  "active_provider": "ollama",
  "uptime_seconds": 86400
}
```

---

### GET `/v1/ai/models`

List available models and capabilities.

**Response:**

```json
{
  "models": {
    "ollama": {
      "name": "mistral:latest",
      "status": "available",
      "cost_per_1k_tokens": 0.0
    },
    "openai": {
      "name": "gpt-3.5-turbo",
      "status": "available",
      "cost_per_1k_tokens": 0.002
    }
  }
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": "Rate limit exceeded",
  "message": "Daily limit of 50 requests exceeded",
  "limit_info": {
    "limit_type": "daily",
    "limit": 50,
    "used": 50,
    "reset_at": "2025-12-04T00:00:00Z"
  }
}
```

### Common Errors

| Status Code | Error | Solution |
|-------------|-------|----------|
| 400 | Invalid ticker | Check ticker format |
| 429 | Rate limit exceeded | Upgrade tier or wait for reset |
| 500 | LLM provider failure | Automatic fallback will retry |

---

## Examples

### Quick Analysis (Python)

```python
import requests

response = requests.post(
    'https://api.quantforge.com/v1/ai/analyze',
    headers={
        'X-User-ID': 'user_123',
        'X-User-Tier': 'pro',
        'Authorization': 'Bearer your_api_key'
    },
    json={
        'ticker': 'AAPL',
        'analysis_type': 'quick'
    }
)

analysis = response.json()
print(f"Sentiment: {analysis['sentiment']}")
print(f"Recommendation: {analysis['recommendation']}")
```

### Comprehensive Analysis (JavaScript)

```javascript
const response = await fetch('https://api.quantforge.com/v1/ai/analyze', {
  method: 'POST',
  headers: {
    'X-User-ID': 'user_123',
    'X-User-Tier': 'enterprise',
    'Authorization': 'Bearer your_api_key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    ticker: 'TSLA',
    analysis_type: 'comprehensive',
    days_before: 14
  })
});

const data = await response.json();
console.log(data.summary);
```

### Error Handling (TypeScript)

```typescript
try {
  const response = await fetch('https://api.quantforge.com/v1/ai/analyze', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(request)
  });
  
  if (response.status === 429) {
    const error = await response.json();
    console.error(`Rate limit: ${error.limit_info.reset_at}`);
    return;
  }
  
  const analysis = await response.json();
  // Process analysis...
  
} catch (error) {
  console.error('Analysis failed:', error);
}
```

---

## Best Practices

### 1. Use Quick Mode When Possible

```python
# Quick mode is 20x faster and doesn't count against token limits
response = analyze(ticker='AAPL', analysis_type='quick')
```

### 2. Handle Rate Limits Gracefully

```python
if response.status_code == 429:
    reset_time = response.json()['limit_info']['reset_at']
    # Wait or queue for later
```

### 3. Cache Results

```python
# Cache analysis results to avoid redundant API calls
cache_key = f"{ticker}_{analysis_type}_{date}"
if cache_key not in cache:
    cache[cache_key] = api.analyze(ticker)
```

### 4. Monitor Validation Warnings

```python
if 'validation_warnings' in result:
    # LLM may have hallucinated - reduce confidence
    confidence *= 0.8
```

---

## Changelog

### v1.0 (Phase 1.4)
- Multi-provider LLM support (Ollama, OpenAI, HF)
- Automatic validation & confidence calibration
- Rate limiting per tier
- Sentry error tracking
- Usage metrics for billing

---

## Support

- **Documentation:** https://docs.quantforge.com
- **API Status:** https://status.quantforge.com
- **Issue Tracker:** https://github.com/Tanishq1030/QuantForge/issues
- **Email:** support@quantforge.com
