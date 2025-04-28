import logging
import json
import requests
from datetime import datetime

from config.config import DISCORD_WEBHOOK_URL

logger = logging.getLogger(__name__)

class DiscordAlert:
    """Sends alerts to Discord using webhooks"""
    
    def __init__(self, webhook_url=DISCORD_WEBHOOK_URL):
        self.webhook_url = webhook_url
    
    def send_trade_alert(self, signal):
        """Send a trade alert to Discord"""
        if not self.webhook_url:
            logger.error("Discord webhook URL not configured")
            return False
        
        try:
            # Create embed color (green for bullish, red for bearish)
            color = 0x00FF00 if signal['direction'] == 'bullish' else 0xFF0000
            
            # Create the Discord embed object
            embed = {
                "title": f"{signal['direction_emoji']} {signal['symbol']} {signal['option_type'].upper()} SIGNAL",
                "description": signal['summary'],
                "color": color,
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": f"Confidence: {signal['confidence_pct']} {signal['confidence_emoji']}"
                },
                "fields": [
                    {
                        "name": "Technical Analysis",
                        "value": self._format_technical_for_discord(signal),
                        "inline": False
                    },
                    {
                        "name": "Sentiment Analysis",
                        "value": self._format_sentiment_for_discord(signal),
                        "inline": False
                    }
                ]
            }
            
            # Create the webhook payload
            payload = {
                "username": "Options Swing Trader",
                "content": f"New {signal['direction'].upper()} signal for {signal['symbol']} {signal['option_type'].upper()}",
                "embeds": [embed]
            }
            
            # Send the webhook
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            logger.info(f"Discord alert sent for {signal['symbol']} {signal['option_type']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")
            return False
    
    def _format_technical_for_discord(self, signal):
        """Format technical analysis data for Discord message"""
        if 'analysis' not in signal or 'technical' not in signal['analysis']:
            return "No technical data available"
            
        tech_data = signal['analysis']['technical']
        formatted = ""
        
        for timeframe, data in tech_data.items():
            # Add emoji indicator based on bullish vs bearish signals
            emoji = "🔵"  # neutral by default
            if 'bullish_signals' in data and 'bearish_signals' in data:
                bulls = data['bullish_signals']
                bears = data['bearish_signals']
                
                if bulls > bears:
                    emoji = "🟢"  # bullish
                elif bears > bulls:
                    emoji = "🔴"  # bearish
            
            formatted += f"{emoji} **{timeframe.upper()}**: "
            if 'bullish_signals' in data and 'bearish_signals' in data:
                formatted += f"Bull {data['bullish_signals']} vs Bear {data['bearish_signals']}\n"
            else:
                formatted += "No data\n"
        
        return formatted
    
    def _format_sentiment_for_discord(self, signal):
        """Format sentiment analysis data for Discord message"""
        if 'analysis' not in signal or 'sentiment' not in signal['analysis']:
            return "No sentiment data available"
            
        sent_data = signal['analysis']['sentiment']
        formatted = ""
        
        # Add sentiment score and label
        if 'overall_score' in sent_data:
            score = sent_data['overall_score']
            emoji = "🟢" if score > 0 else "🔴" if score < 0 else "🔵"
            formatted += f"{emoji} **Score**: {score:.2f}\n"
            
        if 'sentiment_label' in sent_data:
            formatted += f"**Sentiment**: {sent_data['sentiment_label'].upper()}\n"
            
        if 'article_count' in sent_data:
            formatted += f"**Articles**: {sent_data['article_count']}\n"
        
        # Add keyword matches
        if 'keyword_matches' in sent_data:
            keyword_matches = sent_data['keyword_matches']
            if keyword_matches:
                # Sort keywords by count and get top 3
                top_keywords = sorted(keyword_matches.items(), key=lambda x: x[1], reverse=True)[:3]
                kw_text = ', '.join([f"{kw} ({count})" for kw, count in top_keywords if count > 0])
                if kw_text:
                    formatted += f"**Top Keywords**: {kw_text}"
        
        return formatted
    
    def send_system_notification(self, title, message):
        """Send a system notification to Discord"""
        if not self.webhook_url:
            logger.error("Discord webhook URL not configured")
            return False
        
        try:
            # Create the webhook payload
            payload = {
                "username": "Options Swing Trader",
                "content": f"**{title}**\n{message}"
            }
            
            # Send the webhook
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            logger.info(f"System notification sent: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending system notification: {e}")
            return False
