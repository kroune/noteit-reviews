#!/usr/bin/env python3
"""Scrape all obtainable Google Play reviews for me.bukovitz.noteit.

Parallel version: worker threads iterate over locale x sort x rating-filter
combinations, paginate with continuation tokens until exhaustion, dedupe by
reviewId (shared set + lock). Checkpoints to JSONL + state file.
"""
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from google_play_scraper import Sort, reviews

APP_ID = "me.bukovitz.noteit"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(OUT_DIR, "data")
RAW_PATH = os.path.join(DATA_DIR, "reviews_raw.jsonl")
STATE_PATH = os.path.join(DATA_DIR, "scrape_state.json")
WORKERS = 8

LOCALES = [
    ("en", "us"), ("en", "gb"), ("en", "ca"), ("en", "au"),
    ("ru", "ru"), ("uk", "ua"), ("de", "de"), ("fr", "fr"),
    ("es", "es"), ("es", "mx"), ("pt", "br"), ("it", "it"),
    ("pl", "pl"), ("tr", "tr"), ("hi", "in"), ("id", "id"),
    ("ja", "jp"), ("ko", "kr"), ("nl", "nl"), ("ar", "sa"),
]
SORTS = [Sort.NEWEST, Sort.MOST_RELEVANT]
SCORES = [None, 1, 2, 3, 4, 5]

os.makedirs(DATA_DIR, exist_ok=True)

lock = threading.Lock()
done_keys = set()
seen_ids = set()
if os.path.exists(STATE_PATH):
    with open(STATE_PATH) as f:
        done_keys = set(json.load(f).get("done", []))
if os.path.exists(RAW_PATH):
    with open(RAW_PATH) as f:
        for line in f:
            try:
                seen_ids.add(json.loads(line)["reviewId"])
            except Exception:
                pass

out = open(RAW_PATH, "a", encoding="utf-8")
started = time.time()


def fetch_batch(lang, country, sort, score, token, tries=3):
    for attempt in range(tries):
        try:
            return reviews(
                APP_ID, lang=lang, country=country, sort=sort, count=200,
                filter_score_with=score, continuation_token=token,
            )
        except Exception as e:
            if attempt == tries - 1:
                print(f"[{lang}-{country}|{sort.name}|{score}] giving up: {e}", flush=True)
                return [], None
            time.sleep(5 * (attempt + 1))


def work(lang, country, sort, score):
    key = f"{lang}-{country}|{sort.name}|{score}"
    token = None
    new_here = 0
    while True:
        result, token = fetch_batch(lang, country, sort, score, token)
        with lock:
            for r in result:
                rid = r["reviewId"]
                if rid in seen_ids:
                    continue
                seen_ids.add(rid)
                rec = dict(r)
                rec["at"] = rec["at"].isoformat()
                if rec.get("repliedAt"):
                    rec["repliedAt"] = rec["repliedAt"].isoformat()
                rec["_lang"] = lang
                rec["_country"] = country
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                new_here += 1
            out.flush()
        if token is None or not result:
            break
    with lock:
        done_keys.add(key)
        with open(STATE_PATH, "w") as f:
            json.dump({"done": sorted(done_keys)}, f)
        total = len(seen_ids)
    print(f"[{key}] done new={new_here} total={total}", flush=True)


tasks = []
for lang, country in LOCALES:
    for sort in SORTS:
        for score in SCORES:
            key = f"{lang}-{country}|{sort.name}|{score}"
            if key not in done_keys:
                tasks.append((lang, country, sort, score))

print(f"pending combinations: {len(tasks)}, already have {len(seen_ids)} unique reviews", flush=True)
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(lambda t: work(*t), tasks))

out.close()
print(f"DONE. unique reviews={len(seen_ids)} elapsed={time.time()-started:.0f}s")
