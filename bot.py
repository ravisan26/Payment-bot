import io
import logging
import random
import string
from datetime import datetime

import qrcode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import config
import database as db

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def generate_trx_id() -> str:
    """Generate a unique transaction ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = "".join(random.choices(string.digits, k=6))
    return f"TRX{timestamp}{random_part}"


def generate_upi_qr(amount: int, trx_id: str) -> io.BytesIO:
    """Generate UPI QR code."""
    upi_string = f"upi://pay?pa={config.UPI_ID}&pn=Premium&am={amount}&tn={trx_id}&cu=INR"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(upi_string)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    bio = io.BytesIO()
    img.save(bio, "PNG")
    bio.seek(0)
    return bio


def get_upi_link(amount: int, trx_id: str) -> str:
    """Generate UPI deep link."""
    return f"upi://pay?pa={config.UPI_ID}&pn=Premium&am={amount}&tn={trx_id}&cu=INR"


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in config.ADMIN_IDS


def is_checker(user_id: int) -> bool:
    """Check if user can use /checkuser command (admins + checkers)."""
    return user_id in config.ADMIN_IDS or user_id in config.CHECKER_IDS


# ==============================================
# USER HANDLERS
# ==============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name)
    
    # Check if there's a file ID in the start parameter
    # Format: <channel_code>_<message_id> e.g., ch1_123
    if context.args and len(context.args) > 0:
        file_param = context.args[0]
        
        # Parse channel and message ID
        try:
            if '_' in file_param:
                channel_code, msg_id_str = file_param.split('_', 1)
                msg_id = int(msg_id_str)
            else:
                # Legacy format - just message ID, assume ch1
                channel_code = 'ch1'
                msg_id = int(file_param)
        except ValueError:
            await update.message.reply_text("Invalid link.")
            return
        
        # Get the channel ID for this content
        channel_id_map = {
            'ch1': config.CHANNEL_1_ID,
            'ch2': config.CHANNEL_2_ID,
            'ch3': config.CHANNEL_3_ID,
        }
        from_channel_id = channel_id_map.get(channel_code, config.CHANNEL_1_ID)
        channel_name = config.CHANNEL_NAME_MAP.get(channel_code, 'Unknown')
        
        # Check if user has access to this specific channel
        if db.has_channel_access(user.id, channel_code) or is_admin(user.id):
            # Forward file from channel
            try:
                await context.bot.copy_message(
                    chat_id=user.id,
                    from_chat_id=from_channel_id,
                    message_id=msg_id
                )
                return
            except Exception as e:
                logger.error(f"Error forwarding file: {e}")
                await update.message.reply_text("File not found or expired.")
                return
        else:
            # Show channel-specific premium required message
            keyboard = [
                [InlineKeyboardButton("Get Premium", callback_data="show_plans")],
                [InlineKeyboardButton("Contact Admin", url=f"https://t.me/{config.ADMIN_USERNAME}")],
            ]
            await update.message.reply_text(
                config.NOT_PREMIUM_MESSAGE,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return
    
    # Normal start - show menu with image
    if db.is_premium(user.id):
        # Premium user
        expiry = db.get_premium_expiry(user.id)
        keyboard = [
            [InlineKeyboardButton("Contact Admin", url=f"https://t.me/{config.ADMIN_USERNAME}")],
        ]
        await update.message.reply_text(
            config.PREMIUM_MESSAGE.format(name=user.first_name, expiry=expiry),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # Non-premium user - show payment options with image
        keyboard = [
            [InlineKeyboardButton("Get Premium", callback_data="show_plans")],
            [
                InlineKeyboardButton("Tutorial", url=config.TUTORIAL_LINK),
                InlineKeyboardButton("Contact Admin", url=f"https://t.me/{config.ADMIN_USERNAME}"),
            ],
        ]
        
        # Check if there's a start image configured
        start_image = getattr(config, 'START_IMAGE_URL', '') or ''
        
        if start_image:
            try:
                await update.message.reply_photo(
                    photo=start_image,
                    caption=config.START_MESSAGE.format(name=user.first_name),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.error(f"Error sending start image: {e}")
                # Fallback to text message
                await update.message.reply_text(
                    config.START_MESSAGE.format(name=user.first_name),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        else:
            await update.message.reply_text(
                config.START_MESSAGE.format(name=user.first_name),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )


async def plans_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /plans command."""
    await show_plans(update, context)


async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show channel selection menu."""
    # Get user's name for personalized greeting
    if update.callback_query:
        user = update.callback_query.from_user
    else:
        user = update.effective_user
    
    name = user.first_name or user.username or "User"
    
    keyboard = [
        [InlineKeyboardButton("HASEENA MAIN", callback_data="channel_1")],
        [InlineKeyboardButton("HASEENA 2.0", callback_data="channel_2")],
        [InlineKeyboardButton("SHEEP", callback_data="channel_3")],
        [InlineKeyboardButton("ALL IN ONE (Discount)", callback_data="channel_all")],
        [InlineKeyboardButton("Contact Admin", url=f"https://t.me/{config.ADMIN_USERNAME}")],
    ]
    
    text = f"""👋 Hello {name}

🎖️ Want Premium?
Choose a Plan below:

• 💳 Pay with UPI (Instant activation)
• 📁 Pay with Binance (instant)
• 🔖 Pay with PayPal 
• 📥 Any other Payment Method we accept worldwide

———————————————————

🔖 Choose Your Preferred Channel:"""
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def show_channel_plans(update: Update, context: ContextTypes.DEFAULT_TYPE, channel_type: str):
    """Show plans for a specific channel with image."""
    query = update.callback_query
    await query.answer()
    
    if channel_type == "1":
        plans = config.CHANNEL_1_PLANS
        title = "HASEENA MAIN"
    elif channel_type == "2":
        plans = config.CHANNEL_2_PLANS
        title = "HASEENA 2.0"
    elif channel_type == "3":
        plans = config.CHANNEL_3_PLANS
        title = "SHEEP"
    else:  # all
        plans = config.ALL_IN_ONE_PLANS
        title = "ALL IN ONE (Discount)"
    
    keyboard = []
    for plan_id, plan in plans.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{plan['label']} : ₹{plan['price']}",
                callback_data=f"plan_{plan_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("Back to Channels", callback_data="show_plans")])
    keyboard.append([InlineKeyboardButton("Contact Admin", url=f"https://t.me/{config.ADMIN_USERNAME}")])
    
    # Build the plan details message
    plan_lines = []
    for plan_id, plan in plans.items():
        plan_lines.append(f"›› {plan['label']} : ₹{plan['price']}")
    
    text = f"""✦{title}  𝗣𝗟𝗔𝗡𝗦
ᴅᴜʀᴀᴛɪᴏɴ & ᴘʀɪᴄᴇ
────────────────────

{chr(10).join(plan_lines)}

❐ 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗠𝗘𝗧𝗛𝗢𝗗𝗦
❐ 𝗎𝗉𝗂 • binance •paypal• 𝗉𝗁𝗈𝗇𝖾 𝗉𝖺𝗒 • other payment write in inbox us
────────────────────
✦Contact Admin Before Payment 

✦ 𝗔𝗙𝗧𝗘𝗥 𝗣𝗔𝗬𝗠𝗘𝗡𝗧:
❐ Sᴇɴᴅ ᴀ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ & ᴡᴀɪᴛ ᴀ ꜰᴇᴡ ᴍɪɴᴜᴛᴇꜱ ғᴏʀ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ ✓"""
    
    # Check if there's a premium image configured
    premium_image = getattr(config, 'PREMIUM_IMAGE_URL', '') or ''
    
    if premium_image:
        try:
            # Delete the current message and send photo with caption
            await query.message.delete()
            await context.bot.send_photo(
                chat_id=query.from_user.id,
                photo=premium_image,
                caption=text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            # Fallback to text message
            await query.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    else:
        # No image configured, just show text
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plan selection callback - show payment methods."""
    query = update.callback_query
    await query.answer()
    
    plan_id = query.data.replace("plan_", "")
    plan = config.PLANS.get(plan_id)
    
    if not plan:
        await query.edit_message_text("Invalid plan selected.")
        return
    
    # Store plan in user_data for later
    context.user_data["selected_plan_id"] = plan_id
    
    amount = plan["price"]
    validity = plan["label"]
    channel = plan.get("channel", "Premium")
    
    # Show payment method selection
    keyboard = [
        [InlineKeyboardButton("1. UPI", callback_data="pay_upi")],
        [InlineKeyboardButton("2. Binance", callback_data="pay_binance")],
        [InlineKeyboardButton("3. PayPal", callback_data="pay_paypal")],
        [InlineKeyboardButton("4. Other Payment Method", callback_data="pay_other")],
        [InlineKeyboardButton("Back", callback_data="show_plans")],
    ]
    
    await query.edit_message_text(
        f"**PAYMENT**\n"
        f"--------------------\n"
        f"Channel: {channel}\n"
        f"Plan: {validity}\n"
        f"Amount: Rs.{amount}\n\n"
        f"Select payment method:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_type: str):
    """Handle payment method selection - show admin contact."""
    query = update.callback_query
    await query.answer()
    
    plan_id = context.user_data.get("selected_plan_id")
    plan = config.PLANS.get(plan_id)
    
    if not plan:
        await query.edit_message_text("Session expired. Please start again.")
        return
    
    trx_id = generate_trx_id()
    amount = plan["price"]
    validity = plan["label"]
    channel = plan.get("channel", "Premium")
    
    # Payment type labels
    payment_labels = {
        "upi": "UPI",
        "binance": "Binance",
        "paypal": "PayPal",
        "other": "Other"
    }
    payment_label = payment_labels.get(payment_type, "Payment")
    
    keyboard = [
        [InlineKeyboardButton("Contact Admin", url=f"https://t.me/{config.ADMIN_USERNAME}?text={payment_label}%20Payment%20-%20TRX:%20{trx_id}%20-%20{channel}%20-%20{validity}%20-%20Rs.{amount}")],
        [InlineKeyboardButton("Back", callback_data="show_plans")],
    ]
    
    await query.edit_message_text(
        f"✦ 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗣𝗔𝗬𝗠𝗘𝗡𝗧\n\n"
        f"❐ Channel: {channel}\n"
        f"≡ Validity: {validity}\n"
        f"≡ Amount: Rs.{amount}\n"
        f"❐ Transaction ID: `{trx_id}`\n\n"
        f"────────────────────\n"
        f"≡ Contact Admin to Complete Payment.\n\n"
        f"✦ Premium will be added automatically if paid within 5 minutes...",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_upi_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle UPI payment selection."""
    await handle_payment_method(update, context, "upi")


async def handle_binance_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Binance payment selection."""
    await handle_payment_method(update, context, "binance")


async def handle_paypal_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PayPal payment selection."""
    await handle_payment_method(update, context, "paypal")


async def handle_other_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Other payment selection."""
    await handle_payment_method(update, context, "other")


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries."""
    query = update.callback_query
    data = query.data
    
    # User callbacks
    if data == "show_plans":
        await show_plans(update, context)
    elif data.startswith("channel_"):
        channel_type = data.replace("channel_", "")
        await show_channel_plans(update, context, channel_type)
    elif data.startswith("plan_"):
        await handle_plan_selection(update, context)
    
    # Payment method callbacks
    elif data == "pay_upi":
        await handle_upi_payment(update, context)
    elif data == "pay_binance":
        await handle_binance_payment(update, context)
    elif data == "pay_paypal":
        await handle_paypal_payment(update, context)
    elif data == "pay_other":
        await handle_other_payment(update, context)
    
    # Admin callbacks
    elif data.startswith("admin_ch_"):
        await admin_channel_selection(update, context)
    elif data.startswith("admin_plan_"):
        await admin_plan_selection(update, context)
    elif data == "admin_back_channels":
        await admin_back_to_channels(update, context)
    elif data == "admin_cancel":
        await admin_cancel(update, context)


# ==============================================
# ADMIN HANDLERS
# ==============================================

async def add_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addpremium command - Admin only with interactive UI."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Not authorized.")
        return
    
    # Show channel selection menu
    keyboard = [
        [InlineKeyboardButton("HASEENA MAIN", callback_data="admin_ch_1")],
        [InlineKeyboardButton("HASEENA 2.0", callback_data="admin_ch_2")],
        [InlineKeyboardButton("SHEEP", callback_data="admin_ch_3")],
        [InlineKeyboardButton("ALL IN ONE", callback_data="admin_ch_all")],
        [InlineKeyboardButton("Cancel", callback_data="admin_cancel")],
    ]
    
    await update.message.reply_text(
        "**ADD PREMIUM**\n"
        "--------------------\n"
        "Select a channel:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def admin_channel_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin channel selection for adding premium."""
    query = update.callback_query
    await query.answer()
    
    channel_type = query.data.replace("admin_ch_", "")
    
    # Store selected channel in user_data
    context.user_data["admin_add_channel"] = channel_type
    
    # Get plans based on channel
    if channel_type == "1":
        plans = config.CHANNEL_1_PLANS
        title = "HASEENA MAIN"
    elif channel_type == "2":
        plans = config.CHANNEL_2_PLANS
        title = "HASEENA 2.0"
    elif channel_type == "3":
        plans = config.CHANNEL_3_PLANS
        title = "SHEEP"
    else:  # all
        plans = config.ALL_IN_ONE_PLANS
        title = "ALL CHANNELS"
    
    # Build plan selection keyboard
    keyboard = []
    for plan_id, plan in plans.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{plan['label']} : Rs.{plan['price']} ({plan['days']} days)",
                callback_data=f"admin_plan_{plan_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("Back", callback_data="admin_back_channels")])
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="admin_cancel")])
    
    await query.edit_message_text(
        f"**ADD PREMIUM**\n"
        f"--------------------\n"
        f"Channel: {title}\n\n"
        f"Select a plan:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def admin_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin plan selection - ask for user ID."""
    query = update.callback_query
    await query.answer()
    
    plan_id = query.data.replace("admin_plan_", "")
    plan = config.PLANS.get(plan_id)
    
    if not plan:
        await query.edit_message_text("Invalid plan selected.")
        return
    
    # Store selected plan in user_data
    context.user_data["admin_add_plan"] = plan_id
    context.user_data["admin_add_days"] = plan["days"]
    context.user_data["admin_add_channel_name"] = plan["channel"]
    context.user_data["admin_add_label"] = plan["label"]
    context.user_data["awaiting_user_id"] = True
    
    keyboard = [[InlineKeyboardButton("Cancel", callback_data="admin_cancel")]]
    
    await query.edit_message_text(
        f"**ADD PREMIUM**\n"
        f"--------------------\n"
        f"Channel: {plan['channel']}\n"
        f"Plan: {plan['label']} ({plan['days']} days)\n"
        f"Price: Rs.{plan['price']}\n\n"
        f"**Now send the User ID:**\n"
        f"(Forward a message from the user or type their ID)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def admin_handle_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user ID input from admin."""
    if not is_admin(update.effective_user.id):
        return
    
    if not context.user_data.get("awaiting_user_id"):
        return
    
    # Check if it's a forwarded message - extract user ID
    user_id = None
    
    # Method 1: Check forward_origin (newer Telegram API - PTB v20+)
    if hasattr(update.message, 'forward_origin') and update.message.forward_origin:
        origin = update.message.forward_origin
        # MessageOriginUser type has sender_user attribute
        if hasattr(origin, 'sender_user') and origin.sender_user:
            user_id = origin.sender_user.id
            logger.info(f"Got user ID from forward_origin: {user_id}")
    
    # Method 2: Check forward_from (legacy - older PTB versions, user has privacy disabled)
    if user_id is None and hasattr(update.message, 'forward_from') and update.message.forward_from:
        user_id = update.message.forward_from.id
        logger.info(f"Got user ID from forward_from: {user_id}")
    
    # Method 3: Try to parse as user ID from text
    if user_id is None:
        try:
            # Try to extract user ID from the message text
            text = update.message.text or update.message.caption or ""
            text = text.strip()
            
            # Handle cases where text might contain other content
            # Look for a standalone number
            if text.isdigit():
                user_id = int(text)
                logger.info(f"Got user ID from text: {user_id}")
            else:
                # Try to find a user ID in the text (e.g., "User ID: 123456")
                import re
                match = re.search(r'\b(\d{6,15})\b', text)
                if match:
                    user_id = int(match.group(1))
                    logger.info(f"Got user ID from regex match: {user_id}")
    
        except (ValueError, AttributeError):
            pass
    
    # If still no user ID, show error
    if user_id is None:
        await update.message.reply_text(
            "Could not extract User ID!\n\n"
            "Possible reasons:\n"
            "- User has privacy settings enabled (forward won't work)\n"
            "- Invalid User ID format\n\n"
            "Please ask the user for their ID (they can get it from @userinfobot) and send it directly."
        )
        return
    
    # Get stored plan info
    days = context.user_data.get("admin_add_days")
    channel_name = context.user_data.get("admin_add_channel_name")
    label = context.user_data.get("admin_add_label")
    admin_channel = context.user_data.get("admin_add_channel")  # '1', '2', '3', or 'all'
    
    if not days:
        await update.message.reply_text("Session expired. Please start again with /addpremium")
        return
    
    # Map channel selection to channel_id
    channel_id_map = {'1': 'ch1', '2': 'ch2', '3': 'ch3', 'all': 'all'}
    channel_id = channel_id_map.get(admin_channel, 'all')
    
    # Check if user exists
    user = db.get_user(user_id)
    if not user:
        db.add_user(user_id)
    
    # Add premium for specific channel(s)
    db.add_premium(user_id, days, channel_id)
    expiry = db.get_premium_expiry(user_id, channel_id if channel_id != 'all' else None)
    
    # Clear admin session
    context.user_data.pop("awaiting_user_id", None)
    context.user_data.pop("admin_add_plan", None)
    context.user_data.pop("admin_add_days", None)
    context.user_data.pop("admin_add_channel", None)
    context.user_data.pop("admin_add_channel_name", None)
    context.user_data.pop("admin_add_label", None)
    
    await update.message.reply_text(
        f"**PREMIUM ADDED**\n"
        f"--------------------\n"
        f"User ID: `{user_id}`\n"
        f"Channel: {channel_name}\n"
        f"Plan: {label} ({days} days)\n"
        f"Expires: {expiry}",
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"**Congratulations!**\n\n"
                 f"Your premium has been activated!\n\n"
                 f"Channel: {channel_name}\n"
                 f"Validity: {days} days\n"
                 f"Expires: {expiry}\n\n"
                 f"Enjoy your premium access!",
            parse_mode="Markdown"
        )
        await update.message.reply_text("User has been notified!")
    except Exception as e:
        logger.error(f"Could not notify user: {e}")
        await update.message.reply_text("Could not notify user (they may have blocked the bot)")


async def admin_back_to_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to channel selection."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("HASEENA MAIN", callback_data="admin_ch_1")],
        [InlineKeyboardButton("HASEENA 2.0", callback_data="admin_ch_2")],
        [InlineKeyboardButton("SHEEP", callback_data="admin_ch_3")],
        [InlineKeyboardButton("ALL IN ONE", callback_data="admin_ch_all")],
        [InlineKeyboardButton("Cancel", callback_data="admin_cancel")],
    ]
    
    await query.edit_message_text(
        "**ADD PREMIUM**\n"
        "--------------------\n"
        "Select a channel:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel admin operation."""
    query = update.callback_query
    await query.answer()
    
    # Clear admin session
    context.user_data.pop("awaiting_user_id", None)
    context.user_data.pop("admin_add_plan", None)
    context.user_data.pop("admin_add_days", None)
    context.user_data.pop("admin_add_channel", None)
    context.user_data.pop("admin_add_channel_name", None)
    context.user_data.pop("admin_add_label", None)
    
    await query.edit_message_text("Operation cancelled.")


async def remove_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /removepremium command - Admin only."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not authorized.")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "Usage: /removepremium <user_id>\n"
            "Example: /removepremium 123456789"
        )
        return
    
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user_id.")
        return
    
    db.remove_premium(user_id)
    await update.message.reply_text(f"Premium removed from user `{user_id}`", parse_mode="Markdown")


async def check_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /checkuser command - Admin and Checker users."""
    if not is_checker(update.effective_user.id):
        await update.message.reply_text("You are not authorized.")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "Usage: /checkuser <user_id>\n"
            "Example: /checkuser 123456789"
        )
        return
    
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user_id.")
        return
    
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("User not found in database.")
        return
    
    # Get per-channel subscriptions
    subscriptions = db.get_user_subscriptions(user_id)
    has_any_premium = len(subscriptions) > 0
    
    # Build subscription details
    if subscriptions:
        sub_lines = []
        for sub in subscriptions:
            ch_name = config.CHANNEL_NAME_MAP.get(sub['channel_id'], sub['channel_id'])
            sub_lines.append(f"  - {ch_name}: {sub['expiry']}")
        subs_text = "\n".join(sub_lines)
    else:
        subs_text = "  No active subscriptions"
    
    status = "Premium" if has_any_premium else "Free"
    
    await update.message.reply_text(
        f"**User Info**\n\n"
        f"ID: `{user['user_id']}`\n"
        f"Name: {user['first_name'] or 'N/A'}\n"
        f"Username: @{user['username'] or 'N/A'}\n"
        f"Status: {status}\n\n"
        f"**Subscriptions:**\n{subs_text}\n\n"
        f"Joined: {user['joined_at']}",
        parse_mode="Markdown"
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - Admin only."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not authorized.")
        return
    
    stats = db.get_stats()
    channel_stats = stats.get('channel_stats', {})
    
    await update.message.reply_text(
        f"**Bot Statistics**\n\n"
        f"Total Users: {stats['total_users']}\n"
        f"Premium Users: {stats['premium_users']}\n"
        f"Free Users: {stats['free_users']}\n\n"
        f"**Per-Channel Subscriptions:**\n"
        f"  - HASEENA MAIN: {channel_stats.get('ch1', 0)}\n"
        f"  - HASEENA 2.0: {channel_stats.get('ch2', 0)}\n"
        f"  - SHEEP: {channel_stats.get('ch3', 0)}",
        parse_mode="Markdown"
    )


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command - Admin only."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not authorized.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /broadcast <message>\n"
            "Example: /broadcast Hello everyone!"
        )
        return
    
    message = " ".join(context.args)
    users = db.get_all_users()
    
    success = 0
    failed = 0
    
    status_msg = await update.message.reply_text("Please wait... Broadcasting...")
    
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            success += 1
        except Exception:
            failed += 1
    
    await status_msg.edit_text(
        f"Broadcast complete!\n\n"
        f"Sent: {success}\n"
        f"Failed: {failed}"
    )


async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new posts in the file channels - generate shareable link with channel code."""
    chat_id = update.channel_post.chat.id
    
    # Determine which channel this post is from
    channel_code = config.CHANNEL_ID_MAP.get(chat_id)
    if not channel_code:
        return  # Not a monitored channel
    
    message_id = update.channel_post.message_id
    bot_username = (await context.bot.get_me()).username
    
    # Include channel code in the start parameter for channel-specific access
    share_link = f"https://t.me/{bot_username}?start={channel_code}_{message_id}"
    channel_name = config.CHANNEL_NAME_MAP.get(channel_code, 'Unknown')
    
    # Reply with the shareable link
    await update.channel_post.reply_text(
        f"**Shareable Link ({channel_name}):**\n`{share_link}`",
        parse_mode="Markdown"
    )


async def view_plans_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /viewplans command - Admin only. View all current plans."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not authorized.")
        return
    
    plans = db.get_all_plans()
    
    if not plans:
        await update.message.reply_text("No plans found.")
        return
    
    # Group plans by channel
    ch1_plans = []
    ch2_plans = []
    ch3_plans = []
    all_plans = []
    
    for plan_id, plan in sorted(plans.items()):
        line = f"`{plan_id}` - {plan['label']} - Rs.{plan['price']} ({plan['days']} days)"
        if plan_id.startswith('ch1_'):
            ch1_plans.append(line)
        elif plan_id.startswith('ch2_'):
            ch2_plans.append(line)
        elif plan_id.startswith('ch3_'):
            ch3_plans.append(line)
        elif plan_id.startswith('all_'):
            all_plans.append(line)
    
    text = "**ALL PLANS**\n--------------------\n\n"
    
    if ch1_plans:
        text += "**HASEENA LINK (MAIN)**\n" + "\n".join(ch1_plans) + "\n\n"
    if ch2_plans:
        text += "**HASEENA(2.0)**\n" + "\n".join(ch2_plans) + "\n\n"
    if ch3_plans:
        text += "**SHEEP NEWS**\n" + "\n".join(ch3_plans) + "\n\n"
    if all_plans:
        text += "**ALL IN ONE**\n" + "\n".join(all_plans) + "\n\n"
    
    text += "--------------------\n"
    text += "To update: `/setplan <plan_id> <days> <price>`\n"
    text += "Example: `/setplan ch1_7_days 7 299`"
    
    await update.message.reply_text(text, parse_mode="Markdown")


async def set_plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setplan command - Admin only. Update a plan's days and price."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not authorized.")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /setplan <plan_id> <days> <price>\n\n"
            "Example: /setplan ch1_7_days 7 299\n\n"
            "Use /viewplans to see all plan IDs."
        )
        return
    
    plan_id = context.args[0]
    
    try:
        days = int(context.args[1])
        price = int(context.args[2])
    except ValueError:
        await update.message.reply_text("Days and price must be numbers.")
        return
    
    if days <= 0 or price <= 0:
        await update.message.reply_text("Days and price must be positive numbers.")
        return
    
    # Check if plan exists
    old_plan = db.get_plan(plan_id)
    if not old_plan:
        await update.message.reply_text(
            f"Plan `{plan_id}` not found.\n\n"
            "Use /viewplans to see all plan IDs.",
            parse_mode="Markdown"
        )
        return
    
    # Update the plan
    success = db.update_plan(plan_id, days=days, price=price)
    
    if success:
        # Refresh config to use new values
        db.refresh_config_plans()
        
        await update.message.reply_text(
            f"**PLAN UPDATED**\n"
            f"--------------------\n"
            f"Plan ID: `{plan_id}`\n"
            f"Channel: {old_plan['channel']}\n\n"
            f"**OLD:**\n"
            f"Days: {old_plan['days']}\n"
            f"Price: Rs.{old_plan['price']}\n\n"
            f"**NEW:**\n"
            f"Days: {days}\n"
            f"Price: Rs.{price}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("Failed to update plan.")


async def view_settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /viewsettings command - Admin only. View all current settings."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not authorized.")
        return
    
    settings = db.get_all_settings()
    
    if not settings:
        await update.message.reply_text("No settings found.")
        return
    
    # Format settings nicely
    text = "**BOT SETTINGS**\n--------------------\n\n"
    
    # Group by category
    payment_keys = ['upi_id', 'binance_id', 'paypal_email']
    admin_keys = ['admin_username', 'tutorial_link']
    channel_keys = ['channel_1_name', 'channel_2_name', 'channel_3_name']
    
    text += "**Payment Settings**\n"
    for key in payment_keys:
        if key in settings:
            text += f"`{key}`: {settings[key]}\n"
    
    text += "\n**Admin Settings**\n"
    for key in admin_keys:
        if key in settings:
            text += f"`{key}`: {settings[key]}\n"
    
    text += "\n**Channel Names**\n"
    for key in channel_keys:
        if key in settings:
            text += f"`{key}`: {settings[key]}\n"
    
    text += "\n--------------------\n"
    text += "To update: `/setsetting <key> <value>`\n"
    text += "Example: `/setsetting upi_id yourname@upi`"
    
    await update.message.reply_text(text, parse_mode="Markdown")


async def set_setting_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setsetting command - Admin only. Update a setting value."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not authorized.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /setsetting <key> <value>\n\n"
            "Available keys:\n"
            "- `upi_id` - UPI payment ID\n"
            "- `binance_id` - Binance Pay ID\n"
            "- `paypal_email` - PayPal email\n"
            "- `admin_username` - Admin username\n"
            "- `tutorial_link` - Tutorial URL\n"
            "- `channel_1_name` - Channel 1 name\n"
            "- `channel_2_name` - Channel 2 name\n"
            "- `channel_3_name` - Channel 3 name\n\n"
            "Example: `/setsetting upi_id yourname@paytm`",
            parse_mode="Markdown"
        )
        return
    
    key = context.args[0].lower()
    value = " ".join(context.args[1:])  # Allow spaces in value
    
    # Valid keys
    valid_keys = [
        'upi_id', 'binance_id', 'paypal_email', 
        'admin_username', 'tutorial_link',
        'channel_1_name', 'channel_2_name', 'channel_3_name'
    ]
    
    if key not in valid_keys:
        await update.message.reply_text(
            f"Invalid key `{key}`.\n\n"
            f"Valid keys: {', '.join(valid_keys)}",
            parse_mode="Markdown"
        )
        return
    
    # Get old value
    old_value = db.get_setting(key, "Not set")
    
    # Update the setting
    success = db.set_setting(key, value)
    
    if success:
        # Refresh config to use new values
        db.refresh_config_settings()
        
        await update.message.reply_text(
            f"**SETTING UPDATED**\n"
            f"--------------------\n"
            f"Key: `{key}`\n\n"
            f"**OLD:** {old_value}\n"
            f"**NEW:** {value}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("Failed to update setting.")


# ==============================================
# APPLICATION SETUP
# ==============================================

# Initialize database
db.init_db()

# Create application
application = Application.builder().token(config.BOT_TOKEN).build()

# User handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("plans", plans_command))
application.add_handler(CallbackQueryHandler(callback_handler))

# Admin handlers
application.add_handler(CommandHandler("addpremium", add_premium_command))
application.add_handler(CommandHandler("removepremium", remove_premium_command))
application.add_handler(CommandHandler("checkuser", check_user_command))
application.add_handler(CommandHandler("stats", stats_command))
application.add_handler(CommandHandler("broadcast", broadcast_command))
application.add_handler(CommandHandler("viewplans", view_plans_command))
application.add_handler(CommandHandler("setplan", set_plan_command))
application.add_handler(CommandHandler("viewsettings", view_settings_command))
application.add_handler(CommandHandler("setsetting", set_setting_command))

# Admin message handler for user ID input (must come before channel post handler)
application.add_handler(MessageHandler(
    filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND,
    admin_handle_user_id
))

# Channel post handler - monitor all 3 channels
application.add_handler(MessageHandler(
    filters.ChatType.CHANNEL & (filters.Chat(config.CHANNEL_1_ID) | filters.Chat(config.CHANNEL_2_ID) | filters.Chat(config.CHANNEL_3_ID)),
    handle_channel_post
))


def main():
    """Start the bot in polling mode (for local development)."""
    logger.info("Bot started in polling mode!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
