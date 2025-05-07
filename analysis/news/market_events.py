import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz

from config.config import NEWS_API_KEY, TRADING_SYMBOLS

logger = logging.getLogger(__name__)

class MarketEventsMonitor:
    """Monitors market events including earnings, Fed speeches, and other important announcements"""
    
    def __init__(self, api_key: str = NEWS_API_KEY):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        self.utc = pytz.UTC
        
    def get_earnings_announcements(self) -> List[Dict]:
        """Get upcoming earnings announcements for tech companies"""
        try:
            # Get current date and next 30 days
            today = datetime.now()
            next_month = today + timedelta(days=30)
            
            # Search for earnings announcements
            url = f"{self.base_url}/everything"
            params = {
                'apiKey': self.api_key,
                'q': 'earnings OR revenue AND (tech OR technology)',
                'from': today.strftime('%Y-%m-%d'),
                'to': next_month.strftime('%Y-%m-%d'),
                'language': 'en',
                'sortBy': 'publishedAt'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            articles = response.json().get('articles', [])
            
            # Filter and format earnings announcements
            earnings = []
            for article in articles:
                if any(keyword in article['title'].lower() for keyword in ['earnings', 'revenue', 'results']):
                    earnings.append({
                        'title': article['title'],
                        'date': article['publishedAt'],
                        'source': article['source']['name'],
                        'url': article['url']
                    })
            
            return earnings
            
        except Exception as e:
            logger.error(f"Error fetching earnings announcements: {e}")
            return []
    
    def get_fed_speeches(self) -> List[Dict]:
        """Get scheduled Federal Reserve speeches"""
        try:
            # Get current date and next 30 days
            today = datetime.now()
            next_month = today + timedelta(days=30)
            
            # Search for Fed speeches
            url = f"{self.base_url}/everything"
            params = {
                'apiKey': self.api_key,
                'q': '(Federal Reserve OR Fed) AND (speech OR testimony OR appearance)',
                'from': today.strftime('%Y-%m-%d'),
                'to': next_month.strftime('%Y-%m-%d'),
                'language': 'en',
                'sortBy': 'publishedAt'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            articles = response.json().get('articles', [])
            
            # Filter and format Fed speeches
            speeches = []
            for article in articles:
                if any(name in article['title'] for name in ['Powell', 'Federal Reserve Chair', 'Fed Chair']):
                    # Convert published date to UTC
                    pub_date = datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
                    pub_date_utc = self.utc.localize(pub_date)
                    
                    speeches.append({
                        'title': article['title'],
                        'date_utc': pub_date_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
                        'source': article['source']['name'],
                        'url': article['url']
                    })
            
            return speeches
            
        except Exception as e:
            logger.error(f"Error fetching Fed speeches: {e}")
            return []
    
    def get_market_events(self) -> Dict:
        """Get all market events including earnings and Fed speeches"""
        return {
            'earnings': self.get_earnings_announcements(),
            'fed_speeches': self.get_fed_speeches()
        } 