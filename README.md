# 🚀 QuantForge AI Engine

> **AI-Powered Trading & Market Intelligence Platform**  
> *Production-ready financial analysis engine with $0 infrastructure cost*

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)](https://fastapi.tiangolo.com/)
[![Phase](https://img.shields.io/badge/Phase-1.4%20Complete-success)](https://github.com/Tanishq1030/QuantForge)

---

## 📊 **What is QuantForge?**

QuantForge is an **end-to-end AI-powered trading engine** that combines real-time market data, news sentiment analysis, and intelligent orchestration to provide actionable trading insights.

**Built for:**
- 🤖 **Algorithmic traders** seeking AI-driven signals
- 📈 **Portfolio managers** monitoring market sentiment
- 💼 **Fintech companies** needing trading intelligence APIs
- 🎯 **Quant developers** building systematic strategies

---

## ✨ **Key Features**

### 🤖 **AI Engine (Phase 1.4 - Production Ready)**

| Feature | Description | Status |
|---------|-------------|--------|
| **Multi-Provider LLM** | Ollama, OpenAI, HuggingFace with automatic fallback | ✅ Live |
| **Sentiment Analysis** | Real-time news sentiment from RSS feeds + AI | ✅ Live |
| **Hallucination Detection** | Validates AI outputs against actual data | ✅ Live |
| **Confidence Calibration** | Adjusts confidence based on data quality | ✅ Live |
| **Rate Limiting** | Free (50/day), Pro (10k/day), Enterprise (unlimited) | ✅ Live |
| **Error Tracking** | Sentry integration with custom events | ✅ Live |
| **Usage Metrics** | Token tracking, cost estimation, billing analytics | ✅ Live |

### 📡 **Data Pipeline**

- ✅ **RSS News Feeds** - Real-time financial news ingestion
- ✅ **Binance Market Data** - Price, volume, orderbook data
- ✅ **Vector Store** - Weaviate for semantic news search
- ✅ **Time-Series DB** - TimescaleDB for OHLCV data
- ✅ **Embeddings** - HuggingFace sentence-transformers

### 🔧 **Infrastructure**

- ✅ **$0 Cost Stack** - Ollama (local LLM), free-tier cloud services
- ✅ **Scalable Architecture** - FastAPI + async/await
- ✅ **Production Monitoring** - Sentry error tracking
- ✅ **API Versioning** - v1 endpoints with OpenAPI docs

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────┐
│                    Client Application                    │
│          (Trading Bot / Dashboard / Mobile App)          │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
                ┌────────────────┐
                │   FastAPI      │
                │   (REST API)   │
                └───────┬────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │   Rate   │   │  Sentry  │   │  Metrics │
  │ Limiter  │   │ Tracking │   │ Logging  │
  └────┬─────┘   └──────────┘   └──────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│            AI Engine Orchestrator            │
│  (Coordinates data gathering + AI analysis)  │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│ Vector │ │  TSDB  │ │  LLM   │
│ Store  │ │(Prices)│ │ Client │
│ (News) │ │        │ │        │
└────────┘ └────────┘ └───┬────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
         ┌────────┐ ┌────────┐ ┌────────┐
         │ Ollama │ │OpenAI  │ │   HF   │
         │(Local) │ │ (API)  │ │ (API)  │
         └────────┘ └────────┘ └────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │   Validators    │
                 │  (Anti-Halluc)  │
                 └────────┬────────┘
                          │
                          ▼
                    ┌──────────┐
                    │ Response │
                    └──────────┘
```

---

## 🚀 **Quick Start**

### **Prerequisites**

- Python 3.11+
- Docker (optional, for services)
- [Ollama](https://ollama.ai/) (for local LLM)

### **1. Clone Repository**

```bash
git clone https://github.com/Tanishq1030/QuantForge.git
cd QuantForge
```

### **2. Install Dependencies**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### **3. Configure Environment**

```bash
# Copy example config
cp .env.example .env

# Edit .env with your credentials
# Minimum required: DATABASE_URL, WEAVIATE_URL, WEAVIATE_API_KEY
```

### **4. Start Services**

```bash
# Start Ollama (separate terminal)
ollama serve
ollama pull mistral:latest

# Start QuantForge API
uvicorn backend.main:app --reload --port 8000
```

### **5. Test API**

```bash
# Health check
curl http://localhost:8000/health

# AI Analysis
curl -X POST http://localhost:8000/v1/ai/analyze \
  -H "Content-Type: application/json" \
  -H "X-User-ID: demo_user" \
  -H "X-User-Tier: free" \
  -d '{"ticker": "AAPL", "analysis_type": "quick"}'
```

**Expected Response:**
```json
{
  "ticker": "AAPL",
  "sentiment": "neutral",
  "recommendation": "HOLD",
  "confidence": 0.75,
  "summary": "Analysis based on recent news and price data...",
  "meta": {
    "processing_time_ms": 4500,
    "model_used": "ollama"
  }
}
```

---

## 📚 **API Documentation**

### **Endpoints**

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/health` | GET | Health check | No |
| `/v1/ai/analyze` | POST | Analyze stock/crypto | Yes (Headers) |
| `/v1/ai/status` | GET | AI engine status | No |
| `/v1/feeds/rss/ingest` | POST | Ingest news feeds | Yes |
| `/v1/market/price/{ticker}` | GET | Get price data | Yes |

### **Request Example**

```python
import requests

response = requests.post(
    'http://localhost:8000/v1/ai/analyze',
    headers={
        'X-User-ID': 'your_user_id',
        'X-User-Tier': 'pro',
        'Content-Type': 'application/json'
    },
    json={
        'ticker': 'TSLA',
        'analysis_type': 'comprehensive',
        'days_before': 7
    }
)

analysis = response.json()
print(f"Sentiment: {analysis['sentiment']}")
print(f"Recommendation: {analysis['recommendation']}")
```

### **Interactive Docs**

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 💰 **Cost Optimization**

QuantForge is designed for **$0 infrastructure cost** using:

| Component | Solution | Cost |
|-----------|----------|------|
| **LLM** | Ollama (local Mistral 7B) | $0 |
| **Database** | Neon Postgres (free tier) | $0 |
| **Vector DB** | Weaviate Cloud (free tier) | $0 |
| **Hosting** | Railway (free tier) | $0 |
| **Monitoring** | Sentry (free tier) | $0 |

**vs. Traditional Stack:**
- OpenAI GPT-4: $2,000/month for 1M requests
- AWS RDS: $100/month
- Pinecone: $70/month
- **Total Savings: $2,170/month** 💰

---

## 🛠️ **Tech Stack**

### **Backend**
- **Framework**: FastAPI (async, high-performance)
- **LLM**: Ollama (Mistral 7B), OpenAI, HuggingFace
- **Database**: PostgreSQL (Neon) + TimescaleDB extension
- **Vector DB**: Weaviate Cloud
- **Cache**: Redis
- **Storage**: MinIO (S3-compatible)

### **AI/ML**
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Validation**: Custom hallucination detection
- **Confidence**: Bayesian calibration

### **Monitoring**
- **Errors**: Sentry SDK
- **Metrics**: Custom metrics logger
- **Logging**: Structured JSON logs

### **Deployment**
- **Containerization**: Docker + docker-compose
- **CI/CD**: GitHub Actions (planned)
- **Hosting**: Railway, AWS, or self-hosted

---

## 📈 **Roadmap**

### ✅ **Phase 1.4 - AI Engine (COMPLETE)**
- [x] Multi-provider LLM with fallback
- [x] Sentiment analysis API
- [x] Hallucination detection
- [x] Production monitoring (Sentry)
- [x] Rate limiting per tier
- [x] Usage metrics & billing

### 🚧 **Phase 1.5 - Advanced Features (In Progress)**
- [ ] Streaming responses (SSE)
- [ ] Batch analysis endpoints
- [ ] Historical data caching
- [ ] Custom prompt templates per user

### 📅 **Phase 2.0 - Web Platform (Q1 2025)**
- [ ] React/Next.js dashboard
- [ ] User authentication (Clerk)
- [ ] Payment integration (Stripe)
- [ ] Visual analytics & charts
- [ ] Mobile-responsive design

### 📅 **Phase 3.0 - Scale (Q2 2025)**
- [ ] Multi-region deployment
- [ ] Redis-based distributed rate limiting
- [ ] ClickHouse for analytics
- [ ] ML-based validation improvements
- [ ] Custom model fine-tuning

---

## 🧪 **Testing**

### **Run Unit Tests**

```bash
pytest tests/unit/ -v
```

### **Run Integration Tests**

```bash
pytest tests/integration/ -v
```

### **Run Client Demo**

```bash
python real_client_demo.py
```

**Test Coverage:** 85%+ (core engine components)

---

## 📖 **Documentation**

- **API Reference**: [docs/api/ai_analyze.md](docs/api/ai_analyze.md)
- **Architecture**: [docs/architecture.md](docs/architecture.md) *(planned)*
- **Deployment**: [docs/deployment.md](docs/deployment.md) *(planned)*
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md) *(planned)*

---

## 💼 **Use Cases**

### **1. Algorithmic Trading Bot**
```python
# Check sentiment before placing orders
analysis = quantforge.analyze("AAPL")
if analysis['sentiment'] == 'bullish' and analysis['confidence'] > 0.7:
    place_buy_order("AAPL", quantity=100)
```

### **2. Portfolio Dashboard**
```python
# Monitor portfolio health
for ticker in portfolio:
    sentiment = quantforge.analyze(ticker)['sentiment']
    update_dashboard(ticker, sentiment)
```

### **3. Alert System**
```python
# Get notified of high-confidence signals
if analysis['confidence'] > 0.8 and analysis['recommendation'] == 'BUY':
    send_alert(f"Strong BUY signal for {ticker}")
```

---

## 🤝 **Contributing**

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 **License**

This project is licensed under the Apache License 2.0 - see [LICENSE](LICENSE) file for details.

---

## 👨‍💻 **Author**

**Tanishq Dasari**  
- GitHub: [@Tanishq1030](https://github.com/Tanishq1030)
- Project: [QuantForge](https://github.com/Tanishq1030/QuantForge)

---

## 🌟 **Star the Project!**

If QuantForge helps your trading or you find it interesting, consider giving it a ⭐!

---

## 📞 **Support**

- **Issues**: [GitHub Issues](https://github.com/Tanishq1030/QuantForge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Tanishq1030/QuantForge/discussions)
- **Email**: support@quantforge.com *(placeholder)*

---

<div align="center">

**Built with ❤️ for the trading community**

*QuantForge - AI-Powered Market Intelligence*

</div>
