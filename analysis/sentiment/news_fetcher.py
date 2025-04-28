import logging
import time
from datetime import datetime, timedelta
import requests

from config.config import NEWS_API_KEY, SENTIMENT_KEYWORDS

logger = logging.getLogger(__name__)

class NewsFetcher:
    """Fetches news from various sources for sentiment analysis"""
    
    NEWSAPI_URL = "https://newsapi.org/v2/everything"
    
    def __init__(self, api_key=NEWS_API_KEY):
        self.api_key = api_key
        self.session = requests.Session()
    
    def _make_request(self, params):
        """Make a request to NewsAPI with retry logic"""
        if not self.api_key:
            logger.error("NEWS_API_KEY not configured")
            return {'articles': []}
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                params['apiKey'] = self.api_key
                response = self.session.get(self.NEWSAPI_URL, params=params)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"News API request failed (attempt {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error("All retry attempts failed for News API")
                    return {'articles': []}
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def get_news_for_ticker(self, ticker, days=2):
        """Get recent news articles for a specific ticker"""
        today = datetime.now()
        from_date = (today - timedelta(days=days)).strftime('%Y-%m-%d')
        
        params = {
            'q': f'({ticker} OR "${ticker}") AND (stock OR option OR trading OR market)',
            'from': from_date,
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': 10  # Limit to 10 most recent articles
        }
        
        response = self._make_request(params)
        
        if 'articles' in response:
            return response['articles']
        return []
    
    def get_general_market_news(self, days=1):
        """Get general market news"""
        today = datetime.now()
        from_date = (today - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Create a query with all our keywords of interest
        keyword_query = ' OR '.join(SENTIMENT_KEYWORDS)
        
        params = {
            'q': f'(stock market OR financial market) AND ({keyword_query})',
            'from': from_date,
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': 20  # Get more general market news
        }
        
        response = self._make_request(params)
        
        if 'articles' in response:
            return response['articles']
        return []
    
    def get_company_specific_news(self, ticker, days=7):
        """Get company-specific news (for longer timeframe)"""
        today = datetime.now()
        from_date = (today - timedelta(days=days)).strftime('%Y-%m-%d')
        
        params = {
            'q': f'({ticker} OR "${ticker}") AND (earnings OR revenue OR growth OR guidance OR CEO OR executive)',
            'from': from_date,
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': 15
        }
        
        response = self._make_request(params)
        
        if 'articles' in response:
            return response['articles']
        return []
    
    def search_for_keyword_articles(self, keyword, days=2):
        """Search for articles containing specific keywords"""
        today = datetime.now()
        from_date = (today - timedelta(days=days)).strftime('%Y-%m-%d')
        
        params = {
            'q': f'({keyword}) AND (stock OR market OR financial OR economy)',
            'from': from_date,
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': 10
        }
        
        response = self._make_request(params)
        
        if 'articles' in response:
            return response['articles']
        return []
