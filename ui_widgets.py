"""Small native Tk components with rounded, quiet surfaces and keyboard support."""
from __future__ import annotations

import tkinter as tk
import math
from tkinter import font as tkfont, ttk

BG = "#f5f5f7"
INK = "#1d1d1f"
MUTED = "#86868b"
FIELD = "#f2f2f5"
BLUE = "#007aff"
FONT = ("Microsoft YaHei UI", 10)


def rounded(canvas, x1, y1, x2, y2, radius, **kwargs):
    radius = max(0, min(radius, (x2-x1)/2, (y2-y1)/2))
    points=[]
    for cx,cy,start in ((x2-radius,y1+radius,-90),(x2-radius,y2-radius,0),
                        (x1+radius,y2-radius,90),(x1+radius,y1+radius,180)):
        for step in range(9):
            angle=math.radians(start+step*90/8)
            points.extend((cx+radius*math.cos(angle),cy+radius*math.sin(angle)))
    return canvas.create_polygon(*points,smooth=True,splinesteps=12,**kwargs)


class RoundedCard(tk.Canvas):
    def __init__(self, parent, *, background=BG, fill="white", radius=18,
                 padding=18, expand_content=False, natural_width=False, **kwargs):
        super().__init__(parent, background=background, highlightthickness=0,
                         borderwidth=0, width=1, height=100, **kwargs)
        self.fill, self.radius, self.padding = fill, radius, padding
        self.expand_content, self.natural_width = expand_content, natural_width
        self.body=tk.Frame(self, background=fill, borderwidth=0)
        self._window=self.create_window(padding,padding,window=self.body,anchor="nw")
        self._scheduled=False
        self.bind("<Configure>",self._schedule)
        self.body.bind("<Configure>",self._schedule)

    def _schedule(self, _event=None):
        if not self._scheduled:
            self._scheduled=True
            self.after_idle(self._layout)

    def _layout(self):
        self._scheduled=False
        if not self.winfo_exists():
            return
        pad=self.padding
        if self.natural_width:
            self.configure(width=self.body.winfo_reqwidth()+2*pad)
        width=max(1,self.winfo_width())
        self.itemconfigure(self._window,width=max(1,width-2*pad))
        if self.expand_content:
            self.itemconfigure(self._window,height=max(1,self.winfo_height()-2*pad))
        else:
            requested=self.body.winfo_reqheight()+2*pad
            if int(self.cget("height")) != requested:
                self.configure(height=requested)
        self.delete("surface")
        rounded(self,1,1,width-1,max(2,self.winfo_height()-1),self.radius,
                fill=self.fill,outline="#e9e9ed",width=1,tags="surface")
        self.tag_lower("surface")


class RoundedField(tk.Canvas):
    def __init__(self,parent,variable,*,combo=False,values=(),postcommand=None):
        super().__init__(parent,background="white",highlightthickness=0,
                         borderwidth=0,height=42,width=1)
        self._focused=False
        if combo:
            self.widget=ttk.Combobox(self,textvariable=variable,state="readonly",
                values=values,postcommand=postcommand,style="Soft.TCombobox",font=FONT)
        else:
            self.widget=tk.Entry(self,textvariable=variable,font=FONT,background=FIELD,
                foreground=INK,insertbackground=BLUE,selectbackground="#cfe4ff",
                relief="flat",borderwidth=0,highlightthickness=0)
        self._window=self.create_window(12,21,window=self.widget,anchor="w")
        self.bind("<Configure>",self._layout)
        self.widget.bind("<FocusIn>",lambda e:self._focus(True),add=True)
        self.widget.bind("<FocusOut>",lambda e:self._focus(False),add=True)
        self.bind("<Button-1>",lambda e:self.widget.focus_set())

    def _focus(self,value):
        self._focused=value
        self._layout()

    def _layout(self,_event=None):
        width=max(1,self.winfo_width())
        self.delete("surface")
        rounded(self,1,1,width-1,41,11,fill=FIELD,
            outline=BLUE if self._focused else FIELD,width=1.5,tags="surface")
        self.tag_lower("surface")
        self.itemconfigure(self._window,width=max(1,width-24))


class RoundedButton(tk.Canvas):
    def __init__(self,parent,*,text,command,primary=False,background="white",compact=False):
        self._text=text
        self._command=command
        self._primary=primary
        self._enabled=True
        self._hover=False
        self._pressed=False
        self._font=tkfont.Font(family="Microsoft YaHei UI",size=10,weight="bold" if primary else "normal")
        self._height=44 if primary else (34 if compact else 38)
        super().__init__(parent,background=background,highlightthickness=0,
            borderwidth=0,takefocus=True,cursor="hand2",height=self._height,
            width=self._font.measure(text)+(36 if primary else 26))
        self.bind("<Configure>",self._draw)
        self.bind("<Enter>",lambda e:self._change(hover=True))
        self.bind("<Leave>",lambda e:self._change(hover=False,pressed=False))
        self.bind("<ButtonPress-1>",lambda e:self._change(pressed=True))
        self.bind("<ButtonRelease-1>",self._release)
        self.bind("<space>",lambda e:self.invoke())
        self.bind("<Return>",lambda e:self.invoke())
        self.bind("<FocusIn>",self._draw)
        self.bind("<FocusOut>",self._draw)

    def _change(self,**values):
        self._hover=values.get("hover",self._hover)
        self._pressed=values.get("pressed",self._pressed)
        self._draw()

    def _release(self,event):
        was_pressed=self._pressed
        self._pressed=False
        self._draw()
        if was_pressed and 0<=event.x<=self.winfo_width() and 0<=event.y<=self.winfo_height():
            self.focus_set()
            self.invoke()

    def invoke(self):
        if self._enabled:
            return self._command()

    def configure(self,cnf=None,**kwargs):
        if "text" in kwargs:
            self._text=kwargs.pop("text")
            kwargs["width"]=self._font.measure(self._text)+(36 if self._primary else 26)
        if "state" in kwargs:
            self._enabled=kwargs.pop("state")!="disabled"
        result=super().configure(cnf,**kwargs)
        if hasattr(self,"_font"):
            self._draw()
        return result

    config=configure

    def _draw(self,_event=None):
        self.delete("all")
        if self._primary:
            color="#0063ce" if self._pressed else ("#1486ff" if self._hover else BLUE)
            foreground="white"
        else:
            color="#e3e3e8" if self._pressed else ("#eaeaef" if self._hover else FIELD)
            foreground=INK
        if not self._enabled:
            color,foreground="#eeeeF2","#aaaab0"
        focused=self.focus_get()==self
        rounded(self,2,2,max(3,self.winfo_width()-2),self._height-2,12,
            fill=color,outline="#93c5fd" if focused else color,width=2)
        self.create_text(self.winfo_width()/2,self._height/2,text=self._text,
            font=self._font,fill=foreground)


class SlimScrollbar(tk.Canvas):
    """A draggable, arrow-free scroll thumb; the Text keeps its keyboard bindings."""
    def __init__(self,parent,command):
        super().__init__(parent,width=10,background="white",highlightthickness=0,borderwidth=0)
        self.command=command
        self.first,self.last=0.0,1.0
        self._offset=0
        self._hover=False
        self.bind("<Configure>",lambda e:self._draw())
        self.bind("<Enter>",lambda e:self._highlight(True))
        self.bind("<Leave>",lambda e:self._highlight(False))
        self.bind("<ButtonPress-1>",self._press)
        self.bind("<B1-Motion>",self._drag)
        self.bind("<MouseWheel>",lambda e:self.command("scroll",-int(e.delta/120),"units"))

    def set(self,first,last):
        self.first,self.last=float(first),float(last)
        self._draw()

    def _highlight(self,value):
        self._hover=value
        self._draw()

    def _bounds(self):
        height=max(1,self.winfo_height()-6)
        length=min(height,max(28,height*(self.last-self.first)))
        travel=max(1,height-length)
        top=3+travel*self.first/max(.0001,1-(self.last-self.first))
        return top,length,travel

    def _draw(self):
        self.delete("all")
        if self.last-self.first>=.999:
            return
        top,length,_=self._bounds()
        color="#aeaeb2" if self._hover else "#c7c7cc"
        rounded(self,2,top,8,top+length,3,fill=color,outline=color)

    def _press(self,event):
        top,length,_=self._bounds()
        if top<=event.y<=top+length:
            self._offset=event.y-top
        else:
            self._offset=length/2
            self._drag(event)

    def _drag(self,event):
        _top,_length,travel=self._bounds()
        ratio=max(0,min(1,(event.y-3-self._offset)/travel))
        self.command("moveto",ratio*max(0,1-(self.last-self.first)))
