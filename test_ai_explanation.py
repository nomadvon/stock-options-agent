import logging
import json
from analysis.explanation.ai_explainer import AIExplainer
from analysis.technical.technical_analysis import TechnicalAnalyzer
from analysis.sentiment.finbert_analyzer import FinBERTAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_trading_signals():
    # Get OpenAI API key from environment
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Initialize analyzers
    technical_analyzer = TechnicalAnalyzer()
    sentiment_analyzer = FinBERTAnalyzer()
    ai_explainer = AIExplainer(openai_api_key)
    
    # Test with SPY
    symbol = "SPY"
    print(f"\nTesting trading signals for {symbol}...")
    
    # Get technical analysis
    technical_data = technical_analyzer.analyze(symbol)
    print("\nTechnical Analysis Results:")
    print(f"RSI: {technical_data.get('rsi', 'N/A')}")
    print(f"MACD: {technical_data.get('macd', 'N/A')}")
    print("Bollinger Bands:")
    print(f"  - Upper: {technical_data.get('bollinger_bands', {}).get('upper', 'N/A')}")
    print(f"  - Middle: {technical_data.get('bollinger_bands', {}).get('middle', 'N/A')}")
    print(f"  - Lower: {technical_data.get('bollinger_bands', {}).get('lower', 'N/A')}")
    
    # Get sentiment analysis
    sentiment_data = sentiment_analyzer.get_ticker_sentiment(symbol)
    print("\nSentiment Analysis Results:")
    print(f"Overall Score: {sentiment_data.get('overall_score', 'N/A')}")
    print(f"Sentiment Label: {sentiment_data.get('sentiment_label', 'N/A')}")
    print(f"Articles Analyzed: {sentiment_data.get('article_count', 'N/A')}")
    
    # Get AI trading signals
    print("\nTrading Signals:")
    signals = ai_explainer.analyze_trading_signals(symbol, technical_data, sentiment_data)
    try:
        data = json.loads(signals)
        print("\nEntry Points:")
        print(data.get('entry_points', 'N/A'))
        print("\nExit Points:")
        print(data.get('exit_points', 'N/A'))
        print("\nAnalysis:")
        print(data.get('analysis', 'N/A'))
        print("\nConfidence:", data.get('confidence', 'N/A'))
        print("\nKey Levels:")
        print(data.get('key_levels', 'N/A'))
    except json.JSONDecodeError:
        print(signals)

if __name__ == "__main__":
    test_trading_signals() 