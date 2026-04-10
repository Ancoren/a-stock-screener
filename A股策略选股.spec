# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_scanner.py'],
    pathex=[],
    binaries=[],
    datas=[('config.yaml', '.')],
    hiddenimports=['scanner', 'strategies.ma_cross', 'strategies.macd', 'strategies.rsi', 'strategies.bollinger', 'strategies.volume', 'strategies.trend', 'data.fetcher', 'utils.indicators', 'utils.report'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='A股策略选股',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
