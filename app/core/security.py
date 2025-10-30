"""Core security utilities for HMAC signing and verification"""
import hmac
import hashlib
import time
import json
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status
import base64
import urllib.parse


class ApprovalTokenError(Exception):
    """Custom exception for approval token errors"""
    pass


class ApprovalTokenService:
    """Service for creating and verifying approval tokens using HMAC"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
        self.token_expiry_hours = 24  # Tokens expire after 24 hours

    def generate_approval_token(
        self,
        submission_id: int,
        action: str,
        approver_type: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a secure approval token

        Args:
            submission_id: ID of the submission
            action: Action to perform (approve/reject)
            approver_type: Type of approver (leader/chm)
            additional_data: Additional data to include in token

        Returns:
            Encoded token string
        """
        timestamp = int(time.time())
        expiry = timestamp + (self.token_expiry_hours * 3600)

        # Create payload
        payload = {
            'submission_id': submission_id,
            'action': action,
            'approver_type': approver_type,
            'timestamp': timestamp,
            'expiry': expiry
        }

        if additional_data:
            payload.update(additional_data)

        # Create signature
        message = self._create_message_from_payload(payload)
        signature = hmac.new(
            self.secret_key,
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        # Add signature to payload
        payload['sig'] = signature

        # Encode as JSON then base64 URL-safe
        payload_json = json.dumps(payload, separators=(',', ':'))
        encoded = base64.urlsafe_b64encode(
            payload_json.encode()
        ).decode()

        return encoded

    def verify_approval_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode an approval token

        Args:
            token: The encoded token string

        Returns:
            Decoded payload if valid

        Raises:
            ApprovalTokenError: If token is invalid or expired
        """
        try:
            # Decode token
            decoded = base64.urlsafe_b64decode(token.encode()).decode()
            payload = json.loads(decoded)

            # Check required fields
            required_fields = ['submission_id', 'action', 'approver_type', 'timestamp', 'expiry', 'sig']
            for field in required_fields:
                if field not in payload:
                    raise ApprovalTokenError(f"Missing required field: {field}")

            # Check expiry
            if int(time.time()) > payload['expiry']:
                raise ApprovalTokenError("Token has expired")

            # Verify signature
            message = self._create_message_from_payload(payload)
            expected_sig = hmac.new(
                self.secret_key,
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(payload['sig'], expected_sig):
                raise ApprovalTokenError("Invalid token signature")

            # Remove signature from return payload
            result = payload.copy()
            result.pop('sig')
            result['is_valid'] = True

            return result

        except (base64.binascii.Error, ValueError, KeyError) as e:
            raise ApprovalTokenError(f"Invalid token format: {str(e)}")

    def _create_message_from_payload(self, payload: Dict[str, Any]) -> str:
        """Create a consistent message string from payload for signing"""
        # Remove signature if present
        payload_copy = payload.copy()
        payload_copy.pop('sig', None)

        # Sort keys for consistent ordering
        sorted_items = sorted(payload_copy.items())

        # Create message string
        parts = []
        for key, value in sorted_items:
            parts.append(f"{key}={value}")

        return "&".join(parts)

    def generate_approval_url(
        self,
        submission_id: int,
        action: str,
        approver_type: str,
        base_url: str = "http://localhost:8000"
    ) -> str:
        """
        Generate a complete approval URL

        Args:
            submission_id: ID of the submission
            action: Action to perform (approve/reject)
            approver_type: Type of approver (leader/chm)
            base_url: Base URL for the application

        Returns:
            Complete approval URL
        """
        token = self.generate_approval_token(submission_id, action, approver_type)

        if approver_type == "leader":
            path = f"/approve/leader/{submission_id}"
        elif approver_type == "chm":
            path = f"/approve/chm/{submission_id}"
        else:
            raise ValueError(f"Unknown approver type: {approver_type}")

        return f"{base_url}{path}?token={token}&action={action}"


# Global instance - will be initialized in main.py
approval_token_service: Optional[ApprovalTokenService] = None


def get_approval_token_service() -> ApprovalTokenService:
    """Get the global approval token service instance"""
    global approval_token_service
    if approval_token_service is None:
        # Fallback initialization if service wasn't initialized during startup
        try:
            from config import SIGNING_SECRET
            approval_token_service = ApprovalTokenService(SIGNING_SECRET)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize approval token service: {e}")
    return approval_token_service


def verify_approval_token_for_request(token: str) -> Dict[str, Any]:
    """
    Verify token for web requests - raises HTTPException for invalid tokens

    Args:
        token: The token to verify

    Returns:
        Decoded payload if valid

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        service = get_approval_token_service()
        return service.verify_approval_token(token)
    except ApprovalTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid approval token: {str(e)}"
        )