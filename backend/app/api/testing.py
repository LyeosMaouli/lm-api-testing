# backend/app/api/testing.py
"""
API endpoints for executing API tests and managing requests.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
import logging

from ..core.service_discovery import ServiceRegistry
from ..core.rate_limiter import rate_limiter
from ..core.exceptions import (
    ServiceException, 
    ServiceNotFoundError, 
    RateLimitException,
    AuthenticationException
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency injection - will be set by main.py
_service_registry = None

def set_dependencies(service_registry):
    """Set the dependency instances (called from main.py)."""
    global _service_registry
    _service_registry = service_registry

def get_service_registry() -> ServiceRegistry:
    """Get service registry."""
    if not _service_registry:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    return _service_registry


# Request/Response models
class APITestRequest(BaseModel):
    """API test request model."""
    service_name: str = Field(..., description="Name of the service to test")
    environment: str = Field("production", description="Environment to use")
    endpoint: str = Field(..., description="API endpoint to call")
    method: str = Field("GET", description="HTTP method")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Request parameters")
    headers: Dict[str, str] = Field(default_factory=dict, description="Additional headers")
    body: Optional[Union[Dict, str]] = Field(None, description="Request body")
    credentials: Optional[Dict[str, Any]] = Field(None, description="Service credentials")


class APITestResponse(BaseModel):
    """API test response model."""
    success: bool
    service_name: str
    environment: str
    endpoint: str
    method: str
    status_code: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    response_headers: Dict[str, str] = Field(default_factory=dict)
    duration: Optional[float] = None
    error: Optional[str] = None
    request_id: str


class BatchTestRequest(BaseModel):
    """Batch API test request model."""
    requests: List[APITestRequest] = Field(..., min_items=1, max_items=10)
    parallel: bool = Field(False, description="Execute requests in parallel")
    stop_on_error: bool = Field(False, description="Stop batch if any request fails")


class ServiceMethodRequest(BaseModel):
    """Service method call request."""
    service_name: str
    environment: str = "production"
    method_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    credentials: Optional[Dict[str, Any]] = None


# Single API test endpoint
@router.post("/execute", response_model=APITestResponse)
async def execute_api_test(
    test_request: APITestRequest,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Execute a single API test request.
    
    Performs a direct API call to the specified service endpoint
    with the provided parameters and credentials.
    """
    request_id = f"{test_request.service_name}_{test_request.endpoint}_{hash(str(test_request.dict()))}"
    
    try:
        # Get service instance
        service_instance = service_registry.get_service_instance(
            service_name=test_request.service_name,
            environment=test_request.environment,
            credentials=test_request.credentials
        )
        
        # Wait for rate limiting
        await rate_limiter.wait_for_rate_limit(
            test_request.service_name, 
            test_request.endpoint
        )
        
        # Execute the API call
        start_time = asyncio.get_event_loop().time()
        
        try:
            response = await service_instance.make_request(
                method=test_request.method,
                endpoint=test_request.endpoint,
                params=test_request.parameters,
                headers=test_request.headers,
                body=test_request.body
            )
            
            duration = asyncio.get_event_loop().time() - start_time
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
                
            # Record successful request
            await rate_limiter.end_request(
                test_request.service_name, 
                test_request.endpoint, 
                success=True
            )
            
            return APITestResponse(
                success=True,
                service_name=test_request.service_name,
                environment=test_request.environment,
                endpoint=test_request.endpoint,
                method=test_request.method,
                status_code=response.status_code,
                response_data=response_data,
                response_headers=dict(response.headers),
                duration=duration,
                request_id=request_id
            )
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            
            # Record failed request
            await rate_limiter.end_request(
                test_request.service_name, 
                test_request.endpoint, 
                success=False
            )
            
            return APITestResponse(
                success=False,
                service_name=test_request.service_name,
                environment=test_request.environment,
                endpoint=test_request.endpoint,
                method=test_request.method,
                duration=duration,
                error=str(e),
                request_id=request_id
            )
            
    except ServiceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Service '{test_request.service_name}' not found")
    except RateLimitException as e:
        raise HTTPException(status_code=429, detail=str(e), headers={"Retry-After": str(e.retry_after)})
    except Exception as e:
        logger.error(f"Error executing API test: {str(e)}")
        raise HTTPException(status_code=500, detail="Error executing API test")


# Batch API test endpoint
@router.post("/batch", response_model=List[APITestResponse])
async def execute_batch_tests(
    batch_request: BatchTestRequest,
    background_tasks: BackgroundTasks,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Execute multiple API test requests in batch.
    
    Can run requests sequentially or in parallel based on configuration.
    Supports stopping on first error for fail-fast behavior.
    """
    results = []
    
    try:
        if batch_request.parallel:
            # Execute requests in parallel
            tasks = []
            for test_request in batch_request.requests:
                task = asyncio.create_task(
                    _execute_single_test(test_request, service_registry)
                )
                tasks.append(task)
                
            # Wait for all tasks to complete
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in completed_results:
                if isinstance(result, Exception):
                    # Convert exception to error response
                    error_response = APITestResponse(
                        success=False,
                        service_name="unknown",
                        environment="unknown", 
                        endpoint="unknown",
                        method="unknown",
                        error=str(result),
                        request_id=f"error_{hash(str(result))}"
                    )
                    results.append(error_response)
                else:
                    results.append(result)
                    
        else:
            # Execute requests sequentially
            for test_request in batch_request.requests:
                try:
                    result = await _execute_single_test(test_request, service_registry)
                    results.append(result)
                    
                    # Stop on error if configured
                    if batch_request.stop_on_error and not result.success:
                        break
                        
                except Exception as e:
                    error_response = APITestResponse(
                        success=False,
                        service_name=test_request.service_name,
                        environment=test_request.environment,
                        endpoint=test_request.endpoint,
                        method=test_request.method,
                        error=str(e),
                        request_id=f"error_{hash(str(e))}"
                    )
                    results.append(error_response)
                    
                    if batch_request.stop_on_error:
                        break
                        
        return results
        
    except Exception as e:
        logger.error(f"Error executing batch tests: {str(e)}")
        raise HTTPException(status_code=500, detail="Error executing batch tests")


# Service method call endpoint
@router.post("/method", response_model=Dict[str, Any])
async def call_service_method(
    method_request: ServiceMethodRequest,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Call a specific method on a service instance.
    
    Provides access to service-specific methods beyond generic HTTP requests.
    Useful for calling specialized functionality like Stripe's create_customer.
    """
    try:
        # Get service instance
        service_instance = service_registry.get_service_instance(
            service_name=method_request.service_name,
            environment=method_request.environment,
            credentials=method_request.credentials
        )
        
        # Check if method exists
        if not hasattr(service_instance, method_request.method_name):
            raise HTTPException(
                status_code=400, 
                detail=f"Method '{method_request.method_name}' not found on service '{method_request.service_name}'"
            )
            
        method = getattr(service_instance, method_request.method_name)
        
        # Check if method is callable
        if not callable(method):
            raise HTTPException(
                status_code=400,
                detail=f"'{method_request.method_name}' is not a callable method"
            )
            
        # Wait for rate limiting
        await rate_limiter.wait_for_rate_limit(
            method_request.service_name, 
            method_request.method_name
        )
        
        # Call the method
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Call method with provided arguments
            if asyncio.iscoroutinefunction(method):
                result = await method(**method_request.arguments)
            else:
                result = method(**method_request.arguments)
                
            duration = asyncio.get_event_loop().time() - start_time
            
            # Record successful request
            await rate_limiter.end_request(
                method_request.service_name, 
                method_request.method_name, 
                success=True
            )
            
            return {
                "success": True,
                "service_name": method_request.service_name,
                "environment": method_request.environment,
                "method_name": method_request.method_name,
                "result": result,
                "duration": duration,
                "timestamp": "2025-07-01T00:00:00Z"  # Would use datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            
            # Record failed request
            await rate_limiter.end_request(
                method_request.service_name, 
                method_request.method_name, 
                success=False
            )
            
            return {
                "success": False,
                "service_name": method_request.service_name,
                "environment": method_request.environment,
                "method_name": method_request.method_name,
                "error": str(e),
                "duration": duration,
                "timestamp": "2025-07-01T00:00:00Z"
            }
            
    except ServiceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Service '{method_request.service_name}' not found")
    except RateLimitException as e:
        raise HTTPException(status_code=429, detail=str(e), headers={"Retry-After": str(e.retry_after)})
    except Exception as e:
        logger.error(f"Error calling service method: {str(e)}")
        raise HTTPException(status_code=500, detail="Error calling service method")


# Service exploration endpoints
@router.get("/{service_name}/methods")
async def list_service_methods(
    service_name: str,
    environment: str = Query("production"),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    List all available methods for a service.
    
    Returns callable methods on the service instance with their signatures
    and documentation where available.
    """
    try:
        # Get service instance
        service_instance = service_registry.get_service_instance(
            service_name=service_name,
            environment=environment
        )
        
        # Get all callable methods (excluding private methods)
        methods = []
        for attr_name in dir(service_instance):
            if not attr_name.startswith('_'):
                attr = getattr(service_instance, attr_name)
                if callable(attr):
                    # Get method information
                    method_info = {
                        "name": attr_name,
                        "callable": True,
                        "is_coroutine": asyncio.iscoroutinefunction(attr),
                        "doc": attr.__doc__ or "No documentation available"
                    }
                    
                    # Try to get method signature
                    try:
                        import inspect
                        sig = inspect.signature(attr)
                        method_info["signature"] = str(sig)
                        method_info["parameters"] = [
                            {
                                "name": param.name,
                                "default": str(param.default) if param.default != inspect.Parameter.empty else None,
                                "annotation": str(param.annotation) if param.annotation != inspect.Parameter.empty else None
                            }
                            for param in sig.parameters.values()
                            if param.name not in ['self', 'cls']
                        ]
                    except Exception:
                        method_info["signature"] = "Unable to inspect signature"
                        method_info["parameters"] = []
                        
                    methods.append(method_info)
                    
        return {
            "service_name": service_name,
            "environment": environment,
            "total_methods": len(methods),
            "methods": methods
        }
        
    except ServiceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    except Exception as e:
        logger.error(f"Error listing service methods: {str(e)}")
        raise HTTPException(status_code=500, detail="Error listing service methods")


@router.get("/{service_name}/endpoints")
async def list_service_endpoints(
    service_name: str,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    List configured API endpoints for a service.
    
    Returns endpoint definitions from the service configuration
    including HTTP methods, paths, and parameter requirements.
    """
    try:
        service_info = service_registry.get_service_info(service_name)
        endpoints = service_info.get("endpoints", {})
        
        endpoint_list = []
        for endpoint_name, endpoint_config in endpoints.items():
            endpoint_list.append({
                "name": endpoint_name,
                "method": endpoint_config["method"],
                "path": endpoint_config["path"],
                "description": endpoint_config["description"],
                "required_params": endpoint_config["required_params"],
                "optional_params": endpoint_config["optional_params"]
            })
            
        return {
            "service_name": service_name,
            "total_endpoints": len(endpoint_list),
            "endpoints": endpoint_list
        }
        
    except ServiceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    except Exception as e:
        logger.error(f"Error listing service endpoints: {str(e)}")
        raise HTTPException(status_code=500, detail="Error listing service endpoints")


# Rate limiting status endpoint
@router.get("/{service_name}/rate-limits")
async def get_service_rate_limits(
    service_name: str,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get current rate limiting status for a service.
    
    Returns rate limit configuration, current usage, and
    time until limits reset.
    """
    try:
        # Verify service exists
        service_registry.get_service_info(service_name)
        
        # Get rate limit status
        rate_limit_status = rate_limiter.get_service_status(service_name)
        
        return rate_limit_status
        
    except ServiceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    except Exception as e:
        logger.error(f"Error getting rate limits for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving rate limit status")


@router.post("/{service_name}/rate-limits/reset")
async def reset_service_rate_limits(
    service_name: str,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Reset rate limits for a service.
    
    Clears current usage counters and allows immediate API calls.
    Useful for development and testing scenarios.
    """
    try:
        # Verify service exists
        service_registry.get_service_info(service_name)
        
        # Reset rate limits
        await rate_limiter.reset_service_limits(service_name)
        
        return {
            "message": f"Rate limits reset for service '{service_name}'",
            "service_name": service_name,
            "status": "reset",
            "timestamp": "2025-07-01T00:00:00Z"
        }
        
    except ServiceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    except Exception as e:
        logger.error(f"Error resetting rate limits for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error resetting rate limits")


# Service request history endpoint
@router.get("/{service_name}/history")
async def get_service_request_history(
    service_name: str,
    environment: str = Query("production"),
    limit: int = Query(50, le=500),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get request history for a service instance.
    
    Returns recent API calls made through the service instance
    including timing, status codes, and error information.
    """
    try:
        # Get service instance
        service_instance = service_registry.get_service_instance(
            service_name=service_name,
            environment=environment
        )
        
        # Get request history
        history = service_instance.get_request_history(limit=limit)
        
        return {
            "service_name": service_name,
            "environment": environment,
            "total_requests": len(history),
            "history": history
        }
        
    except ServiceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    except Exception as e:
        logger.error(f"Error getting request history for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving request history")


# Helper function for executing single tests
async def _execute_single_test(
    test_request: APITestRequest, 
    service_registry: ServiceRegistry
) -> APITestResponse:
    """Execute a single API test request."""
    request_id = f"{test_request.service_name}_{test_request.endpoint}_{hash(str(test_request.dict()))}"
    
    try:
        # Get service instance
        service_instance = service_registry.get_service_instance(
            service_name=test_request.service_name,
            environment=test_request.environment,
            credentials=test_request.credentials
        )
        
        # Wait for rate limiting
        await rate_limiter.wait_for_rate_limit(
            test_request.service_name, 
            test_request.endpoint
        )
        
        # Execute the API call
        start_time = asyncio.get_event_loop().time()
        
        response = await service_instance.make_request(
            method=test_request.method,
            endpoint=test_request.endpoint,
            params=test_request.parameters,
            headers=test_request.headers,
            body=test_request.body
        )
        
        duration = asyncio.get_event_loop().time() - start_time
        
        # Parse response
        try:
            response_data = response.json()
        except:
            response_data = {"raw_response": response.text}
            
        # Record successful request
        await rate_limiter.end_request(
            test_request.service_name, 
            test_request.endpoint, 
            success=True
        )
        
        return APITestResponse(
            success=True,
            service_name=test_request.service_name,
            environment=test_request.environment,
            endpoint=test_request.endpoint,
            method=test_request.method,
            status_code=response.status_code,
            response_data=response_data,
            response_headers=dict(response.headers),
            duration=duration,
            request_id=request_id
        )
        
    except Exception as e:
        duration = asyncio.get_event_loop().time() - start_time
        
        # Record failed request
        await rate_limiter.end_request(
            test_request.service_name, 
            test_request.endpoint, 
            success=False
        )
        
        return APITestResponse(
            success=False,
            service_name=test_request.service_name,
            environment=test_request.environment,
            endpoint=test_request.endpoint,
            method=test_request.method,
            duration=duration,
            error=str(e),
            request_id=request_id
        )