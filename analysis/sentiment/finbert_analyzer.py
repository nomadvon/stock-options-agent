import logging
import numpy as np
from datetime import datetime

from config.config import SENTIMENT_KEYWORDS
from analysis.sentiment.news_fetcher import NewsFetcher

logger = logging.getLogger(__name__)

class FinBERTAnalyzer:
    """Simplified sentiment analysis without PyTorch dependency"""
    
    def __init__(self, model_name=None, max_length=None):
        logger.info("Initializing simplified sentiment analyzer")
        self.news_fetcher = NewsFetcher()
    
    def _analyze_text(self, text):
        """Simple keyword-based sentiment analysis"""
        positive_words = ["bullish", "up", "rise", "growth", "profit", "positive", "beat", "exceed", 
                         "strong", "surge", "gain", "opportunity", "optimistic", "momentum"]
        negative_words = ["bearish", "down", "fall", "decline", "loss", "negative", "miss", "below", 
                         "weak", "drop", "decrease", "risk", "pessimistic", "downturn"]
        
        text_lower = text.lower()
        
        # Count occurrences of positive and negative words
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            score = 0
            label = "neutral"
        else:
            score = (pos_count - neg_count) / (pos_count + neg_count)
            if score > 0.2:
                label = "positive"
            elif score < -0.2:
                label = "negative"
            else:
                label = "neutral"
                
        return {
            "score": score,  # Range: -1 to 1
            "label": label,
            "raw_scores": {
                "positive": pos_count / (total or 1),
                "negative": neg_count / (total or 1),
                "neutral": 1 - (pos_count + neg_count) / (total or 1) if total else 1
            }
        }
    
    def get_ticker_sentiment(self, ticker):
        """Get sentiment analysis for a specific ticker"""
        # Get news articles for the ticker
        news_articles = self.news_fetcher.get_news_for_ticker(ticker)
        
        if not news_articles:
            logger.warning(f"No news articles found for {ticker}")
            return {
                "ticker": ticker,
                "overall_score": 0,
                "sentiment_label": "neutral",
                "article_count": 0,
                "keyword_matches": {keyword: 0 for keyword in SENTIMENT_KEYWORDS}
            }
        
        # Analyze each article
        sentiment_scores = []
        keyword_matches = {keyword: 0 for keyword in SENTIMENT_KEYWORDS}
        
        for article in news_articles:
            # Check for keywords
            article_text = f"{article['title']} {article['description'] or ''}"
            for keyword in SENTIMENT_KEYWORDS:
                if keyword.lower() in article_text.lower():
                    keyword_matches[keyword] += 1
            
            # Get sentiment score
            sentiment = self._analyze_text(article_text)
            sentiment_scores.append(sentiment["score"])
        
        # Aggregate sentiment scores
        if sentiment_scores:
            # Weighted average with more recent news having higher weight
            weights = np.linspace(1, 0.5, len(sentiment_scores))
            weighted_scores = np.array(sentiment_scores) * weights
            overall_score = np.sum(weighted_scores) / np.sum(weights)
            
            # Determine overall sentiment label
            if overall_score > 0.2:
                sentiment_label = "positive"
            elif overall_score < -0.2:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
        else:
            overall_score = 0
            sentiment_label = "neutral"
        
        return {
            "ticker": ticker,
            "overall_score": float(overall_score),
            "sentiment_label": sentiment_label,
            "article_count": len(news_articles),
            "keyword_matches": keyword_matches
        }
    
    def get_market_sentiment(self):
        """Get overall market sentiment based on general financial news"""
        # Get general market news
        market_news = self.news_fetcher.get_general_market_news()
        
        if not market_news:
            logger.warning("No market news articles found")
            return {
                "overall_score": 0,
                "sentiment_label": "neutral",
                "article_count": 0,
                "keyword_matches": {keyword: 0 for keyword in SENTIMENT_KEYWORDS}
            }
        
        # Analyze each article
        sentiment_scores = []
        keyword_matches = {keyword: 0 for keyword in SENTIMENT_KEYWORDS}
        
        for article in market_news:
            # Check for keywords
            article_text = f"{article['title']} {article['description'] or ''}"
            for keyword in SENTIMENT_KEYWORDS:
                if keyword.lower() in article_text.lower():
                    keyword_matches[keyword] += 1
            
            # Get sentiment score
            sentiment = self._analyze_text(article_text)
            sentiment_scores.append(sentiment["score"])
        
        # Aggregate sentiment scores
        if sentiment_scores:
            # Weighted average with more recent news having higher weight
            weights = np.linspace(1, 0.5, len(sentiment_scores))
            weighted_scores = np.array(sentiment_scores) * weights
            overall_score = np.sum(weighted_scores) / np.sum(weights)
            
            # Determine overall sentiment label
            if overall_score > 0.2:
                sentiment_label = "positive"
            elif overall_score < -0.2:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
        else:
            overall_score = 0
            sentiment_label = "neutral"
        
        return {
            "overall_score": float(overall_score),
            "sentiment_label": sentiment_label,
            "article_count": len(market_news),
            "keyword_matches": keyword_matches
        }
