import logging
import pytz
from datetime import datetime

from config.config import MARKET_HOURS

logger = logging.getLogger(__name__)

def is_market_open():
    """Check if the market is currently open"""
    try:
        eastern = pytz.timezone('America/New_York')
        now = datetime.now(eastern)
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # 5 is Saturday, 6 is Sunday
            return False
            
        # Convert market hours to current day
        market_open = datetime.strptime(MARKET_HOURS['open'], '%H:%M').time()
        market_close = datetime.strptime(MARKET_HOURS['close'], '%H:%M').time()
        
        # Check if current time is within market hours
        current_time = now.time()
        return market_open <= current_time <= market_close
    
    except Exception as e:
        logger.error(f"Error checking if market is open: {e}")
        # Default to assuming market is open on error
        return True

def format_option_symbol(ticker, expiration_date, strike, option_type):
    """Format an option symbol in standard OCC format"""
    try:
        # Parse date (assuming format is YYYY-MM-DD)
        exp_date = datetime.strptime(expiration_date, '%Y-%m-%d')
        
        # Format according to OCC standard (e.g. AAPL230915C00180000)
        exp_str = exp_date.strftime('%y%m%d')
        strike_str = str(int(float(strike) * 1000)).zfill(8)  # Convert to cents and pad with zeros
        opt_type = 'C' if option_type.lower() == 'call' else 'P'
        
        return f"{ticker}{exp_str}{opt_type}{strike_str}"
    
    except Exception as e:
        logger.error(f"Error formatting option symbol: {e}")
        return None

def parse_option_symbol(option_symbol):
    """Parse an OCC option symbol to its components"""
    try:
        # Find where the date part begins (first digit after ticker)
        for i, char in enumerate(option_symbol):
            if char.isdigit():
                ticker_end = i
                break
        else:
            return None
        
        ticker = option_symbol[:ticker_end]
        date_part = option_symbol[ticker_end:ticker_end+6]
        opt_type = option_symbol[ticker_end+6]
        strike_part = option_symbol[ticker_end+7:]
        
        # Parse date (YY MM DD)
        year = int('20' + date_part[:2])
        month = int(date_part[2:4])
        day = int(date_part[4:6])
        expiration_date = f"{year}-{month:02d}-{day:02d}"
        
        # Parse strike (convert from cents to dollars)
        strike = float(strike_part) / 1000
        
        # Get option type
        option_type = 'call' if opt_type == 'C' else 'put'
        
        return {
            'ticker': ticker,
            'expiration_date': expiration_date,
            'strike': strike,
            'option_type': option_type
        }
    
    except Exception as e:
        logger.error(f"Error parsing option symbol {option_symbol}: {e}")
        return None
