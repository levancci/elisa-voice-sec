"""Application package."""

from .registry import ModelEntry, ModelRegistry, resolve_model

__all__ = ["ModelEntry", "ModelRegistry", "resolve_model"]
