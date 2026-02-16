"""
Tests for storage abstraction (v2.3+).
"""
import pytest
import hashlib
import json
from pathlib import Path
import tempfile
import shutil

from storage import LocalStorage, get_storage_provider


class TestLocalStorage:
    """Test LocalStorage provider."""
    
    def setup_method(self):
        """Create temporary storage directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = LocalStorage(base_path=self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_store_and_retrieve(self):
        """Test basic store and retrieve operations."""
        content = b"Hello, RiskCanvas!"
        key = "test/file.txt"
        
        # Store
        result = self.storage.store(key, content, "text/plain")
        
        assert result["provider"] == "local"
        assert result["url"] == f"local://{key}"
        assert "stored_at" in result
        assert result["sha256"] == hashlib.sha256(content).hexdigest()
        
        # Retrieve
        retrieved = self.storage.retrieve(key)
        assert retrieved == content
    
    def test_exists(self):
        """Test key existence check."""
        key = "test/exists.txt"
        
        assert not self.storage.exists(key)
        
        self.storage.store(key, b"content", "text/plain")
        
        assert self.storage.exists(key)
    
    def test_get_download_url(self):
        """Test download URL generation."""
        key = "test/download.txt"
        self.storage.store(key, b"content", "text/plain")
        
        url = self.storage.get_download_url(key)
        
        # Should return proxy URL
        assert url == "/storage/files/test/download.txt"
    
    def test_list_keys(self):
        """Test listing keys."""
        # Store multiple files
        self.storage.store("reports/bundle1/report.html", b"<html>1</html>", "text/html")
        self.storage.store("reports/bundle1/run.json", b"{}", "application/json")
        self.storage.store("reports/bundle2/report.html", b"<html>2</html>", "text/html")
        self.storage.store("other/file.txt", b"text", "text/plain")
        
        # List all
        all_keys = self.storage.list_keys()
        assert len(all_keys) == 4
        
        # List with prefix
        report_keys = self.storage.list_keys(prefix="reports/")
        assert len(report_keys) == 3
        assert all(k.startswith("reports/") for k in report_keys)
        
        bundle1_keys = self.storage.list_keys(prefix="reports/bundle1/")
        assert len(bundle1_keys) == 2
    
    def test_delete(self):
        """Test key deletion."""
        key = "test/delete.txt"
        
        # Store
        self.storage.store(key, b"content", "text/plain")
        assert self.storage.exists(key)
        
        # Delete
        deleted = self.storage.delete(key)
        assert deleted is True
        assert not self.storage.exists(key)
        
        # Delete non-existent
        deleted_again = self.storage.delete(key)
        assert deleted_again is False
    
    def test_deterministic_hashes(self):
        """Test that same content produces same hash."""
        content = b"Deterministic content"
        key1 = "test/hash1.txt"
        key2 = "test/hash2.txt"
        
        result1 = self.storage.store(key1, content, "text/plain")
        result2 = self.storage.store(key2, content, "text/plain")
        
        assert result1["sha256"] == result2["sha256"]
        assert result1["sha256"] == hashlib.sha256(content).hexdigest()
    
    def test_nested_paths(self):
        """Test storing in nested directory structure."""
        key = "level1/level2/level3/file.txt"
        content = b"Nested file"
        
        result = self.storage.store(key, content, "text/plain")
        assert result["provider"] == "local"
        
        retrieved = self.storage.retrieve(key)
        assert retrieved == content
        
        # Verify file exists in nested directory
        path = Path(self.temp_dir) / "level1" / "level2" / "level3" / "file.txt"
        assert path.exists()
    
    def test_metadata_file(self):
        """Test that metadata file is created alongside content."""
        key = "test/metadata.txt"
        content = b"Test content"
        
        self.storage.store(key, content, "text/plain")
        
        # Check metadata file exists
        meta_path = Path(self.temp_dir) / "test" / "metadata.txt.meta.json"
        assert meta_path.exists()
        
        # Verify metadata content
        meta = json.loads(meta_path.read_text())
        assert meta["key"] == key
        assert meta["content_type"] == "text/plain"
        assert meta["size"] == len(content)
        assert meta["sha256"] == hashlib.sha256(content).hexdigest()
        assert "stored_at" in meta


class TestStorageFactory:
    """Test storage provider factory."""
    
    def test_get_storage_demo_mode(self, monkeypatch):
        """Test that DEMO mode returns LocalStorage."""
        monkeypatch.setenv("DEMO_MODE", "true")
        
        storage = get_storage_provider()
        
        assert isinstance(storage, LocalStorage)
    
    def test_get_storage_no_azure(self, monkeypatch):
        """Test that missing Azure config returns LocalStorage."""
        monkeypatch.setenv("DEMO_MODE", "false")
        monkeypatch.delenv("AZURE_STORAGE_CONNECTION_STRING", raising=False)
        monkeypatch.delenv("AZURE_STORAGE_ACCOUNT_NAME", raising=False)
        
        storage = get_storage_provider()
        
        assert isinstance(storage, LocalStorage)
    
    def test_force_local(self):
        """Test force_local parameter."""
        storage = get_storage_provider(force_local=True)
        
        assert isinstance(storage, LocalStorage)


class TestReportBundleStorage:
    """Test report bundle storage integration."""
    
    def setup_method(self):
        """Set_up temporary storage."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = LocalStorage(base_path=self.temp_dir)
    
    def teardown_method(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_store_report_bundle(self):
        """Test storing complete report bundle."""
        from report_bundle import store_report_bundle_to_storage
        
        # Sample run data
        run_data = {
            "run_id": "run_abc123",
            "portfolio_id": "portfolio_xyz",
            "engine_version": "2.3.0",
            "run_params": {},
            "outputs": {
                "pricing": {"portfolio_value": 1000000.00},
                "var": {"var_95": -45000.00, "var_99": -75000.00}
            },
            "output_hash": "hash123",
            "created_at": "2026-02-16T12:00:00Z"
        }
        
        portfolio_data = {
            "assets": [
                {"symbol": "AAPL", "type": "stock", "quantity": 100, "price": 150.00}
            ]
        }
        
        report_bundle_id = "bundle_test_123"
        
        # Store bundle
        manifest = store_report_bundle_to_storage(
            report_bundle_id, run_data, portfolio_data, self.storage
        )
        
        # Verify manifest structure
        assert manifest["report_bundle_id"] == report_bundle_id
        assert manifest["run_id"] == run_data["run_id"]
        assert "storage" in manifest
        assert manifest["storage"]["provider"] == "local"
        assert "hashes" in manifest
        assert "report_html_hash" in manifest["hashes"]
        assert "run_json_hash" in manifest["hashes"]
        assert "manifest_hash" in manifest["hashes"]
        
        # Verify files exist
        assert self.storage.exists(f"reports/{report_bundle_id}/report.html")
        assert self.storage.exists(f"reports/{report_bundle_id}/run.json")
        assert self.storage.exists(f"reports/{report_bundle_id}/manifest.json")
    
    def test_retrieve_report_bundle(self):
        """Test retrieving report bundle from storage."""
        from report_bundle import store_report_bundle_to_storage, get_report_bundle_from_storage
        
        run_data = {
            "run_id": "run_retrieve",
            "portfolio_id": "portfolio_retrieve",
            "engine_version": "2.3.0",
            "run_params": {},
            "outputs": {"pricing": {"portfolio_value": 500000.00}},
            "output_hash": "hash_retrieve",
            "created_at": "2026-02-16T12:00:00Z"
        }
        
        portfolio_data = {"assets": []}
        report_bundle_id = "bundle_retrieve_test"
        
        # Store
        store_report_bundle_to_storage(
            report_bundle_id, run_data, portfolio_data, self.storage
        )
        
        # Retrieve
        manifest = get_report_bundle_from_storage(report_bundle_id, self.storage)
        
        assert manifest is not None
        assert manifest["report_bundle_id"] == report_bundle_id
        assert manifest["run_id"] == run_data["run_id"]
    
    def test_get_download_urls(self):
        """Test generating download URLs."""
        from report_bundle import store_report_bundle_to_storage, get_download_urls
        
        run_data = {
            "run_id": "run_download",
            "portfolio_id": "portfolio_download",
            "engine_version": "2.3.0",
            "run_params": {},
            "outputs": {},
            "output_hash": "hash_download",
            "created_at": "2026-02-16T12:00:00Z"
        }
        
        portfolio_data = {"assets": []}
        report_bundle_id = "bundle_download_test"
        
        # Store bundle
        store_report_bundle_to_storage(
            report_bundle_id, run_data, portfolio_data, self.storage
        )
        
        # Get download URLs
        urls = get_download_urls(report_bundle_id, expires_in=1800, storage=self.storage)
        
        assert "report.html" in urls
        assert "run.json" in urls
        assert "manifest.json" in urls
        assert all(url.startswith("/storage/files/") for url in urls.values())
