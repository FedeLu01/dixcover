from typing import Optional
from datetime import datetime

from app.utils.log import app_logger
import os
import requests
from typing import Dict
from typing import List


class Notifier:
    """Notifier that can emit messages to Slack and Discord via incoming webhooks.

    Behavior:
    - Detects enabled platforms by reading `SLACK_WEBHOOK_URL` and `DISCORD_WEBHOOK_URL` from env.
    - If none are configured, falls back to logging only.
    - `notify_new_alive` sends a concise, human-friendly message showing date/time (no seconds), subdomain, and status code.
    """

    SLACK_ENV = "SLACK_WEBHOOK_URL"
    DISCORD_ENV = "DISCORD_WEBHOOK_URL"
    SLACK_MENTION_ENV = "SLACK_MENTION"
    DISCORD_MENTION_ENV = "DISCORD_MENTION"

    def __init__(self):
        self.slack_url = os.environ.get(self.SLACK_ENV)
        self.discord_url = os.environ.get(self.DISCORD_ENV)
        # mention configuration: values can be 'here' for Slack and 'everyone' or 'here' for Discord
        self.slack_mention = (os.environ.get(self.SLACK_MENTION_ENV) or "").strip().lower()
        self.discord_mention = (os.environ.get(self.DISCORD_MENTION_ENV) or "").strip().lower()
        if self.slack_url:
            app_logger.info("notifier.init", platform="slack", webhook=self._redact(self.slack_url))
        if self.discord_url:
            app_logger.info("notifier.init", platform="discord", webhook=self._redact(self.discord_url))

    def _redact(self, v: str) -> str:
        # redact the webhook URL for logging (show only domain)
        try:
            parsed = v.split('/')
            return f".../{parsed[-1]}"
        except Exception:
            return "(redacted)"

    def _format_common(self, subdomain: str, status_code: Optional[int], probed_at: datetime) -> Dict[str, str]:
        # date/time without seconds
        ts = probed_at.strftime("%Y-%m-%d %H:%M")
        code = str(status_code) if status_code is not None else "-"
        return {"ts": ts, "subdomain": subdomain, "status": code}

    def _send_slack(self, payload: Dict) -> None:
        if not self.slack_url:
            return
        # Use a simple block with a section and small context
        # Slack has limits on message size and blocks. Guard against excessively long messages.
        MAX_TEXT_LEN = 1000
        # format and truncate safely
        raw_text = f"*{payload['ts']}* — `{payload['subdomain']}` — status: `{payload['status']}`"
        text = raw_text if len(raw_text) <= MAX_TEXT_LEN else raw_text[: MAX_TEXT_LEN - 3] + "..."
        # include mention in top-level text so Slack will deliver the notification
        mention_text = ""
        if self.slack_mention == "here":
            mention_text = "<!here> "
        elif self.slack_mention == "channel":
            mention_text = "<!channel> "

        body = {
            "text": f"{mention_text}New alive subdomain: {payload['subdomain']}",
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn", "text": text}},
                {"type": "context", "elements": [{"type": "mrkdwn", "text": "Dixcover probe"}]},
            ],
        }
        try:
            resp = requests.post(self.slack_url, json=body, timeout=5)
            if resp.status_code >= 400:
                app_logger.error("notifier.slack_error", status=resp.status_code, body=resp.text)
            else:
                app_logger.debug("notifier.slack_sent", subdomain=payload['subdomain'])
        except requests.RequestException as e:
            app_logger.error("notifier.slack_exception", error=str(e), subdomain=payload['subdomain'])

    def _send_discord(self, payload: Dict) -> None:
        if not self.discord_url:
            return
        # Use an embed for prettier formatting
        # Discord embed limits: title max 256 chars, description max 4096 chars
        timestamp = probed_at_iso(payload.get('ts', ''))
        embed = {
            "title": "New alive subdomain",
            "description": f"**{payload['subdomain']}**\nStatus: `{payload['status']}`",
            "footer": {"text": "Dixcover"},
        }
        # Only add timestamp if it's valid ISO8601 format
        if timestamp and timestamp != payload.get('ts', ''):
            embed["timestamp"] = timestamp
        
        # Discord mentions must be sent in the `content` field (not inside embeds)
        content = ""
        if self.discord_mention == "everyone":
            content = "@everyone"
        elif self.discord_mention == "here":
            content = "@here"

        body = {"embeds": [embed]}
        if content:
            body["content"] = content
        try:
            resp = requests.post(self.discord_url, json=body, timeout=5)
            if resp.status_code >= 400:
                app_logger.error("notifier.discord_error", status=resp.status_code, body=resp.text)
            else:
                app_logger.debug("notifier.discord_sent", subdomain=payload['subdomain'])
        except requests.RequestException as e:
            app_logger.error("notifier.discord_exception", error=str(e), subdomain=payload['subdomain'])

    def notify_new_alive(self, subdomain: str, status_code: Optional[int], probed_at: datetime) -> None:
        """Called when a new alive subdomain is discovered.

        Sends messages to enabled messaging platforms and always logs the event locally.
        """
        app_logger.info("notifier.new_alive", subdomain=subdomain, status_code=status_code, probed_at=probed_at.isoformat())

        payload = self._format_common(subdomain, status_code, probed_at)

        # send to configured platforms
        if self.slack_url:
            self._send_slack(payload)
        if self.discord_url:
            # Discord wants ISO8601 timestamp in embed; convert the stored ts back to ISO
            self._send_discord(payload)

    def notify_new_alives(self, items: List[Dict[str, object]]) -> None:
        """Notify about multiple new alive subdomains in one message.

        `items` is a list of dicts with keys: `subdomain` (str), `status` (str/int), `ts` (string as %Y-%m-%d %H:%M) or `probed_at` (datetime).
        """
        if not items:
            return

        # log summary locally
        app_logger.info("notifier.new_alives", count=len(items))

        # Normalize payload entries
        normalized = []
        for it in items:
            if isinstance(it.get('probed_at'), datetime):
                ts = it['probed_at'].strftime("%d-%m-%Y %H:%M")
            else:
                ts = it.get('ts') or str(it.get('probed_at') or '')
            normalized.append({
                'ts': ts,
                'subdomain': it.get('subdomain'),
                'status': str(it.get('status') if it.get('status') is not None else it.get('status_code', '-')),
            })

        # If only one item, reuse single-item notifier to keep behavior consistent
        if len(normalized) == 1:
            it = normalized[0]
            if self.slack_url:
                self._send_slack(it)
            if self.discord_url:
                self._send_discord(it)
            return

        # Prepare batched messages
        # Slack: one message with multiple sections
        if self.slack_url:
            blocks = []
            # Slack limits: keep blocks and text bounded. We'll include up to MAX_ITEMS entries and append a summary if truncated.
            MAX_ITEMS = 25
            MAX_BLOCKS = 45
            MAX_LINE_LEN = 600

            header = {"type": "section", "text": {"type": "mrkdwn", "text": f"*{len(normalized)} new alive subdomains detected*"}}
            blocks.append(header)

            display = normalized[:MAX_ITEMS]
            for it in display:
                raw = f"*{it['ts']}* — `{it['subdomain']}` — status: `{it['status']}`"
                text = raw if len(raw) <= MAX_LINE_LEN else raw[: MAX_LINE_LEN - 3] + "..."
                blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})

            remaining = len(normalized) - len(display)
            if remaining > 0:
                more_text = f"And {remaining} more entries..."
                blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": more_text}]})

            # Ensure we don't exceed block count
            if len(blocks) > MAX_BLOCKS:
                blocks = blocks[:MAX_BLOCKS]

            # include mention in top-level text if configured
            mention_text = ""
            if self.slack_mention == "here":
                mention_text = "<!here> "
            elif self.slack_mention == "channel":
                mention_text = "<!channel> "

            body = {"text": f"{mention_text}{len(normalized)} new alive subdomains detected", "blocks": blocks}
            body = {"text": f"{len(normalized)} new alive subdomains detected", "blocks": blocks}
            try:
                resp = requests.post(self.slack_url, json=body, timeout=5)
                if resp.status_code >= 400:
                    app_logger.error("notifier.slack_error", status=resp.status_code, body=resp.text)
                else:
                    app_logger.debug("notifier.slack_sent_batch", count=len(normalized))
            except requests.RequestException as e:
                app_logger.error("notifier.slack_exception", error=str(e))

        # Discord: single embed listing entries in the description (keeps single message)
        # Discord limits: embed description max 4096 chars, title max 256 chars
        if self.discord_url:
            MAX_DESC_LEN = 4096
            MAX_TITLE_LEN = 256
            MAX_ITEMS_DISCORD = 50  # Reasonable limit to prevent description overflow
            
            desc_lines = []
            display_items = normalized[:MAX_ITEMS_DISCORD]
            for it in display_items:
                line = f"**{it['subdomain']}** — `{it['status']}` — {it['ts']}"
                desc_lines.append(line)
            
            description = "\n".join(desc_lines)
            
            # Truncate description if too long (leave room for truncation message)
            if len(description) > MAX_DESC_LEN - 50:
                # Find the last complete line that fits
                truncated = description[:MAX_DESC_LEN - 50]
                last_newline = truncated.rfind('\n')
                if last_newline > 0:
                    description = truncated[:last_newline]
                else:
                    description = truncated
                
                remaining = len(normalized) - len(display_items)
                if remaining > 0:
                    description += f"\n\n... and {remaining} more subdomains"
                else:
                    description += "\n\n... (truncated)"
            
            # Ensure title doesn't exceed limit
            title = f"{len(normalized)} new alive subdomains"
            if len(title) > MAX_TITLE_LEN:
                title = title[:MAX_TITLE_LEN - 3] + "..."
            
            embed = {
                "title": title,
                "description": description,
                "footer": {"text": "Dixcover"},
            }
            
            # Discord mentions must be sent in the `content` field
            content = ""
            if self.discord_mention == "everyone":
                content = "@everyone"
            elif self.discord_mention == "here":
                content = "@here"
            
            body = {"embeds": [embed]}
            if content:
                body["content"] = content
                
            try:
                resp = requests.post(self.discord_url, json=body, timeout=5)
                if resp.status_code >= 400:
                    app_logger.error("notifier.discord_error", status=resp.status_code, body=resp.text)
                else:
                    app_logger.debug("notifier.discord_sent_batch", count=len(normalized))
            except requests.RequestException as e:
                app_logger.error("notifier.discord_exception", error=str(e))



def probed_at_iso(ts_str: str) -> str:
    # helper converting our `%Y-%m-%d %H:%M` back to ISO by appending seconds
    try:
        from datetime import datetime

        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M")
        return dt.isoformat()
    except Exception:
        return ts_str


notifier = Notifier()
