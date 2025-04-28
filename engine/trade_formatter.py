import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TradeFormatter:
    """Formats trade signals for output to different destinations"""
    
    def format_trade_signal(self, signal):
        """Format a trade signal for output"""
        # Add additional fields for display
        formatted = signal.copy()
        
        # Add formatted timestamp
        formatted['formatted_time'] = datetime.fromisoformat(signal['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        
        # Add confidence level as percentage
        formatted['confidence_pct'] = f"{signal['confidence'] * 100:.1f}%"
        
        # Format stop loss and take profit for display
        formatted['formatted_stop_loss'] = [f"{sl*100:.1f}%" for sl in signal['stop_loss_levels']]
        formatted['formatted_profit_targets'] = [f"+{tp*100:.1f}%" for tp in signal['take_profit_levels']]
        
        # Create a summary message
        summary = self._create_summary(formatted)
        formatted['summary'] = summary
        
        # Create detailed analysis
        details = self._create_details(formatted)
        formatted['details'] = details
        
        # Add emoji indicators
        formatted['direction_emoji'] = "🚀" if signal['direction'] == 'bullish' else "🐻"
        formatted['confidence_emoji'] = self._get_confidence_emoji(signal['confidence'])
        
        return formatted
    
    def _create_summary(self, signal):
        """Create a summary message for the signal"""
        direction_text = "BULLISH" if signal['direction'] == 'bullish' else "BEARISH"
        emoji = signal['direction_emoji']
        option_type = signal['option_type'].upper()
        
        summary = (
            f"{emoji} {direction_text} {signal['symbol']} {option_type} OPPORTUNITY {emoji}\n"
            f"Confidence: {signal['confidence_pct']} {signal['confidence_emoji']}\n"
            f"Time: {signal['formatted_time']}\n"
            f"Hold: {signal['holding_period']}\n"
            f"Stop Loss: {' / '.join(signal['formatted_stop_loss'])}\n"
            f"Profit Targets: {' / '.join(signal['formatted_profit_targets'])}"
        )
        
        return summary
    
    def _create_details(self, signal):
        """Create detailed analysis for the signal"""
        # Create a section with technical indicators
        technical_section = "TECHNICAL ANALYSIS:\n"
        if 'analysis' in signal and 'technical' in signal['analysis']:
            tech_data = signal['analysis']['technical']
            for timeframe, data in tech_data.items():
                technical_section += f"- {timeframe.upper()}: "
                if 'bullish_signals' in data and 'bearish_signals' in data:
                    technical_section += f"Bull: {data['bullish_signals']}, Bear: {data['bearish_signals']}"
                    if 'neutral_signals' in data:
                        technical_section += f", Neutral: {data['neutral_signals']}"
                technical_section += "\n"
                
                # Add top indicators if available
                if 'indicators' in data:
                    for indicator, ind_data in data['indicators'].items():
                        if 'value' in ind_data and 'signal' in ind_data:
                            technical_section += f"  • {indicator.upper()}: {ind_data['value']:.2f} ({ind_data['signal']})\n"
        
        # Create a section with sentiment analysis
        sentiment_section = "SENTIMENT ANALYSIS:\n"
        if 'analysis' in signal and 'sentiment' in signal['analysis']:
            sent_data = signal['analysis']['sentiment']
            if 'overall_score' in sent_data:
                sentiment_section += f"- Overall Score: {sent_data['overall_score']:.2f}\n"
            if 'sentiment_label' in sent_data:
                sentiment_section += f"- Sentiment: {sent_data['sentiment_label'].upper()}\n"
            if 'article_count' in sent_data:
                sentiment_section += f"- Article Count: {sent_data['article_count']}\n"
            
            # Add keyword matches if available
            if 'keyword_matches' in sent_data:
                keyword_matches = sent_data['keyword_matches']
                if keyword_matches:
                    sentiment_section += "- Top Keywords:\n"
                    # Sort keywords by count and get top 5
                    top_keywords = sorted(keyword_matches.items(), key=lambda x: x[1], reverse=True)[:5]
                    for keyword, count in top_keywords:
                        if count > 0:
                            sentiment_section += f"  • {keyword}: {count} mentions\n"
        
        # Combine sections
        details = technical_section + "\n" + sentiment_section
        
        return details
    
    def _get_confidence_emoji(self, confidence):
        """Get emoji indicator for confidence level"""
        if confidence >= 0.9:
            return "⭐⭐⭐⭐⭐"
        elif confidence >= 0.8:
            return "⭐⭐⭐⭐"
        elif confidence >= 0.7:
            return "⭐⭐⭐"
        elif confidence >= 0.6:
            return "⭐⭐"
        else:
            return "⭐"
