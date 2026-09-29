from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("sprawl-cli")
except PackageNotFoundError:
    __version__ = "2.0.3"  # Synchronized fallback

__all__ = ["__version__"]
