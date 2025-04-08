import praw
import sqlite3
import time
import os

# Your Reddit app credentials
reddit = praw.Reddit(
    client_id="HJG70Y4rZ6SGk1F9unEY8g",
    client_secret="qFq5gT2tNjMfyHsX4aFNqNnXKKetnA",
    user_agent="subreddit_scraper by u/YOUR_USERNAME"
)

DB_PATH = "subreddits.db"

# Connect to SQLite (will create only if it doesn't exist)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS subreddits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        title TEXT,
        description TEXT,
        subscribers INTEGER,
        created_utc REAL,
        last_checked TEXT
    )
''')

# Fetch subreddits using Reddit API (limited for demo/testing)
subreddits = reddit.subreddits.popular(limit=10)

added = 0
for subreddit in subreddits:
    try:
        name = subreddit.display_name
        title = subreddit.title
        description = subreddit.public_description
        subscribers = subreddit.subscribers
        created_utc = subreddit.created_utc
        last_checked = time.strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
            INSERT OR IGNORE INTO subreddits 
            (name, title, description, subscribers, created_utc, last_checked)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, title, description, subscribers, created_utc, last_checked))

        if cursor.rowcount > 0:
            print(f"✅ Added: r/{name}")
            added += 1
        else:
            print(f"⚠️ Skipped (duplicate): r/{name}")

    except Exception as e:
        print(f"❌ Error with r/{subreddit.display_name}: {e}")

# Save and close
conn.commit()
conn.close()

print(f"✅ Done! Added {added} new subreddits to {DB_PATH}")
