"""
Authentication Module for Supabase Integration
Enhanced with comprehensive user management and security features
"""

import asyncio
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging

try:
    from supabase import create_client, Client
    from gotrue.errors import AuthApiError
except ImportError:
    print("Warning: supabase-py not installed. Install with: pip install supabase")
    Client = None
    AuthApiError = Exception

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthError(Exception):
    """Custom authentication error"""
    pass

class UserRole(Enum):
    """User roles enum"""
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"

@dataclass
class UserProfile:
    """User profile data class"""
    id: str
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    role: str = UserRole.USER.value
    is_email_verified: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_login: Optional[str] = None

@dataclass
class AuthSession:
    """Authentication session data class"""
    access_token: str
    refresh_token: str
    user: UserProfile
    expires_at: int
    token_type: str = "bearer"

class SupabaseAuth:
    """Enhanced Supabase Authentication Manager"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize Supabase client"""
        if not Client:
            raise ImportError("supabase-py is required. Install with: pip install supabase")
        
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client: Client = create_client(supabase_url, supabase_key)
        self._current_session: Optional[AuthSession] = None
        
        # Password requirements
        self.password_min_length = 8
        self.password_require_uppercase = True
        self.password_require_lowercase = True
        self.password_require_numbers = True
        self.password_require_special = True
        
    @property
    def current_user(self) -> Optional[UserProfile]:
        """Get current authenticated user"""
        if self._current_session:
            return self._current_session.user
        return None
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self._current_session is not None
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < self.password_min_length:
            errors.append(f"Password must be at least {self.password_min_length} characters long")
        
        if self.password_require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.password_require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.password_require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if self.password_require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    def validate_username(self, username: str) -> Tuple[bool, List[str]]:
        """Validate username format"""
        errors = []
        
        if not username:
            errors.append("Username cannot be empty")
        elif len(username) < 3:
            errors.append("Username must be at least 3 characters long")
        elif len(username) > 30:
            errors.append("Username cannot be more than 30 characters long")
        elif not re.match(r'^[a-zA-Z0-9_-]+$', username):
            errors.append("Username can only contain letters, numbers, hyphens, and underscores")
        
        return len(errors) == 0, errors
    
    async def sign_up(self, email: str, password: str, **kwargs) -> AuthSession:
        """Register a new user"""
        try:
            # Validate inputs
            if not self.validate_email(email):
                raise AuthError("Invalid email format")
            
            is_valid, password_errors = self.validate_password(password)
            if not is_valid:
                raise AuthError("Password validation failed: " + "; ".join(password_errors))
            
            # Validate username if provided
            username = kwargs.get('username')
            if username:
                is_valid, username_errors = self.validate_username(username)
                if not is_valid:
                    raise AuthError("Username validation failed: " + "; ".join(username_errors))
                
                # Check if username already exists
                if await self.is_username_taken(username):
                    raise AuthError("Username is already taken")
            
            # Prepare user metadata
            user_metadata = {}
            allowed_fields = ['full_name', 'username', 'bio', 'website', 'avatar_url']
            for field in allowed_fields:
                if field in kwargs and kwargs[field]:
                    user_metadata[field] = kwargs[field]
            
            # Sign up user
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata
                }
            })
            
            if response.user:
                # Create user profile
                profile = UserProfile(
                    id=response.user.id,
                    email=response.user.email,
                    username=user_metadata.get('username'),
                    full_name=user_metadata.get('full_name'),
                    avatar_url=user_metadata.get('avatar_url'),
                    bio=user_metadata.get('bio'),
                    website=user_metadata.get('website'),
                    is_email_verified=response.user.email_confirmed_at is not None,
                    created_at=response.user.created_at
                )
                
                # Create session if user is confirmed
                if response.session:
                    self._current_session = AuthSession(
                        access_token=response.session.access_token,
                        refresh_token=response.session.refresh_token,
                        user=profile,
                        expires_at=response.session.expires_at
                    )
                    
                    # Log activity
                    await self._log_activity("user_signup", "auth", response.user.id)
                    
                    return self._current_session
                else:
                    logger.info(f"User {email} signed up successfully. Email confirmation required.")
                    raise AuthError("Email confirmation required. Please check your email.")
            
            raise AuthError("Registration failed")
            
        except AuthApiError as e:
            error_msg = str(e)
            if "already_registered" in error_msg:
                raise AuthError("Email is already registered")
            elif "signup_disabled" in error_msg:
                raise AuthError("New registrations are currently disabled")
            else:
                raise AuthError(f"Registration failed: {error_msg}")
        except Exception as e:
            logger.error(f"Sign up error: {e}")
            raise AuthError(f"Registration failed: {str(e)}")
    
    async def sign_in(self, email: str, password: str) -> AuthSession:
        """Sign in user with email and password"""
        try:
            if not self.validate_email(email):
                raise AuthError("Invalid email format")
            
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                # Get user profile
                profile_data = await self._get_user_profile(response.user.id)
                
                profile = UserProfile(
                    id=response.user.id,
                    email=response.user.email,
                    username=profile_data.get('username'),
                    full_name=profile_data.get('full_name'),
                    avatar_url=profile_data.get('avatar_url'),
                    bio=profile_data.get('bio'),
                    website=profile_data.get('website'),
                    is_email_verified=response.user.email_confirmed_at is not None,
                    created_at=response.user.created_at,
                    last_login=datetime.now().isoformat()
                )
                
                self._current_session = AuthSession(
                    access_token=response.session.access_token,
                    refresh_token=response.session.refresh_token,
                    user=profile,
                    expires_at=response.session.expires_at
                )
                
                # Update last login
                await self._update_last_login(response.user.id)
                
                # Log activity
                await self._log_activity("user_signin", "auth", response.user.id)
                
                logger.info(f"User {email} signed in successfully")
                return self._current_session
            
            raise AuthError("Invalid credentials")
            
        except AuthApiError as e:
            error_msg = str(e)
            if "invalid_credentials" in error_msg or "Invalid login credentials" in error_msg:
                raise AuthError("Invalid email or password")
            elif "email_not_confirmed" in error_msg:
                raise AuthError("Please verify your email address before signing in")
            elif "too_many_requests" in error_msg:
                raise AuthError("Too many login attempts. Please try again later")
            else:
                raise AuthError(f"Sign in failed: {error_msg}")
        except Exception as e:
            logger.error(f"Sign in error: {e}")
            raise AuthError(f"Sign in failed: {str(e)}")
    
    async def sign_out(self) -> bool:
        """Sign out current user"""
        try:
            if self._current_session:
                # Log activity before signing out
                await self._log_activity("user_signout", "auth", self._current_session.user.id)
            
            response = self.client.auth.sign_out()
            self._current_session = None
            
            logger.info("User signed out successfully")
            return True
            
        except Exception as e:
            logger.error(f"Sign out error: {e}")
            return False
    
    async def refresh_session(self) -> Optional[AuthSession]:
        """Refresh current session"""
        try:
            if not self._current_session:
                return None
            
            response = self.client.auth.refresh_session(self._current_session.refresh_token)
            
            if response.session:
                self._current_session.access_token = response.session.access_token
                self._current_session.refresh_token = response.session.refresh_token
                self._current_session.expires_at = response.session.expires_at
                
                logger.info("Session refreshed successfully")
                return self._current_session
            
            return None
            
        except Exception as e:
            logger.error(f"Session refresh error: {e}")
            self._current_session = None
            return None
    
    async def reset_password(self, email: str) -> bool:
        """Send password reset email"""
        try:
            if not self.validate_email(email):
                raise AuthError("Invalid email format")
            
            response = self.client.auth.reset_password_email(email)
            
            logger.info(f"Password reset email sent to {email}")
            return True
            
        except AuthApiError as e:
            logger.error(f"Password reset error: {e}")
            raise AuthError(f"Failed to send password reset email: {str(e)}")
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            return False
    
    async def update_password(self, new_password: str) -> bool:
        """Update user password"""
        try:
            if not self._current_session:
                raise AuthError("No authenticated user")
            
            is_valid, password_errors = self.validate_password(new_password)
            if not is_valid:
                raise AuthError("Password validation failed: " + "; ".join(password_errors))
            
            response = self.client.auth.update_user({
                "password": new_password
            })
            
            if response.user:
                # Log activity
                await self._log_activity("password_update", "auth", self._current_session.user.id)
                
                logger.info("Password updated successfully")
                return True
            
            return False
            
        except AuthApiError as e:
            logger.error(f"Password update error: {e}")
            raise AuthError(f"Failed to update password: {str(e)}")
        except Exception as e:
            logger.error(f"Password update error: {e}")
            return False
    
    async def update_profile(self, **kwargs) -> Optional[UserProfile]:
        """Update user profile"""
        try:
            if not self._current_session:
                raise AuthError("No authenticated user")
            
            user_id = self._current_session.user.id
            
            # Validate username if being updated
            if 'username' in kwargs and kwargs['username']:
                is_valid, username_errors = self.validate_username(kwargs['username'])
                if not is_valid:
                    raise AuthError("Username validation failed: " + "; ".join(username_errors))
                
                # Check if username is taken by another user
                if await self.is_username_taken(kwargs['username'], exclude_user_id=user_id):
                    raise AuthError("Username is already taken")
            
            # Update profile in database
            update_data = {}
            allowed_fields = ['username', 'full_name', 'bio', 'website', 'avatar_url']
            for field in allowed_fields:
                if field in kwargs:
                    update_data[field] = kwargs[field]
            
            if update_data:
                update_data['updated_at'] = datetime.now().isoformat()
                
                response = self.client.table('profiles').update(update_data).eq('id', user_id).execute()
                
                if response.data:
                    # Update current session user data
                    for field, value in update_data.items():
                        if hasattr(self._current_session.user, field):
                            setattr(self._current_session.user, field, value)
                    
                    # Log activity
                    await self._log_activity("profile_update", "profile", user_id, {"fields": list(update_data.keys())})
                    
                    logger.info(f"Profile updated for user {user_id}")
                    return self._current_session.user
            
            return self._current_session.user
            
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            raise AuthError(f"Failed to update profile: {str(e)}")
    
    async def delete_account(self) -> bool:
        """Delete user account"""
        try:
            if not self._current_session:
                raise AuthError("No authenticated user")
            
            user_id = self._current_session.user.id
            
            # Log activity before deletion
            await self._log_activity("account_deletion", "auth", user_id)
            
            # Delete user account (this will cascade delete related data due to FK constraints)
            response = self.client.auth.admin.delete_user(user_id)
            
            # Clear current session
            self._current_session = None
            
            logger.info(f"Account deleted for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Account deletion error: {e}")
            return False
    
    async def is_username_taken(self, username: str, exclude_user_id: Optional[str] = None) -> bool:
        """Check if username is already taken"""
        try:
            query = self.client.table('profiles').select('id').eq('username', username)
            
            if exclude_user_id:
                query = query.neq('id', exclude_user_id)
            
            response = query.execute()
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Username check error: {e}")
            return True  # Assume taken on error to be safe
    
    async def get_user_by_username(self, username: str) -> Optional[UserProfile]:
        """Get user profile by username"""
        try:
            response = self.client.table('profiles').select('*').eq('username', username).execute()
            
            if response.data:
                data = response.data[0]
                return UserProfile(
                    id=data['id'],
                    email="",  # Don't expose email in public profile
                    username=data.get('username'),
                    full_name=data.get('full_name'),
                    avatar_url=data.get('avatar_url'),
                    bio=data.get('bio'),
                    website=data.get('website'),
                    created_at=data.get('created_at')
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Get user by username error: {e}")
            return None
    
    async def verify_email_token(self, token: str, type: str = "email") -> bool:
        """Verify email confirmation token"""
        try:
            response = self.client.auth.verify_otp({
                "token": token,
                "type": type
            })
            
            if response.user:
                logger.info(f"Email verified for user {response.user.id}")
                return True
            
            return False
            
        except AuthApiError as e:
            logger.error(f"Email verification error: {e}")
            return False
    
    async def resend_confirmation_email(self, email: str) -> bool:
        """Resend email confirmation"""
        try:
            if not self.validate_email(email):
                raise AuthError("Invalid email format")
            
            response = self.client.auth.resend({
                "type": "signup",
                "email": email
            })
            
            logger.info(f"Confirmation email resent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Resend confirmation error: {e}")
            return False
    
    async def change_email(self, new_email: str) -> bool:
        """Change user email address"""
        try:
            if not self._current_session:
                raise AuthError("No authenticated user")
            
            if not self.validate_email(new_email):
                raise AuthError("Invalid email format")
            
            response = self.client.auth.update_user({
                "email": new_email
            })
            
            if response.user:
                self._current_session.user.email = new_email
                self._current_session.user.is_email_verified = False
                
                # Log activity
                await self._log_activity("email_change", "auth", self._current_session.user.id)
                
                logger.info(f"Email change initiated for user {self._current_session.user.id}")
                return True
            
            return False
            
        except AuthApiError as e:
            logger.error(f"Email change error: {e}")
            raise AuthError(f"Failed to change email: {str(e)}")
    
    async def get_user_settings(self) -> Optional[Dict[str, Any]]:
        """Get user settings"""
        try:
            if not self._current_session:
                return None
            
            response = self.client.table('user_settings').select('*').eq('user_id', self._current_session.user.id).execute()
            
            if response.data:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Get user settings error: {e}")
            return None
    
    async def update_user_settings(self, settings: Dict[str, Any]) -> bool:
        """Update user settings"""
        try:
            if not self._current_session:
                raise AuthError("No authenticated user")
            
            user_id = self._current_session.user.id
            settings['updated_at'] = datetime.now().isoformat()
            
            response = self.client.table('user_settings').upsert({
                'user_id': user_id,
                **settings
            }).execute()
            
            if response.data:
                # Log activity
                await self._log_activity("settings_update", "settings", user_id)
                
                logger.info(f"Settings updated for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Update user settings error: {e}")
            return False
    
    async def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get current session information"""
        if not self._current_session:
            return None
        
        return {
            "user": asdict(self._current_session.user),
            "expires_at": self._current_session.expires_at,
            "token_type": self._current_session.token_type,
            "is_authenticated": True
        }
    
    async def check_session_validity(self) -> bool:
        """Check if current session is still valid"""
        if not self._current_session:
            return False
        
        # Check if token is expired
        current_time = datetime.now().timestamp()
        if current_time >= self._current_session.expires_at:
            # Try to refresh session
            refreshed_session = await self.refresh_session()
            return refreshed_session is not None
        
        return True
    
    # Private helper methods
    async def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile data from database"""
        try:
            response = self.client.table('profiles').select('*').eq('id', user_id).execute()
            
            if response.data:
                return response.data[0]
            
            return {}
            
        except Exception as e:
            logger.error(f"Get user profile error: {e}")
            return {}
    
    async def _update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp"""
        try:
            self.client.table('profiles').update({
                'updated_at': datetime.now().isoformat()
            }).eq('id', user_id).execute()
            
        except Exception as e:
            logger.error(f"Update last login error: {e}")
    
    async def _log_activity(self, action: str, resource_type: str, user_id: str, details: Optional[Dict] = None) -> None:
        """Log user activity"""
        try:
            activity_data = {
                'user_id': user_id,
                'action': action,
                'resource_type': resource_type,
                'details': details or {},
                'created_at': datetime.now().isoformat()
            }
            
            self.client.table('activity_log').insert(activity_data).execute()
            
        except Exception as e:
            logger.error(f"Activity logging error: {e}")
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash password with salt (for additional security layers)"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return password_hash.hex(), salt
    
    def verify_password_hash(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        expected_hash, _ = self.hash_password(password, salt)
        return secrets.compare_digest(expected_hash, password_hash)


# Utility functions for use in main application
def create_auth_manager(supabase_url: str, supabase_key: str) -> SupabaseAuth:
    """Factory function to create auth manager instance"""
    return SupabaseAuth(supabase_url, supabase_key)

def require_auth(auth_manager: SupabaseAuth):
    """Decorator to require authentication for functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not auth_manager.is_authenticated:
                raise AuthError("Authentication required")
            
            # Check session validity
            if not await auth_manager.check_session_validity():
                raise AuthError("Session expired")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Example usage and testing
async def main():
    """Example usage of the authentication module"""
    # This would be replaced with your actual Supabase credentials
    SUPABASE_URL = "your-supabase-url"
    SUPABASE_KEY = "your-supabase-anon-key"
    
    try:
        # Create auth manager
        auth = create_auth_manager(SUPABASE_URL, SUPABASE_KEY)
        
        print("Testing authentication module...")
        
        # Test sign up
        print("\n1. Testing sign up...")
        try:
            session = await auth.sign_up(
                email="test@example.com",
                password="TestPassword123!",
                full_name="Test User",
                username="testuser"
            )
            print(f"✓ Sign up successful: {session.user.email}")
        except AuthError as e:
            print(f"✗ Sign up failed: {e}")
        
        # Test sign in
        print("\n2. Testing sign in...")
        try:
            session = await auth.sign_in("test@example.com", "TestPassword123!")
            print(f"✓ Sign in successful: {session.user.email}")
        except AuthError as e:
            print(f"✗ Sign in failed: {e}")
        
        # Test profile update
        if auth.is_authenticated:
            print("\n3. Testing profile update...")
            try:
                updated_profile = await auth.update_profile(
                    bio="This is my updated bio",
                    website="https://example.com"
                )
                print(f"✓ Profile updated: {updated_profile.bio}")
            except AuthError as e:
                print(f"✗ Profile update failed: {e}")
        
        # Test session info
        print("\n4. Testing session info...")
        session_info = await auth.get_session_info()
        if session_info:
            print(f"✓ Session active: {session_info['user']['email']}")
        
        # Test sign out
        print("\n5. Testing sign out...")
        if await auth.sign_out():
            print("✓ Sign out successful")
        else:
            print("✗ Sign out failed")
            
        print("\nAuthentication module test completed!")
        
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    asyncio.run(main())