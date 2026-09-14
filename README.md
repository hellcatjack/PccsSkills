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

- PCCS 紫色底栏保留为模板原生区域，位置 `y=345..405pt`；精修背景以 `1920x920`、`48:23` 为目标，完整放入 `720x345pt` 内容区。记录工具实际输出尺寸，比例误差不超过 `0.1%` 的近似尺寸可完整缩放放入，不裁切或负 Y 偏移。
- 每首歌或每个语义页面采用内容匹配的背景，同时维持珍珠白、淡紫、柔金和石灰灰的统一视觉家族。
- Logo 尖端使用原始模板像素和暖象牙白安全区融合；自定义 layout 使用唯一的 `Name` 和 `MatchingName`。

本次确认的投影规范已分别写入[歌词版式](skills/pccs-worship-pptx/references/visual-style.md)与[正式经文版式](skills/pccs-service-pptx/references/visual-style.md)：

| 页面内容 | 默认制作规范 |
| --- | --- |
| 歌词 | 楷体 `40pt`，固定行距 `50pt`，居中并保持在整页上半部；首页通常两行、续页最多三行，按完整乐句分页 |
| 每首歌首页标题 | 楷体 `44pt`；与正文保持稳定间距和留白 |
| 续页歌名及版权 | 歌名 `22pt`，版权通常 `9pt`，右对齐放入底部紫色栏；版权不得进入上方正式阅读区或遮盖教会标识 |
| 非歌曲经文 | 宋体正文统一、最高 `36pt`，严格左对齐、无阴影；章节标题微软雅黑 `28pt`，节号独立排在左侧 |
| 经文美化 | 可用与经文主题紧密相关的独立背景，并在标题与正文之间加入细金线、空心菱形等克制装饰，保持底栏风格不变 |

优先通过分页、文字锚点、行距和留白保证美观及会众朗读；不以自动缩字掩盖溢出。已确认的用户选择持续有效。新的明确歌词字号要求可以通过[字号覆盖参数](skills/pccs-worship-pptx/references/input-contract.md#explicit-song-size-overrides)传入检查器，无须修改检查脚本。

校对保留官方来源、作者及版权信息、实际使用许可依据和逐项决定。经文与歌词采用不同文本规则，保留经文标点、全角空格和固定源行；分离节号时验证原文可重构，并记录译本与节界依据。

检查既看输入计划，也检查成品的实际文字、字体、对齐和位置。所有独立布局须完成真实文字修改后的复制、保存、关闭、重开验证；测试仅操作新副本，不退出用户的 PowerPoint。小范围修订可复用已检视页面的同渲染器哈希证据，最终交付文件须与检查通过的文件一致。

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
