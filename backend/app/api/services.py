"""
API endpoints for service management and discovery.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
import logging

from ..core.config_manager import ConfigManager
from ..core.service_discovery import ServiceRegistry
from ..core.encryption import CredentialManager
from ..core.exceptions import ServiceException, ServiceNotFoundError, ConfigurationException

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for API requests/responses
class ServiceInfo(BaseModel):
    """Service information response model."""
    name: str
    display_name: str
    description: str
    version: str
    documentation_url: Optional[str] = None
    environments: List[str] = Field(default_factory=list)
    authentication_methods: List[str] = Field(default_factory=list)
    endpoints_count: int = 0
    webhooks_supported: bool = False
    loaded: bool = False
    error: Optional[str] = None


class ServiceConfigTemplate(BaseModel):
    """Request model for creating service config template."""
    service_name: str = Field(..., min_length=1, max_length=50)
    display_name: Optional[str] = None
    base_url: Optional[str] = None
    description: Optional[str] = None


class ServiceValidationResult(BaseModel):
    """Service validation result model."""
    service_name: str
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checks: Dict[str, bool] = Field(default_factory=dict)


class CredentialUpdateRequest(BaseModel):
    """Request model for updating service credentials."""
    service_name: str
    environment: str = "production"
    credentials: Dict[str, Any]


# Dependency injection functions - will be set by main.py
_config_manager = None
_service_registry = None
_credential_manager = None

def set_dependencies(config_manager, service_registry, credential_manager):
    """Set the dependency instances (called from main.py)."""
    global _config_manager, _service_registry, _credential_manager
    _config_manager = config_manager
    _service_registry = service_registry
    _credential_manager = credential_manager

def get_config_manager() -> ConfigManager:
    """Get configuration manager."""
    if not _config_manager:
        raise HTTPException(status_code=503, detail="Configuration manager not initialized")
    return _config_manager

def get_service_registry() -> ServiceRegistry:
    """Get service registry."""
    if not _service_registry:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    return _service_registry

def get_credential_manager() -> CredentialManager:
    """Get credential manager."""
    if not _credential_manager:
        raise HTTPException(status_code=503, detail="Credential manager not initialized")
    return _credential_manager


# Service discovery endpoints
@router.get("/", response_model=List[ServiceInfo])
async def list_services(
    include_errors: bool = Query(False, description="Include services with configuration errors"),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    List all available API services.
    
    Returns a list of discovered services with their basic information,
    configuration status, and loading state.
    """
    try:
        services = service_registry.list_available_services()
        
        # Filter out services with errors if requested
        if not include_errors:
            services = [service for service in services if not service.get("error")]
            
        return [ServiceInfo(**service) for service in services]
        
    except Exception as e:
        logger.error(f"Error listing services: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving services list")


@router.get("/{service_name}", response_model=Dict[str, Any])
async def get_service_details(
    service_name: str,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get detailed information about a specific service.
    
    Includes configuration, endpoints, authentication methods,
    and current loading status.
    """
    try:
        service_info = service_registry.get_service_info(service_name)
        return service_info
        
    except ServiceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    except Exception as e:
        logger.error(f"Error getting service details for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving service details")


@router.get("/{service_name}/config")
async def get_service_config(
    service_name: str,
    environment: str = Query("production", description="Environment configuration to retrieve"),
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    Get service configuration for a specific environment.
    
    Returns the complete configuration including authentication methods,
    rate limits, endpoints, and environment-specific settings.
    """
    try:
        env_config = config_manager.get_service_environment_config(service_name, environment)
        return env_config
        
    except ConfigurationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting config for {service_name}/{environment}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving service configuration")


@router.get("/{service_name}/validation", response_model=ServiceValidationResult)
async def validate_service(
    service_name: str,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Validate a service configuration and implementation.
    
    Performs comprehensive validation including:
    - Configuration file validity
    - Service module loading
    - Required dependencies
    - Authentication setup
    """
    try:
        validation_result = service_registry.validate_service(service_name)
        return ServiceValidationResult(**validation_result)
        
    except ServiceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    except Exception as e:
        logger.error(f"Error validating service {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error validating service")


# Service management endpoints
@router.post("/{service_name}/reload")
async def reload_service(
    service_name: str,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Reload a service module and clear cached instances.
    
    Useful for development or when service configuration has changed.
    Forces reloading of the service module and clears any cached instances.
    """
    try:
        success = service_registry.reload_service(service_name)
        
        if success:
            return {
                "message": f"Service '{service_name}' reloaded successfully",
                "service_name": service_name,
                "status": "reloaded"
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to reload service '{service_name}'")
            
    except ServiceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    except Exception as e:
        logger.error(f"Error reloading service {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error reloading service")


@router.post("/template", response_model=Dict[str, str])
async def create_service_template(
    template_request: ServiceConfigTemplate,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    Create a template configuration file for a new service.
    
    Generates a complete YAML configuration template with all required
    sections and common patterns for quick service setup.
    """
    try:
        template_file = config_manager.create_service_config_template(
            service_name=template_request.service_name
        )
        
        return {
            "message": f"Service template created for '{template_request.service_name}'",
            "service_name": template_request.service_name,
            "template_file": template_file,
            "status": "created"
        }
        
    except Exception as e:
        logger.error(f"Error creating service template: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating service template")


# Service instance management
@router.get("/{service_name}/instances")
async def list_service_instances(
    service_name: str,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    List active instances of a service across different environments.
    
    Shows currently loaded service instances with their environment
    and basic status information.
    """
    try:
        service_info = service_registry.get_service_info(service_name)
        instances = service_info.get("instances", [])
        
        instance_details = []
        for instance_key in instances:
            # Parse instance key: service_environment
            parts = instance_key.split('_', 1)
            environment = parts[1] if len(parts) > 1 else "unknown"
            
            instance_details.append({
                "instance_key": instance_key,
                "service_name": service_name,
                "environment": environment,
                "status": "active"
            })
            
        return {
            "service_name": service_name,
            "total_instances": len(instance_details),
            "instances": instance_details
        }
        
    except ServiceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    except Exception as e:
        logger.error(f"Error listing instances for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving service instances")


@router.post("/{service_name}/test-connection")
async def test_service_connection(
    service_name: str,
    environment: str = Query("production", description="Environment to test"),
    credentials: Optional[Dict[str, Any]] = None,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Test connection to a service with provided or stored credentials.
    
    Attempts to establish a connection and authenticate with the service
    to verify that credentials and configuration are working correctly.
    """
    try:
        # Get service instance (will create if needed)
        service_instance = service_registry.get_service_instance(
            service_name=service_name,
            environment=environment,
            credentials=credentials
        )
        
        # Test the connection
        test_result = await service_instance.test_connection()
        
        return {
            "service_name": service_name,
            "environment": environment,
            "connection_test": test_result,
            "timestamp": "2025-07-01T00:00:00Z"  # Would use datetime.utcnow().isoformat()
        }
        
    except ServiceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error testing connection for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error testing service connection")


# Credential management endpoints (delegated to credential manager)
@router.get("/{service_name}/credentials")
async def get_stored_credentials_info(
    service_name: str,
    credential_manager: CredentialManager = Depends(get_credential_manager)
):
    """
    Get information about stored credentials for a service.
    
    Returns metadata about stored credentials without exposing
    the actual credential values for security.
    """
    try:
        stored_credentials = credential_manager.list_stored_credentials()
        service_credentials = stored_credentials.get(service_name, [])
        
        return {
            "service_name": service_name,
            "environments": service_credentials,
            "total_environments": len(service_credentials),
            "has_credentials": len(service_credentials) > 0
        }
        
    except Exception as e:
        logger.error(f"Error getting credential info for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving credential information")


@router.put("/{service_name}/credentials")
async def update_service_credentials(
    service_name: str,
    credential_request: CredentialUpdateRequest,
    credential_manager: CredentialManager = Depends(get_credential_manager),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Update stored credentials for a service and environment.
    
    Encrypts and stores the provided credentials securely.
    Also updates any active service instances with the new credentials.
    """
    try:
        # Store encrypted credentials
        credential_manager.store_credentials(
            service_name=credential_request.service_name,
            credentials=credential_request.credentials,
            environment=credential_request.environment
        )
        
        # Update active service instances if they exist
        try:
            service_instance = service_registry.get_service_instance(
                service_name=credential_request.service_name,
                environment=credential_request.environment,
                credentials=credential_request.credentials
            )
            service_instance.update_credentials(credential_request.credentials)
        except:
            # Instance doesn't exist yet - that's fine
            pass
            
        return {
            "message": f"Credentials updated for {credential_request.service_name}/{credential_request.environment}",
            "service_name": credential_request.service_name,
            "environment": credential_request.environment,
            "status": "updated"
        }
        
    except Exception as e:
        logger.error(f"Error updating credentials for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating service credentials")


@router.delete("/{service_name}/credentials")
async def delete_service_credentials(
    service_name: str,
    environment: str = Query("production", description="Environment credentials to delete"),
    credential_manager: CredentialManager = Depends(get_credential_manager)
):
    """
    Delete stored credentials for a service and environment.
    
    Removes encrypted credentials from storage.
    Active service instances will need to be recreated with new credentials.
    """
    try:
        deleted = credential_manager.delete_credentials(
            service_name=service_name,
            environment=environment
        )
        
        if deleted:
            return {
                "message": f"Credentials deleted for {service_name}/{environment}",
                "service_name": service_name,
                "environment": environment,
                "status": "deleted"
            }
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"No credentials found for {service_name}/{environment}"
            )
            
    except Exception as e:
        logger.error(f"Error deleting credentials for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting service credentials")