# Source Resolution

## Goal

Resolve the exact lyric text and one concrete reference performance for each song. A channel or playlist URL identifies a search space, not automatically the recording to use.

## Scripture From Service Guides

When the user explicitly includes scripture in a TXT or guide file, that file is the authoritative source for scripture wording and line sequence. Capture the passage as an ordered line array before layout work. Do not use web copies, OCR, ASR, or remembered Bible formatting to merge, split, reorder, paraphrase, or re-punctuate those lines.

Apply only scripture-specific authorized character corrections and record each change. Song normalization rules do not change scripture quotations. If standardizing verse labels, check boundaries against the selected Bible edition, keep the raw source, and record the corrected metadata separately.

## With Lyric Images

1. Inspect every image directly with the model's visual ability; do not require OCR software as the first step.
2. Identify title, lyric text, section labels, repeat signs, first/second endings, and cross-line carry-over words.
3. Exclude chords, numbered notation, key, tempo, and non-lyric headers/footers from lyric text. Capture author/copyright lines separately as `credit_lines`; never discard them with the notation.
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

## Official Lyrics and Attribution

When asked to collect lyrics, actively search the matching publisher/ministry's lyric page, downloadable score, official PPT, and recording description. Use the accessible official material for transcription and compare the exact song/version before accepting it. A failed playlist link does not prevent checking official sources for the named songs.

Retain songwriter, publisher, year, license identifier, and required attribution as source metadata. Record actual permission terms or license evidence when reproducing complete publisher materials; nonprofit worship use by itself is not a blanket permission record. Where the source grants the requested use, continue with the required attribution without asking again for already authorized work. If permission or access prevents complete reproduction, state the concrete limitation and continue the unaffected source audit and layout work.

## ASR Use

ASR is corroborating evidence, not automatic truth. Keep timestamps when available. Flag homophones, worship vocabulary, names, short repeated phrases, and low-confidence regions. Compare ASR against musical phrase boundaries and known section repeats before accepting a correction.

The user's arrangement controls the final repeated order even when the reference video repeats sections differently. When no arrangement is provided, derive it from the verified performance and record the source and confidence.
