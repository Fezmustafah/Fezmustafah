#!/usr/bin/env python3
"""
fetch_contributions.py — scrape a public GitHub contribution calendar.

No API token, no GraphQL. GitHub serves the calendar as public HTML at
  https://github.com/users/<username>/contributions
(the same fragment the profile page uses). We fetch it, parse the day cells,
and write data/contributions.json with the raw days plus derived stats.

    python scripts/fetch_contributions.py
    python scripts/fetch_contributions.py --user someoneelse
"""
import os
import re
import sys
import json
import argparse
from collections import defaultdict
from datetime import date, datetime, timezone

import requests
from bs4 import BeautifulSoup

DEFAULT_USER = "fezmustafah"
OUT = os.path.join("data", "contributions.json")
COUNT_RE = re.compile(r"^\s*([\d,]+|No)\b", re.IGNORECASE)


def fetch_html(user):
    url = f"https://github.com/users/{user}/contributions"
    headers = {
        "User-Agent": "Mozilla/5.0 (profile-art contributions fetcher)",
        "Accept": "text/html",
        "X-Requested-With": "XMLHttpRequest",
    }
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text


def parse_count(text):
    if not text:
        return 0
    m = COUNT_RE.match(text.strip())
    if not m:
        return 0
    tok = m.group(1)
    if tok.lower() == "no":
        return 0
    return int(tok.replace(",", ""))


def parse_days(html):
    soup = BeautifulSoup(html, "html.parser")

    # map tooltip target id -> tooltip text ("N contributions on ...")
    tips = {}
    for tt in soup.find_all("tool-tip"):
        tid = tt.get("for")
        if tid:
            tips[tid] = tt.get_text(" ", strip=True)

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        d = td.get("data-date")
        if not d:
            continue
        level = int(td.get("data-level") or 0)
        # count: prefer explicit data-count, else the linked tooltip text
        count = None
        if td.has_attr("data-count"):
            try:
                count = int(td["data-count"])
            except ValueError:
                count = None
        if count is None:
            count = parse_count(tips.get(td.get("id"), ""))
        days.append({"date": d, "count": count, "level": level})

    days.sort(key=lambda x: x["date"])
    return days


def derive_stats(days):
    total = sum(d["count"] for d in days)

    # longest streak
    longest = cur = 0
    for d in days:
        if d["count"] > 0:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0

    # current streak: walk back from the end; today with 0 doesn't break it
    current = 0
    today = date.today()
    for i in range(len(days) - 1, -1, -1):
        c = days[i]["count"]
        dd = datetime.strptime(days[i]["date"], "%Y-%m-%d").date()
        if c > 0:
            current += 1
        else:
            # allow a trailing zero only if it's today (day not finished)
            if dd == today and current == 0:
                continue
            break

    best = max(days, key=lambda x: x["count"], default={"date": None, "count": 0})

    monthly = defaultdict(int)
    for d in days:
        monthly[d["date"][:7]] += d["count"]

    first = days[0]["date"] if days else None
    last = days[-1]["date"] if days else None
    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": dict(sorted(monthly.items())),
        "range": {"from": first, "to": last},
        "weeks": (len(days) + 6) // 7,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("GH_USER", DEFAULT_USER))
    args = ap.parse_args()

    html = fetch_html(args.user)
    days = parse_days(html)
    if not days:
        sys.exit("[fetch] parsed 0 days — GitHub markup may have changed, "
                 "or the username is wrong / private.")

    payload = {
        "user": args.user,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "days": days,
        "stats": derive_stats(days),
    }

    os.makedirs("data", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    s = payload["stats"]
    print(f"[fetch] {args.user}: {len(days)} days, {s['total']} contributions, "
          f"streak {s['current_streak']} (max {s['longest_streak']}) -> {OUT}")


if __name__ == "__main__":
    main()
