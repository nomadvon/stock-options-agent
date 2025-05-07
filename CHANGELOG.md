# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added `get_historical_data` method to `AlpacaConnector` class for fetching historical price data
- Added detailed logging in `BoxAnalyzer` for better debugging of box detection
- Added dual webhook support in `DiscordWebhook` class for separate trading signals and logs
- Added Discord webhook integration for trading signals and notifications
- Added Box Method technical analysis strategy implementation
- Added Alpaca API integration for real-time and historical data
- Added options chain simulation for testing purposes
- Added risk management parameters for position sizing and take profits

### Modified
- Modified `BoxAnalyzer.detect_box` method to include more detailed logging of box detection conditions
- Modified `AlpacaConnector.get_historical_data` to include better error handling and logging
- Modified options chain generation to include more realistic premium calculations
- Modified historical data fetching to support multiple timeframes (1d, 1h, 4h)

### Changed
- Changed box detection parameters in `BoxAnalyzer`:
  - Box size threshold: 2.0% of price range
  - Minimum consolidation candles: 5
  - Volume threshold multiplier: 1.3x
  - Box retest tolerance: 0.5%
- Changed risk management parameters:
  - Risk per trade: $25
  - Risk-reward ratios: [2, 3, 4]
  - Stop loss additional range: 0.35%

### Fixed
- Fixed issue with historical data format in `AlpacaConnector.get_historical_data` to match expected format for technical analysis
- Fixed options chain simulation to handle edge cases and provide more realistic data
- Fixed timezone handling in historical data requests

### Removed
- Removed direct options data access (replaced with simulation for testing)
- Removed delta-based filtering (due to API limitations) 