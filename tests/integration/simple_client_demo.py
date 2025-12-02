# simple_client_demo.py
"""
Simple Interactive Demo - Analyze ANY Stock

The simplest way to test QuantForge API.
Just enter any stock ticker and get instant analysis!
"""

import requests
from colorama import init, Fore, Style

init(autoreset=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"
USER_ID = "demo_user"
USER_TIER = "pro"


def analyze_stock(ticker):
    """Analyze a single stock"""
    
    print(f"\n{Fore.CYAN}🔍 Analyzing {ticker}...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/v1/ai/analyze",
            headers={
                "X-User-ID": USER_ID,
                "X-User-Tier": USER_TIER,
                "Content-Type": "application/json"
            },
            json={
                "ticker": ticker,
                "analysis_type": "quick"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Color code sentiment
            sentiment = data['sentiment']
            if sentiment == "bullish":
                color = Fore.GREEN
                emoji = "📈"
            elif sentiment == "bearish":
                color = Fore.RED
                emoji = "📉"
            else:
                color = Fore.YELLOW
                emoji = "➡️"
            
            print(f"\n{color}{'='*60}")
            print(f"{color}  {emoji} {ticker} ANALYSIS RESULTS")
            print(f"{color}{'='*60}")
            print(f"{color}")
            print(f"{color}📊 Sentiment:      {sentiment.upper()}")
            print(f"{color}💡 Recommendation: {data['recommendation']}")
            print(f"{color}🎯 Confidence:     {data['confidence']:.2f} ({int(data['confidence']*100)}%)")
            print(f"{color}📝 Summary:        {data.get('summary', 'N/A')}")
            print(f"{color}")
            print(f"{color}⏱️  Processing Time: {data['meta']['processing_time_ms']}ms")
            print(f"{color}🤖 Model Used:      {data['meta']['model_used']}")
            print(f"{color}{'='*60}\n")
            
            # Trading suggestion
            if data['confidence'] > 0.7:
                if data['recommendation'] == "BUY":
                    print(f"{Fore.GREEN}✅ STRONG BUY SIGNAL - High Confidence!")
                elif data['recommendation'] == "SELL":
                    print(f"{Fore.RED}⚠️  STRONG SELL SIGNAL - High Confidence!")
                else:
                    print(f"{Fore.YELLOW}⏸️  HOLD - Wait for better signal")
            else:
                print(f"{Fore.YELLOW}⏸️  HOLD - Confidence too low for action")
            
            return True
            
        elif response.status_code == 429:
            print(f"{Fore.RED}⚠️  Rate limit exceeded. Upgrade to Pro tier!")
            return False
        else:
            print(f"{Fore.RED}❌ Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}❌ Cannot connect to API. Is the server running?")
        print(f"{Fore.YELLOW}💡 Start server: uvicorn backend.main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}")
        return False


def main():
    """Interactive stock analysis"""
    
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}🚀 QUANTFORGE - INTERACTIVE STOCK ANALYSIS")
    print(f"{Fore.MAGENTA}{'='*60}\n")
    
    print(f"{Fore.WHITE}Analyze any stock in real-time!")
    print(f"{Fore.WHITE}Enter stock ticker (e.g., AAPL, TSLA, BTC) or 'quit' to exit\n")
    
    while True:
        ticker = input(f"{Fore.CYAN}Enter ticker: {Style.RESET_ALL}").strip().upper()
        
        if not ticker:
            print(f"{Fore.YELLOW}Please enter a ticker symbol")
            continue
        
        if ticker in ['QUIT', 'EXIT', 'Q']:
            print(f"\n{Fore.GREEN}👋 Thanks for using QuantForge!")
            break
        
        # Analyze the stock
        analyze_stock(ticker)
        
        # Ask to continue
        print(f"\n{Fore.WHITE}Analyze another stock? (y/n)")
        again = input(f"{Fore.CYAN}Choice: {Style.RESET_ALL}").strip().lower()
        
        if again not in ['y', 'yes', '']:
            print(f"\n{Fore.GREEN}👋 Thanks for using QuantForge!")
            break


if __name__ == "__main__":
    main()
