import praw
import sqlite3
import time

# --- Reddit Auth ---
reddit = praw.Reddit(
    client_id="6pDYJFzCd_n3EVpzk5MlvQ",
    client_secret="yYFvV0ieN9ixcWZ43C3ZJvp0SjxqBQ",
    user_agent="subreddit_scraper by u/YOUR_USERNAME",
    username="yourpersonalhuman",
    password="Mudar!@#12"
)

# --- DB Setup ---
conn = sqlite3.connect("subreddits.db")
cursor = conn.cursor()

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
    after_token TEXT
)
''')

# --- Get Resume Token ---
cursor.execute("SELECT after_token FROM subreddits WHERE after_token IS NOT NULL ORDER BY id DESC LIMIT 1")
row = cursor.fetchone()
after = row[0] if row else None

if after:
    print(f"🔁 Resuming from token: {after}")
else:
    print("🚀 Starting fresh!")

fetched = 0
new_count = 0
request_count = 0
start_time = time.time()
max_runtime = 5 * 3600 + 45 * 60  # 5 hours 45 minutes = 20,700 seconds

# --- Scraping Loop ---
while True:
    if time.time() - start_time >= max_runtime:
        print("⏰ Max runtime reached (5h45m). Stopping gracefully.")
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

                cursor.execute('''
                    INSERT OR IGNORE INTO subreddits 
                    (name, subscribers, created_utc, last_checked, over18, quarantine, restricted, after_token)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, subscribers, created_utc, last_checked, over18, quarantine, restricted, after_token))

                if cursor.rowcount:
                    print(f"✅ Added: r/{name}")
                    new_count += 1

                fetched += 1
                request_count += 1
                after = subreddit.fullname

            except Exception as e:
                print(f"❌ Error with r/{subreddit.display_name}: {e}")

        if request_count >= 100:
            print("⏸️ Sleeping for 15 seconds to respect API limits...")
            time.sleep(15)
            request_count = 0

    except Exception as e:
        print(f"❌ Error fetching subreddit page: {e}")
        break

# --- Save and Close ---
conn.commit()
conn.close()
print(f"✅ Done! Total new entries added: {new_count}")
