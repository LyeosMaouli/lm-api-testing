# tests/test_brevo_service.py
"""
Test the Brevo service integration.
"""

import pytest
from unittest.mock import AsyncMock, patch
from backend.app.services.brevo.client import BrevoService

@pytest.fixture
def brevo_config():
    """Brevo service configuration for testing."""
    return {
        "service_name": "brevo",
        "environment": "production",
        "base_url": "https://api.brevo.com/v3",
        "authentication": {
            "api_key": {
                "type": "api_key",
                "required_fields": ["api_key"]
            }
        },
        "rate_limits": {
            "requests_per_minute": 300
        }
    }

@pytest.fixture
def brevo_credentials():
    """Test credentials for Brevo."""
    return {
        "api_key": "xkeysib-fake_key_for_testing-123456789"
    }

def test_brevo_service_initialization(brevo_config, brevo_credentials):
    """Test Brevo service initialization."""
    service = BrevoService(brevo_config, brevo_credentials)
    
    assert service.service_name == "brevo"
    assert service.environment == "production"
    assert service.base_url == "https://api.brevo.com/v3"

def test_brevo_service_supported_endpoints(brevo_config):
    """Test that Brevo service returns supported endpoints."""
    service = BrevoService(brevo_config)
    endpoints = service.get_supported_endpoints()
    
    assert isinstance(endpoints, list)
    assert len(endpoints) > 0
    assert "list_contacts" in endpoints
    assert "create_contact" in endpoints
    assert "send_transactional_email" in endpoints

@pytest.mark.asyncio
async def test_brevo_service_test_connection_mock(brevo_config, brevo_credentials):
    """Test Brevo connection with mocked response."""
    service = BrevoService(brevo_config, brevo_credentials)
    
    # Mock the make_request method
    with patch.object(service, 'make_request') as mock_request:
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "email": "test@example.com",
            "companyName": "Test Company",
            "plan": [{
                "type": "free",
                "creditsType": "sendLimit",
                "credits": 300
            }]
        }
        mock_request.return_value = mock_response
        
        # Test connection
        result = await service.test_connection()
        
        assert result["success"] is True
        assert result["account_email"] == "test@example.com"
        assert result["company_name"] == "Test Company"

@pytest.mark.asyncio
async def test_brevo_email_validation(brevo_config):
    """Test email validation helper method."""
    service = BrevoService(brevo_config)
    
    # Valid emails
    assert service._is_valid_email("test@example.com") is True
    assert service._is_valid_email("user.name+tag@example.co.uk") is True
    
    # Invalid emails
    assert service._is_valid_email("invalid-email") is False
    assert service._is_valid_email("@example.com") is False
    assert service._is_valid_email("test@") is False

@pytest.mark.asyncio
async def test_brevo_create_contact_validation(brevo_config, brevo_credentials):
    """Test contact creation with validation."""
    service = BrevoService(brevo_config, brevo_credentials)
    
    # Test with invalid email
    with pytest.raises(Exception):  # Should raise RequestValidationError
        await service.create_contact("invalid-email")

# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])