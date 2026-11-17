# Cue Teams — Teams 桌面字幕保存

将 Microsoft Teams **桌面客户端已经生成的实时字幕**保存为本地 TXT 和 JSON，尽可能保留 Teams 提供的发言人姓名。无需浏览器插件，也不重新进行语音识别。

A Windows desktop tool that saves Microsoft Teams' own live captions locally, with the speaker labels exposed by Teams.

这是基于 [Digitalgrub 的 Cue / meeting-copilot](https://github.com/Digitalgrub-Org/meeting-copilot) **v1.2.3** 开发的社区衍生版本，专注 Teams 字幕保存。不是 Microsoft 或 Digitalgrub 发布的官方产品。原作者的 MIT 许可证及版权声明完整保留于 [LICENSE](LICENSE)，来源提交及改动说明见 [ATTRIBUTION.md](ATTRIBUTION.md)。

## 功能

- 使用 Windows UI Automation 读取 Teams 桌面会议字幕；自动寻找会议窗口，也可手动指定。
- 按字幕行关联发言人与正文，保留逗号、括号和中文姓名；姓名缺失时明确显示“未识别发言人”。
- 更新同一字幕行中逐步完善的句子，保留不同发言人的相同短句。
- 明确显示等待字幕、读取失败、保存失败与已保存状态。
- 自动保存 TXT / JSON；主界面可修改文件名、选择保存目录，并记住目录。
- 采集中可应用新名称和目录，保留原文件；遇到已有名称自动添加序号。
- 浅色圆角界面，支持滚动、快捷键和导出 TXT 副本。

本入口不提供录音、AI 摘要或云端处理；不需要配置 API Key 或启动 Ollama。部分原 Cue 模块仍作为导入依赖保留，直接运行 `live_capture.py` 会进入原有完整入口，不属于此版本的推荐用法。

## 环境

- Windows 10 / 11，Microsoft Teams 桌面客户端。
- Teams 会议能显示实时字幕；保持字幕面板展开且会议窗口可访问。
- 从源码运行：建议 Python 3.12（含 Tcl/Tk）、Windows PowerShell 5.1，以及下列依赖。
- 选择可写的程序和记录目录。组织策略、Teams 界面版本及辅助功能树可能影响读取。

## 从源码运行

下载本仓库源码或克隆后，在仓库根目录打开 PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-teams-lock.txt
.\.venv\Scripts\python.exe teams_app.py
```

锁定文件记录了此版本验证时的依赖，包含测试和构建工具。虽然其中有 AI SDK，它们是保留的原模块的导入依赖，此 Teams 入口不发起 AI 调用。

## 使用

1. 在 Teams 桌面会议中开启实时字幕，保持字幕面板展开。
2. 打开本程序，在主界面填写“会议 / 文件名”并选择保存文件夹。
3. 点击“开始保存字幕”；自动选择失败时，从下拉列表选择真正的会议窗口。
4. **确认正文出现姓名与字幕，且“已保存”计数增长**。仅点击开始不代表已采集成功。
5. 会后点击“停止保存字幕”，从所选文件夹查看 TXT / JSON。

快捷键：`Ctrl+R` 开始 / 停止，`Ctrl+S` 导出 TXT 副本。采集中更改名称或目录后，点击“应用更改”；此前的文件保留。

首次运行默认在程序目录创建 `data/` 和 `字幕记录/`，也可以用 `CUE_DATA_DIR`、`CUE_RECORDINGS_DIR` 指定初始目录。界面中已保存的目录偏好优先于初始记录目录。配置模块在指定数据目录不可写时可能回退到用户目录下的 `.meeting_workflow/`；避免将程序放进只读目录。

TXT 使用 UTF-8，内容格式为 `发言人: 字幕`。JSON 保存本程序采集到的字幕条目；不是 Teams 官方录制或带精确语音时间轴的转录导出。

## 故障排查与限制

- 空白或“等待字幕”：检查 Teams 自己是否已经出现字幕，选中的是否为会议窗口，字幕区域是否展开。帮助菜单可查看最近读取诊断。
- 只有正文没有姓名：本程序只使用 Teams 暴露的姓名，无法恢复隐藏身份、共享麦克风或会议室设备背后的实际个人。
- 本程序只保存开始采集后读到的字幕，不能恢复此前已经消失的内容。
- 读取使用轮询。字幕滚动过快、窗口隐藏 / 最小化或 Teams 更新都可能造成漏采；不能保证永久兼容或零遗漏。
- 合成字幕树、真实 Tk 控件、姓名配对、去重、保存路径和错误状态已有回归验证；**当前修订版仍需要在真实多人会议中完成端到端验收**。

## 测试

测试必须在 Windows 桌面会话中执行，Tk GUI 测试需要可用的显示环境。此公开包仅收录字幕相关回归测试；所有示例身份与文本均为测试用虚构数据。

```powershell
$env:CUE_DATA_DIR = Join-Path $env:TEMP ('cue-test-data-' + [guid]::NewGuid())
$env:CUE_RECORDINGS_DIR = Join-Path $env:TEMP ('cue-test-recordings-' + [guid]::NewGuid())
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe teams_app.py --self-test
```

自检会写入合成字幕文件，应保留上述隔离环境变量。测试结束后可关闭此 PowerShell 窗口，避免环境变量影响日常启动。GitHub Actions 的 Windows 工作流也运行这些检查。发布前可以执行：

```powershell
.\.venv\Scripts\python.exe scripts/check_public_source.py
```

## 构建便携版

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm CueTeams.spec
```

生成 `dist/Cue-Teams/CueTeams.exe`。分发或移动时必须保留整个 `dist/Cue-Teams/`，包括 `_internal/`；不要只复制 EXE。源码包没有包含预编译程序或运行时依赖。

构建配置排除音频转录引擎。发布二进制前另行核对实际打包依赖及其许可证，参见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。

## 上传到自己的 GitHub

建议仓库名：`cue-teams-captions`。仓库介绍可使用：

> Save Microsoft Teams desktop live captions locally with speaker labels. A Teams-focused fork of Digitalgrub Cue.

本目录已排除本地 Git 历史、会议记录、个人配置、缓存和构建产物。GitHub 网页上传时上传**解压后本目录内的文件**，包括隐藏的 `.gitignore` 与 `.github/`，不要只把 ZIP 当成源码上传。

也可在 GitHub 创建空仓库，再在此目录执行以下命令，将占位符替换为自己的地址：

```powershell
git init
git add .
git status --short
git commit -m "Add Teams-focused Cue derivative with attribution"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

这是可由你维护的二次开发项目；保留原作者声明，不将上游代码描述为全部从零原创。分享时不要加入 `data/`、字幕文件或截图中的真实会议信息。请在适用的会议规则下保存与分享字幕。

## 目录与许可

| 文件 | 用途 |
| --- | --- |
| `teams_app.py` | Teams 专用入口、保存流程及状态 |
| `teams_reader.ps1` | Teams 窗口和字幕 UI Automation 读取 |
| `teams_caption.py` | 字幕身份、修订与去重 |
| `save_settings.py` | 文件名、目录与冲突检查 |
| `ui_layout.py` / `ui_widgets.py` | 浅色圆角界面 |
| `live_capture.py` 及其他原模块 | 保留及修改的 Cue 底层代码 |
| `tests/` | 脱敏的字幕相关测试 |
| `UPSTREAM.json` | 原项目版本及文件来源清单 |

代码遵循 MIT，见 [LICENSE](LICENSE)。`Copyright (c) 2026 Digitalgrub` 保留不变。公开包中的 `cue.ico` 是重新绘制的简单对话框图标，见 [assets/README.md](assets/README.md)；没有分发原作者保留权利的图标、Logo 或宣传材料。
