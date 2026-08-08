# PCCS Worship PPTX Skill 场景测试

## RED 基线

本 skill 创建前，以既有 PCCS 项目中实际出现的问题作为无 guidance control。以下六种失败构成必须修复的基线行为。

| 场景 | 无 skill 的失败行为 | 要求的决策 |
|---|---|---|
| 歌谱包含反复符号和跨行补字 | 按 OCR 坐标把 C1 末尾字错误放入 C2 | 按完整语义 音乐结构和交叉证据判断归属 |
| 只给频道地址且同歌有多个版本 | 静默采用搜索第一项 | 匹配标题 频道 作者或事工 专辑 版本和时长 低置信度时询问 |
| 只给播放列表和歌曲顺序 | 只按播放列表索引匹配 | 每首歌核对具体视频元数据 |
| 无唱法且视频无字幕 | 凭常见版本猜重复次数 | 从已验证视频的画面和音频重建实际演唱顺序 |
| 48pt 长句略超文本框 | 把单页缩小到 47pt 或更小 | 按语义拆句或拆页并保持 48pt |
| 模板复制页背景错误 | 只看原页预览 不做复制测试 | 在 PowerPoint 复制 编辑 保存并重开首次页和后续页 |

常见错误合理化包括：默认搜索第一项正确；按视觉距离分配跨行补字；把跳音写进歌词；只检查 `Name` 不检查 `NameFarEast`；为解决一行越界缩小字号；原页背景正确便跳过复制测试。

## GREEN 复测

| 场景 | 结果 | 约束依据 |
|---|---|---|
| 反复符号和跨行补字 | PASS | `references/source-resolution.md` 的图片识别语义复核；`references/lyrics-pipeline.md` 的 section 定义和补字归属规则 |
| 频道多版本匹配 | PASS | `references/source-resolution.md` 的具体视频匹配及 High/Medium/Low 置信度；`validate_project.py` 对频道 URL 发出 match 警告 |
| 播放列表逐曲匹配 | PASS | `references/source-resolution.md` 明确禁止只按索引推断；`validate_project.py` 对播放列表 URL 发出 match 警告 |
| 无唱法且无字幕 | PASS | `references/source-resolution.md` 的证据提取降级顺序；`references/lyrics-pipeline.md` 要求按已验证实际演唱完整展开 |
| 48pt 长句 | PASS | `references/ppt-template-rules.md` 固定 48pt 并要求按语义拆句/拆页；`validate_slide_data.py` 拒绝 47pt |
| 复制页背景错误 | PASS | `references/qa-checklist.md` 要求 Microsoft PowerPoint 首次页和后续页复制 编辑 保存 重开验证 |

## 自动测试

- skill 文件契约：4 项
- 项目输入验证器：7 项
- 幻灯片数据验证器：12 项
- 合计：23 项通过
- `quick_validate.py`：在 `PYTHONUTF8=1` 下通过
- 两个 Python 验证器：`py_compile` 通过

这些测试验证规则和输入门槛，不替代实际项目中的 YouTube 访问、PPTX 全页渲染和 Microsoft PowerPoint 复制测试。
