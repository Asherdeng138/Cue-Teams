"""Airy light layout for the Teams edition. All inputs remain native keyboard controls."""
import tkinter as tk
from tkinter import ttk
from ui_widgets import BG, INK, MUTED, FIELD, BLUE, FONT, RoundedCard, RoundedField, RoundedButton, SlimScrollbar, rounded


def setup_styles(app):
    app.root.configure(background=BG)
    style=ttk.Style(app.root)
    style.theme_use("clam")
    style.configure("TLabel",font=FONT)
    style.configure("App.TFrame",background=BG)
    style.configure("Card.TFrame",background="white",borderwidth=0,relief="flat")
    style.configure("Card.TLabel",background="white",foreground=MUTED,font=("Microsoft YaHei UI",9))
    style.configure("CardTitle.TLabel",background="white",foreground=INK,font=("Microsoft YaHei UI",11,"bold"))
    style.configure("Field.TLabel",background="white",foreground="#6e6e73",font=("Microsoft YaHei UI",9))
    style.configure("Preview.TLabel",background="white",foreground=MUTED,font=("Microsoft YaHei UI",9))
    style.configure("Footer.TLabel",background=BG,foreground=MUTED,font=("Microsoft YaHei UI",9))
    style.configure("Soft.TCombobox",padding=(0,3),arrowsize=14,fieldbackground=FIELD,
                    background=FIELD,foreground=INK,borderwidth=0,relief="flat",
                    lightcolor=FIELD,darkcolor=FIELD,bordercolor=FIELD,arrowcolor="#8e8e93")
    style.map("Soft.TCombobox",fieldbackground=[("readonly",FIELD),("disabled",FIELD)],
              foreground=[("readonly",INK),("disabled",MUTED)],
              selectbackground=[("readonly",FIELD)],selectforeground=[("readonly",INK)])
    style.configure("Soft.Vertical.TScrollbar",background="#d1d1d6",troughcolor="white",
                    borderwidth=0,arrowsize=9,lightcolor="white",darkcolor="white")


def capture_bar(app,root):
    header=tk.Frame(root,background=BG,padx=24,pady=22)
    header.pack(fill="x")
    icon=tk.Canvas(header,width=48,height=48,background=BG,highlightthickness=0)
    rounded(icon,1,1,47,47,13,fill=BLUE,outline=BLUE)
    icon.create_text(24,24,text="T",fill="white",font=("Segoe UI",22,"bold"))
    icon.pack(side="left",padx=(0,13))
    brand=tk.Frame(header,background=BG)
    brand.pack(side="left")
    tk.Label(brand,text="Teams 字幕",background=BG,foreground=INK,
             font=("Microsoft YaHei UI",20,"bold")).pack(anchor="w")
    tk.Label(brand,text="专注会议，让对话自然归档。",background=BG,foreground=MUTED,
             font=("Microsoft YaHei UI",9)).pack(anchor="w",pady=(2,0))
    app.start_btn=RoundedButton(header,text="开始保存字幕",command=app.toggle,primary=True,background=BG)
    app.start_btn.pack(side="right",padx=(18,0))
    app.rec_var=tk.StringVar(value="尚未开始")
    app._status_card=RoundedCard(header,fill="#eaeaee",padding=8,radius=13,natural_width=True)
    app._status_card.pack(side="right")
    app.rec_label=tk.Label(app._status_card.body,textvariable=app.rec_var,background="#eaeaee",
                           foreground="#6e6e73",font=("Microsoft YaHei UI",9,"bold"))
    app.rec_label.pack(padx=4,pady=1)

    app._settings_card=RoundedCard(root,padding=19,radius=20)
    app._settings_card.pack(fill="x",padx=22,pady=(0,12))
    card=app._settings_card.body
    card.columnconfigure(0,weight=2,uniform="fields")
    card.columnconfigure(1,weight=3,uniform="fields")
    ttk.Label(card,text="保存设置",style="CardTitle.TLabel").grid(row=0,column=0,sticky="w",pady=(0,15))
    actions=tk.Frame(card,background="white")
    actions.grid(row=0,column=1,sticky="e",pady=(0,15))
    app.apply_save_btn=RoundedButton(actions,text="应用更改",command=app.apply_save_settings,compact=True)
    app.apply_save_btn.pack(side="right")
    RoundedButton(actions,text="打开文件夹",command=app.open_records,compact=True).pack(side="right",padx=(0,9))
    ttk.Label(card,text="会议 / 文件名",style="Field.TLabel").grid(row=1,column=0,sticky="w",pady=(0,7))
    ttk.Label(card,text="保存位置",style="Field.TLabel").grid(row=1,column=1,sticky="w",pady=(0,7))
    name_row=tk.Frame(card,background="white")
    name_row.grid(row=2,column=0,sticky="ew",padx=(0,18))
    name_row.columnconfigure(0,weight=1)
    app._name_field=RoundedField(name_row,app.filename_var)
    app._name_field.grid(row=0,column=0,sticky="ew")
    app.filename_entry=app._name_field.widget
    app.filename_entry.bind("<Return>",lambda e:app.apply_save_settings())
    ttk.Label(name_row,text="  .txt + .json",style="Preview.TLabel").grid(row=0,column=1)
    folder_row=tk.Frame(card,background="white")
    folder_row.grid(row=2,column=1,sticky="ew")
    folder_row.columnconfigure(0,weight=1)
    app._folder_field=RoundedField(folder_row,app.save_folder_var)
    app._folder_field.grid(row=0,column=0,sticky="ew")
    app.folder_entry=app._folder_field.widget
    app.folder_entry.bind("<Return>",lambda e:app.apply_save_settings())
    app.choose_folder_btn=RoundedButton(folder_row,text="选择…",command=app.choose_save_folder)
    app.choose_folder_btn.grid(row=0,column=1,padx=(9,0))
    app.path_preview_label=ttk.Label(card,textvariable=app.save_preview_var,style="Preview.TLabel",wraplength=980)
    app.path_preview_label.grid(row=3,column=0,columnspan=2,sticky="w",pady=(11,3))
    app.save_hint_label=ttk.Label(card,textvariable=app.save_hint_var,style="Preview.TLabel",wraplength=980)
    app.save_hint_label.grid(row=4,column=0,columnspan=2,sticky="w",pady=(0,16))
    card.bind("<Configure>",lambda e:(app.path_preview_label.configure(wraplength=max(260,e.width-2)),app.save_hint_label.configure(wraplength=max(260,e.width-2))))
    source=tk.Frame(card,background="white")
    source.grid(row=5,column=0,columnspan=2,sticky="ew")
    source.columnconfigure(1,weight=1)
    ttk.Label(source,text="会议窗口",style="Field.TLabel").grid(row=0,column=0,padx=(0,13))
    app._source_field=RoundedField(source,app.preferred,combo=True,
        values=["自动选择正在开会的窗口"],postcommand=app.refresh_meetings)
    app._source_field.grid(row=0,column=1,sticky="ew")
    app.preferred_box=app._source_field.widget
    RoundedButton(source,text="刷新",command=app.refresh_meetings).grid(row=0,column=2,padx=(9,0))
    app._rec_after_id=None
    app._rec_blink_on=False
    app._ai_controls=[]


def statusbar(app,root):
    footer=ttk.Frame(root,style="App.TFrame",padding=(25,10,25,14))
    footer.pack(fill="x",side="bottom")
    app.status=tk.StringVar(value="就绪")
    ttk.Label(footer,textvariable=app.stats,style="Footer.TLabel").pack(side="right",padx=(14,0))
    app.footer_status=ttk.Label(footer,textvariable=app.status,style="Footer.TLabel",wraplength=780)
    app.footer_status.pack(side="left",fill="x",expand=True)


def body(app,root):
    app._transcript_card=RoundedCard(root,padding=19,radius=20,expand_content=True)
    app._transcript_card.pack(fill="both",expand=True,padx=22)
    content=app._transcript_card.body
    head=tk.Frame(content,background="white")
    head.pack(fill="x",pady=(0,12))
    ttk.Label(head,text="实时字幕",style="CardTitle.TLabel").pack(side="left")
    ttk.Label(head,text="   按发言人排列",style="Card.TLabel").pack(side="left")
    RoundedButton(head,text="导出副本…",command=app.save_as,compact=True).pack(side="right")
    frame=tk.Frame(content,background="white")
    frame.pack(fill="both",expand=True)
    app.text=tk.Text(frame,wrap="word",undo=True,font=("Microsoft YaHei UI",11),
        padx=8,pady=9,background="white",foreground=INK,insertbackground=BLUE,
        selectbackground="#d9eaff",relief="flat",borderwidth=0,highlightthickness=0,spacing1=3,spacing3=5)
    app.text.tag_configure("speaker",foreground="#0066cc",font=("Microsoft YaHei UI",10,"bold"))
    app.text.tag_configure("unknown_speaker",foreground="#a16207",font=("Microsoft YaHei UI",10,"bold"))
    scroll=SlimScrollbar(frame,command=app.text.yview)
    app.text.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right",fill="y")
    app.text.pack(side="left",fill="both",expand=True)
    app._empty_panel=tk.Frame(frame,background="white")
    tk.Label(app._empty_panel,text="等待第一条字幕",font=("Microsoft YaHei UI",15,"bold"),
        foreground="#55555a",background="white").pack()
    tk.Label(app._empty_panel,text="在 Teams 中开启实时字幕，再点击「开始保存字幕」。\n对话会显示在这里，并自动保存到你选择的位置。",
        font=("Microsoft YaHei UI",10),foreground="#a1a1a6",background="white",justify="center").pack(pady=(11,0))
    app._sync_empty_state()
