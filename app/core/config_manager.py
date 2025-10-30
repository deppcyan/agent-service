import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple
import aiohttp
from datetime import datetime

from app.utils.logger import logger
from app.storage.downloader import downloader
import tempfile

APP_CONFIG_PATH = Path("config/app.json")
UPDATE_CONFIG_PATH = Path("config/update.json")

class ConfigManager:
    def __init__(self):
        self._app_id: str = "agent-service"
        self._current_version: int = 0
        self._remote_config_url: str = ""
        self._in_memory_refreshers: List[Callable[[], None]] = []
        self._load_local_configs()

    def _load_local_configs(self) -> None:
        # Load read-only app.json for basic app info
        try:
            if APP_CONFIG_PATH.exists():
                with open(APP_CONFIG_PATH, "r") as f:
                    app_data = json.load(f)
                    self._app_id = app_data.get("appId", self._app_id)
                    # remoteConfigUrl is always read from app.json (read-only)
                    self._remote_config_url = app_data.get("remoteConfigUrl", "")
                    # Only use app.json version as fallback if update.json doesn't exist
                    fallback_version = int(app_data.get("version", 0))
            else:
                fallback_version = 0
                self._remote_config_url = ""
        except Exception as e:
            logger.error(f"Failed to read app config: {e}")
            fallback_version = 0
            self._remote_config_url = ""
        
        # Load or create update.json for version tracking only
        try:
            if UPDATE_CONFIG_PATH.exists():
                with open(UPDATE_CONFIG_PATH, "r") as f:
                    update_data = json.load(f)
                    self._current_version = int(update_data.get("version", fallback_version))
            else:
                # Create update.json with fallback version
                self._current_version = fallback_version
                self._persist_update_config()
        except Exception as e:
            logger.error(f"Failed to read update config: {e}")
            self._current_version = fallback_version
            self._persist_update_config()

    def get_status(self) -> Dict[str, Any]:
        # Read latest update info from update.json
        last_updated = None
        try:
            if UPDATE_CONFIG_PATH.exists():
                with open(UPDATE_CONFIG_PATH, "r") as f:
                    update_data = json.load(f)
                    last_updated = update_data.get("lastUpdated")
        except Exception as e:
            logger.error(f"Failed to read update config for status: {e}")
        
        return {
            "appId": self._app_id,
            "version": self._current_version,
            "remoteConfigUrl": self._remote_config_url,
            "lastUpdated": last_updated
        }


    def register_refresher(self, refresher: Callable[[], None]) -> None:
        if refresher not in self._in_memory_refreshers:
            self._in_memory_refreshers.append(refresher)

    def _persist_update_config(self) -> None:
        """Persist version to update.json"""
        try:
            UPDATE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(UPDATE_CONFIG_PATH, "w") as f:
                json.dump({
                    "version": self._current_version,
                    "lastUpdated": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist update config: {e}")
    
    def update_version(self, new_version: int) -> None:
        """Update the version number and persist to update.json"""
        self._current_version = new_version
        self._persist_update_config()
        logger.info(f"Version updated to {new_version}")
    
    async def sync_from_remote(self) -> bool:
        """Sync configuration from remote URL and update version if newer version is available"""
        if not self._remote_config_url:
            logger.warning("Remote config URL not set, cannot sync")
            return False
        
        try:
            # Fetch remote configuration
            remote_config = await self._fetch_remote_json(self._remote_config_url)
            
            # Check if remote version is newer
            remote_version = int(remote_config.get("version", 0))
            if remote_version <= self._current_version:
                logger.info(f"Remote version {remote_version} is not newer than current version {self._current_version}")
                return True  # Not an error, just no update needed
            
            # Update to new version
            self.update_version(remote_version)
            
            # Refresh in-memory configurations
            self._refresh_in_memory()
            
            logger.info(f"Successfully synced from remote, updated to version {remote_version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync from remote: {e}")
            return False

    async def _fetch_remote_json(self, url: str) -> Dict[str, Any]:
        # Use unified downloader to support S3 and HTTP(S)
        import tempfile
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_path = tmp_file.name
        tmp_file.close()
        try:
            await downloader.download(url, tmp_path, job_id="config-sync")
            with open(tmp_path, "r", encoding="utf-8") as f:
                return json.load(f)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def _fetch_remote_bytes(self, url: str) -> bytes:
        # Use unified downloader to support S3 and HTTP(S)
        import tempfile
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_path = tmp_file.name
        tmp_file.close()
        try:
            await downloader.download(url, tmp_path, job_id="config-sync")
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _resolve_remote_file_url(self, path: str) -> str:
        # If remote file path is absolute URL, return as is; otherwise, resolve relative to remoteConfigUrl base
        if path.startswith("http://") or path.startswith("https://") or path.startswith("s3://"):
            return path
        # Derive base URL directory
        base = self._remote_config_url
        if base.endswith(".json"):
            base = base.rsplit("/", 1)[0]
        return f"{base}/{path}"

    def _refresh_in_memory(self) -> None:
        for refresher in self._in_memory_refreshers:
            try:
                refresher()
            except Exception as e:
                logger.error(f"Error in refresher: {e}")

# Global instance
config_manager = ConfigManager()
