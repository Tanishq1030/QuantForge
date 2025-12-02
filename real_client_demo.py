# real_client_demo.py
"""
Real-World Client Demo - How customers actually use QuantForge

This shows realistic use cases:
1. Trading Bot Integration
2. Portfolio Dashboard
3. Alert System
"""

import requests
import time
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"
USER_ID = "demo_customer"
USER_TIER = "pro"  # Change to "free" to test limits


class QuantForgeAPI:
    """Simple client wrapper"""
    
    def __init__(self, base_url, user_id, tier):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "X-User-ID": user_id,
            "X-User-Tier": tier,
            "Content-Type": "application/json"
        })
    
    def analyze(self, ticker, mode="quick"):
        """Analyze a stock"""
        try:
            response = self.session.post(
                f"{self.base_url}/v1/ai/analyze",
                json={"ticker": ticker, "analysis_type": mode},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(f"{Fore.YELLOW}⚠️ Rate limit reached. Upgrade to Pro for more requests!")
                return None
            else:
                print(f"{Fore.RED}❌ Error {response.status_code}")
                return None
        except Exception as e:
            print(f"{Fore.RED}❌ Connection failed: {e}")
            return None


def demo_1_trading_bot():
    """
    USE CASE 1: Automated Trading Bot
    
    A trading bot that:
    - Monitors specific tickers
    - Makes buy/sell decisions based on sentiment
    - Only trades when confidence is high
    """
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}USE CASE 1: Automated Trading Bot")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    api = QuantForgeAPI(API_BASE_URL, USER_ID, USER_TIER)
    
    # Bot's configuration
    watchlist = ["AAPL", "TSLA", "NVDA"]
    confidence_threshold = 0.6
    
    print(f"{Fore.WHITE}📊 Trading Bot Started")
    print(f"{Fore.WHITE}   Watchlist: {', '.join(watchlist)}")
    print(f"{Fore.WHITE}   Confidence Threshold: {confidence_threshold}")
    print(f"{Fore.WHITE}   Strategy: Buy on bullish, Sell on bearish\n")
    
    for ticker in watchlist:
        print(f"{Fore.BLUE}🔍 Analyzing {ticker}...")
        
        result = api.analyze(ticker, "quick")
        
        if result:
            sentiment = result['sentiment']
            recommendation = result['recommendation']
            confidence = result['confidence']
            
            # Color code based on sentiment
            if sentiment == "bullish":
                color = Fore.GREEN
                emoji = "📈"
            elif sentiment == "bearish":
                color = Fore.RED
                emoji = "📉"
            else:
                color = Fore.YELLOW
                emoji = "➡️"
            
            print(f"{color}   {emoji} {ticker}: {sentiment.upper()} | {recommendation} | Confidence: {confidence:.2f}")
            
            # Trading decision
            if confidence >= confidence_threshold:
                if recommendation == "BUY":
                    print(f"{Fore.GREEN}   ✅ ACTION: BUY {ticker} (High confidence)")
                elif recommendation == "SELL":
                    print(f"{Fore.RED}   ✅ ACTION: SELL {ticker} (High confidence)")
                else:
                    print(f"{Fore.YELLOW}   ⏸️ ACTION: HOLD {ticker}")
            else:
                print(f"{Fore.YELLOW}   ⏸️ ACTION: HOLD {ticker} (Low confidence)")
        
        print()
        time.sleep(0.5)
    
    print(f"{Fore.WHITE}✅ Trading bot cycle complete!\n")


def demo_2_portfolio_dashboard():
    """
    USE CASE 2: Investment Portfolio Dashboard
    
    A dashboard that shows:
    - Multiple stock sentiments
    - Overall portfolio health
    - Risk assessment
    """
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}USE CASE 2: Portfolio Dashboard")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    api = QuantForgeAPI(API_BASE_URL, USER_ID, USER_TIER)
    
    # User's actual portfolio
    portfolio = {
        "AAPL": 50,   # 50 shares
        "MSFT": 30,
        "GOOGL": 20,
        "TSLA": 15,
        "AMZN": 10
    }
    
    print(f"{Fore.WHITE}📊 Your Investment Portfolio\n")
    print(f"{Fore.WHITE}{'Ticker':<8} {'Shares':<8} {'Sentiment':<12} {'Action':<12} {'Confidence'}")
    print(f"{Fore.WHITE}{'-'*60}")
    
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0
    
    for ticker, shares in portfolio.items():
        result = api.analyze(ticker, "quick")
        
        if result:
            sentiment = result['sentiment']
            recommendation = result['recommendation']
            confidence = result['confidence']
            
            # Track sentiment distribution
            if sentiment == "bullish":
                bullish_count += 1
                color = Fore.GREEN
            elif sentiment == "bearish":
                bearish_count += 1
                color = Fore.RED
            else:
                neutral_count += 1
                color = Fore.YELLOW
            
            print(f"{color}{ticker:<8} {shares:<8} {sentiment:<12} {recommendation:<12} {confidence:.2f}")
        
        time.sleep(0.3)
    
    # Portfolio summary
    total_stocks = len(portfolio)
    print(f"\n{Fore.WHITE}📈 Portfolio Health:")
    print(f"{Fore.GREEN}   Bullish: {bullish_count}/{total_stocks} ({bullish_count/total_stocks*100:.0f}%)")
    print(f"{Fore.RED}   Bearish: {bearish_count}/{total_stocks} ({bearish_count/total_stocks*100:.0f}%)")
    print(f"{Fore.YELLOW}   Neutral: {neutral_count}/{total_stocks} ({neutral_count/total_stocks*100:.0f}%)")
    
    if bullish_count > bearish_count:
        print(f"\n{Fore.GREEN}✅ Overall: POSITIVE outlook")
    elif bearish_count > bullish_count:
        print(f"\n{Fore.RED}⚠️ Overall: NEGATIVE outlook - Consider rebalancing")
    else:
        print(f"\n{Fore.YELLOW}➡️ Overall: NEUTRAL outlook")
    
    print()


def demo_3_alert_system():
    """
    USE CASE 3: Smart Alert System
    
    Monitor specific stocks and send alerts when:
    - Sentiment changes
    - High confidence signals
    - Unusual activity
    """
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}USE CASE 3: Smart Alert System")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    api = QuantForgeAPI(API_BASE_URL, USER_ID, USER_TIER)
    
    # Stocks to monitor
    watch_for_signals = ["AAPL", "NVDA", "TSLA"]
    
    print(f"{Fore.WHITE}🔔 Alert System Active")
    print(f"{Fore.WHITE}   Monitoring: {', '.join(watch_for_signals)}")
    print(f"{Fore.WHITE}   Alert Criteria: High confidence signals\n")
    
    alerts = []
    
    for ticker in watch_for_signals:
        result = api.analyze(ticker, "quick")
        
        if result:
            sentiment = result['sentiment']
            recommendation = result['recommendation']
            confidence = result['confidence']
            
            # Generate alerts based on criteria
            if confidence > 0.6 and recommendation in ["BUY", "SELL"]:
                alert_type = "🚨 HIGH PRIORITY" if confidence > 0.8 else "⚠️ MEDIUM PRIORITY"
                
                alert = {
                    "ticker": ticker,
                    "type": alert_type,
                    "action": recommendation,
                    "sentiment": sentiment,
                    "confidence": confidence,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                }
                alerts.append(alert)
    
    # Display alerts
    if alerts:
        print(f"{Fore.YELLOW}📬 {len(alerts)} Alert(s) Generated:\n")
        for alert in alerts:
            if "HIGH" in alert['type']:
                color = Fore.RED
            else:
                color = Fore.YELLOW
            
            print(f"{color}{alert['type']}")
            print(f"{color}   Ticker: {alert['ticker']}")
            print(f"{color}   Action: {alert['action']}")
            print(f"{color}   Sentiment: {alert['sentiment']}")
            print(f"{color}   Confidence: {alert['confidence']:.2f}")
            print(f"{color}   Time: {alert['timestamp']}")
            print()
    else:
        print(f"{Fore.GREEN}✅ No high-confidence signals at this time")
        print(f"{Fore.GREEN}   Continuing to monitor...\n")


def main():
    """
    Interactive demo - choose which use case to see
    """
    print(f"\n{Fore.MAGENTA}{'='*70}")
    print(f"{Fore.MAGENTA}🚀 QUANTFORGE API - REAL CLIENT DEMO")
    print(f"{Fore.MAGENTA}{'='*70}\n")
    
    print(f"{Fore.WHITE}Choose a demo:")
    print(f"{Fore.WHITE}  1️⃣  Trading Bot (Automated buy/sell decisions)")
    print(f"{Fore.WHITE}  2️⃣  Portfolio Dashboard (Monitor investments)")
    print(f"{Fore.WHITE}  3️⃣  Alert System (Get notified of signals)")
    print(f"{Fore.WHITE}  4️⃣  Run All Demos")
    print(f"{Fore.WHITE}  0️⃣  Exit\n")
    
    choice = input(f"{Fore.CYAN}Enter choice (0-4): {Style.RESET_ALL}")
    
    if choice == "1":
        demo_1_trading_bot()
    elif choice == "2":
        demo_2_portfolio_dashboard()
    elif choice == "3":
        demo_3_alert_system()
    elif choice == "4":
        demo_1_trading_bot()
        demo_2_portfolio_dashboard()
        demo_3_alert_system()
        
        print(f"\n{Fore.GREEN}{'='*70}")
        print(f"{Fore.GREEN}✅ All demos complete!")
        print(f"{Fore.GREEN}{'='*70}\n")
    elif choice == "0":
        print(f"{Fore.YELLOW}👋 Goodbye!")
        exit(0)
    else:
        print(f"{Fore.RED}Invalid choice!")
        return
    
    # Ask to run again
    again = input(f"\n{Fore.CYAN}Run another demo? (y/n): {Style.RESET_ALL}")
    if again.lower() == 'y':
        main()
    else:
        print(f"\n{Fore.GREEN}🎉 Thanks for trying QuantForge!")
        print(f"{Fore.WHITE}Visit https://quantforge.com to get your API key\n")


if __name__ == "__main__":
    main()
