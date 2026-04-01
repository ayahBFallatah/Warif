"""
Green Engine User Management Interface
Streamlit interface for user management and RBAC
"""

import streamlit as st
import requests
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# API configuration
API_BASE_URL = "http://localhost:8010"

class UserManagement:
    """User management interface for the dashboard"""
    
    def __init__(self):
        self.api_base_url = API_BASE_URL
        self.auth_token = None
    
    def set_auth_token(self, token: str):
        """Set authentication token"""
        self.auth_token = token
    
    def get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Login user and get authentication token"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/v1/auth/login",
                json={"username": username, "password": password},
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                return data
            else:
                st.error(f"Login failed: {response.json().get('detail', 'Unknown error')}")
                return None
                
        except Exception as e:
            st.error(f"Login error: {e}")
            return None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user information"""
        try:
            response = requests.get(
                f"{self.api_base_url}/api/v1/auth/me",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            st.error(f"Error getting user info: {e}")
            return None
    
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users"""
        try:
            response = requests.get(
                f"{self.api_base_url}/api/v1/auth/users",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Error listing users: {response.json().get('detail', 'Unknown error')}")
                return []
                
        except Exception as e:
            st.error(f"Error listing users: {e}")
            return []
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new user"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/v1/auth/users",
                json=user_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Error creating user: {response.json().get('detail', 'Unknown error')}")
                return None
                
        except Exception as e:
            st.error(f"Error creating user: {e}")
            return None
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user"""
        try:
            response = requests.put(
                f"{self.api_base_url}/api/v1/auth/users/{user_id}",
                json=user_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Error updating user: {response.json().get('detail', 'Unknown error')}")
                return None
                
        except Exception as e:
            st.error(f"Error updating user: {e}")
            return None
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        try:
            response = requests.delete(
                f"{self.api_base_url}/api/v1/auth/users/{user_id}",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                return True
            else:
                st.error(f"Error deleting user: {response.json().get('detail', 'Unknown error')}")
                return False
                
        except Exception as e:
            st.error(f"Error deleting user: {e}")
            return False
    
    def list_roles(self) -> List[Dict[str, Any]]:
        """List all roles"""
        try:
            response = requests.get(
                f"{self.api_base_url}/api/v1/auth/roles",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Error listing roles: {response.json().get('detail', 'Unknown error')}")
                return []
                
        except Exception as e:
            st.error(f"Error listing roles: {e}")
            return []

def render_login_form():
    """Render login form"""
    st.subheader("🔐 Login")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if username and password:
                user_mgmt = UserManagement()
                auth_data = user_mgmt.login(username, password)
                
                if auth_data:
                    st.session_state.authenticated = True
                    st.session_state.user = auth_data["user"]
                    st.session_state.auth_token = auth_data["access_token"]
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Login failed. Please check your credentials.")
            else:
                st.error("Please enter both username and password.")

def render_user_management():
    """Render user management interface"""
    if not st.session_state.get("authenticated"):
        render_login_form()
        return
    
    user_mgmt = UserManagement()
    user_mgmt.set_auth_token(st.session_state.get("auth_token"))
    
    # Get current user info
    current_user = user_mgmt.get_current_user()
    if not current_user:
        st.error("Failed to get user information")
        return
    
    # Check if user is admin
    if "admin" not in current_user.get("roles", []):
        st.error("Access denied. Admin privileges required.")
        return
    
    st.subheader("👥 User Management")
    
    # User info
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info(f"Logged in as: **{current_user['username']}** ({', '.join(current_user['roles'])})")
    
    with col2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.auth_token = None
            st.success("Logged out successfully!")
            st.rerun()
    
    # Tabs for different management functions
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Users", "➕ Create User", "🔑 Roles", "📊 Audit Logs"])
    
    with tab1:
        render_users_list(user_mgmt)
    
    with tab2:
        render_create_user_form(user_mgmt)
    
    with tab3:
        render_roles_management(user_mgmt)
    
    with tab4:
        render_audit_logs(user_mgmt)

def render_users_list(user_mgmt: UserManagement):
    """Render users list"""
    st.subheader("👥 Users List")
    
    users = user_mgmt.list_users()
    
    if not users:
        st.info("No users found.")
        return
    
    # Display users in a table
    for user in users:
        with st.expander(f"👤 {user['username']} ({user['email']})"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**Name:** {user['first_name']} {user['last_name']}")
                st.write(f"**Email:** {user['email']}")
                st.write(f"**Roles:** {', '.join(user['roles'])}")
                st.write(f"**Status:** {'✅ Active' if user['is_active'] else '❌ Inactive'}")
                st.write(f"**Verified:** {'✅ Yes' if user['is_verified'] else '❌ No'}")
            
            with col2:
                if st.button(f"Edit {user['username']}", key=f"edit_{user['id']}"):
                    st.session_state.edit_user_id = user['id']
                    st.session_state.edit_user_data = user
                    st.rerun()
            
            with col3:
                if user['id'] != st.session_state.get('user', {}).get('id'):
                    if st.button(f"Delete {user['username']}", key=f"delete_{user['id']}"):
                        if user_mgmt.delete_user(user['id']):
                            st.success(f"User {user['username']} deleted successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete user {user['username']}")

def render_create_user_form(user_mgmt: UserManagement):
    """Render create user form"""
    st.subheader("➕ Create New User")
    
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username", placeholder="Enter username")
            email = st.text_input("Email", placeholder="Enter email address")
            password = st.text_input("Password", type="password", placeholder="Enter password")
        
        with col2:
            first_name = st.text_input("First Name", placeholder="Enter first name")
            last_name = st.text_input("Last Name", placeholder="Enter last name")
        
        # Role selection
        roles = user_mgmt.list_roles()
        role_names = [role['name'] for role in roles]
        selected_roles = st.multiselect("Roles", role_names, default=["viewer"])
        
        submit_button = st.form_submit_button("Create User")
        
        if submit_button:
            if username and email and password:
                user_data = {
                    "username": username,
                    "email": email,
                    "password": password,
                    "first_name": first_name,
                    "last_name": last_name,
                    "roles": selected_roles
                }
                
                new_user = user_mgmt.create_user(user_data)
                if new_user:
                    st.success(f"User {username} created successfully!")
                    st.rerun()
                else:
                    st.error("Failed to create user.")
            else:
                st.error("Please fill in all required fields (username, email, password).")

def render_roles_management(user_mgmt: UserManagement):
    """Render roles management"""
    st.subheader("🔑 Roles & Permissions")
    
    roles = user_mgmt.list_roles()
    
    if not roles:
        st.info("No roles found.")
        return
    
    for role in roles:
        with st.expander(f"🔑 {role['name'].title()} - {role['description']}"):
            st.write(f"**Description:** {role['description']}")
            st.write("**Permissions:**")
            
            permissions = role.get('permissions', {})
            for resource, actions in permissions.items():
                st.write(f"  • **{resource}:** {', '.join(actions)}")

def render_audit_logs(user_mgmt: UserManagement):
    """Render audit logs"""
    st.subheader("📊 Audit Logs")
    
    st.info("Audit logs feature coming soon. This will show user actions and system events.")
    
    # Placeholder for audit logs
    st.write("**Recent Activities:**")
    st.write("• User admin logged in")
    st.write("• User operator1 created new tray")
    st.write("• User viewer1 accessed sensor data")
    st.write("• System backup completed")

def main():
    """Main function for user management"""
    st.set_page_config(
        page_title="Green Engine - User Management",
        page_icon="👥",
        layout="wide"
    )
    
    st.title("👥 Green Engine User Management")
    
    if not st.session_state.get("authenticated"):
        render_login_form()
    else:
        render_user_management()

if __name__ == "__main__":
    main()
