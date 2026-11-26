"""Pick this week's approved entry, or publish the rendered Reel to Facebook + Instagram.

usage:
  python3 publish.py pick <out.json>          -> writes this week's entry
  python3 publish.py post <entry.json> <video_url>
env: META_TOKEN (system-user token), WEEK_INDEX (optional override)
"""
import json, os, sys, time, datetime, urllib.request, urllib.parse

GRAPH = "https://graph.facebook.com/v21.0"
START = datetime.date(2026, 11, 26)          # week 1 = Thursday 26 Nov 2026
HASHTAGS = "#OneExtraMat #Jummah #JummahMubarak #FridayPrayer #Muslim"


def api(method, path, **params):
    data = urllib.parse.urlencode(params).encode()
    url = f"{GRAPH}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Graph API error on {path}: {e.read().decode()}")


def pick(out):
    bank = [e for e in json.load(open("content_bank.json")) if e.get("status") == "Approved"]
    idx = os.environ.get("WEEK_INDEX")
    if not idx:
        today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=4))).date()
        idx = max(0, (today - START).days // 7)
    entry = bank[int(idx) % len(bank)]
    json.dump(entry, open(out, "w"), ensure_ascii=False)
    print(f"Week index {idx}: {entry['reference']}")


def caption(e):
    return (f"{e['cta']}\n\n“{e['translation']}”\n— {e['reference']}\n\n"
            f"Take one extra prayer mat to Jummah, so a fellow worshipper can pray.\n\n{HASHTAGS}")


def post(entry_file, video_url):
    e = json.load(open(entry_file))
    token = os.environ["META_TOKEN"]
    pages = api("GET", "me/accounts", access_token=token, fields="id,name,access_token,instagram_business_account")["data"]
    page = next(p for p in pages if "One Extra Mat" in p["name"])
    ptoken = page["access_token"]
    cap = caption(e)

    fb = api("POST", f"{page['id']}/videos", access_token=ptoken, file_url=video_url, description=cap)
    print("Facebook video posted:", fb.get("id"))

    ig_id = (page.get("instagram_business_account") or {}).get("id")
    if not ig_id:
        ig_id = api("GET", page["id"], access_token=ptoken, fields="instagram_business_account")["instagram_business_account"]["id"]
    c = api("POST", f"{ig_id}/media", access_token=ptoken, media_type="REELS",
            video_url=video_url, caption=cap, share_to_feed="true")["id"]
    for _ in range(60):                       # up to ~10 minutes of processing
        s = api("GET", c, access_token=ptoken, fields="status_code,status")
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            sys.exit(f"Instagram processing failed: {s}")
        time.sleep(10)
    pub = api("POST", f"{ig_id}/media_publish", access_token=ptoken, creation_id=c)
    print("Instagram Reel published:", pub.get("id"))


if __name__ == "__main__":
    if sys.argv[1] == "pick":
        pick(sys.argv[2])
    else:
        post(sys.argv[2], sys.argv[3])
