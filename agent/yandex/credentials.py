"""Yandex Cloud credentials management with Pydantic validation.

Supports multiple authentication methods:
- API Key (simplest, recommended for development)
- IAM Token (short-lived, for production)
- Service Account Key File (for automated systems)
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from collections.abc import Sequence


class YandexCredentials(BaseModel):
    """Credentials for Yandex Cloud services with validation.
    
    Attributes:
        api_key: Yandex Cloud API key (simplest auth method)
        iam_token: IAM token (alternative to api_key)
        folder_id: Yandex Cloud folder ID (required for billing)
        service_account_key_file: Path to SA key JSON file
    
    Example:
        >>> creds = YandexCredentials.from_env()
        >>> metadata = creds.get_auth_metadata()
    """
    
    api_key: str | None = Field(default=None, description="Yandex Cloud API key")
    iam_token: str | None = Field(default=None, description="IAM token")
    folder_id: str | None = Field(default=None, description="Folder ID for billing")
    service_account_key_file: str | None = Field(default=None, description="Path to SA key file")
    
    model_config = {"frozen": False, "extra": "ignore"}
    
    @model_validator(mode="after")
    def validate_has_credentials(self) -> "YandexCredentials":
        """Ensure at least one auth method is configured."""
        if not self.has_credentials():
            raise ValueError(
                "No Yandex Cloud credentials found. "
                "Provide api_key, iam_token, or service_account_key_file."
            )
        return self

    def has_credentials(self) -> bool:
        """Check if any authentication method is configured."""
        return bool(self.api_key or self.iam_token or self.service_account_key_file)
    
    def get_auth_metadata(self) -> Sequence[tuple[str, str]]:
        """Get gRPC metadata for authentication.
        
        Returns:
            Sequence of (key, value) tuples for gRPC metadata.
            
        Raises:
            ValueError: If no credentials are configured.
        """
        if self.api_key:
            return [("authorization", f"Api-Key {self.api_key}")]
        elif self.iam_token:
            return [("authorization", f"Bearer {self.iam_token}")]
        elif self.service_account_key_file:
            # TODO: Implement SA key file auth (requires JWT generation)
            raise NotImplementedError("Service account key file auth not yet implemented")
        else:
            raise ValueError("No credentials configured")
    
    def get_grpc_metadata(self) -> Sequence[tuple[str, str]]:
        """Get full gRPC metadata including folder_id.
        
        Returns:
            Sequence of (key, value) tuples for gRPC calls.
        """
        metadata = list(self.get_auth_metadata())
        if self.folder_id:
            metadata.append(("x-folder-id", self.folder_id))
        return metadata
    
    @classmethod
    def from_env(cls) -> "YandexCredentials":
        """Create credentials from environment variables.
        
        Environment variables:
            YANDEX_API_KEY: API key
            YANDEX_IAM_TOKEN: IAM token
            YANDEX_FOLDER_ID: Folder ID
            YANDEX_SA_KEY_FILE: Path to service account key file
            
        Returns:
            YandexCredentials instance.
            
        Raises:
            ValueError: If no credentials found in environment.
        """
        return cls(
            api_key=os.getenv("YANDEX_API_KEY"),
            iam_token=os.getenv("YANDEX_IAM_TOKEN"),
            folder_id=os.getenv("YANDEX_FOLDER_ID"),
            service_account_key_file=os.getenv("YANDEX_SA_KEY_FILE"),
        )


# Global singleton for convenience
_credentials: YandexCredentials | None = None


def get_credentials() -> YandexCredentials:
    """Get or create global credentials instance.
    
    Returns:
        YandexCredentials singleton instance.
    """
    global _credentials
    if _credentials is None:
        _credentials = YandexCredentials.from_env()
    return _credentials


def reset_credentials() -> None:
    """Reset global credentials (useful for testing)."""
    global _credentials
    _credentials = None
