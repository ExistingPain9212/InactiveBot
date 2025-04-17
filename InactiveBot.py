import praw
import sqlite3
import datetime
import time

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
        posts_last_30_days INTEGER,
        last_post_utc REAL,
        after_token TEXT
    )
''')
conn.commit()

# Get the last after_token (actual Reddit fullname, not display_name)
def get_after_token():
    c.execute("SELECT after_token FROM subreddits ORDER BY sr_no DESC LIMIT 1")
    row = c.fetchone()
    return row[0] if row else None

start_time = time.time()
max_duration = 59 * 60  # Run for 59 minutes for testing
total_inserted = 0
total_skipped = 0

while time.time() - start_time < max_duration:
    after = get_after_token()
    print(f"\n⏩ Resuming from after_token: {after or 'START'}\n")

    batch_inserted = 0
    batch_skipped = 0
    last_fullname = None

    for subreddit in reddit.subreddits.new(limit=100, params={"after": after}):
        print(f"🔍 Fetched: {subreddit.display_name}")

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
                None,  # posts_last_30_days placeholder
                None,  # last_post_utc placeholder
                subreddit.fullname  # after_token stays last
            ))

            if c.rowcount > 0:
                print(f"✅ Inserted: {subreddit.display_name}")
                batch_inserted += 1
            else:
                print(f"⏭️ Skipped (duplicate): {subreddit.display_name}")
                batch_skipped += 1

            last_fullname = subreddit.fullname

        except Exception as e:
            print(f"❌ Error saving {subreddit.display_name}: {e}")

    conn.commit()

    print(f"\n📦 Batch Summary: Inserted {batch_inserted}, Skipped {batch_skipped}\n")
    total_inserted += batch_inserted
    total_skipped += batch_skipped

    if not last_fullname:
        print("🚫 No more new subreddits fetched. Stopping early.")
        break

    time.sleep(20)

conn.close()

# Write commit marker
with open("ready-to-commit.txt", "w") as f:
    f.write("ready")

print(f"\n🚀 DONE! Total Inserted: {total_inserted}, Total Skipped (duplicates): {total_skipped}")
