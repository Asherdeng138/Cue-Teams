"""Render only this application's own window for visual QA; no meeting is read."""
import ctypes
import sys
import tkinter as tk
from pathlib import Path
from PIL import ImageGrab
from teams_app import TeamsApp

ctypes.windll.user32.SetProcessDPIAware()
root=tk.Tk()
app=TeamsApp(root)
app.filename_var.set("示例项目 每日项目同步")
app.save_folder_var.set(str(Path.home()/"Documents"/"会议纪要"/"示例项目"))
app._append("Alex Chen", "接口文档已更新，今天确认测试范围和负责人员。")
app._append("Morgan Li", "收到。我会补充测试结果，并在下次会议前同步进展。")
app._append("Alex Chen", "好的，后续行动项会根据这份字幕整理。")
app._refresh_stats()
app.rec_var.set("界面预览")
app.rec_label.configure(foreground="#6e6e73")
app.status.set("界面预览：以上为示例内容，未连接会议。")
root.update_idletasks();root.update()
def capture():
    root.update_idletasks()
    hwnd=ctypes.windll.user32.GetAncestor(root.winfo_id(),2)
    ImageGrab.grab(window=hwnd).save(sys.argv[1])
    root.destroy()
root.after(450,capture)
root.mainloop()
