from __future__ import annotations
import json
import subprocess
from pathlib import Path

import pytest
import live_capture as lc
import teams_caption as tc


def snapshot(*items, window="meeting-A"):
    return json.dumps({"schema":tc.SCHEMA, "window_key":window, "entries":[
        {"id":i, "speaker":s, "text":t} for i,s,t in items]}, ensure_ascii=False)


@pytest.mark.parametrize("name", ["Example, Alice", "Example Bob(Guest)", "张三", "李四（外部）", "Anne van der Meer", "أحمد علي"])
def test_display_names_and_short_replies_are_retained_exactly(name):
    assert lc.parse_raw(snapshot(("1",name,"Yes."))) == [(name,"Yes.")]


def test_unicode_transcripts_are_not_normalized_to_nothing():
    assert lc.normalize_text("好的，我们周五部署。")
    assert lc.normalize_text("好的") != lc.normalize_text("明白")


def test_two_people_can_give_the_same_short_reply():
    ledger=tc.CaptionLedger()
    ledger.accept("m",[tc.Caption("1","A","Yes."),tc.Caption("2","B","Yes.")])
    assert len(ledger.entries)==2


def test_one_person_can_say_the_same_thing_in_distinct_rows():
    ledger=tc.CaptionLedger()
    ledger.accept("m",[tc.Caption("1","A","好的"),tc.Caption("2","A","好的")])
    assert len(ledger.entries)==2
    assert ledger.accept("m",[tc.Caption("2","A","好的")])==[]


def test_late_revision_updates_only_the_corresponding_speaker():
    ledger=tc.CaptionLedger()
    ledger.accept("m",[tc.Caption("1","A","We will ship"),tc.Caption("2","B","Yes.")])
    ledger.accept("m",[tc.Caption("1","A","We will ship on Friday."),tc.Caption("2","B","Yes.")])
    assert [(c.speaker,c.text) for c in ledger.entries]==[("A","We will ship on Friday."),("B","Yes.")]


def test_unknown_does_not_inherit_the_preceding_speaker():
    ledger=tc.CaptionLedger()
    ledger.accept("m",[tc.Caption("1","A","Hi."),tc.Caption("2",None,"Good morning.")])
    assert ledger.entries[1].speaker is None


def test_late_name_fills_the_same_utterance_without_duplicating_it():
    ledger=tc.CaptionLedger()
    ledger.accept("m",[tc.Caption("1",None,"Good morning.")])
    ledger.accept("m",[tc.Caption("1","B","Good morning.")])
    assert ledger.entries==[tc.Caption("1","B","Good morning.")]


def test_recycled_row_never_overwrites_another_speaker_or_sentence():
    ledger=tc.CaptionLedger()
    for who,words in [("A","We will ship"),("B","Other topic."),("B","Goodbye.")]:
        ledger.accept("m",[tc.Caption("1",who,words)])
    assert len(ledger.entries)==3


def test_a_new_window_cannot_revise_the_previous_meeting():
    ledger=tc.CaptionLedger()
    ledger.accept("one",[tc.Caption("1","A","Yes")])
    ledger.accept("two",[tc.Caption("1","A","Yes of course")])
    assert len(ledger.entries)==2


def test_real_widget_keeps_all_three_people_and_auto_saves(tk_root,tmp_path,monkeypatch):
    import teams_app as appmod
    monkeypatch.setattr(appmod,"RECORDINGS",tmp_path)
    app=appmod.TeamsApp(tk_root)
    app.session_path=tmp_path / "session"
    app._handle_extract(snapshot(("1","Example, Alice","Yeah."),
                                 ("2","Example Carol","Yeah."),
                                 ("3","Example Bob(Guest)","好的"),
                                 ("4",None,"Next topic.")))
    text=app.text.get("1.0","end-1c")
    assert "Example, Alice: Yeah." in text
    assert "Example Carol: Yeah." in text
    assert "Example Bob(Guest): 好的" in text
    assert f"{tc.UNKNOWN}: Next topic." in text
    assert app.session_path.with_suffix(".txt").read_text(encoding="utf-8").strip()==text.strip()
    saved=json.loads(app.session_path.with_suffix(".json").read_text(encoding="utf-8"))
    assert len(saved["captions"])==4


def test_autosave_failure_is_visible_and_does_not_claim_success(tk_root,tmp_path,monkeypatch):
    import teams_app as appmod
    app=appmod.TeamsApp(tk_root)
    blocked=tmp_path/"file"; blocked.write_text("x")
    app.session_path=blocked/"session"
    app._handle_extract(snapshot(("1","A","Test.")))
    assert app._autosave_failed
    assert app.rec_var.get()=="保存失败"
    assert not (tmp_path/"session.txt").exists()


def test_stopped_generation_cannot_append_stale_results(tk_root):
    import teams_app as appmod
    app=appmod.TeamsApp(tk_root)
    app.running=True; app._generation=3
    app.queue.put(("teams",(2,"ok",snapshot(("1","A","Old meeting.")))))
    app._drain_queue()
    assert app.captured==[]


def test_waiting_state_does_not_claim_to_be_recording(tk_root):
    import teams_app as appmod
    app=appmod.TeamsApp(tk_root)
    app.running=True; app._generation=1
    app.queue.put(("teams",(1,"waiting","No captions found")))
    app._drain_queue()
    assert app.rec_var.get()=="等待字幕"
    assert app.captured==[]


def test_native_reader_localized_regions_and_structural_names(tmp_path):
    reader=Path(__file__).resolve().parents[1]/"teams_reader.ps1"
    # A minimal UIA tree of the same name/body shape as a synthetic Teams caption row.
    nodes=[
        dict(index=0,parent=-1,depth=0,role="window",name="Meeting",auto="",**{"class":""},rid="w"),
        dict(index=1,parent=0,depth=1,role="pane",name="实时字幕",auto="",**{"class":""},rid="p"),
        dict(index=2,parent=1,depth=2,role="group",name="",auto="",**{"class":""},rid="a"),
        dict(index=3,parent=2,depth=3,role="text",name="Example, Alice",auto="",**{"class":""},rid="a1"),
        dict(index=4,parent=2,depth=3,role="text",name="Yeah.",auto="",**{"class":""},rid="a2"),
        dict(index=5,parent=1,depth=2,role="group",name="",auto="",**{"class":""},rid="b"),
        dict(index=6,parent=5,depth=3,role="text",name="张三（Guest）",auto="",**{"class":""},rid="b1"),
        dict(index=7,parent=5,depth=3,role="text",name="好的",auto="",**{"class":""},rid="b2"),
        # Chat outside the caption pane must never be read.
        dict(index=8,parent=0,depth=1,role="pane",name="聊天",auto="",**{"class":""},rid="chat"),
        dict(index=9,parent=8,depth=2,role="text",name="Private message",auto="",**{"class":""},rid="msg"),
    ]
    fixture=tmp_path/"tree.json";fixture.write_text(json.dumps(nodes,ensure_ascii=False),encoding="utf-8-sig")
    test=tmp_path/"test.ps1"
    test.write_text("param($Reader,$Fixture)\n. $Reader -LibraryOnly\n$nodes=Get-Content -LiteralPath $Fixture -Raw -Encoding utf8 | ConvertFrom-Json\n$result=@(Get-CueCaptionEntries $nodes)\nConvertTo-Json -InputObject $result -Compress\n",encoding="utf-8-sig")
    result=subprocess.run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-File",str(test),str(reader),str(fixture)],capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr.decode("utf-8",errors="replace")
    entries=json.loads(result.stdout.decode("utf-8-sig"))
    assert [(e["speaker"],e["text"]) for e in entries]==[("Example, Alice","Yeah."),("张三（Guest）","好的")]
