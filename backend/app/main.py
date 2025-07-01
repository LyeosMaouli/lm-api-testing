# backend/app/main.py
"""
Main FastAPI application for the Multi-Service API Testing Platform.
"""

import os
import time
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog

from .core.config_manager import ConfigManager, AppSettings
from .core.service_discovery import ServiceRegistry
from .core.encryption import CredentialManager
from .core.rate_limiter import rate_limiter, RateLimitConfig, RateLimitStrategy
from .core.exceptions import (
    APITestingException, 
    map_exception_to_http,
    ServiceException,
    AuthenticationException,
    ConfigurationException
)

# Import API routers
from .api import auth, webhooks, history, collections
from .api import services, testing

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Set up logging
logging.basicConfig(
    format="%(message)s",
    stream=os.sys.stdout,
    level=logging.INFO,
)
logger = structlog.get_logger()

# Global application state
app_state = {
    "settings": None,
    "config_manager": None,
    "service_registry": None,
    "credential_manager": None,
    "startup_complete": False
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting API Testing Platform...")
    
    try:
        # Load application settings
        settings = AppSettings()
        app_state["settings"] = settings
        
        # Create data directories
        os.makedirs(settings.data_dir, exist_ok=True)
        os.makedirs(settings.config_dir, exist_ok=True)
        os.makedirs(settings.log_dir, exist_ok=True)
        os.makedirs(os.path.join(settings.data_dir, "credentials"), exist_ok=True)
        os.makedirs(os.path.join(settings.data_dir, "history"), exist_ok=True)
        os.makedirs(os.path.join(settings.data_dir, "collections"), exist_ok=True)
        
        # Initialize core components
        config_manager = ConfigManager(settings.config_dir)
        app_state["config_manager"] = config_manager
        
        service_registry = ServiceRegistry(
            services_dir="app/services",
            config_manager=config_manager
        )
        app_state["service_registry"] = service_registry
        
        credential_manager = CredentialManager(
            storage_dir=os.path.join(settings.data_dir, "credentials")
        )
        app_state["credential_manager"] = credential_manager
        
        # Discover and validate services
        discovered_services = service_registry.discover_services()
        logger.info(f"Discovered {len(discovered_services)} services: {discovered_services}")
        
        # Configure rate limiting for discovered services
        for service_name in discovered_services:
            try:
                config = config_manager.load_service_config(service_name)
                if config.rate_limits:
                    rate_limit_config = RateLimitConfig(
                        requests_per_second=config.rate_limits.requests_per_minute / 60 if config.rate_limits.requests_per_minute else None,
                        requests_per_minute=config.rate_limits.requests_per_minute,
                        requests_per_hour=config.rate_limits.requests_per_hour,
                        requests_per_day=config.rate_limits.requests_per_day,
                        burst_limit=config.rate_limits.burst_limit,
                        concurrent_requests=config.rate_limits.concurrent_requests,
                        strategy=RateLimitStrategy.SLIDING_WINDOW
                    )
                    rate_limiter.configure_service(service_name, rate_limit_config)
                    logger.info(f"Configured rate limits for {service_name}")
            except Exception as e:
                logger.warning(f"Could not configure rate limits for {service_name}: {str(e)}")
        
        app_state["startup_complete"] = True
        
        # Set dependencies for API routers to avoid circular imports
        services.set_dependencies(config_manager, service_registry, credential_manager)
        testing.set_dependencies(service_registry)
        
        logger.info("API Testing Platform startup complete")
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down API Testing Platform...")
    
    # Close any open connections, cleanup resources
    # TODO: Add cleanup for HTTP clients, database connections, etc.
    
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Multi-Service API Testing Platform",
    description="Comprehensive API testing platform for business service integrations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)


# Dependency injection
def get_settings() -> AppSettings:
    """Get application settings."""
    if not app_state["settings"]:
        raise HTTPException(status_code=503, detail="Application not initialized")
    return app_state["settings"]


def get_config_manager() -> ConfigManager:
    """Get configuration manager."""
    if not app_state["config_manager"]:
        raise HTTPException(status_code=503, detail="Configuration manager not initialized")
    return app_state["config_manager"]


def get_service_registry() -> ServiceRegistry:
    """Get service registry."""
    if not app_state["service_registry"]:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    return app_state["service_registry"]


def get_credential_manager() -> CredentialManager:
    """Get credential manager."""
    if not app_state["credential_manager"]:
        raise HTTPException(status_code=503, detail="Credential manager not initialized")
    return app_state["credential_manager"]


# Global exception handlers
@app.exception_handler(APITestingException)
async def api_testing_exception_handler(request: Request, exc: APITestingException):
    """Handle custom API testing exceptions."""
    http_exc = map_exception_to_http(exc)
    logger.error(
        "API Testing Exception",
        exception=exc.__class__.__name__,
        message=exc.message,
        details=exc.details,
        error_code=exc.error_code,
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=http_exc.status_code,
        content=http_exc.detail,
        headers=http_exc.headers
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        "Unhandled Exception",
        exception=exc.__class__.__name__,
        message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": {"type": exc.__class__.__name__}
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Multi-Service API Testing Platform",
        "version": "1.0.0",
        "status": "running" if app_state["startup_complete"] else "starting",
        "docs": "/docs",
        "services_count": len(app_state["service_registry"].discover_services()) if app_state["service_registry"] else 0
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health_status = {
        "status": "healthy" if app_state["startup_complete"] else "starting",
        "timestamp": "2025-07-01T00:00:00Z",  # Would use datetime.utcnow().isoformat() in real app
        "components": {
            "config_manager": app_state["config_manager"] is not None,
            "service_registry": app_state["service_registry"] is not None,
            "credential_manager": app_state["credential_manager"] is not None,
        }
    }
    
    # Check if any components are failing
    if not all(health_status["components"].values()):
        health_status["status"] = "unhealthy"
        
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


# System information endpoint
@app.get("/system/info")
async def system_info(
    config_manager: ConfigManager = Depends(get_config_manager),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Get system information and statistics."""
    try:
        available_services = service_registry.list_available_services()
        rate_limit_status = rate_limiter.get_all_services_status()
        
        return {
            "platform": {
                "name": "Multi-Service API Testing Platform",
                "version": "1.0.0",
                "startup_complete": app_state["startup_complete"]
            },
            "services": {
                "total_available": len(available_services),
                "loaded": sum(1 for service in available_services if service.get("loaded", False)),
                "with_errors": sum(1 for service in available_services if service.get("error")),
                "list": available_services
            },
            "rate_limiting": {
                "configured_services": len(rate_limit_status),
                "status": rate_limit_status
            },
            "storage": {
                "data_directory": app_state["settings"].data_dir,
                "config_directory": app_state["settings"].config_dir
            }
        }
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving system information")


# Include API routers
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    services.router,
    prefix="/api/v1/services",
    tags=["Services"]
)

app.include_router(
    testing.router,
    prefix="/api/v1/testing",
    tags=["API Testing"]
)

app.include_router(
    webhooks.router,
    prefix="/api/v1/webhooks",
    tags=["Webhooks"]
)

app.include_router(
    history.router,
    prefix="/api/v1/history",
    tags=["Request History"]
)

app.include_router(
    collections.router,
    prefix="/api/v1/collections",
    tags=["Request Collections"]
)


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    start_time = time.time()
    
    # Log request
    logger.info(
        "HTTP Request",
        method=request.method,
        path=request.url.path,
        query=str(request.query_params),
        client=request.client.host if request.client else None
    )
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        "HTTP Response",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=round(process_time, 4)
    )
    
    # Add process time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

# Add this to your main.py file temporarily for debugging

@app.get("/debug/services")
async def debug_services(
    config_manager: ConfigManager = Depends(get_config_manager),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Debug endpoint to see service discovery details."""
    try:
        # Get discovered services
        discovered = service_registry.discover_services()
        
        debug_info = {
            "discovered_services": discovered,
            "services_directory": str(service_registry.services_dir),
            "services_dir_exists": service_registry.services_dir.exists(),
            "config_directory": str(config_manager.config_dir),
            "available_configs": config_manager.list_available_services()
        }
        
        # Try to load each discovered service
        for service_name in discovered:
            try:
                service_class = service_registry.load_service_module(service_name)
                debug_info[f"{service_name}_load_result"] = {
                    "success": True,
                    "class_name": service_class.__name__,
                    "module": service_class.__module__
                }
            except Exception as e:
                debug_info[f"{service_name}_load_result"] = {
                    "success": False,
                    "error": str(e)
                }
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e)}