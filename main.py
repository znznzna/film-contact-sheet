#!/usr/bin/env python3
"""
Film Contact Sheet Generator
フィルムスキャン画像からコンタクトシートを生成するアプリケーション
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

from ui.main_window import MainWindow


def main():
    """メインエントリーポイント"""
    # High DPI対応
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # アプリケーション作成
    app = QApplication(sys.argv)
    app.setApplicationName("Film Contact Sheet Generator")
    app.setOrganizationName("FilmTools")
    
    # メインウィンドウ作成・表示
    window = MainWindow()
    window.show()
    
    # アプリケーション実行
    sys.exit(app.exec())


if __name__ == "__main__":
    main()