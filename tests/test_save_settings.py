from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from save_settings import clean_filename, destination, recording_file


@pytest.mark.parametrize("value", ["", "..", "CON", "NUL.txt", "COM1.notes", "a/b", "a\\b", "a:b", "bad?", "ending."])
def test_invalid_windows_names_are_rejected(value):
    with pytest.raises(ValueError):
        clean_filename(value)


def test_dots_and_unicode_are_kept_and_extensions_are_not_doubled():
    assert clean_filename("示例项目 周会 v1.2.txt") == "示例项目 周会 v1.2"
    assert recording_file(Path("示例项目 周会 v1.2"), ".txt").name == "示例项目 周会 v1.2.txt"


def test_existing_txt_or_json_is_never_silently_overwritten(tmp_path):
    (tmp_path/"weekly.txt").write_text("original")
    (tmp_path/"weekly_02.json").write_text("original")
    assert destination(str(tmp_path),"weekly").name == "weekly_03"
    assert (tmp_path/"weekly.txt").read_text() == "original"


def test_active_destination_can_be_saved_again(tmp_path):
    active=tmp_path/"weekly"
    recording_file(active,".txt").write_text("current")
    assert destination(str(tmp_path),"weekly",active=active) == active


@pytest.mark.parametrize("folder", ["", "relative/path"])
def test_missing_or_relative_folders_are_rejected(folder):
    with pytest.raises(ValueError):
        destination(folder,"weekly")


@pytest.fixture
def app(tk_root,monkeypatch):
    import teams_app as appmod
    from tkinter import Toplevel
    config=copy.deepcopy(appmod.cfg.get_config())
    config.pop("teams_save",None)
    saved=[]
    monkeypatch.setattr(appmod.cfg,"get_config",lambda:copy.deepcopy(config))
    def save(new):
        config.clear();config.update(copy.deepcopy(new));saved.append(copy.deepcopy(new))
    monkeypatch.setattr(appmod.cfg,"save_config",save)
    top=Toplevel(tk_root)
    instance=appmod.TeamsApp(top)
    instance._saved_settings_for_test=saved
    yield instance
    instance.running=False
    top.destroy()


def feed(app):
    app._handle_extract(json.dumps({"schema":"cue.teams.v1","window_key":"test","entries":[
        {"id":"a","speaker":"A","text":"Meeting content."}]}))


def test_name_and_folder_are_applied_to_automatic_saving(app,tmp_path):
    app.filename_var.set("周会 v1.2.txt")
    app.save_folder_var.set(str(tmp_path/"chosen"))
    assert app.apply_save_settings()
    feed(app)
    assert (tmp_path/"chosen"/"周会 v1.2.txt").read_text(encoding="utf-8").strip()=="A: Meeting content."
    assert (tmp_path/"chosen"/"周会 v1.2.json").exists()
    assert app._saved_settings_for_test[-1]["teams_save"]["directory"]==str(tmp_path/"chosen")


def test_rename_and_folder_change_keeps_old_files_and_continues_at_new_location(app,tmp_path):
    app.filename_var.set("old");app.save_folder_var.set(str(tmp_path/"one"))
    assert app.apply_save_settings()
    feed(app)
    old=app.session_path
    app.running=True
    app.filename_var.set("new");app.save_folder_var.set(str(tmp_path/"two"))
    assert app.apply_save_settings()
    assert app.running
    assert recording_file(old,".txt").exists()
    assert (tmp_path/"two"/"new.txt").read_text(encoding="utf-8")==recording_file(old,".txt").read_text(encoding="utf-8")
    app._handle_extract(json.dumps({"schema":"cue.teams.v1","window_key":"test","entries":[
        {"id":"b","speaker":"B","text":"Next comment."}]}))
    assert "B: Next comment." in (tmp_path/"two"/"new.txt").read_text(encoding="utf-8")
    assert "Next comment" not in recording_file(old,".txt").read_text(encoding="utf-8")


def test_new_session_gets_unique_name_without_overwriting(app,tmp_path,monkeypatch):
    monkeypatch.setattr(app,"_confirm_capture_notice",lambda:True)
    monkeypatch.setattr(app,"_poll",lambda:None)
    app.filename_var.set("Stand-up");app.save_folder_var.set(str(tmp_path))
    app.start();feed(app);first=app.session_path
    app.stop();app.start();feed(app)
    assert app.session_path != first
    assert app.session_path.name == "Stand-up_02"
    assert recording_file(first,".txt").exists()


def test_invalid_destination_does_not_interrupt_current_session(app,tmp_path,monkeypatch):
    import teams_app
    app.filename_var.set("valid");app.save_folder_var.set(str(tmp_path))
    assert app.apply_save_settings()
    feed(app);active=app.session_path
    app.running=True
    errors=[]
    monkeypatch.setattr(teams_app.messagebox,"showerror",lambda *a,**k:errors.append(a))
    app.filename_var.set("bad/name")
    assert app.apply_save_settings() is False
    assert app.running and app.session_path==active and errors


def test_new_writable_folder_can_rescue_a_failed_original_destination(app,tmp_path):
    blocked=tmp_path/"blocked"
    blocked.write_text("This is a file, not a directory")
    app.session_path=blocked/"session"
    feed(app)
    assert app._autosave_failed
    app.filename_var.set("rescued")
    app.save_folder_var.set(str(tmp_path/"working"))
    assert app.apply_save_settings()
    assert not app._autosave_failed
    assert (tmp_path/"working"/"rescued.txt").read_text(encoding="utf-8").strip()=="A: Meeting content."


def test_selected_folder_is_restored_when_app_reopens(app,tmp_path):
    import teams_app
    from tkinter import Toplevel
    app.filename_var.set("weekly");app.save_folder_var.set(str(tmp_path))
    assert app.apply_save_settings()
    top=Toplevel(app.root)
    reopened=teams_app.TeamsApp(top)
    try:
        assert reopened.save_folder_var.get()==str(tmp_path)
    finally:
        top.destroy()


def test_folder_picker_updates_main_interface_without_silent_migration(app,tmp_path,monkeypatch):
    import teams_app
    monkeypatch.setattr(teams_app.filedialog,"askdirectory",lambda **k:str(tmp_path))
    app.choose_save_folder()
    assert app.save_folder_var.get()==str(tmp_path)
    assert app.session_path is None


def test_controls_and_transcript_fit_a_small_window(app):
    app.root.geometry("960x680")
    app.root.deiconify();app.root.update();app.root.update_idletasks()
    for widget in (app.filename_entry,app.folder_entry,app.choose_folder_btn,app.apply_save_btn,app.start_btn):
        assert widget.winfo_ismapped()
        assert widget.winfo_width()>40
        assert widget.winfo_rootx()+widget.winfo_width() <= app.root.winfo_rootx()+app.root.winfo_width()+3
    assert app.text.winfo_height() >= 150


def test_rounded_start_button_still_handles_mouse_clicks(app,tmp_path,monkeypatch):
    monkeypatch.setattr(app,"_confirm_capture_notice",lambda:True)
    monkeypatch.setattr(app,"_poll",lambda:None)
    app.save_folder_var.set(str(tmp_path))
    app.filename_var.set("Button test")
    app.root.deiconify();app.root.update()
    def click():
        app.start_btn.event_generate("<ButtonPress-1>",x=15,y=15)
        app.start_btn.event_generate("<ButtonRelease-1>",x=15,y=15)
        app.root.update()
    click()
    assert app.running
    click()
    assert not app.running


def test_slim_scrollbar_can_scroll_a_long_transcript(app):
    from ui_widgets import SlimScrollbar
    def walk(widget):
        for child in widget.winfo_children():
            yield child
            yield from walk(child)
    scroll=next(w for w in walk(app.root) if isinstance(w,SlimScrollbar))
    app.text.insert("end","\n".join(f"Speaker: Caption number {i}." for i in range(150)))
    app.root.deiconify();app.root.update()
    assert app.text.yview()[0]==0
    scroll.event_generate("<ButtonPress-1>",x=5,y=8)
    scroll.event_generate("<B1-Motion>",x=5,y=scroll.winfo_height()-5)
    app.root.update()
    assert app.text.yview()[0]>.3
