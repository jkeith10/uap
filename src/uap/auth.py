"""Authentication and Authorization for UAP"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import get_config
from .logging_config import get_logger
from .exceptions import AuthenticationError, AuthorizationError

logger = get_logger(__name__)

security = HTTPBearer()


class TokenPayload:
    """JWT token payload"""
    
    def __init__(self, sub: str, exp: datetime, **kwargs):
        self.sub = sub  # Subject (user ID)
        self.exp = exp  # Expiration
        self.extra = kwargs


class AuthManager:
    """Authentication and authorization manager"""
    
    def __init__(self, config: Any):
        self.secret_key = config.security.jwt_secret
        self.algorithm = config.security.jwt_algorithm
        self.expiration = config.security.jwt_expiration
    
    def create_token(self, user_id: str, **extra_claims) -> str:
        """Create a JWT token"""
        exp = datetime.now(timezone.utc) + timedelta(seconds=self.expiration)
        
        payload = {
            "sub": user_id,
            "exp": exp,
            "iat": datetime.now(timezone.utc),
            **extra_claims
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        logger.info("Token created", user_id=user_id)
        return token
    
    def verify_token(self, token: str) -> TokenPayload:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            return TokenPayload(
                sub=payload["sub"],
                exp=datetime.fromtimestamp(payload["exp"], timezone.utc),
                **{k: v for k, v in payload.items() if k not in ["sub", "exp", "iat"]}
            )
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid token", error=str(e))
            raise AuthenticationError("Invalid token")
    
    def check_permission(self, token_payload: TokenPayload, required_permission: str) -> bool:
        """Check if token has required permission"""
        permissions = token_payload.extra.get("permissions", [])
        return required_permission in permissions


# Global auth manager
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get global auth manager"""
    if _auth_manager is None:
        config = get_config()
        return AuthManager(config)
    return _auth_manager


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenPayload:
    """Dependency for getting current authenticated user"""
    try:
        auth_manager = get_auth_manager()
        token = credentials.credentials
        return auth_manager.verify_token(token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_permission(permission: str):
    """Decorator to require specific permission"""
    async def permission_checker(
        current_user: TokenPayload = Depends(get_current_user)
    ):
        auth_manager = get_auth_manager()
        if not auth_manager.check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    
    return permission_checker

