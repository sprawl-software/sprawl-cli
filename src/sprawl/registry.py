from datetime import datetime, timezone
from typing import Any

from .config import config
from .output import print_warning

def update_dna_registry(source_url: str) -> None:
    """Records the global DNA source into the Sprawl configuration."""
    now = datetime.now(timezone.utc).isoformat()
    config.update({
        "dna_source": {
            "url": source_url,
            "local_path": config.agents_dir_global,
            "last_pulled": now
        }
    })

def get_dna_registry() -> dict[str, Any] | None:
    """Returns the registered DNA source configuration."""
    data = config.load()
    return data.get("dna_source")

def check_dna_staleness() -> None:
    """Checks if the global DNA source hasn't been pulled in > 7 days."""
    registry = get_dna_registry()
    if not registry:
        return
    
    last_pulled_str = registry.get("last_pulled")
    if not last_pulled_str:
        return
        
    try:
        last_pulled = datetime.fromisoformat(last_pulled_str)
        delta = datetime.now(timezone.utc) - last_pulled
        if delta.days > 7:
            print_warning(f"DNA source is stale ({delta.days} days old). Run `sprawl dna update` to fetch latest changes.")
    except ValueError:
        # Ignore parse errors from manually modified config files
        pass
