import os
from datetime import datetime, timedelta
from config import DATABASE_URL, DATABASE_PATH

# Try to use PostgreSQL if DATABASE_URL is set, otherwise fall back to SQLite
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
else:
    import sqlite3


def get_connection():
    """Get database connection based on configuration."""
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect(DATABASE_PATH)


def init_db():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        # PostgreSQL syntax
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Channel subscriptions table - tracks per-channel access
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channel_subscriptions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                channel_id TEXT NOT NULL,
                expiry TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, channel_id)
            )
        """)
        
        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_subs_user_id ON channel_subscriptions(user_id)
        """)
    else:
        # SQLite syntax
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Channel subscriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channel_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id TEXT NOT NULL,
                expiry TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, channel_id)
            )
        """)
    
    conn.commit()
    conn.close()


def add_user(user_id: int, username: str = None, first_name: str = None):
    """Add a new user or update existing user info."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (%s, %s, %s)
            ON CONFLICT(user_id) DO UPDATE SET
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name
        """, (user_id, username, first_name))
    else:
        cursor.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
        """, (user_id, username, first_name))
    
    conn.commit()
    conn.close()


def get_user(user_id: int) -> dict:
    """Get user information."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("SELECT user_id, username, first_name, joined_at FROM users WHERE user_id = %s", (user_id,))
    else:
        cursor.execute("SELECT user_id, username, first_name, joined_at FROM users WHERE user_id = ?", (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "joined_at": row[3]
        }
    return None


def add_premium(user_id: int, days: int, channel_id: str = 'all'):
    """Add premium subscription for a specific channel or all channels.
    
    Args:
        user_id: The user's Telegram ID
        days: Number of days for the subscription
        channel_id: 'ch1', 'ch2', 'ch3', or 'all' for all channels
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Determine which channels to add
    if channel_id == 'all':
        channels = ['ch1', 'ch2', 'ch3']
    else:
        channels = [channel_id]
    
    for ch in channels:
        # Get current expiry if exists
        if USE_POSTGRES:
            cursor.execute(
                "SELECT expiry FROM channel_subscriptions WHERE user_id = %s AND channel_id = %s",
                (user_id, ch)
            )
        else:
            cursor.execute(
                "SELECT expiry FROM channel_subscriptions WHERE user_id = ? AND channel_id = ?",
                (user_id, ch)
            )
        
        row = cursor.fetchone()
        
        if row and row[0]:
            try:
                if USE_POSTGRES:
                    current_expiry = row[0]  # Already a datetime in PostgreSQL
                else:
                    current_expiry = datetime.fromisoformat(row[0])
                
                if current_expiry > datetime.now():
                    # Extend from current expiry
                    new_expiry = current_expiry + timedelta(days=days)
                else:
                    # Start from now
                    new_expiry = datetime.now() + timedelta(days=days)
            except:
                new_expiry = datetime.now() + timedelta(days=days)
        else:
            new_expiry = datetime.now() + timedelta(days=days)
        
        # Insert or update subscription
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO channel_subscriptions (user_id, channel_id, expiry)
                VALUES (%s, %s, %s)
                ON CONFLICT(user_id, channel_id) DO UPDATE SET
                    expiry = EXCLUDED.expiry
            """, (user_id, ch, new_expiry))
        else:
            cursor.execute("""
                INSERT INTO channel_subscriptions (user_id, channel_id, expiry)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, channel_id) DO UPDATE SET
                    expiry = excluded.expiry
            """, (user_id, ch, new_expiry.isoformat()))
    
    conn.commit()
    conn.close()


def has_channel_access(user_id: int, channel_id: str) -> bool:
    """Check if user has active access to a specific channel.
    
    Args:
        user_id: The user's Telegram ID
        channel_id: 'ch1', 'ch2', or 'ch3'
    
    Returns:
        True if user has active subscription for the channel
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute(
            "SELECT expiry FROM channel_subscriptions WHERE user_id = %s AND channel_id = %s",
            (user_id, channel_id)
        )
    else:
        cursor.execute(
            "SELECT expiry FROM channel_subscriptions WHERE user_id = ? AND channel_id = ?",
            (user_id, channel_id)
        )
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return False
    
    try:
        if USE_POSTGRES:
            expiry = row[0]
        else:
            expiry = datetime.fromisoformat(row[0])
        
        return expiry > datetime.now()
    except:
        return False


def is_premium(user_id: int, channel_id: str = None) -> bool:
    """Check if user has active premium.
    
    Args:
        user_id: The user's Telegram ID
        channel_id: Optional - check specific channel, or None to check if user has any active subscription
    
    Returns:
        True if user has active subscription
    """
    if channel_id:
        return has_channel_access(user_id, channel_id)
    
    # Check if user has any active subscription
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now()
    
    if USE_POSTGRES:
        cursor.execute(
            "SELECT COUNT(*) FROM channel_subscriptions WHERE user_id = %s AND expiry > %s",
            (user_id, now)
        )
    else:
        cursor.execute(
            "SELECT COUNT(*) FROM channel_subscriptions WHERE user_id = ? AND expiry > ?",
            (user_id, now.isoformat())
        )
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0


def get_user_subscriptions(user_id: int) -> list:
    """Get all active subscriptions for a user.
    
    Returns:
        List of dicts with channel_id and expiry for each active subscription
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now()
    
    if USE_POSTGRES:
        cursor.execute(
            "SELECT channel_id, expiry FROM channel_subscriptions WHERE user_id = %s AND expiry > %s ORDER BY channel_id",
            (user_id, now)
        )
    else:
        cursor.execute(
            "SELECT channel_id, expiry FROM channel_subscriptions WHERE user_id = ? AND expiry > ? ORDER BY channel_id",
            (user_id, now.isoformat())
        )
    
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        if USE_POSTGRES:
            expiry = row[1]
        else:
            expiry = datetime.fromisoformat(row[1])
        
        result.append({
            'channel_id': row[0],
            'expiry': expiry.strftime("%d %b %Y, %I:%M %p")
        })
    
    return result


def get_premium_expiry(user_id: int, channel_id: str = None) -> str:
    """Get premium expiry date as formatted string.
    
    Args:
        user_id: The user's Telegram ID
        channel_id: Optional - get expiry for specific channel
    
    Returns:
        Formatted expiry date or 'N/A'
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if channel_id:
        if USE_POSTGRES:
            cursor.execute(
                "SELECT expiry FROM channel_subscriptions WHERE user_id = %s AND channel_id = %s",
                (user_id, channel_id)
            )
        else:
            cursor.execute(
                "SELECT expiry FROM channel_subscriptions WHERE user_id = ? AND channel_id = ?",
                (user_id, channel_id)
            )
    else:
        # Get the latest expiry across all channels
        if USE_POSTGRES:
            cursor.execute(
                "SELECT MAX(expiry) FROM channel_subscriptions WHERE user_id = %s",
                (user_id,)
            )
        else:
            cursor.execute(
                "SELECT MAX(expiry) FROM channel_subscriptions WHERE user_id = ?",
                (user_id,)
            )
    
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0]:
        try:
            if USE_POSTGRES:
                expiry = row[0]
            else:
                expiry = datetime.fromisoformat(row[0])
            return expiry.strftime("%d %b %Y, %I:%M %p")
        except:
            pass
    
    return "N/A"


def remove_premium(user_id: int, channel_id: str = None):
    """Remove premium subscription from a user.
    
    Args:
        user_id: The user's Telegram ID
        channel_id: Optional - remove specific channel, or None to remove all
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if channel_id:
        if USE_POSTGRES:
            cursor.execute(
                "DELETE FROM channel_subscriptions WHERE user_id = %s AND channel_id = %s",
                (user_id, channel_id)
            )
        else:
            cursor.execute(
                "DELETE FROM channel_subscriptions WHERE user_id = ? AND channel_id = ?",
                (user_id, channel_id)
            )
    else:
        # Remove all subscriptions
        if USE_POSTGRES:
            cursor.execute("DELETE FROM channel_subscriptions WHERE user_id = %s", (user_id,))
        else:
            cursor.execute("DELETE FROM channel_subscriptions WHERE user_id = ?", (user_id,))
    
    conn.commit()
    conn.close()


def get_all_users() -> list:
    """Get all users."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    
    return [row[0] for row in rows]


def get_stats() -> dict:
    """Get bot statistics with per-channel breakdown."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    now = datetime.now()
    
    # Users with any active subscription
    if USE_POSTGRES:
        cursor.execute(
            "SELECT COUNT(DISTINCT user_id) FROM channel_subscriptions WHERE expiry > %s",
            (now,)
        )
    else:
        cursor.execute(
            "SELECT COUNT(DISTINCT user_id) FROM channel_subscriptions WHERE expiry > ?",
            (now.isoformat(),)
        )
    premium_users = cursor.fetchone()[0]
    
    # Per-channel stats
    channel_stats = {}
    for ch in ['ch1', 'ch2', 'ch3']:
        if USE_POSTGRES:
            cursor.execute(
                "SELECT COUNT(*) FROM channel_subscriptions WHERE channel_id = %s AND expiry > %s",
                (ch, now)
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM channel_subscriptions WHERE channel_id = ? AND expiry > ?",
                (ch, now.isoformat())
            )
        channel_stats[ch] = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "free_users": total_users - premium_users,
        "channel_stats": channel_stats
    }


# ==============================================
# DYNAMIC PLANS MANAGEMENT
# ==============================================

def init_plans_table():
    """Initialize the plans table for dynamic plan management."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                plan_id TEXT PRIMARY KEY,
                days INTEGER NOT NULL,
                price INTEGER NOT NULL,
                label TEXT NOT NULL,
                channel TEXT NOT NULL
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                plan_id TEXT PRIMARY KEY,
                days INTEGER NOT NULL,
                price INTEGER NOT NULL,
                label TEXT NOT NULL,
                channel TEXT NOT NULL
            )
        """)
    
    conn.commit()
    conn.close()


def populate_default_plans():
    """Populate plans table with default plans from config if empty."""
    import config
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if plans table is empty
    cursor.execute("SELECT COUNT(*) FROM plans")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Insert default plans from config
        for plan_id, plan in config.PLANS.items():
            if USE_POSTGRES:
                cursor.execute("""
                    INSERT INTO plans (plan_id, days, price, label, channel)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT(plan_id) DO NOTHING
                """, (plan_id, plan['days'], plan['price'], plan['label'], plan['channel']))
            else:
                cursor.execute("""
                    INSERT INTO plans (plan_id, days, price, label, channel)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(plan_id) DO NOTHING
                """, (plan_id, plan['days'], plan['price'], plan['label'], plan['channel']))
        
        conn.commit()
    
    conn.close()


def get_all_plans() -> dict:
    """Get all plans from database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT plan_id, days, price, label, channel FROM plans ORDER BY plan_id")
    rows = cursor.fetchall()
    conn.close()
    
    plans = {}
    for row in rows:
        plans[row[0]] = {
            'days': row[1],
            'price': row[2],
            'label': row[3],
            'channel': row[4]
        }
    
    return plans


def update_plan(plan_id: str, days: int = None, price: int = None, label: str = None) -> bool:
    """Update a plan's days, price, or label.
    
    Args:
        plan_id: The plan ID to update
        days: New number of days (optional)
        price: New price (optional)
        label: New label (optional)
    
    Returns:
        True if plan was updated, False if plan not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if plan exists
    if USE_POSTGRES:
        cursor.execute("SELECT plan_id FROM plans WHERE plan_id = %s", (plan_id,))
    else:
        cursor.execute("SELECT plan_id FROM plans WHERE plan_id = ?", (plan_id,))
    
    if not cursor.fetchone():
        conn.close()
        return False
    
    # Build update query
    updates = []
    params = []
    
    if days is not None:
        updates.append("days = %s" if USE_POSTGRES else "days = ?")
        params.append(days)
    
    if price is not None:
        updates.append("price = %s" if USE_POSTGRES else "price = ?")
        params.append(price)
    
    if label is not None:
        updates.append("label = %s" if USE_POSTGRES else "label = ?")
        params.append(label)
    
    if not updates:
        conn.close()
        return True
    
    params.append(plan_id)
    
    query = f"UPDATE plans SET {', '.join(updates)} WHERE plan_id = {'%s' if USE_POSTGRES else '?'}"
    cursor.execute(query, params)
    
    conn.commit()
    conn.close()
    return True


def get_plan(plan_id: str) -> dict:
    """Get a single plan by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("SELECT plan_id, days, price, label, channel FROM plans WHERE plan_id = %s", (plan_id,))
    else:
        cursor.execute("SELECT plan_id, days, price, label, channel FROM plans WHERE plan_id = ?", (plan_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'plan_id': row[0],
            'days': row[1],
            'price': row[2],
            'label': row[3],
            'channel': row[4]
        }
    return None


def refresh_config_plans():
    """Refresh the config module's PLANS from database."""
    import config
    
    db_plans = get_all_plans()
    
    if db_plans:
        # Update the main PLANS dict
        config.PLANS.clear()
        config.PLANS.update(db_plans)
        
        # Update channel-specific plan dicts
        config.CHANNEL_1_PLANS.clear()
        config.CHANNEL_2_PLANS.clear()
        config.CHANNEL_3_PLANS.clear()
        config.ALL_IN_ONE_PLANS.clear()
        
        for plan_id, plan in db_plans.items():
            if plan_id.startswith('ch1_'):
                config.CHANNEL_1_PLANS[plan_id] = plan
            elif plan_id.startswith('ch2_'):
                config.CHANNEL_2_PLANS[plan_id] = plan
            elif plan_id.startswith('ch3_'):
                config.CHANNEL_3_PLANS[plan_id] = plan
            elif plan_id.startswith('all_'):
                config.ALL_IN_ONE_PLANS[plan_id] = plan


# ==============================================
# DYNAMIC SETTINGS MANAGEMENT
# ==============================================

def init_settings_table():
    """Initialize the settings table for dynamic settings management."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
    
    conn.commit()
    conn.close()


def populate_default_settings():
    """Populate settings table with default settings from config if empty."""
    import config
    
    default_settings = {
        'upi_id': config.UPI_ID,
        'binance_id': config.BINANCE_ID,
        'paypal_email': config.PAYPAL_EMAIL,
        'admin_username': config.ADMIN_USERNAME,
        'tutorial_link': config.TUTORIAL_LINK,
        'channel_1_name': 'HASEENA MAIN',
        'channel_2_name': 'HASEENA 2.0',
        'channel_3_name': 'SHEEP',
        'start_image_url': getattr(config, 'START_IMAGE_URL', ''),
        'premium_image_url': getattr(config, 'PREMIUM_IMAGE_URL', ''),
    }
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for key, value in default_settings.items():
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO settings (key, value)
                VALUES (%s, %s)
                ON CONFLICT(key) DO NOTHING
            """, (key, value))
        else:
            cursor.execute("""
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO NOTHING
            """, (key, value))
    
    conn.commit()
    conn.close()


def get_setting(key: str, default: str = None) -> str:
    """Get a setting value by key."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("SELECT value FROM settings WHERE key = %s", (key,))
    else:
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0]
    return default


def set_setting(key: str, value: str) -> bool:
    """Set a setting value."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("""
            INSERT INTO settings (key, value)
            VALUES (%s, %s)
            ON CONFLICT(key) DO UPDATE SET value = EXCLUDED.value
        """, (key, value))
    else:
        cursor.execute("""
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))
    
    conn.commit()
    conn.close()
    return True


def get_all_settings() -> dict:
    """Get all settings as a dictionary."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT key, value FROM settings ORDER BY key")
    rows = cursor.fetchall()
    conn.close()
    
    return {row[0]: row[1] for row in rows}


def refresh_config_settings():
    """Refresh the config module's settings from database."""
    import config
    
    settings = get_all_settings()
    
    if settings:
        # Update config values
        if 'upi_id' in settings:
            config.UPI_ID = settings['upi_id']
        if 'binance_id' in settings:
            config.BINANCE_ID = settings['binance_id']
        if 'paypal_email' in settings:
            config.PAYPAL_EMAIL = settings['paypal_email']
        if 'admin_username' in settings:
            config.ADMIN_USERNAME = settings['admin_username']
        if 'tutorial_link' in settings:
            config.TUTORIAL_LINK = settings['tutorial_link']
        if 'start_image_url' in settings:
            config.START_IMAGE_URL = settings['start_image_url']
        if 'premium_image_url' in settings:
            config.PREMIUM_IMAGE_URL = settings['premium_image_url']
        
        # Update channel name map
        if 'channel_1_name' in settings:
            config.CHANNEL_NAME_MAP['ch1'] = settings['channel_1_name']
        if 'channel_2_name' in settings:
            config.CHANNEL_NAME_MAP['ch2'] = settings['channel_2_name']
        if 'channel_3_name' in settings:
            config.CHANNEL_NAME_MAP['ch3'] = settings['channel_3_name']


# Initialize database on import
init_db()
init_plans_table()
populate_default_plans()
refresh_config_plans()
init_settings_table()
populate_default_settings()
refresh_config_settings()

