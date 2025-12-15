"""
Adapters for bridging legacy and new architecture.
"""

from .flask_adapter import FlaskToFastAPIAdapter

__all__ = ['FlaskToFastAPIAdapter']
