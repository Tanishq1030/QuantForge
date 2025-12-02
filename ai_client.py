#!/usr/bin/env python3
"""
QuantForge AI - Real Interactive Client

Experience the AI like you experience ChatGPT - ask about any stock,
get intelligent, context-aware analysis powered by your AI engine.
"""

import requests
import sys
from datetime import datetime

# API Configuration
API_URL = "http://localhost:8000/v1/ai/analyze"
USER_ID = "client_user"
TIER = "pro"


def analyze_stock(ticker, mode="comprehensive"):
    """Get real AI analysis for a stock"""
    
    print(f"\n🤖 AI is analyzing {ticker}...")
    print("   (Fetching news, analyzing sentiment, generating insights...)\n")
    
    try:
        response = requests.post(
            API_URL,
            headers={
                "X-User-ID": USER_ID,
                "X-User-Tier": TIER,
                "Content-Type": "application/json"
            },
            json={
                "ticker": ticker.upper(),
                "analysis_type": mode,  # Use comprehensive for REAL AI
                "days_before": 7
            },
            timeout=60  # Give AI time to think
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print("⚠️  Rate limit reached. Wait a moment or upgrade tier.")
            return None
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to QuantForge AI Engine")
        print("💡 Start server: uvicorn backend.main:app --reload --port 8000")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def display_analysis(data):
    """Display AI analysis like a conversation"""
    
    if not data:
        return
    
    ticker = data['ticker']
    sentiment = data['sentiment']
    recommendation = data['recommendation']
    confidence = data['confidence']
    summary = data.get('summary', 'No summary available')
    insights = data.get('key_insights', [])
    reasoning = data.get('confidence_reasoning', [])
    warnings = data.get('validation_warnings', [])
    
    print("=" * 70)
    print(f"🤖 QUANTFORGE AI ANALYSIS: {ticker}")
    print("=" * 70)
    print()
    
    # Main AI Summary (like ChatGPT response)
    print(f"📊 AI INSIGHT:")
    print(f"   {summary}")
    print()
    
    # Sentiment & Recommendation
    sentiment_emoji = {"bullish": "📈", "bearish": "📉", "neutral": "➡️"}
    print(f"{sentiment_emoji.get(sentiment, '❓')} Sentiment: {sentiment.upper()}")
    print(f"💡 Recommendation: {recommendation}")
    print(f"🎯 Confidence: {confidence:.0%}")
    print()
    
    # Key Insights (AI's reasoning)
    if insights:
        print("🔍 KEY INSIGHTS:")
        for insight in insights:
            print(f"   • {insight}")
        print()
    
    # AI's Confidence Reasoning
    if reasoning:
        print("🧠 AI REASONING:")
        for reason in reasoning:
            print(f"   • {reason}")
        print()
    
    # Validation Warnings (hallucination detection)
    if warnings:
        print("⚠️  VALIDATION WARNINGS:")
        for warning in warnings:
            print(f"   • {warning}")
        print()
    
    # Metadata
    meta = data.get('meta', {})
    print(f"⏱️  Processing Time: {meta.get('processing_time_ms', 0)}ms")
    print(f"🤖 AI Model: {meta.get('model_used', 'unknown')}")
    print(f"📰 News Articles: {meta.get('news_count', 0)}")
    print(f"📊 Price Data: {'Available' if meta.get('has_price_data') else 'N/A'}")
    print()
    print("=" * 70)


def interactive_mode():
    """Interactive AI chat mode"""
    
    print("\n" + "=" * 70)
    print("🚀 QUANTFORGE AI - INTERACTIVE MODE")
    print("=" * 70)
    print()
    print("Ask the AI about any stock. Get intelligent, context-aware analysis.")
    print("Type 'quit' to exit.\n")
    
    while True:
        try:
            # Get user input
            ticker = input("💬 What stock would you like me to analyze? ").strip()
            
            if not ticker:
                continue
            
            if ticker.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            # Get AI analysis
            result = analyze_stock(ticker, mode="comprehensive")
            
            # Display results
            if result:
                display_analysis(result)
                print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def single_analysis_mode(ticker):
    """Analyze a single stock (for scripting)"""
    
    result = analyze_stock(ticker, mode="comprehensive")
    
    if result:
        display_analysis(result)
        return True
    return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode: python ai_client.py AAPL
        ticker = sys.argv[1]
        success = single_analysis_mode(ticker)
        sys.exit(0 if success else 1)
    else:
        # Interactive mode
        interactive_mode()
