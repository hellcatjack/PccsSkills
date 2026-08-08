# Verification Contract

## Delivery state

The validator has three states:

- `PASS`: all deterministic checks pass, every risk has complete listening evidence, and immutable source hashes match.
- `REVIEW_REQUIRED`: no deterministic check fails, but one or more mandatory listening reviews are missing.
- `FAIL`: at least one deterministic, semantic-reference, media, or integrity check fails.

Only `PASS` is deliverable.

## Twelve mandatory checks

1. **SubRip encoding and syntax** — UTF-8 without BOM, LF line endings, sequential indices from 1, exact `HH:MM:SS,mmm --> HH:MM:SS,mmm` syntax, and nonempty text.
2. **Timeline legality** — every cue satisfies `0 <= start < end <= ffprobe video duration`; cues are monotonic and non-overlapping.
3. **Canonical equality** — parsed SRT text and millisecond timestamps exactly match `aligned_cues.json`.
4. **Readability** — at most two lines, 18 characters per line, 32 joined characters per cue, 0.1–8.0 seconds duration, and no more than 12 visible characters per second.
5. **Observed boundary evidence** — every automatic start/end is within 0.0011 seconds of a recorded ASR word/character boundary. Manual boundaries need a complete listening review.
6. **Risk coverage** — every cue flagged for ratio below 0.65, shift over 1.0 second, scripture boundary, prayer boundary, first/last cue, or overlap adjustment appears in `boundary_reviews.json`.
7. **Scripture scope and wording** — cues grouped by exact `reference` reconstruct every `spoken: true` entry and contain no text for `spoken: false` entries.
8. **Current-sermon terminology and divine pronouns** — every `required_terms` item exists and every confirmed `forbidden_terms` ASR/accent error is absent. Divine singular references use `祢/祂`; `祢们/祂们`, malformed or stale exceptions, and mixed scripture-reference forms are hard failures. An unresolved ordinary `你/他` candidate near a divine title produces `REVIEW_REQUIRED` until semantic correction or an exact justified human-reference exception closes it. These lists and exceptions come from this sermon.
9. **Revision comparison** — when an earlier SRT exists, the report gives cue/text counts, text hashes, changed starts/ends, median/P95/min/max shifts, and all shifts over one second. An agent reviews the abnormal values.
10. **Representative and risk listening** — opening, scripture, each sermon point, major illustration, summary, prayer, final cue, and all risk cues have been checked against the original video.
11. **Immutable source integrity** — rehash every manifest input, including video and PPTX; all SHA-256 values must match the baseline. Existing formal subtitles included in the baseline must also remain unchanged.
12. **Fresh final report** — `validation_report.json` belongs to the delivered SRT, reports zero hard failures and zero missing reviews, and has status `PASS`.

## Important distinctions

- Passing checks 1–4 does not prove accurate synchronization.
- A 100% lexical match does not prove that the candidate came from the correct semantic window.
- Extending cue duration for readability cannot replace observed speech boundaries.
- Source-segment timestamps are provisional; final starts/ends use word/character evidence or documented listening evidence.
- A local ASR model can omit audible speech under VAD. Dual full passes and regional no-VAD review are required.
- Divine-pronoun candidate detection is an audit aid, not an automatic replacement engine. The agent decides the antecedent from complete context and must preserve ordinary pronouns for human referents.

## Manual evidence completeness

Each review needs:

- stable `cue_id`;
- a precise semantic reason;
- evidence naming the original video/ASR/PPT observation;
- `listened_window` as absolute `[start,end]` seconds;
- decision and, when applicable, new `start`, `end`, or `text`.

Incomplete records are hard failures. A complete record closes all listed risks for the same cue only when its evidence addresses them; the agent must split records when different risks require different listening windows.

## Final handoff fields

Report:

- absolute SRT path and corresponding video path;
- language `zh-Hans` and SubRip format;
- cue count, first start, last end, and video duration;
- whether primary, precision, and regional ASR were used;
- total alignment groups, low-ratio groups, shifts over one second, overlap repairs, and completed reviews;
- total divine-pronoun candidates, unresolved candidates, invalid plural honorifics, and audited human-reference exceptions;
- validator state and 12-check summary;
- final SRT SHA-256.
