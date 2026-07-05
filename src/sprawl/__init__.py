from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("sprawl-cli")
except PackageNotFoundError:
    __version__ = "2.0.2"  # Synchronized fallback

__all__ = ["__version__"]
