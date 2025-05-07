import logging
import numpy as np
from datetime import datetime, timedelta
from analysis.technical.box_analyzer import BoxAnalyzer
from analysis.technical.technical_analyzer import TechnicalAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_box_pattern(base_price: float, box_size: float, num_candles: int = 20) -> tuple:
    """Generate a realistic box pattern with pre-box, box, and breakout phases"""
    prices = []
    volumes = []
    timestamps = []
    current_time = datetime.now()
    
    # Pre-box phase (trending up to box)
    for i in range(5):
        trend = base_price * (1 + 0.001 * i)  # Slight uptrend
        noise = np.random.normal(0, base_price * 0.001)  # 0.1% noise
        prices.append(trend + noise)
        volumes.append(np.random.uniform(8000, 10000))  # Normal volume
        timestamps.append(current_time - timedelta(minutes=(num_candles-i)))
    
    # Box phase (consolidation)
    box_center = prices[-1]  # Last price of pre-box phase
    box_half_range = box_size / 2
    for i in range(10):
        price = box_center + np.random.uniform(-box_half_range, box_half_range)
        prices.append(price)
        volumes.append(np.random.uniform(5000, 7000))  # Lower volume in consolidation
        timestamps.append(current_time - timedelta(minutes=(num_candles-5-i)))
    
    # Breakout phase
    breakout_price = box_center + (box_half_range * 1.5)  # Break above box
    prices.append(breakout_price)
    volumes.append(15000)  # High volume on breakout
    timestamps.append(current_time)
    
    return prices, volumes, timestamps

def test_box_detection():
    """Test box detection with simulated price data"""
    logger.info("Testing box detection...")
    
    # Create box analyzer
    box_analyzer = BoxAnalyzer()
    
    # Generate realistic box pattern
    base_price = 100.0
    box_size = base_price * box_analyzer.box_size_threshold
    prices, volumes, timestamps = generate_box_pattern(base_price, box_size)
    
    # Log the pattern
    logger.info("\nPrice Pattern:")
    for i, (price, volume) in enumerate(zip(prices, volumes)):
        logger.info(f"Candle {i+1}: Price=${price:.2f}, Volume={volume:.0f}")
    
    # Detect box
    result = box_analyzer.detect_box(prices, volumes, timestamps)
    
    if result:
        box_top, box_bottom, breakout_price, breakout_volume = result
        logger.info("\nBox detected successfully!")
        logger.info(f"Box Top: ${box_top:.2f}")
        logger.info(f"Box Bottom: ${box_bottom:.2f}")
        logger.info(f"Breakout Price: ${breakout_price:.2f}")
        logger.info(f"Breakout Volume: {breakout_volume:.0f}")
        logger.info(f"Box Range: {((box_top - box_bottom) / box_bottom * 100):.1f}%")
    else:
        logger.error("Failed to detect box!")

def test_position_sizing():
    """Test position sizing calculations"""
    logger.info("\nTesting position sizing...")
    
    box_analyzer = BoxAnalyzer()
    
    # Test case 1: Small risk
    entry_price = 100.0
    stop_loss = 98.0
    account_value = 1000.0
    
    num_contracts, risk_amount = box_analyzer.calculate_position_size(
        entry_price, stop_loss, account_value
    )
    
    logger.info("Position Sizing Test 1:")
    logger.info(f"Entry: ${entry_price:.2f}")
    logger.info(f"Stop Loss: ${stop_loss:.2f}")
    logger.info(f"Account Value: ${account_value:.2f}")
    logger.info(f"Number of Contracts: {num_contracts}")
    logger.info(f"Risk Amount: ${risk_amount:.2f}")
    logger.info(f"Risk Per Contract: ${(entry_price - stop_loss):.2f}")
    
    # Test case 2: Larger risk
    entry_price = 200.0
    stop_loss = 196.0
    account_value = 5000.0
    
    num_contracts, risk_amount = box_analyzer.calculate_position_size(
        entry_price, stop_loss, account_value
    )
    
    logger.info("\nPosition Sizing Test 2:")
    logger.info(f"Entry: ${entry_price:.2f}")
    logger.info(f"Stop Loss: ${stop_loss:.2f}")
    logger.info(f"Account Value: ${account_value:.2f}")
    logger.info(f"Number of Contracts: {num_contracts}")
    logger.info(f"Risk Amount: ${risk_amount:.2f}")
    logger.info(f"Risk Per Contract: ${(entry_price - stop_loss):.2f}")

def test_take_profits():
    """Test take profit calculations"""
    logger.info("\nTesting take profit calculations...")
    
    box_analyzer = BoxAnalyzer()
    
    # Test case 1: Long trade
    entry_price = 100.0
    stop_loss = 98.0
    is_long = True
    risk = entry_price - stop_loss
    
    take_profits = box_analyzer.calculate_take_profits(
        entry_price, stop_loss, is_long
    )
    
    logger.info("Take Profit Test 1 (Long):")
    logger.info(f"Entry: ${entry_price:.2f}")
    logger.info(f"Stop Loss: ${stop_loss:.2f}")
    logger.info(f"Risk: ${risk:.2f}")
    for i, tp in enumerate(take_profits):
        reward = tp - entry_price
        rr_ratio = reward / risk
        logger.info(f"TP{i+1}: ${tp:.2f} (+{((tp - entry_price) / entry_price * 100):.1f}%) R:R={rr_ratio:.1f}")
    
    # Test case 2: Short trade
    entry_price = 100.0
    stop_loss = 102.0
    is_long = False
    risk = stop_loss - entry_price
    
    take_profits = box_analyzer.calculate_take_profits(
        entry_price, stop_loss, is_long
    )
    
    logger.info("\nTake Profit Test 2 (Short):")
    logger.info(f"Entry: ${entry_price:.2f}")
    logger.info(f"Stop Loss: ${stop_loss:.2f}")
    logger.info(f"Risk: ${risk:.2f}")
    for i, tp in enumerate(take_profits):
        reward = entry_price - tp
        rr_ratio = reward / risk
        logger.info(f"TP{i+1}: ${tp:.2f} (-{((entry_price - tp) / entry_price * 100):.1f}%) R:R={rr_ratio:.1f}")

def test_box_retest():
    """Test box retest validation"""
    logger.info("\nTesting box retest validation...")
    
    box_analyzer = BoxAnalyzer()
    
    # Test case 1: Valid retest
    box_top = 100.0
    box_bottom = 98.0
    box_range = box_top - box_bottom
    current_price = box_top + (box_range * box_analyzer.box_retest_tolerance * 0.9)  # Just within tolerance
    
    is_valid = box_analyzer.validate_box_retest(
        current_price, box_top, box_bottom
    )
    
    logger.info("Box Retest Test 1:")
    logger.info(f"Box Top: ${box_top:.2f}")
    logger.info(f"Box Bottom: ${box_bottom:.2f}")
    logger.info(f"Box Range: ${box_range:.2f}")
    logger.info(f"Current Price: ${current_price:.2f}")
    logger.info(f"Distance from Box: ${(current_price - box_top):.3f}")
    logger.info(f"Max Allowed Distance: ${(box_range * box_analyzer.box_retest_tolerance):.3f}")
    logger.info(f"Valid Retest: {is_valid}")
    
    # Test case 2: Invalid retest
    current_price = box_top + (box_range * box_analyzer.box_retest_tolerance * 1.1)  # Just outside tolerance
    
    is_valid = box_analyzer.validate_box_retest(
        current_price, box_top, box_bottom
    )
    
    logger.info("\nBox Retest Test 2:")
    logger.info(f"Box Top: ${box_top:.2f}")
    logger.info(f"Box Bottom: ${box_bottom:.2f}")
    logger.info(f"Box Range: ${box_range:.2f}")
    logger.info(f"Current Price: ${current_price:.2f}")
    logger.info(f"Distance from Box: ${(current_price - box_top):.3f}")
    logger.info(f"Max Allowed Distance: ${(box_range * box_analyzer.box_retest_tolerance):.3f}")
    logger.info(f"Valid Retest: {is_valid}")

if __name__ == "__main__":
    logger.info("Starting Box Method Tests...")
    
    # Run tests
    test_box_detection()
    test_position_sizing()
    test_take_profits()
    test_box_retest()
    
    logger.info("\nBox Method Tests Completed!") 