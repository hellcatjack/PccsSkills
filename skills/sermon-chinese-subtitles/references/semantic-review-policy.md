# Semantic Review Policy

## Full-sermon reading is mandatory

Read both complete ASR transcripts and the available PPT from beginning to end. Identify the opening, scripture reading, prayers, sermon transitions, major points, illustrations, summary, invitation, and closing prayer. A search hit, ASR confidence score, or isolated excerpt cannot establish the final wording by itself.

## Evidence priority

Use evidence in this order while respecting what is audible:

1. The original video's selected audio track and its absolute timeline.
2. PPT wording for a passage the pastor is directly reading or explicitly quoting.
3. Agreement between primary and precision full ASR.
4. Regional no-VAD ASR for omissions, conflicts, and uncertain boundaries.
5. Current-sermon context: title, sermon points, Bible people/places, historical names, church terms, and nearby argument.
6. A documented best-faith transcription with low confidence when the audio itself is genuinely unclear.

PPT wording never authorizes inserting speech that is not audible.

## Direct scripture versus sermon speech

Classify each biblical use before correction:

- **Direct reading:** Correct recognizable accent/ASR substitutions to the exact PPT/Bible wording for the words actually spoken. Record an exact `reference` on each cue.
- **Explicit quotation:** Use canonical wording only for the quoted portion that is clearly intended as a quotation.
- **Paraphrase or exposition:** Preserve the pastor's explanation. Correct names and obvious recognition errors, but do not rewrite the sentence into a Bible translation.
- **Pastor omission:** Do not add the omitted word, clause, or verse merely to make the reference complete.
- **Pastor self-correction:** Preserve the final intended wording when the correction is audible; keep meaningful repetition when it affects delivery.
- **Possible spoken mistake:** Do not silently change theology or facts. If it is not an accent/recognition issue, transcribe faithfully and document the ambiguity.

If the PPT gives a passage range longer than the actual reading, `scripture_reference.json` must mark the unread entries `spoken: false`. If the PPT wording has no labeled translation, record its source as “PPT wording; version not labeled” instead of guessing a version.

## Hong Kong-accented Mandarin and proper names

Mandarin spoken with a Hong Kong/Cantonese accent can merge initials, finals, and tones that ASR relies on. Correct only after considering sentence meaning and current-sermon terms.

- Build the proper-name list from this PPT and sermon, not from a previous correction script.
- Prefer time-scoped corrections attached to source segments or review notes.
- Require regional ASR or listening when two valid words remain plausible.
- Correct established Bible names, places, book names, historical figures, and church abbreviations when context makes the intended term clear.
- Do not apply a global replacement to a common syllable that may be correct elsewhere.
- Record material changes as raw wording, corrected wording, absolute interval, evidence, and reason.

## Regional ASR selection

Create an absolute review window when any of these occurs:

- A primary VAD gap overlaps audible speech.
- Primary and precision passes disagree materially.
- Consecutive word probability is low or the text is nonsensical in context.
- A scripture verse, person, place, historical example, or church name is dense with ASR errors.
- A cue boundary lands inside a clearly audible word or more than one second away from the likely phrase.
- Prayer start/end, opening, final “amen,” or a long pause is unstable.

Use enough surrounding speech to preserve context. The regional result is not automatically preferred; compare it with the same semantic window in both full passes.

## Divine honorific pronouns

Determine the antecedent from the complete sentence, nearby cues, sermon section, and original audio before choosing a display form:

1. Use `祢、祢的、祢所` when the pastor directly addresses God, the Lord, the Father, Yahweh, Jesus Christ, or the Holy Spirit.
2. Use `祂、祂的、祂所` when the same divine referent is discussed in the third person.
3. Preserve `你、他、你们、他们` when they refer to the pastor, listeners, biblical people, or other humans. Never create `祢们` or `祂们`.
4. Do not globally replace `你` or `他`. When a deterministic candidate is genuinely human, record its exact current `cue_id`, full cue `text`, and a concrete semantic `reason` in `context.json` under `deity_pronoun_exceptions`.
5. Use the same reviewed display form in `reviewed_cues.json`, the rendered SRT, and each spoken `scripture_reference.json` entry so scripture reconstruction remains exact.

Example: write `主啊，我们感谢祢` when prayer addresses God, but retain `主耶稣告诉你要彼此相爱` when `你` addresses the listener and document that human-reference exception.

## Cue authorship

- Segment by meaning, syntax, punctuation, and audible pause.
- Keep at most 32 display characters per cue and prefer one or two balanced lines.
- Do not move the next sentence earlier to improve reading time.
- Keep silence without subtitles.
- Preserve emphasis and meaningful repetition; remove hallucinated slogans, duplicated ASR fragments, and non-speech noise.
- Use Simplified Chinese consistently, with `祢/祂` as intentional divine-honorific display characters. Preserve intended Latin abbreviations and proper spellings.
- Every cue needs a stable id, reason, confidence, source, and alignment evidence.
- Cues split from one primary segment should share an `alignment_group` so their combined text aligns once instead of repeatedly matching the same source words.

## Mandatory listening review

Listen in the original video around every risk:

- ratio below 0.65;
- start or end shift over 1.0 second;
- overlap adjustment;
- first and last cue;
- first and last direct-scripture cue;
- prayer start/end;
- any unresolved person/place or doctrinally significant word.

Use a window that includes at least one phrase before and after when available. Record what the first and last audible words are, the observed boundary evidence, and the final decision. A generic note such as “manual fix” or “sounds right” is not evidence.
