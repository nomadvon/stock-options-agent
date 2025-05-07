import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime

from config.config import (
    DISCORD_WEBHOOK_URL,
    TRADING_SYMBOLS,
    TAKE_PROFIT_LEVELS,
    STOP_LOSS_LEVELS
)
from analysis.news.market_events import MarketEventsMonitor

logger = logging.getLogger(__name__)

class DiscordWebhook:
    """Handles sending notifications to Discord"""
    
    def __init__(self):
        self.webhook_url = DISCORD_WEBHOOK_URL
        self.market_events_monitor = MarketEventsMonitor()
        
        # Emoji mappings
        self.option_type_emojis = {
            'call': '🟢',  # Green circle for calls
            'put': '🔴'    # Red circle for puts
        }
    
    def send_notification(self, message: str, title: str = None):
        """Send a notification to Discord"""
        try:
            # Format the message payload
            payload = {
                "embeds": [{
                    "title": title,
                    "description": message,
                    "color": 0x00ff00,  # Green color
                    "timestamp": datetime.now().isoformat()
                }]
            }
            
            # Send the request
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 204:
                logger.error(f"Failed to send Discord notification: {response.text}")
            
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
    
    def send_market_events(self):
        """Send market events notifications"""
        try:
            # Get market events
            events = self.market_events_monitor.get_market_events()
            
            # Send notifications for tech earnings
            for event in events.get('tech_earnings', []):
                message = (
                    f"**Upcoming Tech Earnings**\n"
                    f"• {event['symbol']}: {event['date']}\n"
                    f"• Expected Move: {event['expected_move']}%"
                )
                self.send_notification(message, "Earnings Alert")
            
            # Send notifications for Fed speeches
            for event in events.get('fed_speeches', []):
                message = (
                    f"**Federal Reserve Speech**\n"
                    f"• Speaker: {event['speaker']}\n"
                    f"• Time: {event['time']}\n"
                    f"• Topic: {event['topic']}"
                )
                self.send_notification(message, "Fed Speech Alert")
            
        except Exception as e:
            logger.error(f"Error sending market events: {e}")
    
    def send_options_signal(self, symbol: str, current_price: float, option_type: str, 
                          expiration_date: str, premium: float, 
                          take_profit_levels: List[float] = None,
                          stop_loss_levels: List[float] = None,
                          ai_analysis: str = None):
        """Send an options trading signal to Discord"""
        try:
            # Use default levels if none provided
            if take_profit_levels is None:
                take_profit_levels = TAKE_PROFIT_LEVELS
            if stop_loss_levels is None:
                stop_loss_levels = STOP_LOSS_LEVELS
            
            # Get emoji for option type
            option_emoji = self.option_type_emojis.get(option_type.lower(), '⚪')  # Default to white circle if unknown
            
            # Format take profit levels with both premium price and percentage
            tp_formatted = [
                f"${premium * (1 + tp):.2f} (+{tp * 100:.1f}%)" 
                for tp in take_profit_levels
            ]
            
            # Format stop loss levels with both premium price and percentage
            sl_formatted = [
                f"${premium * (1 + sl):.2f} ({sl * 100:.1f}%)" 
                for sl in stop_loss_levels
            ]
            
            # Format the current stock price message
            current_price_message = (
                f"**Current Stock Price:** ${current_price:.2f}\n\n"
            )
            
            # Format the options signal message
            options_message = (
                f"**Ticker:** {symbol}\n"
                f"**Option Type:** {option_emoji} {option_type.upper()}\n"
                f"**Premium Price:** ${premium:.2f}\n"
                f"**Exp. Date:** {expiration_date}\n"
                f"**Take Profit Levels:** {', '.join(tp_formatted)}\n"
                f"**Stop Loss Levels:** {', '.join(sl_formatted)}"
            )
            
            # Format the complete message
            message = current_price_message + options_message
            
            # Add AI analysis if provided
            if ai_analysis:
                try:
                    # Parse the AI analysis JSON
                    import json
                    analysis_data = json.loads(ai_analysis)
                    
                    # Add spacing between sections
                    message += "\n\n**📊 Technical Analysis:**\n"
                    
                    # Add entry points
                    if 'entry_points' in analysis_data:
                        message += f"**Entry Points:**\n"
                        for direction, price in analysis_data['entry_points'].items():
                            message += f"• {direction.title()}: ${price}\n"
                    
                    # Add exit points
                    if 'exit_points' in analysis_data:
                        message += f"\n**Exit Points:**\n"
                        for direction, price in analysis_data['exit_points'].items():
                            message += f"• {direction.title()}: ${price}\n"
                    
                    # Add technical analysis
                    if 'analysis' in analysis_data:
                        message += f"\n**Analysis:**\n{analysis_data['analysis']}\n"
                    
                    # Add beginner-friendly explanation
                    if 'simplified_analysis' in analysis_data:
                        message += f"\n**🔰 What This Means for Beginners:**\n{analysis_data['simplified_analysis']}\n"
                    
                    # Add confidence with reason
                    if 'confidence' in analysis_data and 'confidence_reason' in analysis_data:
                        confidence_emoji = "🟢" if analysis_data['confidence'] == "High" else "🟡" if analysis_data['confidence'] == "Medium" else "🔴"
                        message += f"\n**Confidence:** {confidence_emoji} {analysis_data['confidence']}\n**Why?** {analysis_data['confidence_reason']}\n"
                    
                    # Add key levels
                    if 'key_levels' in analysis_data:
                        message += f"\n**📍 Key Price Levels:**\n"
                        for level, price in analysis_data['key_levels'].items():
                            message += f"• {level.title()}: ${price}\n"
                            
                except json.JSONDecodeError:
                    # If AI analysis is not valid JSON, add it as plain text
                    message += f"\n\n**AI Analysis:**\n{ai_analysis}"
            
            # Send the notification
            self.send_notification(
                message=message,
                title=f"Options Signal: {symbol} {option_emoji}"
            )
            
        except Exception as e:
            logger.error(f"Error sending options signal: {e}")
