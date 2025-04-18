# InactiveBot.py

import praw
import sqlite3
import datetime
import time
import os

# Reddit authentication
reddit = praw.Reddit(
    client_id="6pDYJFzCd_n3EVpzk5MlvQ",
    client_secret="yYFvV0ieN9ixcWZ43C3ZJvp0SjxqBQ",
    user_agent="subreddit_scraper by u/YOUR_USERNAME",
    username="yourpersonalhuman",
    password="Mudar!@#12"
)

MAX_DB_SIZE_MB = 100
BASE_DB_NAME = "subreddits"
max_duration = 21000  # 5h 50m
start_time = time.time()
db_index = 1

def get_db_filename(index):
    return f"{BASE_DB_NAME}{index}.db"

def get_db_size_mb(filename):
    if os.path.exists(filename):
        return os.path.getsize(filename) / (1024 * 1024)
    return 0

def find_latest_db_index():
    index = 1
    while os.path.exists(get_db_filename(index)):
        index += 1
    return index - 1 if index > 1 else 1

db_index = find_latest_db_index()
DB_FILE = get_db_filename(db_index)

if get_db_size_mb(DB_FILE) >= MAX_DB_SIZE_MB:
    db_index += 1
    DB_FILE = get_db_filename(db_index)

print(f"📁 Using database file: {DB_FILE}")
conn = sqlite3.connect(DB_FILE)
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
        posts_last_30_days INTEGER,
        last_post_utc REAL,
        after_token TEXT
    )
''')
conn.commit()

def get_after_token():
    c.execute("SELECT after_token FROM subreddits ORDER BY sr_no DESC LIMIT 1")
    row = c.fetchone()
    return row[0] if row else None

total_inserted = 0
total_skipped = 0

while time.time() - start_time < max_duration:
    after = get_after_token()
    print(f"\n⏩ Resuming from after_token: {after or 'START'}\n")

    batch_inserted = 0
    batch_skipped = 0
    last_fullname = None

    for subreddit in reddit.subreddits.new(limit=100, params={"after": after}):
        try:
            c.execute('''
                INSERT OR IGNORE INTO subreddits (
                    name, title, description, public_description, subscribers, active_user_count,
                    lang, type, url, created_utc, last_checked, over18, quarantine, restricted,
                    advertiser_category, submission_type, allow_videos, allow_images, allow_poll,
                    spoilers_enabled, comment_score_hide_mins, wiki_enabled,
                    posts_last_30_days, last_post_utc, after_token
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                None,
                None,
                subreddit.fullname
            ))

            db_size_kb = os.path.getsize(DB_FILE) / 1024

            if c.rowcount > 0:
                print(f"✅ Inserted: {subreddit.display_name} | DB: {DB_FILE} | Size: {db_size_kb:.2f} KB")
                batch_inserted += 1
            else:
                print(f"⏭️ Skipped (duplicate): {subreddit.display_name} | DB: {DB_FILE} | Size: {db_size_kb:.2f} KB")
                batch_skipped += 1

            last_fullname = subreddit.fullname

        except Exception as e:
            print(f"❌ Error saving {subreddit.display_name}: {e}")

        conn.commit()

        if get_db_size_mb(DB_FILE) >= MAX_DB_SIZE_MB:
            print(f"⚠️ {DB_FILE} reached {MAX_DB_SIZE_MB} MB limit. Switching DB...")
            conn.close()
            db_index += 1
            DB_FILE = get_db_filename(db_index)
            conn = sqlite3.connect(DB_FILE)
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
                    posts_last_30_days INTEGER,
                    last_post_utc REAL,
                    after_token TEXT
                )
            ''')
            conn.commit()
            print(f"✅ Switched to new DB: {DB_FILE}")

    print(f"\n📦 Batch Summary: Inserted {batch_inserted}, Skipped {batch_skipped}\n")
    total_inserted += batch_inserted
    total_skipped += batch_skipped

    if not last_fullname:
        print("🚫 No more new subreddits fetched. Stopping early.")
        break

    time.sleep(40)

conn.close()

with open("ready-to-commit.txt", "w") as f:
    f.write("ready")

print(f"\n🚀 DONE! Total Inserted: {total_inserted}, Total Skipped: {total_skipped}")
