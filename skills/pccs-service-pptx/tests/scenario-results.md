# 最终原生PowerPoint回归补充

已在独立新建QA副本上运行更新后的脚本：58页混合稿、5种布局，5条service记录通过final_slide_index映射到经文真实页。原生经文正文校验及5种布局复制、可见改字、保存、关闭、重开均通过。58页原稿重渲染像素与已检视的成品一致；5个副本只在标题改字区域出现像素差异，背景和底栏区域保持一致。源文件SHA256保持 `cd7ae99b212934efd7ca80ddc8176165955a503207a08051a7429c1d2f680e90`。未关闭或退出用户其他PowerPoint文件。

下面各阶段“未执行COM”的记录描述当时的独立脚本检查范围，已由此最终原生回归补充。

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

## Formal Scripture and Safe QA Revision

Read-only baseline scenario: prepare a mixed service deck from an existing PCCS footer template, two supplied songs and a Psalm reading; keep lyrics high, separate supporting metadata, and make the reading formal and easy to read aloud. The prior skill had no scripture alignment or size limit, inherited KaiTi from general typography, lacked a verse-number provenance contract, and could force scripture through worship's 48pt-oriented rules. The old PowerPoint QA called application `Quit()`, located layouts only in the first master, and treated appending a space as the edit test.

Confirmed reading behavior now uses left-aligned SimSun body, normally 36pt and capped at 36pt under that profile, a uniform size throughout the reading, YaHei title and separate verse numbers, no body shadow, and the documented upper reading grid. Fixed lines stay intact; continuous input may wrap visually. A single-slide requirement triggers safe geometry changes and a uniform smaller size only when the render remains readable. Verified metadata extraction keeps raw lines and reconstructable prefixes; it never rewrites the quotation. Particular Psalms, background subjects, and page counts are not defaults.

Validation performed:

- The original 13 service tests passed before editing.
- New behavior tests first exposed 12 failures: unconstrained scripture typography, mixed passage sizes, changed raw quotation text, missing verse audit, fixed-line wrapping, unmeasured background acceptance, application exit, and missing layout/path safety guards.
- Follow-up red cases exposed rejection of the existing `Scripture body` shape name and omission of background geometry from reopen snapshots; both were corrected.
- All **28 tests pass**, including executable PowerShell helper tests for master/layout identity, source/output protection, a visible character replacement, actual scripture body text/font/alignment checks, compatible body names, and detection of changed background geometry.
- Both PowerShell scripts parse successfully. The skill-creator quick validator passes with Python UTF-8 mode; `git diff --check` passes.
- Native Microsoft PowerPoint COM was **not run in this subtask**, to avoid conflicting with the coordinating task's PowerPoint session. Mock helper checks and syntax validation do not prove native COM or rendered legibility. Native duplicate/edit/save/reopen and visual results must be recorded by the coordinating task after its separate smoke test.

PowerPoint QA now opens only a newly created copy, refuses existing output paths, never quits the shared application, and closes only its own opened copy. Distinct used layouts are keyed by master/layout index, then checked for unique names; snapshots cover editable text, character typography, slide text geometry, and layout shape geometry. `-ProjectJson` is optional and checks actual scripture bodies, not title/verse/reference boxes or the authenticity of the chosen translation. Without it, the report explicitly says scripture body checks were not requested. Mixed decks can pass a background name pattern matching their existing layout assets.

## Forward-Test Follow-Up

Forward review found that requiring a service plan record for every final mixed-deck slide conflicted with the service-only input schema. A new bridge keeps `index` locally consecutive and adds optional `final_slide_index`; the QA maps only declared service pages, rejects duplicate/out-of-range positions, and verifies every declared page was consumed. Whole-deck structure, layouts and duplication remain covered. The new mapping tests first failed with seven assertions, then passed after implementation; the service suite now has **31 passing tests**.

Forward review also identified that the fifth 49pt line in the default upper grid approached `y=340pt` and could overlap the protruding logo-tip bounds. The documentation now prefers two or three rendered lines, limits the default grid to four, and directs longer readings to paginate before any explicitly required single-slide geometry exception. It explicitly distinguishes `y=345pt` as the footer edge from a safe text boundary.


## Wide-v3 integration

The current 960×540pt reference and foreground template are included with original layered PNGs, image prompts and SHA256 manifest. Purple subtitle mist is visible by default; the65% alternative remains hidden. New52pt lyric/40pt title tests coexist with the earlier refined-projection checks. Existing source, verse reconstruction, attribution and native QA safeguards are retained.

Publication verification: all 68 service tests and skill metadata validation passed. Native PowerPoint rendered the 64-slide reference and one-page foreground template. Copy/edit/save/reopen checks passed across five scene layouts and the foreground layout, including foreground visibility. Both declared scripture bodies passed native text, 38pt SimSun, left-alignment and no-shadow checks. Representative native renders were visually inspected.
