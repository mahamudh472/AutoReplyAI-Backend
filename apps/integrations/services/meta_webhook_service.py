import hmac
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple
from django.conf import settings
from common.enums import PlatformChoice
from ..models import Integration
from .message_service import MetaMessageService

logger = logging.getLogger(__name__)

DEFAULT_STATIC_REPLY = "Hello! Thank you for reaching out. We have received your message and will get back to you soon."

class MetaWebhookService:
    """
    Handles verification of Meta webhook callbacks and processes incoming
    messages from Facebook Pages, Instagram, and WhatsApp Business, responding
    with a static message.
    """

    @staticmethod
    def verify_token(mode: Optional[str], token: Optional[str], challenge: Optional[str]) -> Tuple[bool, str]:
        """
        Validates the webhook verification handshake from Meta.
        
        Args:
            mode: The hub.mode query parameter (expected: 'subscribe')
            token: The hub.verify_token query parameter
            challenge: The hub.challenge query parameter
            
        Returns:
            Tuple[bool, str]: (is_valid, challenge or error_message)
        """
        expected_token = getattr(settings, "META_WEBHOOK_VERIFY_TOKEN", "")

        if mode == "subscribe" and token and expected_token and token == expected_token:
            return True, challenge or ""
        
        return False, "Verification token mismatch or invalid mode."

    @staticmethod
    def verify_signature(payload_bytes: bytes, signature_header: Optional[str]) -> bool:
        """
        Verifies X-Hub-Signature-256 header using META_CLIENT_SECRET.
        """
        secret = getattr(settings, "META_CLIENT_SECRET", "")
        if not secret or not signature_header:
            return True  # If secret or header is omitted, skip signature check

        if not signature_header.startswith("sha256="):
            return False

        expected_sig = signature_header[len("sha256="):]
        mac = hmac.new(secret.encode("utf-8"), msg=payload_bytes, digestmod=hashlib.sha256)
        return hmac.compare_digest(mac.hexdigest(), expected_sig)

    @classmethod
    def get_static_reply_text(cls) -> str:
        """
        Returns the configured static message reply text.
        """
        return getattr(settings, "META_DEFAULT_STATIC_REPLY", DEFAULT_STATIC_REPLY)

    @classmethod
    def process_webhook_payload(cls, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses Meta webhook event payload, extracts messages, and dispatches
        a static reply for each valid incoming user message.

        Returns:
            List[Dict[str, Any]]: Summary of replies sent or skipped.
        """
        object_type = data.get("object")
        entries = data.get("entry", [])
        results: List[Dict[str, Any]] = []

        for entry in entries:
            entry_id = str(entry.get("id", ""))

            # 1. Handle Facebook Page & Instagram (entry.messaging)
            if "messaging" in entry:
                for event in entry.get("messaging", []):
                    res = cls._handle_messaging_event(object_type, entry_id, event)
                    if res:
                        results.append(res)

            # 2. Handle WhatsApp Business Account (entry.changes)
            elif "changes" in entry:
                for change in entry.get("changes", []):
                    field = change.get("field")
                    value = change.get("value", {})
                    if field == "messages" or "messages" in value:
                        res_list = cls._handle_whatsapp_change(entry_id, value)
                        results.extend(res_list)

        return results

    @classmethod
    def _handle_messaging_event(cls, object_type: Optional[str], entry_id: str, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Processes a single messaging event for Facebook Pages or Instagram.
        """
        sender_id = event.get("sender", {}).get("id")
        recipient_id = event.get("recipient", {}).get("id")
        message_data = event.get("message")

        # Ignore if there is no message payload or if it is an echo of our own outgoing message
        if not message_data:
            return None

        if message_data.get("is_echo"):
            logger.info("Ignoring echo message from mid: %s", message_data.get("mid"))
            return {"status": "ignored", "reason": "is_echo", "mid": message_data.get("mid")}

        user_text = message_data.get("text", "")
        message_id = message_data.get("mid", "")

        # Determine target integration
        integration = None
        if object_type == "instagram":
            # Look up Instagram integration by entry_id or recipient_id
            integration = Integration.objects.filter(
                platform=PlatformChoice.INSTAGRAM,
                platform_identifier__in=[entry_id, str(recipient_id)],
                is_active=True
            ).first()
        else:
            # Look up Facebook Page integration by entry_id or recipient_id
            integration = Integration.objects.filter(
                platform=PlatformChoice.FACEBOOK_PAGE,
                platform_identifier__in=[entry_id, str(recipient_id)],
                is_active=True
            ).first()

        if not integration:
            logger.warning(
                "No active integration found for entry_id=%s, recipient_id=%s, platform=%s",
                entry_id, recipient_id, object_type
            )
            return {
                "status": "skipped",
                "reason": "integration_not_found",
                "entry_id": entry_id,
                "recipient_id": recipient_id,
                "sender_id": sender_id
            }

        # Send static message response to sender
        static_reply = cls.get_static_reply_text()
        success, info, payload = MetaMessageService.send_message(
            integration=integration,
            recipient_id=sender_id,
            message_content=static_reply
        )

        return {
            "status": "replied" if success else "reply_failed",
            "integration_id": str(integration.id),
            "platform": integration.platform,
            "sender_id": sender_id,
            "incoming_message_id": message_id,
            "incoming_text": user_text,
            "outgoing_message_id": info if success else None,
            "error": info if not success else None
        }

    @classmethod
    def _handle_whatsapp_change(cls, entry_id: str, value: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Processes WhatsApp messages within a webhook change event.
        """
        results: List[Dict[str, Any]] = []
        metadata = value.get("metadata", {})
        phone_number_id = str(metadata.get("phone_number_id", ""))
        messages = value.get("messages", [])

        # Look up WhatsApp integration by phone_number_id or entry_id (WABA ID)
        integration = Integration.objects.filter(
            platform=PlatformChoice.WHATSAPP_BUSINESS,
            platform_identifier=phone_number_id,
            is_active=True
        ).first()

        if not integration and entry_id:
            integration = Integration.objects.filter(
                platform=PlatformChoice.WHATSAPP_BUSINESS,
                additional_data__waba_id=entry_id,
                is_active=True
            ).first()

        for msg in messages:
            from_number = msg.get("from")
            msg_id = msg.get("id")
            text_body = msg.get("text", {}).get("body", "")

            if not integration:
                logger.warning(
                    "No active WhatsApp integration found for phone_number_id=%s, waba_id=%s",
                    phone_number_id, entry_id
                )
                results.append({
                    "status": "skipped",
                    "reason": "integration_not_found",
                    "phone_number_id": phone_number_id,
                    "sender_id": from_number
                })
                continue

            # Send static response
            static_reply = cls.get_static_reply_text()
            success, info, payload = MetaMessageService.send_message(
                integration=integration,
                recipient_id=from_number,
                message_content=static_reply
            )

            results.append({
                "status": "replied" if success else "reply_failed",
                "integration_id": str(integration.id),
                "platform": integration.platform,
                "sender_id": from_number,
                "incoming_message_id": msg_id,
                "incoming_text": text_body,
                "outgoing_message_id": info if success else None,
                "error": info if not success else None
            })

        return results
