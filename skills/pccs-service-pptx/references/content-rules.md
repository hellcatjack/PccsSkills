# Content Rules

## Exact Text

- Preserve user-supplied titles, announcements, dates, names, email addresses, phone numbers, account information, prices, and punctuation.
- Do not shorten dense copy unless the user explicitly approves edited wording.
- Improve fit through layout, spacing, pagination, or explicit font selection, not silent rewriting.
- Do not apply lyric-specific simplified-Chinese or divine-pronoun substitutions to quoted scripture.

## Scripture

- Treat `source_lines` as canonical characters and canonical order.
- Do not add a missing bracket, verse marker, punctuation mark, honorific, or translation correction unless the user asks.
- When the user corrects a quotation, retain the raw extracted line, record the exact authorized change, and update the accepted source used by the PPTX and any companion text files together.
- Do not remove whitespace or punctuation that belongs to the quoted text, including full-width spaces (`U+3000`).
- Keep each fixed `source_lines` entry as one PowerPoint paragraph.
- When the user supplies one continuous paragraph without fixed line breaks, visual wrapping may occur, but character order must remain exact.
- If `single_slide: true`, fit all text on one slide by changing scripture-specific geometry and font size; never alter the text.
- Verify the translation/edition and verse boundaries against the user-supplied or authoritative source before treating numbers as verse metadata. A familiar-sounding passage is not evidence for silently correcting it.
- To display verse numbers in a separate left column, retain the original `raw_source_lines`, exact removed `verse_prefixes`, separate `verse_numbers`, translation, and `verse_metadata_audit`. For every line, `verse_prefixes[i] + source_lines[i]` must exactly equal `raw_source_lines[i]`; keep body punctuation, spacing, characters, and line order unchanged. A supplied passage with no printed verse number can have an empty prefix and a verified metadata number; record how the boundary was established.
- Do not add honorifics or apply lyric `祢/祂` substitution to scripture. Preserve the supplied edition's wording even when lyric pages use a different policy.
- Preserve fixed lines; paginate at complete lines or verse boundaries where they coincide. For continuous input without fixed lines, wrapping is visual only and must preserve the character sequence. Prefer pagination to font reduction; the formal reading profile is `SimSun`, left-aligned, no shadow, one uniform size per passage (`36pt` ceiling for legacy-refined; wide-v3 begins from the38pt sample and records explicit fit exceptions).
- When the user requests all verses on one slide, use a consistent row grid without blank rows and choose one readable font size for the passage. Keep the final row above any subtitle overlay. With a separate verse-number gutter, align the visible digits to the corresponding Chinese text after rendering; matching text-box `Top` coordinates alone can look misaligned, and duplicated marker shapes may shift horizontally unless `Left` is reset.

## QR Codes And Forms

- Copy the uploaded QR code or form image directly.
- Preserve aspect ratio and quiet-zone margins around a QR code.
- Do not sharpen, redraw, recreate, or place decorative material over a QR code.
- Test the QR code from the rendered slide when practical.

## Photos

- Use authentic uploaded photographs.
- Preserve people and event identity; do not replace them with generated substitutes.
- Crop only to improve composition without removing essential people or context.
- Keep photos above the PCCS protruding logo-tip area.

## Cover And Announcement Copy

- Cover pages may use restrained graphical framing but must keep the church name and service identity prominent.
- Announcements should remain readable from a sanctuary screen. Use concise hierarchy, high contrast, and the upper content area.
- Do not expose production instructions, layout notes, keyboard shortcuts, or internal labels on the slide.

## Mixed Decks

If non-lyric pages are inserted into a worship lyric deck:

1. Keep lyric layouts owned by `pccs-worship-pptx`.
2. Keep service layouts owned by this skill.
3. Preserve both layout families and unique `MatchingName` values when combining.
4. Re-run duplication QA for every distinct layout after combination.
5. Use a `BackgroundNamePattern` that identifies both layout families when running the service QA script on the combined deck, or run structural QA on each family plus a manual combined-deck duplication check. Do not rename or flatten artwork merely to satisfy a default script name pattern.
6. Keep service input `index` values locally consecutive and use `final_slide_index` to point at the actual combined-deck pages. `-ProjectJson` consumes only these declared non-lyric pages; it does not require fabricated lyric records to fill the gaps.
