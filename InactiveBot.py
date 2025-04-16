import praw
import sqlite3
import datetime

# Reddit auth using secrets from GitHub Actions
reddit = praw.Reddit(
    client_id="6pDYJFzCd_n3EVpzk5MlvQ",
    client_secret="yYFvV0ieN9ixcWZ43C3ZJvp0SjxqBQ",
    user_agent="subreddit_scraper by u/YOUR_USERNAME",
    username="yourpersonalhuman",
    password="Mudar!@#12"
)

# Setup SQLite DB
conn = sqlite3.connect('subreddits.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS subreddits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        title TEXT,
        subscribers INTEGER,
        created_utc REAL,
        last_checked TEXT,
        over18 INTEGER,
        quarantine INTEGER,
        restricted INTEGER
    )
''')
conn.commit()

# Scrape up to 10 new subreddits
count = 0
for subreddit in reddit.subreddits.new(limit=None):
    name = subreddit.display_name
    title = subreddit.title
    subscribers = subreddit.subscribers or 0
    created_utc = float(subreddit.created_utc)
    last_checked = datetime.datetime.utcnow().isoformat()
    over18 = int(subreddit.over18)
    quarantine = int(getattr(subreddit, "quarantine", False))
    restricted = int(getattr(subreddit, "restrict_posting", False))

    try:
        c.execute('''
            INSERT OR IGNORE INTO subreddits (
                name, title, subscribers, created_utc,
                last_checked, over18, quarantine, restricted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, title, subscribers, created_utc, last_checked, over18, quarantine, restricted))
        if c.rowcount > 0:
            count += 1
    except Exception as e:
        print(f"Error inserting {name}: {e}")

    if count >= 10:
        break

conn.commit()
conn.close()

# Create marker file to trigger branch commit
with open("ready-to-commit.txt", "w") as f:
    f.write("Subreddits updated")

print(f"✅ Scraped and saved {count} new subreddits successfully.")
