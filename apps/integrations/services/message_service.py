import json
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple
from django.utils import timezone
from ..models import Integration, MessageLog
from common.enums import PlatformChoice

class MetaMessageService:
    """
    Service to send messages on behalf of the user's connected Meta channels
    (Facebook Pages, Instagram, WhatsApp Business) and log the actions.
    """

    @staticmethod
    def send_message(integration: Integration, recipient_id: str, message_content: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Dispatches a message using the integration access token and platform identifier.
        Returns:
            Tuple[bool, str, dict]: (success, error_message or platform_message_id, response_data)
        """
        # If integration is inactive, fail early
        if not integration.is_active:
            error_msg = "Integration is inactive."
            MessageLog.objects.create(
                integration=integration,
                recipient_id=recipient_id,
                message_content=message_content,
                status="failed",
                error_message=error_msg
            )
            return False, error_msg, {}

        # Prepare request details based on platform
        url = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {integration.access_token}"
        }
        payload: Dict[str, Any] = {}

        try:
            if integration.platform == PlatformChoice.FACEBOOK_PAGE:
                # Facebook Page Message API
                # POST https://graph.facebook.com/v19.0/{page_id}/messages
                url = f"https://graph.facebook.com/v19.0/{integration.platform_identifier}/messages"
                payload = {
                    "recipient": {"id": recipient_id},
                    "message": {"text": message_content}
                }

            elif integration.platform == PlatformChoice.INSTAGRAM:
                # Instagram Professional Account Message API
                # POST https://graph.facebook.com/v19.0/{instagram_account_id}/messages
                url = f"https://graph.facebook.com/v19.0/{integration.platform_identifier}/messages"
                payload = {
                    "recipient": {"id": recipient_id},
                    "message": {"text": message_content}
                }

            elif integration.platform == PlatformChoice.WHATSAPP_BUSINESS:
                # WhatsApp Business Cloud API
                # POST https://graph.facebook.com/v19.0/{phone_number_id}/messages
                url = f"https://graph.facebook.com/v19.0/{integration.platform_identifier}/messages"
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": recipient_id,
                    "type": "text",
                    "text": {
                        "preview_url": False,
                        "body": message_content
                    }
                }
            else:
                raise ValueError(f"Unsupported platform: {integration.platform}")

            # Send HTTP request
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode("utf-8")
                res_data = json.loads(res_body)

            # Extract platform message ID
            platform_message_id = ""
            if integration.platform == PlatformChoice.WHATSAPP_BUSINESS:
                messages = res_data.get("messages", [])
                if messages:
                    platform_message_id = messages[0].get("id", "")
            else:
                platform_message_id = res_data.get("message_id", "")

            # Log success
            MessageLog.objects.create(
                integration=integration,
                recipient_id=recipient_id,
                message_content=message_content,
                platform_message_id=platform_message_id,
                status="sent"
            )
            return True, platform_message_id, res_data

        except urllib.error.HTTPError as e:
            # Handle HTTP errors from Meta Graph API
            try:
                error_body = e.read().decode("utf-8")
                error_data = json.loads(error_body)
                error_msg = error_data.get("error", {}).get("message", str(e))
            except Exception:
                error_msg = str(e)

            MessageLog.objects.create(
                integration=integration,
                recipient_id=recipient_id,
                message_content=message_content,
                status="failed",
                error_message=error_msg
            )
            return False, error_msg, {}

        except Exception as e:
            # Handle general connection/timeout errors
            error_msg = str(e)
            MessageLog.objects.create(
                integration=integration,
                recipient_id=recipient_id,
                message_content=message_content,
                status="failed",
                error_message=error_msg
            )
            return False, error_msg, {}
