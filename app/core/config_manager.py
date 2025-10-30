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
UPDATE_CONFIG_PATH = Path("update/update.json")

class ConfigManager:
    def __init__(self):
        self._app_id: str = "agent-service"
        self._config_version: int = 0  # configVersion from remote config (for monitoring)
        self._app_version: int = 0  # app version from app.json (for config matching)
        self._remote_config_url: str = ""
        self._file_refreshers: Dict[str, List[Callable[[], None]]] = {}  # file path -> refreshers
        self._file_versions: Dict[str, int] = {}  # file path -> version
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
                    # App version for config matching
                    self._app_version = int(app_data.get("version", 0))
            else:
                self._app_version = 0
                self._remote_config_url = ""
        except Exception as e:
            logger.error(f"Failed to read app config: {e}")
            self._app_version = 0
            self._remote_config_url = ""
        
        # Load or create update.json for config version tracking and file versions
        try:
            if UPDATE_CONFIG_PATH.exists():
                with open(UPDATE_CONFIG_PATH, "r") as f:
                    update_data = json.load(f)
                    self._config_version = int(update_data.get("configVersion", 0))
                    self._file_versions = update_data.get("fileVersions", {})
            else:
                # No update.json means no sync has happened yet, default configVersion is 0
                self._config_version = 0
                self._file_versions = {}
                self._persist_update_config()
        except Exception as e:
            logger.error(f"Failed to read update config: {e}")
            self._config_version = 0
            self._file_versions = {}
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
            "appVersion": self._app_version,
            "configVersion": self._config_version,
            "remoteConfigUrl": self._remote_config_url,
            "lastUpdated": last_updated
        }


    def register_file_refresher(self, file_path: str, refresher: Callable[[], None]) -> None:
        """Register a refresher for a specific file"""
        if file_path not in self._file_refreshers:
            self._file_refreshers[file_path] = []
        if refresher not in self._file_refreshers[file_path]:
            self._file_refreshers[file_path].append(refresher)

    def _persist_update_config(self) -> None:
        """Persist config version and file versions to update.json"""
        try:
            UPDATE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(UPDATE_CONFIG_PATH, "w") as f:
                json.dump({
                    "configVersion": self._config_version,
                    "lastUpdated": datetime.now().isoformat(),
                    "fileVersions": self._file_versions
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist update config: {e}")
    
    def update_config_version(self, new_config_version: int) -> None:
        """Update the config version number and persist to update.json"""
        self._config_version = new_config_version
        self._persist_update_config()
        logger.info(f"Config version updated to {new_config_version}")
    
    async def sync_from_remote(self) -> bool:
        """Sync configuration from remote URL and update config version if newer version is available"""
        if not self._remote_config_url:
            logger.warning("Remote config URL not set, cannot sync")
            return False
        
        try:
            # Fetch remote configuration
            remote_config = await self._fetch_remote_json(self._remote_config_url)
            
            # Check if remote config version is newer
            remote_config_version = int(remote_config.get("configVersion", 0))
            if remote_config_version <= self._config_version:
                logger.info(f"Remote config version {remote_config_version} is not newer than current config version {self._config_version}")
                return True  # Not an error, just no update needed
            
            # Parse and download configuration files
            updated_files = await self._process_config_files(remote_config)
            
            # Update to new config version
            self.update_config_version(remote_config_version)
            
            # Refresh file-specific configurations for updated files
            self._refresh_file_configs(updated_files)
            
            logger.info(f"Successfully synced from remote, updated to config version {remote_config_version}")
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

    async def _process_config_files(self, remote_config: Dict[str, Any]) -> List[str]:
        """Process configuration files from remote config and download updated files"""
        updated_files = []
        
        app_config = remote_config.get("appConfig", {})
        versions = app_config.get("versions", {})
        
        # Get files from "all" version (always apply)
        all_files = versions.get("all", {}).get("files", [])
        
        # Get files from current app version (only apply if version matches current app version from app.json)
        app_version_files = versions.get(str(self._app_version), {}).get("files", [])
        
        # Combine all files that need to be processed
        all_config_files = all_files + app_version_files
        
        for file_config in all_config_files:
            app_path = file_config.get("appPath")
            s3_path = file_config.get("s3Path")
            file_version = int(file_config.get("version", 0))
            
            if not app_path or not s3_path:
                logger.warning(f"Invalid file config: {file_config}")
                continue
            
            # Check if file needs update
            current_file_version = self._file_versions.get(app_path, 0)
            if file_version <= current_file_version:
                logger.debug(f"File {app_path} version {file_version} is not newer than current {current_file_version}")
                continue
            
            try:
                # Download file from S3
                s3_url = self._resolve_remote_file_url(s3_path)
                local_path = Path(app_path)
                
                # Ensure directory exists
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Download file
                await downloader.download(s3_url, str(local_path), job_id=f"config-file-{app_path}")
                
                # Update file version
                self._file_versions[app_path] = file_version
                updated_files.append(app_path)
                
                logger.info(f"Downloaded config file {app_path} version {file_version} from {s3_url}")
                
            except Exception as e:
                logger.error(f"Failed to download config file {app_path}: {e}")
        
        # Persist file versions if any files were updated
        if updated_files:
            self._persist_update_config()
        
        return updated_files
    
    def _refresh_file_configs(self, updated_files: List[str]) -> None:
        """Refresh configurations for specific updated files"""
        for file_path in updated_files:
            if file_path in self._file_refreshers:
                for refresher in self._file_refreshers[file_path]:
                    try:
                        refresher()
                        logger.debug(f"Refreshed config for file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error in file refresher for {file_path}: {e}")

# Global instance
config_manager = ConfigManager()
