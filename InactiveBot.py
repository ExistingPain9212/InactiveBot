import requests
import requests.auth
import sqlite3
import datetime
import time
import os

# Credentials (use env vars or hardcode as before)
CLIENT_ID     = os.environ.get("CLIENT_ID", "6pDYJFzCd_n3EVpzk5MlvQ")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "yYFvV0ieN9ixcWZ43C3ZJvp0SjxqBQ")
USERNAME      = os.environ.get("USERNAME", "yourpersonalhuman")
PASSWORD      = os.environ.get("PASSWORD", "Mudar!@#12")
USER_AGENT    = os.environ.get("USER_AGENT", "subreddit_scraper by u/yourpersonalhuman")

# 1) Get OAuth token via password grant
auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
data = {
    "grant_type": "password",
    "username": USERNAME,
    "password": PASSWORD
}
headers = {"User-Agent": USER_AGENT}
res = requests.post("https://www.reddit.com/api/v1/access_token",
                    auth=auth, data=data, headers=headers)
res.raise_for_status()
token = res.json()["access_token"]
headers["Authorization"] = f"bearer {token}"

# 2) Prepare DB
conn = sqlite3.connect("subreddits.db")
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

# 3) Loop for 5 minutes, 100 at a time
start = time.time()
max_duration = 5 * 60
total = 0

while time.time() - start < max_duration:
    after = get_after_token()
    params = {"limit": 100}
    if after:
        # Reddit fullnames for subs are t5_<id>
        params["after"] = f"t5_{after}"

    resp = requests.get("https://oauth.reddit.com/subreddits/new",
                        headers=headers, params=params)
    if resp.status_code != 200:
        print("⚠️ fetch failed:", resp.status_code, resp.text)
        break

    page = resp.json()["data"]
    subs = page.get("children", [])
    next_after = page.get("after", None)

    batch_count = 0
    for entry in subs:
        s = entry["data"]
        try:
            c.execute('''
INSERT OR IGNORE INTO subreddits (
 name, title, description, public_description, subscribers, active_user_count,
 lang, type, url, created_utc, last_checked, over18, quarantine, restricted,
 advertiser_category, submission_type, allow_videos, allow_images, allow_poll,
 spoilers_enabled, comment_score_hide_mins, wiki_enabled, after_token
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    s.get("display_name",""),
    s.get("title",""),
    s.get("description","") or "",
    s.get("public_description","") or "",
    s.get("subscribers",0),
    s.get("active_user_count",0),
    s.get("lang",""),
    s.get("subreddit_type",""),
    s.get("url",""),
    float(s.get("created_utc",0)),
    datetime.datetime.utcnow().isoformat(),
    int(s.get("over18",False)),
    int(s.get("quarantine",False)),
    int(s.get("restrict_posting",False)),
    s.get("advertiser_category",""),
    s.get("submission_type",""),
    int(s.get("allow_videos",False)),
    int(s.get("allow_images",False)),
    int(s.get("allow_poll",False)),
    int(s.get("spoilers_enabled",False)),
    int(s.get("comment_score_hide_mins",0) or 0),
    int(s.get("wiki_enabled",False)),
    s.get("name","")[3:] if s.get("name","").startswith("t5_") else ""
))
            batch_count += 1
        except Exception as e:
            print(f"⚠️ Error saving {s.get('display_name')}: {e}")

    conn.commit()
    total += batch_count
    print(f"✅ Batch: {batch_count} saved; total so far: {total}")

    if not next_after:
        print("🚫 No more pages.")
        break

    time.sleep(15)

conn.close()

# 4) Signal commit
with open("ready-to-commit.txt","w") as f:
    f.write("ready")

print(f"🎉 Done: {total} subreddits saved.")
