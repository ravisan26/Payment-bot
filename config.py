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

# Private Channel ID for file storage (bot must be admin)
# Format: -100xxxxxxxxxx
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1001234567890"))

# Admin contact username (without @)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "yourusername")

# Tutorial link
TUTORIAL_LINK = os.environ.get("TUTORIAL_LINK", "https://youtube.com/your-tutorial")

# Database path
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

Want Premium?
Pay with UPI (Instant activation)

━━━━ HASEENA LINK (MAIN) ━━━━
›› 7 Days : ₹299
›› 15 Days : ₹500
›› 30 Days : ₹650

━━━━ HASEENA(2.0) ━━━━
›› 7 Days : ₹149
›› 15 Days : ₹249
›› 1 Month : ₹320

━━━━ SHEEP NEWS ━━━━
›› 7 Days : ₹149
›› 15 Days : ₹249
›› 1 Month : ₹320

━━━ ALL IN ONE DISCOUNT ━━━
›› 15 Days : ₹699
›› 30 Days : ₹899

PAYMENT METHODS
paytm • gpay • phonepe • upi
────────────────────
Premium will be added once paid
After payment: Send screenshot to admin
"""

PREMIUM_MESSAGE = """
👋 Hi {name}ㅤㅤㅤ

✅ 𝗬𝗢𝗨 𝗔𝗥𝗘 𝗣𝗥𝗘𝗠𝗜𝗨𝗠!
────────────────────
📅 Expires: {expiry}

You have full access to all files!
"""

PAYMENT_MESSAGE = """
✦ 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗣𝗔𝗬𝗠𝗘𝗡𝗧

📺 Cʜᴀɴɴᴇʟ: {channel}
❐ Aᴍᴏᴜɴᴛ: ₹{amount}
≡ Vᴀʟɪᴅɪᴛʏ: {validity}
❐ Tʀᴀɴsᴀᴄᴛɪᴏɴ ID: `{trx_id}`
────────────────────
≡ Sᴄᴀɴ ᴛʜɪs QR ᴡɪᴛʜ ᴀɴʏ UPI ᴀᴘᴘ ᴛᴏ ᴘᴀʏ.

✦ OR tap here to pay directly
›› Pay ₹{amount} via UPI

━━━━━━━━━━━━━━━━━━━━
⚠️ 𝗜𝗠𝗣𝗢𝗥𝗧𝗔𝗡𝗧: 𝗔𝗙𝗧𝗘𝗥 𝗣𝗔𝗬𝗠𝗘𝗡𝗧

1️⃣ Tᴀᴋᴇ ᴀ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ ᴏғ ᴘᴀʏᴍᴇɴᴛ
2️⃣ Cʟɪᴄᴋ "📸 Vᴇʀɪғʏ Pᴀʏᴍᴇɴᴛ" ʙᴜᴛᴛᴏɴ
3️⃣ Sᴇɴᴅ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ ᴛᴏ ᴀᴅᴍɪɴ
4️⃣ Wᴀɪᴛ ғᴏʀ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ✓
"""

NOT_PREMIUM_MESSAGE = """
⚠️ 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗥𝗘𝗤𝗨𝗜𝗥𝗘𝗗

You need premium to access this file.
Click the button below to get premium!
"""
