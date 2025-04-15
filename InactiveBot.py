import praw
import sqlite3
import datetime
import os

# Reddit auth using secrets from GitHub Actions
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    username=os.getenv('REDDIT_USERNAME'),
    password=os.getenv('REDDIT_PASSWORD'),
    user_agent='minimal-scraper-test'
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
        restricted INTEGER,
        after_token TEXT
    )
''')
conn.commit()

# Get 10 subreddits with after token logic
def get_after_token():
    c.execute("SELECT after_token FROM subreddits ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    return row[0] if row else None

after = get_after_token()
print(f"Resuming from: {after}")

count = 0
for subreddit in reddit.subreddits.default(limit=10, params={"after": after}):
    name = subreddit.display_name
    title = subreddit.title
    subscribers = subreddit.subscribers or 0
    created_utc = float(subreddit.created_utc)
    last_checked = datetime.datetime.utcnow().isoformat()
    over18 = int(subreddit.over18)
    quarantine = int(getattr(subreddit, "quarantine", False))
    restricted = int(getattr(subreddit, "restrict_posting", False))
    after_token = name

    c.execute('''
        INSERT OR IGNORE INTO subreddits (
            name, title, subscribers, created_utc,
            last_checked, over18, quarantine, restricted, after_token
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, title, subscribers, created_utc, last_checked, over18, quarantine, restricted, after_token))
    count += 1

conn.commit()
conn.close()

print(f"✅ Scraped and saved {count} subreddits successfully.")
