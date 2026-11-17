# Teams-only portable fork. Audio engines are deliberately not included.
from PyInstaller.utils.hooks import collect_data_files
datas=[("teams_reader.ps1","."),("cue.ico","."),("LICENSE",".")]
datas+=collect_data_files("sv_ttk")
a=Analysis(["teams_app.py"],pathex=[],binaries=[],datas=datas,
    hiddenimports=["docx","pypdf","sv_ttk"],
    excludes=["numpy","torch","faster_whisper","ctranslate2","onnxruntime","soundcard","av","pytest","PyInstaller"],
    hookspath=[],hooksconfig={},runtime_hooks=[],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name="CueTeams",console=False,
    icon="cue.ico",upx=False,disable_windowed_traceback=False)
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name="Cue-Teams")
