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

# Checker IDs - Users who can ONLY use /checkuser command (subscription check)
# Separate from full admin access
checker_ids_str = os.environ.get("CHECKER_IDS", "")
CHECKER_IDS = [int(x.strip()) for x in checker_ids_str.split(",") if x.strip()]

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
    'ch1': 'HASEENA MAIN',
    'ch2': 'HASEENA 2.0',
    'ch3': 'SHEEP',
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
# IMAGES - Set image URLs or Telegram file_ids
# ==============================================
# Start message image - shown when user sends /start
START_IMAGE_URL = os.environ.get("START_IMAGE_URL", "")

# Premium/Plans image - shown when user clicks "Get Premium" and selects a channel
PREMIUM_IMAGE_URL = os.environ.get("PREMIUM_IMAGE_URL", "")

# ==============================================
# PREMIUM PLANS - CHANNEL BASED
# ==============================================

# Channel 1 Plans - HASEENA MAIN - UPDATED PRICING
CHANNEL_1_PLANS = {
    "ch1_7_days": {"days": 7, "price": 299, "label": "7 Days", "channel": "HASEENA MAIN"},
    "ch1_15_days": {"days": 15, "price": 399, "label": "15 Days", "channel": "HASEENA MAIN"},
    "ch1_30_days": {"days": 30, "price": 499, "label": "1 Month", "channel": "HASEENA MAIN"},
    "ch1_90_days": {"days": 90, "price": 999, "label": "3 Months", "channel": "HASEENA MAIN"},
}

# Channel 2 Plans - HASEENA(2.0) - UPDATED PRICING
CHANNEL_2_PLANS = {
    "ch2_7_days": {"days": 7, "price": 120, "label": "7 Days", "channel": "HASEENA(2.0)"},
    "ch2_15_days": {"days": 15, "price": 199, "label": "15 Days", "channel": "HASEENA(2.0)"},
    "ch2_30_days": {"days": 30, "price": 249, "label": "1 Month", "channel": "HASEENA(2.0)"},
    "ch2_90_days": {"days": 90, "price": 499, "label": "3 Months", "channel": "HASEENA(2.0)"},
}

# Channel 3 Plans - SHEEP NEWS - UPDATED PRICING
CHANNEL_3_PLANS = {
    "ch3_7_days": {"days": 7, "price": 199, "label": "7 Days", "channel": "SHEEP"},
    "ch3_15_days": {"days": 15, "price": 249, "label": "15 Days", "channel": "SHEEP"},
    "ch3_30_days": {"days": 30, "price": 349, "label": "1 Month", "channel": "SHEEP"},
    "ch3_90_days": {"days": 90, "price": 799, "label": "3 Months", "channel": "SHEEP"},
}

# All-in-One Discount Plans (All 3 Channels) - UPDATED PRICING
ALL_IN_ONE_PLANS = {
    "all_7_days": {"days": 7, "price": 499, "label": "7 Days", "channel": "ALL CHANNELS"},
    "all_15_days": {"days": 15, "price": 699, "label": "15 Days", "channel": "ALL CHANNELS"},
    "all_30_days": {"days": 30, "price": 899, "label": "1 Month", "channel": "ALL CHANNELS"},
    "all_90_days": {"days": 90, "price": 1499, "label": "3 Months", "channel": "ALL CHANNELS"},
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
✦ 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗣𝗔𝗬𝗠𝗘𝗡𝗧

❐ Channel: {channel}
≡ Validity: {validity}
≡ Amount: Rs.{amount}
❐ Transaction ID: `{trx_id}`

────────────────────
≡ Contact Admin to Complete Payment.

✦ Premium will be added automatically if paid within 5 minutes...
"""

NOT_PREMIUM_MESSAGE = """
♻️ PREMIUM ♻️

💎 ᴛʜɪs mega ᴄᴏɴᴛᴇɴᴛ ɪs ᴘʀᴇᴍɪᴜᴍ ᴏɴʟʏ.

•  Pay and activate premium to get instant access.

• Click the button below to get premium!
"""
