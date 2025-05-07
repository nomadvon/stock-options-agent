import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_API_SECRET = os.getenv('ALPACA_API_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Trading Symbols
TRADING_SYMBOLS = [
    'SPY',    # S&P 500 ETF
    'QQQ',    # Nasdaq 100 ETF
    'IWM'     # Russell 2000 ETF
]

# Market Check Intervals
MARKET_EVENTS_CHECK_INTERVAL_HOURS = 0.1  # Check every 6 minutes

# Option Parameters
OPTION_TYPES = ['call', 'put']
DTE_RANGE = [5, 30]  # Days to expiration range
DELTA_RANGE = [0.3, 0.7]  # Delta range for option selection

# Box Method Parameters
BOX_SIZE_THRESHOLD = 0.02  # 2% price range
MIN_CONSOLIDATION_CANDLES = 5
VOLUME_THRESHOLD_MULTIPLIER = 1.3
BOX_RETEST_TOLERANCE = 0.005

# Risk Management
STOP_LOSS_TOLERANCE = 0.005
MAX_CONCURRENT_TRADES = 2
RISK_PER_TRADE = 0.02  # 2% of capital
RISK_REWARD_RATIOS = [2, 3, 4]

# Take Profit and Stop Loss Levels
TAKE_PROFIT_LEVELS = [
    0.02,  # 2% profit
    0.04,  # 4% profit
    0.06   # 6% profit
]

STOP_LOSS_LEVELS = [
    0.01,  # 1% loss
    0.02   # 2% loss
]

# Sentiment Keywords
SENTIMENT_KEYWORDS = [
    # Bullish keywords
    'breakout', 'upgrade', 'beat', 'growth', 'innovation',
    'launch', 'partnership', 'expansion', 'acquisition',
    'bullish', 'outperform', 'buy', 'strong',
    
    # Bearish keywords
    'breakdown', 'downgrade', 'miss', 'decline', 'risk',
    'lawsuit', 'investigation', 'recall', 'bearish',
    'underperform', 'sell', 'weak'
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

# Check interval in minutes
CHECK_INTERVAL_MINUTES = 15
