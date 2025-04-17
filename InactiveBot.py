import praw
import sqlite3
import time
import datetime

# Full Reddit authentication (not read-only)
reddit = praw.Reddit(
    client_id="6pDYJFzCd_n3EVpzk5MlvQ",
    client_secret="yYFvV0ieN9ixcWZ43C3ZJvp0SjxqBQ",
    user_agent="subreddit_scraper by u/YOUR_USERNAME",
    username="yourpersonalhuman",
    password="Mudar!@#12"
)

# Connect to SQLite
conn = sqlite3.connect("subreddits.db")
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''
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

# Helper function to handle None values and safely convert them to integers or strings
def safe_int(value, default=0):
    """Convert value to int, return default if value is None."""
    return int(value) if value is not None else default

def safe_str(value, default=""):
    """Convert value to string, return default if value is None."""
    return str(value) if value is not None else default

# Start time (in seconds) to limit script to 5 minutes
start_time = time.time()
time_limit = 5 * 60  # 5 minutes in seconds

# Resume from last token
cursor.execute("SELECT after_token FROM subreddits WHERE after_token IS NOT NULL ORDER BY sr_no DESC LIMIT 1")
row = cursor.fetchone()
after = row[0] if row else None

cursor.execute("SELECT name FROM subreddits ORDER BY sr_no DESC LIMIT 1")
last_added = cursor.fetchone()
if last_added:
    print(f"🔁 Last subreddit added: r/{last_added[0]}")
else:
    print("🚀 Starting fresh!")

fetched = 0
new_count = 0
request_count = 0

while True:
    # Check if the script has run for more than 5 minutes
    elapsed_time = time.time() - start_time
    if elapsed_time > time_limit:
        print("⏰ Time limit reached! Stopping the script.")
        break

    try:
        subreddits = list(reddit.get("/subreddits/new", params={"limit": 100, "after": after}))
        if not subreddits:
            print("✅ No more subreddits to fetch.")
            break

        for subreddit in subreddits:
            try:
                # Collect all the required values, ensuring that None is handled properly
                name = safe_str(subreddit.display_name)
                title = safe_str(subreddit.title)
                description = safe_str(subreddit.description)
                public_description = safe_str(subreddit.public_description)
                subscribers = safe_int(subreddit.subscribers)
                active_user_count = safe_int(subreddit.accounts_active)
                lang = safe_str(subreddit.lang)
                type_ = safe_str(subreddit.subreddit_type)
                url = safe_str(subreddit.url)
                created_utc = safe_int(subreddit.created_utc)
                last_checked = datetime.datetime.utcnow().isoformat()
                over18 = safe_int(subreddit.over18)
                quarantine = safe_int(subreddit.quarantine)
                restricted = safe_int(subreddit.restrict_posting)
                advertiser_category = safe_str(subreddit.advertiser_category)
                submission_type = safe_str(subreddit.submission_type)
                allow_videos = safe_int(subreddit.allow_videos)
                allow_images = safe_int(subreddit.allow_images)
                allow_poll = safe_int(subreddit.allow_polls)
                spoilers_enabled = safe_int(subreddit.spoilers_enabled)
                comment_score_hide_mins = safe_int(subreddit.comment_score_hide_mins, default=0)
                wiki_enabled = safe_int(subreddit.wiki_enabled)
                after_token = safe_str(subreddit.fullname)  # Ensure this is safely assigned

                # Insert data into SQLite
                cursor.execute('''
                    INSERT OR IGNORE INTO subreddits 
                    (name, title, description, public_description, subscribers, active_user_count,
                     lang, type, url, created_utc, last_checked, over18, quarantine, restricted,
                     advertiser_category, submission_type, allow_videos, allow_images, allow_poll,
                     spoilers_enabled, comment_score_hide_mins, wiki_enabled, after_token)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    name, title, description, public_description, subscribers, active_user_count,
                    lang, type_, url, created_utc, last_checked, over18, quarantine, restricted,
                    advertiser_category, submission_type, allow_videos, allow_images, allow_poll,
                    spoilers_enabled, comment_score_hide_mins, wiki_enabled, after_token
                ))

                if cursor.rowcount:
                    print(f"✅ Added: r/{name}")
                    new_count += 1

                fetched += 1
                request_count += 1
                after = subreddit.fullname
            except Exception as e:
                print(f"❌ Error with r/{subreddit.display_name}: {e}")

        if request_count >= 100:
            print("⏸️ Sleeping for 15 seconds...")
            time.sleep(15)
            request_count = 0

    except Exception as e:
        print(f"❌ Error fetching subreddit page: {e}")
        break

conn.commit()
conn.close()
print(f"✅ Done! Total new entries added: {new_count}")
