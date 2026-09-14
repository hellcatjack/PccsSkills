# Composition policy

## Landscape capture and stable framing

Inspect actual metadata and frames near the beginning, middle, end, page transitions, wide gestures, leaning and prayer posture. A fixed camera still records a moving person. Preserve the head, useful hand area and recorded lectern detail needed for the composition. If the physical lectern base is outside the original recording, document that boundary; do not fabricate it or reject a sound crop for missing unrecorded pixels.

Choose one fixed crop; avoid tracking, digital pans and side changes. Remove irrelevant wall/aisle before reducing gesture space. Check headroom, eye line, body scale, microphone clearance and visual balance at native output size. Scale uniformly: crop and panel aspect ratios must match.

## Default starting preset: landscape inset A

For a 1920×1080 canvas and 16:9 slides:

| Element | x | y | width | height |
| --- | ---: | ---: | ---: | ---: |
| PPT viewport | 40 | 198 | 1216 | 684 |
| Pastor viewport | 1280 | 198 | 600 | 684 |

Use a restrained dark canvas, for example `#171B1F`. The panels share a baseline and a 24-pixel gap; the complete slide remains visible. Store these as `layout.pptRect` and `layout.pastorRect`. Derive `pastorCrop` from **this recording**, not a prior week. Check slide readability and adapt the preset when needed.

The bundled filter builds panels and focus transitions. Optional title/scripture graphics require a separately authored, verified overlay. Place them in the upper margin; fade the complete heading layer out before the expanding PPT reaches it. Do not leave half a heading clipped during a zoom. Check every consecutive transition frame. Legacy edge-to-edge 1560/360 plans remain supported, but are not the new capture default.

## Opening protection

- Record `intro.cameraForbiddenBefore` from the current user exclusion or inspected setup footage. It is **not a fixed 16-second rule** for future recordings.
- Record `coverSlide` and `coverUntil`; require `cameraForbiddenBefore <= coverUntil <= fullUntil < splitComplete`. `fullUntil` ends the initial full-screen PPT period; it may extend beyond the cover into reading.
- Audio starts at zero. Covering setup footage does not cut or delay either timeline.
- If cover is followed immediately by reading, continue into full-screen scripture and introduce the pastor at a useful semantic boundary. Avoid a one-second split-view flash.
- Use frame-aligned smooth ramps, usually 24 frames at 30 fps. Duration is configurable, not a page-timing algorithm.

## Normal, focus and repeated slides

Normal mode keeps both panels stable. Expand PPT to full-screen for complete reading, dense verse explanation, first presentation of a major point, important diagrams or synthesis. Each `fullScreenBlocks` interval includes ramp-in, stable hold and ramp-out, with its own semantic reason. Do not schedule focus on a timer.

Fade the fixed pastor panel as the PPT grows and restore the identical crop on return. Only fully opaque PPT intervals can be skipped during camera processing; transition frames still need the pastor.

Model every repeated page instance. After prayer, choose the page appropriate to the next spoken thought: cover, previously read passage or other content. Neither automatic replay nor a blanket ban on returning to the cover is appropriate. Verify every second pass background, master, font and image.

## Ending and previews

Choose the return-to-cover boundary from the last summary, appeal or closing prayer without interrupting an explanation. Default `left-cover-right-pastor` crossfades only the PPT viewport and preserves the pastor through the complete audio tail. A requested different ending needs an explicit plan and adapted verification; the bundled filter implements this default.

For a new layout, make an actual full-frame composition preview and short transition sample. If the user asks to choose, prepare concrete alternatives before asking. Otherwise proceed within existing authorization. Prior approval carries forward, while new footage still needs framing inspection. Do not re-ask about the same approved layout because encoding or denoising changed.
