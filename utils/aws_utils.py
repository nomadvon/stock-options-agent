import boto3
import logging
import time

logger = logging.getLogger(__name__)

class AWSIntegration:
    """Handles AWS service integrations for the trading agent"""
    
    def __init__(self, region_name='us-east-2'):
        """Initialize AWS clients - no credentials needed since we're using IAM role"""
        try:
            # The SDK automatically uses the EC2 instance role credentials
            self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
            self.logs = boto3.client('logs', region_name=region_name)
            logger.info("AWS integration initialized successfully")
            
            # Test permissions by putting a test metric
            try:
                self.cloudwatch.list_metrics(Namespace='AWS/EC2', MetricName='CPUUtilization', Dimensions=[])
                self.permissions_ok = True
                logger.info("AWS CloudWatch permissions verified")
            except Exception as perm_e:
                logger.warning(f"CloudWatch permissions not active yet: {perm_e}")
                self.permissions_ok = False
                
        except Exception as e:
            logger.error(f"Error initializing AWS integration: {e}")
            self.cloudwatch = None
            self.logs = None
            self.permissions_ok = False
    
    def put_metric(self, metric_name, value, ticker="ALL", unit="Count"):
        """Send a custom metric to CloudWatch"""
        if not self.cloudwatch or not self.permissions_ok:
            # Skip without error logging since we know permissions aren't ready
            return False
            
        try:
            response = self.cloudwatch.put_metric_data(
                Namespace='TradingAgent',
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Dimensions': [
                            {
                                'Name': 'Ticker',
                                'Value': ticker
                            },
                        ],
                        'Value': value,
                        'Unit': unit
                    },
                ]
            )
            return True
        except Exception as e:
            # Only log once and then suppress subsequent errors
            if self.permissions_ok:
                logger.error(f"Error putting metric {metric_name}: {e}")
                self.permissions_ok = False
            return False
