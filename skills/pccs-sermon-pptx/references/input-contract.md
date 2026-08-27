# Input Contract

Normalize the weekly request before editing.

## Fields

| Field | Required | Rule |
|---|---:|---|
| `source_pptx` | yes | Exact user-named PPTX wins. Otherwise select the newest plausible source deck, preferring files without QA/output suffixes. |
| `sermon_video` | discover | Search the deck directory and workspace recursively for `.mp4`, `.mov`, `.m4v`, `.avi`, `.wmv`, and `.mkv`. Prefer the same directory, matching date, recent modification time, and substantial file size. |
| `output_pptx` | infer | Write a new file such as `_美化版_视频版.pptx` or `_统一排版.pptx`; never overwrite the source unless explicitly requested. |
| `style_basis` | cover | Use the current deck cover as the primary visual reference. The bundled images show the approved direction, not a replacement for the weekly cover. |
| `cover_redraw` | project default | If the exported cover is visibly soft at the target video size or its native pixels are insufficient, redraw it as a strict edit. Preserve the camera, people, wall/object layout, negative space, palette, and lighting; generate no text. |
| `font_family` | default | `STKaiti` for all visible text unless the user supplies another single family. |
| `scripture_gap` | project default | Add a small point-based gap before each verse after the first; start at `4pt`, with `1pt` after ordinary body paragraphs. |
| `constraints` | yes | Preserve slide count, wording, hard line breaks, pictures, animations, and transitions. The authorized low-resolution cover redraw is the only default picture change. |

## Discovery Command

```powershell
& '<skill-dir>/scripts/discover_sermon_inputs.ps1' -Root '<project-root>' -Deck '<optional-explicit-deck>'
```

The command returns ranked JSON. Treat the top result as a recommendation, not permission to edit a different file than the user named.

## Video Use

The video is contextual input. Confirm that it belongs to the same service and, when useful, sample a few frames to understand the speaker, room, projected content, and video-safe composition. Do not transcribe, trim, replace, or publish the video unless separately requested.

## Version Selection

When several PPTX versions exist:

1. Exact user-named file.
2. Same date/service folder.
3. Highest explicit version number.
4. Newest modification time.

Exclude generated QA copies and render artifacts. If the user asks to continue an already beautified file, that named beautified file becomes the source.
