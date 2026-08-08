from __future__ import annotations

import math
import re
from collections.abc import Iterable


TIMESTAMP_PATTERN = re.compile(r"^(\d{2,}):(\d{2}):(\d{2}),(\d{3})$")
TIMELINE_PATTERN = re.compile(
    r"^(\d{2,}:\d{2}:\d{2},\d{3}) --> (\d{2,}:\d{2}:\d{2},\d{3})$"
)
PUNCTUATION = "，。！？；：、,.!?;:）】》〉」』”’"


def format_timestamp(seconds: float) -> str:
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError(f"invalid timestamp: {seconds!r}")
    total_ms = int(round(seconds * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def parse_timestamp(value: str) -> float:
    match = TIMESTAMP_PATTERN.fullmatch(value.strip())
    if not match:
        raise ValueError(f"invalid SRT timestamp: {value!r}")
    hours, minutes, seconds, milliseconds = map(int, match.groups())
    if minutes >= 60 or seconds >= 60:
        raise ValueError(f"invalid SRT timestamp: {value!r}")
    return round(hours * 3600 + minutes * 60 + seconds + milliseconds / 1000, 3)


def _splits_protected_term(text: str, position: int, protected_terms: Iterable[str]) -> bool:
    for term in protected_terms:
        if not term:
            continue
        start = text.find(term)
        while start >= 0:
            if start < position < start + len(term):
                return True
            start = text.find(term, start + 1)
    return False


def wrap_text(
    text: str,
    width: int = 18,
    protected_terms: Iterable[str] = (),
) -> str:
    if width <= 0:
        raise ValueError("subtitle line width must be positive")
    existing = [line.strip() for line in str(text).splitlines() if line.strip()]
    if not existing:
        raise ValueError("subtitle text is empty")
    if len(existing) <= 2 and all(len(line) <= width for line in existing):
        return "\n".join(existing)

    plain = "".join(existing)
    if len(plain) <= width:
        return plain
    if len(plain) > width * 2:
        raise ValueError(f"subtitle text exceeds two {width}-character lines: {plain}")

    minimum = max(1, len(plain) - width)
    maximum = min(width, len(plain) - 1)
    midpoint = len(plain) / 2
    punctuation_positions = [
        position
        for position in range(minimum, maximum + 1)
        if plain[position - 1] in PUNCTUATION
    ]
    all_positions = sorted(
        range(minimum, maximum + 1),
        key=lambda position: (
            position not in punctuation_positions,
            abs(position - midpoint),
            position,
        ),
    )
    split_at = next(
        (
            position
            for position in all_positions
            if not _splits_protected_term(plain, position, protected_terms)
        ),
        None,
    )
    if split_at is None:
        raise ValueError(f"unable to wrap subtitle without splitting a protected term: {plain}")

    first, second = plain[:split_at], plain[split_at:]
    if not first or not second or len(first) > width or len(second) > width:
        raise ValueError(f"unable to wrap subtitle safely: {plain}")
    return f"{first}\n{second}"


def render_srt(
    cues: Iterable[dict],
    *,
    width: int = 18,
    protected_terms: Iterable[str] = (),
) -> str:
    blocks: list[str] = []
    previous_end = 0.0
    for index, cue in enumerate(cues, start=1):
        start = float(cue["start"])
        end = float(cue["end"])
        if start < 0 or end <= start:
            raise ValueError(f"cue {index} has an invalid interval")
        if index > 1 and start < previous_end - 0.0005:
            raise ValueError(f"cue {index} overlaps the previous cue")
        wrapped = wrap_text(
            str(cue["text"]),
            width=width,
            protected_terms=protected_terms,
        )
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{format_timestamp(start)} --> {format_timestamp(end)}",
                    wrapped,
                ]
            )
        )
        previous_end = end
    if not blocks:
        raise ValueError("cannot render an empty subtitle file")
    return "\n\n".join(blocks) + "\n"


def parse_srt(content: str | bytes) -> list[dict]:
    if isinstance(content, bytes):
        if content.startswith(b"\xef\xbb\xbf"):
            raise ValueError("SRT must be UTF-8 without BOM")
        text = content.decode("utf-8")
    else:
        text = content
        if text.startswith("\ufeff"):
            raise ValueError("SRT must be UTF-8 without BOM")
    if not text.strip():
        raise ValueError("SRT is empty")

    blocks = re.split(r"\r?\n\r?\n", text.strip())
    cues: list[dict] = []
    for expected_index, block in enumerate(blocks, start=1):
        lines = block.splitlines()
        if len(lines) < 3:
            raise ValueError(f"SRT block {expected_index} is incomplete")
        try:
            actual_index = int(lines[0])
        except ValueError as error:
            raise ValueError(f"SRT block {expected_index} has an invalid index") from error
        if actual_index != expected_index:
            raise ValueError(f"SRT block {expected_index} has a nonsequential index")
        match = TIMELINE_PATTERN.fullmatch(lines[1])
        if not match:
            raise ValueError(f"SRT block {expected_index} has an invalid timeline")
        subtitle_lines = [line for line in lines[2:] if line.strip()]
        if not subtitle_lines:
            raise ValueError(f"SRT block {expected_index} has empty text")
        cues.append(
            {
                "index": expected_index,
                "start": parse_timestamp(match.group(1)),
                "end": parse_timestamp(match.group(2)),
                "lines": subtitle_lines,
                "text": "".join(subtitle_lines),
            }
        )
    return cues
