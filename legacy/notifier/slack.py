import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

IMPACT_EMOJI = {
    "HIGH": "🔴",
    "MEDIUM": "🟡",
    "LOW": "🟢",
}

def send_slack_digest(results: list[dict]):
    if not results:
        print("[Notifier] No new circulars.")
        return
    message = []

    message.append(
        f"*RegIntel AI Digest*"
        f"({datetime.now().strftime('%Y-%m-%d %H:%M')})"
    )
    message.append("")
    for r in results:
        circular = r["circular"]
        summary = r["summary"]
        impact = r["impact"]
        emoji = IMPACT_EMOJI.get(impact["impact_level"], "⚪")
        message.append(f"{emoji} *{circular.title}*")
        message.append(f"*Source:* {circular.source}")
        message.append(f"*Impact:* {impact['impact_level']}")
        message.append(f"*Summary:* {summary}")
        message.append(f"*Action:* {impact['action_required']}")
        message.append(f"<{circular.url}|Read Circular>")
        message.append("")
    final_message = "\n".join(message)

    if not SLACK_WEBHOOK_URL:
        print("[Notifier] SLACK_WEBHOOK_URL missing.")
        print(final_message)
        return
    try:
        response = requests.post(SLACK_WEBHOOK_URL,
            json={
                "text": final_message
            }, timeout=10
        )
        if response.status_code == 200:
            print("[Notifier] Slack message sent successfully.")
        else:
            print(
                f"[Notifier] Slack failed "
                f"({response.status_code})"
            )
            print(response.text)
    except Exception as e:
        print("[Notifier] Slack exception:")
        print(e)