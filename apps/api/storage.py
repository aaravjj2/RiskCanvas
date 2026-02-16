"""
Storage abstraction for RiskCanvas artifacts.
Supports local filesystem (DEMO) and Azure Blob Storage (production).
"""
import hashlib
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote


class IStorage(ABC):
    """Storage interface for report bundles and artifacts."""

    @abstractmethod
    def store(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> Dict:
        """
        Store content at key.
        Returns: {"url": str, "provider": str, "stored_at": str}
        """
        pass

    @abstractmethod
    def retrieve(self, key: str) -> bytes:
        """Retrieve content by key."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    def get_download_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Get signed/proxy download URL.
        expires_in: seconds (for SAS tokens)
        """
        pass

    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with optional prefix filter."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key. Returns True if deleted, False if not found."""
        pass


class LocalStorage(IStorage):
    """
    Local filesystem storage (DEMO mode).
    Stores in ./data/storage (gitignored).
    """

    def __init__(self, base_path: str = "./data/storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _key_to_path(self, key: str) -> Path:
        """Convert storage key to filesystem path."""
        # Sanitize key to prevent directory traversal
        safe_key = key.replace("..", "").replace("\\", "/")
        return self.base_path / safe_key

    def store(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> Dict:
        """Store content to local filesystem."""
        path = self._key_to_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        path.write_bytes(content)

        # Store metadata alongside
        meta_path = path.with_suffix(path.suffix + ".meta.json")
        meta = {
            "key": key,
            "content_type": content_type,
            "size": len(content),
            "stored_at": datetime.utcnow().isoformat() + "Z",
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        meta_path.write_text(json.dumps(meta, indent=2))

        return {
            "url": f"local://{key}",
            "provider": "local",
            "stored_at": meta["stored_at"],
            "sha256": meta["sha256"],
        }

    def retrieve(self, key: str) -> bytes:
        """Retrieve content from local filesystem."""
        path = self._key_to_path(key)
        if not path.exists():
            raise FileNotFoundError(f"Key not found: {key}")
        return path.read_bytes()

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return self._key_to_path(key).exists()

    def get_download_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Return proxy URL for local storage.
        In DEMO mode, API serves files via /storage/files/{key}.
        """
        # URL-encode the key for safe URL construction
        encoded_key = quote(key, safe="/")
        return f"/storage/files/{encoded_key}"

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with optional prefix filter."""
        keys = []
        for path in self.base_path.rglob("*"):
            if path.is_file() and not path.name.endswith(".meta.json"):
                # Convert path to key
                rel_path = path.relative_to(self.base_path)
                key = str(rel_path).replace("\\", "/")
                if key.startswith(prefix):
                    keys.append(key)
        return sorted(keys)

    def delete(self, key: str) -> bool:
        """Delete key and metadata."""
        path = self._key_to_path(key)
        meta_path = path.with_suffix(path.suffix + ".meta.json")

        deleted = False
        if path.exists():
            path.unlink()
            deleted = True
        if meta_path.exists():
            meta_path.unlink()

        return deleted


class AzureBlobStorage(IStorage):
    """
    Azure Blob Storage provider (production mode).
    Requires: AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_NAME + KEY.
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        account_name: Optional[str] = None,
        account_key: Optional[str] = None,
        container_name: str = "riskcanvas-artifacts",
    ):
        """
        Initialize Azure Blob Storage client.
        Falls back to environment variables if not provided.
        """
        # NOTE: Azure SDK import is conditional (only if configured)
        try:
            from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
            self._BlobServiceClient = BlobServiceClient
            self._generate_blob_sas = generate_blob_sas
            self._BlobSasPermissions = BlobSasPermissions
        except ImportError:
            raise RuntimeError(
                "Azure Blob Storage requires azure-storage-blob package. "
                "Install with: pip install azure-storage-blob"
            )

        self.container_name = container_name
        self.account_name = account_name or os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.account_key = account_key or os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

        # Initialize client
        conn_str = connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if conn_str:
            self.client = self._BlobServiceClient.from_connection_string(conn_str)
        elif self.account_name and self.account_key:
            self.client = self._BlobServiceClient(
                account_url=f"https://{self.account_name}.blob.core.windows.net",
                credential=self.account_key,
            )
        else:
            raise ValueError(
                "Azure Blob Storage requires either AZURE_STORAGE_CONNECTION_STRING "
                "or AZURE_STORAGE_ACCOUNT_NAME + AZURE_STORAGE_ACCOUNT_KEY"
            )

        self.container_client = self.client.get_container_client(self.container_name)

        # Create container if it doesn't exist
        try:
            self.container_client.create_container()
        except Exception:
            pass  # Container already exists

    def store(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> Dict:
        """Upload content to Azure Blob Storage."""
        blob_client = self.container_client.get_blob_client(key)

        # Upload with metadata
        blob_client.upload_blob(
            content,
            overwrite=True,
            content_settings={"content_type": content_type},
            metadata={
                "sha256": hashlib.sha256(content).hexdigest(),
                "stored_at": datetime.utcnow().isoformat() + "Z",
            },
        )

        return {
            "url": blob_client.url,
            "provider": "azure",
            "stored_at": datetime.utcnow().isoformat() + "Z",
            "sha256": hashlib.sha256(content).hexdigest(),
        }

    def retrieve(self, key: str) -> bytes:
        """Download content from Azure Blob Storage."""
        blob_client = self.container_client.get_blob_client(key)
        return blob_client.download_blob().readall()

    def exists(self, key: str) -> bool:
        """Check if blob exists."""
        blob_client = self.container_client.get_blob_client(key)
        return blob_client.exists()

    def get_download_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate SAS token URL for blob download."""
        blob_client = self.container_client.get_blob_client(key)

        # Generate SAS token
        sas_token = self._generate_blob_sas(
            account_name=self.account_name,
            container_name=self.container_name,
            blob_name=key,
            account_key=self.account_key,
            permission=self._BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(seconds=expires_in),
        )

        return f"{blob_client.url}?{sas_token}"

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all blobs with optional prefix filter."""
        blobs = self.container_client.list_blobs(name_starts_with=prefix)
        return sorted([blob.name for blob in blobs])

    def delete(self, key: str) -> bool:
        """Delete blob."""
        blob_client = self.container_client.get_blob_client(key)
        try:
            blob_client.delete_blob()
            return True
        except Exception:
            return False


def get_storage_provider(force_local: bool = False) -> IStorage:
    """
    Factory function to get appropriate storage provider.
    Returns LocalStorage in DEMO mode or when force_local=True.
    Returns AzureBlobStorage in production when Azure credentials are available.
    """
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"

    if demo_mode or force_local:
        return LocalStorage()

    # Check for Azure configuration
    has_azure = (
        os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        or (os.getenv("AZURE_STORAGE_ACCOUNT_NAME") and os.getenv("AZURE_STORAGE_ACCOUNT_KEY"))
    )

    if has_azure:
        try:
            return AzureBlobStorage()
        except Exception as e:
            # Fall back to local if Azure fails
            print(f"Warning: Azure Blob Storage initialization failed: {e}")
            print("Falling back to LocalStorage")
            return LocalStorage()

    # Default to local storage
    return LocalStorage()
