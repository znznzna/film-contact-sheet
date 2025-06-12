from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QLineEdit, QPushButton, QComboBox,
                            QListWidget, QGroupBox, QFileDialog, QMessageBox,
                            QSplitter, QScrollArea, QTextEdit, QAbstractItemView)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image
import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.film_formats import FilmType, get_film_format
from core.image_processor import ImageProcessor
from core.contact_sheet import ContactSheet


class DropAreaWidget(QListWidget):
    """ドラッグ&ドロップ対応のリストウィジェット"""
    
    files_dropped = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #cccccc;
                border-radius: 5px;
                background-color: #f5f5f5;
            }
        """)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                files.append(url.toLocalFile())
        if files:
            self.files_dropped.emit(files)


class InfoFieldWidget(QWidget):
    """情報入力フィールドウィジェット"""
    
    value_changed = pyqtSignal()
    
    def __init__(self, label: str, placeholder: str = ""):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(f"{label}:")
        self.label.setFixedWidth(80)
        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.textChanged.connect(self.value_changed.emit)
        
        # 初期状態
        self._original_style = self.input.styleSheet()
        self._has_unsaved_changes = False
        
        layout.addWidget(self.label)
        layout.addWidget(self.input)
        self.setLayout(layout)
    
    def mark_as_changed(self):
        """変更があったことを視覚的に示す"""
        self._has_unsaved_changes = True
        self.input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ff8c00;
                border-radius: 3px;
                padding: 2px;
            }
        """)
    
    def mark_as_saved(self):
        """保存済みの状態に戻す"""
        self._has_unsaved_changes = False
        self.input.setStyleSheet(self._original_style)
    
    def get_value(self) -> str:
        return self.input.text()
    
    def has_unsaved_changes(self) -> bool:
        return self._has_unsaved_changes


class MainWindow(QMainWindow):
    """メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.image_processor = ImageProcessor()
        self.contact_sheet = ContactSheet()
        self.current_sheet = None
        self.has_unsaved_changes = False
        
        self.init_ui()
        
    def init_ui(self):
        """UIを初期化"""
        self.setWindowTitle("Film Contact Sheet Generator")
        self.setGeometry(100, 100, 1200, 800)
        
        # メインウィジェット
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # メインレイアウト（水平分割）
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        
        # 左側パネル
        left_panel = self.create_left_panel()
        
        # 右側パネル（プレビュー）
        right_panel = self.create_right_panel()
        
        # スプリッター
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)
    
    def create_left_panel(self) -> QWidget:
        """左側パネルを作成"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # フィルムフォーマット選択
        format_group = QGroupBox("Film Format")
        format_layout = QVBoxLayout()
        self.format_combo = QComboBox()
        for film_type in FilmType:
            self.format_combo.addItem(film_type.value, film_type)
        self.format_combo.currentIndexChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.format_combo)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # 画像リスト
        image_group = QGroupBox("Images")
        image_layout = QVBoxLayout()
        
        # ボタン
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Images")
        self.add_button.clicked.connect(self.add_images)
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_images)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.clear_button)
        image_layout.addLayout(button_layout)
        
        # ドロップエリア
        self.image_list = DropAreaWidget()
        self.image_list.files_dropped.connect(self.handle_dropped_files)
        image_layout.addWidget(self.image_list)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        # 情報入力
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout()
        
        self.info_fields = {
            'date': InfoFieldWidget("Date", "YYYY-MM-DD"),
            'location': InfoFieldWidget("Location", "Tokyo, Japan"),
            'camera': InfoFieldWidget("Camera", "Nikon F3"),
            'lens': InfoFieldWidget("Lens", "50mm f/1.4"),
            'film': InfoFieldWidget("Film", "Kodak Portra 400")
        }
        
        for field in self.info_fields.values():
            field.value_changed.connect(self.on_info_changed)
            info_layout.addWidget(field)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # アクションボタン
        action_layout = QHBoxLayout()
        self.update_button = QPushButton("Update Preview")
        self.update_button.clicked.connect(self.update_preview)
        self.update_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        action_layout.addWidget(self.update_button)
        layout.addLayout(action_layout)
        
        # 出力設定
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()
        
        # フォーマット選択
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.export_format = QComboBox()
        self.export_format.addItems(["JPEG", "PNG", "PDF"])
        format_layout.addWidget(self.export_format)
        export_layout.addLayout(format_layout)
        
        # エクスポートボタン
        self.export_button = QPushButton("Export Contact Sheet")
        self.export_button.clicked.connect(self.export_sheet)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        export_layout.addWidget(self.export_button)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """右側パネル（プレビュー）を作成"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # プレビューラベル
        preview_label = QLabel("Preview")
        preview_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(preview_label)
        
        # プレビューエリア
        scroll_area = QScrollArea()
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #f0f0f0;")
        self.preview_label.setText("No preview available.\nAdd images and click 'Update Preview'.")
        
        scroll_area.setWidget(self.preview_label)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        return panel
    
    def add_images(self):
        """画像を追加"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Image Files (*.jpg *.jpeg *.png *.tiff *.tif *.bmp)"
        )
        if files:
            self.handle_dropped_files(files)
    
    def handle_dropped_files(self, files: List[str]):
        """ドロップされたファイルを処理"""
        # 既存のファイルリストを取得
        existing_files = []
        for i in range(self.image_list.count()):
            existing_files.append(self.image_list.item(i).data(Qt.ItemDataRole.UserRole))
        
        # 新しいファイルを追加
        new_files = []
        for file in files:
            if file not in existing_files:
                new_files.append(file)
        
        # 画像ファイルのみをフィルタリング
        self.image_processor.load_images(existing_files + new_files)
        
        # リストを更新
        self.update_image_list()
        
        # 変更フラグを立てる
        self.mark_images_changed()
    
    def update_image_list(self):
        """画像リストを更新"""
        self.image_list.clear()
        for img_path in self.image_processor.images:
            item_text = f"{img_path.name}"
            self.image_list.addItem(item_text)
            # ファイルパスをアイテムに保存
            self.image_list.item(self.image_list.count() - 1).setData(
                Qt.ItemDataRole.UserRole, str(img_path)
            )
    
    def clear_images(self):
        """画像をクリア"""
        if self.image_list.count() > 0:
            reply = QMessageBox.question(
                self,
                "Clear Images",
                "Are you sure you want to clear all images?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.image_list.clear()
                self.image_processor.images = []
                self.mark_images_changed()
    
    def on_format_changed(self):
        """フィルムフォーマットが変更された"""
        self.mark_format_changed()
    
    def on_info_changed(self):
        """情報フィールドが変更された"""
        sender = self.sender()
        if isinstance(sender, InfoFieldWidget):
            sender.mark_as_changed()
            self.has_unsaved_changes = True
    
    def mark_images_changed(self):
        """画像リストが変更されたことを示す"""
        self.has_unsaved_changes = True
        self.image_list.setStyleSheet("""
            QListWidget {
                border: 2px dashed #ff8c00;
                border-radius: 5px;
                background-color: #f5f5f5;
            }
        """)
    
    def mark_format_changed(self):
        """フォーマットが変更されたことを示す"""
        self.has_unsaved_changes = True
        self.format_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #ff8c00;
                border-radius: 3px;
            }
        """)
    
    def reset_change_indicators(self):
        """変更インジケーターをリセット"""
        self.has_unsaved_changes = False
        
        # 画像リスト
        self.image_list.setStyleSheet("""
            QListWidget {
                border: 2px dashed #cccccc;
                border-radius: 5px;
                background-color: #f5f5f5;
            }
        """)
        
        # フォーマット選択
        self.format_combo.setStyleSheet("")
        
        # 情報フィールド
        for field in self.info_fields.values():
            field.mark_as_saved()
    
    def update_preview(self):
        """プレビューを更新"""
        if not self.image_processor.images:
            QMessageBox.warning(self, "No Images", "Please add images first.")
            return
        
        try:
            # フィルムフォーマットを取得
            film_type = self.format_combo.currentData()
            film_format = get_film_format(film_type)
            
            # 画像を処理
            processed_images = self.image_processor.process_images(film_format)
            
            # 情報を収集
            info = {
                'date': self.info_fields['date'].get_value(),
                'location': self.info_fields['location'].get_value(),
                'camera': self.info_fields['camera'].get_value(),
                'lens': self.info_fields['lens'].get_value(),
                'film': self.info_fields['film'].get_value()
            }
            
            # コンタクトシートを作成
            self.current_sheet = self.contact_sheet.create_sheet(
                processed_images, film_format, info
            )
            
            # プレビューを表示
            self.show_preview(self.current_sheet)
            
            # 変更インジケーターをリセット
            self.reset_change_indicators()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create preview: {str(e)}")
    
    def show_preview(self, sheet: Image.Image):
        """プレビューを表示"""
        # PIL ImageをQPixmapに変換
        sheet_rgb = sheet.convert('RGB')
        
        # プレビュー用にリサイズ（アスペクト比を維持）
        preview_width = 600
        aspect_ratio = sheet.height / sheet.width
        preview_height = int(preview_width * aspect_ratio)
        
        sheet_preview = sheet_rgb.resize(
            (preview_width, preview_height),
            Image.Resampling.LANCZOS
        )
        
        # QImageに変換
        data = sheet_preview.tobytes('raw', 'RGB')
        qimage = QImage(
            data,
            sheet_preview.width,
            sheet_preview.height,
            sheet_preview.width * 3,
            QImage.Format.Format_RGB888
        )
        
        # QPixmapに変換して表示
        pixmap = QPixmap.fromImage(qimage)
        self.preview_label.setPixmap(pixmap)
    
    def export_sheet(self):
        """コンタクトシートをエクスポート"""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to update the preview before exporting?",
                QMessageBox.StandardButton.Yes | 
                QMessageBox.StandardButton.No | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.update_preview()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        if self.current_sheet is None:
            QMessageBox.warning(self, "No Sheet", "Please create a contact sheet first.")
            return
        
        # ファイル形式を取得
        format_type = self.export_format.currentText()
        
        # ファイル拡張子
        if format_type == "JPEG":
            ext = "jpg"
        elif format_type == "PNG":
            ext = "png"
        else:  # PDF
            ext = "pdf"
        
        # ファイルダイアログ
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Contact Sheet",
            f"contact_sheet.{ext}",
            f"{format_type} Files (*.{ext})"
        )
        
        if file_path:
            try:
                if format_type == "JPEG":
                    self.contact_sheet.save_as_jpeg(self.current_sheet, file_path)
                elif format_type == "PNG":
                    self.contact_sheet.save_as_png(self.current_sheet, file_path)
                else:  # PDF
                    self.contact_sheet.save_as_pdf([self.current_sheet], file_path)
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Contact sheet exported successfully to:\n{file_path}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export contact sheet: {str(e)}"
                )
    
    def closeEvent(self, event):
        """ウィンドウを閉じる際の処理"""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        event.accept()