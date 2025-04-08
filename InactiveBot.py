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

# Check if database exists
db_exists = os.path.isfile("subreddits.db")

# Connect to SQLite
conn = sqlite3.connect("subreddits.db")
cursor = conn.cursor()

# Create table if not exists
if not db_exists:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subreddits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            title TEXT,
            description TEXT,
            subscribers INTEGER,
            created_utc REAL,
            last_checked TEXT,
            over18 BOOLEAN,
            lang TEXT,
            url TEXT,
            active_user_count INTEGER,
            accounts_active_is_fuzzed BOOLEAN,
            advertiser_category TEXT,
            submission_type TEXT,
            subreddit_type TEXT,
            quarantine BOOLEAN,
            user_is_moderator BOOLEAN,
            user_is_subscriber BOOLEAN,
            public_description TEXT,
            display_name_prefixed TEXT,
            banner_img TEXT,
            icon_img TEXT
        )
    ''')

# Fetch subreddits (you can increase the limit as needed)
subreddits = reddit.subreddits.popular(limit=10)

count = 0
for subreddit in subreddits:
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO subreddits (
                name, title, description, subscribers, created_utc, last_checked,
                over18, lang, url, active_user_count, accounts_active_is_fuzzed,
                advertiser_category, submission_type, subreddit_type, quarantine,
                user_is_moderator, user_is_subscriber, public_description,
                display_name_prefixed, banner_img, icon_img
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            subreddit.display_name,
            subreddit.title,
            subreddit.description,
            subreddit.subscribers,
            subreddit.created_utc,
            time.strftime('%Y-%m-%d %H:%M:%S'),
            subreddit.over18,
            subreddit.lang,
            subreddit.url,
            subreddit.active_user_count,
            subreddit.accounts_active_is_fuzzed,
            subreddit.advertiser_category,
            subreddit.submission_type,
            subreddit.subreddit_type,
            subreddit.quarantine,
            subreddit.user_is_moderator,
            subreddit.user_is_subscriber,
            subreddit.public_description,
            subreddit.display_name_prefixed,
            subreddit.banner_img,
            subreddit.icon_img
        ))

        if cursor.rowcount:
            print(f"✅ Added: r/{subreddit.display_name}")
            count += 1
        else:
            print(f"ℹ️ Skipped (already exists): r/{subreddit.display_name}")

    except Exception as e:
        print(f"❌ Error with r/{subreddit.display_name}: {e}")

# Finalize and close
conn.commit()
conn.close()

print(f"✅ Done! {count} new subreddits added to subreddits.db")
