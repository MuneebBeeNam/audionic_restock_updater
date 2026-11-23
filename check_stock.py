"""
Audionic Stock Notifier
Monitors Audionic products (such as Trance Infinity) and sends instant push
notifications to your phone via ntfy.sh, Telegram, or Discord when back in stock.
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    cffi_requests = None

import requests

# Defaults
DEFAULT_PRODUCT_URL = "https://audionic.co/products/trance-infinity"
STATE_FILE = Path(__file__).parent / "stock_state.json"


def get_config():
    return {
        "product_url": os.getenv("PRODUCT_URL", DEFAULT_PRODUCT_URL).strip(),
        "ntfy_topic": os.getenv("NTFY_TOPIC", "").strip(),
        "telegram_token": os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", "").strip(),
        "discord_webhook": os.getenv("DISCORD_WEBHOOK_URL", "").strip(),
        "check_interval": int(os.getenv("CHECK_INTERVAL_SECONDS", "120")),
    }


def send_ntfy_notification(topic: str, title: str, message: str, url: str) -> bool:
    """Send a push notification via ntfy.sh (No account needed, instant phone alert)"""
    if not topic:
        return False
    try:
        endpoint = f"https://ntfy.sh/{topic}"
        headers = {
            "Title": title.encode("utf-8"),
            "Priority": "urgent",
            "Tags": "loudspeaker,tada,shopping_cart",
            "Click": url,
            "Actions": f"view, Open Product Page, {url}",
        }
        res = requests.post(endpoint, data=message.encode("utf-8"), headers=headers, timeout=10)
        if res.status_code == 200:
            print(f"[+] Notification sent to ntfy.sh/{topic}")
            return True
        else:
            print(f"[-] ntfy.sh returned error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[-] Failed to send ntfy notification: {e}")
    return False


def send_telegram_notification(token: str, chat_id: str, title: str, message: str, url: str) -> bool:
    """Send notification via Telegram bot"""
    if not token or not chat_id:
        return False
    try:
        endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
        text = f"<b>{title}</b>\n\n{message}\n\n🔗 <a href='{url}'>Click here to Buy Now</a>"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        res = requests.post(endpoint, json=payload, timeout=10)
        if res.status_code == 200 and res.json().get("ok"):
            print(f"[+] Notification sent to Telegram chat {chat_id}")
            return True
        else:
            print(f"[-] Telegram error: {res.text}")
    except Exception as e:
        print(f"[-] Failed to send Telegram notification: {e}")
    return False


def send_discord_notification(webhook_url: str, title: str, message: str, url: str) -> bool:
    """Send notification via Discord Webhook"""
    if not webhook_url:
        return False
    try:
        payload = {
            "content": f"@everyone 🚨 **{title}**\n{message}\n👉 **Buy Link:** {url}",
            "embeds": [
                {
                    "title": title,
                    "description": message,
                    "url": url,
                    "color": 3066993,  # Green
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ],
        }
        res = requests.post(webhook_url, json=payload, timeout=10)
        if res.status_code in [200, 204]:
            print("[+] Notification sent to Discord webhook")
            return True
        else:
            print(f"[-] Discord error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[-] Failed to send Discord notification: {e}")
    return False


def notify_all(title: str, message: str, url: str, cfg: dict) -> bool:
    """Broadcast notifications to all configured channels"""
    sent_any = False
    if cfg["ntfy_topic"]:
        sent_any = send_ntfy_notification(cfg["ntfy_topic"], title, message, url) or sent_any
    if cfg["telegram_token"] and cfg["telegram_chat_id"]:
        sent_any = send_telegram_notification(cfg["telegram_token"], cfg["telegram_chat_id"], title, message, url) or sent_any
    if cfg["discord_webhook"]:
        sent_any = send_discord_notification(cfg["discord_webhook"], title, message, url) or sent_any

    if not sent_any and not (cfg["ntfy_topic"] or cfg["telegram_token"] or cfg["discord_webhook"]):
        print("[!] No notification channels configured! Please edit your .env file.")
    return sent_any


def check_product(product_url: str) -> dict:
    """
    Checks the product stock on Audionic using Shopify JSON endpoint.
    Bypasses Cloudflare using curl_cffi with Chrome fingerprint impersonation.
    """
    clean_url = product_url.split("?")[0].rstrip("/")
    json_url = f"{clean_url}.js"

    # Use curl_cffi if installed, otherwise fallback to requests
    session = cffi_requests if cffi_requests is not None else requests

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": clean_url,
    }

    try:
        kwargs = {"headers": headers, "timeout": 15}
        if cffi_requests is not None:
            kwargs["impersonate"] = "chrome120"

        res = session.get(json_url, **kwargs)
        if res.status_code == 200:
            data = res.json()
            variants = []
            for v in data.get("variants", []):
                # price in shopify .js is in cents (e.g. 999900 = 9999 PKR)
                raw_price = v.get("price", 0)
                formatted_price = raw_price / 100 if raw_price > 1000 else raw_price
                variants.append({
                    "id": v.get("id"),
                    "title": v.get("title"),
                    "available": bool(v.get("available")),
                    "price": formatted_price,
                })

            available = bool(data.get("available")) or any(v["available"] for v in variants)
            return {
                "success": True,
                "title": data.get("title", "Product"),
                "available": available,
                "variants": variants,
                "url": clean_url,
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {res.status_code}",
                "url": clean_url,
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "url": clean_url,
        }


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_available": False, "in_stock_variants": []}


def save_state(state: dict):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"[-] Could not save state file: {e}")


def execute_check(cfg: dict, force_notify: bool = False):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now_str}] Checking stock for: {cfg['product_url']}")

    # Print configured channels so user can verify secrets are picked up in GitHub Actions
    channels = []
    if cfg.get("ntfy_topic"):
        channels.append(f"ntfy (topic: {cfg['ntfy_topic']})")
    if cfg.get("telegram_token"):
        channels.append("Telegram")
    if cfg.get("discord_webhook"):
        channels.append("Discord")

    if channels:
        print(f"[i] Active notification channel(s): {', '.join(channels)}")
    else:
        print("[!] WARNING: No notification channels found! Did you set the NTFY_TOPIC secret in GitHub?")

    result = check_product(cfg["product_url"])
    if not result.get("success"):
        print(f"[-] Failed to fetch product info: {result.get('error')}")
        return

    title = result["title"]
    is_available = result["available"]
    variants = result.get("variants", [])
    in_stock_variants = [v["title"] for v in variants if v["available"]]

    print(f"[i] Product: {title}")
    print(f"[i] Available: {is_available}")
    for v in variants:
        status_text = "IN STOCK" if v["available"] else "OUT OF STOCK"
        print(f"    - Variant: {v['title']} (PKR {v['price']:,.0f}) -> {status_text}")

    state = load_state()
    prev_available = state.get("last_available", False)
    prev_in_stock = state.get("in_stock_variants", [])

    newly_available = is_available and (not prev_available or set(in_stock_variants) - set(prev_in_stock))

    if newly_available or force_notify:
        notif_title = f"🎉 RESTOCK ALERT: {title}"
        if in_stock_variants:
            var_list = ", ".join(in_stock_variants)
            notif_msg = f"The following variants are now IN STOCK: {var_list}!\nPrice: PKR {variants[0]['price']:,.0f}\nGrab it before it sells out again!"
        else:
            notif_msg = f"{title} is now in stock!\nGrab it quickly!"

        print("\n🚀 [RESTOCK DETECTED] Sending alerts...")
        notify_all(notif_title, notif_msg, result["url"], cfg)
    else:
        if not is_available:
            print("[-] Currently OUT OF STOCK. No restock alert triggered.")
        else:
            print("[=] Already in stock (no state change).")

    # Update state
    state["last_available"] = is_available
    state["in_stock_variants"] = in_stock_variants
    state["last_checked"] = now_str
    save_state(state)


def main():
    parser = argparse.ArgumentParser(description="Audionic Stock Restock Notifier")
    parser.add_argument("--loop", action="store_true", help="Run continuously in a loop")
    parser.add_argument("--interval", type=int, help="Override check interval in seconds (default: 120)")
    parser.add_argument("--force-notify", action="store_true", help="Send restock notification regardless of state change")
    parser.add_argument("--test-notify", action="store_true", help="Send a test notification to verify your phone receives alerts")

    args = parser.parse_args()
    cfg = get_config()

    if args.interval:
        cfg["check_interval"] = args.interval

    if args.test_notify:
        print("[*] Sending test notification to configured channels...")
        success = notify_all(
            "🔔 Audionic Notifier: Test Notification",
            "Success! Your phone is correctly connected to the Audionic Restock Notifier. You will receive an alert here when the headphones are back in stock.",
            cfg["product_url"],
            cfg,
        )
        if success:
            print("[+] Test notification sent! Check your phone.")
        else:
            print("[-] Could not send test notification. Make sure your .env has NTFY_TOPIC, TELEGRAM_BOT_TOKEN, or DISCORD_WEBHOOK_URL set.")
        return

    if args.loop:
        print(f"[*] Starting stock monitor loop (every {cfg['check_interval']} seconds). Press Ctrl+C to stop.")
        while True:
            try:
                execute_check(cfg, force_notify=args.force_notify)
                print(f"[*] Sleeping for {cfg['check_interval']} seconds...\n")
                time.sleep(cfg["check_interval"])
            except KeyboardInterrupt:
                print("\n[*] Stopped by user.")
                break
            except Exception as e:
                print(f"[-] Unexpected error in loop: {e}")
                time.sleep(30)
    else:
        execute_check(cfg, force_notify=args.force_notify)


if __name__ == "__main__":
    main()
