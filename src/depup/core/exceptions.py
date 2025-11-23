"""
Custom exception hierarchy for depup.
"""


class DepupError(Exception):
    """Base class for all depup-specific exceptions."""


class InvalidDependencyFileError(DepupError):
    """Raised when an unsupported or malformed dependency file is encountered."""
