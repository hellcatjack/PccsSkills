# Optional publication assets

Use this reference when the user requests titles, descriptions or thumbnails. Publication is separate from creating local assets; do not upload or send them without authorization.

## Metadata grounded in the current sermon

Read the title and passage from the current PPT cover and cross-check with the spoken opening and complete transcript. Speaker identity must come from the user or reliable current project evidence. Use the user's explicit album/series name over an older series prefix. Never inherit last week's speaker, date, passage or title from an example.

Suggested title structure when a series is specified: `{series}：{sermon title} {book} {passage} by {speaker}牧师`. Preserve the requested writing system and meaning; offer a shorter form only if a platform limit requires it.

The description begins with title, passage and speaker, then the actual main points and application. Follow applicable PCCS project instructions for the fixed church identity, founding date, mission, all four visions and invitation. Do not invent times, addresses, links, affiliations or unspoken theological conclusions. If no project policy supplies these facts, retrieve a reliable current policy before adding them. Provide separately copyable title and description blocks.

## One wide thumbnail that survives a cropped card

Use the image-generation skill and available image tool for image creation/editing. Inspect reference images first. Treat screenshots as layout evidence, not a source of this week's sermon metadata.

Obtain or inspect the website card's actual width/height, `object-fit`, `object-position` and play-button position. For centered `cover`, scale by `max(cardWidth/imageWidth, cardHeight/imageHeight)`. The surviving source width is `cardWidth/scale`, centered horizontally; use the analogous calculation for height. A 174×220 card retains about the middle 44.5% of a 16:9 image, so ordinary wide left/right headlines can disappear.

For that narrow-card pattern, a useful starting layout is two short title lines in the upper center, supporting text in the lower center, all crucial text within roughly x34–66%. Keep the central y36–68% clear for the play overlay. These are **example safe zones**, not a universal website crop rule. Test the actual font bounds, longest title, player-button size and responsive card dimensions; avoid unreadably small metadata.

Create the full 16:9 design with generous side scenery and meaningful center content. Render both a YouTube landscape preview and the real card crop with its center play button. Inspect complete title, scripture and speaker text and keep a screenshot as evidence. Do not bake the website's play icon into the source thumbnail.

Inspect the generated file's actual pixel dimensions, aspect ratio and byte size; the requested dimensions in a prompt are not output evidence. If an image tool returns a smaller raster, report its native resolution and create a separately identified exact-size export through the permitted image workflow when required. Do not call an upscaled image native 4K. Export PNG and, if useful, a high-quality JPEG; verify the final deliverable again after conversion.
