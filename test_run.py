import logging
from config.logging_config import setup_logging
from data.polygon_connector import PolygonConnector
from analysis.sentiment.finbert_analyzer import FinBERTAnalyzer
from analysis.technical.indicators import TechnicalAnalysis
from engine.signal_engine import SignalEngine
from alerts.discord_webhook import DiscordAlert
from config.config import TRADING_SYMBOLS

# Setup logging
logger = setup_logging()

def run_single_scan():
    """Run a single scan for testing purposes"""
    logger.info("Starting test scan...")
    
    try:
        # Initialize components
        polygon = PolygonConnector()
        sentiment_analyzer = FinBERTAnalyzer()
        technical_analyzer = TechnicalAnalysis()
        signal_engine = SignalEngine()
        discord_alert = DiscordAlert()
        
        # Send test alert
        discord_alert.send_system_notification(
            "Test Scan Started",
            f"Running a test scan for: {', '.join(TRADING_SYMBOLS)}"
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
            
            # Generate trade signals
            signals = signal_engine.generate_signals(symbol, sentiment_data, technical_data)
            logger.info(f"Generated {len(signals)} signals")
            
            # Send alerts for valid signals
            for signal in signals:
                discord_alert.send_trade_alert(signal)
                logger.info(f"Sent alert for {symbol}")
        
        # Send completion notification
        discord_alert.send_system_notification(
            "Test Scan Completed",
            "The test scan has completed successfully."
        )
        
        logger.info("Test scan completed successfully")
        
    except Exception as e:
        logger.error(f"Error during test scan: {e}", exc_info=True)
        
        # Send error notification
        discord_alert = DiscordAlert()
        discord_alert.send_system_notification(
            "Test Scan Error",
            f"An error occurred during the test scan: {str(e)}"
        )

if __name__ == "__main__":
    run_single_scan()
