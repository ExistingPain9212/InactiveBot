import praw
import requests
import sqlite3
import datetime
import time

# Reddit Auth (for access token only)
reddit = praw.Reddit(
    client_id="6pDYJFzCd_n3EVpzk5MlvQ",
    client_secret="yYFvV0ieN9ixcWZ43C3ZJvp0SjxqBQ",
    user_agent="subreddit_scraper by u/yourpersonalhuman",
    username="yourpersonalhuman",
    password="Mudar!@#12"
)

# Get OAuth2 access token from PRAW
token = reddit.auth.authorizer.access_token
headers = {
    "Authorization": f"bearer {token}",
    "User-Agent": "subreddit_scraper by u/yourpersonalhuman"
}

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

def get_after_token():
    c.execute("SELECT after_token FROM subreddits ORDER BY sr_no DESC LIMIT 1")
    row = c.fetchone()
    return row[0] if row else None

start_time = time.time()
max_duration = 5 * 60  # 5 minutes
total_count = 0

while time.time() - start_time < max_duration:
    after = get_after_token()
    url = "https://oauth.reddit.com/subreddits/new"
    params = {"limit": 100}
    if after:
        params["after"] = f"t5_{after.lower()}"  # Subreddit fullname format

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"⚠️ Failed to fetch subreddits: {response.status_code} - {response.text}")
        break

    data = response.json()
    children = data.get("data", {}).get("children", [])
    after_token = data.get("data", {}).get("after", None)

    batch_count = 0
    for child in children:
        s = child["data"]
        try:
            c.execute('''
                INSERT OR IGNORE INTO subreddits (
                    name, title, description, public_description, subscribers, active_user_count,
                    lang, type, url, created_utc, last_checked, over18, quarantine, restricted,
                    advertiser_category, submission_type, allow_videos, allow_images, allow_poll,
                    spoilers_enabled, comment_score_hide_mins, wiki_enabled, after_token
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                s.get("display_name", ""),
                s.get("title", ""),
                s.get("description", ""),
                s.get("public_description", ""),
                s.get("subscribers", 0),
                s.get("active_user_count", 0),
                s.get("lang", ""),
                s.get("subreddit_type", ""),
                s.get("url", ""),
                float(s.get("created_utc", 0)),
                datetime.datetime.utcnow().isoformat(),
                int(s.get("over18", False)),
                int(s.get("quarantine", False)),
                int(s.get("restrict_posting", False)),
                s.get("advertiser_category", ""),
                s.get("submission_type", ""),
                int(s.get("allow_videos", False)),
                int(s.get("allow_images", False)),
                int(s.get("allow_poll", False)),
                int(s.get("spoilers_enabled", False)),
                int(s.get("comment_score_hide_mins", 0)),
                int(s.get("wiki_enabled", False)),
                s.get("name", "")[3:] if s.get("name", "").startswith("t5_") else s.get("name", "")  # just the ID
            ))
            batch_count += 1
        except Exception as e:
            print(f"⚠️ Error saving subreddit {s.get('display_name')}: {e}")

    conn.commit()
    total_count += batch_count
    print(f"✅ Scraped and saved {batch_count} subreddits in this batch.")

    if not after_token:
        print("🚫 No more pages to fetch.")
        break

    time.sleep(15)

conn.close()

# Write commit marker
with open("ready-to-commit.txt", "w") as f:
    f.write("ready")

print(f"✅ Total subreddits scraped and saved: {total_count}")
