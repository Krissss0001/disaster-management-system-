import os
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# In-memory log of recent emergency alerts
DISPATCH_ALERT_LOG: List[Dict[str, Any]] = []


def dispatch_emergency_alert(
    event_type: str,
    title: str,
    urgency_or_severity: int,
    details: str,
    location_str: Optional[str] = None
) -> Dict[str, Any]:
    """
    Trigger real-time emergency dispatch call/SMS alert.
    Supports 'mock' mode (simulated emergency calling) or 'live' with Twilio/Webhook.
    """
    alert_mode = os.getenv("ALERT_MODE", "mock").lower()
    dispatch_phone = os.getenv("EMERGENCY_DISPATCH_PHONE", "+15551234567")
    webhook_url = os.getenv("ALERT_WEBHOOK_URL", "").strip()
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    alert_payload = {
        "timestamp": timestamp,
        "event_type": event_type,
        "title": title,
        "urgency_or_severity": urgency_or_severity,
        "details": details,
        "location": location_str or "Unspecified coordinates",
        "target_dispatch": dispatch_phone,
        "mode": alert_mode,
        "status": "pending"
    }

    message_body = (
        f"🚨 [EMERGENCY ALERT] Level {urgency_or_severity}/5 - {title}\n"
        f"Details: {details}\nLocation: {location_str}\nTarget: {dispatch_phone}"
    )

    if alert_mode == "mock":
        alert_payload["status"] = "simulated_call_dispatched"
        alert_payload["summary"] = f"Simulated automated emergency call & SMS dispatched to {dispatch_phone}."
    else:
        # Check if Twilio is configured
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_phone = os.getenv("TWILIO_FROM_NUMBER")

        if account_sid and auth_token and from_phone:
            try:
                # Direct HTTP call to Twilio Messages API without heavy twilio sdk dependency
                url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
                resp = requests.post(
                    url,
                    data={"From": from_phone, "To": dispatch_phone, "Body": message_body},
                    auth=(account_sid, auth_token),
                    timeout=5
                )
                if resp.status_code in [200, 201]:
                    alert_payload["status"] = "live_sms_dispatched"
                    alert_payload["summary"] = f"Live SMS dispatched to {dispatch_phone} via Twilio."
                else:
                    alert_payload["status"] = "api_error"
                    alert_payload["summary"] = f"Twilio API error: {resp.text}"
            except Exception as e:
                alert_payload["status"] = "failed"
                alert_payload["summary"] = f"Failed to dispatch Twilio alert: {str(e)}"
        else:
            alert_payload["status"] = "live_keys_missing"
            alert_payload["summary"] = "Twilio credentials not fully set in .env. Switched to simulation."

    # Dispatch to Webhook if provided
    if webhook_url:
        try:
            requests.post(webhook_url, json=alert_payload, timeout=3)
            alert_payload["webhook_sent"] = True
        except Exception:
            alert_payload["webhook_sent"] = False

    DISPATCH_ALERT_LOG.insert(0, alert_payload)
    return alert_payload


def get_recent_alerts(limit: int = 10) -> List[Dict[str, Any]]:
    """Return the recent emergency alert history."""
    return DISPATCH_ALERT_LOG[:limit]
