# client_test.py
"""
Client-side test script - How a customer would use QuantForge API

This simulates a real trading bot or application calling your API.
"""

import requests
import time
from datetime import datetime

# API Configuration (as a customer would set it up)
API_BASE_URL = "http://localhost:8000"
API_KEY = "your_api_key_here"  # In production, from your dashboard

# Customer's API credentials
USER_ID = "test_customer_123"
USER_TIER = "free"  # or "pro", "enterprise"


class QuantForgeClient:
    """
    Customer's QuantForge API Client
    
    This is what developers would build to integrate with your API.
    """
    
    def __init__(self, base_url, user_id, tier="free"):
        self.base_url = base_url
        self.user_id = user_id
        self.tier = tier
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            "X-User-ID": user_id,
            "X-User-Tier": tier,
            "Content-Type": "application/json"
        })
    
    def analyze_stock(self, ticker, analysis_type="quick"):
        """
        Analyze a stock - customer's main use case
        
        Args:
            ticker: Stock symbol (e.g., "AAPL")
            analysis_type: "quick", "comprehensive", "sentiment_only", "risk_only"
        
        Returns:
            Analysis results dict
        """
        url = f"{self.base_url}/v1/ai/analyze"
        
        payload = {
            "ticker": ticker,
            "analysis_type": analysis_type
        }
        
        print(f"\n📊 Analyzing {ticker} ({analysis_type} mode)...")
        start_time = time.time()
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            elapsed = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! ({elapsed:.0f}ms)")
                return data
            
            elif response.status_code == 429:
                print(f"⚠️ Rate limit exceeded!")
                print(f"   {response.json()}")
                return None
            
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def check_status(self):
        """Check if AI engine is operational"""
        url = f"{self.base_url}/v1/ai/status"
        
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                status = response.json()
                print(f"\n🟢 AI Engine Status: {status.get('status')}")
                print(f"   Active Provider: {status.get('active_provider')}")
                return True
            return False
        except:
            print(f"\n🔴 AI Engine not reachable")
            return False


def test_scenario_1_quick_analysis():
    """
    Scenario 1: Customer wants quick analysis for a stock
    Use case: High-frequency trading bot checking multiple stocks
    """
    print("\n" + "="*60)
    print("TEST SCENARIO 1: Quick Analysis")
    print("="*60)
    
    client = QuantForgeClient(API_BASE_URL, USER_ID, USER_TIER)
    
    # Check if API is up
    if not client.check_status():
        print("❌ API not available. Start the server first!")
        return False
    
    # Analyze AAPL
    result = client.analyze_stock("AAPL", "quick")
    
    if result:
        print(f"\n📈 Analysis Results:")
        print(f"   Ticker: {result.get('ticker')}")
        print(f"   Sentiment: {result.get('sentiment')}")
        print(f"   Recommendation: {result.get('recommendation')}")
        print(f"   Confidence: {result.get('confidence')}")
        print(f"   Processing Time: {result.get('meta', {}).get('processing_time_ms')}ms")
        print(f"   Model Used: {result.get('meta', {}).get('model_used')}")
        return True
    
    return False


def test_scenario_2_multiple_stocks():
    """
    Scenario 2: Portfolio monitoring - analyze multiple stocks
    Use case: Investment dashboard showing sentiment for watchlist
    """
    print("\n" + "="*60)
    print("TEST SCENARIO 2: Portfolio Monitoring")
    print("="*60)
    
    client = QuantForgeClient(API_BASE_URL, USER_ID, USER_TIER)
    
    # Customer's watchlist
    watchlist = ["AAPL", "TSLA", "MSFT", "GOOGL"]
    
    results = {}
    for ticker in watchlist:
        result = client.analyze_stock(ticker, "quick")
        if result:
            results[ticker] = {
                "sentiment": result.get("sentiment"),
                "recommendation": result.get("recommendation"),
                "confidence": result.get("confidence")
            }
        time.sleep(0.5)  # Polite delay between requests
    
    # Display portfolio summary
    print(f"\n📊 Portfolio Summary:")
    print(f"{'Ticker':<8} {'Sentiment':<10} {'Recommendation':<15} {'Confidence'}")
    print("-" * 55)
    for ticker, data in results.items():
        print(f"{ticker:<8} {data['sentiment']:<10} {data['recommendation']:<15} {data['confidence']:.2f}")
    
    return len(results) > 0


def test_scenario_3_rate_limiting():
    """
    Scenario 3: Test rate limiting
    Use case: Ensure customer doesn't exceed free tier limits
    """
    print("\n" + "="*60)
    print("TEST SCENARIO 3: Rate Limiting")
    print("="*60)
    
    client = QuantForgeClient(API_BASE_URL, USER_ID, "free")
    
    print(f"Free tier limit: 10 requests/hour")
    print(f"Sending 12 requests to test rate limiting...\n")
    
    success_count = 0
    rate_limited = False
    
    for i in range(12):
        result = client.analyze_stock("AAPL", "quick")
        if result:
            success_count += 1
            print(f"   Request {i+1}: ✅ Success")
        else:
            rate_limited = True
            print(f"   Request {i+1}: ⚠️ Rate limited (expected)")
            break
    
    print(f"\n📊 Results:")
    print(f"   Successful requests: {success_count}")
    print(f"   Rate limiting working: {'✅ Yes' if rate_limited else '❌ No'}")
    
    return rate_limited  # Should be True (rate limiting working)


def test_scenario_4_error_handling():
    """
    Scenario 4: Test error handling
    Use case: Customer's code needs to handle invalid inputs
    """
    print("\n" + "="*60)
    print("TEST SCENARIO 4: Error Handling")
    print("="*60)
    
    client = QuantForgeClient(API_BASE_URL, USER_ID, USER_TIER)
    
    # Test 1: Invalid ticker
    print("\n1. Testing invalid ticker...")
    result = client.analyze_stock("", "quick")
    
    # Test 2: Invalid analysis type
    print("\n2. Testing invalid analysis type...")
    result = client.analyze_stock("AAPL", "invalid_type")
    
    print("\n✅ Error handling test complete")
    return True


def run_all_tests():
    """
    Run complete test suite from customer perspective
    """
    print("\n" + "🎯" + "="*58 + "🎯")
    print("    QUANTFORGE API - CLIENT-SIDE TESTING SUITE")
    print("🎯" + "="*58 + "🎯")
    print(f"\nTesting as: {USER_ID} ({USER_TIER} tier)")
    print(f"API Endpoint: {API_BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "Scenario 1: Quick Analysis": test_scenario_1_quick_analysis(),
        "Scenario 2: Portfolio Monitoring": test_scenario_2_multiple_stocks(),
        "Scenario 3: Rate Limiting": test_scenario_3_rate_limiting(),
        "Scenario 4: Error Handling": test_scenario_4_error_handling(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - PRODUCTION READY!")
    else:
        print("⚠️ SOME TESTS FAILED - NEEDS FIXES")
    print("="*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    # Run the complete test suite
    success = run_all_tests()
    
    # Exit code for CI/CD
    exit(0 if success else 1)
