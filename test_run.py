import logging
from config.logging_config import setup_logging
from data.alpaca_connector import AlpacaConnector
from analysis.sentiment.finbert_analyzer import FinBERTAnalyzer
from analysis.technical.indicators import TechnicalAnalysis
from engine.signal_engine import SignalEngine
from alerts.discord_webhook import DiscordWebhook
from config.config import TRADING_SYMBOLS

# Setup logging
logger = setup_logging()

def format_sentiment_data(sentiment_data: dict) -> str:
    """Format sentiment data for Discord message"""
    # Get only the keywords that have matches
    matched_keywords = {k: v for k, v in sentiment_data['keyword_matches'].items() if v > 0}
    
    # Sentiment score explanation
    score_explanation = (
        "**Sentiment Score Range:**\n"
        "• -1.0 to -0.5: Strongly Negative\n"
        "• -0.5 to -0.1: Moderately Negative\n"
        "• -0.1 to 0.1: Neutral\n"
        "• 0.1 to 0.5: Moderately Positive\n"
        "• 0.5 to 1.0: Strongly Positive\n\n"
    )
    
    # Format the sentiment results
    sentiment_results = (
        f"**Sentiment Analysis Results:**\n"
        f"• Overall Score: {sentiment_data['overall_score']:.2f}\n"
        f"• Sentiment Label: {sentiment_data['sentiment_label']}\n"
        f"• Articles Analyzed: {sentiment_data['article_count']}\n"
    )
    
    # Add keyword matches if any exist
    if matched_keywords:
        sentiment_results += (
            f"• Total Keyword Matches: {sum(matched_keywords.values())}\n"
            f"• Matched Keywords:\n"
            + "\n".join(f"  - {k}: {v}" for k, v in matched_keywords.items())
        )
    
    return score_explanation + sentiment_results

def format_technical_data(technical_data: dict) -> str:
    """Format technical data for Discord message"""
    # Check if we have real data or fallback data
    has_real_data = any(
        'rsi' in data or 
        'macd' in data or 
        'bollinger_bands' in data
        for data in technical_data.values()
    )
    
    if not has_real_data:
        return "**Technical Analysis:**\n• Real-time market data not available at this time."
    
    message = "**Technical Analysis Results:**\n"
    for timeframe, data in technical_data.items():
        message += f"\n**{timeframe} Timeframe:**\n"
        if 'rsi' in data:
            message += f"• RSI: {data['rsi']}\n"
        if 'macd' in data:
            message += f"• MACD: {data['macd']}\n"
        if 'bollinger_bands' in data:
            bb = data['bollinger_bands']
            message += f"• Bollinger Bands:\n"
            message += f"  - Upper: {bb.get('upper', 'N/A')}\n"
            message += f"  - Middle: {bb.get('middle', 'N/A')}\n"
            message += f"  - Lower: {bb.get('lower', 'N/A')}\n"
    return message

def run_single_scan():
    """Run a single scan for testing purposes"""
    logger.info("Starting test scan...")
    
    try:
        # Initialize components
        alpaca = AlpacaConnector()
        sentiment_analyzer = FinBERTAnalyzer()
        technical_analyzer = TechnicalAnalysis()
        signal_engine = SignalEngine()
        discord = DiscordWebhook()
        
        # Send test alert
        discord.send_notification(
            message=(
                f"**Starting Test Scan**\n\n"
                f"**Symbols to Analyze:**\n"
                + "\n".join(f"• {symbol}" for symbol in TRADING_SYMBOLS)
            ),
            title="Test Scan Started"
        )
        
        # Process each symbol
        for symbol in TRADING_SYMBOLS:
            logger.info(f"Processing {symbol}...")
            
            # Get sentiment data
            sentiment_data = sentiment_analyzer.get_ticker_sentiment(symbol)
            logger.info(f"Sentiment data: {sentiment_data}")
            
            # Get technical signals
            technical_data = technical_analyzer.get_technical_signals(symbol)
            logger.info(f"Technical data summary: {technical_data.keys() if technical_data else 'None'}")
            
            # Send analysis results to Discord
            discord.send_notification(
                message=(
                    f"**Analysis Results for {symbol}**\n\n"
                    f"{format_sentiment_data(sentiment_data)}\n\n"
                    f"{format_technical_data(technical_data)}"
                ),
                title=f"Analysis: {symbol}"
            )
            
            # Generate trade signals
            signals = signal_engine.generate_signals(symbol, sentiment_data, technical_data)
            logger.info(f"Generated {len(signals)} signals")
            
            # Send alerts for valid signals
            for signal in signals:
                discord.send_notification(
                    message=str(signal),
                    title=f"Trade Signal: {symbol}"
                )
                logger.info(f"Sent alert for {symbol}")
        
        # Send completion notification
        discord.send_notification(
            message="The test scan has completed successfully.",
            title="Test Scan Completed"
        )
        
        logger.info("Test scan completed successfully")
        
    except Exception as e:
        logger.error(f"Error during test scan: {e}", exc_info=True)
        
        # Send error notification
        discord = DiscordWebhook()
        discord.send_notification(
            message=f"An error occurred during the test scan: {str(e)}",
            title="Test Scan Error"
        )

if __name__ == "__main__":
    run_single_scan()
