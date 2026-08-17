# -*- coding: utf-8 -*-
"""PromptOS Inbox; send per-account confirmations after a filing run.

The standing final step of every processing run. Each account that submitted
something gets a summary of what was filed and where.

Idempotent: it only sends for items that are processed and not yet confirmed,
then marks them confirmed. Running it twice sends nothing twice.

    python confirm.py
"""

import datetime
import json
import os
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE_DIR, "config.json")
INBOX = os.path.join(BASE_DIR, "inbox.json")
MAX_LINES = 25

cfg = json.load(open(CONFIG, encoding="utf-8"))
TOKEN = cfg["token"]
OWNERS = cfg.get("owners", [])
BASE_NAME = cfg.get("base_name", "PromptOS")

raw = json.load(open(INBOX, encoding="utf-8"))
items = raw if isinstance(raw, list) else raw.get("items", raw.get("messages", []))


def send(chat_id, text):
    data = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    ).encode()
    req = urllib.request.Request(
        "https://api.telegram.org/bot%s/sendMessage" % TOKEN, data=data
    )
    try:
        return json.load(urllib.request.urlopen(req, timeout=20)).get("ok", False)
    except Exception:
        return False


# Group everything filed but not yet acknowledged, by the account that sent it.
by_chat = {}
for x in items:
    if not isinstance(x, dict):
        continue
    if x.get("processed") and not x.get("confirmed"):
        filed = x.get("filed_as")
        if filed and filed != "command":
            by_chat.setdefault(x.get("chat_id"), []).append((x, filed))

today = datetime.datetime.now().strftime("%Y-%m-%d")
report = []

for cid in OWNERS:
    entries = by_chat.get(cid, [])

    if not entries:
        ok = send(cid, "%s: all caught up, nothing pending. (%s)" % (BASE_NAME, today))
        report.append("%s: %s (no pending)" % (cid, "sent" if ok else "FAILED"))
        continue

    seen, lines = set(), []
    for _, filed in entries:
        if filed not in seen:
            seen.add(filed)
            lines.append("- " + filed)
    more = "" if len(lines) <= MAX_LINES else "\n(+%d more)" % (len(lines) - MAX_LINES)

    ok = send(
        cid,
        "%s (%s)\nFiled from your submissions:\n%s%s\n\n"
        "Send /cleanup to tidy the processed messages when ready."
        % (BASE_NAME, today, "\n".join(lines[:MAX_LINES]), more),
    )
    report.append("%s: %s (%d items)" % (cid, "sent" if ok else "FAILED", len(entries)))

    if ok:
        for x, _ in entries:
            x["confirmed"] = True
            x["confirmed_at"] = today

json.dump(raw, open(INBOX, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n".join(report))
