# backend/app/core/env_utils.py
"""
Environment variable utilities for service configuration.
"""

import os
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

def get_env_for_service(service_name: str, key: str, default: Any = None) -> Any:
    """
    Get environment variable for a specific service.
    
    Tries multiple naming conventions:
    1. SERVICE_NAME_KEY (e.g., BREVO_DEFAULT_SENDER_EMAIL)
    2. KEY (e.g., DEFAULT_SENDER_EMAIL)
    
    Args:
        service_name: Name of the service (e.g., 'brevo')
        key: Configuration key (e.g., 'default_sender_email')
        default: Default value if not found
        
    Returns:
        Environment variable value or default
    """
    # Convert to uppercase and replace underscores
    service_upper = service_name.upper()
    key_upper = key.upper()
    
    # Try service-specific variable first
    service_var = f"{service_upper}_{key_upper}"
    value = os.getenv(service_var)
    
    if value is not None:
        logger.debug(f"Found environment variable: {service_var}")
        return value
    
    # Try generic variable
    generic_var = key_upper
    value = os.getenv(generic_var)
    
    if value is not None:
        logger.debug(f"Found environment variable: {generic_var}")
        return value
    
    # Return default
    logger.debug(f"Using default value for {service_name}.{key}: {default}")
    return default

def load_service_env_vars(service_name: str) -> Dict[str, Any]:
    """
    Load all environment variables for a service.
    
    Args:
        service_name: Name of the service
        
    Returns:
        Dictionary of environment variables for the service
    """
    env_vars = {}
    service_prefix = f"{service_name.upper()}_"
    
    for key, value in os.environ.items():
        if key.startswith(service_prefix):
            # Remove service prefix and convert to lowercase
            config_key = key[len(service_prefix):].lower()
            env_vars[config_key] = value
    