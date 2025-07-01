# backend/app/services/brevo/client.py
"""
Brevo (formerly Sendinblue) API service implementation.
Provides integration with Brevo's email marketing, transactional email, SMS, and WhatsApp APIs.
"""

import json
import hmac
import hashlib
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import httpx
import logging

from ...services.base import BaseService
from ...core.exceptions import (
    ServiceException, 
    AuthenticationException, 
    ExternalAPIError,
    RequestValidationError
)

logger = logging.getLogger(__name__)


class BrevoService(BaseService):
    """
    Brevo email marketing and communication service integration.
    
    Provides methods for:
    - Contact and list management
    - Email campaign creation and management
    - Transactional email sending
    - SMS campaigns and transactional SMS
    - WhatsApp messaging
    - Statistics and analytics
    - Webhook handling
    """
    
    def __init__(self, config: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None):
        super().__init__(config, credentials)
        
        # Brevo-specific settings with fallbacks
        settings = self.client_config
        self.default_sender_email = settings.get('default_sender_email', 'noreply@example.com')
        self.default_sender_name = settings.get('default_sender_name', 'API Testing Platform')
        self.enable_tracking = settings.get('enable_tracking', True)
        self.enable_batch_processing = settings.get('enable_batch_processing', True)
        
        # Log the configuration for debugging (without sensitive data)
        logger.info(f"Brevo service initialized with sender: {self.default_sender_name} <{self.default_sender_email}>")
        
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for Brevo API requests."""
        headers = super()._get_default_headers()
        
        # Add Brevo-specific headers
        headers.update({
            'User-Agent': f'APITestingPlatform/1.0 (brevo-integration)',
            'Accept': 'application/json'
        })
        
        return headers
        
    def _setup_api_key_auth(self, method_config: Dict[str, Any]):
        """Setup Brevo API key authentication."""
        api_key = self.credentials.get('api_key')
        if not api_key:
            raise AuthenticationException("Brevo API key not provided")
            
        # Brevo uses custom header 'api-key'
        self.auth_headers['api-key'] = api_key
        
    # Connection testing
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Brevo API."""
        try:
            # Make a simple API call to verify authentication and connectivity
            response = await self.make_request("GET", "/account")
            
            account_data = response.json()
            
            return {
                "success": True,
                "message": "Successfully connected to Brevo API",
                "account_email": account_data.get("email"),
                "company_name": account_data.get("companyName"),
                "plan": account_data.get("plan", [{}])[0].get("type") if account_data.get("plan") else None,
                "email_credits": account_data.get("plan", [{}])[0].get("creditsType") if account_data.get("plan") else None,
                "sms_credits": account_data.get("plan", [{}])[0].get("credits") if account_data.get("plan") else None
            }
            
        except ExternalAPIError as e:
            return {
                "success": False,
                "error": "API Error",
                "message": f"Brevo API returned error: {e.response_body}",
                "status_code": e.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Connection Error",
                "message": f"Failed to connect to Brevo: {str(e)}"
            }
            
    def get_supported_endpoints(self) -> List[str]:
        """Get list of supported Brevo API endpoints."""
        return [
            "get_account",
            "list_contacts", "create_contact", "get_contact", "update_contact", "delete_contact",
            "list_contact_lists", "create_contact_list", "get_contact_list",
            "list_email_campaigns", "create_email_campaign", "get_email_campaign", "send_email_campaign",
            "send_transactional_email", "list_email_templates", "create_email_template",
            "list_sms_campaigns", "create_sms_campaign", "send_transactional_sms",
            "send_whatsapp_message",
            "get_email_statistics", "get_email_events", "get_email_activity"
        ]
        
    # Account information
    async def get_account(self) -> Dict[str, Any]:
        """Get account information and plan details."""
        response = await self.make_request("GET", "/account")
        return response.json()
        
    # Contact management methods
    async def list_contacts(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        modified_since: Optional[str] = None,
        sort: str = "desc"
    ) -> Dict[str, Any]:
        """List contacts from Brevo account."""
        params = {"sort": sort}
        
        if limit:
            params['limit'] = min(limit, 1000)  # Brevo max is 1000
        if offset:
            params['offset'] = offset
        if modified_since:
            params['modifiedSince'] = modified_since
            
        response = await self.make_request("GET", "/contacts", params=params)
        return response.json()
        
    async def create_contact(
        self,
        email: str,
        attributes: Optional[Dict[str, Any]] = None,
        list_ids: Optional[List[int]] = None,
        update_enabled: bool = False
    ) -> Dict[str, Any]:
        """Create a new contact in Brevo."""
        if not self._is_valid_email(email):
            raise RequestValidationError({"email": "Invalid email format"})
            
        data = {
            "email": email,
            "updateEnabled": update_enabled
        }
        
        if attributes:
            data['attributes'] = attributes
        if list_ids:
            data['listIds'] = list_ids
            
        response = await self.make_request("POST", "/contacts", body=data)
        return response.json()
        
    async def get_contact(self, identifier: str) -> Dict[str, Any]:
        """Retrieve a specific contact by email or ID."""
        if not identifier:
            raise RequestValidationError({"identifier": "Contact identifier is required"})
            
        response = await self.make_request("GET", f"/contacts/{identifier}")
        return response.json()
        
    async def update_contact(
        self,
        identifier: str,
        attributes: Optional[Dict[str, Any]] = None,
        list_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Update an existing contact."""
        if not identifier:
            raise RequestValidationError({"identifier": "Contact identifier is required"})
            
        data = {}
        if attributes:
            data['attributes'] = attributes
        if list_ids:
            data['listIds'] = list_ids
            
        if not data:
            raise RequestValidationError({"data": "At least one field must be provided for update"})
            
        response = await self.make_request("PUT", f"/contacts/{identifier}", body=data)
        return response.json()
        
    async def delete_contact(self, identifier: str) -> Dict[str, Any]:
        """Delete a contact."""
        if not identifier:
            raise RequestValidationError({"identifier": "Contact identifier is required"})
            
        response = await self.make_request("DELETE", f"/contacts/{identifier}")
        return {"success": True, "message": f"Contact {identifier} deleted"}
        
    # Contact list management
    async def list_contact_lists(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort: str = "desc"
    ) -> Dict[str, Any]:
        """List all contact lists."""
        params = {"sort": sort}
        
        if limit:
            params['limit'] = min(limit, 1000)
        if offset:
            params['offset'] = offset
            
        response = await self.make_request("GET", "/contacts/lists", params=params)
        return response.json()
        
    async def create_contact_list(
        self,
        name: str,
        folder_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new contact list."""
        if not name or len(name.strip()) == 0:
            raise RequestValidationError({"name": "List name is required"})
            
        data = {"name": name.strip()}
        
        if folder_id:
            data['folderId'] = folder_id
            
        response = await self.make_request("POST", "/contacts/lists", body=data)
        return response.json()
        
    async def get_contact_list(self, list_id: int) -> Dict[str, Any]:
        """Get a specific contact list."""
        if not list_id:
            raise RequestValidationError({"list_id": "List ID is required"})
            
        response = await self.make_request("GET", f"/contacts/lists/{list_id}")
        return response.json()
        
    # Email campaign methods
    async def list_email_campaigns(
        self,
        campaign_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Dict[str, Any]:
        """List email campaigns."""
        params = {}
        
        if campaign_type:
            params['type'] = campaign_type
        if status:
            params['status'] = status
        if limit:
            params['limit'] = min(limit, 1000)
        if offset:
            params['offset'] = offset
            
        response = await self.make_request("GET", "/emailCampaigns", params=params)
        return response.json()
        
    async def create_email_campaign(
        self,
        name: str,
        subject: str,
        sender: Dict[str, str],
        recipients: Dict[str, Any],
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        scheduled_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an email campaign."""
        if not name or not subject:
            raise RequestValidationError({
                "name": "Campaign name is required",
                "subject": "Subject is required"
            })
            
        data = {
            "name": name,
            "subject": subject,
            "sender": sender,
            "recipients": recipients
        }
        
        if html_content:
            data['htmlContent'] = html_content
        if text_content:
            data['textContent'] = text_content
        if scheduled_at:
            data['scheduledAt'] = scheduled_at
            
        response = await self.make_request("POST", "/emailCampaigns", body=data)
        return response.json()
        
    async def get_email_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Get an email campaign."""
        if not campaign_id:
            raise RequestValidationError({"campaign_id": "Campaign ID is required"})
            
        response = await self.make_request("GET", f"/emailCampaigns/{campaign_id}")
        return response.json()
        
    async def send_email_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Send an email campaign immediately."""
        if not campaign_id:
            raise RequestValidationError({"campaign_id": "Campaign ID is required"})
            
        response = await self.make_request("POST", f"/emailCampaigns/{campaign_id}/sendNow")
        return response.json()
        
    # Transactional email methods
    async def send_transactional_email(
        self,
        to: List[Dict[str, str]],
        sender: Optional[Dict[str, str]] = None,
        subject: Optional[str] = None,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        template_id: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send a transactional email."""
        if not to or len(to) == 0:
            raise RequestValidationError({"to": "At least one recipient is required"})
            
        # Validate email addresses
        for recipient in to:
            if 'email' not in recipient or not self._is_valid_email(recipient['email']):
                raise RequestValidationError({"to": f"Invalid email address: {recipient.get('email', 'missing')}"})
                
        data = {"to": to}
        
        # Use default sender if not provided
        if not sender:
            sender = {
                "email": self.default_sender_email,
                "name": self.default_sender_name
            }
        data['sender'] = sender
        
        if subject:
            data['subject'] = subject
        if html_content:
            data['htmlContent'] = html_content
        if text_content:
            data['textContent'] = text_content
        if template_id:
            data['templateId'] = template_id
        if params:
            data['params'] = params
        if headers:
            data['headers'] = headers
        if tags:
            data['tags'] = tags
            
        response = await self.make_request("POST", "/smtp/email", body=data)
        return response.json()
        
    # Email template methods
    async def list_email_templates(
        self,
        template_status: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Dict[str, Any]:
        """List email templates."""
        params = {}
        
        if template_status is not None:
            params['templateStatus'] = template_status
        if limit:
            params['limit'] = min(limit, 1000)
        if offset:
            params['offset'] = offset
            
        response = await self.make_request("GET", "/smtp/templates", params=params)
        return response.json()
        
    async def create_email_template(
        self,
        template_name: str,
        html_content: str,
        subject: str,
        sender: Dict[str, str],
        text_content: Optional[str] = None,
        tag: Optional[str] = None,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """Create an email template."""
        if not all([template_name, html_content, subject]):
            raise RequestValidationError({
                "template_name": "Template name is required",
                "html_content": "HTML content is required",
                "subject": "Subject is required"
            })
            
        data = {
            "templateName": template_name,
            "htmlContent": html_content,
            "subject": subject,
            "sender": sender,
            "isActive": is_active
        }
        
        if text_content:
            data['textContent'] = text_content
        if tag:
            data['tag'] = tag
            
        response = await self.make_request("POST", "/smtp/templates", body=data)
        return response.json()
        
    # SMS methods
    async def send_transactional_sms(
        self,
        sender: str,
        recipient: str,
        content: str,
        sms_type: str = "transactional",
        tag: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a transactional SMS."""
        if not all([sender, recipient, content]):
            raise RequestValidationError({
                "sender": "Sender is required",
                "recipient": "Recipient is required", 
                "content": "Content is required"
            })
            
        data = {
            "sender": sender,
            "recipient": recipient,
            "content": content,
            "type": sms_type
        }
        
        if tag:
            data['tag'] = tag
            
        response = await self.make_request("POST", "/transactionalSMS/sms", body=data)
        return response.json()
        
    # Statistics methods
    async def get_email_statistics(self, campaign_id: int) -> Dict[str, Any]:
        """Get email campaign statistics."""
        if not campaign_id:
            raise RequestValidationError({"campaign_id": "Campaign ID is required"})
            
        response = await self.make_request("GET", f"/emailCampaigns/{campaign_id}/statistics")
        return response.json()
        
    async def get_email_activity(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
        tag: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get global email activity statistics."""
        params = {}
        
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date
        if days:
            params['days'] = days
        if tag:
            params['tag'] = tag
            
        response = await self.make_request("GET", "/emailActivity", params=params)
        return response.json()
        
    # Webhook handling
    async def handle_webhook(self, headers: Dict[str, str], body: bytes) -> Dict[str, Any]:
        """Handle incoming Brevo webhook."""
        signature = headers.get('x-brevo-signature') or headers.get('X-Brevo-Signature')
        
        if not signature:
            return {
                "success": False,
                "error": "Missing webhook signature"
            }
            
        # Get webhook endpoint secret from credentials
        webhook_secret = self.credentials.get('webhook_secret')
        if not webhook_secret:
            logger.warning("Webhook secret not configured for Brevo")
            return {
                "success": True,
                "message": "Webhook received but signature verification skipped (no secret configured)",
                "event_type": "unknown"
            }
            
        # Verify webhook signature
        try:
            if not self._verify_webhook_signature(body, signature, webhook_secret):
                return {
                    "success": False,
                    "error": "Invalid webhook signature"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Signature verification failed: {str(e)}"
            }
            
        # Parse webhook event
        try:
            event = json.loads(body.decode('utf-8'))
            event_type = event.get('event', 'unknown')
            
            logger.info(f"Received Brevo webhook: {event_type}")
            
            return {
                "success": True,
                "message": f"Webhook processed successfully",
                "event_type": event_type,
                "email": event.get('email'),
                "timestamp": event.get('ts'),
                "data": event
            }
            
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Invalid JSON in webhook body"
            }
            
    def _verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify Brevo webhook signature."""
        try:
            # Brevo uses HMAC-SHA256
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying Brevo webhook signature: {str(e)}")
            return False
            
    def _is_valid_email(self, email: str) -> bool:
        """Validate email address format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
        
    # Helper methods for common operations
    async def create_test_contact(
        self,
        email: str = "test@example.com",
        first_name: str = "Test",
        last_name: str = "User"
    ) -> Dict[str, Any]:
        """Create a test contact for development/testing."""
        return await self.create_contact(
            email=email,
            attributes={
                "FIRSTNAME": first_name,
                "LASTNAME": last_name,
                "SMS": "+1234567890"
            }
        )
        
    async def send_test_email(
        self,
        to_email: str,
        subject: str = "Test Email from API Testing Platform"
    ) -> Dict[str, Any]:
        """Send a test email for development/testing."""
        return await self.send_transactional_email(
            to=[{"email": to_email, "name": "Test Recipient"}],
            subject=subject,
            html_content="""
            <h1>Test Email</h1>
            <p>This is a test email sent from the API Testing Platform.</p>
            <p>If you received this email, the Brevo integration is working correctly!</p>
            """,
            text_content="This is a test email sent from the API Testing Platform. If you received this email, the Brevo integration is working correctly!",
            tags=["api_testing_platform", "test"]
        )
        
    async def get_contact_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get contact by email address."""
        try:
            return await self.get_contact(email)
        except:
            return None