"""Configuration management commands."""

from ..config import config
from ..output import print_status, print_error


def cmd_config_set(key: str, value: str) -> None:
    """Sets a configuration value.

    Args:
        key: Configuration key (e.g., 'vault_path').
        value: Configuration value.
    """
    config.update({key: value})
    config._load_dynamic_config()  # Reload dynamic values without resetting paths
    print_status(f"Configuration updated: {key} = {value}")


def cmd_config_get(key: str) -> None:
    """Gets a configuration value.

    Args:
        key: Configuration key.
    """
    data = config.load()
    if key in data:
        print_status(f"{key} = {data[key]}")
    else:
        print_error(f"Configuration key '{key}' not found.")


def cmd_config_list() -> None:
    """Lists all configuration values."""
    data = config.load()
    if not data:
        print_status("Configuration is empty.")
        return
    
    from rich.table import Table
    from ..output import console
    
    table = Table(title="Global Configuration")
    table.add_column("Key", style="accent")
    table.add_column("Value", style="info")
    
    for k, v in sorted(data.items()):
        table.add_row(k, str(v))
        
    console.print(table)
