import logging
import time
import schedule
from datetime import datetime
import pytz

from config.config import TRADING_SYMBOLS, SCAN_INTERVAL, MARKET_HOURS
from config.logging_config import setup_logging
from data.alpaca_connector import AlpacaConnector
from analysis.sentiment.finbert_analyzer import FinBERTAnalyzer
from analysis.technical.indicators import TechnicalAnalysis
from engine.signal_engine import SignalEngine
from alerts.discord_webhook import DiscordAlert
from utils.helpers import is_market_open
from utils.aws_utils import AWSIntegration  # New import for AWS integration

# Setup logging
logger = setup_logging()

def scan_for_opportunities():
    """Main function to scan for trading opportunities"""
    logger.info("Starting scan for trading opportunities...")
    
    try:
        # Initialize components
        alpaca = AlpacaConnector()
        sentiment_analyzer = FinBERTAnalyzer()
        technical_analyzer = TechnicalAnalysis()
        signal_engine = SignalEngine()
        discord_alert = DiscordAlert()
        aws = AWSIntegration()  # Initialize AWS integration
        
        # Track signals for metrics
        signal_count = 0
        
        # Process each symbol
        for symbol in TRADING_SYMBOLS:
            logger.info(f"Processing {symbol}...")
            
            # Get sentiment data
            sentiment_data = sentiment_analyzer.get_ticker_sentiment(symbol)
            
            # Record sentiment as CloudWatch metric
            if sentiment_data and 'overall_score' in sentiment_data:
                aws.put_metric("SentimentScore", sentiment_data['overall_score'], symbol, "None")
            
            # Get technical signals
            technical_data = technical_analyzer.get_technical_signals(symbol)
            
            # Generate trade signals
            signals = signal_engine.generate_signals(symbol, sentiment_data, technical_data)
            signal_count += len(signals)
            
            # Send alerts for valid signals
            for signal in signals:
                if signal['confidence'] >= signal_engine.signal_threshold:
                    discord_alert.send_trade_alert(signal)
                    
                    # Record signal details in CloudWatch
                    aws.put_metric("SignalConfidence", signal['confidence'], symbol, "None")
                    aws.put_metric("SignalGenerated", 1, symbol, "Count")
        
        # Record scan metrics
        aws.put_metric("TotalSignals", signal_count, "ALL", "Count")
        aws.put_metric("ScanCompleted", 1, "ALL", "Count")
        
        logger.info("Scan completed successfully")
        
    except Exception as e:
        logger.error(f"Error during scan: {e}", exc_info=True)
        
        # Record error in CloudWatch
        try:
            aws = AWSIntegration()
            aws.put_metric("ScanError", 1, "ALL", "Count")
        except:
            pass  # Avoid errors in error handling

def main():
    """Main entry point"""
    logger.info("Starting Real-Time Stock Options Swing Trade Agent")
    
    # Initialize AWS integration
    aws = AWSIntegration()
    
    # Send startup notification
    discord_alert = DiscordAlert()
    discord_alert.send_system_notification(
        "Swing Trade Agent Started",
        f"The Options Swing Trade Agent has started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.\n"
        f"Monitoring: {', '.join(TRADING_SYMBOLS)}\n"
        f"Scan interval: {SCAN_INTERVAL} seconds"
    )
    
    # Record startup in CloudWatch
    aws.put_metric("AgentStartup", 1, "ALL", "Count")
    
    # Run initial scan
    scan_for_opportunities()
    
    # Schedule regular scans
    schedule.every(SCAN_INTERVAL).seconds.do(scan_for_opportunities)
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        
        # Send shutdown notification
        discord_alert.send_system_notification(
            "Agent Stopped",
            f"The Options Swing Trade Agent has been stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        )
        
        # Record shutdown in CloudWatch
        aws.put_metric("AgentShutdown", 1, "ALL", "Count")

if __name__ == "__main__":
    main()
