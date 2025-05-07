import os
from dotenv import load_dotenv
from utils.discord_webhook import DiscordWebhook
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_discord_webhooks():
    # Load environment variables
    load_dotenv()
    
    # Initialize Discord webhook
    webhook = DiscordWebhook()
    
    # Test main webhook
    logger.info("Testing main webhook...")
    webhook.send_update({
        'type': 'startup',
        'message': 'Testing Discord webhook integration'
    })
    
    # Test logs webhook
    logger.info("Testing logs webhook...")
    webhook.stream_logs('PRICE_ACTION', 'Test price action message')
    webhook.stream_logs('BOX_METHOD', 'Test box method analysis message')

if __name__ == "__main__":
    test_discord_webhooks() 