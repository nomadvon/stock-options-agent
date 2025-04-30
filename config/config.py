import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_API_SECRET = os.getenv('ALPACA_API_SECRET')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Trading Parameters
TRADING_SYMBOLS = [
    'QQQ', 'SPY'         # ETFs
]

# Option Parameters
OPTION_TYPES = ['call', 'put']
DTE_RANGE = (1, 20)  # Days to expiration range for options
DELTA_RANGE = (0.3, 0.7)  # Delta range for option selection

# Stop Loss and Take Profit Levels
STOP_LOSS_LEVELS = [-0.15, -0.30]  # 15% and 30% stop loss
TAKE_PROFIT_LEVELS = [0.25, 0.50]  # 25% and 50% take profit

# Sentiment Analysis Parameters
SENTIMENT_KEYWORDS = [
    'tariffs', 'trade war', 'Donald Trump', 'Trump',
    'tech regulation', 'antitrust', 'Federal Reserve',
    'interest rates', 'inflation', 'AI', 'artificial intelligence',
    'earnings', 'revenue', 'guidance', 'forecast'
]

# Technical Parameters
TECHNICAL_TIMEFRAMES = ['1h', '4h', '1d']  # Time frames for technical analysis
RSI_THRESHOLDS = {'oversold': 30, 'overbought': 70}
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Signal Engine Parameters
SENTIMENT_WEIGHT = 0.4
TECHNICAL_WEIGHT = 0.6
SIGNAL_THRESHOLD = 0.7  # Minimum score to generate a signal

# System Parameters
SCAN_INTERVAL = 1800  # Scan interval in seconds (30 mins)
MARKET_HOURS = {
    'open': '09:30',
    'close': '16:00',
    'timezone': 'America/New_York'
}

# Logging Parameters
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/trading_agent.log'
