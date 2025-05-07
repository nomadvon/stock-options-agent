import logging
import json
import requests
import os
from typing import Dict, Any
from datetime import datetime

class DiscordWebhook:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        self.logs_webhook_url = os.getenv('DISCORD_LOGS_WEBHOOK_URL')
        
        if not self.webhook_url:
            raise ValueError("DISCORD_WEBHOOK_URL environment variable is required")
        if not self.logs_webhook_url:
            raise ValueError("DISCORD_LOGS_WEBHOOK_URL environment variable is required")
            
    def test_connection(self) -> bool:
        """Test the Discord webhook connections"""
        try:
            # Test main webhook
            embed = {
                "title": "Discord Webhook Test",
                "description": "Testing main webhook connection...",
                "color": 0x00ff00,
                "timestamp": datetime.now().isoformat()
            }
            
            message = {
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=message)
            response.raise_for_status()
            self.logger.info("Main Discord webhook test successful")
            
            # Test logs webhook
            embed["description"] = "Testing logs webhook connection..."
            response = requests.post(self.logs_webhook_url, json=message)
            response.raise_for_status()
            self.logger.info("Logs Discord webhook test successful")
            
            return True
        except Exception as e:
            self.logger.error(f"Discord webhook test failed: {str(e)}")
            return False
            
    def send_signal(self, signal: Dict[str, Any]):
        """Send a trading signal to Discord"""
        try:
            # Format take profit levels
            tp_levels = "\n".join([
                f"• TP{i+1}: ${tp:.2f} (+{((tp - signal['entry_price']) / signal['entry_price'] * 100):.1f}%)"
                for i, tp in enumerate(signal['take_profits'])
            ])
            
            # Create embed for the signal
            embed = {
                "title": f"📈 BOX BREAKOUT SIGNAL - {signal['symbol']}",
                "color": 0x00ff00,  # Green color
                "fields": [
                    {
                        "name": "Signal Details",
                        "value": (
                            f"**Type:** {signal['option_type'].upper()}\n"
                            f"**Entry:** ${signal['entry_price']:.2f}\n"
                            f"**Stop Loss:** ${signal['stop_loss']:.2f}\n"
                            f"**Box Range:** ${signal['box_top']:.2f} - ${signal['box_bottom']:.2f}\n"
                            f"**Premium:** ${signal['premium']:.2f}\n"
                            f"**Position Size:** {signal['position_size']} contracts\n"
                            f"**Risk Amount:** ${signal['risk_amount']:.2f}"
                        ),
                        "inline": False
                    },
                    {
                        "name": "Take Profit Levels",
                        "value": tp_levels,
                        "inline": False
                    },
                    {
                        "name": "Analysis",
                        "value": signal['explanation'],
                        "inline": False
                    }
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            message = {
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=message)
            if response.status_code != 204:
                self.logger.error(f"Failed to send Discord message: {response.text}")
                
        except Exception as e:
            self.logger.error(f"Error sending Discord signal: {str(e)}")
            
    def send_update(self, update: Dict[str, Any]):
        """Send a trade update to Discord"""
        try:
            update_type = update.get('type', '')
            self.logger.info(f"Sending Discord update of type: {update_type}")
            
            if update_type == 'sentiment_update':
                embed = {
                    "title": "🔄 SENTIMENT UPDATE",
                    "color": 0x00ff00,  # Green color
                    "fields": [
                        {
                            "name": "Symbol",
                            "value": update['symbol'],
                            "inline": True
                        },
                        {
                            "name": "New Sentiment",
                            "value": f"{update['new_sentiment']:.2f}",
                            "inline": True
                        },
                        {
                            "name": "Details",
                            "value": update['explanation'],
                            "inline": False
                        }
                    ],
                    "timestamp": datetime.now().isoformat()
                }
            elif update_type == 'startup':
                embed = {
                    "title": "🤖 PRODUCTION DEPLOYMENT",
                    "description": update.get('message', 'Options Trading Agent Started in Production Mode'),
                    "color": 0x00ff00,  # Green color
                    "fields": [
                        {
                            "name": "Symbols to Monitor",
                            "value": "• SPY\n• QQQ\n• IWM",
                            "inline": False
                        },
                        {
                            "name": "Market Hours",
                            "value": "09:30 - 16:00 ET",
                            "inline": True
                        },
                        {
                            "name": "Mode",
                            "value": "Real-time event processing",
                            "inline": True
                        }
                    ],
                    "timestamp": datetime.now().isoformat()
                }
            elif update_type == 'market_hours':
                embed = {
                    "title": "⏰ MARKET HOURS",
                    "description": update.get('message', 'Market is currently closed'),
                    "color": 0xffff00,  # Yellow color
                    "timestamp": datetime.now().isoformat()
                }
            elif update_type == 'error':
                embed = {
                    "title": "⚠️ ERROR",
                    "description": update.get('message', 'An error occurred'),
                    "color": 0xff9900,  # Orange color
                    "timestamp": datetime.now().isoformat()
                }
            elif update_type == 'fatal_error':
                embed = {
                    "title": "🚨 FATAL ERROR",
                    "description": update.get('message', 'A fatal error occurred'),
                    "color": 0xff0000,  # Red color
                    "timestamp": datetime.now().isoformat()
                }
            else:
                embed = {
                    "title": "⚠️ UNKNOWN UPDATE",
                    "description": f"Unknown update type: {update_type}",
                    "color": 0xff0000,  # Red color for errors
                    "timestamp": datetime.now().isoformat()
                }
            
            message = {
                "embeds": [embed]
            }
            
            self.logger.info(f"Sending Discord message to webhook: {self.webhook_url}")
            response = requests.post(self.webhook_url, json=message)
            if response.status_code != 204:
                self.logger.error(f"Failed to send Discord update: {response.text}")
            else:
                self.logger.info("Successfully sent Discord update")
                
        except Exception as e:
            self.logger.error(f"Error sending Discord update: {str(e)}")
            
    def stream_logs(self, log_type: str, message: str):
        """Stream logs to a separate Discord channel"""
        try:
            embed = {
                "title": f"📊 {log_type.upper()}",
                "description": message,
                "color": 0x00ff00,  # Green color
                "timestamp": datetime.now().isoformat()
            }
            
            message = {
                "embeds": [embed]
            }
            
            self.logger.info(f"Sending {log_type} log to Discord")
            response = requests.post(self.logs_webhook_url, json=message)
            if response.status_code != 204:
                self.logger.error(f"Failed to send {log_type} log to Discord: {response.text}")
            else:
                self.logger.info(f"Successfully sent {log_type} log to Discord")
                
        except Exception as e:
            self.logger.error(f"Error sending {log_type} log to Discord: {str(e)}") 