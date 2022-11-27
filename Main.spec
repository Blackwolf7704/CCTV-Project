# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.building.datastruct import TOC

block_cipher = None

data = [
	('./UI/*.ui', './UI'),
	('./detect.onnx', './Model'),
]

a = Analysis(
    ['Main.py'],
    pathex=[],
    binaries=[],
    datas=data,
    hiddenimports=['PIL', 'cv2', 'PyQt6', 'onnxruntime', 'time', 'sys', 'os', 'json', 'datetime'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

x = 'cp39-win_amd64'
datas_upd = TOC()

for d in a.datas:
    if x not in d[0] and x not in d[1]:
        datas_upd.append(d)

a.datas = datas_upd

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
