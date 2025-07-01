# backend/app/core/config_manager.py
"""
Configuration management system for API testing platform.
Handles service configurations, application settings, and environment management.
"""

import os
import yaml
import re
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings

from .exceptions import ConfigurationException


def substitute_env_vars(value: Any) -> Any:
    """
    Substitute environment variables in configuration values.
    
    Supports syntax: ${VAR_NAME:default_value} or ${VAR_NAME}
    
    Args:
        value: Configuration value that may contain environment variable references
        
    Returns:
        Value with environment variables substituted
    """
    if not isinstance(value, str):
        return value
        
    # Pattern to match ${VAR_NAME:default_value} or ${VAR_NAME}
    pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
    
    def replace_env_var(match):
        var_name = match.group(1)
        default_value = match.group(2) if match.group(2) is not None else ""
        env_value = os.getenv(var_name, default_value)
        return env_value
    
    try:
        return re.sub(pattern, replace_env_var, value)
    except Exception as e:
        # If substitution fails, return original value
        return value


def process_config_dict(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively process a configuration dictionary to substitute environment variables.
    
    Args:
        config_dict: Configuration dictionary
        
    Returns:
        Processed configuration with environment variables substituted
    """
    if config_dict is None:
        return {}
        
    if isinstance(config_dict, dict):
        return {key: process_config_dict(value) for key, value in config_dict.items()}
    elif isinstance(config_dict, list):
        return [process_config_dict(item) for item in config_dict]
    elif isinstance(config_dict, str):
        return substitute_env_vars(config_dict)
    else:
        return config_dict


class AuthMethod(BaseModel):
    """Authentication method configuration."""
    type: str = Field(..., description="Authentication type (api_key, oauth2, jwt, basic)")
    header: Optional[str] = Field(None, description="Header name for API key")
    parameter: Optional[str] = Field(None, description="Query parameter name")
    description: str = Field("", description="Human-readable description")
    required_fields: List[str] = Field(default_factory=list, description="Required credential fields")
    oauth_config: Optional[Dict[str, Any]] = Field(None, description="OAuth-specific configuration")


class RateLimit(BaseModel):
    """Rate limiting configuration."""
    requests_per_minute: Optional[int] = Field(None, description="Requests per minute limit")
    requests_per_hour: Optional[int] = Field(None, description="Requests per hour limit")
    requests_per_day: Optional[int] = Field(None, description="Requests per day limit")
    burst_limit: Optional[int] = Field(None, description="Burst request limit")
    concurrent_requests: Optional[int] = Field(None, description="Max concurrent requests")


class ServiceEndpoint(BaseModel):
    """API endpoint configuration."""
    method: str = Field(..., description="HTTP method")
    path: str = Field(..., description="URL path")
    description: str = Field("", description="Endpoint description")
    required_params: List[str] = Field(default_factory=list, description="Required parameters")
    optional_params: List[str] = Field(default_factory=list, description="Optional parameters")
    request_schema: Optional[Dict[str, Any]] = Field(None, description="Request schema")
    response_schema: Optional[Dict[str, Any]] = Field(None, description="Response schema")


class WebhookConfig(BaseModel):
    """Webhook configuration."""
    supported: bool = Field(False, description="Whether service supports webhooks")
    events: List[str] = Field(default_factory=list, description="Supported webhook events")
    signature_header: Optional[str] = Field(None, description="Webhook signature header")
    verification_method: Optional[str] = Field(None, description="Signature verification method")


class ServiceEnvironment(BaseModel):
    """Service environment configuration."""
    name: str = Field(..., description="Environment name")
    base_url: str = Field(..., description="Base URL for this environment")
    description: Optional[str] = Field(None, description="Environment description")
    rate_limits: Optional[RateLimit] = Field(None, description="Environment-specific rate limits")


class ServiceConfig(BaseModel):
    """Complete service configuration."""
    name: str = Field(..., description="Service name")
    display_name: str = Field(..., description="Human-readable service name")
    description: str = Field("", description="Service description")
    version: str = Field("v1", description="API version")
    base_url: str = Field(..., description="Default base URL")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")
    
    # Authentication
    authentication: Dict[str, AuthMethod] = Field(default_factory=dict, description="Authentication methods")
    
    # Rate limiting
    rate_limits: Optional[RateLimit] = Field(None, description="Default rate limits")
    
    # API endpoints
    endpoints: Dict[str, ServiceEndpoint] = Field(default_factory=dict, description="API endpoints")
    
    # Webhooks
    webhooks: Optional[WebhookConfig] = Field(None, description="Webhook configuration")
    
    # Environments
    environments: Dict[str, ServiceEnvironment] = Field(default_factory=dict, description="Service environments")
    
    # Service-specific settings
    settings: Dict[str, Any] = Field(default_factory=dict, description="Additional service settings")
    
    @validator('authentication')
    def validate_auth_methods(cls, v):
        """Validate authentication method configurations."""
        for method_name, method_config in v.items():
            if method_config.type not in ['api_key', 'oauth2', 'jwt', 'basic', 'bearer']:
                raise ValueError(f"Unsupported authentication type: {method_config.type}")
        return v


class AppSettings(BaseSettings):
    """Application settings from environment variables."""
    
    # Application
    app_name: str = "API Testing Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True
    
    # Security
    secret_key: str = Field(default_factory=lambda: os.urandom(32).hex())
    access_token_expire_minutes: int = 30
    
    # Storage
    data_dir: str = "./data"
    config_dir: str = "./config"
    log_dir: str = "./data/logs"
    
    # Database
    database_url: str = "sqlite:///./data/app.db"
    redis_url: Optional[str] = None
    
    # External services
    webhook_base_url: str = "http://localhost:8000"
    ngrok_enabled: bool = False
    
    class Config:
        env_file = ".env"
        env_prefix = "API_TESTING_"


class ConfigManager:
    """
    Manages configuration loading and caching for services and application.
    """
    
    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self._service_configs: Dict[str, ServiceConfig] = {}
        self._app_settings: Optional[AppSettings] = None
        
    def load_app_settings(self) -> AppSettings:
        """Load and cache application settings."""
        if self._app_settings is None:
            self._app_settings = AppSettings()
        return self._app_settings
        
    def load_service_config(self, service_name: str) -> ServiceConfig:
        """
        Load service configuration from YAML file.
        
        Args:
            service_name: Name of the service to load
            
        Returns:
            ServiceConfig object
            
        Raises:
            ConfigurationException: If config file not found or invalid
        """
        if service_name in self._service_configs:
            return self._service_configs[service_name]
            
        config_file = self.config_dir / "services" / f"{service_name}.yaml"
        
        if not config_file.exists():
            raise ConfigurationException(
                f"Service configuration not found: {config_file}",
                {"service_name": service_name, "config_file": str(config_file)}
            )
            
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                
            # Check if config_data is None (empty file)
            if config_data is None:
                raise ConfigurationException(
                    f"Configuration file is empty or invalid: {config_file}",
                    {"service_name": service_name, "config_file": str(config_file)}
                )
                
            # Process environment variable substitutions
            config_data = process_config_dict(config_data)
            
            # Validate that config_data is a dictionary
            if not isinstance(config_data, dict):
                raise ConfigurationException(
                    f"Configuration file must contain a dictionary, got {type(config_data).__name__}: {config_file}",
                    {"service_name": service_name, "config_file": str(config_file)}
                )
                
            # Parse authentication methods
            if 'authentication' in config_data:
                auth_methods = {}
                for method_name, method_data in config_data['authentication'].items():
                    auth_methods[method_name] = AuthMethod(**method_data)
                config_data['authentication'] = auth_methods
                
            # Parse rate limits
            if 'rate_limits' in config_data:
                config_data['rate_limits'] = RateLimit(**config_data['rate_limits'])
                
            # Parse endpoints
            if 'endpoints' in config_data:
                endpoints = {}
                for endpoint_name, endpoint_data in config_data['endpoints'].items():
                    endpoints[endpoint_name] = ServiceEndpoint(**endpoint_data)
                config_data['endpoints'] = endpoints
                
            # Parse webhook config
            if 'webhooks' in config_data:
                config_data['webhooks'] = WebhookConfig(**config_data['webhooks'])
                
            # Parse environments
            if 'environments' in config_data:
                environments = {}
                for env_name, env_data in config_data['environments'].items():
                    env_data['name'] = env_name
                    if 'rate_limits' in env_data:
                        env_data['rate_limits'] = RateLimit(**env_data['rate_limits'])
                    environments[env_name] = ServiceEnvironment(**env_data)
                config_data['environments'] = environments
                
            # Create service config
            service_config = ServiceConfig(**config_data)
            self._service_configs[service_name] = service_config
            
            return service_config
            
        except yaml.YAMLError as e:
            raise ConfigurationException(
                f"Invalid YAML in service config: {str(e)}",
                {"service_name": service_name, "yaml_error": str(e)}
            )
        except Exception as e:
            raise ConfigurationException(
                f"Error loading service config: {str(e)}",
                {"service_name": service_name, "error": str(e)}
            )
            
    def get_service_config(self, service_name: str) -> Optional[ServiceConfig]:
        """Get cached service configuration or None if not loaded."""
        return self._service_configs.get(service_name)
        
    def list_available_services(self) -> List[str]:
        """List all available service configurations."""
        services_dir = self.config_dir / "services"
        if not services_dir.exists():
            return []
            
        services = []
        for config_file in services_dir.glob("*.yaml"):
            if config_file.is_file():
                services.append(config_file.stem)
                
        return sorted(services)
        
    def reload_service_config(self, service_name: str) -> ServiceConfig:
        """Force reload of service configuration."""
        if service_name in self._service_configs:
            del self._service_configs[service_name]
        return self.load_service_config(service_name)
        
    def create_service_config_template(self, service_name: str) -> str:
        """
        Create a template configuration file for a new service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Path to created template file
        """
        services_dir = self.config_dir / "services"
        services_dir.mkdir(parents=True, exist_ok=True)
        
        template_file = services_dir / f"{service_name}.yaml"
        
        template_content = f"""# {service_name.title()} API Service Configuration
name: "{service_name}"
display_name: "{service_name.title()}"
description: "API integration for {service_name.title()}"
version: "v1"
base_url: "https://api.{service_name}.com/v1"
documentation_url: "https://docs.{service_name}.com/api"

# Authentication methods supported by this service
authentication:
  api_key:
    type: "api_key"
    header: "Authorization"
    description: "API key authentication"
    required_fields: ["api_key"]
  
  # oauth2:
  #   type: "oauth2"
  #   description: "OAuth2 authorization code flow"
  #   required_fields: ["client_id", "client_secret"]
  #   oauth_config:
  #     authorization_url: "https://auth.{service_name}.com/oauth/authorize"
  #     token_url: "https://auth.{service_name}.com/oauth/token"
  #     scopes: ["read", "write"]

# Rate limiting configuration
rate_limits:
  requests_per_minute: 60
  requests_per_hour: 1000
  burst_limit: 10
  concurrent_requests: 5

# API endpoints
endpoints:
  list_items:
    method: "GET"
    path: "/items"
    description: "List all items"
    optional_params: ["limit", "offset"]
    
  create_item:
    method: "POST"
    path: "/items"
    description: "Create a new item"
    required_params: ["name"]
    optional_params: ["description"]

# Webhook configuration
webhooks:
  supported: false
  events: []
  signature_header: "X-{service_name.title()}-Signature"
  verification_method: "hmac_sha256"

# Environment configurations
environments:
  production:
    base_url: "https://api.{service_name}.com/v1"
    description: "Production environment"
    
  sandbox:
    base_url: "https://sandbox-api.{service_name}.com/v1"
    description: "Sandbox/testing environment"
    rate_limits:
      requests_per_minute: 30
      requests_per_hour: 500

# Additional service-specific settings
settings:
  timeout: 30
  retries: 3
  verify_ssl: true
"""
        
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
            
        return str(template_file)
        
    def validate_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        Validate a service configuration and return validation results.
        
        Args:
            service_name: Name of the service to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            config = self.load_service_config(service_name)
            
            validation_results = {
                "valid": True,
                "service_name": service_name,
                "config": config.dict(),
                "warnings": [],
                "errors": []
            }
            
            # Check for common issues
            if not config.authentication:
                validation_results["warnings"].append("No authentication methods configured")
                
            if not config.endpoints:
                validation_results["warnings"].append("No API endpoints configured")
                
            if config.webhooks and config.webhooks.supported and not config.webhooks.events:
                validation_results["warnings"].append("Webhooks enabled but no events configured")
                
            # Validate URLs
            if not config.base_url.startswith(('http://', 'https://')):
                validation_results["errors"].append("Invalid base_url: must start with http:// or https://")
                
            return validation_results
            
        except ConfigurationException as e:
            return {
                "valid": False,
                "service_name": service_name,
                "config": None,
                "warnings": [],
                "errors": [e.message]
            }
            
    def get_service_environment_config(
        self, 
        service_name: str, 
        environment: str = "production"
    ) -> Dict[str, Any]:
        """
        Get configuration for a specific service environment.
        
        Args:
            service_name: Name of the service
            environment: Environment name (default: "production")
            
        Returns:
            Dictionary with environment-specific configuration
        """
        config = self.load_service_config(service_name)
        
        # Start with base configuration
        env_config = {
            "service_name": service_name,
            "environment": environment,
            "base_url": config.base_url,
            "rate_limits": config.rate_limits.dict() if config.rate_limits else None,
            "authentication": {name: method.dict() for name, method in config.authentication.items()},
            "webhooks": config.webhooks.dict() if config.webhooks else None,
            "settings": config.settings
        }
        
        # Override with environment-specific settings
        if environment in config.environments:
            env = config.environments[environment]
            env_config["base_url"] = env.base_url
            env_config["description"] = env.description
            
            if env.rate_limits:
                env_config["rate_limits"] = env.rate_limits.dict()
                
        return env_config