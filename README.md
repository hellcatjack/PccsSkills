# PCCS Skills

本仓库收录匹兹堡南区基督教会讲道视频制作项目中形成的可复用 Codex Skills。每个 Skill 均保留完整的 `SKILL.md`、参考资料、执行脚本、测试和 `agents/openai.yaml` 元数据。

## Skills

- `producing-single-camera-sermon-video`：将已含最终音轨的固定单机位牧师视频与本地 PPTX 合成为动态 1080p 讲道视频；内嵌音轨只允许码流复制，禁止重复处理。
- `replacing-video-audio-track`：以视频时间轴为基准，对齐、截取并替换较长或起点不同的独立录音，同时保留非目标视频流。
- `sermon-audio-restoration`：诊断并修复讲道音频中的啸叫、爆音、回声及人声音量不稳定问题，并保持严格的同步与时长约束。
- `sermon-chinese-subtitles`：为讲道视频制作和校验高精度简体中文字幕，支持香港口音纠正、圣经文本复核及可审计的时间轴证据。

## 目录结构

```text
skills/
  <skill-name>/
    SKILL.md
    agents/
    references/
    scripts/
    tests/
```

## 使用方式

将需要的目录复制到个人 Codex Skills 目录：

```powershell
Copy-Item -Recurse skills\<skill-name> $env:CODEX_HOME\skills\
```

也可以复制到项目级 `.agents/skills/`，由项目内的 Codex 会话自动发现。使用前请阅读对应 `SKILL.md`，并按其中的依赖和验证要求执行。

## 贡献者

- hellcatjack <hellcatjack@gmail.com>
