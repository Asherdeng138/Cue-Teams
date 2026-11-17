"""A local Teams-caption-only edition of Cue. Original MIT-licensed app is retained.

This entry point deliberately offers no audio recording or cloud/AI actions.
"""
from __future__ import annotations

import json
import os
import sys
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
os.environ.setdefault("CUE_DATA_DIR", str(APP_ROOT / "data"))

import config as cfg
cfg.DEFAULTS["ui"]["transcript_only"] = True
cfg.DEFAULTS["archive"]["on_close"] = "never"
cfg.DEFAULTS["cadence"]["caption_poll_sec"] = 1

import live_capture as lc
import teams_caption
import ui_layout
from save_settings import check_writable, destination, recording_file

TEAMS_READER = lc._resource_dir() / "teams_reader.ps1"
RECORDINGS = Path(os.environ.get("CUE_RECORDINGS_DIR", str(APP_ROOT / "字幕记录")))
VERSION = "1.2.3-teams.2"


class TeamsApp(lc.LiveCapture):
    def __init__(self, root):
        self.session_path: Path | None = None
        self._last_success = 0.0
        self._started_at = 0.0
        self.preferred = tk.StringVar(root, value="自动选择正在开会的窗口")
        self._generation = 0
        self._diagnostic = ""
        self._autosave_failed = False
        saved_folder = cfg.get_config().get("teams_save", {}).get("directory", str(RECORDINGS))
        self.save_folder_var = tk.StringVar(root, value=saved_folder)
        self.filename_var = tk.StringVar(root, value=datetime.now().strftime("会议字幕_%Y-%m-%d_%H-%M-%S"))
        self.save_preview_var = tk.StringVar(root)
        self.save_hint_var = tk.StringVar(root, value="开始记录前可直接修改；记录中修改后，点击「应用更改」。")
        super().__init__(root)
        root.title(f"Cue Teams · 字幕保存 · {VERSION}")
        root.geometry("1120x780")
        root.minsize(940, 650)
        self.poll_seconds.set(1)
        self.transcript_only.set(True)
        self.status.set("就绪：Teams 开启实时字幕后，点击「开始保存字幕」。")
        self.save_folder_var.trace_add("write", self._preview_destination)
        self.filename_var.trace_add("write", self._preview_destination)
        self._preview_destination()

    def _setup_styles(self):
        ui_layout.setup_styles(self)

    def _build_menubar(self):
        bar = tk.Menu(self.root)
        file = tk.Menu(bar, tearoff=False)
        file.add_command(label="开始／停止保存字幕", command=self.toggle, accelerator="Ctrl+R")
        file.add_command(label="另存为 TXT…", command=self.save_as, accelerator="Ctrl+S")
        file.add_command(label="打开字幕记录文件夹", command=self.open_records)
        bar.add_cascade(label="文件", menu=file)
        help = tk.Menu(bar, tearoff=False)
        help.add_command(label="使用说明", command=lambda: messagebox.showinfo("使用说明",
            "1. 在 Teams 桌面会议中开启实时字幕，并保持字幕面板展开。\n"
            "2. 点击开始保存字幕。首次读到字幕后，状态才会变为绿色。\n"
            "3. 在主界面填写会议名称并选择保存文件夹；软件会记住保存路径。\n"
            "4. 可另存为 TXT。姓名仅来自 Teams；未提供姓名时会明确标记。\n\n"
            "Teams 界面更新仍可能影响读取。等待字幕或报错状态不代表保存成功。"))
        help.add_command(label="查看最近的读取诊断", command=lambda: messagebox.showinfo("读取诊断", self._diagnostic or self.status.get()))
        help.add_command(label="关于", command=lambda: messagebox.showinfo("关于",
            f"Cue Teams {VERSION}\n基于 Digitalgrub Cue v1.2.3，MIT 许可。\n本地定制版；不是微软或原作者发布的官方版本。"))
        bar.add_cascade(label="帮助", menu=help)
        self.root.config(menu=bar)
        self.root.bind("<Control-r>", lambda e: self.toggle())
        self.root.bind("<Control-s>", lambda e: self.save_as())

    def _build_capture_bar(self, root):
        ui_layout.capture_bar(self, root)

    def _build_statusbar(self, root):
        ui_layout.statusbar(self, root)

    def _build_body(self, root):
        ui_layout.body(self, root)

    def _apply_transcript_only(self, save=True):
        self._refresh_stats()

    def _schedule_auto_index(self):
        pass

    def _set_initial_sash(self):
        pass

    def _warm_kb(self):
        pass

    def _sync_empty_state(self):
        if self.captured:
            self._empty_panel.place_forget()
        else:
            self._empty_panel.place(relx=.5, rely=.42, anchor="center")

    def _append(self, speaker, text):
        super()._append(speaker, text)
        self._style_speaker(len(self.captured)-1, speaker)
        self._sync_empty_state()

    def _replace_entry(self, index, speaker, text):
        super()._replace_entry(index, speaker, text)
        self._style_speaker(index, speaker)

    def _style_speaker(self, index, speaker):
        if not speaker:
            return
        ranges = self.text.tag_ranges(self._entry_tags[index])
        if ranges:
            tag = "unknown_speaker" if speaker == teams_caption.UNKNOWN else "speaker"
            self.text.tag_add(tag, ranges[0], f"{ranges[0]}+{len(speaker)+1}c")

    def _reset_transcript(self):
        super()._reset_transcript()
        self._sync_empty_state()

    def _preview_destination(self, *_args):
        try:
            # Preview is read-only; applying or starting performs the write check.
            selected = destination(self.save_folder_var.get(), self.filename_var.get(), active=self.session_path)
            if self.session_path and selected != self.session_path:
                self.save_preview_var.set(f"当前保存：{recording_file(self.session_path, '.txt')}")
                self.save_hint_var.set("有未应用的更改。点击「应用更改」后，现有字幕和后续字幕将保存到新位置；原文件保留。")
            else:
                label = "当前保存" if self.session_path else "将保存到"
                self.save_preview_var.set(f"{label}：{recording_file(selected, '.txt')}")
                self.save_hint_var.set("自动保存 TXT + JSON。重名时会添加序号，避免覆盖其他会议。")
        except (ValueError, OSError) as error:
            self.save_preview_var.set(str(error))
            self.save_hint_var.set("请检查文件名和保存文件夹。")

    def choose_save_folder(self):
        initial = Path(os.path.expandvars(self.save_folder_var.get())).expanduser()
        if not initial.is_dir():
            initial = RECORDINGS if RECORDINGS.is_dir() else APP_ROOT
        chosen = filedialog.askdirectory(parent=self.root, title="选择字幕保存文件夹", initialdir=str(initial), mustexist=False)
        if chosen:
            self.save_folder_var.set(chosen)

    def _save_folder_preference(self, folder):
        config = cfg.get_config()
        config.setdefault("teams_save", {})["directory"] = str(folder)
        cfg.save_config(config)

    def apply_save_settings(self, *, new_session=False):
        previous = self.session_path
        try:
            selected = destination(self.save_folder_var.get(), self.filename_var.get(),
                                   active=None if new_session else self.session_path)
            check_writable(selected.parent)
        except (OSError, ValueError) as error:
            messagebox.showerror("无法使用这个保存位置", str(error), parent=self.root)
            return False
        # A running transcript is copied to its new destination. The prior files stay
        # intact, and the active destination only changes if the copy succeeds.
        if not new_session and self.captured:
            # A new writable folder must also be usable to rescue an unwritable
            # original destination. Preserve its latest snapshot when possible.
            self._autosave()
        self.session_path = selected
        if not new_session and self.captured and not self._autosave():
            failed_message = self._diagnostic
            self.session_path = previous
            self._autosave()
            messagebox.showerror("新位置保存失败", f"当前保存位置未更改。\n{failed_message}", parent=self.root)
            self._preview_destination()
            return False
        self.filename_var.set(selected.name)
        self.save_folder_var.set(str(selected.parent))
        try:
            self._save_folder_preference(selected.parent)
        except OSError as error:
            self._diagnostic = str(error)
            self.status.set("保存设置已应用，但未能记住路径。")
        else:
            self.status.set("保存设置已应用。现有字幕及后续字幕将保存到选定位置。" if self.captured else "保存设置已应用，开始后将自动保存到选定位置。")
        self._preview_destination()
        return True

    def refresh_meetings(self):
        titles = [title for title in lc.window_capture.list_windows()
            if title.lower().endswith("microsoft teams") and not title.lower().startswith(("chat |", "聊天 |", "calendar |", "日历 |"))]
        self.preferred_box["values"] = ["自动选择正在开会的窗口", *titles]

    def start(self):
        if not self._confirm_capture_notice():
            return
        if self.captured:
            if not self._autosave():
                return
        if not self.apply_save_settings(new_session=True):
            return
        if self.captured:
            self._reset_transcript()
        self._generation += 1
        self._started_at = time.monotonic()
        self._last_success = 0.0
        self._autosave_failed = False
        self.teams_mode, self.zoom_mode = True, False
        self.capture_window_title = "Captions"
        self._preferred_title = self.preferred.get()
        self.running = True
        self.start_btn.configure(text="停止保存字幕")
        self.preferred_box.configure(state="disabled")
        self._start_rec_blink()
        self.status.set("等待读取第一条字幕。此时还不能确认保存成功。")
        self._poll()

    def _start_rec_blink(self):
        self.rec_var.set("等待字幕")
        self.rec_label.configure(foreground="#a16207")

    def _stop_rec_blink(self):
        self.rec_var.set("已停止")
        self.rec_label.configure(foreground="#6b7280")

    def _poll(self):
        if not self.running:
            return
        if not self._extract_busy:
            self._extract_busy = True
            import threading
            generation = self._generation
            argv = self._extract_argv()
            threading.Thread(target=self._read_once, args=(generation, argv), daemon=True).start()
        if self._last_success and time.monotonic() - self._last_success > 15:
            self.rec_var.set("暂未收到新字幕")
            self.rec_label.configure(foreground="#a16207")
        self.poll_after_id = self.root.after(1000, self._poll)

    def _extract_argv(self):
        args = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                str(TEAMS_READER), "-OutPath", str(lc.RAW_TXT), "-TeamsMode"]
        title = getattr(self, "_preferred_title", "")
        if title and title != "自动选择正在开会的窗口":
            args += ["-PreferredWindow", title]
        return args

    def _read_once(self, generation, argv):
        import subprocess
        try:
            result = subprocess.run(argv, capture_output=True, timeout=18,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            if result.returncode == 0:
                self.queue.put(("teams", (generation, "ok", lc.RAW_TXT.read_text(encoding="utf-8-sig"))))
            else:
                message = result.stderr.decode("utf-8", errors="replace").strip()
                self.queue.put(("teams", (generation, "waiting" if result.returncode == 2 else "error", message)))
        except Exception as error:
            self.queue.put(("teams", (generation, "error", str(error))))
        finally:
            self._extract_busy = False

    def _drain_queue(self):
        import queue
        try:
            while True:
                _kind, (generation, kind, payload) = self.queue.get_nowait()
                if generation != self._generation or not self.running:
                    continue
                if kind == "ok":
                    try:
                        self._handle_extract(payload)
                    except (ValueError, TypeError, KeyError) as error:
                        self._diagnostic = str(error)
                        self.rec_var.set("读取失败")
                        self.rec_label.configure(foreground="#b91c1c")
                        self.status.set("字幕数据格式异常。本轮没有保存新字幕，可查看读取诊断。")
                else:
                    self._diagnostic = payload
                    self.rec_var.set("等待字幕" if kind == "waiting" else "读取失败")
                    self.rec_label.configure(foreground="#a16207" if kind == "waiting" else "#b91c1c")
                    self.status.set("没有读到字幕：确认字幕已展开；可从上方手动选择当前会议窗口。" if kind == "waiting" else "读取失败：本轮没有保存新字幕。详情见「帮助 → 查看最近的读取诊断」。")
        except queue.Empty:
            pass
        self.root.after(150, self._drain_queue)

    def _handle_extract(self, raw):
        snapshot = teams_caption.read_snapshot(raw)
        if snapshot is None:
            raise ValueError("Caption reader returned an unsupported format")
        if not snapshot[1]:
            self._start_rec_blink()
            self.status.set("本轮未取得字幕，仍在等待。")
            return
        before = tuple(self.captured)
        super()._handle_extract(raw)
        changed = before != tuple(self.captured)
        if changed:
            self._last_success = time.monotonic()
        if (changed or self._autosave_failed) and not self._autosave():
            self.rec_var.set("保存失败")
            self.rec_label.configure(foreground="#b91c1c")
            return
        unknown = sum(1 for speaker, _ in self.captured if speaker == teams_caption.UNKNOWN)
        people = len({speaker for speaker, _ in self.captured if speaker != teams_caption.UNKNOWN})
        quiet = self._last_success and time.monotonic() - self._last_success > 15
        self.rec_var.set(f"已保存 {len(self.captured)} 条" + (" · 等待发言" if quiet else ""))
        self.rec_label.configure(foreground="#a16207" if quiet else "#15803d")
        self.status.set(f"{people} 位已识别发言人 · {unknown} 条未取得姓名 · 已自动保存")

    def _autosave(self):
        if not self.session_path or not self.captured:
            return True
        try:
            text = self.text.get("1.0", "end-1c").strip() + "\n"
            records = [{"speaker":who, "text":words} for who, words in self.captured]
            for suffix, value in ((".txt", text), (".json", json.dumps({"version":VERSION, "transcript":text, "captions":records}, ensure_ascii=False, indent=2))):
                path = recording_file(self.session_path, suffix)
                temp = path.with_suffix(suffix + ".tmp")
                temp.write_text(value, encoding="utf-8")
                temp.replace(path)
            self._autosave_failed = False
            return True
        except OSError as error:
            self._autosave_failed = True
            self._diagnostic = str(error)
            self.status.set("自动保存失败，请使用「另存为 TXT」保留窗口中的文字。")
            return False

    def stop(self):
        super().stop()
        self._generation += 1
        self.preferred_box.configure(state="readonly")
        self.start_btn.configure(text="开始保存字幕")
        self._autosave()
        self.status.set(f"已停止，共保留 {len(self.captured)} 条字幕。" + ("自动保存失败，请另存为。" if self._autosave_failed else ""))

    def _refresh_stats(self):
        self.stats.set(f"{len(self.captured)} 条字幕 · 本地保存")

    def save_as(self):
        text = self.text.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showinfo("暂无字幕", "还没有读取到字幕，无法导出。")
            return
        folder = self.session_path.parent if self.session_path else Path(self.save_folder_var.get()).expanduser()
        if not folder.is_dir():
            folder = APP_ROOT
        path = filedialog.asksaveasfilename(parent=self.root, title="导出字幕副本", initialdir=str(folder),
            initialfile=(self.session_path.name if self.session_path else "Teams字幕") + ".txt",
            defaultextension=".txt", filetypes=[("文本文件", "*.txt")])
        if path:
            try:
                Path(path).write_text(text+"\n", encoding="utf-8")
                self.status.set(f"已保存：{path}")
            except OSError as error:
                messagebox.showerror("保存失败", str(error))

    def open_records(self):
        try:
            folder = self.session_path.parent if self.session_path else destination(self.save_folder_var.get(), self.filename_var.get()).parent
            check_writable(folder)
            os.startfile(folder)
        except (OSError, ValueError) as error:
            messagebox.showerror("无法打开文件夹", str(error), parent=self.root)

    def _on_close(self):
        self.stop()
        if self._autosave_failed:
            messagebox.showerror("字幕尚未保存", "自动保存失败。请先点击「另存为 TXT」，再关闭窗口。")
            return
        self.root.destroy()


def main():
    if "--self-test" in sys.argv:
        root = tk.Tk(); root.withdraw()
        app = TeamsApp(root)
        RECORDINGS.mkdir(parents=True, exist_ok=True)
        app.filename_var.set("_self_test.v2")
        app.save_folder_var.set(str(RECORDINGS / "before"))
        assert app.apply_save_settings()
        app._handle_extract(json.dumps({"schema":"cue.teams.v1", "window_key":"self-test", "entries":[
            {"id":"a", "speaker":"Test, Alice", "text":"Yes."},
            {"id":"b", "speaker":"测试乙（Bob）", "text":"Yes."}]}))
        assert len(app.captured) == 2
        original = app.session_path
        assert recording_file(original, ".txt").exists()
        app.filename_var.set("_self_test.renamed")
        app.save_folder_var.set(str(RECORDINGS / "after"))
        assert app.apply_save_settings()
        assert recording_file(original, ".txt").exists()
        assert recording_file(app.session_path, ".txt").exists()
        assert recording_file(app.session_path, ".json").exists()
        root.destroy()
        return
    root = tk.Tk()
    try:
        import sv_ttk
        sv_ttk.set_theme("light")
        root.iconbitmap(str(lc.ICON_PATH))
    except Exception:
        pass
    TeamsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
