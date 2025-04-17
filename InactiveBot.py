import praw
import sqlite3
import time
from datetime import datetime

# --- AUTH: Old PRAW-style user authentication ---
reddit = praw.Reddit(
    client_id="6pDYJFzCd_n3EVpzk5MlvQ",
    client_secret="yYFvV0ieN9ixcWZ43C3ZJvp0SjxqBQ",
    username="yourpersonalhuman",
    password="Mudar!@#12",
    user_agent="inactive-subreddit-bot/0.1 by u/YOUR_USERNAME"
)

# --- DATABASE SETUP ---
conn = sqlite3.connect("subreddits.db")
c = conn.cursor()

c.execute("""
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
    created_utc INTEGER,
    last_checked INTEGER,
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
""")

# Get last after_token
c.execute("SELECT after_token FROM subreddits ORDER BY sr_no DESC LIMIT 1")
row = c.fetchone()
after_token = row[0] if row and row[0] else None

# --- SCRAPE SUBREDDITS ---
count = 0
limit = 10
subreddits = reddit.subreddits.new(limit=None)
for subreddit in subreddits:
    if count >= limit:
        break

    if after_token and subreddit.fullname <= after_token:
        continue

    data = {
        "name": subreddit.display_name,
        "title": subreddit.title,
        "description": subreddit.description,
        "public_description": subreddit.public_description,
        "subscribers": subreddit.subscribers,
        "active_user_count": subreddit.accounts_active,
        "lang": subreddit.lang,
        "type": subreddit.subreddit_type,
        "url": subreddit.url,
        "created_utc": int(subreddit.created_utc),
        "last_checked": int(time.time()),
        "over18": int(subreddit.over18),
        "quarantine": int(subreddit.quarantine),
        "restricted": int(subreddit.restrict_posting),
        "advertiser_category": subreddit.advertiser_category,
        "submission_type": subreddit.submission_type,
        "allow_videos": int(subreddit.allow_videos),
        "allow_images": int(subreddit.allow_images),
        "allow_poll": int(subreddit.allow_polls),
        "spoilers_enabled": int(subreddit.spoilers_enabled),
        "comment_score_hide_mins": subreddit.comment_score_hide_mins,
        "wiki_enabled": int(subreddit.wiki_enabled),
        "after_token": subreddit.fullname
    }

    try:
        c.execute("""
            INSERT OR IGNORE INTO subreddits (
                name, title, description, public_description, subscribers, active_user_count,
                lang, type, url, created_utc, last_checked, over18, quarantine, restricted,
                advertiser_category, submission_type, allow_videos, allow_images, allow_poll,
                spoilers_enabled, comment_score_hide_mins, wiki_enabled, after_token
            ) VALUES (
                :name, :title, :description, :public_description, :subscribers, :active_user_count,
                :lang, :type, :url, :created_utc, :last_checked, :over18, :quarantine, :restricted,
                :advertiser_category, :submission_type, :allow_videos, :allow_images, :allow_poll,
                :spoilers_enabled, :comment_score_hide_mins, :wiki_enabled, :after_token
            )
        """, data)
        conn.commit()
        count += 1
        print(f"[{count}] Saved r/{subreddit.display_name}")
    except Exception as e:
        print(f"Error saving r/{subreddit.display_name}: {e}")

# --- FINALIZE ---
if count > 0:
    with open("ready-to-commit.txt", "w") as f:
        f.write("Database ready to commit.\n")

conn.close()
print("Done.")
