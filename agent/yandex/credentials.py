"""Yandex Cloud credentials management.

Supports multiple authentication methods:
- API Key (simplest, recommended for development)
- IAM Token (short-lived, for production)
- Service Account Key File (for automated systems)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class YandexCredentials:
    """Credentials for Yandex Cloud services.
    
    Attributes:
        api_key: Yandex Cloud API key (simplest auth method)
        iam_token: IAM token (alternative to api_key)
        folder_id: Yandex Cloud folder ID (required for billing)
        service_account_key_file: Path to SA key JSON file
    
    Example:
        >>> creds = YandexCredentials.from_env()
        >>> metadata = creds.get_auth_metadata()
        >>> # Use metadata in gRPC calls
    """
    
    api_key: str | None = None
    iam_token: str | None = None
    folder_id: str | None = None
    service_account_key_file: str | None = None
    
    @classmethod
    def from_env(cls) -> YandexCredentials:
        """Load credentials from environment variables.
        
        Environment variables:
            YC_API_KEY: Yandex Cloud API key
            YC_IAM_TOKEN: IAM token (alternative)
            YC_FOLDER_ID: Folder ID for billing
            YC_SA_KEY_FILE: Path to service account key file
        
        Returns:
            YandexCredentials instance
        
        Raises:
            ValueError: If no valid credentials found
        """
        creds = cls(
            api_key=os.getenv("YC_API_KEY"),
            iam_token=os.getenv("YC_IAM_TOKEN"),
            folder_id=os.getenv("YC_FOLDER_ID"),
            service_account_key_file=os.getenv("YC_SA_KEY_FILE"),
        )
        
        # Validate that we have at least one auth method
        if not creds.has_credentials():
            raise ValueError(
                "No Yandex Cloud credentials found. "
                "Set YC_API_KEY, YC_IAM_TOKEN, or YC_SA_KEY_FILE environment variable."
            )
        
        return creds
    
    def has_credentials(self) -> bool:
        """Check if any authentication method is configured."""
        return bool(
            self.api_key 
            or self.iam_token 
            or self.service_account_key_file
        )
    
    def get_auth_metadata(self) -> tuple[str, str]:
        """Get gRPC metadata tuple for authentication.
        
        Returns:
            Tuple of (header_name, header_value) for gRPC metadata
        
        Raises:
            ValueError: If no valid credentials configured
        """
        if self.api_key:
            return ("authorization", f"Api-Key {self.api_key}")
        elif self.iam_token:
            return ("authorization", f"Bearer {self.iam_token}")
        elif self.service_account_key_file:
            # For SA key file, we need to get IAM token first
            # This is a simplified version - in production, use yandexcloud SDK
            raise NotImplementedError(
                "Service account key file authentication requires IAM token exchange. "
                "Use YC_API_KEY or YC_IAM_TOKEN instead, or implement token exchange."
            )
        
        raise ValueError(
            "No valid credentials configured. "
            "Set api_key, iam_token, or service_account_key_file."
        )
    
    def get_grpc_metadata(self) -> Sequence[tuple[str, str]]:
        """Get full gRPC metadata including folder_id.
        
        Returns:
            List of metadata tuples for gRPC calls
        """
        metadata: list[tuple[str, str]] = [self.get_auth_metadata()]
        
        if self.folder_id:
            metadata.append(("x-folder-id", self.folder_id))
        
        return metadata
    
    def validate(self) -> None:
        """Validate credentials configuration.
        
        Raises:
            ValueError: If credentials are invalid or incomplete
        """
        if not self.has_credentials():
            raise ValueError("No authentication credentials provided")
        
        if not self.folder_id:
            raise ValueError(
                "folder_id is required for Yandex Cloud services. "
                "Set YC_FOLDER_ID environment variable."
            )
