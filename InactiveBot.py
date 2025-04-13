import praw
import sqlite3
import time
import datetime
import gc
import os
import sys

# Reddit authentication
reddit = praw.Reddit(
    client_id='6pDYJFzCd_n3EVpzk5MlvQ',
    client_secret='yYFvV0ieN9ixcWZ43C3ZJvp0SjxqBQ',
    username='yourpersonalhuman',
    password='Mudar!@#12',
    user_agent='subreddit-scraper-script'
)

# Create/connect to database
conn = sqlite3.connect('subreddits.db')
c = conn.cursor()

# Create table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS subreddits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    title TEXT,
    subscribers INTEGER,
    created_utc INTEGER,
    over18 BOOLEAN,
    last_post_utc INTEGER
)''')
conn.commit()

# Load last token from DB
def get_last_token():
    c.execute("SELECT name FROM subreddits ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    return row[0] if row else None

after = get_last_token()
print(f"Resuming from: {after}")

# Track runtime
start_time = time.time()
max_runtime_seconds = 5 * 3600 + 45 * 60  # 5 hours 45 minutes

# Buffer for batch inserts
batch = []
BATCH_SIZE = 1000
processed_count = 0

def save_batch():
    global batch
    if not batch:
        return
    try:
        c.executemany('''INSERT OR IGNORE INTO subreddits (
            name, title, subscribers, created_utc, over18, last_post_utc
        ) VALUES (?, ?, ?, ?, ?, ?)''', batch)
        conn.commit()
        print(f"Inserted batch of {len(batch)} subreddits.")
    except Exception as e:
        print(f"Error inserting batch: {e}")
    finally:
        batch = []
        gc.collect()  # Free memory

while True:
    if time.time() - start_time > max_runtime_seconds:
        print("⏰ Max runtime reached. Exiting.")
        break

    try:
        subreddits = list(reddit.subreddits.default(limit=100, params={"after": after}))
        if not subreddits:
            print("✅ No more subreddits to process.")
            break

        for subreddit in subreddits:
            try:
                name = subreddit.display_name
                title = subreddit.title
                subscribers = subreddit.subscribers or 0
                created_utc = int(subreddit.created_utc)
                over18 = subreddit.over18

                # Fetch latest post timestamp
                posts = list(subreddit.new(limit=1))
                last_post_utc = int(posts[0].created_utc) if posts else 0

                batch.append((name, title, subscribers, created_utc, over18, last_post_utc))
                processed_count += 1

                if processed_count % BATCH_SIZE == 0:
                    save_batch()

                after = name  # Save token for next page

            except Exception as e:
                print(f"⚠️ Error with subreddit '{subreddit.display_name}': {e}")
                continue

        print(f"✅ Processed 100 subreddits, sleeping for 15 seconds...")
        time.sleep(15)

    except Exception as e:
        print(f"🚨 Unexpected error: {e}")
        time.sleep(30)

# Final batch flush
save_batch()
conn.close()
print("🎉 Scraping complete.")
