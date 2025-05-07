import json
from alerts.discord_webhook import DiscordWebhook

def test_discord_format():
    # Sample trading signals
    signals = {
        "entry_points": {
            "long": 533.58,
            "short": 570.11
        },
        "exit_points": {
            "long": 570.11,
            "short": 497.06
        },
        "analysis": "SPY is currently trading within the Bollinger Bands, with RSI at a neutral level and positive sentiment. A long entry can be considered at the lower band support of 533.58, while a short entry can be considered at the upper band resistance of 570.11.",
        "confidence": "Medium",
        "key_levels": {
            "support": 533.58,
            "resistance": 570.11
        }
    }
    
    # Format the message
    message = (
        f"**Trading Signals for SPY**\n\n"
        f"**Entry Points:**\n"
        f"• Long: {signals['entry_points']['long']}\n"
        f"• Short: {signals['entry_points']['short']}\n\n"
        f"**Exit Points:**\n"
        f"• Long: {signals['exit_points']['long']}\n"
        f"• Short: {signals['exit_points']['short']}\n\n"
        f"**Analysis:**\n{signals['analysis']}\n\n"
        f"**Confidence:** {signals['confidence']}\n\n"
        f"**Key Levels:**\n"
        f"• Support: {signals['key_levels']['support']}\n"
        f"• Resistance: {signals['key_levels']['resistance']}"
    )
    
    print("Discord Message Format:")
    print("=" * 50)
    print(message)
    print("=" * 50)
    
    # Test sending to Discord
    webhook = DiscordWebhook()
    try:
        webhook.send_notification(
            message=message,
            title="Trading Signals Test"
        )
        print("\nMessage sent to Discord successfully!")
    except Exception as e:
        print(f"\nError sending to Discord: {e}")

if __name__ == "__main__":
    test_discord_format() 