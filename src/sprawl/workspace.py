import json
import os
import datetime
from typing import Optional, Dict, Any

from .config import config
from .exceptions import SprawlError

class WorkspaceError(SprawlError):
    """Base exception for workspace-related errors."""
    pass


class Workspace:
    """Represents a Sprawl workspace and its associated metadata."""

    def __init__(self, path: str) -> None:
        self.path = os.path.abspath(os.path.expanduser(path))
        self.mgt_dir = config.get_workspace_mgt_dir(self.path)
        self.dna_binding_path = os.path.join(self.mgt_dir, "dna_binding.json")
        self.sync_state_path = os.path.join(self.mgt_dir, "sync_state.json")
        self.manifest_path = os.path.join(self.path, ".agents", "sprawl_manifest.yml")

    def ensure_mgt_dir(self) -> None:
        """Ensures the management directory exists."""
        os.makedirs(self.mgt_dir, exist_ok=True)

    def get_dna_alias(self) -> Optional[str]:
        """Returns the bound DNA alias for this workspace."""
        # 1. Check management plane (New way)
        if os.path.exists(self.dna_binding_path):
            try:
                with open(self.dna_binding_path, "r") as f:
                    data = json.load(f)
                    return data.get("alias")
            except (json.JSONDecodeError, IOError):
                pass

        # 2. Check workspace root (Old way - Migration)
        old_dna_path = os.path.join(self.path, ".sprawl_dna")
        if os.path.exists(old_dna_path):
            try:
                with open(old_dna_path, "r") as f:
                    alias = f.read().strip()
                if alias:
                    self.bind_dna(alias)
                    # We don't delete the old file yet, just migrate the data
                    return alias
            except IOError:
                pass
        
        return None

    def bind_dna(self, alias: str) -> None:
        """Binds this workspace to a DNA alias in the management plane."""
        self.ensure_mgt_dir()
        with open(self.dna_binding_path, "w") as f:
            json.dump({"alias": alias, "bound_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}, f, indent=4)

    def get_sync_state(self) -> Dict[str, Any]:
        """Returns the sync state for this workspace."""
        if not os.path.exists(self.sync_state_path):
            return {}
        try:
            with open(self.sync_state_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def update_sync_state(self, state: Dict[str, Any]) -> None:
        """Updates the sync state in the management plane."""
        self.ensure_mgt_dir()
        current_state = self.get_sync_state()
        current_state.update(state)
        current_state["last_sync_timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with open(self.sync_state_path, "w") as f:
            json.dump(current_state, f, indent=4)


class WorkspaceRegistry:
    """Manages the tracked workspaces in ~/.sprawl/workspaces.json."""
    
    @classmethod
    def load(cls) -> Dict[str, Any]:
        """Loads the registry from disk."""
        path = config.workspace_registry_path
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    @classmethod
    def save(cls, data: Dict[str, Any]) -> None:
        """Saves the registry to disk."""
        path = config.workspace_registry_path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    @classmethod
    def register(cls, name: str, path: str, dna_source: Optional[str] = None) -> None:
        """Registers a new workspace or updates an existing one's tracking info."""
        data = cls.load()
        
        # Ensure path is absolute
        abs_path = os.path.abspath(os.path.expanduser(path))
        
        if name not in data:
            data[name] = {
                "path": abs_path,
                "dna_source": dna_source,
                "last_sync_timestamp": None
            }
        else:
            data[name]["path"] = abs_path
            data[name]["dna_source"] = dna_source
        
        cls.save(data)

    @classmethod
    def deregister(cls, name: str) -> None:
        """Removes a workspace from the registry."""
        data = cls.load()
        if name in data:
            del data[name]
            cls.save(data)
        else:
            raise WorkspaceError(f"Workspace '{name}' is not registered.")

    @classmethod
    def get(cls, name: str) -> Optional[Dict[str, Any]]:
        """Gets a workspace's tracking info."""
        data = cls.load()
        return data.get(name)

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """Returns all registered workspaces."""
        return cls.load()

    @classmethod
    def update_sync_timestamp(cls, name: str) -> None:
        """Updates the last sync timestamp for a given workspace by name or path."""
        data = cls.load()
        if name not in data:
            # Fallback: search by path
            found_name = None
            for ws_name, ws_data in data.items():
                if ws_data.get("path") == name:
                    found_name = ws_name
                    break
            if not found_name:
                raise WorkspaceError(f"Workspace '{name}' is not registered.")
            name = found_name
        
        data[name]["last_sync_timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cls.save(data)
