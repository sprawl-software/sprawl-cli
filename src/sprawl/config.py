"""Sprawl CLI Configuration — Injectable dataclass with environment-driven construction.

Replaces the old global singleton with a proper dataclass that supports
dependency injection for testing and environment-driven path resolution.
"""

import os
import json
import hashlib
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SprawlConfig:
    """Core configuration state for the Sprawl CLI engine.

    All filesystem paths are resolved deterministically based on the
    `test_mode` flag. Supports DI by instantiating with overrides.
    """

    dry_run: bool = False
    verbose: bool = False
    json_logging: bool = False
    test_mode: bool = field(default_factory=lambda: os.environ.get("SPRAWL_TEST_MODE") == "1")

    # Paths — resolved post-init based on test_mode
    agents_dir_global: str = field(default="", init=False)
    dna_registry_dir: str = field(default="", init=False)
    sprawl_dir: str = field(default="", init=False)
    config_path: str = field(default="", init=False)
    workspace_registry_path: str = field(default="", init=False)
    workspaces_dir: str = field(default="", init=False)
    vault_path: Optional[str] = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Resolve all filesystem paths based on current test_mode state."""
        self._resolve_paths()
        self._load_dynamic_config()

    def _resolve_paths(self) -> None:
        """Resolves and sets all filesystem paths based on the current test_mode flag."""
        if self.test_mode:
            base_dir = os.path.normpath(os.path.expanduser("~/.sprawl_test"))
            self.sprawl_dir = os.path.normpath(os.path.expanduser("~/Documents/Sprawl_Test"))
        else:
            base_dir = os.path.normpath(os.path.expanduser("~/.sprawl"))
            self.sprawl_dir = os.path.normpath(os.path.expanduser("~/Documents/Sprawl"))

        self.agents_dir_global = os.path.join(base_dir, "core")
        self.dna_registry_dir = os.path.join(base_dir, "dna")
        self.config_path = os.path.join(base_dir, "config.json")
        self.workspace_registry_path = os.path.join(base_dir, "workspaces.json")
        self.workspaces_dir = os.path.join(base_dir, "workspaces")

    def _load_dynamic_config(self) -> None:
        """Loads user-configured values from config.json."""
        data = self.load()
        self.vault_path = data.get("vault_path")

    def get_workspace_mgt_dir(self, workspace_path: str) -> str:
        """Returns the hidden management directory for a given workspace path."""
        abs_path = os.path.abspath(os.path.expanduser(workspace_path))
        path_hash = hashlib.sha256(abs_path.encode()).hexdigest()
        return os.path.join(self.workspaces_dir, path_hash)


    def reinitialize(self) -> None:
        """Re-evaluates environment state and resolves paths accordingly."""
        self.test_mode = os.environ.get("SPRAWL_TEST_MODE") == "1"
        self._resolve_paths()
        self._load_dynamic_config()

    def load(self) -> dict[str, Any]:
        """Loads and parses the .sprawl_rc deterministic routing definitions."""
        if not os.path.exists(self.config_path):
            return {}
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def update(self, updates: dict[str, Any]) -> None:
        """Binds global execution configs safely by updating the existing configuration."""
        config_data = self.load()
        config_data.update(updates)
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        tmp_path = self.config_path + ".tmp"
        try:
            with open(tmp_path, "w") as f:
                json.dump(config_data, f, indent=4)
            os.replace(tmp_path, self.config_path)
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise

    @classmethod
    def from_env(cls) -> "SprawlConfig":
        """Factory constructor — creates a config instance driven entirely by environment."""
        return cls(
            test_mode=os.environ.get("SPRAWL_TEST_MODE") == "1"
        )


def create_config(test_mode: bool = False) -> SprawlConfig:
    """Factory function for creating config instances with explicit test_mode override."""
    return SprawlConfig(test_mode=test_mode)


# Module-level default instance — maintains backward compatibility
# while allowing DI via create_config() or SprawlConfig() in tests
config = SprawlConfig()
