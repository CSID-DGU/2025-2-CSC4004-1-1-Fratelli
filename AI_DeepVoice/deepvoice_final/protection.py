"""Simple wrapper module that exposes HighQualityVoiceProtection.

This file used to contain partial/placeholder implementations which caused
syntax errors when imported by `api_server.py`. Import the fully
implemented class from `final_ver4.py` instead.
"""

try:
    from final_ver4 import HighQualityVoiceProtection
except Exception:
    # Fall back to relative import if running as a package
    from .final_ver4 import HighQualityVoiceProtection  # type: ignore

__all__ = ["HighQualityVoiceProtection"]