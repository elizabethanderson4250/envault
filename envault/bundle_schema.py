"""Schema validation helpers for envault bundle files."""

from __future__ import annotations

from typing import Any, Dict, List


class BundleValidationError(ValueError):
    """Raised when a bundle dict fails schema validation."""


# Required top-level keys and their expected types.
_REQUIRED: List[tuple] = [
    ("version", int),
    ("recipients", list),
    ("ciphertext", str),
]

SUPPORTED_VERSIONS = frozenset({1})


def validate_bundle(data: Dict[str, Any]) -> None:
    """Raise ``BundleValidationError`` if *data* is not a valid bundle dict.

    Checks:
    - All required keys are present with correct types.
    - ``version`` is a supported value.
    - ``recipients`` contains only strings.
    - ``ciphertext`` is non-empty.
    """
    if not isinstance(data, dict):
        raise BundleValidationError("Bundle must be a JSON object.")

    for key, expected_type in _REQUIRED:
        if key not in data:
            raise BundleValidationError(f"Missing required field: '{key}'.")
        if not isinstance(data[key], expected_type):
            raise BundleValidationError(
                f"Field '{key}' must be of type {expected_type.__name__}."
            )

    if data["version"] not in SUPPORTED_VERSIONS:
        raise BundleValidationError(
            f"Unsupported bundle version {data['version']!r}. "
            f"Supported: {sorted(SUPPORTED_VERSIONS)}."
        )

    for i, item in enumerate(data["recipients"]):
        if not isinstance(item, str):
            raise BundleValidationError(
                f"recipients[{i}] must be a string, got {type(item).__name__}."
            )

    if not data["ciphertext"].strip():
        raise BundleValidationError("Field 'ciphertext' must not be empty.")


def is_valid_bundle(data: Dict[str, Any]) -> bool:
    """Return True if *data* passes schema validation, False otherwise."""
    try:
        validate_bundle(data)
        return True
    except BundleValidationError:
        return False
