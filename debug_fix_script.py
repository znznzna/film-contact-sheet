#!/usr/bin/env python3
"""
Film Contact Sheet Generator 修正スクリプト（デバッグ版）
問題を特定して確実に修正を適用します
"""

import os
import shutil
from pathlib import Path

def check_current_files():
    """現在のファイル状況を確認"""
    print("現在のファイル状況:")
    files_to_check = ["main_window.py", "contact_sheet.py", "ui/main_window.py", "core/contact_sheet.py"]
    
    for file in files_to_check:
        if Path(file).exists():
            print(f"  ✓ {file} が存在します")
            # ファイルの一部を確認
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'Developer' in content:
                    print(f"    → Developerフィールドは既に存在")
                if 'color: #000000' in content:
                    print(f"    → テキスト色修正は既に適用済み")
        else:
            print(f"  ✗ {file} が見つかりません")
    print()

def find_actual_files():
    """実際のファイル構造を確認"""
    print("プロジェクト構造を確認中...")
    
    # カレントディレクトリから検索
    ui_files = list(Path('.').rglob('*main_window.py'))
    contact_files = list(Path('.').rglob('*contact_sheet.py'))
    
    print("見つかったファイル:")
    for file in ui_files:
        print(f"  main_window.py: {file}")
    for file in contact_files:
        print(f"  contact_sheet.py: {file}")
    
    return ui_files, contact_files

def backup_files(files_to_backup):
    """ファイルをバックアップ"""
    backup_dir = Path("backup")
    backup_dir.mkdir(exist_ok=True)
    
    for file_path in files_to_backup:
        if file_path.exists():
            backup_name = f"{file_path.parent.name}_{file_path.name}" if file_path.parent.name != '.' else file_path.name
            backup_path = backup_dir / backup_name
            shutil.copy2(file_path, backup_path)
            print(f"バックアップ: {file_path} → {backup_path}")

def fix_main_window_file(file_path):
    """main_window.pyファイルを修正"""
    print(f"{file_path} を修正中...")
    
    # 現在のファイル内容を読み込み
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 既に修正済みかチェック
    if 'color: #000000' in content and 'Developer' in content:
        print("  → 既に修正済みです")
        return
    
    # QListWidgetのスタイル修正
    old_style = '''        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #cccccc;
                border-radius: 5px;
                background-color: #f5f5f5;
            }
        """)'''
    
    new_style = '''        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #cccccc;
                border-radius: 5px;
                background-color: #f5f5f5;
                color: #000000;
            }
            QListWidget::item {
                color: #000000;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: #3399ff;
                color: white;
            }
        """)'''
    
    if old_style in content:
        content = content.replace(old_style, new_style)
        print("  ✓ リストの文字色を修正")
    
    # dragMoveEventを追加
    if 'def dragMoveEvent(self, event):' not in content:
        drag_enter_pos = content.find('def dropEvent(self, event: QDropEvent):')
        if drag_enter_pos != -1:
            drag_move_method = '''    
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    '''
            content = content[:drag_enter_pos] + drag_move_method + '\n' + content[drag_enter_pos:]
            print("  ✓ dragMoveEventを追加")
    
    # Developerフィールドを追加
    if "'developer'" not in content:
        developer_field = "            'developer': InfoFieldWidget(\"Developer\", \"Carmencita Film Lab\")"
        
        # info_fieldsの定義を探して追加
        film_field_pos = content.find("'film': InfoFieldWidget(\"Film\", \"Kodak Portra 400\")")
        if film_field_pos != -1:
            insert_pos = content.find('\n', film_field_pos) + 1
            content = content[:insert_pos] + '            ' + developer_field + ',\n' + content[insert_pos:]
            print("  ✓ Developerフィールドを追加")
    
    # フォルダ対応のためのメソッド追加
    if '_collect_files_from_path' not in content:
        collect_method = '''    
    def _collect_files_from_path(self, path: str) -> List[str]:
        """パスから画像ファイルを収集（ディレクトリの場合は中身も含む）"""
        path_obj = Path(path)
        files = []
        
        if path_obj.is_file() and self._is_image_file(path):
            files.append(path)
        elif path_obj.is_dir():
            # ディレクトリの場合、中身の画像ファイルを再帰的に検索
            image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
            for file_path in path_obj.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    files.append(str(file_path))
        
        return files
    
    def _is_image_file(self, file_path: str) -> bool:
        """画像ファイルかどうかチェック"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
        return Path(file_path).suffix.lower() in image_extensions
'''
        
        # クラスの最後に追加
        class_end = content.rfind('        event.accept()')
        if class_end != -1:
            insert_pos = content.find('\n', class_end) + 1
            content = content[:insert_pos] + collect_method + content[insert_pos:]
            print("  ✓ フォルダ対応メソッドを追加")
    
    # dropEventの修正
    old_drop_event = '''    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                files.append(url.toLocalFile())
        if files:
            self.files_dropped.emit(files)'''
    
    new_drop_event = '''    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                file_path = url.toLocalFile()
                files.extend(self._collect_files_from_path(file_path))
        if files:
            self.files_dropped.emit(files)'''
    
    if old_drop_event in content:
        content = content.replace(old_drop_event, new_drop_event)
        print("  ✓ dropEventを修正")
    
    # 変更されたスタイルも修正
    changed_style_old = '''        self.image_list.setStyleSheet("""
            QListWidget {
                border: 2px dashed #ff8c00;
                border-radius: 5px;
                background-color: #f5f5f5;
            }
        """)'''
    
    changed_style_new = '''        self.image_list.setStyleSheet("""
            QListWidget {
                border: 2px dashed #ff8c00;
                border-radius: 5px;
                background-color: #f5f5f5;
                color: #000000;
            }
            QListWidget::item {
                color: #000000;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: #3399ff;
                color: white;
            }
        """)'''
    
    if changed_style_old in content:
        content = content.replace(changed_style_old, changed_style_new)
        print("  ✓ 変更時のスタイルも修正")
    
    # reset_change_indicators内のスタイルも修正
    reset_style_old = '''        self.image_list.setStyleSheet("""
            QListWidget {
                border: 2px dashed #cccccc;
                border-radius: 5px;
                background-color: #f5f5f5;
            }
        """)'''
    
    reset_style_new = '''        self.image_list.setStyleSheet("""
            QListWidget {
                border: 2px dashed #cccccc;
                border-radius: 5px;
                background-color: #f5f5f5;
                color: #000000;
            }
            QListWidget::item {
                color: #000000;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: #3399ff;
                color: white;
            }
        """)'''
    
    if reset_style_old in content:
        content = content.replace(reset_style_old, reset_style_new)
        print("  ✓ リセット時のスタイルも修正")
    
    # 情報収集部分にdeveloperを追加
    if "'developer': self.info_fields['developer'].get_value()" not in content:
        info_collection = content.find("'film': self.info_fields['film'].get_value()")
        if info_collection != -1:
            insert_pos = content.find('\n', info_collection) + 1
            new_line = "                'developer': self.info_fields['developer'].get_value()\n"
            content = content[:insert_pos] + new_line + content[insert_pos:]
            print("  ✓ 情報収集にdeveloperを追加")
    
    # ファイルに書き込み
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✓ {file_path} の修正完了")

def fix_contact_sheet_file(file_path):
    """contact_sheet.pyファイルを修正"""
    print(f"{file_path} を修正中...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # info_heightを30から35に変更
    if "self.info_height = int(30 * self.DPI / 25.4)" in content:
        content = content.replace(
            "self.info_height = int(30 * self.DPI / 25.4)",
            "self.info_height = int(35 * self.DPI / 25.4)"
        )
        print("  ✓ 情報エリアの高さを35mmに変更")
    
    # _add_info_sectionメソッドを新しいバージョンに置換
    old_method_start = "def _add_info_section(self, sheet: Image.Image, draw: ImageDraw.Draw,"
    old_method_end = "font=font_bold, fill='black')"
    
    start_pos = content.find(old_method_start)
    if start_pos != -1:
        # メソッド全体を探す
        method_start = content.rfind('def _add_info_section', 0, start_pos + len(old_method_start))
        
        # 次のメソッドまたはクラス終了を探す
        next_method = content.find('\n    def ', method_start + 1)
        if next_method == -1:
            next_method = len(content)
        
        new_method = '''    def _add_info_section(self, sheet: Image.Image, draw: ImageDraw.Draw, 
                         info: Dict[str, str]) -> None:
        """情報セクションを追加（レイアウト改善）"""
        # フォント設定
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 
                                    int(14 * self.DPI / 72))  # 14pt
            font_bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 
                                         int(16 * self.DPI / 72), index=1)  # Bold
        except:
            font = ImageFont.load_default()
            font_bold = font
        
        # 情報エリアの開始位置
        info_y = self.height - self.margin - self.info_height
        
        # 区切り線
        draw.line([(self.margin, info_y), 
                  (self.width - self.margin, info_y)], 
                 fill='black', width=2)
        
        # 情報を描画
        y_offset = info_y + 15  # 上部余白を増加
        line_height = int(18 * self.DPI / 72)  # 行間を調整
        
        # 左側の情報
        left_items = []
        if info.get('date'):
            left_items.append(f"Date: {info['date']}")
        if info.get('location'):
            left_items.append(f"Location: {info['location']}")
        if info.get('developer'):
            left_items.append(f"Developer: {info['developer']}")
        
        for i, item in enumerate(left_items):
            draw.text((self.margin, y_offset + i * line_height), 
                     item, font=font, fill='black')
        
        # 右側の情報
        right_x = self.width // 2
        right_items = []
        if info.get('camera'):
            right_items.append(f"Camera: {info['camera']}")
        if info.get('lens'):
            right_items.append(f"Lens: {info['lens']}")
        
        for i, item in enumerate(right_items):
            draw.text((right_x, y_offset + i * line_height), 
                     item, font=font, fill='black')
        
        # フィルム名（中央下、他の情報から間隔を空ける）
        if info.get('film'):
            film_text = f"Film: {info['film']}"
            bbox = draw.textbbox((0, 0), film_text, font=font_bold)
            text_width = bbox[2] - bbox[0]
            
            # フィルム名の位置を他の情報から少し離す
            film_y = y_offset + max(len(left_items), len(right_items)) * line_height + int(8 * self.DPI / 72)
            
            draw.text(((self.width - text_width) // 2, film_y), 
                     film_text, 
                     font=font_bold, fill='black')
'''
        
        content = content[:method_start] + new_method + content[next_method:]
        print("  ✓ 情報セクションのレイアウトを改善")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✓ {file_path} の修正完了")

def main():
    """メイン関数"""
    print("=== Film Contact Sheet Generator 修正スクリプト（デバッグ版） ===")
    print()
    
    # 現在の状況確認
    check_current_files()
    
    # 実際のファイルを探す
    ui_files, contact_files = find_actual_files()
    
    if not ui_files and not contact_files:
        print("修正対象のファイルが見つかりません。")
        print("main.pyと同じディレクトリで実行してください。")
        return
    
    # バックアップ
    all_files = ui_files + contact_files
    print("バックアップを作成中...")
    backup_files(all_files)
    print()
    
    # 修正実行
    print("修正を実行中...")
    
    for ui_file in ui_files:
        fix_main_window_file(ui_file)
    
    for contact_file in contact_files:
        fix_contact_sheet_file(contact_file)
    
    print()
    print("=== 修正完了 ===")
    print()
    print("修正内容:")
    print("✓ リスト画面のファイル名テキストを黒色に変更")
    print("✓ ドラッグ&ドロップ機能を修正・改善")
    print("✓ フォルダドロップ時に中身の画像ファイルを自動追加")
    print("✓ Developer フィールドを追加（デフォルト: Carmencita Film Lab）")
    print("✓ 下部情報エリアのレイアウトを調整（Film名との間隔改善）")
    print()
    print("アプリケーションを再起動して変更を確認してください：")
    print("python main.py")

if __name__ == "__main__":
    main()