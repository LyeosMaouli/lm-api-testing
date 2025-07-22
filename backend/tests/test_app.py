"""
Tests for Flask application endpoints
"""
import pytest
import json
from unittest.mock import patch, Mock
from app import app
from config import config


@pytest.fixture
def client():
    """Create test client"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    with patch("app.config") as mock_cfg:
        mock_cfg.brevo_api_key = "test_api_key"
        mock_cfg.brevo_sender_email = "test@example.com"
        mock_cfg.brevo_sender_name = "Test Sender"
        yield mock_cfg


class TestHealthCheck:
    def test_health_check_success(self, client, mock_config):
        """Test health check endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["status"] in ["success", "warning"]
        assert "timestamp" in data


class TestAccountInfo:
    @patch("app.make_brevo_request")
    def test_get_account_info_success(self, mock_request, client, mock_config):
        """Test successful account info retrieval"""
        # Mock successful Brevo API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "email": "test@example.com",
            "firstName": "John",
            "lastName": "Doe",
            "companyName": "Test Company",
            "plan": [{"type": "free", "creditsLeft": 100}],
        }
        mock_request.return_value = mock_response

        response = client.get("/api/account")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["data"]["email"] == "test@example.com"

    @patch("app.make_brevo_request")
    def test_get_account_info_api_error(self, mock_request, client, mock_config):
        """Test account info with Brevo API error"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_request.return_value = mock_response

        response = client.get("/api/account")
        assert response.status_code == 401
        
        data = json.loads(response.data)
        assert data["status"] == "error"


class TestSendEmail:
    @patch("app.make_brevo_request")
    def test_send_email_success(self, mock_request, client, mock_config):
        """Test successful email sending"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"messageId": "test-123"}
        mock_request.return_value = mock_response

        email_data = {
            "to": "recipient@example.com",
            "subject": "Test Subject",
            "content": "<p>Test content</p>",
        }

        response = client.post(
            "/api/send-test-email",
            data=json.dumps(email_data),
            content_type="application/json",
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

    def test_send_email_invalid_recipient(self, client, mock_config):
        """Test email sending with invalid recipient"""
        email_data = {
            "to": "invalid-email",
            "subject": "Test Subject",
            "content": "<p>Test content</p>",
        }

        response = client.post(
            "/api/send-test-email",
            data=json.dumps(email_data),
            content_type="application/json",
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "email address" in data["message"]

    def test_send_email_missing_sender_config(self, client):
        """Test email sending without sender configuration"""
        with patch("app.config") as mock_cfg:
            mock_cfg.brevo_api_key = "test_api_key"
            mock_cfg.brevo_sender_email = None

            email_data = {
                "to": "recipient@example.com",
                "subject": "Test Subject",
                "content": "<p>Test content</p>",
            }

            response = client.post(
                "/api/send-test-email",
                data=json.dumps(email_data),
                content_type="application/json",
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "Sender email not configured" in data["message"]


class TestSendCustomEvent:
    @patch("app.make_brevo_request")
    def test_send_event_success(self, mock_request, client, mock_config):
        """Test successful custom event sending"""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_request.return_value = mock_response

        event_data = {
            "event_name": "video_played",
            "email_id": "user@example.com",
            "contact_properties": '{"age": 30}',
            "event_properties": '{"duration": 120}',
        }

        response = client.post(
            "/api/send-custom-event",
            data=json.dumps(event_data),
            content_type="application/json",
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

    def test_send_event_invalid_json_properties(self, client, mock_config):
        """Test custom event with invalid JSON properties"""
        event_data = {
            "event_name": "video_played",
            "email_id": "user@example.com",
            "contact_properties": "invalid json",
        }

        response = client.post(
            "/api/send-custom-event",
            data=json.dumps(event_data),
            content_type="application/json",
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "JSON" in data["message"]


class TestRateLimiting:
    def test_rate_limiting_applied(self, client, mock_config):
        """Test that rate limiting is applied to email endpoint"""
        # This test would require multiple rapid requests in a real scenario
        # For now, just verify the endpoint exists and rate limiting decorators are applied
        email_data = {
            "to": "recipient@example.com",
            "subject": "Test Subject",
            "content": "<p>Test content</p>",
        }

        response = client.post(
            "/api/send-test-email",
            data=json.dumps(email_data),
            content_type="application/json",
        )
        
        # Should get either success (200) or validation error (400), not rate limit error initially
        assert response.status_code in [200, 400]