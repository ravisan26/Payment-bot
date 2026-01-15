# ==============================================
# TELEGRAM FILE STORE BOT - CONFIGURATION
# ==============================================
import os

# Bot Token from @BotFather
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Your UPI ID for receiving payments
UPI_ID = os.environ.get("UPI_ID", "yourname@paytm")

# Binance Pay ID / USDT Address
BINANCE_ID = os.environ.get("BINANCE_ID", "your_binance_pay_id")

# PayPal Email
PAYPAL_EMAIL = os.environ.get("PAYPAL_EMAIL", "your_paypal@email.com")

# Your Telegram User ID (get from @userinfobot)
# For multiple admins: "123,456,789"
admin_ids_str = os.environ.get("ADMIN_IDS", "123456789")
ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(",")]

# ==============================================
# CHANNEL IDs (Bot must be admin in all channels)
# Format: -100xxxxxxxxxx
# ==============================================
# Channel 1 - HASEENA LINK (MAIN)
CHANNEL_1_ID = int(os.environ.get("CHANNEL_1_ID", "-1001234567890"))

# Channel 2 - HASEENA(2.0)
CHANNEL_2_ID = int(os.environ.get("CHANNEL_2_ID", "-1001234567891"))

# Channel 3 - SHEEP NEWS
CHANNEL_3_ID = int(os.environ.get("CHANNEL_3_ID", "-1001234567892"))

# Legacy single channel ID (for backward compatibility)
CHANNEL_ID = CHANNEL_1_ID

# Channel ID to channel code mapping
CHANNEL_ID_MAP = {
    CHANNEL_1_ID: 'ch1',
    CHANNEL_2_ID: 'ch2',
    CHANNEL_3_ID: 'ch3',
}

# Channel code to name mapping
CHANNEL_NAME_MAP = {
    'ch1': 'HASEENA LINK (MAIN)',
    'ch2': 'HASEENA(2.0)',
    'ch3': 'SHEEP NEWS',
    'all': 'ALL CHANNELS'
}

# Admin contact username (without @)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "yourusername")

# Tutorial link
TUTORIAL_LINK = os.environ.get("TUTORIAL_LINK", "https://youtube.com/your-tutorial")

# ==============================================
# DATABASE - PostgreSQL (Neon)
# ==============================================
# Connection string format: postgresql://user:password@host/database?sslmode=require
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Fallback to SQLite for local development
DATABASE_PATH = os.environ.get("DATABASE_PATH", "database.db")

# ==============================================
# PREMIUM PLANS - CHANNEL BASED
# ==============================================

# Channel 1 Plans - HASEENA LINK (MAIN)
CHANNEL_1_PLANS = {
    "ch1_7_days": {"days": 7, "price": 299, "label": "7 Days", "channel": "HASEENA LINK (MAIN)"},
    "ch1_15_days": {"days": 15, "price": 500, "label": "15 Days", "channel": "HASEENA LINK (MAIN)"},
    "ch1_30_days": {"days": 30, "price": 650, "label": "30 Days", "channel": "HASEENA LINK (MAIN)"},
}

# Channel 2 Plans - HASEENA(2.0)
CHANNEL_2_PLANS = {
    "ch2_7_days": {"days": 7, "price": 149, "label": "7 Days", "channel": "HASEENA(2.0)"},
    "ch2_15_days": {"days": 15, "price": 249, "label": "15 Days", "channel": "HASEENA(2.0)"},
    "ch2_30_days": {"days": 30, "price": 320, "label": "1 Month", "channel": "HASEENA(2.0)"},
}

# Channel 3 Plans - SHEEP NEWS
CHANNEL_3_PLANS = {
    "ch3_7_days": {"days": 7, "price": 149, "label": "7 Days", "channel": "SHEEP NEWS"},
    "ch3_15_days": {"days": 15, "price": 249, "label": "15 Days", "channel": "SHEEP NEWS"},
    "ch3_30_days": {"days": 30, "price": 320, "label": "1 Month", "channel": "SHEEP NEWS"},
}

# All-in-One Discount Plans (All 3 Channels)
ALL_IN_ONE_PLANS = {
    "all_15_days": {"days": 15, "price": 699, "label": "15 Days", "channel": "ALL CHANNELS"},
    "all_30_days": {"days": 30, "price": 899, "label": "30 Days", "channel": "ALL CHANNELS"},
}

# Combined PLANS dictionary for backward compatibility
PLANS = {
    **CHANNEL_1_PLANS,
    **CHANNEL_2_PLANS,
    **CHANNEL_3_PLANS,
    **ALL_IN_ONE_PLANS,
}

# ==============================================
# MESSAGES
# ==============================================
START_MESSAGE = """
Hi {name}

Get Premium to unlock exclusive content.

PAYMENT METHODS
UPI | Binance | PayPal | More
--------------------
Click "Get Premium" below to see plans!
"""

PREMIUM_MESSAGE = """
Hi {name}

YOU ARE PREMIUM!
--------------------
Expires: {expiry}

You have full access to your subscribed channels.
"""

PAYMENT_MESSAGE = """
PREMIUM PAYMENT

Channel: {channel}
Amount: Rs.{amount}
Validity: {validity}
Transaction ID: `{trx_id}`
--------------------
Scan QR with any UPI app to pay.

Or tap here to pay directly.

AFTER PAYMENT:
1. Take a screenshot of payment
2. Click "Verify Payment" button
3. Send screenshot to admin
4. Wait for verification
"""

NOT_PREMIUM_MESSAGE = """
PREMIUM REQUIRED

You need premium to access this file.
Click the button below to get premium!
"""

