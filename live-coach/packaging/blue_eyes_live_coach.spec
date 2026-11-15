# Build from live-coach directory: python -m PyInstaller packaging/blue_eyes_live_coach.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

root = Path(SPECPATH).resolve()
a = Analysis(
    [str(root / "app.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / "data" / "blue-eyes-primite.json"), "data")],
    hiddenimports=collect_submodules("PySide6"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="BlueEyesLiveCoach",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=None,
)
