import praw
import sqlite3
import time
from datetime import datetime, timedelta

# Full Reddit authentication
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

# Create table if not exists with new fields
cursor.execute('''
CREATE TABLE IF NOT EXISTS subreddits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    subscribers INTEGER,
    created_utc REAL,
    last_checked TEXT,
    over18 INTEGER,
    quarantine INTEGER,
    restricted INTEGER,
    after_token TEXT,
    last_post_utc REAL,
    posts_last_30_days INTEGER
)
''')

# Get last token (if any)
cursor.execute("SELECT after_token FROM subreddits WHERE after_token IS NOT NULL ORDER BY id DESC LIMIT 1")
row = cursor.fetchone()
after = row[0] if row else None

# Display last added subreddit
cursor.execute("SELECT name FROM subreddits ORDER BY id DESC LIMIT 1")
last_added = cursor.fetchone()
if last_added:
    print(f"🔁 Last subreddit added: r/{last_added[0]}")
else:
    print("🚀 Starting fresh!")

fetched = 0
new_count = 0
request_count = 0
start_time = time.time()
max_duration = 5.75 * 60 * 60  # 5 hours 45 minutes

while True:
    # Check time limit
    if time.time() - start_time > max_duration:
        print("⏰ Time limit reached. Stopping gracefully to save progress.")
        break

    try:
        subreddits = reddit.get("/subreddits/new", params={"limit": 100, "after": after})
        subreddits = list(subreddits)

        if not subreddits:
            print("✅ No more subreddits to fetch.")
            break

        for subreddit in subreddits:
            try:
                name = subreddit.display_name
                subscribers = subreddit.subscribers
                created_utc = subreddit.created_utc
                last_checked = time.strftime('%Y-%m-%d %H:%M:%S')
                over18 = int(subreddit.over18)
                quarantine = int(subreddit.quarantine)
                restricted = int(subreddit.subreddit_type != 'public')
                after_token = subreddit.fullname

                # Get latest post timestamp and count of posts in last 30 days
                last_post_utc = None
                posts_last_30_days = 0

                try:
                    posts = list(reddit.subreddit(name).new(limit=100))
                    if posts:
                        last_post_utc = posts[0].created_utc
                        thirty_days_ago = time.time() - 30 * 24 * 60 * 60
                        posts_last_30_days = sum(1 for post in posts if post.created_utc >= thirty_days_ago)
                except Exception as e:
                    print(f"⚠️ Could not fetch posts for r/{name}: {e}")

                cursor.execute('''
                    INSERT OR IGNORE INTO subreddits 
                    (name, subscribers, created_utc, last_checked, over18, quarantine, restricted, after_token, last_post_utc, posts_last_30_days)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, subscribers, created_utc, last_checked, over18, quarantine, restricted, after_token, last_post_utc, posts_last_30_days))

                if cursor.rowcount:
                    print(f"✅ Added: r/{name}")
                    new_count += 1

                fetched += 1
                request_count += 1
                after = subreddit.fullname
            except Exception as e:
                print(f"❌ Error with r/{subreddit.display_name}: {e}")

        if request_count >= 100:
            print("⏸️ Sleeping for 40 seconds to respect API limits...")
            time.sleep(40)
            request_count = 0

    except Exception as e:
        print(f"❌ Error fetching subreddit page: {e}")
        break

# Save and close
conn.commit()
conn.close()
print(f"✅ Done! Total new entries added: {new_count}")
