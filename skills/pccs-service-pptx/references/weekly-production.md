# 主日崇拜整套 PPTX

[720×405 pt 原生周次模板](../assets/pccs-weekly-720.pptx) 来自 2026-11-22 v5 的已验证版式。它提供使命与异象开场、家讯报告、欢迎、[原版线上周报二维码](../assets/bulletin-qr.png)、三套歌词场景、西奈旷野经文背景及祷告、三图回顾、竖版海报、三一颂版式。PCCS 标识、底栏、背景和字幕图层可分别编辑。每周提供新歌词、经文和讲道原稿。按流程补入当周活动照片、说明、海报和伴奏。

## 从资料到完整主日流程

1. 确认周次、当前完整 PPTX、当周歌单、讲道与家讯原稿。上周完整 PPTX 是顺序和视觉参考。用本周已确认素材更新每一项，并保持绝对页码、歌曲段落位置与源文件对应。用户给出完整新版本时从该版续修。
2. 按 [敬拜歌词流程](../../pccs-worship-pptx/references/lyrics-pipeline.md) 校对曲目、谱面和录音版本。依次展开串烧回接、重复的 B 段和尾句，分别写出每遍。新增经文放在用户指定的歌曲或段落之后。确认安排和内容，再分页。
3. 在完整主日稿中通常按开场、敬拜与插入经文、讲道、家讯及结束项目排页，以当次流程为准。若讲道原样并入，选原稿讲道页加入。周报页默认沿用模板内的二维码，用户提供更新时换入新码。二维码留足白边，从导出画面解码比对。相册按照片实际方向适配，海报完整等比例显示。按本周内容取用活动回顾和海报版式。
4. 渲染成品。逐页比内容、页序、同一布局的元素位置，保留的讲道页与原稿在同一投影尺寸渲染比对。对变动版式在桌面 PowerPoint 测试复制、改字、保存、重开，并检查字幕云雾开关。发生渲染器差异时，明确哪项检查用的是什么渲染器。
5. 后续修订从最近验证版另存新版本。用户有意压缩经文、调整 B 段或只换背景时，逐一局部修改并核对其他页。用户需要 PDF 时从同一最终 PPTX 导出。

## 跨平台生成

在 Windows、macOS 或 Linux 用 Python 3.10+ 运行。若 Codex 已提供 lxml 和 Pillow，复用该运行时。否则在独立 Python 环境安装 [依赖](../scripts/requirements-weekly.txt)。从技能目录运行：

```text
python -m pip install -r scripts/requirements-weekly.txt
python scripts/compose_weekly_pptx.py assets/weekly-plan.example.json demo.pptx
```

新周次将 [计划样例](../assets/weekly-plan.example.json) 复制到项目目录，按播放顺序填充 `slides`。图片、MP3 和源 PPTX 路径相对于计划文件。每个项目使用新的输出路径。

- `template` 选择下面的原型。可选 `name` 为编辑器中的页名，`text` 按对象名写可编辑文字，`notes` 写演讲者备注，`pictures` 按对象名放本周 PNG/JPEG。文字数组每项生成一个段落。字符串内部的 JSON `\n` 是同段落的软换行。新歌词通常用 2–3 行，保持原型字号。
- `{"source":"牧师讲道.pptx","pages":[1,2,3]}` 原样并入同尺寸的指定页，页码从 1 开始。省略 `pages` 导入整份。保留原生版式、图片、文字、备注和页面动画。桌面 PowerPoint 仍需验证媒体和交互。跨页链接涉及相邻页时，把目标页也收入。当周讲道和礼仪共用一个原稿时，只从这个入口取讲道页。
- 画布须一致。720×405 pt 和 960×540 pt 都是 16:9，但原生单位不同。若原讲道为 720 pt，沿用这一模板保护其渲染。960 pt 的歌词从已审核的行数据重新填入当前原型，或在 PowerPoint 原生合并后复查三套 Custom Layout 中的背景与相对字号。不要把同画面比例当成同尺寸。
- 使用相同模板、原始素材、内容与分行可以复现现版。不同机器的字体安装和应用渲染可能影响字形与换行。核对 KaiTi、SimSun、Microsoft YaHei、Noto Serif SC、Garamond、Georgia 等实际使用的字体。模板保留字体名称。需要在不同设备上看到固定版式时，分发经过校验的 PDF。

复现验证使用 v5 当周原始资料重建 67 页。两份 PPTX 在同一台 PowerPoint 以 1280 × 720 渲染，67 张图逐像素一致。示例计划只用于检查安装及生成。

| 原型名称 | 可变对象 |
| --- | --- |
| `opening` | 开场使用固定使命、异象和教会标识 |
| `water-first` / `water-lyrics` | `Lyrics`、`Song footer`、`Copyright`，首段另有 `Song title` |
| `sunrise-first` / `sunrise-lyrics` | 同上，使用山谷晨光场景 |
| `path-first` / `path-lyrics` | 同上，使用晨光小径场景 |
| `scripture` | `Scripture title`、`Scripture body`、`Scripture footer` |
| `announcements` / `welcome` / `prayer` | `Announcement title` / `Welcome title` / `Prayer title` |
| `bulletin` | `Online bulletin title`，图片 `bulletin-qr` 已嵌入既定二维码 |
| `gallery` | `Serving report title`、`Serving report subtitle`，图片 `gallery-1`、`gallery-2`、`gallery-3` |
| `poster` | 图片 `poster` |
| `doxology` | `Doxology title`、`Doxology lyrics` |

背景和图片嵌入 PPTX。`{"template":"bulletin"}` 可直接生成完整周报页。仅在换码时提供 `pictures.bulletin-qr`。歌词、经文和三一颂正文使用可编辑占位文字，画廊与海报使用中性占位图。交付前检查所有采用的页面已填入当周内容。需要现场可暂停／续播伴奏时，按 [离线音频与祷告](../../pccs-worship-pptx/references/audio-and-prayer.md) 添加 `audio_cues`。

## 经文容量和换图

- 保留给定的文字、标点和经节次序。长段经文按用户指定页数在节界分页，每节保留一个段落。语义自然处用软换行避开孤字。正文统一宋体、左对齐、无阴影。使用实际字形边界检查最大一页。
- 两页密集经文原型采用 720×405 pt 页面上的 25 pt 正文，正文起点约 49.5 pt，行距约 27.5 pt。这是实际可读的起点，段落密度改变时依据占用验证。优先上移标题、分隔线和正文，压缩段间留白。用户允许时才借用字幕区上缘，字幕内容按剩余净高实测。
- 西奈场景按《出埃及记》中旷野与寻求同在设计。绘制新背景时，把淡而安静的阅读区延伸到正文最密处，并将具体山脊放在最右侧或更低的位置。文字、Logo、底栏和字幕云雾保留为 PPTX 图层。
- 只换背景时先追踪当前页 → layout → picture → media。该版式与媒体在选定编辑范围内唯一时，可用下列命令。它校验所有共用该 layout 的页，在新文件中只替换一个 PNG 部件。若背景跨布局共享或不是这类全幅图，先在 PowerPoint 复制并隔离布局。

```text
python scripts/replace_layout_background.py current.pptx new-background.png revised.pptx --slides 23 24
```

## PDF 和验收

Windows 桌面 PowerPoint 可运行 `scripts/export_weekly_pdf.ps1 -Pptx final.pptx -Pdf final.pdf`。其他平台用桌面 PowerPoint 的 PDF 导出，或用可用的同类渲染器导出并复查字形和媒体。核对每页一张幻灯片、总页数及关键页渲染。PDF 是静态投影版，现场伴奏使用 PPTX 放映。

共享技能包保留可复用的版式、PCCS 品牌元素、背景及线上周报二维码。每周的歌词、经文、讲道和具体活动内容在周次工作区补入。
