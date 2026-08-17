# -*- coding: utf-8 -*-
"""PromptOS Inbox; Telegram collector daemon.

Captures everything an approved account sends into inbox.json. The Telegram Bot
API cannot read history, and it keeps unfetched updates for roughly 24 hours, so
this has to run continuously for capture to be reliable.

Standard library only. No pip install, no dependencies, no build step.

    python bot.py

Configuration lives in config.json beside this file. Start from
config.example.json. Never commit config.json; it holds the bot token.
"""

import json
import os
import time
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE_DIR, "config.json")
INBOX = os.path.join(BASE_DIR, "inbox.json")
LOG = os.path.join(BASE_DIR, "bot.log")


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save(path, data):
    # Write then rename: a crash mid-write must never truncate the queue.
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + str(msg) + "\n")


cfg_boot = load(CONFIG, {})
TOKEN = cfg_boot.get("token", "")
BASE_NAME = cfg_boot.get("base_name", "PromptOS")
API = "https://api.telegram.org/bot" + TOKEN + "/"

if not TOKEN:
    raise SystemExit(
        "No bot token. Copy config.example.json to config.json and add the token "
        "from @BotFather."
    )


def api(method, **params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(API + method, data=data)
    try:
        with urllib.request.urlopen(req, timeout=70) as r:
            return json.load(r)
    except Exception as e:
        log("api %s error: %s" % (method, e))
        return {"ok": False}


HELP = (
    "\U0001F4E5 %s Inbox\n"
    "• Send links or notes from any device; they queue here\n"
    "• Mention '%s' in a message to flag a processing run\n"
    "• /cleanup deletes everything already filed\n"
    "• Your agent processes the queue on request or on schedule"
) % (BASE_NAME, BASE_NAME)


def handle_cleanup(chat_id, cmd_mid):
    """Delete only what has already been filed, and only on the user's command."""
    inbox = load(INBOX, [])
    deleted, failed, keep = 0, 0, []
    for item in inbox:
        if item.get("processed"):
            # Each item carries its own chat id, so several approved accounts work.
            item_chat = item.get("chat_id", chat_id)
            ok = api(
                "deleteMessage", chat_id=item_chat, message_id=item["message_id"]
            ).get("ok")
            if ok:
                deleted += 1
            else:
                failed += 1
            for rid in item.get("bot_reply_ids", []):
                api("deleteMessage", chat_id=item_chat, message_id=rid)
        else:
            keep.append(item)
    save(INBOX, keep)
    api("deleteMessage", chat_id=chat_id, message_id=cmd_mid)
    note = "\U0001F9F9 Cleanup: deleted %d processed message(s)" % deleted
    if failed:
        # Telegram only lets a bot delete its chat's messages under 48 hours old.
        note += ", %d too old (over 48h); delete those manually" % failed
    api("sendMessage", chat_id=chat_id, text=note)


def maybe_auto_process(cfg):
    """Optional scheduled run. Off unless config sets auto_hour to an hour."""
    import datetime
    import subprocess
    import threading

    if not cfg.get("auto_hour"):
        return
    today = datetime.date.today().isoformat()
    if cfg.get("last_auto") == today or datetime.datetime.now().hour < cfg["auto_hour"]:
        return

    cfg["last_auto"] = today
    save(CONFIG, cfg)

    inbox = load(INBOX, [])
    pending = [m for m in inbox if not m.get("processed")]
    if not pending:
        log("auto-process: queue empty, skipped")
        return

    chat_ids = {m["chat_id"] for m in pending}
    for cid in chat_ids:
        api(
            "sendMessage",
            chat_id=cid,
            text="⏳ %s auto-run started; processing %d queued item(s)."
            % (BASE_NAME, len(pending)),
        )

    base_dir = cfg.get("base_dir") or BASE_DIR
    agent = cfg.get("agent_path", "claude")
    prompt = cfg.get(
        "auto_prompt", "Run /promptos:process and follow it exactly."
    )
    out = open(os.path.join(BASE_DIR, "auto_run.log"), "a", encoding="utf-8")
    out.write("\n===== run %s =====\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
    log("auto-process: spawning agent run")
    proc = subprocess.Popen(
        [agent, "-p", prompt, "--dangerously-skip-permissions"],
        cwd=base_dir,
        stdout=out,
        stderr=out,
    )

    def waiter():
        rc = proc.wait()
        out.close()
        if rc != 0:
            # A silent scheduled failure destroys trust in the pipeline.
            for cid in chat_ids:
                api(
                    "sendMessage",
                    chat_id=cid,
                    text="⚠️ %s auto-run FAILED (exit %d). Check auto_run.log. "
                    "Most common cause: the agent CLI is not logged in."
                    % (BASE_NAME, rc),
                )
            log("auto-process: run failed rc=%d" % rc)
        else:
            log("auto-process: run finished ok")

    threading.Thread(target=waiter, daemon=True).start()


def main():
    log("bot started")
    while True:
        cfg = load(CONFIG, {})
        offset = cfg.get("offset", 0)
        maybe_auto_process(cfg)

        resp = api("getUpdates", offset=offset, timeout=50)
        if not resp.get("ok"):
            time.sleep(5)
            continue

        for upd in resp["result"]:
            offset = upd["update_id"] + 1
            msg = upd.get("message")
            if not msg or msg["chat"].get("type") != "private":
                continue

            chat_id = msg["chat"]["id"]
            uid = msg["from"]["id"]
            owners = cfg.setdefault("owners", [])

            if uid not in owners:
                # Enrolment window: the user opens N slots, then it closes itself.
                if cfg.get("enroll_remaining", 0) > 0:
                    owners.append(uid)
                    cfg["enroll_remaining"] -= 1
                    log(
                        "enrolled %s (%s)"
                        % (
                            uid,
                            msg["from"].get("username")
                            or msg["from"].get("first_name"),
                        )
                    )
                    api(
                        "sendMessage",
                        chat_id=chat_id,
                        text="done ✅ this account can now send materials to %s"
                        % BASE_NAME,
                    )
                    save(CONFIG, cfg)
                # Everyone else is ignored in silence, giving nothing away.
                continue

            text = (msg.get("text") or msg.get("caption") or "").strip()
            cmd = text.lower().split("@")[0]

            if cmd == "/cleanup":
                handle_cleanup(chat_id, msg["message_id"])
            elif cmd in ("/start", "/help"):
                api("sendMessage", chat_id=chat_id, text=HELP)
            elif text:
                trigger = BASE_NAME.lower() in text.lower()
                inbox = load(INBOX, [])
                inbox.append(
                    {
                        "message_id": msg["message_id"],
                        "date": msg["date"],
                        "text": text,
                        "chat_id": chat_id,
                        "processed": False,
                        "trigger": trigger,
                    }
                )
                save(INBOX, inbox)
                if trigger:
                    api(
                        "sendMessage",
                        chat_id=chat_id,
                        text="\U0001F7E2 Trigger noted; the queue will be processed on "
                        "the next run.",
                    )

        cfg["offset"] = offset
        save(CONFIG, cfg)


if __name__ == "__main__":
    # Never let one unhandled exception end capture. A dead collector loses
    # messages permanently, because Telegram drops unfetched updates after ~24h.
    while True:
        try:
            main()
        except Exception as e:
            log("FATAL restart: %r" % (e,))
            time.sleep(10)
