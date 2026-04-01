"""
Green Engine Authentication Service
Handles user authentication, JWT tokens, and session management
"""

from jose import jwt
import hashlib
import secrets
import psycopg2
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class User:
    """User data class"""
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    roles: List[str]
    permissions: Dict[str, List[str]]

@dataclass
class Session:
    """Session data class"""
    user_id: int
    session_token: str
    refresh_token: str
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuthenticationService:
    """Authentication service for user management and JWT tokens"""
    
    def __init__(self):
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key_change_me")
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        self.max_login_attempts = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        self.lockout_duration_minutes = int(os.getenv("LOCKOUT_DURATION_MINUTES", "30"))
        
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres"),
            database=os.getenv("DB_NAME", "green_engine"),
            user=os.getenv("DB_USER", "green_user"),
            password=os.getenv("DB_PASSWORD", "password"),
            port=os.getenv("DB_PORT", "5432")
        )
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 (in production, use bcrypt)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(password) == hashed_password
    
    def generate_tokens(self, user_id: int) -> Dict[str, str]:
        """Generate JWT access and refresh tokens"""
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            "user_id": user_id,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self.access_token_expire_minutes)
        }
        
        # Refresh token payload
        refresh_payload = {
            "user_id": user_id,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=self.refresh_token_expire_days)
        }
        
        # Generate tokens
        access_token = jwt.encode(access_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            if payload.get("type") != token_type:
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID with roles and permissions"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get user data
            cursor.execute("""
                SELECT id, username, email, first_name, last_name, is_active, is_verified
                FROM users WHERE id = %s
            """, (user_id,))
            
            user_row = cursor.fetchone()
            if not user_row:
                return None
            
            # Get user roles and permissions
            cursor.execute("""
                SELECT r.name, r.permissions
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = %s
            """, (user_id,))
            
            roles = []
            all_permissions = {}
            
            for role_name, permissions in cursor.fetchall():
                roles.append(role_name)
                if permissions:
                    all_permissions.update(permissions)
            
            return User(
                id=user_row[0],
                username=user_row[1],
                email=user_row[2],
                first_name=user_row[3],
                last_name=user_row[4],
                is_active=user_row[5],
                is_verified=user_row[6],
                roles=roles,
                permissions=all_permissions
            )
            
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user_row = cursor.fetchone()
            
            if user_row:
                return self.get_user_by_id(user_row[0])
            return None
            
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def authenticate_user(self, username: str, password: str, ip_address: str = None, user_agent: str = None) -> Optional[Dict[str, Any]]:
        """Authenticate user and return tokens"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get user data
            cursor.execute("""
                SELECT id, username, password_hash, is_active, is_verified, 
                       failed_login_attempts, locked_until
                FROM users WHERE username = %s
            """, (username,))
            
            user_row = cursor.fetchone()
            if not user_row:
                return None
            
            user_id, username, password_hash, is_active, is_verified, failed_attempts, locked_until = user_row
            
            # Check if user is active
            if not is_active:
                return None
            
            # Check if account is locked
            if locked_until and datetime.utcnow() < locked_until:
                return None
            
            # Verify password
            if not self.verify_password(password, password_hash):
                # Increment failed login attempts
                cursor.execute("""
                    UPDATE users 
                    SET failed_login_attempts = failed_login_attempts + 1,
                        locked_until = CASE 
                            WHEN failed_login_attempts + 1 >= %s 
                            THEN CURRENT_TIMESTAMP + INTERVAL '%s minutes'
                            ELSE locked_until
                        END
                    WHERE id = %s
                """, (self.max_login_attempts, self.lockout_duration_minutes, user_id))
                conn.commit()
                return None
            
            # Reset failed login attempts on successful login
            cursor.execute("""
                UPDATE users 
                SET failed_login_attempts = 0, locked_until = NULL, last_login = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (user_id,))
            
            # Generate tokens
            tokens = self.generate_tokens(user_id)
            
            # Create session
            session_token = secrets.token_urlsafe(32)
            refresh_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
            
            cursor.execute("""
                INSERT INTO user_sessions (user_id, session_token, refresh_token, expires_at, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, session_token, refresh_token, expires_at, ip_address, user_agent))
            
            conn.commit()
            
            # Get user data
            user = self.get_user_by_id(user_id)
            
            return {
                "user": user,
                "tokens": tokens,
                "session_token": session_token
            }
            
        except Exception as e:
            conn.rollback()
            print(f"Error authenticating user: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh access token using refresh token"""
        # Verify refresh token
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        # Check if user still exists and is active
        user = self.get_user_by_id(user_id)
        if not user or not user.is_active:
            return None
        
        # Generate new access token
        tokens = self.generate_tokens(user_id)
        return tokens
    
    def logout_user(self, session_token: str) -> bool:
        """Logout user by invalidating session"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE user_sessions 
                SET is_active = false 
                WHERE session_token = %s
            """, (session_token,))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            print(f"Error logging out user: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def check_permission(self, user: User, resource: str, action: str) -> bool:
        """Check if user has permission for resource and action"""
        if not user or not user.is_active:
            return False
        
        # Admin has all permissions
        if "admin" in user.roles:
            return True
        
        # Check specific permissions
        resource_permissions = user.permissions.get(resource, [])
        return action in resource_permissions
    
    def create_user(self, username: str, email: str, password: str, first_name: str = None, last_name: str = None, roles: List[str] = None) -> Optional[User]:
        """Create new user"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
            if cursor.fetchone():
                return None
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Create user
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, first_name, last_name, is_active, is_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (username, email, password_hash, first_name, last_name, True, False))
            
            user_id = cursor.fetchone()[0]
            
            # Assign roles
            if roles:
                for role_name in roles:
                    cursor.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
                    role_row = cursor.fetchone()
                    if role_row:
                        cursor.execute("""
                            INSERT INTO user_roles (user_id, role_id, assigned_by)
                            VALUES (%s, %s, %s)
                        """, (user_id, role_row[0], user_id))
            
            conn.commit()
            return self.get_user_by_id(user_id)
            
        except Exception as e:
            conn.rollback()
            print(f"Error creating user: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user information"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Build update query
            update_fields = []
            values = []
            
            allowed_fields = ["first_name", "last_name", "email", "is_active", "is_verified"]
            for field, value in kwargs.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = %s")
                    values.append(value)
            
            if not update_fields:
                return self.get_user_by_id(user_id)
            
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
            
            cursor.execute(query, values)
            conn.commit()
            
            return self.get_user_by_id(user_id)
            
        except Exception as e:
            conn.rollback()
            print(f"Error updating user: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user (soft delete by deactivating)"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE users 
                SET is_active = false, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (user_id,))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            print(f"Error deleting user: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id FROM users 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            user_ids = [row[0] for row in cursor.fetchall()]
            users = []
            
            for user_id in user_ids:
                user = self.get_user_by_id(user_id)
                if user:
                    users.append(user)
            
            return users
            
        except Exception as e:
            print(f"Error listing users: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def log_audit_event(self, user_id: int, action: str, resource_type: str = None, resource_id: str = None, details: Dict = None, ip_address: str = None, user_agent: str = None):
        """Log audit event"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, action, resource_type, resource_id, details, ip_address, user_agent))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"Error logging audit event: {e}")
        finally:
            cursor.close()
            conn.close()
