import sqlite3
from datetime import datetime, timedelta
from config import DATABASE_PATH


def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            is_premium INTEGER DEFAULT 0,
            premium_expiry TEXT,
            joined_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def add_user(user_id: int, username: str = None, first_name: str = None):
    """Add a new user or update existing user info."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
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
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "is_premium": bool(row[3]),
            "premium_expiry": row[4],
            "joined_at": row[5]
        }
    return None


def is_premium(user_id: int) -> bool:
    """Check if user has active premium."""
    user = get_user(user_id)
    if not user or not user["is_premium"]:
        return False
    
    if user["premium_expiry"]:
        expiry = datetime.fromisoformat(user["premium_expiry"])
        if expiry < datetime.now():
            # Premium expired, update status
            remove_premium(user_id)
            return False
    
    return True


def get_premium_expiry(user_id: int) -> str:
    """Get premium expiry date as formatted string."""
    user = get_user(user_id)
    if user and user["premium_expiry"]:
        expiry = datetime.fromisoformat(user["premium_expiry"])
        return expiry.strftime("%d %b %Y, %I:%M %p")
    return "N/A"


def add_premium(user_id: int, days: int):
    """Add premium days to a user."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get current expiry if exists
    user = get_user(user_id)
    if user and user["premium_expiry"]:
        try:
            current_expiry = datetime.fromisoformat(user["premium_expiry"])
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
    
    cursor.execute("""
        UPDATE users SET is_premium = 1, premium_expiry = ?
        WHERE user_id = ?
    """, (new_expiry.isoformat(), user_id))
    
    conn.commit()
    conn.close()


def remove_premium(user_id: int):
    """Remove premium from a user."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users SET is_premium = 0, premium_expiry = NULL
        WHERE user_id = ?
    """, (user_id,))
    
    conn.commit()
    conn.close()


def get_all_users() -> list:
    """Get all users."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    
    return [row[0] for row in rows]


def get_stats() -> dict:
    """Get bot statistics."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
    premium_users = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "free_users": total_users - premium_users
    }


# Initialize database on import
init_db()
