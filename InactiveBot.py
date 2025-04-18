import praw
import sqlite3
import datetime
import time
import os

MAX_DB_SIZE_MB = 100
MAX_DURATION_SECONDS = 5 * 3600 + 50 * 60  # 5 hours 50 minutes

# Reddit auth
reddit = praw.Reddit(
    client_id="6pDYJFzCd_n3EVpzk5MlvQ",
    client_secret="yYFvV0ieN9ixcWZ43C3ZJvp0SjxqBQ",
    user_agent="subreddit_scraper by u/YOUR_USERNAME",
    username="yourpersonalhuman",
    password="Mudar!@#12"
)

# ---------------------- DB Setup and Rotation Logic ------------------------

def get_db_size_mb(path):
    return os.path.getsize(path) / (1024 * 1024)

def get_db_filename(index):
    if index == 0:
        return "subreddits.db"
    return f"subreddits{index}.db"

def find_initial_db_file():
    if os.path.exists("subreddits.db"):
        return "subreddits.db", 0
    else:
        index = 1
        while os.path.exists(get_db_filename(index)):
            index += 1
        return get_db_filename(index - 1 if index > 1 else 1), max(1, index - 1)

DB_FILE, db_index = find_initial_db_file()

print(f"📂 Using database: {DB_FILE}")

# Connect to database
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

# Get last after_token
def get_after_token():
    c.execute("SELECT after_token FROM subreddits ORDER BY sr_no DESC LIMIT 1")
    row = c.fetchone()
    return row[0] if row else None

# ---------------------- Main Scraping Loop ------------------------

start_time = time.time()
total_inserted = 0
total_skipped = 0

while time.time() - start_time < MAX_DURATION_SECONDS:
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
                None,  # posts_last_30_days
                None,  # last_post_utc
                subreddit.fullname
            ))

            if c.rowcount > 0:
                batch_inserted += 1
                print(f"✅ Inserted: {subreddit.display_name} | Size: {get_db_size_mb(DB_FILE):.2f} MB | DB: {DB_FILE}")
            else:
                batch_skipped += 1
                print(f"⏭️ Skipped (duplicate): {subreddit.display_name}")

            last_fullname = subreddit.fullname

        except Exception as e:
            print(f"❌ Error: {e}")

    conn.commit()

    total_inserted += batch_inserted
    total_skipped += batch_skipped

    # Rotate DB if size exceeded
    if get_db_size_mb(DB_FILE) >= MAX_DB_SIZE_MB:
        print(f"\n⚠️ Database {DB_FILE} exceeded {MAX_DB_SIZE_MB}MB. Rotating...\n")
        conn.close()
        db_index += 1
        DB_FILE = get_db_filename(db_index)
        print(f"📦 Switching to new DB: {DB_FILE}")
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS subreddits (...)''')  # You can reuse table creation here
        conn.commit()

    if not last_fullname:
        print("🚫 No more new subreddits. Stopping early.")
        break

    time.sleep(40)

conn.close()

# Create ready-to-commit flag
with open("ready-to-commit.txt", "w") as f:
    f.write("ready")

print(f"\n🚀 DONE! Total Inserted: {total_inserted}, Total Skipped: {total_skipped}")
