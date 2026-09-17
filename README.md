# PCCS Skills

本仓库收录匹兹堡南区基督教会（PCCS）媒体与敬拜制作中形成的可复用 Codex Skills，覆盖 PowerPoint、讲道视频、音频修复、音轨替换和中文字幕。每个 skill 以 `SKILL.md` 为入口，并按需附带参考资料、脚本、测试和 Codex UI 元数据。

## 技能目录

### PowerPoint 制作

| Skill | 适用场景 | 主要交付 |
| --- | --- | --- |
| [`pccs-worship-pptx`](skills/pccs-worship-pptx/SKILL.md) | 根据模板、诗歌顺序、V/C/B/End 编排、歌词图片及 YouTube 来源制作敬拜歌词 PPTX | 歌词审计、完整歌词、可编辑 PPTX、逐页渲染与模板复制验证 |
| [`pccs-service-pptx`](skills/pccs-service-pptx/SKILL.md) | 制作封面、家讯、经文、欢迎、二维码、祷告、洗礼、圣餐、奉献及三一颂等非歌词页面 | 可编辑的每周主日礼仪 PPTX、素材与版式验证 |
| [`pccs-sermon-pptx`](skills/pccs-sermon-pptx/SKILL.md) | 逐页美化用于视频制作的牧师讲道 PPTX，尤其适合低清封面、经文拥挤和动画保留场景 | 封面风格统一、经文与讲道版式精校、结构保护及全尺寸 QA |

### 讲道视频制作

| Skill | 适用场景 | 主要交付 |
| --- | --- | --- |
| [`producing-single-camera-sermon-video`](skills/producing-single-camera-sermon-video/SKILL.md) | 横屏 4K 单机位牧师视频与本地 PPTX 合成，支持留白双栏、开头遮挡和牧师画面降噪 | 1920×1080/30 视频、语义 PPT 时间轴、可见片段降噪规划、已认可音轨码流复制与完整验证 |

### 音频与字幕

| Skill | 适用场景 | 主要交付 |
| --- | --- | --- |
| [`sermon-audio-restoration`](skills/sermon-audio-restoration/SKILL.md) | 诊断和修复讲道录音中的啸叫、爆音、回声或人声音量不稳定 | 保持时间轴的修复音频、诊断证据及验证报告 |
| [`replacing-video-audio-track`](skills/replacing-video-audio-track/SKILL.md) | 将较长或起点不同的独立录音与视频对齐，并仅替换目标音轨 | 对齐报告、保留非目标流的新视频及同步验证 |
| [`sermon-chinese-subtitles`](skills/sermon-chinese-subtitles/SKILL.md) | 为讲道视频制作高精度简体中文字幕，处理香港口音、圣经文本和神性代词 | 经人工语义复核、逐词对齐且可审计的 SRT |

## 推荐制作顺序

每周讲道项目按实际素材选择需要的环节，不要求机械地运行全部 skill：

1. 相机音频存在明显缺陷时，先用 `sermon-audio-restoration` 修复独立录音。
2. 需要把独立录音写回视频时，用 `replacing-video-audio-track` 对齐并替换目标音轨。
3. 用 `pccs-sermon-pptx` 美化讲道幻灯片，并完成结构与视觉 QA。
4. 用 `producing-single-camera-sermon-video` 锁定已认可音轨，检查横屏 4K 构图，按可见范围裁切、缩放和处理牧师噪点，再与独立的原生 PPT 合成为讲道成片。
5. 用 `sermon-chinese-subtitles` 对最终视频制作和校验简体中文字幕。

敬拜歌词页与其他主日礼仪页分别使用 `pccs-worship-pptx` 和 `pccs-service-pptx`；混合式主日 PPT 应保留两套 skill 各自的可编辑版式，再进行组合。

### 横屏 4K 制作约定

- 默认拍摄为横屏 4K，交付仍为 1080p/30；每次实测帧率、色彩和时间轴，不假定所有 4K 都是 30 fps SDR。
- 以留白双栏 A 为构图起点，依据当次人物、讲台与手势重新确定裁切；用户已批准的布局和已接受的微小音画差异持续有效。
- 摄像机设置阶段由当次 `cameraForbiddenBefore` 指定，使用 PPT 封面遮挡并完整保留音频；不把某一次的 16 秒变成固定规则。
- 先裁切并缩放到实际显示大小，再降噪牧师可见片段；过渡帧保留，多帧模型补足前后文。PPT 不经过降噪，片段按原始帧索引还原完整时间轴。
- 原始画面和已优化音轨可以来自同一次拍摄的不同文件，但必须分别锁定来源并验证时间映射。已压软的画面不应反复转码。
- [GPT-6 执行约定](skills/producing-single-camera-sermon-video/references/gpt6-execution.md)规定异步任务调度、中途需求调整、证据复用与断点恢复；只使用宿主实际提供的能力，不把模型推理当作视频降噪或原生音视频解码。

视频脚本验证与回归测试：

```powershell
python -m pytest skills/producing-single-camera-sermon-video/tests -q
```

新增的 `plan_camera_processing.py` 生成可见帧与上下文范围，**不执行神经降噪**；实际处理、性能试片和片段组装要求见 [画面降噪规范](skills/producing-single-camera-sermon-video/references/camera-denoising.md)。构图脚本支持留白双栏和已处理的完整时间轴牧师面板；额外标题图层须单独制作并逐帧核验。

## PCCS PPT 制作共识

三个 PowerPoint skill 的职责不同，但共享以下交付原则：

- 用户明确指定的最新模板或源 PPTX 优先；编辑前先盘点页面、文字、硬换行、对象、图片、动画和切换效果。
- 保留用户提供的文字和真实素材。纠正文字或经文节号时保留原文、核实依据并记录决定，不静默改写、合并、拆分或重排内容。
- 背景服务于阅读；正文保持可编辑，并按用途避开视频安全边界或会众视线遮挡区。歌词可用克制阴影，正式经文正文不加阴影。
- 同一页面家族使用稳定的标题基线、正文起点、文本框尺寸、字体与字号规则；只有页面容量不足时才逐级调整字号和段落间距。
- 最终文件必须逐页全尺寸渲染检查，并执行对应 skill 的结构、内容、复制或重开验证。

### 敬拜与礼仪 PPT

当前默认使用宽屏分层 **wide-v3**，用户明确提供的最新模板仍优先。

- 画布为960×540pt（16:9）；独立背景完整铺满画布。上部尽量浅色、低对比，主要景物安排在右侧中部，下方四分之一保留简单自然灰紫纹理，禁止把紫色纯色块或字幕烟雾画进背景。
- Logo、紧凑的单行中英文教会名称、低紫色底栏和字幕云雾保持独立。当前字幕紫色云雾**默认显示**，65%透明备选层隐藏，避免重复叠加；用户可在选择窗格中关闭。
- 每首歌或每组经文采用匹配内容的新场景，保持珍珠白、淡紫、柔金和石灰灰的统一风格。全新重绘只输入完整提示词，不以旧图为编辑底图。
- 歌名40pt、歌词52pt，歌词最多三行，优先两行完整乐句；保留贴近字形的轻阴影。经文样页为38pt宋体，具体按容量调整，并保留原文、标点、全角空格及固定源行。
- 两行英文字幕以28pt作为测试起点，保留宽裕的中央区域。65%备选云雾PNG是原始底图，需要同时应用PPT内0.35的alpha乘数；素材清单已记录，不能只根据文件名判断透明度。
- 只换背景时保持源文件页数、顺序、文字、字号、Logo、底栏和云雾设置，按媒体清单替换；不要重建歌词或重新分页。

两个技能都完整包含以下资源，安装时请连同assets一起复制：

| 资源 | 用途 |
| --- | --- |
| [完整参考PPTX](skills/pccs-worship-pptx/assets/pccs-wide-v3.pptx) | 64页定稿样式与五种背景；新周次只复用所需代表页并替换历史内容 |
| [无上部背景模板](skills/pccs-worship-pptx/assets/pccs-wide-v3-foreground.pptx) | 单页可编辑模板，字幕紫雾默认显示，正文和备注不含旧歌词 |
| [图层与哈希清单](skills/pccs-worship-pptx/assets/pccs-wide-v3/manifest.json) | 独立Logo、云雾、底部装饰原件及实际透明度设置 |
| [优化规范](skills/pccs-worship-pptx/references/layered-template-v3.md) | 字号比例、构图、字幕、分层和检查细节 |
| [背景提示词](skills/pccs-worship-pptx/references/background-prompts-v3.md) | 五幅图的完整提示词，可按实际内容替换景物描述 |

保留旧版兼容：`legacy`对应原始720×405模板的48pt歌词/54pt歌名；仓库较早的精修方案使用40pt歌词/44pt歌名和36pt正式经文，称为`legacy-refined`，旧计划省略profile时仍走原有校验。新项目必须明确设置`template_profile: wide-v3`。旧版背景与字号规则不覆盖新模板。

校验仍保留来源与版权审计、节号拆分后的原文重构、混合页面映射和实际文字检查。宽屏歌词校验按52pt核查真实文本；标题、经文、前景和字幕另作原生/视觉检查。PowerPoint QA只操作新副本，不退出用户的PowerPoint，并检查云雾显隐和前景几何在复制、修改、保存、重开后保持一致。

### 讲道 PPT

以下规则用于视频中的牧师讲道稿；敬拜投影的上半部歌词位置和经文 `36pt` 规范不自动覆盖已有讲道稿的动画、字体及视频安全网格。

- 封面是整套插画风格的视觉基准。低清封面应按原镜头、人物、物件、负空间和光线高清重绘，不生成文字或擅自增加元素。
- 封面图片通过原位媒体替换保护图片关系、裁切、层级、对象 ID 和动画，不使用普通形状填充覆盖。
- 连续经文页和讲道内容页分别使用统一网格；经文后续节号前默认增加 `4pt`，正文后默认 `1pt`，密集页再按既定容量顺序收紧。
- 使用深色背景、浅色文字和克制黑色阴影，充分利用视频安全高度，避免把正文压缩在画面上半部。

## 目录结构

```text
skills/
  <skill-name>/
    SKILL.md              # 入口、适用条件、核心流程和硬性边界
    agents/openai.yaml    # Codex UI 名称、简介和默认调用提示
    references/           # 按场景加载的详细规范
    scripts/              # 可重复执行的确定性工具
    tests/                # 契约、校验器和回归测试
    assets/               # 模板或参考素材（仅在需要时存在）
```

`SKILL.md` 应保持为清晰的入口和路由层。大段操作规范放入 `references/`，重复执行且容易出错的操作放入 `scripts/`，不在每个 skill 内另建重复的 README。

## 安装与调用

将整个仓库中的 skills 安装到个人 Codex 目录：

```powershell
$personalSkillRoot = if ($env:CODEX_HOME) {
  Join-Path $env:CODEX_HOME 'skills'
} else {
  Join-Path $env:USERPROFILE '.codex\skills'
}
New-Item -ItemType Directory -Force -Path $personalSkillRoot | Out-Null
Copy-Item -Recurse -Force .\skills\* $personalSkillRoot
```

也可以只复制一个 skill，或将所需目录复制到项目级 `.agents/skills/`。安装后可在请求中直接写 `$pccs-sermon-pptx` 等 skill 名称；符合 `description` 的任务也可被 Codex 自动识别。

## 验证与维护

仓库级目录和文档契约：

```powershell
$env:PYTHONUTF8 = '1'
python -m unittest tests.test_repository_docs tests.test_ppt_skills_catalog -v
```

PPT skills 使用独立测试目录运行，避免不同 skill 中同名测试模块相互冲突：

```powershell
python -m unittest discover -s skills/pccs-worship-pptx/tests -p 'test_*.py' -q
python -m unittest discover -s skills/pccs-service-pptx/tests -p 'test_*.py' -q
python -m unittest discover -s skills/pccs-sermon-pptx/tests -p 'test_*.py' -q
```

音频修复 skill 使用自身的固定依赖环境：

```powershell
.\skills\sermon-audio-restoration\scripts\bootstrap.ps1
.\.audio-skill-venv\Scripts\python.exe -m pytest -q skills/sermon-audio-restoration/tests
```

修改 skill 后还应：

1. 运行该 skill 自带的全部测试和脚本语法检查。
2. 使用 Codex `skill-creator` 附带的 `quick_validate.py` 校验 `SKILL.md` frontmatter、名称和脚手架残留。
3. 检查 `SKILL.md` 能找到所有必读 reference，Markdown 本地链接均可解析。
4. 更新根 README 的技能目录或共享流程，并在提交前审阅 `git diff`。

各媒体 skill 的额外依赖和验收命令以其 `SKILL.md` 及存在时的 `references/verification-contract.md` 为准。

## 贡献者

- hellcatjack <hellcatjack@gmail.com>
