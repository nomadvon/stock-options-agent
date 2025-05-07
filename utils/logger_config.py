import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import colorlog

def setup_logging():
    """Configure logging with separate files for different components"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # Create today's log directory
    today = datetime.now().strftime('%Y-%m-%d')
    today_log_dir = f'logs/{today}'
    if not os.path.exists(today_log_dir):
        os.makedirs(today_log_dir)
    
    # Configure root logger to only show warnings and above
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    
    # Common formatter for console handlers
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white'
        }
    )
    
    # Price Action Logger
    price_logger = logging.getLogger('price_action')
    price_logger.setLevel(logging.INFO)
    price_logger.propagate = False  # Prevent propagation to root logger
    
    # Console handler
    price_console_handler = colorlog.StreamHandler()
    price_console_handler.setFormatter(console_formatter)
    price_logger.addHandler(price_console_handler)
    
    # File handler
    price_handler = RotatingFileHandler(
        f'{today_log_dir}/price_action.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    price_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    price_logger.addHandler(price_handler)
    
    # Box Method Logger
    box_logger = logging.getLogger('box_method')
    box_logger.setLevel(logging.INFO)
    box_logger.propagate = False  # Prevent propagation to root logger
    
    # Console handler
    box_console_handler = colorlog.StreamHandler()
    box_console_handler.setFormatter(console_formatter)
    box_logger.addHandler(box_console_handler)
    
    # File handler
    box_handler = RotatingFileHandler(
        f'{today_log_dir}/box_method.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    box_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    box_logger.addHandler(box_handler)
    
    # Trade Logger
    trade_logger = logging.getLogger('trades')
    trade_logger.setLevel(logging.INFO)
    trade_logger.propagate = False  # Prevent propagation to root logger
    
    # Console handler
    trade_console_handler = colorlog.StreamHandler()
    trade_console_handler.setFormatter(console_formatter)
    trade_logger.addHandler(trade_console_handler)
    
    # File handler
    trade_handler = RotatingFileHandler(
        f'{today_log_dir}/trades.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    trade_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    trade_logger.addHandler(trade_handler)
    
    # Error Logger
    error_logger = logging.getLogger('errors')
    error_logger.setLevel(logging.ERROR)
    error_logger.propagate = False  # Prevent propagation to root logger
    
    # Console handler
    error_console_handler = colorlog.StreamHandler()
    error_console_handler.setFormatter(console_formatter)
    error_logger.addHandler(error_console_handler)
    
    # File handler
    error_handler = RotatingFileHandler(
        f'{today_log_dir}/errors.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    error_logger.addHandler(error_handler)
    
    return {
        'price_action': price_logger,
        'box_method': box_logger,
        'trades': trade_logger,
        'errors': error_logger
    } 