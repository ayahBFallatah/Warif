"""
Green Engine RBAC Middleware
Handles authentication and authorization for API endpoints
"""

from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Callable
from functools import wraps
import logging

from .authentication import AuthenticationService, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()

class RBACMiddleware:
    """Role-Based Access Control middleware"""
    
    def __init__(self):
        self.auth_service = AuthenticationService()
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """Get current authenticated user from JWT token"""
        try:
            # Extract token from Authorization header
            token = credentials.credentials
            
            # Verify token
            payload = self.auth_service.verify_token(token, "access")
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Get user data
            user = self.auth_service.get_user_by_id(payload.get("user_id"))
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def get_current_user_optional(self, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
        """Get current user if authenticated, otherwise return None"""
        try:
            if not credentials:
                return None
            return self.get_current_user(credentials)
        except HTTPException:
            return None
    
    def require_permission(self, resource: str, action: str):
        """Decorator to require specific permission"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get current user from kwargs
                current_user = kwargs.get('current_user')
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                # Check permission
                if not self.auth_service.check_permission(current_user, resource, action):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {action} on {resource}"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_role(self, required_roles: List[str]):
        """Decorator to require specific roles"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get current user from kwargs
                current_user = kwargs.get('current_user')
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                # Check if user has any of the required roles
                if not any(role in current_user.roles for role in required_roles):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Required roles: {', '.join(required_roles)}"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_admin(self):
        """Decorator to require admin role"""
        return self.require_role(["admin"])
    
    def require_operator_or_admin(self):
        """Decorator to require operator or admin role"""
        return self.require_role(["admin", "operator"])
    
    def require_any_role(self):
        """Decorator to require any authenticated user"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get current user from kwargs
                current_user = kwargs.get('current_user')
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator

# Global RBAC middleware instance
rbac = RBACMiddleware()

# Common dependency functions
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current authenticated user"""
    return rbac.get_current_user(credentials)

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """Dependency to get current user if authenticated"""
    return rbac.get_current_user_optional(credentials)

def require_permission(resource: str, action: str):
    """Dependency factory for permission requirements"""
    def check_permission(current_user: User = Depends(get_current_user)):
        if not rbac.auth_service.check_permission(current_user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {action} on {resource}"
            )
        return current_user
    return check_permission

def require_role(required_roles: List[str]):
    """Dependency factory for role requirements"""
    def check_role(current_user: User = Depends(get_current_user)):
        if not any(role in current_user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(required_roles)}"
            )
        return current_user
    return check_role

def require_admin():
    """Dependency to require admin role"""
    return require_role(["admin"])

def require_operator_or_admin():
    """Dependency to require operator or admin role"""
    return require_role(["admin", "operator"])

def require_any_role():
    """Dependency to require any authenticated user"""
    return get_current_user

# Permission constants
class Permissions:
    """Permission constants for resources and actions"""
    
    # User management
    USERS_CREATE = ("users", "create")
    USERS_READ = ("users", "read")
    USERS_UPDATE = ("users", "update")
    USERS_DELETE = ("users", "delete")
    
    # Role management
    ROLES_CREATE = ("roles", "create")
    ROLES_READ = ("roles", "read")
    ROLES_UPDATE = ("roles", "update")
    ROLES_DELETE = ("roles", "delete")
    
    # Sensor data
    SENSORS_CREATE = ("sensors", "create")
    SENSORS_READ = ("sensors", "read")
    SENSORS_UPDATE = ("sensors", "update")
    SENSORS_DELETE = ("sensors", "delete")
    
    # Tray management
    TRAYS_CREATE = ("trays", "create")
    TRAYS_READ = ("trays", "read")
    TRAYS_UPDATE = ("trays", "update")
    TRAYS_DELETE = ("trays", "delete")
    
    # Alert management
    ALERTS_CREATE = ("alerts", "create")
    ALERTS_READ = ("alerts", "read")
    ALERTS_UPDATE = ("alerts", "update")
    ALERTS_DELETE = ("alerts", "delete")
    
    # Command management
    COMMANDS_CREATE = ("commands", "create")
    COMMANDS_READ = ("commands", "read")
    COMMANDS_UPDATE = ("commands", "update")
    COMMANDS_DELETE = ("commands", "delete")
    
    # Configuration
    CONFIG_CREATE = ("config", "create")
    CONFIG_READ = ("config", "read")
    CONFIG_UPDATE = ("config", "update")
    CONFIG_DELETE = ("config", "delete")
    
    # Analytics
    ANALYTICS_READ = ("analytics", "read")
    
    # ML
    ML_READ = ("ml", "read")
    ML_UPDATE = ("ml", "update")
    
    # System
    SYSTEM_READ = ("system", "read")
    SYSTEM_UPDATE = ("system", "update")

# Role constants
class Roles:
    """Role constants"""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

# Audit logging helper
def log_audit_event(request: Request, user: User, action: str, resource_type: str = None, resource_id: str = None, details: dict = None):
    """Log audit event for user action"""
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        rbac.auth_service.log_audit_event(
            user_id=user.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        logger.error(f"Error logging audit event: {e}")

# Request logging middleware
async def log_requests(request: Request, call_next):
    """Middleware to log all requests"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Log request
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response
