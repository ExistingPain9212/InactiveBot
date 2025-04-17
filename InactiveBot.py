import praw
import sqlite3
import datetime

# Reddit authentication
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
        sr_no INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        title TEXT,
        description TEXT,
        public_description TEXT,
        subscribers INTEGER,
        active_user_count INTEGER,
        lang TEXT,
        type TEXT,
        url TEXT,
        created_utc REAL,
        last_checked TEXT,
        over18 INTEGER,
        quarantine INTEGER,
        restricted INTEGER,
        advertiser_category TEXT,
        submission_type TEXT,
        allow_videos INTEGER,
        allow_images INTEGER,
        allow_poll INTEGER,
        spoilers_enabled INTEGER,
        comment_score_hide_mins INTEGER,
        wiki_enabled INTEGER,
        after_token TEXT
    )
''')
conn.commit()

# Get after token logic
def get_after_token():
    c.execute("SELECT after_token FROM subreddits ORDER BY sr_no DESC LIMIT 1")
    row = c.fetchone()
    return row[0] if row else None

after = get_after_token()
print(f"Resuming from: {after}")

count = 0
for subreddit in reddit.subreddits.new(limit=10, params={"after": after}):
    try:
        c.execute('''
            INSERT OR IGNORE INTO subreddits (
                name, title, description, public_description, subscribers, active_user_count,
                lang, type, url, created_utc, last_checked, over18, quarantine, restricted,
                advertiser_category, submission_type, allow_videos, allow_images, allow_poll,
                spoilers_enabled, comment_score_hide_mins, wiki_enabled, after_token
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            subreddit.display_name,
            subreddit.title or '',
            getattr(subreddit, 'description', '') or '',
            getattr(subreddit, 'public_description', '') or '',
            subreddit.subscribers or 0,
            getattr(subreddit, 'active_user_count', 0) or 0,
            getattr(subreddit, 'lang', '') or '',
            getattr(subreddit, 'subreddit_type', '') or '',
            subreddit.url or '',
            float(subreddit.created_utc) if subreddit.created_utc else 0,
            datetime.datetime.utcnow().isoformat(),
            int(bool(subreddit.over18)),
            int(bool(getattr(subreddit, 'quarantine', False))),
            int(bool(getattr(subreddit, 'restrict_posting', False))),
            getattr(subreddit, 'advertiser_category', '') or '',
            getattr(subreddit, 'submission_type', '') or '',
            int(bool(getattr(subreddit, 'allow_videos', False))),
            int(bool(getattr(subreddit, 'allow_images', False))),
            int(bool(getattr(subreddit, 'allow_poll', False))),
            int(bool(getattr(subreddit, 'spoilers_enabled', False))),
            int(getattr(subreddit, 'comment_score_hide_mins', 0) or 0),
            int(bool(getattr(subreddit, 'wiki_enabled', False))),
            subreddit.display_name  # after_token
        ))
        count += 1
    except Exception as e:
        print(f"⚠️ Error saving subreddit {subreddit.display_name}: {e}")

conn.commit()
conn.close()

# Write commit marker
with open("ready-to-commit.txt", "w") as f:
    f.write("ready")

print(f"✅ Scraped and saved {count} subreddits successfully.")
