# Scenario Results

No subagents were used because the workflow owner explicitly prohibited them. The RED baseline comes from the real pre-skill sermon deck and the first deterministic validation run.

## Baseline Failures Observed

- The source video deck mixed `STKaiti` titles with `Microsoft JhengHei` body text.
- Most text frames used middle vertical anchoring, so title position changed with content height.
- Consecutive scripture pages used different title sizes, body sizes, text-box positions, widths, heights, and blank-paragraph sizes.
- Paragraph spacing was not standardized.
- Dense slides required measured capacity handling rather than global shrinking.
- Whole-range PowerPoint `BoundWidth` included wrapping artifacts; reliable overflow checks had to measure visible text line by line.
- The workflow had to preserve all 30 slides, exact text/hard line breaks, shape IDs/types, pictures, animations, and transitions.
- A low-detail cover remained visible after `Shape.Fill.UserPicture()` because the visible picture shape still referenced its original `p:pic/a:blip` media; the new image became an unused package part.
- Setting `SpaceBefore = 4` while `LineRuleBefore = -1` produced four lines of space and severe overflow instead of a subtle four-point verse gap.
- PowerPoint `Shapes.Item(number)` treats the number as a collection index, not a shape ID; shape lookup must compare each shape's `Id`.

## Required Corrective Behavior

- Discover the exact deck and likely sermon video before editing.
- Inventory the source and create page-family layout rules.
- Use one font family, fixed title baselines, top anchoring, consistent paragraph spacing, subtle black text shadow, and cover-matched sacred illustration styling.
- Adjust body size or spacing only after a rendered page proves the standard rule does not fit.
- Redraw visibly soft covers as strict image edits and replace only the unique embedded media payload, preserving the picture relationship and shape ID.
- Apply scripture gaps in points: `4pt` before later verse starts, `0pt` before continuations, `1pt` after ordinary body, and `0pt` after body only for verified dense pages.
- Compare source and candidate structurally, then render and inspect every slide before delivery.
