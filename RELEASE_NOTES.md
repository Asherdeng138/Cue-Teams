# Cue Teams 1.2.3-teams.2 — Windows portable / Windows 便携版

[English](#english) · [简体中文](#简体中文)

## English

**Download `Cue-Teams-Windows-x64.zip` to use the app. No Python installation is needed.**

### Quick start

1. Requires Windows 10 / 11 x64. Download the ZIP and choose **Extract All**.
2. Open the extracted `Cue-Teams` folder and run `CueTeams.exe`. Keep `_internal` alongside it.
3. Enable live captions in your Teams desktop meeting and keep the caption panel expanded.
4. Enter a file name, choose a save folder, and click **开始保存字幕** (start saving captions).
5. Check that captions and speaker names appear and the **已保存** (saved) count increases. Stop capture after the meeting.

The current application UI is in Simplified Chinese. This edition saves Teams' own captions without additional speech recognition. It supports speaker pairing, evolving caption-row updates, automatic TXT / JSON saving, file-name and folder controls, and a light interface with rounded controls.

### Downloads

- `Cue-Teams-Windows-x64.zip`: application, runtime dependencies, and license notices. No personal settings, meeting recordings, keys, or audio models are included.
- `Cue-Teams-Windows-x64.zip.sha256`: download checksum.
- `Cue-Teams-GitHub.zip`: prepared source for developers; source is also available in the repository.
- GitHub's automatic **Source code** archives do not include the runnable Windows application.

This community build is unsigned. Follow your organization's software requirements. Teams UI updates may affect capture; missing speaker identities cannot be reconstructed. Only captions read after capture starts are saved.

All 137 caption-related source regression tests passed. The portable EXE was tested with isolated synthetic data for startup, multiple speaker names, TXT / JSON saving, and save-folder migration. End-to-end validation in a real multi-participant Teams meeting is still pending.

Based on [Digitalgrub Cue v1.2.3](https://github.com/Digitalgrub-Org/meeting-copilot), under MIT. Original copyright and dependency notices are included. This is not an official Microsoft or Digitalgrub release.

---

## 简体中文

**普通用户请下载 `Cue-Teams-Windows-x64.zip`，无需安装 Python。**

### 开始使用

1. 适用 Windows 10 / 11 x64。下载 ZIP 后，右键选择“全部解压缩”。
2. 打开解压后的 `Cue-Teams` 文件夹，双击 `CueTeams.exe`。保留 `_internal` 文件夹。
3. 在 Teams 桌面会议中开启实时字幕，保持字幕面板展开。
4. 在本程序填写文件名、选择保存文件夹，点击“开始保存字幕”。
5. 确认正文出现字幕和姓名，且“已保存”计数增长；会后点击停止。

本版保存 Teams 自己生成的字幕，不重新识别音频。支持发言人配对、相同字幕行修订、TXT / JSON 自动保存、主界面文件名与路径设置，以及浅色圆角界面。

### 下载内容

- `Cue-Teams-Windows-x64.zip`：程序和运行依赖、许可文件；不含个人设置、会议记录、密钥或音频模型。
- `Cue-Teams-Windows-x64.zip.sha256`：下载文件校验值。
- `Cue-Teams-GitHub.zip`：整理后的开发源码，也可直接浏览仓库；开发者使用。
- GitHub 自动生成的 `Source code` 下载不包含可直接运行的 Windows 程序。

社区修订版，尚未进行代码签名。请按所在组织的软件管理要求使用。Teams 版本变化可能影响读取；发言人身份仅来自 Teams，缺失时无法恢复。仅保存开始采集后读到的字幕。

字幕相关源码回归测试 137 项通过。便携 EXE 已使用隔离的合成数据验证启动、多人姓名、TXT / JSON 保存和保存目录迁移；真实多人 Teams 会议的端到端验收仍待完成。

基于 [Digitalgrub Cue v1.2.3](https://github.com/Digitalgrub-Org/meeting-copilot)，MIT 许可；原版权声明和依赖许可随包保留。这不是 Microsoft 或 Digitalgrub 的官方版本。
