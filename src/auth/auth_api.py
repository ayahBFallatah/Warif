"""
Warif Authentication API
REST endpoints for user authentication and management
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from .authentication import AuthenticationService, User
from .middleware import (
    get_current_user, get_current_user_optional, require_admin, 
    require_operator_or_admin, require_any_role, log_audit_event,
    Permissions, Roles
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# Initialize auth service
auth_service = AuthenticationService()

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    roles: List[str] = []

class UpdateUserRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    roles: List[str]
    permissions: Dict[str, List[str]]
    created_at: datetime
    last_login: Optional[datetime]

class RoleResponse(BaseModel):
    id: int
    name: str
    description: str
    permissions: Dict[str, List[str]]

class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    username: str
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str]
    timestamp: datetime

# Authentication endpoints
@router.post("/login", response_model=LoginResponse)
async def login(request: Request, login_data: LoginRequest):
    """Authenticate user and return JWT tokens"""
    try:
        # Get client information
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Authenticate user
        auth_result = auth_service.authenticate_user(
            username=login_data.username,
            password=login_data.password,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        user = auth_result["user"]
        tokens = auth_result["tokens"]
        
        # Log successful login
        log_audit_event(
            request=request,
            user=user,
            action="login",
            details={"ip_address": ip_address, "user_agent": user_agent}
        )
        
        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "roles": user.roles,
                "permissions": user.permissions
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    try:
        tokens = auth_service.refresh_access_token(refresh_data.refresh_token)
        
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        return RefreshTokenResponse(
            access_token=tokens["access_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout(request: Request, current_user: User = Depends(require_any_role())):
    """Logout user and invalidate session"""
    try:
        # Get session token from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )
        
        session_token = auth_header.split(" ")[1]
        
        # Logout user
        success = auth_service.logout_user(session_token)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Logout failed"
            )
        
        # Log logout
        log_audit_event(
            request=request,
            user=current_user,
            action="logout"
        )
        
        return {"message": "Logged out successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(require_any_role())):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        roles=current_user.roles,
        permissions=current_user.permissions,
        created_at=datetime.utcnow(),  # This should come from database
        last_login=None  # This should come from database
    )

# User management endpoints (Admin only)
@router.post("/users", response_model=UserResponse)
async def create_user(
    request: Request,
    user_data: CreateUserRequest,
    current_user: User = Depends(require_admin())
):
    """Create new user (Admin only)"""
    try:
        # Create user
        new_user = auth_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            roles=user_data.roles
        )
        
        if not new_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User creation failed - username or email already exists"
            )
        
        # Log user creation
        log_audit_event(
            request=request,
            user=current_user,
            action="create_user",
            resource_type="user",
            resource_id=str(new_user.id),
            details={"username": new_user.username, "email": new_user.email, "roles": new_user.roles}
        )
        
        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            first_name=new_user.first_name,
            last_name=new_user.last_name,
            is_active=new_user.is_active,
            is_verified=new_user.is_verified,
            roles=new_user.roles,
            permissions=new_user.permissions,
            created_at=datetime.utcnow(),
            last_login=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed"
        )

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(require_admin())
):
    """List all users (Admin only)"""
    try:
        users = auth_service.list_users(limit=limit, offset=offset)
        
        # Log user listing
        log_audit_event(
            request=request,
            user=current_user,
            action="list_users",
            details={"limit": limit, "offset": offset, "count": len(users)}
        )
        
        return [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                roles=user.roles,
                permissions=user.permissions,
                created_at=datetime.utcnow(),
                last_login=None
            )
            for user in users
        ]
        
    except Exception as e:
        logger.error(f"User listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User listing failed"
        )

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    request: Request,
    user_id: int,
    current_user: User = Depends(require_admin())
):
    """Get user by ID (Admin only)"""
    try:
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Log user access
        log_audit_event(
            request=request,
            user=current_user,
            action="get_user",
            resource_type="user",
            resource_id=str(user_id)
        )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            roles=user.roles,
            permissions=user.permissions,
            created_at=datetime.utcnow(),
            last_login=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Get user failed"
        )

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: int,
    user_data: UpdateUserRequest,
    current_user: User = Depends(require_admin())
):
    """Update user (Admin only)"""
    try:
        # Check if user exists
        existing_user = auth_service.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update user
        updated_user = auth_service.update_user(
            user_id=user_id,
            **user_data.dict(exclude_unset=True)
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User update failed"
            )
        
        # Log user update
        log_audit_event(
            request=request,
            user=current_user,
            action="update_user",
            resource_type="user",
            resource_id=str(user_id),
            details=user_data.dict(exclude_unset=True)
        )
        
        return UserResponse(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            is_active=updated_user.is_active,
            is_verified=updated_user.is_verified,
            roles=updated_user.roles,
            permissions=updated_user.permissions,
            created_at=datetime.utcnow(),
            last_login=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    request: Request,
    user_id: int,
    current_user: User = Depends(require_admin())
):
    """Delete user (Admin only)"""
    try:
        # Check if user exists
        existing_user = auth_service.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent self-deletion
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Delete user
        success = auth_service.delete_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User deletion failed"
            )
        
        # Log user deletion
        log_audit_event(
            request=request,
            user=current_user,
            action="delete_user",
            resource_type="user",
            resource_id=str(user_id),
            details={"username": existing_user.username, "email": existing_user.email}
        )
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed"
        )

# Role management endpoints (Admin only)
@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    request: Request,
    current_user: User = Depends(require_admin())
):
    """List all roles (Admin only)"""
    try:
        # This would need to be implemented in the auth service
        # For now, return default roles
        roles = [
            RoleResponse(
                id=1,
                name="admin",
                description="Full system access",
                permissions={
                    "users": ["create", "read", "update", "delete"],
                    "roles": ["create", "read", "update", "delete"],
                    "sensors": ["create", "read", "update", "delete"],
                    "trays": ["create", "read", "update", "delete"],
                    "alerts": ["create", "read", "update", "delete"],
                    "commands": ["create", "read", "update", "delete"],
                    "config": ["create", "read", "update", "delete"],
                    "analytics": ["read"],
                    "ml": ["read", "update"],
                    "system": ["read", "update"]
                }
            ),
            RoleResponse(
                id=2,
                name="operator",
                description="Operational access for daily tasks",
                permissions={
                    "sensors": ["read"],
                    "trays": ["read", "update"],
                    "alerts": ["read", "update"],
                    "commands": ["create", "read"],
                    "config": ["read"],
                    "analytics": ["read"],
                    "ml": ["read"]
                }
            ),
            RoleResponse(
                id=3,
                name="viewer",
                description="Read-only access for monitoring",
                permissions={
                    "sensors": ["read"],
                    "trays": ["read"],
                    "alerts": ["read"],
                    "commands": ["read"],
                    "config": ["read"],
                    "analytics": ["read"],
                    "ml": ["read"]
                }
            )
        ]
        
        # Log role listing
        log_audit_event(
            request=request,
            user=current_user,
            action="list_roles"
        )
        
        return roles
        
    except Exception as e:
        logger.error(f"Role listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Role listing failed"
        )

# Audit log endpoints (Admin only)
@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(require_admin())
):
    """List audit logs (Admin only)"""
    try:
        # This would need to be implemented in the auth service
        # For now, return empty list
        audit_logs = []
        
        # Log audit log access
        log_audit_event(
            request=request,
            user=current_user,
            action="list_audit_logs",
            details={"limit": limit, "offset": offset}
        )
        
        return audit_logs
        
    except Exception as e:
        logger.error(f"Audit log listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Audit log listing failed"
        )
