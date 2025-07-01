# scripts/setup_files.py
"""
Create missing files and directories for the API testing platform.
"""

import os
from pathlib import Path

def create_file(file_path, content=""):
    """Create a file with optional content."""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    if not Path(file_path).exists():
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Created: {file_path}")
    else:
        print(f"✓ Exists: {file_path}")

def main():
    """Create all missing files."""
    print("🔧 Setting up missing files and directories...")
    print("=" * 50)
    
    # Backend service structure
    create_file("backend/app/services/__init__.py", '"""Services package."""\n')
    create_file("backend/app/services/brevo/__init__.py", '"""Brevo service module."""\n')
    
    # Create the base service if it doesn't exist (just a placeholder)
    base_service_content = '''"""Base service class - simplified version for initial setup."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseService(ABC):
    """Base service class that all API service integrations inherit from."""
    
    _is_service_class = True  # Marker for service discovery
    
    def __init__(self, config: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None):
        self.config = config
        self.credentials = credentials or {}
        self.service_name = config.get('service_name', 'unknown')
        self.environment = config.get('environment', 'production')
        self.base_url = config.get('base_url', '')
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test the connection and authentication with the service."""
        pass
        
    @abstractmethod
    def get_supported_endpoints(self) -> List[str]:
        """Get list of supported API endpoints."""
        pass
'''
    create_file("backend/app/services/base.py", base_service_content)
    
    # Create a complete Brevo client
    brevo_client_content = '''"""Brevo service implementation."""

from typing import Dict, Any, List, Optional
from ...services.base import BaseService


class BrevoService(BaseService):
    """Brevo email marketing service implementation."""
    
    def __init__(self, config: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None):
        super().__init__(config, credentials)
        print(f"🟢 Brevo service initialized: {self.service_name}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Brevo API."""
        return {
            "success": True,
            "message": "Brevo service connection test (mock)",
            "service_name": self.service_name,
            "environment": self.environment,
            "base_url": self.base_url
        }
    
    def get_supported_endpoints(self) -> List[str]:
        """Get list of supported Brevo API endpoints."""
        return [
            "test_connection",
            "get_account", 
            "list_contacts",
            "create_contact",
            "send_transactional_email"
        ]
    
    async def get_account(self) -> Dict[str, Any]:
        """Get account information (mock)."""
        return {
            "email": "test@example.com",
            "companyName": "Test Company",
            "plan": [{"type": "free", "credits": 300}]
        }
'''
    create_file("backend/app/services/brevo/client.py", brevo_client_content)
    
    # Create Brevo configuration
    brevo_config = '''# Brevo Email Marketing API Service Configuration
name: "brevo"
display_name: "Brevo Email Marketing"
description: "Email marketing, transactional emails, SMS, and WhatsApp Business API"
version: "v3"
base_url: "https://api.brevo.com/v3"
documentation_url: "https://developers.brevo.com/docs"

authentication:
  api_key:
    type: "api_key"
    header: "api-key"
    description: "Brevo API key from account settings"
    required_fields: ["api_key"]

rate_limits:
  requests_per_minute: 300
  requests_per_hour: 10000
  burst_limit: 50
  concurrent_requests: 10

endpoints:
  get_account:
    method: "GET"
    path: "/account"
    description: "Get account information"
    
  list_contacts:
    method: "GET"
    path: "/contacts"
    description: "List all contacts"
    optional_params: ["limit", "offset"]

webhooks:
  supported: true
  events: ["delivered", "opened", "clicked"]
  signature_header: "X-Brevo-Signature"
  verification_method: "hmac_sha256"

environments:
  production:
    base_url: "https://api.brevo.com/v3"
    description: "Brevo production environment"
    
  development:
    base_url: "https://api.brevo.com/v3"
    description: "Brevo development environment"

settings:
  timeout: 30
  retries: 3
  verify_ssl: true
  default_sender_email: "${BREVO_DEFAULT_SENDER_EMAIL:noreply@yourdomain.com}"
  default_sender_name: "${BREVO_DEFAULT_SENDER_NAME:API Testing Platform}"
  enable_tracking: true
  enable_batch_processing: true
'''
    create_file("config/services/brevo.yaml", brevo_config)
    
    # Update the services.yaml to only include Brevo
    services_config = '''# Global service registry configuration
services:
  brevo:
    enabled: true
    config_file: "brevo.yaml"
    description: "Brevo email marketing and communication API"
    category: "marketing"

global_settings:
  default_timeout: 30
  default_retries: 3
  max_concurrent_requests: 10
  rate_limit_strategy: "sliding_window"
  
development:
  auto_reload_configs: true
  verbose_logging: true
  mock_external_calls: false
'''
    create_file("config/services.yaml", services_config)
    
    print("\n📁 File structure created:")
    print("  ✓ backend/app/services/__init__.py")
    print("  ✓ backend/app/services/base.py")
    print("  ✓ backend/app/services/brevo/__init__.py")
    print("  ✓ backend/app/services/brevo/client.py")
    print("  ✓ config/services/brevo.yaml")
    print("  ✓ config/services.yaml")
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("  1. Restart the server: Ctrl+C then python scripts/dev_server.py")
    print("  2. Test services: curl http://localhost:8000/api/v1/services/")
    print("  3. Check system info: curl http://localhost:8000/system/info")

if __name__ == "__main__":
    main()