import praw
import sqlite3
import time
import os

# Reddit credentials
reddit = praw.Reddit(
    client_id="HJG70Y4rZ6SGk1F9unEY8g",
    client_secret="qFq5gT2tNjMfyHsX4aFNqNnXKKetnA",
    user_agent="subreddit_scraper by u/YOUR_USERNAME"
)

# Connect to database
db_path = "subreddits.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create table (without 'archived')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS subreddits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        subscribers INTEGER,
        created_utc REAL,
        last_checked TEXT,
        over18 BOOLEAN,
        quarantine BOOLEAN,
        restricted BOOLEAN
    )
''')

# Fetch popular subreddits (change limit if needed)
subreddits = reddit.subreddits.popular(limit=10)

new_entries = 0  # Counter for new inserts

for subreddit in subreddits:
    try:
        name = subreddit.display_name
        subscribers = subreddit.subscribers
        created_utc = subreddit.created_utc
        last_checked = time.strftime('%Y-%m-%d %H:%M:%S')
        over18 = subreddit.over18
        quarantine = subreddit.quarantine
        restricted = subreddit.restrict_posting

        cursor.execute('''
            INSERT OR IGNORE INTO subreddits 
            (name, subscribers, created_utc, last_checked, over18, quarantine, restricted)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, subscribers, created_utc, last_checked, over18, quarantine, restricted))

        if cursor.rowcount > 0:
            print(f"✅ Added: r/{name}")
            new_entries += 1
        else:
            print(f"⚠️ Skipped (duplicate): r/{name}")
    except Exception as e:
        print(f"❌ Error with r/{subreddit.display_name}: {e}")

# Commit and close
conn.commit()
conn.close()

print(f"✅ Done! New subreddits added: {new_entries}")
