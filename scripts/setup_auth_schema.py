#!/usr/bin/env python3
"""
Warif Authentication Schema Setup
Creates user management and RBAC database tables
"""

import psycopg2
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
import hashlib
import secrets

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        database=os.getenv("DB_NAME", "warif"),
        user=os.getenv("DB_USER", "warif_user"),
        password=os.getenv("DB_PASSWORD", "password"),
        port=os.getenv("DB_PORT", "5432")
    )

def create_auth_tables():
    """Create authentication and user management tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("🔐 Creating authentication tables...")
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                is_active BOOLEAN DEFAULT true,
                is_verified BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP
            )
        """)
        
        # Roles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                permissions JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User roles junction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                assigned_by INTEGER REFERENCES users(id),
                UNIQUE(user_id, role_id)
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                session_token VARCHAR(255) UNIQUE NOT NULL,
                refresh_token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address INET,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT true
            )
        """)
        
        # Audit log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                action VARCHAR(100) NOT NULL,
                resource_type VARCHAR(100),
                resource_id VARCHAR(100),
                details JSONB DEFAULT '{}',
                ip_address INET,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # API keys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                key_name VARCHAR(100) NOT NULL,
                api_key VARCHAR(255) UNIQUE NOT NULL,
                permissions JSONB DEFAULT '{}',
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                last_used TIMESTAMP
            )
        """)
        
        # Password reset tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Email verification tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_verification_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("✅ Authentication tables created successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating authentication tables: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def create_indexes():
    """Create indexes for better performance"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("📊 Creating indexes...")
        
        # User indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)")
        
        # Session indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at)")
        
        # Audit log indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)")
        
        # API key indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(api_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id)")
        
        # Token indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reset_tokens_token ON password_reset_tokens(token)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_verify_tokens_token ON email_verification_tokens(token)")
        
        conn.commit()
        print("✅ Indexes created successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating indexes: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def create_default_roles():
    """Create default roles with permissions"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("👥 Creating default roles...")
        
        # Admin role
        admin_permissions = {
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
        
        cursor.execute("""
            INSERT INTO roles (name, description, permissions) 
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                description = EXCLUDED.description,
                permissions = EXCLUDED.permissions
        """, ("admin", "Full system access", json.dumps(admin_permissions)))
        
        # Operator role
        operator_permissions = {
            "sensors": ["read"],
            "trays": ["read", "update"],
            "alerts": ["read", "update"],
            "commands": ["create", "read"],
            "config": ["read"],
            "analytics": ["read"],
            "ml": ["read"]
        }
        
        cursor.execute("""
            INSERT INTO roles (name, description, permissions) 
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                description = EXCLUDED.description,
                permissions = EXCLUDED.permissions
        """, ("operator", "Operational access for daily tasks", json.dumps(operator_permissions)))
        
        # Viewer role
        viewer_permissions = {
            "sensors": ["read"],
            "trays": ["read"],
            "alerts": ["read"],
            "commands": ["read"],
            "config": ["read"],
            "analytics": ["read"],
            "ml": ["read"]
        }
        
        cursor.execute("""
            INSERT INTO roles (name, description, permissions) 
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                description = EXCLUDED.description,
                permissions = EXCLUDED.permissions
        """, ("viewer", "Read-only access for monitoring", json.dumps(viewer_permissions)))
        
        conn.commit()
        print("✅ Default roles created successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating default roles: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def create_default_admin_user():
    """Create default admin user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("👤 Creating default admin user...")
        
        # Check if admin user already exists
        cursor.execute("SELECT id FROM users WHERE username = %s", ("admin",))
        if cursor.fetchone():
            print("⚠️ Admin user already exists")
            return
        
        # Create password hash (in production, use proper password hashing)
        password = "admin123"  # Change this in production!
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create admin user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, first_name, last_name, is_active, is_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, ("admin", "admin@warif.com", password_hash, "System", "Administrator", True, True))
        
        user_id = cursor.fetchone()[0]
        
        # Assign admin role
        cursor.execute("SELECT id FROM roles WHERE name = %s", ("admin",))
        role_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO user_roles (user_id, role_id, assigned_by)
            VALUES (%s, %s, %s)
        """, (user_id, role_id, user_id))
        
        conn.commit()
        print("✅ Default admin user created successfully")
        print("   Username: admin")
        print("   Password: admin123")
        print("   ⚠️ Please change the password in production!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating default admin user: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def create_sample_users():
    """Create sample users for testing"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("👥 Creating sample users...")
        
        sample_users = [
            {
                "username": "operator1",
                "email": "operator1@warif.com",
                "password": "operator123",
                "first_name": "John",
                "last_name": "Operator",
                "role": "operator"
            },
            {
                "username": "viewer1",
                "email": "viewer1@warif.com",
                "password": "viewer123",
                "first_name": "Jane",
                "last_name": "Viewer",
                "role": "viewer"
            }
        ]
        
        for user_data in sample_users:
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE username = %s", (user_data["username"],))
            if cursor.fetchone():
                print(f"⚠️ User {user_data['username']} already exists")
                continue
            
            # Create password hash
            password_hash = hashlib.sha256(user_data["password"].encode()).hexdigest()
            
            # Create user
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, first_name, last_name, is_active, is_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (user_data["username"], user_data["email"], password_hash, 
                  user_data["first_name"], user_data["last_name"], True, True))
            
            user_id = cursor.fetchone()[0]
            
            # Assign role
            cursor.execute("SELECT id FROM roles WHERE name = %s", (user_data["role"],))
            role_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO user_roles (user_id, role_id, assigned_by)
                VALUES (%s, %s, %s)
            """, (user_id, role_id, 1))  # Assigned by admin (user_id 1)
            
            print(f"✅ Created user: {user_data['username']} ({user_data['role']})")
        
        conn.commit()
        print("✅ Sample users created successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating sample users: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function"""
    print("🚀 Setting up Warif Authentication Schema...")
    print("=" * 60)
    
    try:
        create_auth_tables()
        create_indexes()
        create_default_roles()
        create_default_admin_user()
        create_sample_users()
        
        print("\n" + "=" * 60)
        print("🎉 Authentication schema setup completed successfully!")
        print("\n📋 Created:")
        print("   • Users table with authentication")
        print("   • Roles table with permissions")
        print("   • User roles junction table")
        print("   • Sessions table for JWT management")
        print("   • Audit logs table for security")
        print("   • API keys table for programmatic access")
        print("   • Password reset and email verification tables")
        print("   • Default roles: admin, operator, viewer")
        print("   • Default admin user: admin/admin123")
        print("   • Sample users: operator1/operator123, viewer1/viewer123")
        
        print("\n⚠️ Security Notes:")
        print("   • Change default passwords in production")
        print("   • Use proper password hashing (bcrypt, scrypt)")
        print("   • Implement rate limiting for login attempts")
        print("   • Use HTTPS in production")
        print("   • Regularly rotate API keys")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
