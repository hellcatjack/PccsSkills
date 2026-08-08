from __future__ import annotations

import hashlib
from pathlib import Path
import re
from typing import Any, Iterable, Mapping


class PolicyError(RuntimeError):
    """Raised before an operation can violate source or timeline safety."""


FORBIDDEN_OPTIONS = frozenset({"-ss", "-to", "-t", "-shortest"})
FORBIDDEN_FILTERS = frozenset(
    {
        "atrim",
        "silenceremove",
        "atempo",
        "concat",
        "asegment",
        "aselect",
        "afade",
        "acrossfade",
    }
)
CUTTER_FIELDS = (
    "silence_cutter",
    "filler_cutter",
    "cough_cutter",
    "music_cutter",
)
FILTER_OPTIONS = frozenset({"-af", "-filter:a", "-filter_complex"})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_filter_option(token: str) -> bool:
    return token in FILTER_OPTIONS or token.startswith("-filter:a:")


def _filter_names(expression: str) -> set[str]:
    names: set[str] = set()
    for candidate in FORBIDDEN_FILTERS:
        pattern = rf"(?<![A-Za-z0-9_]){re.escape(candidate)}\s*(?==|,|;|\[|$)"
        if re.search(pattern, expression, flags=re.IGNORECASE):
            names.add(candidate)
    return names


def assert_safe_command(args: Iterable[str]) -> None:
    tokens = [str(arg) for arg in args]
    for index, token in enumerate(tokens):
        lowered = token.lower()
        if lowered in FORBIDDEN_OPTIONS:
            raise PolicyError(f"Forbidden timeline option: {token}")
        if _is_filter_option(lowered) and index + 1 < len(tokens):
            forbidden = _filter_names(tokens[index + 1])
            if forbidden:
                names = ", ".join(sorted(forbidden))
                raise PolicyError(f"Forbidden timeline filter: {names}")


def _normalized_path(path: Path) -> str:
    return str(path.resolve()).casefold()


def assert_safe_output(
    source: Path,
    output: Path,
    *,
    protected_paths: Iterable[Path] = (),
    allow_existing: bool = False,
) -> None:
    output_key = _normalized_path(output)
    protected = {_normalized_path(source)}
    protected.update(_normalized_path(path) for path in protected_paths)
    if output_key in protected:
        raise PolicyError("Output path would overwrite protected source media")
    if output.exists() and not allow_existing:
        raise PolicyError(f"Output already exists: {output}")


def assert_source_unchanged(source: Path, baseline_sha256: str) -> None:
    current = sha256_file(source)
    if current.casefold() != baseline_sha256.casefold():
        raise PolicyError(
            f"Source hash changed: expected {baseline_sha256}, found {current}"
        )


def assert_cloud_free_allowed(
    *,
    duration_hours: float,
    recurring_credits: float,
    recurring_cap: float,
    documented_free_cap: float = 2.0,
) -> None:
    if duration_hours <= 0:
        raise PolicyError("Cloud duration must be positive")
    if recurring_cap <= 0 or recurring_cap > documented_free_cap + 1e-9:
        raise PolicyError("Account is not proven to be on the free recurring tier")
    if recurring_credits + 1e-9 < duration_hours:
        raise PolicyError("Free recurring credits are insufficient")


def validate_auphonic_algorithms(algorithms: Mapping[str, Any]) -> None:
    missing = [name for name in CUTTER_FIELDS if name not in algorithms]
    if missing:
        raise PolicyError(f"Auphonic cutter fields must be explicit: {', '.join(missing)}")
    enabled = [name for name in CUTTER_FIELDS if algorithms.get(name) is not False]
    if enabled:
        raise PolicyError(f"Auphonic cutters must remain disabled: {', '.join(enabled)}")
