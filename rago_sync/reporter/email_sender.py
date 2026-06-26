import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

_CONFIG_PATH = Path.home() / ".config/opencode/skills/send-simplification-report/scripts/config.json"


def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        return json.loads(_CONFIG_PATH.read_text())
    alt = Path.home() / ".config/opencode/skills/send-simplification-report (2)/scripts/config.json"
    if alt.exists():
        return json.loads(alt.read_text())
    raise FileNotFoundError(f"Email config not found at {_CONFIG_PATH}")


def send_report(html: str, subject: str = "[RAGO Sync] Weekly Detect Report") -> bool:
    """Send HTML report via Gmail SMTP. Returns True on success."""
    try:
        config = _load_config()
        sender = config["sender"]
        recipients = config["recipients"]
        password = config["app_password"]

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False
