#!/usr/bin/env python3
"""Build static GitHub Pages site from scraped reviews JSONL.

Outputs into docs/:
  - data/meta.json      app metadata + aggregate stats
  - data/reviews.json   compact review array
  - index.html          dashboard (filters, charts, table)
"""
import json
import os
from collections import Counter

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(OUT_DIR, "data")
DOCS = os.path.join(OUT_DIR, "docs")

reviews = []
with open(os.path.join(DATA_DIR, "reviews_raw.jsonl"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            reviews.append(json.loads(line))

reviews.sort(key=lambda r: r["at"], reverse=True)

# compact representation, keep all obtainable meta
compact = [
    {
        "id": r["reviewId"],
        "user": r.get("userName"),
        "avatar": r.get("userImage"),
        "text": r.get("content"),
        "score": r.get("score"),
        "likes": r.get("thumbsUpCount", 0),
        "version": r.get("reviewCreatedVersion"),
        "at": r.get("at"),
        "reply": r.get("replyContent"),
        "repliedAt": r.get("repliedAt"),
        "lang": r.get("_lang"),
        "country": r.get("_country"),
    }
    for r in reviews
]

score_dist = Counter(r["score"] for r in compact)
versions = Counter(r["version"] or "unknown" for r in compact)
langs = Counter(f'{r["lang"]}-{r["country"]}' for r in compact)
by_month = Counter(r["at"][:7] for r in compact if r.get("at"))
replied = sum(1 for r in compact if r.get("reply"))

meta = {
    "appId": "me.bukovitz.noteit",
    "title": "noteit widget - by sendit",
    "totalReviews": len(compact),
    "avgScore": round(sum(r["score"] for r in compact) / max(len(compact), 1), 3),
    "scoreDist": {str(k): score_dist.get(k, 0) for k in range(1, 6)},
    "byMonth": dict(sorted(by_month.items())),
    "topVersions": versions.most_common(20),
    "locales": langs.most_common(),
    "repliedCount": replied,
    "scrapedAt": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
}

os.makedirs(os.path.join(DOCS, "data"), exist_ok=True)
with open(os.path.join(DOCS, "data", "reviews.json"), "w", encoding="utf-8") as f:
    json.dump(compact, f, ensure_ascii=False, separators=(",", ":"))
with open(os.path.join(DOCS, "data", "meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

size = os.path.getsize(os.path.join(DOCS, "data", "reviews.json"))
print(f"reviews: {len(compact)}, reviews.json: {size/1024/1024:.1f} MB")
