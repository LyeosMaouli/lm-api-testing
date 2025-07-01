# backend/app/core/service_discovery.py
"""
Service discovery and management system.
Automatically discovers and loads service modules with plugin-style architecture.
"""

import os
import importlib
import inspect
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
import logging

from .config_manager import ConfigManager, ServiceConfig
from .exceptions import ServiceException, ServiceNotFoundError, ServiceConfigurationError

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """
    Registry for managing available API service modules.
    Provides plugin-style architecture for service discovery and loading.
    """
    
    def __init__(self, services_dir: str, config_manager: ConfigManager):
        self.services_dir = Path(services_dir)
        self.config_manager = config_manager
        self._services: Dict[str, Type] = {}
        self._service_instances: Dict[str, Any] = {}
        self._loaded_services: Dict[str, ServiceConfig] = {}
        
    def discover_services(self) -> List[str]:
        """
        Discover all available service modules in the services directory.
        
        Returns:
            List of discovered service names
        """
        discovered_services = []
        
        if not self.services_dir.exists():
            logger.warning(f"Services directory not found: {self.services_dir}")
            return discovered_services
            
        # Look for Python packages in services directory
        for item in self.services_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                # Check if it's a valid Python package
                init_file = item / "__init__.py"
                client_file = item / "client.py"
                
                if init_file.exists() and client_file.exists():
                    discovered_services.append(item.name)
                    logger.debug(f"Discovered service: {item.name}")
                    
        return sorted(discovered_services)
        
    def load_service_module(self, service_name: str) -> Type:
        """
        Dynamically load a service module.
        
        Args:
            service_name: Name of the service to load
            
        Returns:
            Service class type
            
        Raises:
            ServiceException: If service cannot be loaded
        """
        if service_name in self._services:
            return self._services[service_name]
            
        try:
            # Import the service module
            module_path = f"app.services.{service_name}.client"
            logger.info(f"Attempting to load service module: {module_path}")
            module = importlib.import_module(module_path)
            
            # Find the service class (should inherit from BaseService)
            service_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                logger.debug(f"Found class: {name} in module {module_path}")
                if (hasattr(obj, '__module__') and 
                    obj.__module__ == module_path and 
                    hasattr(obj, '_is_service_class')):
                    service_class = obj
                    logger.info(f"Found service class with marker: {name}")
                    break
                    
            if service_class is None:
                # Fallback: look for class ending with 'Service' or 'Client'
                logger.warning(f"No service class with marker found, trying fallback for {service_name}")
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (name.endswith(('Service', 'Client')) and 
                        hasattr(obj, '__module__') and 
                        obj.__module__ == module_path):
                        service_class = obj
                        logger.info(f"Found service class by name pattern: {name}")
                        break
                        
            if service_class is None:
                available_classes = [name for name, obj in inspect.getmembers(module, inspect.isclass)
                                   if hasattr(obj, '__module__') and obj.__module__ == module_path]
                raise ServiceException(f"No service class found in {module_path}. Available classes: {available_classes}")
                
            self._services[service_name] = service_class
            logger.info(f"Successfully loaded service module: {service_name} -> {service_class.__name__}")
            
            return service_class
            
        except ImportError as e:
            logger.error(f"Failed to import service {service_name}: {str(e)}")
            raise ServiceException(f"Failed to import service {service_name}: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading service {service_name}: {str(e)}")
            raise ServiceException(f"Error loading service {service_name}: {str(e)}")
            
    def get_service_instance(
        self, 
        service_name: str, 
        environment: str = "production",
        credentials: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Get or create a service instance.
        
        Args:
            service_name: Name of the service
            environment: Environment name
            credentials: Service credentials
            
        Returns:
            Service instance
        """
        instance_key = f"{service_name}_{environment}"
        
        if instance_key in self._service_instances:
            instance = self._service_instances[instance_key]
            # Update credentials if provided
            if credentials and hasattr(instance, 'update_credentials'):
                instance.update_credentials(credentials)
            return instance
            
        # Load service configuration
        try:
            config = self.config_manager.load_service_config(service_name)
            self._loaded_services[service_name] = config
        except Exception as e:
            raise ServiceConfigurationError(service_name, str(e))
            
        # Load service class
        service_class = self.load_service_module(service_name)
        
        # Get environment-specific configuration
        env_config = self.config_manager.get_service_environment_config(
            service_name, environment
        )
        
        # Create service instance
        try:
            instance = service_class(
                config=env_config,
                credentials=credentials
            )
            
            self._service_instances[instance_key] = instance
            logger.info(f"Created service instance: {instance_key}")
            
            return instance
            
        except Exception as e:
            raise ServiceException(f"Failed to create service instance {service_name}: {str(e)}")
            
    def list_available_services(self) -> List[Dict[str, Any]]:
        """
        List all available services with their configurations.
        
        Returns:
            List of service information dictionaries
        """
        services = []
        discovered = self.discover_services()
        
        for service_name in discovered:
            try:
                config = self.config_manager.load_service_config(service_name)
                
                service_info = {
                    "name": service_name,
                    "display_name": config.display_name,
                    "description": config.description,
                    "version": config.version,
                    "documentation_url": config.documentation_url,
                    "environments": list(config.environments.keys()),
                    "authentication_methods": list(config.authentication.keys()),
                    "endpoints_count": len(config.endpoints),
                    "webhooks_supported": config.webhooks.supported if config.webhooks else False,
                    "loaded": service_name in self._services
                }
                
                services.append(service_info)
                
            except Exception as e:
                logger.error(f"Error loading config for service {service_name}: {str(e)}")
                services.append({
                    "name": service_name,
                    "display_name": service_name.title(),
                    "description": f"Configuration error: {str(e)}",
                    "version": "unknown",
                    "documentation_url": None,
                    "environments": [],
                    "authentication_methods": [],
                    "endpoints_count": 0,
                    "webhooks_supported": False,
                    "loaded": False,
                    "error": str(e)
                })
                
        return services
        
    def get_service_info(self, service_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service information dictionary
        """
        if service_name not in self.discover_services():
            raise ServiceNotFoundError(service_name)
            
        try:
            config = self.config_manager.load_service_config(service_name)
            
            # Get service class information if loaded
            service_class_info = {}
            if service_name in self._services:
                service_class = self._services[service_name]
                service_class_info = {
                    "class_name": service_class.__name__,
                    "module": service_class.__module__,
                    "methods": [method for method in dir(service_class) 
                              if not method.startswith('_') and callable(getattr(service_class, method))]
                }
                
            return {
                "name": service_name,
                "display_name": config.display_name,
                "description": config.description,
                "version": config.version,
                "base_url": config.base_url,
                "documentation_url": config.documentation_url,
                "authentication": {
                    name: {
                        "type": method.type,
                        "description": method.description,
                        "required_fields": method.required_fields
                    }
                    for name, method in config.authentication.items()
                },
                "rate_limits": config.rate_limits.dict() if config.rate_limits else None,
                "endpoints": {
                    name: {
                        "method": endpoint.method,
                        "path": endpoint.path,
                        "description": endpoint.description,
                        "required_params": endpoint.required_params,
                        "optional_params": endpoint.optional_params
                    }
                    for name, endpoint in config.endpoints.items()
                },
                "webhooks": config.webhooks.dict() if config.webhooks else None,
                "environments": {
                    name: {
                        "base_url": env.base_url,
                        "description": env.description
                    }
                    for name, env in config.environments.items()
                },
                "settings": config.settings,
                "class_info": service_class_info,
                "loaded": service_name in self._services,
                "instances": [key for key in self._service_instances.keys() 
                            if key.startswith(f"{service_name}_")]
            }
            
        except Exception as e:
            raise ServiceException(f"Error getting service info for {service_name}: {str(e)}")
            
    def validate_service(self, service_name: str) -> Dict[str, Any]:
        """
        Validate a service configuration and implementation.
        
        Args:
            service_name: Name of the service to validate
            
        Returns:
            Validation results dictionary
        """
        validation_results = {
            "service_name": service_name,
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks": {}
        }
        
        try:
            # Check if service exists
            if service_name not in self.discover_services():
                validation_results["valid"] = False
                validation_results["errors"].append(f"Service {service_name} not found")
                return validation_results
                
            validation_results["checks"]["service_exists"] = True
            
            # Validate configuration
            config_validation = self.config_manager.validate_service_config(service_name)
            validation_results["checks"]["config_valid"] = config_validation["valid"]
            
            if not config_validation["valid"]:
                validation_results["valid"] = False
                validation_results["errors"].extend(config_validation["errors"])
                
            validation_results["warnings"].extend(config_validation["warnings"])
            
            # Try to load service module
            try:
                self.load_service_module(service_name)
                validation_results["checks"]["module_loadable"] = True
            except Exception as e:
                validation_results["valid"] = False
                validation_results["errors"].append(f"Cannot load service module: {str(e)}")
                validation_results["checks"]["module_loadable"] = False
                
            # Try to create service instance (without credentials)
            if validation_results["checks"]["module_loadable"]:
                try:
                    config = self.config_manager.load_service_config(service_name)
                    env_config = self.config_manager.get_service_environment_config(
                        service_name, "production"
                    )
                    
                    service_class = self._services[service_name]
                    # Try to instantiate without credentials (should not fail)
                    service_class(config=env_config, credentials=None)
                    validation_results["checks"]["instance_creatable"] = True
                    
                except Exception as e:
                    validation_results["warnings"].append(
                        f"Cannot create service instance without credentials: {str(e)}"
                    )
                    validation_results["checks"]["instance_creatable"] = False
                    
        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Validation error: {str(e)}")
            
        return validation_results
        
    def reload_service(self, service_name: str) -> bool:
        """
        Reload a service module and clear cached instances.
        
        Args:
            service_name: Name of the service to reload
            
        Returns:
            True if reload successful
        """
        try:
            # Clear cached instances
            keys_to_remove = [key for key in self._service_instances.keys() 
                            if key.startswith(f"{service_name}_")]
            for key in keys_to_remove:
                del self._service_instances[key]
                
            # Clear cached service class
            if service_name in self._services:
                del self._services[service_name]
                
            # Clear cached config
            if service_name in self._loaded_services:
                del self._loaded_services[service_name]
                
            # Reload configuration
            self.config_manager.reload_service_config(service_name)
            
            # Reload module
            self.load_service_module(service_name)
            
            logger.info(f"Successfully reloaded service: {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload service {service_name}: {str(e)}")
            return False