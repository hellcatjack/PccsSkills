"""Exact verse-prefix preservation shared by worship input and slide-plan checks."""


def validate_verse_metadata(record, label):
    errors = []
    if not {"raw_source_lines", "verse_prefixes", "verse_numbers"}.intersection(record):
        return errors
    lines = record.get("source_lines", record.get("lines", []))
    raw = record.get("raw_source_lines")
    if not isinstance(raw, list) or len(raw) != len(lines) or any(not isinstance(x, str) for x in raw):
        return [f"{label}.raw_source_lines must preserve one raw entry per source line."]
    prefixes, numbers = record.get("verse_prefixes"), record.get("verse_numbers")
    if prefixes is None and numbers is None:
        if raw != lines:
            errors.append(f"{label}: raw_source_lines cannot be reconstructed without verse metadata.")
        return errors
    for field, value in (("verse_prefixes", prefixes), ("verse_numbers", numbers)):
        if not isinstance(value, list) or len(value) != len(lines) or any(not isinstance(x, str) for x in value):
            errors.append(f"{label}.{field} must have one string per source line.")
    if errors:
        return errors
    if any(not isinstance(line, str) for line in lines) or [a + b for a, b in zip(prefixes, lines)] != raw:
        errors.append(f"{label}: verse_prefixes + source_lines must reconstruct raw_source_lines exactly.")
    if record.get("verse_boundaries_verified") is not True:
        errors.append(f"{label}.verse_boundaries_verified must be true.")
    for field in ("translation", "verse_metadata_audit"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f"{label}.{field} must record the source edition and numbering decision.")
    return errors
