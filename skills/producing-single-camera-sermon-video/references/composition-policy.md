# Composition policy

## Communication job

The congregation must be able to read the teaching material while still seeing the preacher's presence and gestures. Visual changes reinforce the sermon structure; they do not compete with it.

## Establish one stable pastor crop

1. Inspect one representative frame from the fixed-camera recording. Inspect additional frames only when the source itself changes framing, lighting, zoom, or obstruction.
2. Keep the full lectern and the pastor's useful hand-gesture area. Remove empty wall, unused aisle, and irrelevant left/right space first.
3. Choose a fixed crop for the entire program. Do not pan, track, or alternate sides to simulate another camera.
4. Place the pastor on the side supported by gesture direction and sightline. A source in which the pastor gestures toward the left usually belongs in the right panel.
5. Make the panel only as wide as needed for a balanced human figure and lectern. Give the remaining width to the PPT.

For a 1920×1080 canvas and a 16:9 deck, a proven starting geometry is a 1560-pixel PPT region and a 360-pixel pastor panel. Fit the full slide inside the PPT region without cropping; derive the vertical size and centering from the actual deck ratio. Store all dimensions and crop coordinates in the plan rather than embedding them in code.

## Opening

- Begin with the PPT cover full-screen for five seconds by default.
- Start audio at program time zero; the cover hold never delays audio.
- Transition to split view over roughly 0.65–0.8 seconds with smoothstep-like easing. Avoid hard cuts, black flashes, or a shrinking slide over an unprepared background.

## Normal and focus modes

Normal mode shows the full PPT at maximum size in the left region and the fixed crop of the pastor on the right. Use a subtle derived background only to fill unavoidable letterbox space.

Use full-screen PPT when the audience needs maximum reading or visual concentration, such as:

- a complete scripture reading;
- the first clear statement of a major point;
- a dense verse or list being explained line by line;
- a map, diagram, or image central to the current argument;
- a short synthesis where the slide itself carries the message.

Return to split view when the preacher moves into explanation, illustration, application, interaction, or prayer. Medium frequency means a few meaningful focus blocks across the sermon, not a fixed interval. Each block requires a transcript/PPT reason and enough time for both transition ramps plus a stable hold.

Keep the pastor location unchanged while the PPT grows over the pastor panel. Fade or mask the pastor as the slide reaches full width, then restore the same crop when focus ends.

## Repeated slides

If reading and preaching use the deck twice, model both runs explicitly. The first pass may cover sequential scripture reading; after prayer, the second pass starts at the correct page rather than replaying the cover. Render or retime each repeated page instance so its master, background, font, and images remain intact. Treat a white or missing second pass background as a failed output.

## Ending

Choose the return boundary from the last summary, appeal, or transition into closing prayer. Do not interrupt an unfinished explanation.

Use `left-cover-right-pastor`: crossfade only the PPT region to the cover while the right-side pastor continues uninterrupted. Hold that composition through the final prayer, final word, room tail, and the end of the immutable input-video audio.

## Preview policy

Create one composition preview before the full encode when the crop or layout is new. Show the full 1920×1080 frame with the actual PPT and representative pastor frame. A previously approved identical source/crop/layout may be reused; do not request redundant previews for a genuinely fixed camera.
