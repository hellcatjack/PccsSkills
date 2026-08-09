# Source Resolution

## Goal

Resolve the exact lyric text and one concrete reference performance for each song. A channel or playlist URL identifies a search space, not automatically the recording to use.

## Scripture From Service Guides

When the user explicitly includes scripture in a TXT or guide file, that file is the authoritative source for scripture wording and line sequence. Capture the passage as an ordered line array before layout work. Do not use web copies, OCR, ASR, or remembered Bible formatting to merge, split, reorder, paraphrase, or re-punctuate those lines.

If a global rule explicitly requires simplified Chinese or divine-pronoun normalization, apply it within each original line, record the character changes in the audit, and keep the original line count, order, and boundaries.

## With Lyric Images

1. Inspect every image directly with the model's visual ability; do not require OCR software as the first step.
2. Identify title, lyric text, section labels, repeat signs, first/second endings, and cross-line carry-over words.
3. Ignore chords, numbered notation, key, tempo, copyright lines, and non-lyric headers/footers.
4. Treat image lyrics as the baseline.
5. Use a matched YouTube recording, official lyrics, subtitles, audio, or ASR to detect missing or wrong characters.

Do not use visual coordinates alone to assign a word to C1 or C2. Resolve its ownership from complete phrase meaning, repeat structure, alternate endings, and corroborating sources.

## Without Lyric Images

Resolve sources in this order:

1. Direct video URL supplied for the named song.
2. Matching video inside a supplied playlist.
3. Matching upload inside a supplied channel.
4. Search using title, ministry/artist, album, language, key, and user hints.

Compare title, uploader/channel, ministry or songwriter, album, arrangement/version, duration, publish context, and playlist position. Prefer official ministry, artist, publisher, or church uploads over reposts when the performance matches.

## Confidence

- **High**: title/version and performer match; description, subtitles, frames, or audio also support the match.
- **Medium**: likely correct recording, but one metadata dimension is missing; proceed and document the limitation.
- **Low**: several plausible recordings or materially different lyric versions remain; stop and ask the user to choose.

Never infer that neighboring entries in a playlist correspond to user song order without checking each title.

## Evidence Extraction

Use the strongest available evidence in this order:

1. Official lyric text in the description or linked official page.
2. Human-authored subtitles/captions.
3. Clearly readable lyric frames in the video.
4. Direct audio listening and model transcription.
5. ASR output, preferably full-file transcription when supported.

YouTube access may fail or expose no captions. State exactly what was accessed. Do not claim to have heard audio or read subtitles unless the tool output proves it.

## ASR Use

ASR is corroborating evidence, not automatic truth. Keep timestamps when available. Flag homophones, worship vocabulary, names, short repeated phrases, and low-confidence regions. Compare ASR against musical phrase boundaries and known section repeats before accepting a correction.

The user's arrangement controls the final repeated order even when the reference video repeats sections differently. When no arrangement is provided, derive it from the verified performance and record the source and confidence.
