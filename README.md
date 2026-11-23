# 🎧 Audionic Trance Infinity Restock Notifier

Automated stock tracker that checks **[Audionic Trance Infinity Hybrid ANC Headphones](https://audionic.co/products/trance-infinity)** and sends an instant push notification to your phone the second it is restocked.

- **100% Free**: No paid APIs, no servers to rent.
- **Bypasses Cloudflare**: Emulates genuine browser TLS fingerprints so requests aren't blocked.
- **Variants Tracked**: Checks both "Black" and "White" variants and alerts with price and restock details.
- **Multiple Notification Channels**:
  - **ntfy.sh** *(Recommended - instant phone push notifications, no account/login needed)*
  - **Telegram Bot** *(Direct message to your personal Telegram account)*
  - **Discord Webhook** *(Alerts in a Discord channel)*

---

## ⚡ Option 1: Instant Phone Alert via `ntfy` (Easiest - 1 Minute Setup)

`ntfy` is a free, open-source push notification service that delivers instant alerts to iOS and Android.

1. **Install the App on your Phone**:
   - **Android**: Download [ntfy on Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
   - **iOS**: Download [ntfy on the App Store](https://apps.apple.com/us/app/ntfy/id1625396347)
2. **Subscribe to a Unique Topic**:
   - Open the ntfy app.
   - Tap the `+` button to subscribe to a new topic.
   - Enter a unique name, e.g. `audionic_trance_infinity_restock_xyz99` (use something random so others don't subscribe to yours).
3. **Configure the script**:
   - Create or edit the `.env` file in this folder:
     ```env
     NTFY_TOPIC=audionic_trance_infinity_restock_xyz99
     ```
4. **Test it**:
   - Run:
     ```bash
     python check_stock.py --test-notify
     ```
   - Your phone will instantly ring/vibrate with a test notification! Tapping it opens the Audionic store page.

---

## 🤖 Option 2: Telegram Bot (Optional)

If you prefer Telegram:
1. Open Telegram and search for `@BotFather`. Send `/newbot` and follow the prompts to get your **Bot Token**.
2. Search for `@userinfobot` on Telegram and send a message to get your numeric **Chat ID**.
3. Send a message like "hello" to your newly created bot.
4. Add them to your `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
   TELEGRAM_CHAT_ID=987654321
   ```

---

## 🌐 How to Run 24/7 in the Cloud for FREE (GitHub Actions)

You don't need to leave your computer running! You can let GitHub run this script for you every 15 minutes completely free:

1. Create a repository on [GitHub](https://github.com) (can be Private or Public).
2. Push this folder to your repository:
   ```bash
   git init
   git add .
   git commit -m "Audionic restock monitor"
   git remote add origin https://github.com/YOUR_USERNAME/audionic-restock.git
   git push -u origin main
   ```
3. In your GitHub repository:
   - Go to **Settings** > **Secrets and variables** > **Actions**.
   - Click **New repository secret**.
   - Name: `NTFY_TOPIC` (Value: your chosen topic name).
   *(Or add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` if using Telegram)*.
4. Go to the **Actions** tab in GitHub and click **Enable workflows**.
   - The workflow (`.github/workflows/stock_check.yml`) will automatically run every 15 minutes, 24 hours a day, 7 days a week, and ping your phone when it's back in stock!

---

## 💻 How to Run Locally on your PC

If you have your computer running and want to monitor locally:

### Option A: Double-Click Runner (Windows)
Double-click `run_local.bat`. It will automatically check dependencies and run the continuous loop.

### Option B: Command Line
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run a single check
python check_stock.py

# 3. Run continuously (checks every 2 minutes by default)
python check_stock.py --loop

# 4. Run with custom check interval (e.g. every 60 seconds)
python check_stock.py --loop --interval 60
```
