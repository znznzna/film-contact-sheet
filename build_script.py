#!/usr/bin/env python3
"""
アプリケーションをビルドするスクリプト
Mac用の.appファイルを生成
"""

import os
import sys
import shutil
from pathlib import Path
import subprocess


def clean_build_dirs():
    """ビルドディレクトリをクリーンアップ"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"Cleaned: {dir_name}")


def create_spec_file():
    """PyInstallerのspecファイルを作成"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('core', 'core'),
        ('ui', 'ui'),
    ],
    hiddenimports=['PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FilmContactSheet',
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

app = BUNDLE(
    exe,
    name='FilmContactSheet.app',
    icon=None,
    bundle_identifier='com.filmtools.contactsheet',
    version='1.0.0',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Image Files',
                'CFBundleTypeRole': 'Viewer',
                'LSItemContentTypes': ['public.image'],
            }
        ],
        'NSHighResolutionCapable': 'True',
    },
)
'''
    
    with open('FilmContactSheet.spec', 'w') as f:
        f.write(spec_content)
    print("Created: FilmContactSheet.spec")


def build_app():
    """アプリケーションをビルド"""
    print("Building application...")
    
    # PyInstallerコマンド
    cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        'FilmContactSheet.spec'
    ]
    
    # ビルド実行
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Build successful!")
        print(f"Application created: dist/FilmContactSheet.app")
    else:
        print("Build failed!")
        print(result.stderr)
        sys.exit(1)


def create_dmg():
    """DMGファイルを作成（オプション）"""
    if sys.platform == 'darwin':
        print("Creating DMG...")
        cmd = [
            'hdiutil', 'create',
            '-volname', 'FilmContactSheet',
            '-srcfolder', 'dist/FilmContactSheet.app',
            '-ov',
            '-format', 'UDZO',
            'dist/FilmContactSheet.dmg'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("DMG created: dist/FilmContactSheet.dmg")
        else:
            print("DMG creation failed!")
            print(result.stderr)


def main():
    """メイン処理"""
    print("Film Contact Sheet Generator - Build Script")
    print("=" * 50)
    
    # クリーンアップ
    clean_build_dirs()
    
    # specファイル作成
    create_spec_file()
    
    # ビルド
    build_app()
    
    # DMG作成（Macの場合）
    if sys.platform == 'darwin':
        create_dmg()
    
    print("\nBuild completed!")
    print("You can find the application in the 'dist' directory.")


if __name__ == "__main__":
    main()