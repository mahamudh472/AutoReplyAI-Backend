import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, Any, List, Optional
from django.conf import settings

class MetaAuthError(Exception):
    """Exception raised for errors during Meta OAuth and API interactions."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class MetaAuthService:
    """
    Service to handle Meta OAuth token exchanges and fetching Meta Page resources.
    """

    @staticmethod
    def get_user_access_token(code: str) -> Dict[str, Any]:
        """
        Exchanges the authorization code for a short-lived access token,
        then upgrades it to a long-lived access token.
        
        Returns:
            Dict[str, Any]: The payload containing:
                - access_token (str)
                - token_type (str)
                - expires_in (int)
        """
        client_id = getattr(settings, "META_CLIENT_ID", "")
        client_secret = getattr(settings, "META_CLIENT_SECRET", "")
        redirect_uri = getattr(settings, "META_REDIRECT_URI", "")

        if not client_id or not client_secret or not redirect_uri:
            raise MetaAuthError(
                "Meta OAuth configuration is incomplete in settings. Ensure META_CLIENT_ID, "
                "META_CLIENT_SECRET, and META_REDIRECT_URI are set."
            )

        # 1. Exchange authorization code for short-lived token
        token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
        params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        }
        query_string = urllib.parse.urlencode(params)
        full_url = f"{token_url}?{query_string}"

        try:
            req = urllib.request.Request(full_url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode("utf-8")
                res_data = json.loads(res_body)
        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode("utf-8")
                error_data = json.loads(error_body)
                error_msg = error_data.get("error", {}).get("message", str(e))
            except Exception:
                error_data = {}
                error_msg = str(e)
            raise MetaAuthError(f"Failed to exchange code: {error_msg}", error_data)
        except Exception as e:
            raise MetaAuthError(f"Network error during code exchange: {str(e)}")

        short_lived_token = res_data.get("access_token")
        if not short_lived_token:
            raise MetaAuthError("No access token returned in the initial response.", res_data)

        # 2. Exchange short-lived token for long-lived token
        upgrade_params = {
            "grant_type": "fb_exchange_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "fb_exchange_token": short_lived_token,
        }
        upgrade_query = urllib.parse.urlencode(upgrade_params)
        upgrade_url = f"{token_url}?{upgrade_query}"

        try:
            upgrade_req = urllib.request.Request(upgrade_url, method="GET")
            with urllib.request.urlopen(upgrade_req, timeout=10) as response:
                upgrade_res_body = response.read().decode("utf-8")
                upgrade_res_data = json.loads(upgrade_res_body)
            return upgrade_res_data
        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode("utf-8")
                error_data = json.loads(error_body)
                error_msg = error_data.get("error", {}).get("message", str(e))
            except Exception:
                error_data = {}
                error_msg = str(e)
            raise MetaAuthError(f"Failed to upgrade user token: {error_msg}", error_data)
        except Exception as e:
            raise MetaAuthError(f"Network error during token upgrade: {str(e)}")

    @staticmethod
    def get_user_pages(access_token: str) -> List[Dict[str, Any]]:
        """
        Fetches the list of Facebook pages the user has managed access to.
        
        Returns:
            List[Dict[str, Any]]: List of pages with id, name, access_token, etc.
        """
        url = "https://graph.facebook.com/v19.0/me/accounts"
        params = {
            "access_token": access_token,
            "limit": 100
        }
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"

        try:
            req = urllib.request.Request(full_url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode("utf-8")
                res_data = json.loads(res_body)
            return res_data.get("data", [])
        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode("utf-8")
                error_data = json.loads(error_body)
                error_msg = error_data.get("error", {}).get("message", str(e))
            except Exception:
                error_data = {}
                error_msg = str(e)
            raise MetaAuthError(f"Failed to retrieve pages: {error_msg}", error_data)
        except Exception as e:
            raise MetaAuthError(f"Network error during pages fetch: {str(e)}")

    @staticmethod
    def subscribe_page_to_app(page_id: str, page_access_token: str, subscribed_fields: Optional[List[str]] = None) -> bool:
        """
        Subscribes an app to a Facebook Page's webhook events so that incoming messages
        and interactions are forwarded to the configured webhook URL.
        
        POST https://graph.facebook.com/v19.0/{page_id}/subscribed_apps
        """
        if not subscribed_fields:
            subscribed_fields = [
                "messages",
                "messaging_postbacks",
                "messaging_optins",
                "message_deliveries",
                "message_reads",
                "message_echoes"
            ]

        url = f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {page_access_token}"
        }
        payload = {
            "subscribed_fields": ",".join(subscribed_fields)
        }

        try:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode("utf-8")
                res_data = json.loads(res_body)
                return bool(res_data.get("success", False))
        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode("utf-8")
                error_data = json.loads(error_body)
                error_msg = error_data.get("error", {}).get("message", str(e))
            except Exception:
                error_data = {}
                error_msg = str(e)
            raise MetaAuthError(f"Failed to subscribe page to webhook: {error_msg}", error_data)
        except Exception as e:
            raise MetaAuthError(f"Network error during webhook subscription: {str(e)}")

    @staticmethod
    def unsubscribe_page_from_app(page_id: str, page_access_token: str) -> bool:
        """
        Unsubscribes an app from a Facebook Page's webhook events.
        
        DELETE https://graph.facebook.com/v19.0/{page_id}/subscribed_apps
        """
        url = f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps"
        headers = {
            "Authorization": f"Bearer {page_access_token}"
        }

        try:
            req = urllib.request.Request(url, headers=headers, method="DELETE")
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode("utf-8")
                res_data = json.loads(res_body)
                return bool(res_data.get("success", False))
        except Exception:
            return False

