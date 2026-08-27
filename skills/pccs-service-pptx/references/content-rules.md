# Content Rules

## Exact Text

- Preserve user-supplied titles, announcements, dates, names, email addresses, phone numbers, account information, prices, and punctuation.
- Do not shorten dense copy unless the user explicitly approves edited wording.
- Improve fit through layout, spacing, pagination, or explicit font selection, not silent rewriting.
- Do not apply lyric-specific simplified-Chinese or divine-pronoun substitutions to quoted scripture.

## Scripture

- Treat `source_lines` as canonical characters and canonical order.
- Do not add a missing bracket, verse marker, punctuation mark, honorific, or translation correction unless the user asks.
- Do not remove whitespace or punctuation that belongs to the quoted text.
- Keep each fixed `source_lines` entry as one PowerPoint paragraph.
- When the user supplies one continuous paragraph without fixed line breaks, visual wrapping may occur, but character order must remain exact.
- If `single_slide: true`, fit all text on one slide by changing scripture-specific geometry and font size; never alter the text.

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
