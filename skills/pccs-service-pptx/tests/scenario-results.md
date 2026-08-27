# Scenario Results

## Baseline Failures Observed Without This Skill

- A full 16:9 generated background was placed at `0,-60,720,405`, so the footer cropped architectural subjects and weakened the composition.
- The transparent PCCS cross-tip halo was placed over lavender or detailed pixels, creating a visible color blob.
- Empty title, subtitle, and page-number placeholders remained available in Microsoft PowerPoint edit mode.
- Reused custom-layout identities could make duplicated slides inherit the wrong background.
- Scripture and announcement text risked being reflowed or normalized instead of preserved exactly.

## Required Corrective Behavior

- Compose backgrounds natively at `1920x920` and place them at `0,0,720,345`.
- Reserve and verify a feathered warm-ivory logo-tip zone.
- Use unique `Name` and `MatchingName` values for distinct layouts.
- Delete unused structural placeholders from final layouts and slides.
- Preserve user text and scripture `source_lines` exactly.
- Render every page and duplicate one page from every distinct layout before delivery.
